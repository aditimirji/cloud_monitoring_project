import json
import time
import os
import sys
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093")
LOG_TOPIC = os.getenv("LOG_TOPIC", "application_logs")

LOG_FILE = LOG_FILE = "/Users/amankumar/Desktop/cloud_monitoring_project/load_generator/logfile.log"


# Function to create Kafka producer with retry logic
def create_kafka_producer():
    retries = 0
    max_retries = 10

    while retries < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3
            )
            logging.info(f"Successfully connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return producer
        except KafkaError as e:
            retries += 1
            wait_time = 5  # seconds
            logging.error(f"Failed to connect to Kafka (attempt {retries}/{max_retries}): {str(e)}")
            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    logging.critical("Failed to connect to Kafka after maximum retries")
    return None

def follow_file(file_path):
    """Generator function to read new lines as they are written to the file."""
    with open(file_path, "r") as file:
        file.seek(0, os.SEEK_END)  # Start at the end of the file
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.5)  # Wait for new logs
                continue
            yield line.strip()

# Main function to read logs from file and send to Kafka
def main():
    producer = create_kafka_producer()
    if not producer:
        sys.exit(1)

    logging.info(f"Starting to forward logs to Kafka topic: {LOG_TOPIC}")

    try:
        for line in follow_file(LOG_FILE):
            try:
                log_data = json.loads(line)
                producer.send(LOG_TOPIC, log_data)
                logging.info(f"Sent log to Kafka: {log_data}")
            except json.JSONDecodeError:
                logging.warning(f"Error parsing JSON log: {line}")
            except KafkaError as e:
                logging.error(f"Error sending log to Kafka: {str(e)}")

    except KeyboardInterrupt:
        logging.info("Log forwarder interrupted")
    finally:
        if producer:
            producer.flush()
            producer.close()
            logging.info("Kafka producer closed")

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        logging.error(f"Log file {LOG_FILE} not found. Make sure load_generator.py is running.")
        sys.exit(1)

    main()
