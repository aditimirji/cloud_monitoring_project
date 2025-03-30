# kafka_producer.py
import json
import time
import os
import sys
from kafka import KafkaProducer

# Configure Kafka producer
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
LOG_TOPIC = os.getenv('LOG_TOPIC', 'application_logs')

# Function to create Kafka producer with retry logic
def create_kafka_producer():
    retries = 0
    max_retries = 10
    
    while retries < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"Successfully connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return producer
        except Exception as e:
            retries += 1
            wait_time = 5  # seconds
            print(f"Failed to connect to Kafka (attempt {retries}/{max_retries}): {str(e)}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    print("Failed to connect to Kafka after maximum retries")
    return None

# Main function to read logs from stdin and send to Kafka
def main():
    producer = create_kafka_producer()
    if not producer:
        sys.exit(1)
    
    print(f"Starting to forward logs to Kafka topic: {LOG_TOPIC}")
    
    try:
        for line in sys.stdin:
            try:
                # Parse the JSON log line
                log_data = json.loads(line.strip())
                
                # Send to Kafka
                producer.send(LOG_TOPIC, log_data)
                
            except json.JSONDecodeError:
                print(f"Error parsing JSON log: {line.strip()}")
            except Exception as e:
                print(f"Error sending log to Kafka: {str(e)}")
        
    except KeyboardInterrupt:
        print("Log forwarder interrupted")
    finally:
        if producer:
            producer.flush()
            producer.close()
            print("Kafka producer closed")

if __name__ == "__main__":
    main()
