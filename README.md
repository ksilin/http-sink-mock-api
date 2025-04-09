# HTTP Sink Mock FastAPI Server

A simple HTTP endpoint for testing the Confluent HTTP Sink connector along with a Kafka producer to send test messages.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── producer.py
│   └── server.py
├── scripts/
│   ├── __init__.py
│   ├── produce_test_messages.py
│   └── run_demo.py
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── .env.example
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.8 or higher
- UV

## Installation

1. Clone this repository
2. Create a virtual environment and install dependencies with UV:

```bash
# Create and activate a virtual environment
# Install the project with UV
pip install uv
uv sync
```

3. Copy `.env.example` to `.env` and update it with your Kafka credentials:

```bash
cp .env.example .env
# Edit .env with your desired configuration
```

## Usage

### Running the HTTP Server

```bash
# Basic usage
python -m app.main

# With custom host and port
python -m app.main --host 127.0.0.1 --port 8080

# With auto-reload for development
python -m app.main --reload
```

### Using the Kafka Producer

```bash
# Run the producer example (sends test messages to Kafka)
python -m app.producer
```

### Using the Scripts

```bash
# Run the producer with custom parameters
python -m scripts.produce_test_messages --count 20 --delay 0.5

# Run a complete demo (starts server and producer)
python -m scripts.run_demo --port 8080 --message-count 15 --delay 1.0
```

### Running Tests

```bash
# Install test dependencies
uv pip install .[dev]

# Run tests
pytest
```

### Testing the HTTP Endpoint

The server will respond with different HTTP status codes based on the content of the messages. Here are some examples:

```bash
# Test default response (200 OK)
curl -X POST http://localhost:8000/api/messages -H "Content-Type: application/json" -d '{"id": 1, "message": "Hello, world!"}'

# Test error response (400 Bad Request)
curl -X POST http://localhost:8000/api/messages -H "Content-Type: application/json" -d '{"id": 2, "status": "error", "message": "Error message"}'

# Test high priority response (201 Created)
curl -X POST http://localhost:8000/api/messages -H "Content-Type: application/json" -d '{"id": 3, "priority": "high", "message": "High priority message"}'
```

### Configuring Response Behavior

You can update the server's response configuration via the `/config` endpoint:

```bash
# Get current configuration
curl -X GET http://localhost:8000/config

# Update configuration
curl -X POST http://localhost:8000/config -H "Content-Type: application/json" -d '{
  "default": {
    "response_code": 200, 
    "response_body": {"message": "Custom default response"}
  },
  "configurations": [
    {
      "match_field": "type",
      "match_value": "warning",
      "response_code": 429,
      "response_body": {"error": "Too many requests"}
    }
  ]
}'
```

## Confluent HTTP Sink Connector Configuration

When configuring your Confluent HTTP Sink connector, point it to this server:

```json
{
  "name": "HttpSinkConnector",
  "config": {
    "connector.class": "io.confluent.connect.http.HttpSinkConnector",
    "topics": "http-sink-test-topic",
    "http.api.url": "http://your-server-address:8000/api/messages",
    "tasks.max": "1",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false",
    "confluent.topic.bootstrap.servers": "your-bootstrap-servers",
    "confluent.topic.replication.factor": "3"
  }
}
```