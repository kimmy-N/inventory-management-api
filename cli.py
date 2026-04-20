"""
CLI Frontend for the Inventory Management System
=================================================
An interactive command-line interface that communicates with the
Flask REST API running at http://localhost:5000.

Usage:
    python cli.py
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

# ─────────────────────────────────────────────
#  Display Helpers
# ─────────────────────────────────────────────

def print_header(title):
    """Print a formatted section header."""
    width = 55
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_item(item):
    """Pretty-print a single inventory item."""
    print(f"\n  ID          : {item.get('id')}")
    print(f"  Product     : {item.get('product_name')}")
    print(f"  Brand       : {item.get('brands', 'N/A')}")
    print(f"  Barcode     : {item.get('barcode', 'N/A')}")
    print(f"  Categories  : {item.get('categories', 'N/A')}")
    print(f"  Quantity    : {item.get('quantity', 'N/A')}")
    print(f"  Price       : ${item.get('price', 0.0):.2f}")
    print(f"  Stock       : {item.get('stock', 0)} {item.get('unit', 'unit')}(s)")
    print(f"  Ingredients : {item.get('ingredients_text', 'N/A')[:60]}...")
    print("-" * 55)


def print_error(msg):
    print(f"\n  [ERROR] {msg}")


def print_success(msg):
    print(f"\n  [SUCCESS] {msg}")


# ─────────────────────────────────────────────
#  API call wrappers
# ─────────────────────────────────────────────

def api_get(path):
    """Make a GET request to the Flask API."""
    try:
        r = requests.get(BASE_URL + path, timeout=8)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to the API. Is Flask running? (python app.py)")
        return None, None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None, None


def api_post(path, payload=None):
    """Make a POST request to the Flask API."""
    try:
        r = requests.post(BASE_URL + path, json=payload, timeout=8)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to the API. Is Flask running? (python app.py)")
        return None, None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None, None


def api_patch(path, payload):
    """Make a PATCH request to the Flask API."""
    try:
        r = requests.patch(BASE_URL + path, json=payload, timeout=8)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to the API. Is Flask running? (python app.py)")
        return None, None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None, None


def api_delete(path):
    """Make a DELETE request to the Flask API."""
    try:
        r = requests.delete(BASE_URL + path, timeout=8)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to the API. Is Flask running? (python app.py)")
        return None, None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None, None


# ─────────────────────────────────────────────
#  CLI Actions
# ─────────────────────────────────────────────

def view_all_inventory():
    """Display all items in the inventory."""
    print_header("All Inventory Items")
    code, data = api_get("/inventory")
    if data is None:
        return
    if code == 200:
        items = data.get("inventory", [])
        if not items:
            print("  No items in inventory.")
            return
        print(f"  Total items: {data.get('count', 0)}")
        for item in items:
            print_item(item)
    else:
        print_error(data.get("message", "Unknown error"))


def view_single_item():
    """Fetch and display a single item by ID."""
    print_header("View Single Item")
    item_id = input("  Enter item ID: ").strip()
    if not item_id:
        print_error("Item ID cannot be empty.")
        return
    code, data = api_get(f"/inventory/{item_id}")
    if data is None:
        return
    if code == 200:
        print_item(data["item"])
    else:
        print_error(data.get("message", "Item not found"))


def search_local_inventory():
    """Search the local inventory by product name."""
    print_header("Search Inventory")
    query = input("  Enter search term: ").strip()
    if not query:
        print_error("Search term cannot be empty.")
        return
    code, data = api_get(f"/inventory/search?q={query}")
    if data is None:
        return
    if code == 200:
        results = data.get("results", [])
        print(f"\n  Found {data.get('count', 0)} result(s) for '{query}':")
        if not results:
            print("  No matching items found.")
        for item in results:
            print_item(item)
    else:
        print_error(data.get("message", "Search failed"))


def add_new_item():
    """Prompt user for details and add a new item to inventory."""
    print_header("Add New Inventory Item")
    print("  Fill in the details below (press Enter to skip optional fields):\n")

    product_name = input("  Product Name*: ").strip()
    if not product_name:
        print_error("Product name is required.")
        return

    brands = input("  Brand: ").strip()
    barcode = input("  Barcode: ").strip()

    price_str = input("  Price* (e.g. 2.99): ").strip()
    try:
        price = float(price_str)
    except ValueError:
        print_error("Invalid price. Must be a number.")
        return

    stock_str = input("  Stock quantity*: ").strip()
    try:
        stock = int(stock_str)
    except ValueError:
        print_error("Invalid stock. Must be a whole number.")
        return

    unit = input("  Unit (e.g. bottle, can, box) [default: unit]: ").strip() or "unit"
    quantity = input("  Package size (e.g. '1 L', '16 oz'): ").strip()
    categories = input("  Categories: ").strip()
    ingredients = input("  Ingredients: ").strip()

    payload = {
        "product_name": product_name,
        "brands": brands,
        "barcode": barcode,
        "price": price,
        "stock": stock,
        "unit": unit,
        "quantity": quantity,
        "categories": categories,
        "ingredients_text": ingredients,
    }

    code, data = api_post("/inventory", payload)
    if data is None:
        return
    if code == 201:
        print_success(data.get("message", "Item added!"))
        print_item(data["item"])
    else:
        print_error(data.get("message", "Failed to add item"))


def update_item():
    """Update price, stock, or other fields on an existing item."""
    print_header("Update Inventory Item")
    item_id = input("  Enter item ID to update: ").strip()
    if not item_id:
        print_error("Item ID cannot be empty.")
        return

    # Confirm the item exists first
    code, data = api_get(f"/inventory/{item_id}")
    if data is None:
        return
    if code != 200:
        print_error(data.get("message", "Item not found"))
        return

    current = data["item"]
    print(f"\n  Editing: {current['product_name']} (ID: {item_id})")
    print("  Press Enter to keep the current value.\n")

    updates = {}

    new_price = input(f"  New price (current: ${current.get('price', 0):.2f}): ").strip()
    if new_price:
        try:
            updates["price"] = float(new_price)
        except ValueError:
            print_error("Invalid price — keeping current value.")

    new_stock = input(f"  New stock (current: {current.get('stock', 0)}): ").strip()
    if new_stock:
        try:
            updates["stock"] = int(new_stock)
        except ValueError:
            print_error("Invalid stock — keeping current value.")

    new_name = input(f"  New product name (current: {current.get('product_name')}): ").strip()
    if new_name:
        updates["product_name"] = new_name

    new_brands = input(f"  New brand (current: {current.get('brands', 'N/A')}): ").strip()
    if new_brands:
        updates["brands"] = new_brands

    if not updates:
        print("\n  No changes made.")
        return

    code, data = api_patch(f"/inventory/{item_id}", updates)
    if data is None:
        return
    if code == 200:
        print_success(data.get("message", "Updated!"))
        print_item(data["item"])
    else:
        print_error(data.get("message", "Update failed"))


def delete_item():
    """Remove an item from the inventory after confirmation."""
    print_header("Delete Inventory Item")
    item_id = input("  Enter item ID to delete: ").strip()
    if not item_id:
        print_error("Item ID cannot be empty.")
        return

    # Show item before deleting
    code, data = api_get(f"/inventory/{item_id}")
    if data is None:
        return
    if code != 200:
        print_error(data.get("message", "Item not found"))
        return

    item = data["item"]
    print(f"\n  You are about to delete: {item['product_name']}")
    confirm = input("  Are you sure? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("  Deletion cancelled.")
        return

    code, data = api_delete(f"/inventory/{item_id}")
    if data is None:
        return
    if code == 200:
        print_success(data.get("message", "Deleted!"))
    else:
        print_error(data.get("message", "Deletion failed"))


def lookup_barcode():
    """Fetch product info from OpenFoodFacts by barcode (does not add to inventory)."""
    print_header("Lookup Product by Barcode (OpenFoodFacts)")
    barcode = input("  Enter barcode: ").strip()
    if not barcode:
        print_error("Barcode cannot be empty.")
        return
    code, data = api_get(f"/openfoodfacts/barcode/{barcode}")
    if data is None:
        return
    if code == 200:
        p = data["product"]
        print(f"\n  Product Name : {p.get('product_name')}")
        print(f"  Brand        : {p.get('brands')}")
        print(f"  Barcode      : {p.get('barcode')}")
        print(f"  Quantity     : {p.get('quantity')}")
        print(f"  Categories   : {p.get('categories')}")
        print(f"  Image        : {p.get('image_url')}")
        print(f"  Ingredients  : {p.get('ingredients_text', '')[:80]}...")
    else:
        print_error(data.get("message", "Lookup failed"))


def search_openfoodfacts():
    """Search OpenFoodFacts by product name."""
    print_header("Search OpenFoodFacts by Name")
    query = input("  Enter product name to search: ").strip()
    if not query:
        print_error("Search term cannot be empty.")
        return
    code, data = api_get(f"/openfoodfacts/search?q={query}")
    if data is None:
        return
    if code == 200:
        products = data.get("products", [])
        print(f"\n  Found {data.get('count', 0)} result(s) for '{query}':\n")
        for i, p in enumerate(products, 1):
            print(f"  [{i}] {p.get('product_name')} — {p.get('brands')}  (Barcode: {p.get('barcode')})")
    else:
        print_error(data.get("message", "Search failed"))


def add_from_openfoodfacts():
    """
    Fetch a product from OpenFoodFacts by barcode and add it directly
    to the inventory, prompting for price & stock.
    """
    print_header("Add Product from OpenFoodFacts to Inventory")
    barcode = input("  Enter barcode to look up & add: ").strip()
    if not barcode:
        print_error("Barcode cannot be empty.")
        return

    # Preview product first
    print("\n  Looking up barcode on OpenFoodFacts...")
    preview_code, preview_data = api_get(f"/openfoodfacts/barcode/{barcode}")
    if preview_data is None:
        return
    if preview_code != 200:
        print_error(preview_data.get("message", "Product not found on OpenFoodFacts"))
        return

    p = preview_data["product"]
    print(f"\n  Found: {p.get('product_name')} by {p.get('brands')}")
    print(f"  Barcode: {barcode} | Qty: {p.get('quantity')}")

    confirm = input("\n  Add this product to inventory? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("  Cancelled.")
        return

    price_str = input("  Set price (e.g. 3.99): ").strip()
    try:
        price = float(price_str)
    except ValueError:
        print_error("Invalid price.")
        return

    stock_str = input("  Set initial stock quantity: ").strip()
    try:
        stock = int(stock_str)
    except ValueError:
        print_error("Invalid stock.")
        return

    unit = input("  Unit (e.g. bottle, can, box) [default: unit]: ").strip() or "unit"

    payload = {"price": price, "stock": stock, "unit": unit}
    code, data = api_post(f"/openfoodfacts/add/{barcode}", payload)
    if data is None:
        return
    if code == 201:
        print_success(data.get("message", "Added to inventory!"))
        print_item(data["item"])
    else:
        print_error(data.get("message", "Failed to add item"))


# ─────────────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════════════╗
║      Inventory Management System — CLI           ║
╠══════════════════════════════════════════════════╣
║  INVENTORY                                       ║
║   1. View all inventory                          ║
║   2. View single item by ID                      ║
║   3. Search local inventory by name              ║
║   4. Add new item manually                       ║
║   5. Update item (price / stock / details)       ║
║   6. Delete item                                 ║
╠══════════════════════════════════════════════════╣
║  OPENFOODFACTS API                               ║
║   7. Lookup product by barcode (preview only)    ║
║   8. Search OpenFoodFacts by product name        ║
║   9. Fetch from OpenFoodFacts & add to inventory ║
╠══════════════════════════════════════════════════╣
║   0. Exit                                        ║
╚══════════════════════════════════════════════════╝
"""

ACTIONS = {
    "1": view_all_inventory,
    "2": view_single_item,
    "3": search_local_inventory,
    "4": add_new_item,
    "5": update_item,
    "6": delete_item,
    "7": lookup_barcode,
    "8": search_openfoodfacts,
    "9": add_from_openfoodfacts,
}


def main():
    """Entry point — display the main menu loop."""
    print("\n  Welcome to the Inventory Management System!")
    print(f"  Connecting to Flask API at: {BASE_URL}\n")

    while True:
        print(MENU)
        choice = input("  Enter your choice: ").strip()

        if choice == "0":
            print("\n  Goodbye!\n")
            sys.exit(0)
        elif choice in ACTIONS:
            ACTIONS[choice]()
        else:
            print_error("Invalid choice. Please enter a number from the menu.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()
