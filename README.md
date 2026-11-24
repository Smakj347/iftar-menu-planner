# Iftar Menu Planner

**Student Name:** Muhammaad Abdulkadir Saeed  
**Course:** Advanced Programming 462 — Individual Client-Server Project  
**Instructor:** Dr. Majed Hariri  
**Architecture:** Python Tkinter Front End, Flask Back End (Port `5050`), and SQLite Database

---

## 1. Overview

**Iftar Menu Planner** is a client-server desktop application for planning Iftar meals, organizing dishes by course category, and calculating total estimated meal costs and per-serving budgets in Saudi Riyals (SAR).

* **Tkinter Front End (`client.py`):** Provides an interface to add, view, edit, delete, and filter Iftar dishes without manually entering server URLs. Displays live cost metrics (Total Dishes, Total Estimated Cost, Total Servings, and Cost per Serving) and clear feedback messages.
* **Flask Back End (`server.py`):** Listens on `http://127.0.0.1:5050`, validates all incoming fields, returns structured JSON responses with appropriate HTTP status codes (`200`, `400`, `404`, `500`), and delegates persistence to SQLite.
* **SQLite Database (`database.py`):** Encapsulates all database operations inside the `MenuDatabase` class. Automatically creates the `dishes` table if missing while preserving existing records, opens a dedicated connection per request, uses parameterized SQL placeholders (`?`), and closes the connection after each operation.
* **Threaded Report Helper (`report.py`):** Connects to Flask's JSON endpoint (`GET /dishes`), spawns a worker `threading.Thread` (`start()` / `join()`), and writes a formatted UTF-8 summary report (`iftar_menu_report.txt`).

---

## 2. Project Structure

| File | Purpose |
| :--- | :--- |
| `database.py` | `MenuDatabase` class managing SQLite table initialization and parameterized CRUD queries. |
| `server.py` | Flask HTTP server running on port `5050` with input validation and JSON endpoints. |
| `client.py` | Tkinter GUI client communicating with Flask via `urllib.request.urlopen` and `urllib.parse.urlencode`. |
| `report.py` | Standalone multi-threaded report generator that writes `iftar_menu_report.txt` in UTF-8. |
| `requirements.txt` | Python package dependencies (`Flask`). |
| `README.md` | Project documentation, setup guide, course topic mapping, and QA test results. |

---

## 3. Setup and Execution Instructions

### Step 1: Install Required Packages
Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

### Step 2: Database Table Initialization
The SQLite database (`iftar_menu.db`) and the `dishes` table are created automatically when `server.py` starts via `db.initialize(seed_if_empty=True)` in `database.py`. If the database is empty on first run, six sample Iftar dishes are inserted. Existing records are always preserved across restarts.

To initialize or verify the database table directly from the terminal:

```bash
python -c "from database import MenuDatabase; MenuDatabase().initialize()"
```

### Step 3: Start the Flask Back End (Port 5050)
Start the Flask server first and keep its terminal running:

```bash
python server.py
```

The server listens on `http://127.0.0.1:5050`.

### Step 4: Start the Tkinter Front End
Open a second terminal in the same folder and launch the desktop GUI:

```bash
python client.py
```

### Step 5: Run the Multi-Threaded Report Helper
While `server.py` is running, execute the report helper from a terminal:

```bash
python report.py
```

This fetches the current records from `http://127.0.0.1:5050/dishes` and uses a background thread to generate `iftar_menu_report.txt`.

---

## 4. Course Topics Location Map

