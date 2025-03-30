# load_generator.py
import requests
import random
import time
import json
from concurrent.futures import ThreadPoolExecutor

API_BASE_URL = "http://api:5000/api"
NUM_WORKERS = 5
REQUEST_INTERVAL = 0.1  # seconds between requests per worker

# List of endpoints to hit
ENDPOINTS = [
    ("GET", "/users"),
    ("GET", "/users/1"),
    ("GET", "/users/2"),
    ("GET", "/users/999"),  # Will generate 404
    ("POST", "/users"),
    ("GET", "/products"),
    ("GET", "/products/1"),
    ("GET", "/products/999"),  # Will generate 404
    ("GET", "/orders"),
    ("POST", "/orders"),
    ("GET", "/orders/1"),
    ("GET", "/health")
]

# Sample data for POST requests
NEW_USERS = [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"},
    {"name": "Mike Johnson", "email": "mike@example.com"}
]

def create_order():
    user_id = random.randint(1, 3)
    num_products = random.randint(1, 3)
    product_ids = random.sample(range(1, 6), num_products)
    return {"user_id": user_id, "product_ids": product_ids}

def make_request():
    while True:
        method, endpoint = random.choice(ENDPOINTS)
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                if endpoint == "/users":
                    data = random.choice(NEW_USERS)
                elif endpoint == "/orders":
                    data = create_order()
                else:
                    data = {}
                
                response = requests.post(url, json=data, timeout=5)
            
            print(f"{method} {url} - Status: {response.status_code}")
            
        except Exception as e:
            print(f"Error making request to {url}: {str(e)}")
        
        time.sleep(REQUEST_INTERVAL)

def main():
    print("Starting load generator...")
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        for _ in range(NUM_WORKERS):
            executor.submit(make_request)

if __name__ == "__main__":
    main()
