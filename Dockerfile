# Use an official Python runtime as a parent image
FROM python:3.12-alpine
# alpine or slim ?

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1

#DEBUG:
RUN ls -la

# Run app.py using python
#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "src/app.py"]
