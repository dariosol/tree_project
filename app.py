#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from geopy.geocoders import Nominatim  # 📍 For geocoding
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins (for development)

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:c0st4m4gn4@localhost/trees_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Geolocator for address-to-coordinates conversion
geolocator = Nominatim(user_agent="tree_locator")

class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custom_id = db.Column(db.String(50), unique=True, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    comments = db.Column(db.Text)
    actions = db.Column(db.Text)                      # New: Actions taken
    height = db.Column(db.String(50))                 # New: Height (can store letters like "M")
    trunk_diameter_cm = db.Column(db.Float)           # Updated: Trunk diameter (cm)
    crown_diameter_m = db.Column(db.Float)            # New: Crown diameter (m)
    age = db.Column(db.String(50))                    # New: Age (e.g., "Young", "Old")
    location = db.Column(db.String(255))              # New: Specific location
    cpc = db.Column(db.String(50))                    # New: Conservation Priority Code
    next_check = db.Column(db.Date)                   # New: Next inspection date
    geom = db.Column(Geometry('POINT', srid=4326))    # Geographic coordinates

# Create the database tables
with app.app_context():
    db.create_all()

# ✅ 1. Get list of unique cities
@app.route('/cities', methods=['GET'])
def get_cities():
    cities = db.session.query(Tree.city.distinct()).all()
    return jsonify([c[0] for c in cities])

# ✅ 2. Get streets in a given city
@app.route('/streets/<string:city>', methods=['GET'])
def get_streets(city):
    streets = db.session.query(Tree.address.distinct()).filter(Tree.city == city).all()
    return jsonify([s[0] for s in streets])

@app.route('/trees', methods=['GET'])
def get_trees():
    city = request.args.get('city')
    address_part = request.args.get('address')

    query = Tree.query
    if city:
        query = query.filter(Tree.city.ilike(f"%{city}%"))
    if address_part:
        query = query.filter(Tree.address.ilike(f"%{address_part}%"))

    trees = query.all()

    return jsonify([
        {
            'id': tree.id,
            'custom_id': tree.custom_id,
            'latitude': tree.latitude,
            'longitude': tree.longitude,
            'address': tree.address,
            'city': tree.city,
            'species': tree.species,
            'condition': tree.condition,
            'comments': tree.comments,
            'actions': tree.actions,
            'height': tree.height,
            'trunk_diameter_cm': tree.trunk_diameter_cm,
            'crown_diameter_m': tree.crown_diameter_m,
            'age': tree.age,
            'location': tree.location,
            'cpc': tree.cpc,
            'next_check': tree.next_check.strftime("%Y-%m-%d") if tree.next_check else None
        }
        for tree in trees
    ])


@app.route('/tree/<int:tree_id>', methods=['PATCH'])
def update_tree(tree_id):
    tree = Tree.query.get(tree_id)

    if not tree:
        return jsonify({'message': 'Tree not found'}), 404

    data = request.json

    # Update the provided fields only if they are present
    for field in ['condition', 'comments', 'actions', 'height', 'trunk_diameter_cm',
                  'crown_diameter_m', 'age', 'location', 'cpc', 'next_check']:
        if field in data:
            setattr(tree, field, data[field])

    # Handle 'next_check' if provided
    if 'next_check' in data and data['next_check']:
        try:
            tree.next_check = datetime.strptime(data['next_check'], "%Y-%m-%d")
        except ValueError:
            return jsonify({'message': 'Invalid date format for next_check. Use YYYY-MM-DD'}), 400

    db.session.commit()
    return jsonify({'message': f'Tree {tree_id} updated successfully!'}), 200


@app.route('/tree/custom/<string:custom_id>', methods=['GET'])
def get_tree_by_custom_id(custom_id):
    # Find tree by its custom_id
    tree = Tree.query.filter_by(custom_id=custom_id).first()

    if not tree:
        return jsonify({'message': 'Tree not found'}), 404

    # Return all fields including the new ones
    return jsonify({
        'id': tree.id,
        'custom_id': tree.custom_id,
        'latitude': tree.latitude,
        'longitude': tree.longitude,
        'address': tree.address,
        'city': tree.city,
        'species': tree.species,
        'condition': tree.condition,
        'comments': tree.comments,
        'actions': tree.actions,
        'height': tree.height,
        'trunk_diameter_cm': tree.trunk_diameter_cm,
        'crown_diameter_m': tree.crown_diameter_m,
        'age': tree.age,
        'location': tree.location,
        'cpc': tree.cpc,
        'next_check': tree.next_check.strftime("%Y-%m-%d") if tree.next_check else None
    })

@app.route('/tree/<int:tree_id>', methods=['GET'])
def get_tree_by_id(tree_id):
    print(f"🔍 Searching for tree with id: {tree_id}")  # Debugging

    # Fetch the tree by ID (Primary Key)
    tree = Tree.query.get(tree_id)

    # Handle missing tree
    if not tree:
        print(f"❌ Tree with id {tree_id} not found")  # Debugging
        return jsonify({'message': 'Tree not found'}), 404

    print(f"✅ Tree found: {tree.custom_id}")  # Debugging

    # Return all fields, including new ones
    return jsonify({
        'id': tree.id,
        'custom_id': tree.custom_id,
        'latitude': tree.latitude,
        'longitude': tree.longitude,
        'address': tree.address,
        'city': tree.city,
        'species': tree.species,
        'condition': tree.condition,
        'comments': tree.comments,
        'actions': tree.actions,
        'height': tree.height,
        'trunk_diameter_cm': tree.trunk_diameter_cm,
        'crown_diameter_m': tree.crown_diameter_m,
        'age': tree.age,
        'location': tree.location,
        'cpc': tree.cpc,
        'next_check': tree.next_check.strftime("%Y-%m-%d") if tree.next_check else None
    })

@app.route('/tree/<int:tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    tree = Tree.query.get(tree_id)
    if not tree:
        return jsonify({'message': 'Tree not found'}), 404

    db.session.delete(tree)
    db.session.commit()
    
    return jsonify({'message': f'Tree {tree_id} deleted successfully!'}), 200


@app.route('/add_tree', methods=['POST'])
def add_tree():
    data = request.json

    # Handle geolocation if latitude/longitude is missing
    if not data.get('latitude') or not data.get('longitude'):
        location = geolocator.geocode(data['address'])
        if location:
            data['latitude'] = location.latitude
            data['longitude'] = location.longitude
        else:
            return jsonify({'error': 'Invalid address, coordinates not found'}), 400

    # Create a new Tree object
    new_tree = Tree(
        custom_id=data['custom_id'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data.get('address', ''),
        city=data['city'],
        species=data['species'],
        condition=data['condition'],
        comments=data.get('comments', ''),
        actions=data.get('actions', ''),
        height=data.get('height', ''),
        trunk_diameter_cm=data.get('trunk_diameter_cm'),
        crown_diameter_m=data.get('crown_diameter_m'),
        age=data.get('age', ''),
        location=data.get('location', ''),
        cpc=data.get('cpc', ''),
        next_check=datetime.strptime(data.get('next_check'), "%Y-%m-%d") if data.get('next_check') else None,
        geom=f'SRID=4326;POINT({data["longitude"]} {data["latitude"]})'
    )

    # Add and commit to database
    db.session.add(new_tree)
    db.session.commit()

    return jsonify({'message': 'Tree added successfully!'}), 201

@app.route('/test_geocode', methods=['POST'])
def test_geocode():
    address = request.json.get('address')
    location = geolocator.geocode(address)
    if location:
        return jsonify({'latitude': location.latitude, 'longitude': location.longitude})
    return jsonify({'error': 'Address not found'}), 404
