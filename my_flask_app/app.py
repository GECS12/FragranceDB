from flask import Flask, request, render_template, jsonify
from mongo import db
import os

app = Flask(__name__)

def search_fragrances(query):
    query_str = {"$regex": query, "$options": "i"}
    results = []
    for doc in db.PerfumeDigital.find({"$or": [{"fragrance_name": query_str}, {"website": query_str}]}):
        results.append([
            doc.get("brand", ""),
            doc.get("fragrance_name", ""),
            doc.get("quantity", ""),
            doc.get("price_amount", ""),
            doc.get("link", ""),
            doc.get("website", "")
        ])
    return results

def search_by_brand(brand):
    brand_str = {"$regex": brand, "$options": "i"}
    results = []
    for doc in db.PerfumeDigital.find({"brand": brand_str}):
        results.append([
            doc.get("brand", ""),
            doc.get("fragrance_name", ""),
            doc.get("quantity", ""),
            doc.get("price_amount", ""),
            doc.get("link", ""),
            doc.get("website", "")
        ])
    return results

def get_brand_suggestions(query):
    query_str = {"$regex": query, "$options": "i"}
    brands = set()
    for doc in db.PerfumeDigital.find({"brand": query_str}):
        brands.add(doc.get("brand", ""))
    return sorted(list(brands))

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '')
    suggestions = get_brand_suggestions(query)
    return jsonify(suggestions)

@app.route('/', methods=['GET', 'POST'])
def index():
    query = ""
    results = []
    if request.method == 'POST':
        if 'brand' in request.form:
            query = request.form['brand']
            results = search_by_brand(query)
        else:
            query = request.form['query']
            results = search_fragrances(query)
    return render_template('index.html', query=query, results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
