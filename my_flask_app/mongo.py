import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

# MongoDB connection URI from environment variable
uri = os.getenv("MONGO_URI")

# Debug: Print the URI to verify it's being read correctly
print(f"MongoDB URI: {uri}")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'), tls=True, tlsCAFile=certifi.where())

# Access the database
db = client["FragrancesDatabase"]

# Function to test the connection
def test_connection():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()