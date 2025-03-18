#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from geoalchemy2 import Geometry
from geopy.geocoders import Nominatim  # 📍 For geocoding
from datetime import datetime, timedelta
import pandas as pd
from functools import wraps
import bcrypt  # For password hashing
import jwt    # JSON Web Tokens for authentication
import os
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins (for development)

# Secret key for JWT (keep it safe!)
app.config['SECRET_KEY'] = 'your_secret_key_here'


# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:c0st4m4gn4@localhost/trees_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#############################################################
#############################################################
#############################################################
##AUTHENTICATION SECTION
# User Model
# Ensure user model matches
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

# Create tables
with app.app_context():
    db.create_all()


# Helper: Generate JWT Token
def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=12)  # Token expires in 12 hours
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# Helper: Authenticate Requests
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization required'}), 401
        try:
            # Extract token (Bearer <token>)
            token = token.split()[1]
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['POST'])
def public_register():
    data = request.json

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username already taken'}), 409

    try:
        # Hash password and create user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password, role='user')

        # ✅ Add and commit without flush/close (safer for PostgreSQL)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': f'User {username} registered successfully!'}), 201
    except Exception as e:
        # Rollback if there's an error
        db.session.rollback()
        app.logger.error(f"Error registering user: {e}")
        return jsonify({'message': f'Error registering user: {str(e)}'}), 500


# ✅ Admin-Only Registration (Authorization Required)
@app.route('/admin/register', methods=['POST'])
@login_required
def admin_register():
    if request.user['role'] != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already taken'}), 409

    # Hash password and create new user (can specify user/admin role)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username=username, password_hash=hashed_password, role=role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': f'User {username} registered successfully by admin!'}), 201

# ✅ User Login (Returns JWT Token)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = generate_token(user)
    return jsonify({'token': token})

# ✅ Protected Example (Test Access Control)
@app.route('/protected', methods=['GET'])
@login_required
def protected():
    return jsonify({
        'message': f'Hello, {request.user["username"]}! You are a {request.user["role"]}.'
    })


@app.route('/debug_users', methods=['GET'])
def debug_users():
    result = db.session.execute(text("SELECT current_schema();"))
    print("Current schema:", result.scalar())  # Debugging current schema
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'role': user.role} for user in users])
#############################################################
#############################################################
#############################################################
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
        full_address = data['address'] +" " + data['city']
        print("full address " + full_address)
        location = geolocator.geocode(full_address)
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
