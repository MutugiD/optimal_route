# Fuel Planner API

A Django-based API for optimal fuel stop planning during long-distance travel. This API helps drivers plan their fuel stops efficiently by considering factors like distance, fuel prices, and vehicle range.

## Features

- Route optimization with fuel stop planning
- Real-time fuel price integration
- Rate limiting and API key authentication
- Docker support for easy deployment
- Comprehensive test suite
- Detailed API documentation

## Requirements

- Python 3.10 or higher
- Django 3.2.23
- OpenRoute API key
- Fuel price data CSV

## Installation

### Using pip

### From source

```bash
git clone https://github.com/MutugiD/optimal_route.git
cd optimal_route
pip install .
```

## Configuration

Create a `.env` file in your project root with the following variables:

```env
DEBUG=True
DJANGO_LOG_LEVEL=INFO
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=your-secret-key
API_KEY=your-api-key
OPENROUTE_API_KEY=your-api-key
ORS_ROUTE_PROFILE=driving-car
MAX_RANGE_MILES=500
FUEL_ECONOMY_MPG=10
STATION_SEARCH_RADIUS=5000
BUFFER_DISTANCE=1000
CACHE_DIR=cache
CACHE_TTL=3600
FUEL_PRICES_CSV=data/fuel-prices.csv
MAX_PAYLOAD_SIZE=1048576
RATE_LIMIT=100
```

## Usage

### API Endpoints

#### Optimize Route

```http
POST /api/optimize/
Content-Type: application/json
X-API-Key: your-api-key

{
    "start_point": {
        "latitude": 37.7749,
        "longitude": -122.4194
    },
    "end_point": {
        "latitude": 34.0522,
        "longitude": -118.2437
    }
}
```

### Security Features

- API Key Authentication
- Rate Limiting (60 requests/minute by default)
- Payload Size Limits (1MB by default)
- Request Validation

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv optimal_env
source optimal_env/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install .

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Running Tests

```bash
python manage.py test
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenRoute Service for routing data
- Django REST framework for API development
- All contributors and users of the project