| Course Topic | File Name | Function / Class / Method | How It Is Used in the Project |
| :--- | :--- | :--- | :--- |
| **Python and collections** | `server.py` | `calculate_summary()`, `validate_dish_form()`, `ALLOWED_CATEGORIES` | Functions, conditions, and `for` loops iterate over lists of dish dictionaries to calculate `total_cost`, `total_servings`, `average_cost`, and `cost_per_serving`. Dictionaries store named record fields and JSON payloads. |
| **Exceptions** | `client.py` / `server.py` / `report.py` | `IftarPlannerClient.send_request()`, `validate_dish_form()`, `write_report_worker()` | Catches `HTTPError` (before `URLError`), `URLError`, and `socket.timeout` in `client.py` and `report.py`; handles `ValueError` and `sqlite3.Error` in `server.py`; handles `OSError` during UTF-8 file writing in `report.py`. |
| **Classes** | `database.py` / `client.py` | `MenuDatabase`, `IftarPlannerClient` | `MenuDatabase` encapsulates SQLite connection management and CRUD operations (`initialize`, `get_dishes`, `add_dish`, `update_dish`, `delete_dish`). `IftarPlannerClient` encapsulates Tkinter state and event handlers. |
| **SQLite** | `database.py` | `MenuDatabase.initialize()`, `get_dishes()`, `add_dish()`, `update_dish()`, `delete_dish()` | Creates the `dishes` table with `CREATE TABLE IF NOT EXISTS`, opens a new connection per request, uses `?` placeholders for all SQL statements, commits changes, and closes the connection inside a `finally` block. |
| **Threads and files** | `report.py` | `generate_report()`, `write_report_worker()` | Queries `GET /dishes`, starts a `threading.Thread` with `worker.start()`, writes a formatted report using `with open(..., encoding="utf-8")`, catches `OSError`, and waits for completion with `worker.join()`. |
| **Tkinter** | `client.py` | `IftarPlannerClient._build_layout()`, `load_dishes()`, `add_dish()`, `edit_dish()`, `delete_dish()` | Desktop GUI with entry fields, category selector, summary metric cards, `ttk.Treeview` table, confirmation dialog on delete (`messagebox.askyesno`), category filter, and color-coded status bar. |
| **Client and server** | `client.py` / `server.py` | `IftarPlannerClient.send_request()` <-> `@app.route("/dishes/add")` | HTTP GET and POST requests over `http://127.0.0.1:5050` using `urllib.request.urlopen` (`timeout=5`), `urllib.parse.urlencode`, and JSON replies parsed via `json.loads`. |
| **Flask** | `server.py` | `list_dishes()`, `add_dish()`, `edit_dish()`, `delete_dish()` | Defines `GET /dishes`, `POST /dishes/add`, `POST /dishes/edit`, and `POST /dishes/delete`. Reads form data via `request.form`, validates fields, and returns JSON with HTTP status `200`, `400`, or `404`. |

---

## 5. Client-Server HTTP Request and Reply Walkthrough

Below is the step-by-step trace of adding a new dish (**"Chicken Mandi"**) from the Tkinter GUI to SQLite and back:

1. **User Action in Tkinter (`client.py`):**
   The user enters Dish Name (`Chicken Mandi`), Category (`Main Dish`), Estimated Cost (`65.50`), and Servings (`5`), then clicks **Add Dish** (`IftarPlannerClient.add_dish`).
2. **Encoding and Sending the HTTP POST Request (`client.py`):**
   `send_request("/dishes/add", values)` packs the form dictionary and encodes it into URL-encoded UTF-8 bytes using `urlencode(values).encode("utf-8")`. It calls:
   ```python
   with urlopen("http://127.0.0.1:5050/dishes/add", data=body, timeout=5) as reply:
       raw_text = reply.read().decode("utf-8")
       return True, json.loads(raw_text)
   ```
3. **Validation and SQLite Insert in Flask (`server.py` & `database.py`):**
   Flask receives the `POST /dishes/add` request and passes `request.form` to `validate_dish_form()`. After verifying that all required fields are present and numeric ranges are valid (`0 < cost <= 10000`, `1 <= servings <= 500`), Flask calls `db.add_dish(...)`, which runs:
   ```sql
   INSERT INTO dishes (name, category, cost, servings) VALUES (?, ?, ?, ?)
   ```
   and commits the transaction.
4. **JSON Reply and GUI Refresh:**
   Flask returns HTTP `200` with JSON:
   ```json
   {
     "status": "ok",
     "message": "Dish 'Chicken Mandi' added successfully.",
     "dish": {
       "id": 7,
       "name": "Chicken Mandi",
       "category": "Main Dish",
       "cost": 65.5,
       "servings": 5
     }
   }
   ```
   Tkinter decodes the JSON reply, clears the input form, calls `load_dishes()` (`GET /dishes`) to refresh the table and recalculate the **Total Estimated Cost**, and displays the confirmation message in the status bar.

