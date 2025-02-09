#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from geopy.geocoders import Nominatim  # 📍 For geocoding
import pandas as pd

app = Flask(__name__)
CORS(app)  # 🔥 This allows all domains to access the AP

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:c0st4m4gn4@localhost/trees_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Geolocator for address-to-coordinates conversion
geolocator = Nominatim(user_agent="tree_locator")

class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custom_id = db.Column(db.String(50), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=True)  # Allow NULL for geocoding
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    geom = db.Column(db.String, nullable=True)  # PostGIS geometry field

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

# ✅ 3. Get trees with optional filters (city, street)
@app.route('/trees', methods=['GET'])
def get_trees():
    city = request.args.get('city')
    address_part = request.args.get('address')  # Get partial address from query params

    query = Tree.query
    if city:
        query = query.filter(Tree.city.ilike(f"%{city}%"))  # Case-insensitive city match
    if address_part:
        query = query.filter(Tree.address.ilike(f"%{address_part}%"))  # Case-insensitive partial address match

    trees = query.all()
    
    return jsonify([{
        'id': tree.id,
        'custom_id': tree.custom_id,
        'species': tree.species,
        'condition': tree.condition,
        'address': tree.address,
        'latitude': tree.latitude, 
        'longitude': tree.longitude
    } for tree in trees])

# ✅ 4. Update tree (condition/comments only)
@app.route('/tree/<int:tree_id>', methods=['PATCH'])
def update_tree(tree_id):
    tree = Tree.query.get(tree_id)
    if not tree:
        return jsonify({'message': 'Tree not found'}), 404
    
    data = request.json
    if 'condition' in data:
        tree.condition = data['condition']
    if 'comments' in data:
        tree.comments = data['comments']

    db.session.commit()
    return jsonify({'message': f'Tree {tree_id} updated successfully!'}), 200


@app.route('/tree/custom/<string:custom_id>', methods=['GET'])
def get_tree_by_custom_id(custom_id):
    tree = Tree.query.filter_by(custom_id=custom_id).first()
    if not tree:
        return jsonify({'message': 'Tree not found'}), 404
    return jsonify({
        'id': tree.id,
        'custom_id': tree.custom_id,
        'species': tree.species,
        'condition': tree.condition,
        'address': tree.address,
        'city': tree.city,
        'comments': tree.comments
    })


@app.route('/tree/<int:tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    tree = Tree.query.get(tree_id)
    if not tree:
        return jsonify({'message': 'Tree not found'}), 404

    db.session.delete(tree)
    db.session.commit()
    
    return jsonify({'message': f'Tree {tree_id} deleted successfully!'}), 200


# ✅ 5. Add a new tree (supports geocoding)
@app.route('/add_tree', methods=['POST'])
def add_tree():
    data = request.json

    # Convert empty strings to None
    latitude = data.get('latitude') or None
    longitude = data.get('longitude') or None
    address = data.get('address') or None

    # If lat/lon are missing but address exists, geocode it
    if (not latitude or not longitude) and address:
        location = geolocator.geocode(address)
        if location:
            latitude = location.latitude
            longitude = location.longitude
        else:
            return jsonify({'error': 'Invalid address, could not find coordinates'}), 400

    # If still missing lat/lon, return an error
    if not latitude or not longitude:
        return jsonify({'error': 'Either latitude/longitude or a valid address is required'}), 400

    new_tree = Tree(
        custom_id=data['custom_id'],
        latitude=latitude,
        longitude=longitude,
        address=address,
        city=data['city'],
        species=data['species'],
        condition=data['condition'],
        comments=data.get('comments', ''),
        geom=f'SRID=4326;POINT({longitude} {latitude})'
    )

    db.session.add(new_tree)
    db.session.commit()
    return jsonify({'message': 'Tree added successfully!', 'latitude': latitude, 'longitude': longitude}), 201
