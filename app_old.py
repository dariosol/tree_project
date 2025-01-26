from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
import pandas as pd
import os

app = Flask(__name__)

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:c0st4m4gn4@localhost/trees_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Tree model
class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text)
    species = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(10), nullable=False)
    comments = db.Column(db.Text)
    geom = db.Column(Geometry('POINT', srid=4326), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Route to add a new tree
@app.route('/add_tree', methods=['POST'])
def add_tree():
    data = request.json
    new_tree = Tree(
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data['address'],
        species=data['species'],
        condition=data['condition'],
        comments=data.get('comments', ''),
        geom=f'SRID=4326;POINT({data["longitude"]} {data["latitude"]})'
    )
    db.session.add(new_tree)
    db.session.commit()
    return jsonify({'message': 'Tree added successfully!'}), 201

# Route to get all trees
@app.route('/trees', methods=['GET'])
def get_trees():
    trees = Tree.query.all()  # ✅ Fix: Define 'trees' before using it
    tree_list = [{
        'id': tree.id,
        'latitude': tree.latitude,
        'longitude': tree.longitude,
        'address': tree.address,
        'species': tree.species,
        'condition': tree.condition,
        'comments': tree.comments
    } for tree in trees]
    return jsonify(tree_list)

# Route to get a specific tree by ID
@app.route('/tree/<int:tree_id>', methods=['GET'])
def get_tree(tree_id):
    tree = Tree.query.get(tree_id)
    if not tree:
        return jsonify({'message': 'Tree not found'}), 404
    return jsonify({
        'id': tree.id,
        'latitude': tree.latitude,
        'longitude': tree.longitude,
        'address': tree.address,
        'species': tree.species,
        'condition': tree.condition,
        'comments': tree.comments
    })

# Route to filter trees by condition
@app.route('/trees/condition/<string:condition>', methods=['GET'])
def get_trees_by_condition(condition):
    trees = Tree.query.filter_by(condition=condition).all()
    tree_list = [{
        'id': tree.id,
        'latitude': tree.latitude,
        'longitude': tree.longitude,
        'address': tree.address,
        'species': tree.species,
        'condition': tree.condition,
        'comments': tree.comments
    } for tree in trees]
    return jsonify(tree_list)

# Route to export trees as CSV
@app.route('/export', methods=['GET'])
def export_trees():
    trees = Tree.query.all()
    df = pd.DataFrame([{
        'ID': tree.id,
        'Latitude': tree.latitude,
        'Longitude': tree.longitude,
        'Address': tree.address,
        'Species': tree.species,
        'Condition': tree.condition,
        'Comments': tree.comments
    } for tree in trees])
    
    file_path = 'trees_data.csv'
    df.to_csv(file_path, index=False)
    
    return send_file(file_path, as_attachment=True)


@app.route('/tree/<int:tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    tree = Tree.query.get(tree_id)
    if not tree:
        return jsonify({'message': 'Tree not found'}), 404
    
    db.session.delete(tree)
    db.session.commit()
    
    return jsonify({'message': f'Tree with ID {tree_id} deleted successfully!'}), 200


@app.route('/trees', methods=['DELETE'])
def delete_all_trees():
    try:
        num_rows_deleted = db.session.query(Tree).delete()
        db.session.commit()
        return jsonify({'message': f'All {num_rows_deleted} trees deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
