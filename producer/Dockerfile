FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the Kafka producer script
COPY kafka_producer.py .

# Install dependencies directly
RUN pip install --no-cache-dir kafka-python

# Set the command to execute the script
CMD ["python", "kafka_producer.py"]
