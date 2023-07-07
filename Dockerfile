# Use the official Python base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install OpenCV
RUN apt-get update && apt-get install -y python3-opencv

# Copy the app files to the working directory
COPY . /app

# Expose the port on which the app will run
EXPOSE 5003

# Set the entrypoint command to run the app
CMD ["python", "app.py"]