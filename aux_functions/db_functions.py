import logging
from pymongo import UpdateOne, DeleteOne
from bson import ObjectId
from classes.classes import FragranceItem
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
load_dotenv()
# Enable detailed logging
#logging.basicConfig(level=logging.DEBUG)

DATABASE_NAME = "FragrancesDatabase"

#retorna o user + pass mongo
def get_MongoDB_URI():
    uri = os.getenv("MONGO_URI")
    return print((f"MongoDB URI: {uri}"))

#ligar a db
def get_database():
    # Load the MongoDB URI from environment variables
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)

    # Specify your database name
    database_name = DATABASE_NAME  # Change this to your database name
    db = client[database_name]
    return db

def test_mongo_connection():
    uri = os.getenv("MONGO_URI")
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'), tls=True, tlsCAFile=certifi.where())
    # Access the database
    db = client[DATABASE_NAME]
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error: {e}")



# Apagar uma tabela duma db da Mongo (collection)
def delete_collection(collection_name):
    db = get_database()
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        print(f"Collection '{collection_name}' has been deleted.")
    else:
        print(f"Collection '{collection_name}' does not exist.")


def fragrance_item_to_dict(fragrance):
    return fragrance.to_dict()


def insert_or_update_fragrances(collection, fragrances):
    operations = []
    new_count = 0
    update_count = 0

    new_fragrances = []
    updated_fragrances = []
    removed_fragrances = []

    existing_links = set()
    for fragrance in fragrances:
        current_time = datetime.now()
        price_history_entry = {"price": fragrance.price_amount, "date": current_time}
        existing_links.add(fragrance.link)

        # Fetch existing document
        existing_doc = collection.find_one({"link": fragrance.link})

        if existing_doc:
            # Update price history
            price_history = existing_doc.get("price_history", [])
            price_history.append(price_history_entry)

            # Check for price change
            if existing_doc["price_amount"] != fragrance.price_amount:
                fragrance.price_changed = True
                update_count += 1
                updated_fragrances.append(fragrance.fragrance_name)
            else:
                fragrance.price_changed = False

            fragrance.price_history = price_history

            # Check for price drop alert
            if fragrance.price_alert_threshold and fragrance.price_amount < fragrance.price_alert_threshold:
                print(
                    f"Alert! Price drop for {fragrance.fragrance_name}: {fragrance.price_amount}{fragrance.price_currency}")
        else:
            # New document, initialize price history
            fragrance.price_history = [price_history_entry]
            fragrance.price_changed = False
            new_count += 1
            new_fragrances.append(fragrance.fragrance_name)

        operations.append(
            UpdateOne(
                {"link": fragrance.link},
                {"$set": fragrance_item_to_dict(fragrance)},
                upsert=True
            )
        )

    # Perform bulk write operations for insertions/updates
    if operations:
        collection.bulk_write(operations)

    # Remove fragrances that are not in the current scrape
    all_links_in_db = {doc['link'] for doc in collection.find({}, {"link": 1})}
    links_to_remove = all_links_in_db - existing_links
    remove_count = len(links_to_remove)
    if links_to_remove:
        removed_fragrances = [doc['fragrance_name'] for doc in collection.find({"link": {"$in": list(links_to_remove)}})]
        collection.bulk_write([DeleteOne({"link": link}) for link in links_to_remove])

    print(f"New fragrances inserted: {new_count}")
    print(f"Fragrances updated: {update_count}")
    print(f"Fragrances removed: {remove_count}")

    if new_count > 0:
        count_inserted = 0
        print("Inserted fragrances:")
        for name in new_fragrances:
            count_inserted = count_inserted + 1
            print(str(count_inserted) + " - " + name)

    if update_count > 0:
        count_updated = 0
        print("Updated fragrances:")
        for name in updated_fragrances:
            count_updated = count_updated + 1
            print(str(count_updated) + " - " + name)

    if remove_count > 0:
        count_removed = 0
        print("Removed fragrances:")
        for name in removed_fragrances:
            count_removed = count_removed + 1
            print(str(count_removed) + " - " + name)



def get_all_fragrances(collection):
    return [FragranceItem(**{key: value for key, value in fragrance.items() if key != '_id'}) for fragrance in
            collection.find()]


def get_fragrance_by_id(collection, fragrance_id):
    fragrance = collection.find_one({"_id": ObjectId(fragrance_id)})
    if fragrance:
        del fragrance['_id']  # Remove the _id field
    return FragranceItem(**fragrance) if fragrance else None

# Update the brand of fragrances in the collection
def update_db_brand(collection, old_brand, new_brand):
    result = collection.update_many(
        {"brand": old_brand},
        {"$set": {"brand": new_brand}}
    )
    return result.matched_count, result.modified_count

def export_collections_to_excel(output_file):
    db = get_database()
    collections = db.list_collection_names()

    writer = pd.ExcelWriter(output_file, engine='openpyxl')

    for collection_name in collections:
        collection = db[collection_name]
        data = list(collection.find())
        if data:
            df = pd.DataFrame(data)
            df.drop(columns=['_id'], inplace=True, errors='ignore')  # Remove MongoDB ID field if it exists
            df.to_excel(writer, sheet_name=collection_name, index=False)

    writer.save()
    print(f"Database has been exported to '{output_file}'.")