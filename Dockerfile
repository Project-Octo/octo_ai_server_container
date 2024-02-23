# Use the official Python base image with version 3.11.6
FROM python:3.11.6

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY ./requirements.txt /app

# Install the project dependencies
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Copy the entire project to the working directory
COPY . .

# Expose the port on which the Flask app will run
EXPOSE 8080

# Set the entrypoint command to run the Flask app
CMD ["python", "server.py"]
