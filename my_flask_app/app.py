from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import hashlib
import os
import sys
import certifi
from dotenv import load_dotenv
import re

# Ensure the base directory is in the sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from aux_functions.db_functions import *
from classes.classes import FragranceItem


load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection setup
uri = os.getenv("MONGO_URI")
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client['FragrancesDatabase']
collection_perfumes_digital = db['PerfumesDigital']
collection_perfumes_24h = db['Perfumes24h']
collection_perfume_clique = db['PerfumeClique']
users_collection = db['users']  # Add users collection for managing favorites


def get_all_fragrances():
    all_fragrances = []

    try:
        if collection_perfumes_digital.count_documents({}) > 0:
            all_fragrances.extend(list(collection_perfumes_digital.find({}, {'_id': 0, 'brand': 1,
                                                                             'clean_fragrance_name': 1, 'quantity': 1,
                                                                             'price_amount': 1, 'link': 1, 'website': 1,
                                                                             'gender': 1})))
    except Exception as e:
        print(f"Error querying PerfumesDigital: {e}")

    try:
        if collection_perfumes_24h.count_documents({}) > 0:
            all_fragrances.extend(list(collection_perfumes_24h.find({},
                                                                    {'_id': 0, 'brand': 1, 'clean_fragrance_name': 1,
                                                                     'quantity': 1, 'price_amount': 1, 'link': 1,
                                                                     'website': 1, 'gender': 1})))
    except Exception as e:
        print(f"Error querying Perfumes24h: {e}")

    try:
        if collection_perfume_clique.count_documents({}) > 0:
            all_fragrances.extend(list(collection_perfume_clique.find({},
                                                                      {'_id': 0, 'brand': 1, 'clean_fragrance_name': 1,
                                                                       'quantity': 1, 'price_amount': 1, 'link': 1,
                                                                       'website': 1, 'gender': 1})))
    except Exception as e:
        print(f"Error querying PerfumeClique: {e}")

    return all_fragrances


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def data():
    fragrances = get_all_fragrances()
    print(f"Querying all collections: found {len(fragrances)} items")  # Debug statement
    return jsonify({"data": fragrances})


@app.route('/autocomplete_brand', methods=['GET'])
def autocomplete_brand():
    query = request.args.get('query')
    all_brands = set()

    if query:
        regex = re.compile(f'{query}', re.IGNORECASE)
        collections = [collection_perfumes_digital, collection_perfumes_24h, collection_perfume_clique]

        for collection in collections:
            try:
                brands = collection.distinct("brand", {"brand": regex})
                all_brands.update(brands)
            except Exception as e:
                print(f"Error querying {collection.name}: {e}")

    sorted_brands = sorted(all_brands)  # Sort alphabetically
    print(f"Autocomplete brand query: {query}, found {len(sorted_brands)} brands")  # Debug statement
    return jsonify(sorted_brands)


@app.route('/autocomplete_fragrance', methods=['GET'])
def autocomplete_fragrance():
    query = request.args.get('query')
    all_fragrances = set()

    if query:
        regex = re.compile(f'{query}', re.IGNORECASE)
        collections = [collection_perfumes_digital, collection_perfumes_24h, collection_perfume_clique]

        for collection in collections:
            try:
                fragrances = collection.distinct("clean_fragrance_name", {"clean_fragrance_name": regex})
                all_fragrances.update(fragrances)
            except Exception as e:
                print(f"Error querying {collection.name}: {e}")

    sorted_fragrances = sorted(all_fragrances)  # Sort alphabetically
    print(f"Autocomplete fragrance query: {query}, found {len(sorted_fragrances)} fragrances")  # Debug statement
    return jsonify(sorted_fragrances)


@app.route('/search_by_brand', methods=['GET'])
def search_by_brand():
    query = request.args.get('query')
    all_fragrances = []

    if query:
        regex = re.compile('.*' + '.*'.join(query.split()) + '.*', re.IGNORECASE)
        collections = [collection_perfumes_digital, collection_perfumes_24h, collection_perfume_clique]

        for collection in collections:
            try:
                fragrances = list(collection.find({"brand": regex}, {'_id': 0}))
                all_fragrances.extend(fragrances)
            except Exception as e:
                print(f"Error querying {collection.name}: {e}")

    print(f"Search by brand query: {query}, found {len(all_fragrances)} items")  # Debug statement
    return jsonify({"data": all_fragrances})


@app.route('/search_by_fragrance', methods=['GET'])
def search_by_fragrance():
    query = request.args.get('query')
    all_fragrances = []

    if query:
        regex = re.compile('.*' + '.*'.join(query.split()) + '.*', re.IGNORECASE)
        collections = [collection_perfumes_digital, collection_perfumes_24h, collection_perfume_clique]

        for collection in collections:
            try:
                fragrances = list(collection.find({"clean_fragrance_name": regex}, {'_id': 0}))
                all_fragrances.extend(fragrances)
            except Exception as e:
                print(f"Error querying {collection.name}: {e}")

    print(f"Search by fragrance query: {query}, found {len(all_fragrances)} items")  # Debug statement
    return jsonify({"data": all_fragrances})


# User authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if username and password and email:
            users_collection.insert_one({"username": username, "password": password, "email": email, "favorites": []})
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')

        if username_or_email and password:
            user = users_collection.find_one({
                "$or": [{"username": username_or_email}, {"email": username_or_email}],
                "password": password
            })
            if user:
                session['username'] = user['username']
                return redirect(url_for('index'))

    return render_template('signin.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        user = users_collection.find_one({"username": session['username']})
        if request.method == 'POST':
            # Update price alert threshold
            fragrance_id = request.form.get('fragrance_id')
            price_alert_threshold = request.form.get('price_alert_threshold')
            if fragrance_id and price_alert_threshold:
                users_collection.update_one(
                    {"username": session['username'], "favorites._id": fragrance_id},
                    {"$set": {"favorites.$.price_alert_threshold": float(price_alert_threshold)}}
                )
        return render_template('profile.html', user=user)
    return redirect(url_for('signin'))


@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    if 'username' in session:
        fragrance = request.json
        if not fragrance.get('_id'):
            unique_string = f"{fragrance['brand']}{fragrance['clean_fragrance_name']}{fragrance['quantity']}{fragrance['price_amount']}{fragrance['website']}"
            fragrance['_id'] = hashlib.md5(unique_string.encode()).hexdigest()
        fragrance_id = fragrance.get('_id')
        if fragrance_id:
            try:
                users_collection.update_one(
                    {"username": session['username']},
                    {"$addToSet": {"favorites": fragrance}}
                )
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        return jsonify({"success": False, "error": "Fragrance ID missing"}), 400
    return jsonify({"success": False, "error": "Unauthorized"}), 401


if __name__ == '__main__':
    #export_collections_to_excel("collections.xlsx")
    app.run(debug=True)
