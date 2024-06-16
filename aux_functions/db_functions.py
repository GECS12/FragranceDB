import logging
from pymongo import UpdateOne, DeleteOne
from bson import ObjectId
from classes.classes import FragranceItem
from datetime import datetime

# Enable detailed logging
#logging.basicConfig(level=logging.DEBUG)


def fragrance_item_to_dict(fragrance):
    return fragrance.to_dict()


def insert_or_update_fragrances(collection, fragrances):
    operations = []
    new_count = 0
    update_count = 0

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
        collection.bulk_write([DeleteOne({"link": link}) for link in links_to_remove])

    print(f"New fragrances inserted: {new_count}")
    print(f"Fragrances updated: {update_count}")
    print(f"Fragrances removed: {remove_count}")


def get_all_fragrances(collection):
    return [FragranceItem(**{key: value for key, value in fragrance.items() if key != '_id'}) for fragrance in
            collection.find()]


def get_fragrance_by_id(collection, fragrance_id):
    fragrance = collection.find_one({"_id": ObjectId(fragrance_id)})
    if fragrance:
        del fragrance['_id']  # Remove the _id field
    return FragranceItem(**fragrance) if fragrance else None
