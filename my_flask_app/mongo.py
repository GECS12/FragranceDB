import certifi
import os

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from aux_functions.data_functions import read_excel, convert_df_to_fragrance_items
from aux_functions.db_functions import get_database, db_insert_update_remove, delete_collection


# Load environment variables from .env file
load_dotenv()

# MongoDB connection URI from environment variable
uri = os.getenv("MONGO_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'), tls=True, tlsCAFile=certifi.where())


# Function to test the connection
def test_connection():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error: {e}")

def insert_collection_from_excel():
    # Load database and collection
    db = client["FragrancesDatabase"]
    collection = db['PerfumesDigital']

    # Path to the Excel file
    excel_file_path = r'D:\Drive Folder\Fragrances_DB\scrapers\PerfumesDigital\data\PerfumesDigital on 25_Jun_2024 15h37m.xlsx'

    # Read the Excel file
    df = read_excel(excel_file_path)

    # Convert DataFrame to list of FragranceItem instances
    fragrances = convert_df_to_fragrance_items(df)

    # Insert the fragrances into MongoDB
    db_insert_update_remove(collection, fragrances)

if __name__ == "__main__":
    test_connection()
    # insert_collection_from_excel()
    delete_collection("PerfumesDigital")