---

## 6. Verification and QA Test Results

All functional, validation, persistence, and error-recovery requirements were tested and verified:

| Test Case | Action Performed | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- |
| **1. View & Cost Summary** | Start `server.py` and `client.py` (`GET /dishes`). | Displays saved dishes in `Treeview` and shows total estimated cost (`204.50 SAR`). | **PASS** — 6 dishes loaded; summary metrics match total cost and servings. |
| **2. Add Record** | Submit `"Chicken Mandi"`, `"Main Dish"`, `65.50`, `5` (`POST /dishes/add`). | Record saved in SQLite; table and total cost update immediately. | **PASS** — Created Dish ID `#7`; status bar confirmed addition. |
| **3. Edit Record** | Select Dish `#7`, change name to `"Roasted Chicken Mandi"` and cost to `70.00` (`POST /dishes/edit`). | Only Dish `#7` updates in SQLite and in the GUI table. | **PASS** — Dish `#7` updated; other records remained unchanged. |
| **4. Extra Feature (Filter & Cost Breakdown)** | Select `"Main Dish"` in the **Filter by Category** dropdown (`GET /dishes?category=Main+Dish`). | Table displays only Main Dishes and recalculates the filtered cost and servings metrics. | **PASS** — Filtered view showed only Main Dish records and their subtotal cost. |
| **5. Delete Record** | Select Dish `#7`, click **Delete Selected**, and confirm in dialog (`POST /dishes/delete`). | Confirmation prompt appears; upon confirmation, Dish `#7` is removed. | **PASS** — Dish `#7` deleted from SQLite and removed from table. |
| **6. Persistence Check** | Stop both `client.py` and `server.py`, then start both again. | Previously saved records remain intact in `iftar_menu.db`. | **PASS** — All saved records persisted across restarts. |
| **7. Missing Input (`HTTP 400`)** | Click **Add Dish** with an empty Dish Name. | Flask returns `400` JSON; Tkinter catches `HTTPError` and shows message. | **PASS** — Status bar displayed: `Error: Dish name is required.` |
| **8. Invalid Value (`HTTP 400`)** | Enter `-15` or `abc` in Estimated Cost (SAR). | Flask returns `400` JSON; Tkinter catches `HTTPError` and shows message. | **PASS** — Status bar displayed: `Error: Estimated cost must be greater than 0 and at most 10,000 SAR.` |
| **9. Unknown Record ID (`HTTP 404`)** | Attempt to edit or delete an ID that was already deleted from the database. | Flask returns `404` JSON; Tkinter displays the not-found error cleanly. | **PASS** — Status bar displayed: `Error: Record with ID 7 was not found.` |
| **10. Empty List Handling** | Filter by a category with zero records (or clear all records). | GUI shows a clear empty-state message and `0.00 SAR` summary without errors. | **PASS** — Empty message and zeroed cost metrics displayed cleanly. |
| **11. Offline Server Recovery** | Stop `server.py`, click **Refresh List** in Tkinter, then start `server.py` again and click **Refresh List**. | Shows connection error when offline and recovers without restarting the Tkinter window. | **PASS** — Displayed connection error on port `5050` when stopped, and reloaded records after server restart. |
| **12. Threaded Report Helper** | Run `python report.py` while `server.py` is running. | Queries `GET /dishes`, runs `Thread.start()` and `Thread.join()`, and saves `iftar_menu_report.txt` in UTF-8. | **PASS** — `iftar_menu_report.txt` generated with full dish table, category cost breakdown, and summary metrics. |

---

## 7. Credits and Academic Integrity

* Built using Python's standard library (`tkinter`, `sqlite3`, `urllib`, `json`, `socket`, `threading`, `pathlib`, `datetime`) and the `Flask` web framework.
* Developed in accordance with the Advanced Programming 462 course guidelines and academic integrity policy.
