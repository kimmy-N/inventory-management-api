"""
Inventory Management System - Flask REST API
============================================
A RESTful API built with Flask to manage a product inventory.
Supports full CRUD operations and integrates with the OpenFoodFacts API
to enrich inventory items with real product data.
"""

from flask import Flask, jsonify, request
import requests as req
import uuid

# ─────────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────────
app = Flask(__name__)

# ─────────────────────────────────────────────
#  Mock Database (in-memory array)
#  Data modeled after OpenFoodFacts product schema
# ─────────────────────────────────────────────
inventory = [
    {
        "id": "1",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "barcode": "0025293004269",
        "ingredients_text": "Filtered water, almonds, cane sugar, vitamin E acetate, zinc gluconate",
        "quantity": "1 L",
        "categories": "Plant-based milks, Beverages",
        "image_url": "https://images.openfoodfacts.org/images/products/002/529/300/4269/front_en.jpg",
        "price": 3.99,
        "stock": 50,
        "unit": "bottle"
    },
    {
        "id": "2",
        "product_name": "Classic Peanut Butter",
        "brands": "Jif",
        "barcode": "0051500280287",
        "ingredients_text": "Roasted peanuts, sugar, palm oil, salt, mono and diglycerides",
        "quantity": "16 oz",
        "categories": "Spreads, Nut butters",
        "image_url": "https://images.openfoodfacts.org/images/products/005/150/028/0287/front_en.jpg",
        "price": 4.49,
        "stock": 35,
        "unit": "jar"
    },
    {
        "id": "3",
        "product_name": "Whole Grain Oats",
        "brands": "Quaker",
        "barcode": "0030000057704",
        "ingredients_text": "100% whole grain rolled oats",
        "quantity": "42 oz",
        "categories": "Breakfast cereals, Oats",
        "image_url": "https://images.openfoodfacts.org/images/products/003/000/005/7704/front_en.jpg",
        "price": 5.99,
        "stock": 20,
        "unit": "canister"
    },
    {
        "id": "4",
        "product_name": "Sparkling Water Lime",
        "brands": "LaCroix",
        "barcode": "0096619872602",
        "ingredients_text": "Carbonated water, natural lime flavor",
        "quantity": "12 fl oz",
        "categories": "Beverages, Sparkling water",
        "image_url": "https://images.openfoodfacts.org/images/products/009/661/987/2602/front_en.jpg",
        "price": 1.29,
        "stock": 100,
        "unit": "can"
    },
    {
        "id": "5",
        "product_name": "Dark Chocolate Bar 70%",
        "brands": "Lindt",
        "barcode": "0009542004710",
        "ingredients_text": "Chocolate, cocoa mass, cocoa powder, sugar, cocoa butter, vanilla extract",
        "quantity": "3.5 oz",
        "categories": "Chocolate, Confectionery",
        "image_url": "https://images.openfoodfacts.org/images/products/000/954/200/4710/front_en.jpg",
        "price": 2.99,
        "stock": 60,
        "unit": "bar"
    }
]


# ─────────────────────────────────────────────
#  Helper: Generate a unique ID
# ─────────────────────────────────────────────
def generate_id():
    """Generate a unique string ID for a new inventory item."""
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
#  Helper: Find item by ID
# ─────────────────────────────────────────────
def find_item(item_id):
    """Return the inventory item matching item_id, or None."""
    return next((item for item in inventory if item["id"] == item_id), None)


# ─────────────────────────────────────────────
#  OpenFoodFacts API Integration
# ─────────────────────────────────────────────
OPENFOODFACTS_BASE = "https://world.openfoodfacts.org"


def fetch_by_barcode(barcode):
    """
    Query the OpenFoodFacts API for a product by its barcode.
    Returns a simplified product dict or None if not found.
    """
    url = f"{OPENFOODFACTS_BASE}/api/v0/product/{barcode}.json"
    try:
        response = req.get(url, timeout=8)
        data = response.json()
        if data.get("status") == 1:
            p = data["product"]
            return {
                "product_name": p.get("product_name", "Unknown"),
                "brands": p.get("brands", "Unknown"),
                "barcode": barcode,
                "ingredients_text": p.get("ingredients_text", ""),
                "quantity": p.get("quantity", ""),
                "categories": p.get("categories", ""),
                "image_url": p.get("image_url", ""),
            }
    except req.exceptions.RequestException:
        return None
    return None


def fetch_by_name(name):
    """
    Search the OpenFoodFacts API for products matching a name.
    Returns a list of simplified product dicts (up to 5).
    """
    url = f"{OPENFOODFACTS_BASE}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
    }
    try:
        response = req.get(url, params=params, timeout=8)
        data = response.json()
        products = []
        for p in data.get("products", []):
            products.append({
                "product_name": p.get("product_name", "Unknown"),
                "brands": p.get("brands", "Unknown"),
                "barcode": p.get("code", ""),
                "ingredients_text": p.get("ingredients_text", ""),
                "quantity": p.get("quantity", ""),
                "categories": p.get("categories", ""),
                "image_url": p.get("image_url", ""),
            })
        return products
    except req.exceptions.RequestException:
        return []


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

# ── Health Check (helper route) ────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    """Health check / welcome route."""
    return jsonify({
        "message": "Inventory Management API is running",
        "version": "1.0",
        "endpoints": [
            "GET  /inventory",
            "GET  /inventory/<id>",
            "POST /inventory",
            "PATCH /inventory/<id>",
            "DELETE /inventory/<id>",
            "GET  /inventory/search?q=<name>",
            "GET  /openfoodfacts/barcode/<barcode>",
            "GET  /openfoodfacts/search?q=<name>",
            "POST /openfoodfacts/add/<barcode>",
        ]
    }), 200


