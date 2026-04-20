"""
Unit Tests — Inventory Management System
=========================================
Covers:
  - All Flask API endpoints (GET, POST, PATCH, DELETE)
  - Local inventory search helper route
  - OpenFoodFacts integration routes (mocked with unittest.mock)
  - CLI functions (mocked API calls)

Run with:
    pytest test_app.py -v
"""

import json
import pytest
from unittest.mock import patch, MagicMock

# Import the Flask app and the inventory list
import app as flask_app


# ─────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a Flask test client with a fresh inventory for each test."""
    flask_app.app.config["TESTING"] = True

    # Reset inventory to a known state before each test
    flask_app.inventory.clear()
    flask_app.inventory.extend([
        {
            "id": "1",
            "product_name": "Organic Almond Milk",
            "brands": "Silk",
            "barcode": "0025293004269",
            "ingredients_text": "Filtered water, almonds",
            "quantity": "1 L",
            "categories": "Beverages",
            "image_url": "",
            "price": 3.99,
            "stock": 50,
            "unit": "bottle"
        },
        {
            "id": "2",
            "product_name": "Classic Peanut Butter",
            "brands": "Jif",
            "barcode": "0051500280287",
            "ingredients_text": "Roasted peanuts, sugar",
            "quantity": "16 oz",
            "categories": "Spreads",
            "image_url": "",
            "price": 4.49,
            "stock": 35,
            "unit": "jar"
        }
    ])

    with flask_app.app.test_client() as c:
        yield c


# ─────────────────────────────────────────────
#  Tests: Health Check
# ─────────────────────────────────────────────

class TestHealthCheck:
    def test_index_returns_200(self, client):
        """GET / should return 200 with API info."""
        res = client.get("/")
        assert res.status_code == 200
        data = res.get_json()
        assert data["message"] == "Inventory Management API is running"
        assert "endpoints" in data


# ─────────────────────────────────────────────
#  Tests: GET /inventory
# ─────────────────────────────────────────────

class TestGetInventory:
    def test_get_all_items_returns_200(self, client):
        """GET /inventory should return 200 and a list of items."""
        res = client.get("/inventory")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert isinstance(data["inventory"], list)
        assert data["count"] == 2

    def test_get_all_items_has_correct_fields(self, client):
        """Each item in GET /inventory must include required fields."""
        res = client.get("/inventory")
        items = res.get_json()["inventory"]
        for item in items:
            assert "id" in item
            assert "product_name" in item
            assert "price" in item
            assert "stock" in item


# ─────────────────────────────────────────────
#  Tests: GET /inventory/<id>
# ─────────────────────────────────────────────

class TestGetSingleItem:
    def test_get_existing_item_returns_200(self, client):
        """GET /inventory/1 should return the correct item."""
        res = client.get("/inventory/1")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["item"]["id"] == "1"
        assert data["item"]["product_name"] == "Organic Almond Milk"

    def test_get_nonexistent_item_returns_404(self, client):
        """GET /inventory/999 should return 404."""
        res = client.get("/inventory/999")
        assert res.status_code == 404
        data = res.get_json()
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()


# ─────────────────────────────────────────────
#  Tests: GET /inventory/search
# ─────────────────────────────────────────────

class TestSearchInventory:
    def test_search_finds_matching_items(self, client):
        """GET /inventory/search?q=almond should return matching items."""
        res = client.get("/inventory/search?q=almond")
        assert res.status_code == 200
        data = res.get_json()
        assert data["count"] >= 1
        assert any("Almond" in i["product_name"] for i in data["results"])

    def test_search_no_results(self, client):
        """GET /inventory/search?q=xyz should return empty results."""
        res = client.get("/inventory/search?q=xyznotarealproduct123")
        assert res.status_code == 200
        data = res.get_json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_search_missing_query_returns_400(self, client):
        """GET /inventory/search without q param should return 400."""
        res = client.get("/inventory/search")
        assert res.status_code == 400
        data = res.get_json()
        assert data["status"] == "error"


