# test_update_prices.py
from datetime import datetime
from classes.classes import FragranceItem
from aux_functions.db_functions import insert_or_update_fragrances, get_all_fragrances
from my_flask_app.mongo import db

# Define the collection
collection = db["PerfumeDigitalTest"]

# Simulate price updates for the remaining fragrances
updated_fragrances = [
    FragranceItem(
        brand="TestBrand",
        fragrance_name="TestFragrance1",
        quantity=50,
        price_amount=17.00,  # Price dropped below alert threshold
        price_currency="€",
        link="http://testsite.com/fragrance1",
        website="TestSite",
        country=["PT"],
        last_updated_at=datetime.now(),
        is_set_or_pack="N",
        gender="Women",
        price_alert_threshold=18.00
    ),
    FragranceItem(
        brand="TestBrand",
        fragrance_name="TestFragrance2",
        quantity=75,
        price_amount=15.50,  # Price increased
        price_currency="€",
        link="http://testsite.com/fragrance2",
        website="TestSite",
        country=["PT"],
        last_updated_at=datetime.now(),
        is_set_or_pack="N",
        gender="Men",
        price_alert_threshold=12.00
    )
]

# Update prices in MongoDB
insert_or_update_fragrances(collection, updated_fragrances)
print("Prices updated.")

# Retrieve all fragrances to check the updates
all_fragrances = get_all_fragrances(collection)
for fragrance in all_fragrances:
    print(f"Fragrance: {fragrance.fragrance_name}, Price: {fragrance.price_amount}, Price History: {fragrance.price_history}, Price Changed: {fragrance.price_changed}, Price Alert Threshold: {fragrance.price_alert_threshold}")
