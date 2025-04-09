#!/usr/bin/env python3
"""
FastAPI server for testing Confluent HTTP Sink connector.
This server can be configured to return different HTTP response codes
based on the content of received JSON messages.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HTTP Mock Server",
    description="Mock HTTP server for testing Confluent HTTP Sink connector",
    version="0.1.0",
)

# Configuration to determine response codes based on message content
RESPONSE_CONFIGS = {
    # Default configuration
    "default": {
        "response_code": 200,
        "response_body": {"message": "Message received successfully"},
    },
    # Response configs based on message content matching
    "configurations": [
        {
            "match_field": "status",
            "match_value": "error",
            "response_code": 400,
            "response_body": {"error": "Bad request due to status=error"},
        },
        {
            "match_field": "priority",
            "match_value": "high",
            "response_code": 201,
            "response_body": {"message": "High priority message processed"},
        },
        {
            "match_field": "action",
            "match_value": "reject",
            "response_code": 422,
            "response_body": {"error": "Message rejected as requested"},
        },
        {
            "match_field": "simulate",
            "match_value": "timeout",
            "response_code": 504,
            "response_body": {"error": "Gateway timeout simulated"},
        },
        {
            "match_field": "simulate",
            "match_value": "server_error",
            "response_code": 500,
            "response_body": {"error": "Internal server error simulated"},
        },
    ],
}


class ResponseConfig(BaseModel):
    """Configuration for response settings"""
    match_field: str
    match_value: Any
    response_code: int
    response_body: Dict[str, Any]


class MockServerConfig(BaseModel):
    """Complete configuration for the mock server"""
    default: Dict[str, Any] = Field(
        default={
            "response_code": 200,
            "response_body": {"message": "Message received successfully"},
        }
    )
    configurations: List[ResponseConfig] = []


# Current server configuration
server_config = MockServerConfig(
    default=RESPONSE_CONFIGS["default"],
    configurations=[
        ResponseConfig(**config) for config in RESPONSE_CONFIGS["configurations"]
    ],
)


@app.get("/", status_code=200)
async def root():
    """Root endpoint that confirms the server is running"""
    return {"status": "ok", "message": "HTTP Mock Server is running"}


@app.post("/config", status_code=200)
async def update_configuration(config: MockServerConfig):
    """Update the server's response configuration"""
    global server_config
    server_config = config
    logger.info(f"Updated server configuration: {server_config}")
    return {"status": "ok", "message": "Configuration updated successfully"}


@app.get("/config", status_code=200)
async def get_configuration():
    """Get the current server configuration"""
    return server_config


@app.post("/{path:path}", status_code=200)
async def handle_message(request: Request, path: str):
    """
    Main endpoint that processes incoming messages and returns
    configured responses based on message content
    """
    try:
        # Get the raw request body
        body = await request.body()
        
        # Try to parse as JSON
        try:
            data = json.loads(body)
            logger.info(f"Received message at /{path}: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message at /{path}")
            # Return 400 for non-JSON messages
            return Response(
                content=json.dumps({"error": "Invalid JSON format"}),
                status_code=400,
                media_type="application/json",
            )

        # Check if the message matches any of our configured response rules
        for config in server_config.configurations:
            if (
                config.match_field in data
                and data[config.match_field] == config.match_value
            ):
                logger.info(
                    f"Matched rule: {config.match_field}={config.match_value}, "
                    f"returning status code {config.response_code}"
                )
                return Response(
                    content=json.dumps(config.response_body),
                    status_code=config.response_code,
                    media_type="application/json",
                )

        # If no match, use the default response
        logger.info(f"No matching rule found, using default response")
        return Response(
            content=json.dumps(server_config.default["response_body"]),
            status_code=server_config.default["response_code"],
            media_type="application/json",
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return Response(
            content=json.dumps({"error": f"Server error: {str(e)}"}),
            status_code=500,
            media_type="application/json",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