# ── GET /inventory  →  List all inventory items ────────────────────
@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Return all items in the inventory."""
    return jsonify({
        "status": "success",
        "count": len(inventory),
        "inventory": inventory
    }), 200


# ── GET /inventory/<id>  →  Get a single item ─────────────────────
@app.route("/inventory/<string:item_id>", methods=["GET"])
def get_item(item_id):
    """Return a single inventory item by its ID."""
    item = find_item(item_id)
    if item is None:
        return jsonify({"status": "error", "message": f"Item '{item_id}' not found"}), 404
    return jsonify({"status": "success", "item": item}), 200


# ── GET /inventory/search  →  Search by product name ──────────────
@app.route("/inventory/search", methods=["GET"])
def search_inventory():
    """Search the local inventory by product name (query param: q)."""
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify({"status": "error", "message": "Query parameter 'q' is required"}), 400
    results = [i for i in inventory if query in i["product_name"].lower()]
    return jsonify({
        "status": "success",
        "query": query,
        "count": len(results),
        "results": results
    }), 200


# ── POST /inventory  →  Add a new item ────────────────────────────
@app.route("/inventory", methods=["POST"])
def add_item():
    """
    Add a new item to the inventory.
    Required fields: product_name, price, stock
    Optional fields: brands, barcode, ingredients_text, quantity, categories, image_url, unit
    """
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

    # Validate required fields
    required = ["product_name", "price", "stock"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    # Validate types
    try:
        price = float(data["price"])
        stock = int(data["stock"])
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "'price' must be a number and 'stock' must be an integer"}), 400

    new_item = {
        "id": generate_id(),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "barcode": data.get("barcode", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "quantity": data.get("quantity", ""),
        "categories": data.get("categories", ""),
        "image_url": data.get("image_url", ""),
        "price": price,
        "stock": stock,
        "unit": data.get("unit", "unit"),
    }

    inventory.append(new_item)
    return jsonify({
        "status": "success",
        "message": "Item added to inventory",
        "item": new_item
    }), 201


# ── PATCH /inventory/<id>  →  Update an item ──────────────────────
@app.route("/inventory/<string:item_id>", methods=["PATCH"])
def update_item(item_id):
    """
    Partially update an existing inventory item.
    Only the fields provided in the request body will be updated.
    The 'id' field cannot be changed.
    """
    item = find_item(item_id)
    if item is None:
        return jsonify({"status": "error", "message": f"Item '{item_id}' not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

    # Prevent changing the ID
    data.pop("id", None)

    # Validate numeric fields if provided
    if "price" in data:
        try:
            data["price"] = float(data["price"])
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "'price' must be a number"}), 400

    if "stock" in data:
        try:
            data["stock"] = int(data["stock"])
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "'stock' must be an integer"}), 400

    # Apply updates
    item.update(data)

    return jsonify({
        "status": "success",
        "message": "Item updated successfully",
        "item": item
    }), 200


# ── DELETE /inventory/<id>  →  Remove an item ─────────────────────
@app.route("/inventory/<string:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Remove an item from the inventory by its ID."""
    item = find_item(item_id)
    if item is None:
        return jsonify({"status": "error", "message": f"Item '{item_id}' not found"}), 404

    inventory.remove(item)
    return jsonify({
        "status": "success",
        "message": f"Item '{item['product_name']}' deleted from inventory"
    }), 200


# ── GET /openfoodfacts/barcode/<barcode>  →  Lookup by barcode ────
@app.route("/openfoodfacts/barcode/<string:barcode>", methods=["GET"])
def lookup_barcode(barcode):
    """
    Fetch product details from OpenFoodFacts using a barcode.
    Does NOT add to inventory — use POST /openfoodfacts/add/<barcode> for that.
    """
    product = fetch_by_barcode(barcode)
    if product is None:
        return jsonify({
            "status": "error",
            "message": f"No product found for barcode '{barcode}'"
        }), 404
    return jsonify({"status": "success", "product": product}), 200


# ── GET /openfoodfacts/search  →  Search by name ──────────────────
@app.route("/openfoodfacts/search", methods=["GET"])
def search_openfoodfacts():
    """
    Search OpenFoodFacts by product name (query param: q).
    Returns up to 5 matching products.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Query parameter 'q' is required"}), 400

    products = fetch_by_name(query)
    return jsonify({
        "status": "success",
        "query": query,
        "count": len(products),
        "products": products
    }), 200


# ── POST /openfoodfacts/add/<barcode>  →  Fetch & add to inventory ─
@app.route("/openfoodfacts/add/<string:barcode>", methods=["POST"])
def add_from_openfoodfacts(barcode):
    """
    Fetch a product from OpenFoodFacts by barcode and add it to the inventory.
    Optional JSON body: { "price": 1.99, "stock": 10, "unit": "box" }
    """
    product = fetch_by_barcode(barcode)
    if product is None:
        return jsonify({
            "status": "error",
            "message": f"No product found for barcode '{barcode}' on OpenFoodFacts"
        }), 404

    data = request.get_json(silent=True) or {}

    new_item = {
        "id": generate_id(),
        "product_name": product["product_name"],
        "brands": product["brands"],
        "barcode": barcode,
        "ingredients_text": product["ingredients_text"],
        "quantity": product["quantity"],
        "categories": product["categories"],
        "image_url": product["image_url"],
        "price": float(data.get("price", 0.0)),
        "stock": int(data.get("stock", 0)),
        "unit": data.get("unit", "unit"),
    }

    inventory.append(new_item)
    return jsonify({
        "status": "success",
        "message": f"'{new_item['product_name']}' added to inventory from OpenFoodFacts",
        "item": new_item
    }), 201


# ─────────────────────────────────────────────
#  Run
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
