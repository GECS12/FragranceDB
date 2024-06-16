# classes.py

from datetime import datetime
from typing import List, Optional

class FragranceItem:
    def __init__(self, brand: str, fragrance_name: str, quantity: int, price_amount: float, price_currency: str, link: str, website: str, country: List[str], last_updated_at: datetime, is_set_or_pack: str, gender: Optional[str] = None, price_history: Optional[List[dict]] = None, price_changed: Optional[bool] = False, price_alert_threshold: Optional[float] = None):
        self.brand = brand
        self.fragrance_name = fragrance_name
        self.quantity = quantity
        self.price_amount = price_amount
        self.price_currency = price_currency
        self.link = link
        self.website = website
        self.country = country
        self.last_updated_at = last_updated_at
        self.is_set_or_pack = is_set_or_pack
        self.gender = gender
        self.price_history = price_history if price_history else []
        self.price_changed = price_changed
        self.price_alert_threshold = price_alert_threshold

    def to_dict(self):
        return {
            "brand": self.brand,
            "fragrance_name": self.fragrance_name,
            "quantity": self.quantity,
            "price_amount": self.price_amount,
            "price_currency": self.price_currency,
            "link": self.link,
            "website": self.website,
            "country": self.country,
            "last_updated_at": self.last_updated_at,
            "is_set_or_pack": self.is_set_or_pack,
            "gender": self.gender,
            "price_history": self.price_history,
            "price_changed": self.price_changed,
            "price_alert_threshold": self.price_alert_threshold
        }
