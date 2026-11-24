import json
import socket
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from database import ALLOWED_CATEGORIES

SERVER_BASE_URL = "http://127.0.0.1:5050"
REQUEST_TIMEOUT = 5


class IftarPlannerClient:
    """Tkinter front-end application for the Iftar Menu Planner."""

    def __init__(self, root):
        self.root = root
        self.root.title("Iftar Menu Planner - Client Application")
        self.root.geometry("980x640")
        self.root.minsize(900, 580)
        self.root.configure(bg="#F4F6F8")

        self.selected_id = None

        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar(value=ALLOWED_CATEGORIES[0])
        self.cost_var = tk.StringVar()
        self.servings_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")

        self.total_dishes_var = tk.StringVar(value="0")
        self.total_cost_var = tk.StringVar(value="0.00 SAR")
        self.total_servings_var = tk.StringVar(value="0")
        self.cost_per_serving_var = tk.StringVar(value="0.00 SAR")

        self.status_var = tk.StringVar(value="Ready.")
        self.selected_label_var = tk.StringVar(value="Selected Record ID: None (New Entry Mode)")

        self._configure_styles()
        self._build_layout()
        self.load_dishes()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TFrame", background="#F4F6F8")
        style.configure("Card.TFrame", background="#FFFFFF", relief="solid", borderwidth=1)
        style.configure(
            "Header.TLabel",
            background="#1E293B",
            foreground="#FFFFFF",
            font=("Segoe UI", 15, "bold"),
        )
        style.configure(
            "SubHeader.TLabel",
            background="#1E293B",
            foreground="#CBD5E1",
            font=("Segoe UI", 9),
        )
        style.configure(
            "SectionTitle.TLabel",
            background="#FFFFFF",
            foreground="#0F172A",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "FieldLabel.TLabel",
            background="#FFFFFF",
            foreground="#334155",
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "MetricLabel.TLabel",
            background="#FFFFFF",
            foreground="#64748B",
            font=("Segoe UI", 9),
        )
        style.configure(
            "MetricValue.TLabel",
            background="#FFFFFF",
            foreground="#0F172A",
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "AccentMetricValue.TLabel",
            background="#FFFFFF",
            foreground="#0284C7",
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=28,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#0F172A",
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E2E8F0",
            foreground="#1E293B",
            padding=(6, 6),
        )
        style.map(
            "Treeview",
            background=[("selected", "#0284C7")],
            foreground=[("selected", "#FFFFFF")],
        )

    def _build_layout(self):
        # Top Header Banner
        header_frame = tk.Frame(self.root, bg="#1E293B", padx=20, pady=14)
        header_frame.pack(fill="x")

        title_lbl = ttk.Label(
            header_frame,
            text="Iftar Menu Planner",
            style="Header.TLabel",
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ttk.Label(
            header_frame,
            text="Manage Iftar dishes, filter courses by category, and track total estimated cost",
            style="SubHeader.TLabel",
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Summary Metrics Bar
        metrics_container = ttk.Frame(self.root, padding=(18, 12, 18, 6))
        metrics_container.pack(fill="x")

        self._create_metric_card(
            metrics_container, 0, "Total Dishes", self.total_dishes_var, accent=False
        )
        self._create_metric_card(
            metrics_container, 1, "Total Estimated Cost", self.total_cost_var, accent=True
        )
        self._create_metric_card(
            metrics_container, 2, "Total Servings", self.total_servings_var, accent=False
        )
        self._create_metric_card(
            metrics_container, 3, "Estimated Cost / Serving", self.cost_per_serving_var, accent=False
        )
        for col in range(4):
            metrics_container.columnconfigure(col, weight=1)

        # Main Workspace Split (Left Form Card, Right Table Card)
        workspace = ttk.Frame(self.root, padding=(18, 6, 18, 12))
        workspace.pack(fill="both", expand=True)
        workspace.columnconfigure(0, weight=0)
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        # Left Panel: Dish Details Form
        form_card = tk.Frame(
            workspace,
            bg="#FFFFFF",
            highlightbackground="#CBD5E1",
            highlightthickness=1,
            padx=18,
            pady=16,
            width=310,
        )
        form_card.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        form_card.grid_propagate(False)

        ttk.Label(form_card, text="Dish Details", style="SectionTitle.TLabel").pack(
            anchor="w", pady=(0, 4)
        )

        selected_id_lbl = tk.Label(
            form_card,
            textvariable=self.selected_label_var,
            bg="#FFFFFF",
            fg="#64748B",
            font=("Segoe UI", 8),
        )
        selected_id_lbl.pack(anchor="w", pady=(0, 14))

        # Dish Name
        ttk.Label(form_card, text="Dish Name *", style="FieldLabel.TLabel").pack(anchor="w")
        self.name_entry = ttk.Entry(form_card, textvariable=self.name_var, font=("Segoe UI", 10))
        self.name_entry.pack(fill="x", pady=(4, 12), ipady=3)

        # Category
        ttk.Label(form_card, text="Category *", style="FieldLabel.TLabel").pack(anchor="w")
        self.category_combo = ttk.Combobox(
            form_card,
            textvariable=self.category_var,
            values=list(ALLOWED_CATEGORIES),
            state="readonly",
            font=("Segoe UI", 10),
        )
        self.category_combo.pack(fill="x", pady=(4, 12), ipady=2)

        # Estimated Cost (SAR)
        ttk.Label(form_card, text="Estimated Cost (SAR) *", style="FieldLabel.TLabel").pack(
            anchor="w"
        )
        self.cost_entry = ttk.Entry(form_card, textvariable=self.cost_var, font=("Segoe UI", 10))
        self.cost_entry.pack(fill="x", pady=(4, 12), ipady=3)

        # Servings Count
        ttk.Label(form_card, text="Servings *", style="FieldLabel.TLabel").pack(anchor="w")
        self.servings_entry = ttk.Entry(
            form_card, textvariable=self.servings_var, font=("Segoe UI", 10)
        )
        self.servings_entry.pack(fill="x", pady=(4, 18), ipady=3)

        # Form Action Buttons
        btn_grid = tk.Frame(form_card, bg="#FFFFFF")
        btn_grid.pack(fill="x")
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        self.add_btn = tk.Button(
            btn_grid,
            text="Add Dish",
            command=self.add_dish,
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            pady=7,
            cursor="hand2",
        )
        self.add_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 8))

        self.edit_btn = tk.Button(
            btn_grid,
            text="Save Edit",
            command=self.edit_dish,
            bg="#0F766E",
            fg="#FFFFFF",
            activebackground="#115E59",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            pady=7,
            cursor="hand2",
        )
        self.edit_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=(0, 8))

        self.delete_btn = tk.Button(
            btn_grid,
            text="Delete Selected",
            command=self.delete_dish,
            bg="#DC2626",
            fg="#FFFFFF",
            activebackground="#B91C1C",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            pady=7,
            cursor="hand2",
        )
        self.delete_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.clear_btn = tk.Button(
            btn_grid,
            text="Clear Form",
            command=self.clear_form,
            bg="#E2E8F0",
            fg="#1E293B",
            activebackground="#CBD5E1",
            activeforeground="#0F172A",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            pady=7,
            cursor="hand2",
        )
        self.clear_btn.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Right Panel: Records Table and Category Filter (Extra Feature)
        table_card = tk.Frame(
            workspace,
            bg="#FFFFFF",
            highlightbackground="#CBD5E1",
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        table_card.grid(row=0, column=1, sticky="nsew")
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(1, weight=1)

        # Filter & Refresh Toolbar
        toolbar = tk.Frame(table_card, bg="#FFFFFF")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        ttk.Label(toolbar, text="Scheduled Iftar Menu", style="SectionTitle.TLabel").pack(
            side="left"
        )

        refresh_btn = tk.Button(
            toolbar,
            text="Refresh List",
            command=self.load_dishes,
            bg="#F1F5F9",
            fg="#0F172A",
            activebackground="#E2E8F0",
            relief="solid",
            bd=1,
            font=("Segoe UI", 9),
            padx=10,
            pady=3,
            cursor="hand2",
        )
        refresh_btn.pack(side="right", padx=(8, 0))

        filter_values = ["All"] + list(ALLOWED_CATEGORIES)
        self.filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=filter_values,
            state="readonly",
            width=16,
            font=("Segoe UI", 9),
        )
        self.filter_combo.pack(side="right")
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_dishes())

        filter_lbl = tk.Label(
            toolbar,
            text="Filter by Category:",
            bg="#FFFFFF",
            fg="#475569",
            font=("Segoe UI", 9, "bold"),
        )
        filter_lbl.pack(side="right", padx=(0, 6))

        # Treeview Table
        tree_frame = tk.Frame(table_card, bg="#FFFFFF")
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("id", "name", "category", "cost", "servings")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("id", text="ID", anchor="center")
        self.tree.heading("name", text="Dish Name", anchor="w")
        self.tree.heading("category", text="Category", anchor="w")
        self.tree.heading("cost", text="Est. Cost (SAR)", anchor="e")
        self.tree.heading("servings", text="Servings", anchor="center")

        self.tree.column("id", width=55, minwidth=45, anchor="center", stretch=False)
        self.tree.column("name", width=210, minwidth=150, anchor="w", stretch=True)
        self.tree.column("category", width=120, minwidth=100, anchor="w", stretch=False)
        self.tree.column("cost", width=120, minwidth=95, anchor="e", stretch=False)
        self.tree.column("servings", width=85, minwidth=70, anchor="center", stretch=False)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)

        # Empty State Label
        self.empty_label = tk.Label(
            table_card,
            text="",
            bg="#FFFFFF",
            fg="#64748B",
            font=("Segoe UI", 9),
        )
        self.empty_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Bottom Status Bar
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#E2E8F0",
            fg="#1E293B",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            padx=18,
            pady=8,
        )
        self.status_bar.pack(fill="x", side="bottom")

    def _create_metric_card(self, parent, column, title, value_var, accent=False):
        card = tk.Frame(
            parent,
            bg="#FFFFFF",
            highlightbackground="#CBD5E1",
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        padx = (0, 8) if column < 3 else (0, 0)
        card.grid(row=0, column=column, sticky="ew", padx=padx)

        ttk.Label(card, text=title, style="MetricLabel.TLabel").pack(anchor="w")
        style_name = "AccentMetricValue.TLabel" if accent else "MetricValue.TLabel"
        ttk.Label(card, textvariable=value_var, style=style_name).pack(anchor="w", pady=(2, 0))

    def set_status(self, message, level="info"):
        """Updates the bottom feedback bar with color-coded status messages."""
        self.status_var.set(message)
        if level == "success":
            self.status_bar.configure(bg="#DCFCE7", fg="#166534")
        elif level == "error":
            self.status_bar.configure(bg="#FEE2E2", fg="#991B1B")
        else:
            self.status_bar.configure(bg="#E2E8F0", fg="#1E293B")

    def send_request(self, path, values=None):
        """Sends an HTTP GET or POST request to the Flask backend on port 5050."""
        url = f"{SERVER_BASE_URL}{path}"
        body = None
        if values is not None:
            body = urlencode(values).encode("utf-8")

        try:
            with urlopen(url, data=body, timeout=REQUEST_TIMEOUT) as reply:
                raw_text = reply.read().decode("utf-8")
                return True, json.loads(raw_text)
        except HTTPError as error:
            try:
                error_body = error.read().decode("utf-8")
                payload = json.loads(error_body)
                msg = payload.get("message", f"Server error (HTTP {error.code}).")
            except (ValueError, KeyError):
                msg = f"Request failed with HTTP status {error.code}."
            self.set_status(f"Error: {msg}", level="error")
            return False, None
        except (URLError, socket.timeout):
            self.set_status(
                "Connection error: Cannot reach Flask server on port 5050. Ensure server.py is running.",
                level="error",
            )
            return False, None
        except ValueError:
            self.set_status("Error: Received an invalid JSON response from server.", level="error")
            return False, None

    def load_dishes(self, status_override=None):
        """Fetches saved records from Flask using GET and populates the Treeview."""
        category = self.filter_var.get()
        query = urlencode({"category": category})
        ok, data = self.send_request(f"/dishes?{query}")
        if not ok or data is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        dishes = data.get("dishes", [])
        for dish in dishes:
            self.tree.insert(
                "",
                "end",
                values=(
                    dish["id"],
                    dish["name"],
                    dish["category"],
                    f"{dish['cost']:.2f}",
                    dish["servings"],
                ),
            )

        summary = data.get("summary", {})
        self.total_dishes_var.set(str(summary.get("count", 0)))
        self.total_cost_var.set(f"{summary.get('total_cost', 0.0):.2f} SAR")
        self.total_servings_var.set(str(summary.get("total_servings", 0)))
        self.cost_per_serving_var.set(f"{summary.get('cost_per_serving', 0.0):.2f} SAR")

        if not dishes:
            if category == "All":
                self.empty_label.configure(
                    text="No dishes saved yet. Fill in the form on the left and click 'Add Dish'."
                )
            else:
                self.empty_label.configure(
                    text=f"No dishes found in category '{category}'."
                )
            if not status_override:
                self.set_status("No records found for the current view.", level="info")
        else:
            self.empty_label.configure(
                text=f"Showing {len(dishes)} record(s). Select any row to edit or delete."
            )
            if not status_override:
                self.set_status(
                    f"Loaded {len(dishes)} dish(es) from Flask server.", level="info"
                )

        if status_override:
            msg, level = status_override
            self.set_status(msg, level=level)

    def on_row_selected(self, _event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        values = self.tree.item(selected_items[0], "values")
        if not values:
            return

        self.selected_id = values[0]
        self.name_var.set(values[1])
        self.category_var.set(values[2])
        self.cost_var.set(values[3])
        self.servings_var.set(values[4])
        self.selected_label_var.set(f"Selected Record ID: #{self.selected_id}")

    def clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.category_var.set(ALLOWED_CATEGORIES[0])
        self.cost_var.set("")
        self.servings_var.set("")
        self.selected_label_var.set("Selected Record ID: None (New Entry Mode)")
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        self.set_status("Form cleared. Ready to add a new dish.", level="info")

    def add_dish(self):
        values = {
            "name": self.name_var.get().strip(),
            "category": self.category_var.get().strip(),
            "cost": self.cost_var.get().strip(),
            "servings": self.servings_var.get().strip(),
        }
        ok, data = self.send_request("/dishes/add", values=values)
        if ok and data:
            msg = data.get("message", "Dish added.")
            self.clear_form()
            self.load_dishes(status_override=(msg, "success"))

    def edit_dish(self):
        if self.selected_id is None:
            self.set_status(
                "Error: Please select a dish from the table before clicking 'Save Edit'.",
                level="error",
            )
            return

        values = {
            "id": str(self.selected_id),
            "name": self.name_var.get().strip(),
            "category": self.category_var.get().strip(),
            "cost": self.cost_var.get().strip(),
            "servings": self.servings_var.get().strip(),
        }
        ok, data = self.send_request("/dishes/edit", values=values)
        if ok and data:
            msg = data.get("message", "Dish updated.")
            self.clear_form()
            self.load_dishes(status_override=(msg, "success"))

    def delete_dish(self):
        if self.selected_id is None:
            self.set_status(
                "Error: Please select a dish from the table before clicking 'Delete Selected'.",
                level="error",
            )
            return

        dish_name = self.name_var.get().strip() or f"ID #{self.selected_id}"
        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete dish #{self.selected_id} ('{dish_name}')?",
        )
        if not confirmed:
            self.set_status("Delete action cancelled.", level="info")
            return

        values = {"id": str(self.selected_id)}
        ok, data = self.send_request("/dishes/delete", values=values)
        if ok and data:
            msg = data.get("message", "Dish deleted.")
            self.clear_form()
            self.load_dishes(status_override=(msg, "success"))


def main():
    root = tk.Tk()
    IftarPlannerClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
