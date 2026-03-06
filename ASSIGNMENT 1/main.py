from fastapi import FastAPI

app = FastAPI()

# Product Database (List of Dictionaries)
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 120, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Office Chair", "price": 3499, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},

    # Q1 — Added products
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
]


# Existing endpoint
@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }


# Filter by Category
@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):
    filtered = [p for p in products if p["category"].lower() == category_name.lower()]

    if not filtered:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": filtered,
        "count": len(filtered)
    }


#Only In-Stock Products
@app.get("/products/instock")
def get_instock_products():
    instock = [p for p in products if p["in_stock"]]

    return {
        "in_stock_products": instock,
        "count": len(instock)
    }


#Store Summary
@app.get("/store/summary")
def store_summary():

    total = len(products)
    in_stock = len([p for p in products if p["in_stock"]])
    out_stock = total - in_stock

    categories = list(set([p["category"] for p in products]))

    return {
        "store_name": "My E-commerce Store",
        "total_products": total,
        "in_stock": in_stock,
        "out_of_stock": out_stock,
        "categories": categories
    }


# Search Products
@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    matched = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not matched:
        return {"message": "No products matched your search"}

    return {
        "matched_products": matched,
        "count": len(matched)
    }


# best_deal

@app.get("/products/deals")
def product_deals():

    cheapest = min(products, key=lambda x: x["price"])
    expensive = max(products, key=lambda x: x["price"])

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }