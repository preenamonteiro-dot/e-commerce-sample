from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "my-ecommerce-secret-key-123"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["ecommerce_db"]
users = db["users"]
products=db["products"]


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")

        # Check if user already exists
        existing_user = users.find_one({"email": email})

        if existing_user:
            return "User already registered!"

        # Save user in MongoDB
        users.insert_one({
            "name": name,
            "email": email
        })

        return f"Registration successful! Welcome, {name}."

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")

        # Find user in MongoDB
        user = users.find_one({"email": email})

        if user:
            return f"Login successful! Welcome back, {email}."

        return "User not found. Please register first."

    return render_template("login.html")
@app.route("/products")
def product_list():
    # Add sample products if collection is empty
    if products.count_documents({}) == 0:
        sample_products = [
            {
                "name": "Laptop",
                "price": 55000,
                "description": "High-performance laptop"
            },
            {
                "name": "Smartphone",
                "price": 25000,
                "description": "Modern smartphone"
            },
            {
                "name": "Headphones",
                "price": 3000,
                "description": "Wireless headphones"
            }
        ]

        products.insert_many(sample_products)

    product_data = list(products.find())

    return render_template(
        "products.html",
        products=product_data
    )
@app.route("/add_to_cart/<product_id>", methods=["POST"])
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(product_id)
    session.modified = True

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart_ids = session.get("cart", [])

    cart_products = []

    for product_id in cart_ids:
        product = products.find_one({
            "_id": ObjectId(product_id)
        })

        if product:
            cart_products.append(product)

    total = sum(product["price"] for product in cart_products)
    return render_template("cart.html", products=cart_products, total=total)
@app.route("/remove_from_cart/<product_id>")
def remove_from_cart(product_id):
    cart_ids = session.get("cart", [])

    if product_id in cart_ids:
        cart_ids.remove(product_id)

    session["cart"] = cart_ids
    session.modified = True

    return redirect("/cart")
@app.route("/checkout")
def checkout():
    cart_ids = session.get("cart", [])

    cart_products = []

    for product_id in cart_ids:
        product = products.find_one({
            "_id": ObjectId(product_id)
        })

        if product:
            cart_products.append(product)

    total = sum(product["price"] for product in cart_products)

    return render_template(
        "checkout.html",
        products=cart_products,
        total=total
    )
@app.route("/place_order", methods=["POST"])
def place_order():
    cart_ids = session.get("cart", [])

    if not cart_ids:
        return redirect("/cart")

    cart_products = []

    for product_id in cart_ids:
        product = products.find_one({
            "_id": ObjectId(product_id)
        })

        if product:
            cart_products.append(product)

    total = sum(product["price"] for product in cart_products)

    order = {
    "products": cart_ids,
    "total": total,
    "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    "status": "Pending"
}

    products.database["orders"].insert_one(order)

    session["cart"] = []
    session.modified = True

    return render_template("order_success.html")
@app.route("/orders")
def orders():
    orders_collection = db["orders"]

    search = request.args.get("search", "").strip()

    if search:
        all_orders = list(
            orders_collection.find({
                "product_details.name": {
                    "$regex": search,
                    "$options": "i"
                }
            }).sort("_id", -1)
        )
    else:
        all_orders = list(
            orders_collection.find().sort("_id", -1)
        )

    for order in all_orders:
        order["product_details"] = []

        for product_id in order["products"]:
            product = products.find_one({
                "_id": ObjectId(product_id)
            })

            if product:
                order["product_details"].append(product)

    return render_template(
        "orders.html",
        orders=all_orders,
        search=search
    )
@app.route("/update_order_status/<order_id>", methods=["POST"])
def update_order_status(order_id):
    status = request.form.get("status", "Pending")

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}}
    )

    return redirect(url_for("orders"))
@app.route("/admin")
def admin():
    orders_collection = db["orders"]

    total_orders = orders_collection.count_documents({})

    pending_orders = orders_collection.count_documents({
        "status": "Pending"
    })

    delivered_orders = orders_collection.count_documents({
        "status": "Delivered"
    })

    cancelled_orders = orders_collection.count_documents({
        "status": "Cancelled"
    })

    return render_template(
        "admin.html",
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders
    )

if __name__ == "__main__":
    app.run(debug=True)