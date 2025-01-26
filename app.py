#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from geopy.geocoders import Nominatim  # 📍 For geocoding
import pandas as pd

app = Flask(__name__)

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:c0st4m4gn4@localhost/trees_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Geolocator for address-to-coordinates conversion
geolocator = Nominatim(user_agent="tree_locator")

# Define the Tree model
class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custom_id = db.Column(db.String(100), unique=True)  # Custom ID field, unique
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100), nullable=False)  # ✅ Added city field
    species = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(10), nullable=False)
    comments = db.Column(db.Text)
    geom = db.Column(Geometry('POINT', srid=4326), nullable=False)

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
    street = request.args.get('street')
    
    query = Tree.query
    if city:
        query = query.filter(Tree.city == city)
    if street:
        query = query.filter(Tree.address.ilike(f"%{street}%"))  # Case-insensitive

    trees = query.all()
    return jsonify([
        {
            'id': tree.id,
            'custom_id':tree.custom_id,
            'latitude': tree.latitude,
            'longitude': tree.longitude,
            'address': tree.address,
            'city': tree.city,
            'species': tree.species,
            'condition': tree.condition,
            'comments': tree.comments
        }
        for tree in trees
    ])

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

# ✅ 5. Add a new tree (supports geocoding)
@app.route('/add_tree', methods=['POST'])
def add_tree():
    data = request.json

    # Try to get lat/lon from address if missing
    if 'latitude' not in data or 'longitude' not in data:
        location = geolocator.geocode(data['address'])
        if location:
            data['latitude'] = location.latitude
            data['longitude'] = location.longitude
        else:
            return jsonify({'error': 'Invalid address, could not find coordinates'}), 400

    new_tree = Tree(
        custom_id="T12345",  # Your custom ID
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data['address'],
        city=data['city'],  # ✅ Required
        species=data['species'],
        condition=data['condition'],
        comments=data.get('comments', ''),
        geom=f'SRID=4326;POINT({data["longitude"]} {data["latitude"]})'
    )

    db.session.add(new_tree)
    db.session.commit()
    return jsonify({'message': 'Tree added successfully!'}), 201
