
# kafka_consumer.py
import json
import time
import os
import sys
import psycopg2
from psycopg2 import sql
from kafka import KafkaConsumer

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'logs')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
LOG_TOPIC = os.getenv('LOG_TOPIC', 'application_logs')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'log_processor')

def create_db_connection():
    """Create a database connection with retry logic"""
    retries = 0
    max_retries = 10
    
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print(f"Successfully connected to database at {DB_HOST}:{DB_PORT}/{DB_NAME}")
            return conn
        except Exception as e:
            retries += 1
            wait_time = 5  # seconds
            print(f"Failed to connect to database (attempt {retries}/{max_retries}): {str(e)}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    print("Failed to connect to database after maximum retries")
    return None

def setup_db_tables(conn):
    """Create necessary database tables if they don't exist"""
    try:
        with conn.cursor() as cur:
            # Create requests table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id SERIAL PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time FLOAT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT
                )
            """)
            
            # Create indices for faster queries
            cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests (timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_path ON requests (path)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_status_code ON requests (status_code)")
            
            conn.commit()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error setting up database tables: {str(e)}")
        conn.rollback()

def process_log(log_data, conn):
    """Process a log entry and store it in the database"""
    try:
        with conn.cursor() as cur:
            # Parse timestamp
            timestamp = log_data.get('timestamp')
            
            # Insert log into requests table
            cur.execute("""
                INSERT INTO requests (
                    request_id, timestamp, path, method, 
                    status_code, response_time, level, message
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log_data.get('request_id', ''),
                timestamp,
                log_data.get('path', ''),
                log_data.get('method', ''),
                log_data.get('status_code', 0),
                log_data.get('response_time', 0),
                log_data.get('level', 'INFO'),
                log_data.get('message', '')
            ))
            
            conn.commit()
    except Exception as e:
        print(f"Error processing log entry: {str(e)}")
        conn.rollback()

def create_kafka_consumer():
    """Create a Kafka consumer with retry logic"""
    retries = 0
    max_retries = 10
    
    while retries < max_retries:
        try:
            consumer = KafkaConsumer(
                LOG_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=CONSUMER_GROUP,
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                enable_auto_commit=True,
                auto_commit_interval_ms=5000
            )
            print(f"Successfully connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return consumer
        except Exception as e:
            retries += 1
            wait_time = 5  # seconds
            print(f"Failed to connect to Kafka (attempt {retries}/{max_retries}): {str(e)}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    print("Failed to connect to Kafka after maximum retries")
    return None

def main():
    """Main function to process logs from Kafka and store in database"""
    # Create database connection
    conn = create_db_connection()
    if not conn:
        sys.exit(1)
    
    # Setup database tables
    setup_db_tables(conn)
    
    # Create Kafka consumer
    consumer = create_kafka_consumer()
    if not consumer:
        conn.close()
        sys.exit(1)
    
    print(f"Starting to consume logs from Kafka topic: {LOG_TOPIC}")
    
    try:
        for message in consumer:
            try:
                log_data = message.value
                process_log(log_data, conn)
            except Exception as e:
                print(f"Error processing message: {str(e)}")
    
    except KeyboardInterrupt:
        print("Log consumer interrupted")
    finally:
        if consumer:
            consumer.close()
            print("Kafka consumer closed")
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    main()
