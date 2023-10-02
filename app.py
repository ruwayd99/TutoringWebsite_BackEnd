from flask import Flask, request, jsonify, send_file
from flask_pymongo import PyMongo
from gridfs import GridFS
from bson import ObjectId
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

# Loading environment variables from .env file
load_dotenv()

# Retrieving my MongoDB URI from the environment variable
mongo_uri = os.environ.get('MONGO_URI')

if not mongo_uri:
    raise ValueError('MONGO_URI is not set in the .env file')

# Custom JSON encoder class
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Serialize ObjectId as a string
        return super().default(obj)

app = Flask(__name__)
app.config['MONGO_URI'] = mongo_uri
mongo = PyMongo(app)
fs = GridFS(mongo.db)

CORS(app)  # Enable CORS for the entire app
app.json_encoder = CustomJSONEncoder  # Set the custom JSON encoder

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        file_id = fs.put(file, filename=file.filename)
        return jsonify({'message': 'File uploaded successfully', 'file_id': str(file_id)})
    return jsonify({'message': 'No file provided'}), 400

@app.route('/files', methods=['GET'])
def get_files():
    files = list(mongo.db.fs.files.find())
    serialized_files = [{'_id': str(file['_id']), 'filename': file['filename']} for file in files]
    
    #Download URL for each file
    for file in serialized_files:
        file['download_url'] = f'/file/{file["_id"]}'
    
    return jsonify({'files': serialized_files})

@app.route('/file/<file_id>', methods=['GET'])
def download_file(file_id):
    file = fs.find_one({"_id": ObjectId(file_id)})
    if file:
        response = send_file(file, as_attachment=True, download_name=file.filename)
        return response
    return jsonify({'message': 'File not found'}), 404

@app.route('/file/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    file = fs.find_one({"_id": ObjectId(file_id)})
    if file:
        fs.delete(file._id)
        return jsonify({'message': 'File deleted successfully'})
    return jsonify({'message': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
