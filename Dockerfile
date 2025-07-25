# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for mysqlclient and pkg-config
RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install boto3

# Copy the rest of the working directory contents into the container at /app
COPY . /app

# Expose port 8001
EXPOSE 8001

# Run uvicorn server with secrets fetching
CMD ["sh", "-c", "python /app/fetch_secrets.py && uvicorn main:app --host 0.0.0.0 --port 8001"]
