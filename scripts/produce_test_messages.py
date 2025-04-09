#!/usr/bin/env python3
"""
Script to produce test messages to Kafka for HTTP Sink connector testing.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, List

# Add parent directory to path to allow importing the app modules
sys.path.insert(0, "..")

from app.producer import create_sample_producer_from_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Produce test messages to Kafka for HTTP Sink testing"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of messages to produce (default: 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between messages in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--message-file",
        type=str,
        help="JSON file containing message templates to use",
    )
    return parser.parse_args()


def get_default_messages() -> List[Dict]:
    """
    Get a list of default test messages that will trigger different
    HTTP response codes from the server.
    """
    return [
        {"id": 1, "status": "success", "data": "Test message 1"},
        {"id": 2, "status": "error", "data": "Test message 2"},
        {"id": 3, "priority": "high", "data": "Test message 3"},
        {"id": 4, "action": "reject", "data": "Test message 4"},
        {"id": 5, "simulate": "timeout", "data": "Test message 5"},
        {"id": 6, "simulate": "server_error", "data": "Test message 6"},
    ]


def load_messages_from_file(file_path: str) -> List[Dict]:
    """
    Load message templates from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing message templates
        
    Returns:
        List of message templates
    """
    try:
        with open(file_path, "r") as f:
            messages = json.load(f)
            
        if not isinstance(messages, list):
            logger.error("Message file must contain a JSON array of message objects")
            return get_default_messages()
            
        return messages
    except Exception as e:
        logger.error(f"Error loading message file: {e}")
        return get_default_messages()


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    try:
        # Create the producer using environment variables
        producer = create_sample_producer_from_env()
        
        # Get message templates
        if args.message_file:
            message_templates = load_messages_from_file(args.message_file)
            logger.info(f"Loaded {len(message_templates)} message templates from file")
        else:
            message_templates = get_default_messages()
            logger.info(f"Using {len(message_templates)} default message templates")
        
        # Produce messages
        logger.info(f"Producing {args.count} messages with {args.delay}s delay")
        
        for i in range(args.count):
            # Select a message template (cycling through the available templates)
            template_idx = i % len(message_templates)
            message = message_templates[template_idx].copy()
            
            # Add a unique ID if not present
            if "id" not in message:
                message["id"] = i + 1
            
            # Add a timestamp
            message["timestamp"] = int(time.time())
            
            # Use the message ID as the key
            key = str(message["id"])
            
            # Add some headers
            headers = {
                "timestamp": str(int(time.time())),
                "source": "test-producer",
                "batch": str(i // len(message_templates) + 1),
            }
            
            # Produce the message
            producer.produce(message=message, key=key, headers=headers)
            logger.info(f"Sent message {i+1}/{args.count}: {message}")
            
            # Small delay between messages
            if i < args.count - 1:
                time.sleep(args.delay)
        
        # Make sure all messages are delivered
        producer.flush()
        logger.info("All messages sent successfully")
        
    except KeyboardInterrupt:
        logger.info("Producer interrupted by user")
    except Exception as e:
        logger.error(f"Error running producer: {e}")


if __name__ == "__main__":
    main()
