# Pharmacy AI Backend

A simple FastAPI backend for pharmacy AI application with Heroku deployment.

## Features

- FastAPI web framework
- CORS enabled for frontend integration
- Health check endpoints
- Ready for Heroku deployment

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check

## Interactive API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Heroku Deployment

1. Install Heroku CLI
2. Login to Heroku: `heroku login`
3. Create app: `heroku create your-app-name`
4. Deploy: `git push heroku main`

## Environment Variables

- `PORT` - Server port (automatically set by Heroku)

## Project Structure

```
pharmacy-ai/
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies
├── Procfile         # Heroku process file
├── runtime.txt      # Python version for Heroku
└── README.md        # This file
```
