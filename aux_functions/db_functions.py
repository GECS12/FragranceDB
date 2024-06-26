import logging
from bson import ObjectId
from pymongo.errors import BulkWriteError
from classes.classes import FragranceItem
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import time
from pymongo import UpdateOne, DeleteOne, InsertOne, DeleteMany

load_dotenv()
# Enable detailed logging
#logging.basicConfig(level=logging.DEBUG)

DATABASE_NAME = "FragrancesDatabase"

def get_MongoDB_URI():
    uri = os.getenv("MONGO_URI")
    return print((f"MongoDB URI: {uri}"))

def get_database():
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    database_name = DATABASE_NAME
    db = client[database_name]
    return db

def add_db_collection(db, collection_name):
    collection = db[collection_name]
    print(f"Collection '{collection_name}' added to the database.")

def test_mongo_connection():
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri, server_api=ServerApi('1'), tls=True, tlsCAFile=certifi.where())
    db = client[DATABASE_NAME]
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error: {e}")

def delete_collection(collection_name):
    db = get_database()
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        print(f"Collection '{collection_name}' has been deleted.")
    else:
        print(f"Collection '{collection_name}' does not exist.")

def fragrance_item_to_dict(fragrance):
    return fragrance.to_dict()

def db_insert_update_remove(collection, fragrances, batch_size=500, delay=1):
    operations = []
    new_count = 0
    update_count = 0

    new_fragrances = []
    updated_fragrances = []
    removed_fragrances = []

    existing_ids = set()
    for fragrance in fragrances:
        current_time = datetime.now()
        price_history_entry = {"price": fragrance.price_amount, "date": current_time}
        existing_ids.add(fragrance.get_id())

        # Fetch existing document
        existing_doc = collection.find_one({"_id": fragrance.get_id()})

        if existing_doc:
            # Update price history
            price_history = existing_doc.get("price_history", [])
            price_history.append(price_history_entry)

            # Check for price change
            if existing_doc["price_amount"] != fragrance.price_amount:
                fragrance.price_changed = True
                update_count += 1
                updated_fragrances.append(fragrance.final_clean_fragrance_name)  # Updated line
            else:
                fragrance.price_changed = False

            fragrance.price_history = price_history

            # Check for price drop alert
            if fragrance.price_alert_threshold and fragrance.price_amount < fragrance.price_alert_threshold:
                print(f"Alert! Price drop for {fragrance.final_clean_fragrance_name}: {fragrance.price_amount}{fragrance.price_currency}")  # Updated line
        else:
            # New document, initialize price history
            fragrance.price_history = [price_history_entry]
            fragrance.price_changed = False
            new_count += 1
            new_fragrances.append(fragrance.final_clean_fragrance_name)  # Updated line

        fragrance_dict = fragrance.to_dict()
        if existing_doc:
            # Ensure the same _id is used for updating
            fragrance_dict['_id'] = existing_doc['_id']

        operations.append(
            UpdateOne(
                {"_id": fragrance.get_id()},
                {"$set": fragrance_dict},
                upsert=True
            )
        )

    # Remove fragrances that are not in the current scrape
    all_ids_in_db = {doc['_id'] for doc in collection.find({}, {"_id": 1})}
    ids_to_remove = all_ids_in_db - existing_ids
    remove_count = len(ids_to_remove)
    if ids_to_remove:
        removed_fragrances = [doc['final_clean_fragrance_name'] for doc in collection.find({"_id": {"$in": list(ids_to_remove)}})]  # Updated line
        try:
            collection.delete_many({"_id": {"$in": list(ids_to_remove)}})
        except BulkWriteError as bwe:
            print("Bulk write error occurred during removal:", bwe.details)

    # Perform batch write operations with delay
    if operations:
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            try:
                print(f"Executing batch write for {len(batch)} operations")  # Debug statement
                collection.bulk_write(batch)
            except BulkWriteError as bwe:
                print("Bulk write error occurred:", bwe.details)
            time.sleep(delay)

    print(f"New fragrances inserted: {new_count}")
    print(f"Fragrances updated: {update_count}")
    print(f"Fragrances removed: {remove_count}")

    if new_count > 0:
        count_inserted = 0
        #print("Inserted fragrances:")
        for name in new_fragrances:
            count_inserted += 1
            #print(f"{count_inserted} - {name}")

    if update_count > 0:
        count_updated = 0
        #print("Updated fragrances:")
        for name in updated_fragrances:
            count_updated += 1
            #print(f"{count_updated} - {name}")

    if remove_count > 0:
        count_removed = 0
        #print("Removed fragrances:")
        for name in removed_fragrances:
            count_removed += 1
            #print(f"{count_removed} - {name}")



def get_all_fragrances(collection):
    return [FragranceItem(**{key: value for key, value in fragrance.items() if key != '_id'}) for fragrance in
            collection.find()]

def get_fragrance_by_id(collection, fragrance_id):
    fragrance = collection.find_one({"_id": ObjectId(fragrance_id)})
    if fragrance:
        del fragrance['_id']  # Remove the _id field
    return FragranceItem(**fragrance) if fragrance else None

def update_db_brand(collection, old_brand, new_brand):
    result = collection.update_many(
        {"brand": old_brand},
        {"$set": {"brand": new_brand}}
    )
    return result.matched_count, result.modified_count

def export_collections_to_excel(output_file):
    db = get_database()
    collections = db.list_collection_names()

    all_data = []

    for collection_name in collections:
        collection = db[collection_name]
        data = list(collection.find())
        if data:
            df = pd.DataFrame(data)
            df['collection'] = collection_name  # Add a column to indicate the collection name
            all_data.append(df)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.drop(columns=['_id'], inplace=True, errors='ignore')  # Remove MongoDB ID field if it exists
        combined_df.to_excel(output_file, sheet_name='AllCollections', index=False)
        print(f"Database has been exported to '{output_file}'.")

def insert_user(db, user):
    users_collection = db["users"]
    users_collection.insert_one(user.to_dict())


