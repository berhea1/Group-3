"""
Counter API Implementation
"""
from flask import Flask, jsonify
from . import status
import re

app = Flask(__name__)

COUNTERS = {}

def counter_exists(name):
    """Check if counter exists"""
    return name in COUNTERS

@app.route('/counters/<name>', methods=['POST'])
def create_counter(name):
    """Create a counter"""
    if not re.match("^[a-zA-Z0-9]+$", name):
        return jsonify({"error": "Counter name must contain only letters and numbers"}), status.HTTP_400_BAD_REQUEST
    if counter_exists(name):
        return jsonify({"error": f"Counter {name} already exists"}), status.HTTP_409_CONFLICT
    COUNTERS[name] = 0
    return jsonify({name: COUNTERS[name]}), status.HTTP_201_CREATED

@app.route('/counters/<name>', methods=['DELETE'])
def delete_counter(name):
    """Delete a counter"""
    if counter_exists(name):
        del COUNTERS[name]
    return '', status.HTTP_204_NO_CONTENT

@app.route('/counters/<name>', methods=['GET'])
def get_counter(name):
    """Retrieve an existing counter"""
@app.route('/counters/<name>', methods=['GET'])
def get_counter(name):
    """Retrieve an existing counter"""
    if not counter_exists(name):
        return jsonify(
            {"error": f"Counter {name} not found"}
        ), status.HTTP_404_NOT_FOUND

    return jsonify({name: COUNTERS[name]}), status.HTTP_200_OK


@app.route('/counters/<name>', methods=['PUT'])
def increment_counter(name):
    """Increment an existing counter"""
    COUNTERS[name] += 1
    return jsonify({name: COUNTERS[name]}), status.HTTP_200_OK
