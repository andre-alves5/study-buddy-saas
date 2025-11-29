# Use an official Python runtime as a parent image
FROM python:3.12-alpine

# Upgrade busybox to patch vulnerabilities
RUN apk upgrade --no-cache busybox

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY src/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY src/ .

# Run processor.py when the container launches
CMD ["python", "processor.py"]
