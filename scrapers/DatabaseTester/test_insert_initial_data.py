# test_insert_initial_data.py
from datetime import datetime
from classes.classes import FragranceItem
from aux_functions.db_functions import insert_or_update_fragrances
from my_flask_app.mongo import db

# Define the collection
collection = db["PerfumeDigitalTest"]

# Create test data
test_fragrances = [
    FragranceItem(
        brand="TestBrand",
        fragrance_name="TestFragrance1",
        quantity=50,
        price_amount=20.00,
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
        price_amount=15.00,
        price_currency="€",
        link="http://testsite.com/fragrance2",
        website="TestSite",
        country=["PT"],
        last_updated_at=datetime.now(),
        is_set_or_pack="N",
        gender="Men",
        price_alert_threshold=12.00
    ),
    FragranceItem(
        brand="TestBrand",
        fragrance_name="TestFragrance3",
        quantity=100,
        price_amount=25.00,
        price_currency="€",
        link="http://testsite.com/fragrance3",
        website="TestSite",
        country=["PT"],
        last_updated_at=datetime.now(),
        is_set_or_pack="N",
        gender="Unisex",
        price_alert_threshold=20.00
    )
]

# Insert test data into MongoDB
insert_or_update_fragrances(collection, test_fragrances)
print("Initial test data inserted.")