# ─────────────────────────────────────────────
#  Tests: POST /inventory
# ─────────────────────────────────────────────

class TestAddItem:
    def test_add_valid_item_returns_201(self, client):
        """POST /inventory with valid data should return 201 and the new item."""
        payload = {
            "product_name": "Granola Bar",
            "brands": "Kind",
            "price": 1.99,
            "stock": 100,
            "unit": "bar"
        }
        res = client.post("/inventory", json=payload)
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"
        assert data["item"]["product_name"] == "Granola Bar"
        assert "id" in data["item"]

    def test_add_item_appears_in_inventory(self, client):
        """After POST /inventory, the new item should appear in GET /inventory."""
        payload = {"product_name": "Test Item", "price": 0.99, "stock": 5}
        client.post("/inventory", json=payload)
        res = client.get("/inventory")
        names = [i["product_name"] for i in res.get_json()["inventory"]]
        assert "Test Item" in names

    def test_add_item_missing_required_fields_returns_400(self, client):
        """POST /inventory without required fields should return 400."""
        payload = {"brands": "No Name"}  # Missing product_name, price, stock
        res = client.post("/inventory", json=payload)
        assert res.status_code == 400
        data = res.get_json()
        assert data["status"] == "error"
        assert "Missing required fields" in data["message"]

    def test_add_item_invalid_price_returns_400(self, client):
        """POST /inventory with a non-numeric price should return 400."""
        payload = {"product_name": "Bad Item", "price": "free", "stock": 10}
        res = client.post("/inventory", json=payload)
        assert res.status_code == 400

    def test_add_item_invalid_stock_returns_400(self, client):
        """POST /inventory with a non-integer stock should return 400."""
        payload = {"product_name": "Bad Item", "price": 1.99, "stock": "lots"}
        res = client.post("/inventory", json=payload)
        assert res.status_code == 400

    def test_add_item_no_body_returns_400(self, client):
        """POST /inventory with no body should return 400."""
        res = client.post("/inventory", content_type="application/json")
        assert res.status_code == 400


# ─────────────────────────────────────────────
#  Tests: PATCH /inventory/<id>
# ─────────────────────────────────────────────

