import sqlite3
from flask import Flask, jsonify, request
from database import ALLOWED_CATEGORIES, MenuDatabase

app = Flask(__name__)
db = MenuDatabase()
db.initialize(seed_if_empty=True)


def validate_dish_form(form):
    """Validates form fields for creating or updating a dish."""
    name = form.get("name", "").strip()
    category = form.get("category", "").strip()
    cost_raw = form.get("cost", "").strip()
    servings_raw = form.get("servings", "").strip()

    if not name:
        return None, "Dish name is required."
    if len(name) > 80:
        return None, "Dish name must not exceed 80 characters."

    if not category:
        return None, "Category is required."
    if category not in ALLOWED_CATEGORIES:
        allowed = ", ".join(ALLOWED_CATEGORIES)
        return None, f"Invalid category. Choose one of: {allowed}."

    if not cost_raw:
        return None, "Estimated cost is required."
    try:
        cost = float(cost_raw)
    except ValueError:
        return None, "Estimated cost must be a valid number."
    if cost <= 0 or cost > 10000:
        return None, "Estimated cost must be greater than 0 and at most 10,000 SAR."

    if not servings_raw:
        return None, "Servings count is required."
    try:
        servings = int(servings_raw)
    except ValueError:
        return None, "Servings must be a whole number."
    if servings < 1 or servings > 500:
        return None, "Servings must be between 1 and 500."

    return {
        "name": name,
        "category": category,
        "cost": round(cost, 2),
        "servings": servings,
    }, None


def parse_dish_id(raw_id):
    """Parses and validates a positive integer record ID."""
    if raw_id is None or str(raw_id).strip() == "":
        return None, "Record ID is required."
    try:
        dish_id = int(str(raw_id).strip())
        if dish_id <= 0:
            return None, "Record ID must be a positive integer."
        return dish_id, None
    except ValueError:
        return None, "Record ID must be a valid integer."


def calculate_summary(dishes):
    """Computes total estimated cost and total servings using a loop over records."""
    total_cost = 0.0
    total_servings = 0
    for dish in dishes:
        total_cost += dish["cost"]
        total_servings += dish["servings"]

    count = len(dishes)
    average_cost = round(total_cost / count, 2) if count > 0 else 0.0
    cost_per_serving = round(total_cost / total_servings, 2) if total_servings > 0 else 0.0

    return {
        "count": count,
        "total_cost": round(total_cost, 2),
        "total_servings": total_servings,
        "average_cost": average_cost,
        "cost_per_serving": cost_per_serving,
    }


@app.route("/dishes", methods=["GET"])
def list_dishes():
    category = request.args.get("category", "All").strip()
    if category and category != "All" and category not in ALLOWED_CATEGORIES:
        return jsonify({"status": "error", "message": "Invalid filter category."}), 400

    try:
        dishes = db.get_dishes(category=category)
        summary = calculate_summary(dishes)
        return (
            jsonify(
                {
                    "status": "ok",
                    "dishes": dishes,
                    "summary": summary,
                    "categories": list(ALLOWED_CATEGORIES),
                }
            ),
            200,
        )
    except sqlite3.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500


@app.route("/dishes/add", methods=["POST"])
def add_dish():
    cleaned, error_msg = validate_dish_form(request.form)
    if error_msg:
        return jsonify({"status": "error", "message": error_msg}), 400

    try:
        dish = db.add_dish(
            name=cleaned["name"],
            category=cleaned["category"],
            cost=cleaned["cost"],
            servings=cleaned["servings"],
        )
        return (
            jsonify(
                {
                    "status": "ok",
                    "message": f"Dish '{dish['name']}' added successfully.",
                    "dish": dish,
                }
            ),
            200,
        )
    except sqlite3.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500


@app.route("/dishes/edit", methods=["POST"])
def edit_dish():
    dish_id, id_error = parse_dish_id(request.form.get("id"))
    if id_error:
        return jsonify({"status": "error", "message": id_error}), 400

    cleaned, error_msg = validate_dish_form(request.form)
    if error_msg:
        return jsonify({"status": "error", "message": error_msg}), 400

    try:
        updated = db.update_dish(
            dish_id=dish_id,
            name=cleaned["name"],
            category=cleaned["category"],
            cost=cleaned["cost"],
            servings=cleaned["servings"],
        )
        if not updated:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Record with ID {dish_id} was not found.",
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "status": "ok",
                    "message": f"Dish #{dish_id} ('{cleaned['name']}') updated successfully.",
                }
            ),
            200,
        )
    except sqlite3.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500


@app.route("/dishes/delete", methods=["POST"])
def delete_dish():
    dish_id, id_error = parse_dish_id(request.form.get("id"))
    if id_error:
        return jsonify({"status": "error", "message": id_error}), 400

    try:
        deleted = db.delete_dish(dish_id=dish_id)
        if not deleted:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Record with ID {dish_id} was not found.",
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "status": "ok",
                    "message": f"Dish #{dish_id} deleted successfully.",
                }
            ),
            200,
        )
    except sqlite3.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
