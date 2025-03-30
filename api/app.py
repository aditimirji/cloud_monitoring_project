from flask import Flask, request, jsonify
import time
import random
import logging
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# In-memory data for the API
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]

products = [
    {"id": 1, "name": "Laptop", "price": 999.99},
    {"id": 2, "name": "Phone", "price": 699.99},
    {"id": 3, "name": "Tablet", "price": 399.99},
    {"id": 4, "name": "Headphones", "price": 149.99},
    {"id": 5, "name": "Monitor", "price": 299.99}
]

orders = []

@app.before_request
def before_request():
    request.start_time = time.time()
    request.request_id = str(uuid.uuid4())

@app.after_request
def after_request(response):
    response_time = time.time() - request.start_time

    # Simulate occasional random errors
    if random.random() < 0.05:  # 5% chance of error
        status_code = random.choice([400, 401, 403, 404, 500])
        response.status_code = status_code
        error_message = f"Simulated error with status code {status_code}"
    else:
        error_message = None

    # Log request details
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request.request_id,
        "level": "ERROR" if error_message else "INFO",
        "message": error_message or "Request processed",
        "path": request.path,
        "method": request.method,
        "response_time": round(response_time * 1000, 2),  # Convert to ms
        "status_code": response.status_code
    }

    logger.info(json.dumps(log_data))
    return response

# Root Route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Cloud Monitoring API"}), 200

# API Endpoints
@app.route('/api/users', methods=['GET'])
def get_users():
    time.sleep(random.uniform(0.01, 0.2))
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    time.sleep(random.uniform(0.01, 0.1))
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    time.sleep(random.uniform(0.05, 0.3))
    data = request.json
    if not data or not all(k in data for k in ("name", "email")):
        return jsonify({"error": "Invalid data"}), 400
    
    new_id = max(u["id"] for u in users) + 1 if users else 1
    new_user = {
        "id": new_id,
        "name": data["name"],
        "email": data["email"]
    }
    users.append(new_user)
    return jsonify(new_user), 201

@app.route('/api/products', methods=['GET'])
def get_products():
    time.sleep(random.uniform(0.02, 0.15))
    return jsonify(products)

@app.route('/api/orders', methods=['POST'])
def create_order():
    time.sleep(random.uniform(0.1, 0.5))
    data = request.json
    if not data or not all(k in data for k in ("user_id", "product_ids")):
        return jsonify({"error": "Invalid data"}), 400
    
    user = next((u for u in users if u["id"] == data["user_id"]), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    valid_products = [p for p in products if p["id"] in data["product_ids"]]
    if len(valid_products) != len(data["product_ids"]):
        return jsonify({"error": "One or more products not found"}), 404
    
    total = sum(p["price"] for p in valid_products)
    new_id = max(o["id"] for o in orders) + 1 if orders else 1
    new_order = {
        "id": new_id,
        "user_id": data["user_id"],
        "products": valid_products,
        "total": total,
        "date": datetime.now().isoformat()
    }
    orders.append(new_order)
    return jsonify(new_order), 201

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

