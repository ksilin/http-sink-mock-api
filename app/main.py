#!/usr/bin/env python3
"""
Main entry point for the HTTP Mock FastAPI server.
"""

import argparse
import logging
import uvicorn

from app.server import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="HTTP Mock Server for testing Confluent HTTP Sink connector"
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
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    return parser.parse_args()


def main():
    """Run the FastAPI server"""
    args = parse_args()
    
    logger.info(
        f"Starting HTTP Mock Server on {args.host}:{args.port} "
        f"(reload: {args.reload})"
    )
    
    uvicorn.run(
        "app.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
