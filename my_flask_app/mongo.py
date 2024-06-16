# mongo.py
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection URI
uri = "mongodb+srv://gscrac12:Ff8gjnVXuRHYggV@fragrancedb.yguufac.mongodb.net/?retryWrites=true&w=majority"

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
