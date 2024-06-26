import hashlib
from datetime import datetime
from typing import List, Optional

class FragranceItem:
    def __init__(self, original_brand: str, original_fragrance_name: str, clean_brand: str,
                 website_clean_fragrance_name: Optional[str], final_clean_fragrance_name: str, quantity: Optional[float],
                 price_amount: float, price_currency: str, link: str, website: str, country: List[str],
                 last_updated_at: datetime, is_set_or_pack: bool, page: Optional[int], gender: Optional[str] = None,
                 price_history: Optional[List[dict]] = None, price_changed: Optional[bool] = False,
                 price_alert_threshold: Optional[float] = None, is_in_stock: Optional[bool] = None):
        self.original_brand = original_brand
        self.original_fragrance_name = original_fragrance_name
        self.clean_brand = clean_brand
        self.website_clean_fragrance_name = website_clean_fragrance_name
        self.final_clean_fragrance_name = final_clean_fragrance_name
        self.quantity = quantity
        self.price_amount = price_amount
        self.price_currency = price_currency
        self.link = link
        self.website = website
        self.country = country
        self.last_updated_at = last_updated_at
        self.is_set_or_pack = is_set_or_pack
        self.page = page
        self.gender = gender
        self.price_history = price_history if price_history else []
        self.price_changed = price_changed
        self.price_alert_threshold = price_alert_threshold
        self.is_in_stock = is_in_stock
        self._id = self.generate_id()

    def generate_id(self):
        # Generate ID based on core attributes
        unique_string = f"{self.original_brand}{self.original_fragrance_name}{self.quantity}{self.link}{self.website}{self.page}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "_id": self._id,
            "page": self.page,
            "is_set_or_pack": self.is_set_or_pack,
            "original_brand": self.original_brand,
            "clean_brand": self.clean_brand,
            "original_fragrance_name": self.original_fragrance_name,
            "website_clean_fragrance_name": self.website_clean_fragrance_name,
            "final_clean_fragrance_name": self.final_clean_fragrance_name,
            "quantity": float(f'{self.quantity:.2f}') if self.quantity is not None else None,
            "price_amount": self.price_amount,
            "price_currency": self.price_currency,
            "link": self.link,
            "website": self.website,
            "country": self.country,
            "last_updated_at": self.last_updated_at,
            "gender": self.gender,
            "price_history": self.price_history,
            "price_changed": self.price_changed,
            "price_alert_threshold": self.price_alert_threshold,
            "is_in_stock": self.is_in_stock
        }

    def __str__(self):
        return str(self.to_dict())

    def get_id(self):
        return self._id

    def get_link(self):
        return self.link

    def get_final_clean_fragrance_name(self):
        return self.final_clean_fragrance_name

    def get_is_set_or_pack(self):
        return self.is_set_or_pack