class TestUpdateItem:
    def test_patch_price_and_stock(self, client):
        """PATCH /inventory/1 should update price and stock correctly."""
        payload = {"price": 9.99, "stock": 200}
        res = client.patch("/inventory/1", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["item"]["price"] == 9.99
        assert data["item"]["stock"] == 200

    def test_patch_product_name(self, client):
        """PATCH /inventory/1 can update the product name."""
        payload = {"product_name": "Oat Milk"}
        res = client.patch("/inventory/1", json=payload)
        assert res.status_code == 200
        assert res.get_json()["item"]["product_name"] == "Oat Milk"

    def test_patch_cannot_change_id(self, client):
        """PATCH /inventory/1 should ignore attempts to change the ID."""
        payload = {"id": "999", "stock": 10}
        res = client.patch("/inventory/1", json=payload)
        assert res.status_code == 200
        assert res.get_json()["item"]["id"] == "1"  # ID unchanged

    def test_patch_nonexistent_item_returns_404(self, client):
        """PATCH /inventory/999 should return 404."""
        res = client.patch("/inventory/999", json={"price": 1.00})
        assert res.status_code == 404

    def test_patch_invalid_price_returns_400(self, client):
        """PATCH with invalid price should return 400."""
        res = client.patch("/inventory/1", json={"price": "expensive"})
        assert res.status_code == 400

    def test_patch_invalid_stock_returns_400(self, client):
        """PATCH with invalid stock should return 400."""
        res = client.patch("/inventory/1", json={"stock": "many"})
        assert res.status_code == 400


# ─────────────────────────────────────────────
#  Tests: DELETE /inventory/<id>
# ─────────────────────────────────────────────

class TestDeleteItem:
    def test_delete_existing_item_returns_200(self, client):
        """DELETE /inventory/1 should succeed and remove the item."""
        res = client.delete("/inventory/1")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert "deleted" in data["message"].lower()

    def test_delete_removes_item_from_inventory(self, client):
        """After DELETE /inventory/1, item should not appear in GET /inventory."""
        client.delete("/inventory/1")
        res = client.get("/inventory")
        ids = [i["id"] for i in res.get_json()["inventory"]]
        assert "1" not in ids

    def test_delete_nonexistent_item_returns_404(self, client):
        """DELETE /inventory/999 should return 404."""
        res = client.delete("/inventory/999")
        assert res.status_code == 404
        assert res.get_json()["status"] == "error"


# ─────────────────────────────────────────────
#  Tests: OpenFoodFacts API — Barcode Lookup
# ─────────────────────────────────────────────

MOCK_OFF_RESPONSE = {
    "status": 1,
    "product": {
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "ingredients_text": "Filtered water, almonds, cane sugar",
        "quantity": "1 L",
        "categories": "Plant-based milks",
        "image_url": "https://example.com/image.jpg",
    }
}

MOCK_OFF_SEARCH_RESPONSE = {
    "products": [
        {
            "product_name": "Almond Milk",
            "brands": "Silk",
            "code": "0025293004269",
            "ingredients_text": "Filtered water, almonds",
            "quantity": "1 L",
            "categories": "Beverages",
            "image_url": "",
        }
    ]
}


class TestOpenFoodFactsBarcode:
    @patch("app.req.get")
    def test_barcode_lookup_success(self, mock_get, client):
        """GET /openfoodfacts/barcode/<barcode> returns product data when found."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_RESPONSE
        mock_get.return_value = mock_response

        res = client.get("/openfoodfacts/barcode/0025293004269")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["product"]["product_name"] == "Organic Almond Milk"

    @patch("app.req.get")
    def test_barcode_lookup_not_found(self, mock_get, client):
        """GET /openfoodfacts/barcode/<barcode> returns 404 when product is missing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0, "product": {}}
        mock_get.return_value = mock_response

        res = client.get("/openfoodfacts/barcode/0000000000000")
        assert res.status_code == 404
        assert res.get_json()["status"] == "error"

    @patch("app.req.get")
    def test_barcode_lookup_connection_error(self, mock_get, client):
        """GET /openfoodfacts/barcode/<barcode> returns 404 on network failure."""
        import requests as rq
        mock_get.side_effect = rq.exceptions.RequestException("Network error")

        res = client.get("/openfoodfacts/barcode/0025293004269")
        assert res.status_code == 404


# ─────────────────────────────────────────────
#  Tests: OpenFoodFacts API — Name Search
# ─────────────────────────────────────────────

class TestOpenFoodFactsSearch:
    @patch("app.req.get")
    def test_search_by_name_returns_products(self, mock_get, client):
        """GET /openfoodfacts/search?q=almond returns product list."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        res = client.get("/openfoodfacts/search?q=almond")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["count"] == 1
        assert data["products"][0]["product_name"] == "Almond Milk"

    def test_search_missing_query_returns_400(self, client):
        """GET /openfoodfacts/search without q param returns 400."""
        res = client.get("/openfoodfacts/search")
        assert res.status_code == 400

    @patch("app.req.get")
    def test_search_empty_results(self, mock_get, client):
        """GET /openfoodfacts/search?q=xyz returns empty list on no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"products": []}
        mock_get.return_value = mock_response

        res = client.get("/openfoodfacts/search?q=xyznotreal")
        assert res.status_code == 200
        assert res.get_json()["count"] == 0


# ─────────────────────────────────────────────
#  Tests: POST /openfoodfacts/add/<barcode>
#  (Fetch from OpenFoodFacts AND add to inventory)
# ─────────────────────────────────────────────

