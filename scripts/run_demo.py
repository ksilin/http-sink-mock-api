#!/usr/bin/env python3
"""
Demo script to run both the HTTP server and test the producer.
This will start a FastAPI server in the background and then run
the producer to send test messages to Kafka.
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run HTTP Mock Server and producer demo"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--message-count",
        type=int,
        default=10,
        help="Number of messages to produce (default: 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between messages in seconds (default: 1.0)",
    )
    return parser.parse_args()


def main():
    """Main entry point for the demo script."""
    args = parse_args()
    
    # Get the absolute path to the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    try:
        logger.info("Starting HTTP Mock Server...")
        
        # Start the server in a separate process
        server_cmd = [
            sys.executable,
            "-m",
            "app.main",
            "--host",
            args.host,
            "--port",
            str(args.port),
            "--reload",
        ]
        server_process = subprocess.Popen(
            server_cmd,
            cwd=project_root,
            # Redirect stdout and stderr to the current process
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
        )
        
        # Start a thread to read and log output from the server process
        import threading
        
        def log_server_output():
            for line in server_process.stdout:
                print(f"[SERVER] {line.strip()}")
        
        output_thread = threading.Thread(target=log_server_output, daemon=True)
        output_thread.start()
        
        # Wait for the server to start
        logger.info("Waiting for server to start...")
        time.sleep(3)
        
        # Check if the server is running
        if server_process.poll() is not None:
            logger.error("Server failed to start")
            return
        
        logger.info(f"Server started on {args.host}:{args.port}")
        
        # Run the producer
        logger.info(f"Producing {args.message_count} test messages...")
        producer_cmd = [
            sys.executable,
            os.path.join(script_dir, "produce_test_messages.py"),
            "--count",
            str(args.message_count),
            "--delay",
            str(args.delay),
        ]
        producer_process = subprocess.run(
            producer_cmd,
            cwd=project_root,
            check=True,
        )
        
        logger.info("Producer completed successfully")
        
        # Keep the server running until the user presses Ctrl+C
        logger.info("Press Ctrl+C to stop the server and exit")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error running demo: {e}")
    finally:
        # Clean up
        if "server_process" in locals():
            logger.info("Stopping server...")
            server_process.send_signal(signal.SIGINT)
            server_process.wait(timeout=5)
            logger.info("Server stopped")


if __name__ == "__main__":
    main()
