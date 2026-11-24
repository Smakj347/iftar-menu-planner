import json
import socket
import threading
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

SERVER_URL = "http://127.0.0.1:5050/dishes"
REPORT_FILE = Path(__file__).resolve().parent / "iftar_menu_report.txt"
REQUEST_TIMEOUT = 5


def fetch_dishes_from_server(url=SERVER_URL):
    """Fetches saved dish records and summary metrics from the Flask JSON route."""
    with urlopen(url, timeout=REQUEST_TIMEOUT) as reply:
        payload = json.loads(reply.read().decode("utf-8"))
        return payload


def write_report_worker(payload, output_path, result_holder):
    """Thread target function that writes the Iftar menu report to a UTF-8 text file."""
    dishes = payload.get("dishes", [])
    summary = payload.get("summary", {})
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    category_totals = {}
    for dish in dishes:
        cat = dish["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + float(dish["cost"])

    lines = [
        "=" * 68,
        "IFTAR MENU PLANNER - SUMMARY REPORT",
        f"Generated At: {generated_at}",
        "=" * 68,
        "",
        "1. SAVED IFTAR DISHES",
        "-" * 68,
        f"{'ID':<5} {'Dish Name':<26} {'Category':<14} {'Cost (SAR)':>12} {'Servings':>9}",
        "-" * 68,
    ]

    if not dishes:
        lines.append("No dishes are currently saved in the menu.")
    else:
        for dish in dishes:
            lines.append(
                f"{dish['id']:<5} "
                f"{dish['name'][:25]:<26} "
                f"{dish['category']:<14} "
                f"{dish['cost']:>12.2f} "
                f"{dish['servings']:>9}"
            )

    lines.extend(
        [
            "-" * 68,
            "",
            "2. COST BREAKDOWN BY CATEGORY",
            "-" * 68,
        ]
    )

    if not category_totals:
        lines.append("No category totals available.")
    else:
        for category, subtotal in category_totals.items():
            lines.append(f"{category:<25}: {subtotal:>10.2f} SAR")

    lines.extend(
        [
            "-" * 68,
            "",
            "3. OVERALL SUMMARY",
            "-" * 68,
            f"Total Saved Dishes        : {summary.get('count', 0)}",
            f"Total Servings            : {summary.get('total_servings', 0)}",
            f"Total Estimated Cost      : {summary.get('total_cost', 0.0):.2f} SAR",
            f"Average Cost per Dish     : {summary.get('average_cost', 0.0):.2f} SAR",
            f"Estimated Cost per Serving: {summary.get('cost_per_serving', 0.0):.2f} SAR",
            "=" * 68,
            "",
        ]
    )

    try:
        with open(output_path, mode="w", encoding="utf-8") as report_file:
            report_file.write("\n".join(lines))
        result_holder["success"] = True
        result_holder["message"] = f"Report saved successfully to: {output_path}"
    except OSError as file_error:
        result_holder["success"] = False
        result_holder["message"] = f"Failed to write report file: {file_error}"


def generate_report(output_path=REPORT_FILE):
    """Coordinates fetching records from Flask and writing the report on a background thread."""
    try:
        payload = fetch_dishes_from_server()
    except HTTPError as err:
        print(f"Report generation failed: Server returned HTTP {err.code}.")
        return False
    except (URLError, socket.timeout):
        print(
            "Report generation failed: Cannot reach Flask server at "
            f"{SERVER_URL}. Start server.py first."
        )
        return False
    except ValueError:
        print("Report generation failed: Server did not return valid JSON.")
        return False

    result_holder = {"success": False, "message": ""}
    worker = threading.Thread(
        target=write_report_worker,
        args=(payload, output_path, result_holder),
    )
    worker.start()
    worker.join()

    print(result_holder["message"])
    return result_holder["success"]


if __name__ == "__main__":
    generate_report()
