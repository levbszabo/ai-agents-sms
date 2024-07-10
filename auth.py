from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from fetch_secrets import get_secret
import os

secrets = get_secret()

# Set the secrets as environment variables
for key, value in secrets.items():
    os.environ[key] = value

# Define the API key header name
API_KEY_NAME = "JourneymanAI-SMS-API-Key"

# Create the APIKeyHeader dependency
api_key_header = APIKeyHeader(name=API_KEY_NAME)

# Dummy API key - replace with your actual key or fetch from environment variable
API_KEY = os.getenv("SMS_API_KEY")


async def get_api_key(request: Request):
    api_key = request.query_params.get("api_key")
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
