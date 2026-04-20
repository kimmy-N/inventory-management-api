# Inventory Management System — Flask REST API

A RESTful inventory management system built with **Python + Flask**, featuring full CRUD operations, an interactive CLI, and real-time product data from the [OpenFoodFacts API](https://world.openfoodfacts.org/).

---

## 📦 Features

| Feature | Details |
|---|---|
| **Flask REST API** | 9 fully functional routes including CRUD + helper routes |
| **CRUD Operations** | GET, POST, PATCH, DELETE on `/inventory` |
| **OpenFoodFacts Integration** | Lookup by barcode, search by name, and import directly into inventory |
| **CLI Interface** | Interactive menu-driven command-line tool |
| **Unit Tests** | 30+ tests covering endpoints, helpers, and mocked external API calls |

---

## 🛠️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/kimmy-N/inventory-management-api.git
cd python-rest-api
```

### 2. (Optional) Create a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### Start the Flask API
```bash
python app.py
```
The API will run at: **http://localhost:5000**

### Start the CLI (in a separate terminal)
```bash
python cli.py
```

---

## 🔗 API Endpoints

### Inventory Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check & list of all endpoints |
| `GET` | `/inventory` | Fetch all inventory items |
| `GET` | `/inventory/<id>` | Fetch a single item by ID |
| `GET` | `/inventory/search?q=<name>` | Search local inventory by product name |
| `POST` | `/inventory` | Add a new item manually |
| `PATCH` | `/inventory/<id>` | Partially update an item |
| `DELETE` | `/inventory/<id>` | Remove an item |

### OpenFoodFacts Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/openfoodfacts/barcode/<barcode>` | Preview product by barcode |
| `GET` | `/openfoodfacts/search?q=<name>` | Search OpenFoodFacts by name |
| `POST` | `/openfoodfacts/add/<barcode>` | Fetch from OpenFoodFacts & add to inventory |

---

## 📋 API Usage Examples

### Get all inventory items
```bash
curl http://localhost:5000/inventory
```

### Get a single item
```bash
curl http://localhost:5000/inventory/1
```

### Add a new item
```bash
curl -X POST http://localhost:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Orange Juice", "brands": "Tropicana", "price": 3.49, "stock": 40, "unit": "bottle"}'
```

### Update an item's price and stock
```bash
curl -X PATCH http://localhost:5000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 4.99, "stock": 30}'
```

### Delete an item
```bash
curl -X DELETE http://localhost:5000/inventory/1
```

### Lookup product by barcode (OpenFoodFacts)
```bash
curl http://localhost:5000/openfoodfacts/barcode/0025293004269
```

### Search OpenFoodFacts by name
```bash
curl "http://localhost:5000/openfoodfacts/search?q=almond+milk"
```

### Fetch product from OpenFoodFacts and add to inventory
```bash
curl -X POST http://localhost:5000/openfoodfacts/add/0025293004269 \
  -H "Content-Type: application/json" \
  -d '{"price": 3.99, "stock": 20, "unit": "bottle"}'
```

---

## 💻 CLI Usage

Run the CLI in a terminal (Flask API must be running):

```bash
python cli.py
```

**Available menu options:**

```
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
```

### Example: Add a product from OpenFoodFacts
1. Choose option `9`
2. Enter a barcode (e.g. `0025293004269`)
3. Confirm the product details shown
4. Set the price and stock level
5. The product is added to inventory instantly

---

## 🧪 Running Tests

```bash
pytest test_app.py -v
```

**Test coverage includes:**
- `GET /inventory` — list all items
- `GET /inventory/<id>` — single item retrieval & 404 errors
- `GET /inventory/search` — local search with query param
- `POST /inventory` — add item with validation
- `PATCH /inventory/<id>` — partial updates & ID protection
- `DELETE /inventory/<id>` — deletion and 404 handling
- `GET /openfoodfacts/barcode/<barcode>` — mocked barcode lookup
- `GET /openfoodfacts/search` — mocked name search
- `POST /openfoodfacts/add/<barcode>` — mocked fetch & add to inventory
- Helper functions: `generate_id()`, `find_item()`, `fetch_by_barcode()`, `fetch_by_name()`

---

## 📁 Project Structure

```
python-rest-api/
├── app.py            # Flask REST API (all routes + OpenFoodFacts integration)
├── cli.py            # Interactive CLI frontend
├── test_app.py       # Unit tests (pytest + unittest.mock)
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## 🗂️ Mock Inventory Data Schema

Each item in the inventory array follows this structure (modeled after OpenFoodFacts):

```json
{
  "id": "unique-string-id",
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "barcode": "0025293004269",
  "ingredients_text": "Filtered water, almonds, cane sugar, ...",
  "quantity": "1 L",
  "categories": "Plant-based milks, Beverages",
  "image_url": "https://images.openfoodfacts.org/...",
  "price": 3.99,
  "stock": 50,
  "unit": "bottle"
}
```

---

## 🌐 External API Reference

This project uses the **OpenFoodFacts Open API** (no authentication required):
- Documentation: https://openfoodfacts.github.io/openfoodfacts-server/api/
- Product lookup by barcode: `GET https://world.openfoodfacts.org/api/v0/product/{barcode}.json`
- Product search: `GET https://world.openfoodfacts.org/cgi/search.pl?search_terms={name}&json=1`

---

## 👩‍💻 Author
**KIMBERLY AYIAKI**

Built as part of the Python REST API with Flask — Inventory Management System lab.

## 💡 Notes
- Built following RESTful patterns
