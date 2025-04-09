#!/usr/bin/env python3
"""
Kafka producer for sending test messages to a Confluent Kafka topic.
Configured for SASL_SSL authentication.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from confluent_kafka import Producer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Confluent Kafka producer for sending messages to a topic.
    Configured with SASL_SSL security protocol.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        sasl_username: str,
        sasl_password: str,
        topic: str,
        client_id: Optional[str] = None,
    ):
        """
        Initialize the Kafka producer with SASL_SSL configuration.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            sasl_username: SASL username for authentication
            sasl_password: SASL password for authentication
            topic: Default topic to produce messages to
            client_id: Optional client ID for the producer
        """
        self.topic = topic
        
        # Configure the producer with SASL_SSL
        config = {
            'bootstrap.servers': bootstrap_servers,
            'security.protocol': 'SASL_PLAINTEXT',
            # 'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': sasl_username,
            'sasl.password': sasl_password,
            # Set sensible defaults for reliable delivery
            'acks': 'all',
            'retries': 5,
            'retry.backoff.ms': 500,
            'socket.keepalive.enable': True,
        }
        
        # Add client ID if provided
        if client_id:
            config['client.id'] = client_id
            
        # Create the producer instance
        self.producer = Producer(config)
        logger.info(f"Kafka producer initialized for topic: {topic}")

    def delivery_callback(self, err, msg):
        """
        Callback function called once for each produced message to
        indicate success or failure.
        
        Args:
            err: Error (if any)
            msg: Message metadata
        """
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(
                f"Message delivered to {msg.topic()} [{msg.partition()}] "
                f"at offset {msg.offset()}"
            )

    def produce(
        self, 
        message: Dict[str, Any], 
        key: Optional[str] = None, 
        headers: Optional[Dict[str, str]] = None,
        topic: Optional[str] = None,
    ) -> None:
        """
        Produce a message to Kafka.
        
        Args:
            message: Message payload as a dictionary (will be serialized to JSON)
            key: Optional message key
            headers: Optional message headers
            topic: Optional topic override (uses instance default if not specified)
        """
        # Use the provided topic or fall back to the default
        target_topic = topic or self.topic
        
        # Serialize the message to JSON
        value = json.dumps(message).encode('utf-8')
        
        # Convert key to bytes if it's not None
        key_bytes = key.encode('utf-8') if key else None
        
        # Convert headers to the format expected by confluent-kafka
        header_list = []
        if headers:
            header_list = [(k, v.encode('utf-8')) for k, v in headers.items()]
        
        # Produce the message
        self.producer.produce(
            topic=target_topic,
            value=value,
            key=key_bytes,
            headers=header_list,
            callback=self.delivery_callback,
        )
        
        # Poll to handle delivery callbacks
        self.producer.poll(0)
        
        logger.info(f"Sent message to topic {target_topic}: {message}")

    def flush(self, timeout: int = 10) -> None:
        """
        Wait for all messages to be delivered.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            logger.warning(f"{remaining} messages remain unflushed after timeout")
        else:
            logger.info("All messages flushed successfully")


def create_sample_producer_from_env() -> KafkaProducer:
    """
    Create a sample producer using environment variables.
    
    Required environment variables:
        KAFKA_BOOTSTRAP_SERVERS: Kafka bootstrap servers
        KAFKA_SASL_USERNAME: SASL username
        KAFKA_SASL_PASSWORD: SASL password
        KAFKA_TOPIC: Default topic
    
    Optional environment variables:
        KAFKA_CLIENT_ID: Client ID for the producer
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    sasl_username = os.getenv("KAFKA_SASL_USERNAME")
    sasl_password = os.getenv("KAFKA_SASL_PASSWORD")
    topic = os.getenv("KAFKA_TOPIC")
    client_id = os.getenv("KAFKA_CLIENT_ID")
    
    # Check if required variables are set
    if not all([bootstrap_servers, sasl_username, sasl_password, topic]):
        raise ValueError(
            "Missing required environment variables. Please check your .env file."
        )
    
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        sasl_username=sasl_username,
        sasl_password=sasl_password,
        topic=topic,
        client_id=client_id,
    )


if __name__ == "__main__":
    # Example usage of the producer
    try:
        producer = create_sample_producer_from_env()
        
        # Send some test messages
        test_messages = [
            {"id": 1, "status": "success", "data": "Test message 1"},
            {"id": 2, "status": "error", "data": "Test message 2"},
            {"id": 3, "priority": "high", "data": "Test message 3"},
            {"id": 4, "action": "reject", "data": "Test message 4"},
            {"id": 5, "simulate": "timeout", "data": "Test message 5"},
        ]
        
        for msg in test_messages:
            # Use the message ID as the key
            key = str(msg["id"])
            
            # Add a timestamp header
            headers = {"timestamp": str(int(time.time()))}
            
            # Produce the message
            producer.produce(message=msg, key=key, headers=headers)
            
            # Small delay between messages
            time.sleep(0.5)
        
        # Make sure all messages are delivered
        producer.flush()
        
    except Exception as e:
        logger.error(f"Error running producer example: {e}")
