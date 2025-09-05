# Inbound Carrier Sales AI API

A Flask-based REST API for managing carrier sales operations, including load searching and carrier call tracking.

## Features

- **Load Search**: Search for loads by equipment type
- **Carrier Calls**: Create and retrieve carrier call records with flexible schema
- **Carrier Verification**: Verify carrier MC numbers via FMCSA API
- **MongoDB Integration**: Persistent data storage with MongoDB Atlas
- **API Key Authentication**: Secure endpoints with API key validation

## Docker Setup

### Prerequisites

- Docker and Docker Compose installed
- MongoDB Atlas account (or local MongoDB instance)
- Environment variables configured

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Configuration
API_SECRET_KEY=your-secret-api-key
FMCSA_API_KEY=your-fmcsa-api-key

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
DATABASE_NAME=happyrobot
LOADS_COLLECTION_NAME=loads
CARRIERS_CALLS_COLLECTION_NAME=carriers_calls

# Flask Configuration
FLASK_ENV=development
PORT=5000
DEBUG=true
```

### Quick Start with Docker Compose

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd inbound_carrier_sales_ai
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API:**
   - API Base URL: `http://localhost:5000`
   - Health Check: `http://localhost:5000/health`

### Manual Docker Commands

1. **Build the Docker image:**
   ```bash
   docker build -t inbound-carrier-sales-api .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name inbound-carrier-sales-api \
     -p 5000:5000 \
     --env-file .env \
     inbound-carrier-sales-api
   ```

3. **View logs:**
   ```bash
   docker logs inbound-carrier-sales-api
   ```

4. **Stop and remove:**
   ```bash
   docker stop inbound-carrier-sales-api
   docker rm inbound-carrier-sales-api
   ```

## API Endpoints

### Authentication
All endpoints require an `X-API-Key` header with your API secret key.

### Available Endpoints

- `GET /health` - Health check endpoint
- `POST /verify-carrier` - Verify carrier MC number
- `POST /search-loads` - Search loads by equipment type
- `GET /carriers-calls` - Retrieve all carrier call records
- `POST /carriers-calls` - Create new carrier call record

### Example Usage

```bash
# Health Check
curl http://localhost:5000/health

# Search for loads
curl -X POST http://localhost:5000/search-loads \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"equipment_type": "dry_van"}'

# Create carrier call record
curl -X POST http://localhost:5000/carriers-calls \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"carrier_name": "ABC Trucking", "contact_person": "John Doe"}'

# Get all carrier calls
curl -X GET http://localhost:5000/carriers-calls \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

## Development

### Local Development with Docker

The docker-compose.yml is configured for development with:
- Hot reloading (volume mounts)
- Debug mode enabled
- Environment variable loading from `.env`

### Production Deployment

For production deployment:
1. Set `FLASK_ENV=production` and `DEBUG=false`
2. Use a production WSGI server (already configured with Gunicorn)
3. Ensure proper MongoDB connection string and security settings
4. Configure appropriate resource limits and health checks

## Monitoring

- **Health Check**: Built-in health check endpoint at `/health`
- **Docker Health Check**: Configured to check application health every 30 seconds
- **Logs**: Application logs available via `docker logs` command

## Security Features

- Non-root user in Docker container
- API key authentication on all endpoints
- MongoDB connection with proper timeout and SSL settings
- Environment variable-based configuration (no hardcoded secrets)