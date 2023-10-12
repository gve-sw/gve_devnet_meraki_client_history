# Use a base image
FROM python:3.11.4

# Set the working directory inside the container
WORKDIR /app

# Copy dependencies and install them
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# Copy the rest of the code inside the container
COPY . .

# Command to run the script with arguments
ENTRYPOINT ["python", "./app.py"]