class TestAddFromOpenFoodFacts:
    @patch("app.req.get")
    def test_add_from_off_success(self, mock_get, client):
        """POST /openfoodfacts/add/<barcode> adds product to inventory."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_RESPONSE
        mock_get.return_value = mock_response

        payload = {"price": 3.99, "stock": 25, "unit": "bottle"}
        res = client.post("/openfoodfacts/add/0025293004269", json=payload)
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"
        assert data["item"]["product_name"] == "Organic Almond Milk"
        assert data["item"]["price"] == 3.99
        assert data["item"]["stock"] == 25
        assert "id" in data["item"]

    @patch("app.req.get")
    def test_add_from_off_appears_in_inventory(self, mock_get, client):
        """After POST /openfoodfacts/add/<barcode>, item appears in GET /inventory."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_RESPONSE
        mock_get.return_value = mock_response

        client.post("/openfoodfacts/add/0025293004269", json={"price": 3.99, "stock": 25})
        res = client.get("/inventory")
        names = [i["product_name"] for i in res.get_json()["inventory"]]
        assert "Organic Almond Milk" in names

    @patch("app.req.get")
    def test_add_from_off_product_not_found(self, mock_get, client):
        """POST /openfoodfacts/add/<barcode> returns 404 if product not found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0}
        mock_get.return_value = mock_response

        res = client.post("/openfoodfacts/add/0000000000000", json={"price": 1.0, "stock": 1})
        assert res.status_code == 404

    @patch("app.req.get")
    def test_add_from_off_defaults_price_and_stock(self, mock_get, client):
        """POST /openfoodfacts/add/<barcode> with no body defaults price=0, stock=0."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_RESPONSE
        mock_get.return_value = mock_response

        res = client.post("/openfoodfacts/add/0025293004269")
        assert res.status_code == 201
        data = res.get_json()
        assert data["item"]["price"] == 0.0
        assert data["item"]["stock"] == 0


# ─────────────────────────────────────────────
#  Tests: Helper utilities (unit-level)
# ─────────────────────────────────────────────

class TestHelpers:
    def test_generate_id_returns_unique_ids(self):
        """generate_id() should produce unique IDs each time."""
        ids = {flask_app.generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_find_item_returns_correct_item(self, client):
        """find_item() should return the item with the matching ID."""
        item = flask_app.find_item("1")
        assert item is not None
        assert item["product_name"] == "Organic Almond Milk"

    def test_find_item_returns_none_for_missing(self, client):
        """find_item() should return None for an unknown ID."""
        item = flask_app.find_item("does_not_exist")
        assert item is None

    @patch("app.req.get")
    def test_fetch_by_barcode_success(self, mock_get):
        """fetch_by_barcode() returns a product dict on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_RESPONSE
        mock_get.return_value = mock_response

        product = flask_app.fetch_by_barcode("0025293004269")
        assert product is not None
        assert product["product_name"] == "Organic Almond Milk"

    @patch("app.req.get")
    def test_fetch_by_barcode_not_found(self, mock_get):
        """fetch_by_barcode() returns None when status != 1."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0}
        mock_get.return_value = mock_response

        product = flask_app.fetch_by_barcode("0000000000000")
        assert product is None

    @patch("app.req.get")
    def test_fetch_by_name_returns_list(self, mock_get):
        """fetch_by_name() returns a list of products."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_OFF_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        products = flask_app.fetch_by_name("almond")
        assert isinstance(products, list)
        assert len(products) == 1

    @patch("app.req.get")
    def test_fetch_by_name_on_network_error(self, mock_get):
        """fetch_by_name() returns empty list on network error."""
        import requests as rq
        mock_get.side_effect = rq.exceptions.RequestException("timeout")

        products = flask_app.fetch_by_name("anything")
        assert products == []
