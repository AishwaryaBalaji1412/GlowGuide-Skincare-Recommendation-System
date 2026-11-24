
"""GlowGuide - Personalized Skincare Recommendation Application."""

import shutil
import math
import re
import tkinter as tk
import hashlib
import secrets

from pathlib import Path
from tkinter import ttk, messagebox, simpledialog, filedialog

from PIL import Image, ImageTk, UnidentifiedImageError

from database import (
    DATABASE_ERROR,
    execute_query,
    register_user,
    get_user_by_email,
    save_user_preferences,
    get_user_preferences,
    fetch_active_products,
    save_recommendations,
    get_recommendation_history,
    save_skincare_routines,
    get_skincare_routines,
    add_product,
    update_product,
    deactivate_product,
    create_admin,
    get_admin_by_username,
)

from recommendations import (
    recommend_products,
    generate_skincare_routine,
)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

APP_NAME = "GlowGuide"
BASE_DIR = Path(__file__).resolve().parent

BG = "#FFF5F8"
PINK = "#E88BAA"
DARK_PINK = "#C65F86"
LIGHT_PINK = "#FCE4EC"
WHITE = "#FFFFFF"
TEXT = "#49343D"
MUTED = "#806B74"

PASSWORD_ITERATIONS = 150000

SKIN_TYPES = [
    "Normal", "Dry", "Oily", "Combination", "Sensitive"
]

SKIN_CONCERNS = [
    "Acne", "Dark Spots", "Dullness", "Dryness",
    "Sensitivity", "Excess Oil", "Clogged Pores",
    "Wrinkles", "Uneven Skin Tone", "Redness", "Pigmentation",
]


# --------------------------------------------------
# COMMON HELPERS
# --------------------------------------------------

def database_operation_succeeded(result):
    return result is not None and result is not DATABASE_ERROR


def resolve_image_path(image_path):
    """Resolve image paths relative to the project folder."""

    if not image_path:
        return None

    path = Path(image_path).expanduser()

    if not path.is_absolute():
        path = BASE_DIR / path

    return path.resolve()


# --------------------------------------------------
# PASSWORD SECURITY
# --------------------------------------------------

def hash_password(password):
    """Hash passwords using PBKDF2-HMAC-SHA256."""

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    """Verify a password against a stored hash."""

    try:
        salt, original_hash = stored_hash.split("$")

        for iterations in (PASSWORD_ITERATIONS, 100000):
            new_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            ).hex()

            if secrets.compare_digest(new_hash, original_hash):
                return True

        return False

    except (ValueError, AttributeError, TypeError):
        return False


# --------------------------------------------------
# SCROLLABLE FRAME
# --------------------------------------------------

class ScrollableFrame(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(
            self,
            bg=BG,
            highlightthickness=0,
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )

        self.content = ttk.Frame(self.canvas)

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw",
        )

        self.content.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas_width)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel_linux)

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_canvas_width(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def on_mousewheel(self, event):
        """Handle mouse-wheel scrolling on macOS and Windows."""

        if not self.winfo_exists() or not event.delta:
            return

        try:
            is_mac = self.tk.call("tk", "windowingsystem") == "aqua"
        except tk.TclError:
            is_mac = False

        if is_mac:
            units = -int(event.delta)
        else:
            units = -int(event.delta / 120)

        if units == 0:
            units = -1 if event.delta > 0 else 1

        self.canvas.yview_scroll(units, "units")

    def on_mousewheel_linux(self, event):
        """Handle Linux mouse-wheel events."""

        if not self.winfo_exists():
            return

        self.canvas.yview_scroll(
            -1 if event.num == 4 else 1,
            "units",
        )


# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

class GlowGuideApp:

    def __init__(self, root):

        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1100x760")
        self.root.minsize(850, 600)
        self.root.configure(bg=BG)

        self.current_user = None
        self.current_recommendations = []
        self.current_routine = None
        self.product_images = []

        self._last_saved_recommendation_signature = None

        self.setup_styles()
        self.show_login()

    # ------------------------------------------------
    # STYLES
    # ------------------------------------------------

    def setup_styles(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG)

        style.configure(
            "TLabel",
            background=BG,
            foreground=TEXT,
            font=("Arial", 10),
        )

        style.configure(
            "Title.TLabel",
            font=("Arial", 24, "bold"),
            foreground=DARK_PINK,
        )

        style.configure(
            "Heading.TLabel",
            font=("Arial", 15, "bold"),
            foreground=DARK_PINK,
        )

        style.configure(
            "TButton",
            font=("Arial", 10, "bold"),
            padding=8,
        )

        style.configure(
            "Accent.TButton",
            background=PINK,
            foreground=WHITE,
        )

        style.map(
            "Accent.TButton",
            background=[("active", DARK_PINK)],
        )

        style.configure("TEntry", padding=7)
        style.configure("TCombobox", padding=6)
        style.configure("TLabelframe", background=BG)

        style.configure(
            "TLabelframe.Label",
            background=BG,
            foreground=DARK_PINK,
            font=("Arial", 11, "bold"),
        )

        style.configure("Treeview", rowheight=28, font=("Arial", 9))
        style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

    # ------------------------------------------------
    # COMMON UI HELPERS
    # ------------------------------------------------

    def clear_window(self):

        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")

        for widget in self.root.winfo_children():
            widget.destroy()

        self.product_images.clear()

    def load_image(self, filename, size):
        """Load and resize an image from the images folder."""

        path = BASE_DIR / "images" / filename

        if not path.is_file():
            return None

        try:
            with Image.open(path) as original:
                image = original.convert("RGB")
                image.thumbnail(size)

            photo = ImageTk.PhotoImage(image)
            self.product_images.append(photo)
            return photo

        except (OSError, ValueError, UnidentifiedImageError):
            return None

    def show_brand_banner(self):
        """Display the GlowGuide skincare banner."""

        photo = self.load_image("glowguide_banner.jpg", (820, 260))

        if photo:
            ttk.Label(
                self.root,
                image=photo,
            ).pack(pady=8)

    def create_header(self, title, subtitle=None):

        header = ttk.Frame(self.root, padding=15)
        header.pack(fill="x")

        brand = ttk.Frame(header)
        brand.pack()

        logo = self.load_image("glowguide_logo_mark.jpg", (45, 45))

        if logo:
            ttk.Label(
                brand,
                image=logo,
            ).pack(side="left", padx=8)

        ttk.Label(
            brand,
            text=title,
            style="Title.TLabel",
        ).pack(side="left")

        if subtitle:
            ttk.Label(
                header,
                text=subtitle,
                foreground=MUTED,
            ).pack(pady=4)

    def create_button(self, parent, text, command):

        return ttk.Button(
            parent,
            text=text,
            command=command,
            style="Accent.TButton",
        )

    def get_scrollable_page(self):

        page = ScrollableFrame(self.root)

        page.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10,
        )

        return page.content

    def show_database_error(self):

        messagebox.showerror(
            "Database Error",
            "Unable to retrieve data from the database. "
            "Please check your MySQL connection and try again.",
        )

    # ------------------------------------------------
    # LOGIN
    # ------------------------------------------------

    def show_login(self):

        self.clear_window()

        self.create_header(
            APP_NAME,
            "Your personalized skincare companion",
        )

        self.show_brand_banner()

        container = ttk.Frame(self.root, padding=35)
        container.pack(expand=True)

        ttk.Label(
            container,
            text="Welcome Back!",
            style="Heading.TLabel",
        ).pack(pady=15)

        ttk.Label(container, text="Email").pack(anchor="w")

        self.login_email = ttk.Entry(container, width=38)
        self.login_email.pack(pady=6)

        ttk.Label(container, text="Password").pack(anchor="w")

        self.login_password = ttk.Entry(
            container,
            width=38,
            show="*",
        )
        self.login_password.pack(pady=6)

        self.create_button(
            container,
            "Login",
            self.login_user,
        ).pack(fill="x", pady=12)

        ttk.Button(
            container,
            text="Create New Account",
            command=self.show_register,
        ).pack(fill="x", pady=4)

        ttk.Button(
            container,
            text="Admin Login",
            command=self.show_admin_login,
        ).pack(fill="x", pady=4)

    def login_user(self):

        email = self.login_email.get().strip().lower()
        password = self.login_password.get()

        if not email or not password:
            messagebox.showwarning(
                "Missing Details",
                "Please enter your email and password.",
            )
            return

        user = get_user_by_email(email)

        if user is DATABASE_ERROR:
            self.show_database_error()
            return

        if not user or not verify_password(
            password,
            user.get("password_hash"),
        ):
            messagebox.showerror(
                "Login Failed",
                "Invalid email or password.",
            )
            return

        self.current_user = user
        self.current_recommendations = []
        self.current_routine = None
        self._last_saved_recommendation_signature = None

        self.show_dashboard()

    # ------------------------------------------------
    # REGISTRATION
    # ------------------------------------------------

    def show_register(self):

        self.clear_window()

        self.create_header(
            "Create Your Account",
            "Join GlowGuide",
        )

        container = ttk.Frame(self.root, padding=35)
        container.pack(expand=True)

        self.register_entries = {}

        fields = [
            ("Username", "username"),
            ("Email", "email"),
            ("Password", "password"),
            ("Confirm Password", "confirm"),
        ]

        for label, key in fields:

            ttk.Label(container, text=label).pack(anchor="w")

            entry = ttk.Entry(
                container,
                width=38,
                show="*" if key in ("password", "confirm") else "",
            )

            entry.pack(pady=6)
            self.register_entries[key] = entry

        self.create_button(
            container,
            "Register",
            self.register_user,
        ).pack(fill="x", pady=12)

        ttk.Button(
            container,
            text="Back to Login",
            command=self.show_login,
        ).pack(fill="x")

    def register_user(self):

        username = self.register_entries["username"].get().strip()
        email = self.register_entries["email"].get().strip().lower()
        password = self.register_entries["password"].get()
        confirm = self.register_entries["confirm"].get()

        if not all((username, email, password, confirm)):
            messagebox.showwarning(
                "Missing Details",
                "Please complete all fields.",
            )
            return

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            messagebox.showwarning(
                "Invalid Email",
                "Enter a valid email address.",
            )
            return

        if len(password) < 8:
            messagebox.showwarning(
                "Weak Password",
                "Password must contain at least 8 characters.",
            )
            return

        if password != confirm:
            messagebox.showwarning(
                "Password Mismatch",
                "Passwords do not match.",
            )
            return

        result = register_user(
            username,
            email,
            hash_password(password),
        )

        if database_operation_succeeded(result):
            messagebox.showinfo(
                "Success",
                "Account created successfully!",
            )
            self.show_login()
        else:
            messagebox.showerror(
                "Registration Failed",
                "Unable to create account. "
                "The email may already be registered, "
                "or the database may be unavailable.",
            )

    # ------------------------------------------------
    # USER DASHBOARD
    # ------------------------------------------------

    def show_dashboard(self):

        self.clear_window()

        username = self.current_user["username"]

        self.create_header(
            f"Hello, {username}!",
            "Welcome to your personalized skincare dashboard",
        )

        self.show_brand_banner()

        container = ttk.Frame(self.root, padding=30)
        container.pack(expand=True)

        options = [
            ("My Skin Profile", self.show_profile),
            ("Product Catalogue", self.show_catalogue),
            ("My Recommendations", self.show_recommendations),
            ("My AM / PM Routine", self.show_routine),
            ("Saved Routines", self.show_saved_routines),
            ("Recommendation History", self.show_history),
        ]

        for title, command in options:
            self.create_button(
                container,
                title,
                command,
            ).pack(fill="x", pady=7, ipady=4)

        ttk.Button(
            container,
            text="Logout",
            command=self.logout,
        ).pack(fill="x", pady=15)

    def logout(self):

        self.current_user = None
        self.current_recommendations = []
        self.current_routine = None
        self._last_saved_recommendation_signature = None

        self.show_login()

    # ------------------------------------------------
    # USER PROFILE
    # ------------------------------------------------

    def show_profile(self):

        self.clear_window()

        self.create_header(
            "My Skin Profile",
            "Tell us about your skin preferences",
        )

        content = self.get_scrollable_page()

        ttk.Label(
            content,
            text="Skin Type",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(10, 5))

        self.skin_type = tk.StringVar()

        ttk.Combobox(
            content,
            textvariable=self.skin_type,
            values=SKIN_TYPES,
            state="readonly",
            width=35,
        ).pack(anchor="w", pady=5)

        ttk.Label(
            content,
            text="Skin Concerns",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(20, 5))

        self.concern_vars = {}

        concern_frame = ttk.LabelFrame(
            content,
            text="Select all that apply",
            padding=12,
        )
        concern_frame.pack(fill="x", pady=5)

        for index, concern in enumerate(SKIN_CONCERNS):

            variable = tk.BooleanVar()
            self.concern_vars[concern] = variable

            ttk.Checkbutton(
                concern_frame,
                text=concern,
                variable=variable,
            ).grid(
                row=index // 3,
                column=index % 3,
                sticky="w",
                padx=12,
                pady=7,
            )

        ttk.Label(
            content,
            text="Maximum Budget (₹)",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(20, 5))

        self.budget_entry = ttk.Entry(content, width=35)
        self.budget_entry.pack(anchor="w", pady=5)

        ttk.Label(
            content,
            text="Ingredients to Avoid",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(20, 5))

        ttk.Label(
            content,
            text="Enter ingredient names separated by commas.",
        ).pack(anchor="w")

        self.avoid_entry = ttk.Entry(content, width=55)
        self.avoid_entry.pack(anchor="w", pady=6)

        self.create_button(
            content,
            "Save My Profile",
            self.save_profile,
        ).pack(anchor="w", pady=20)

        ttk.Button(
            content,
            text="Back to Dashboard",
            command=self.show_dashboard,
        ).pack(anchor="w", pady=5)

        self.load_profile()

    def load_profile(self):

        preferences = get_user_preferences(
            self.current_user["user_id"]
        )

        if preferences is DATABASE_ERROR:
            self.show_database_error()
            return

        if not preferences:
            return

        saved_type = preferences.get("skin_type") or ""

        if saved_type in SKIN_TYPES:
            self.skin_type.set(saved_type)

        saved_concerns = {
            item.strip().casefold()
            for item in (preferences.get("skin_concerns") or "").split(",")
        }

        for concern, variable in self.concern_vars.items():
            variable.set(concern.casefold() in saved_concerns)

        budget = preferences.get("budget")

        if budget is not None:
            self.budget_entry.insert(0, str(budget))

        self.avoid_entry.insert(
            0,
            preferences.get("avoid_ingredients") or "",
        )

    def save_profile(self):

        skin_type = self.skin_type.get().strip()

        concerns = [
            concern
            for concern, variable in self.concern_vars.items()
            if variable.get()
        ]

        budget_text = self.budget_entry.get().strip()
        avoid = self.avoid_entry.get().strip()

        if skin_type not in SKIN_TYPES:
            messagebox.showwarning(
                "Missing Skin Type",
                "Please select a valid skin type.",
            )
            return

        budget = None

        if budget_text:
            try:
                budget = float(budget_text)

                if not math.isfinite(budget) or budget <= 0:
                    raise ValueError

            except (TypeError, ValueError):
                messagebox.showwarning(
                    "Invalid Budget",
                    "Enter a valid positive budget.",
                )
                return

        result = save_user_preferences(
            self.current_user["user_id"],
            skin_type,
            ", ".join(concerns),
            budget,
            avoid,
        )

        if database_operation_succeeded(result):

            self._last_saved_recommendation_signature = None
            self.current_recommendations = []
            self.current_routine = None

            messagebox.showinfo(
                "Saved",
                "Your skin profile has been saved!",
            )

        else:
            messagebox.showerror(
                "Error",
                "Unable to save your profile. "
                "Please check your database connection.",
            )

    # ------------------------------------------------
    # PRODUCT CATALOGUE
    # ------------------------------------------------

    def get_sample_product_image(self, product):
        """Return a representative image based on product category."""

        category = str(product.get("category") or "").strip().casefold()

        image_map = {
            "cleanser": "gentle_cleanser.jpg",
            "moisturizer": "face_cream.jpg",
            "moisturiser": "face_cream.jpg",
            "serum": "vitamin_c_serum.jpg",
            "sunscreen": "sunscreen.jpg",
            "toner": "face_cream.jpg",
        }

        return image_map.get(category)

    def show_catalogue(self):

        self.clear_window()

        self.create_header(
            "Product Catalogue",
            "Explore the available skincare products",
        )

        content = self.get_scrollable_page()
        products = fetch_active_products()

        if products is DATABASE_ERROR:
            self.show_database_error()

            ttk.Button(
                content,
                text="Back to Dashboard",
                command=self.show_dashboard,
            ).pack(pady=15)
            return

        if not products:
            ttk.Label(
                content,
                text="No products are available yet.",
            ).pack(pady=30)

        for product in products:
            self.create_product_card(content, product)

        ttk.Button(
            content,
            text="Back to Dashboard",
            command=self.show_dashboard,
        ).pack(pady=15)

    def create_product_card(
        self,
        parent,
        product,
        show_score=False,
        score=None,
        reason=None,
    ):

        card = ttk.LabelFrame(
            parent,
            text=product.get("product_name") or "Product",
            padding=12,
        )
        card.pack(fill="x", pady=9, padx=5)

        photo = None

        image_path = resolve_image_path(product.get("image_path"))

        if image_path and image_path.is_file():
            try:
                with Image.open(image_path) as original:
                    image = original.convert("RGB")
                    image.thumbnail((110, 110))

                photo = ImageTk.PhotoImage(image)

            except (OSError, ValueError, UnidentifiedImageError):
                pass

        if photo is None:
            filename = self.get_sample_product_image(product)

            if filename:
                photo = self.load_image(filename, (110, 110))

        if photo:
            self.product_images.append(photo)

            ttk.Label(
                card,
                image=photo,
            ).pack(side="left", padx=10)

        details = ttk.Frame(card)
        details.pack(side="left", fill="both", expand=True)

        fields = [
            ("Brand", product.get("brand") or "Not specified"),
            ("Category", product.get("category") or "Not specified"),
            ("Price", f"₹{product.get('price') or 0}"),
        ]

        for label, value in fields:
            ttk.Label(
                details,
                text=f"{label}: {value}",
            ).pack(anchor="w")

        if show_score:

            ttk.Label(
                details,
                text=f"Match Score: {score}",
            ).pack(anchor="w")

            ttk.Label(
                details,
                text=f"Why recommended: {reason}",
                wraplength=650,
            ).pack(anchor="w", pady=3)

        details_text = [
            ("Description", product.get("description") or "Not available"),
            ("Ingredients", product.get("ingredients") or "Not specified"),
            (
                "Usage",
                product.get("usage_instructions") or "Follow product label",
            ),
        ]

        for label, value in details_text:
            ttk.Label(
                details,
                text=f"{label}: {value}",
                wraplength=650,
            ).pack(anchor="w", pady=3)

    # ------------------------------------------------
    # RECOMMENDATIONS
    # ------------------------------------------------

    def show_recommendations(self):

        self.clear_window()

        self.create_header(
            "Personalized Recommendations",
            "Products selected according to your skin profile",
        )

        preferences = get_user_preferences(
            self.current_user["user_id"]
        )

        if preferences is DATABASE_ERROR:
            self.show_database_error()
            return

        if not preferences:

            ttk.Label(
                self.root,
                text="Please complete your skin profile first.",
            ).pack(pady=20)

            ttk.Button(
                self.root,
                text="Go to My Profile",
                command=self.show_profile,
            ).pack()
            return

        products = fetch_active_products()

        if products is DATABASE_ERROR:
            self.show_database_error()
            return

        matches = recommend_products(
            products,
            preferences.get("skin_type"),
            preferences.get("skin_concerns"),
            preferences.get("budget"),
            preferences.get("avoid_ingredients"),
        )

        self.current_recommendations = matches
        content = self.get_scrollable_page()

        if not matches:

            ttk.Label(
                content,
                text=(
                    "No matching products were found.\n"
                    "Try adjusting your profile or budget."
                ),
                justify="center",
            ).pack(pady=30)

        else:

            ttk.Label(
                content,
                text=f"{len(matches)} matching products found",
                style="Heading.TLabel",
            ).pack(anchor="w", pady=10)

            for item in matches:
                self.create_product_card(
                    content,
                    item["product"],
                    show_score=True,
                    score=item["score"],
                    reason=item["reason"],
                )

            signature = (
                self.current_user["user_id"],
                tuple(
                    (
                        item["product"].get("product_id"),
                        item["score"],
                        item["reason"],
                    )
                    for item in matches
                ),
            )

            if signature != self._last_saved_recommendation_signature:

                result = save_recommendations(
                    self.current_user["user_id"],
                    matches,
                )

                if database_operation_succeeded(result):
                    self._last_saved_recommendation_signature = signature

                else:
                    messagebox.showwarning(
                        "History Not Saved",
                        "Recommendations were generated, but "
                        "their history could not be saved.",
                    )

        buttons = ttk.Frame(content)
        buttons.pack(pady=15)

        self.create_button(
            buttons,
            "Generate My Routine",
            self.show_routine,
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Back to Dashboard",
            command=self.show_dashboard,
        ).pack(side="left", padx=5)

    # ------------------------------------------------
    # SKINCARE ROUTINE
    # ------------------------------------------------

    def show_routine(self):

        self.clear_window()

        self.create_header(
            "My Skincare Routine",
            "Your personalized morning and evening routine",
        )

        content = self.get_scrollable_page()

        preferences = get_user_preferences(
            self.current_user["user_id"]
        )

        if preferences is DATABASE_ERROR:
            self.show_database_error()
            return

        if not preferences:

            ttk.Label(
                content,
                text="Please complete your skin profile first.",
            ).pack(pady=20)

            ttk.Button(
                content,
                text="Go to My Profile",
                command=self.show_profile,
            ).pack()
            return

        products = fetch_active_products()

        if products is DATABASE_ERROR:
            self.show_database_error()
            return

        matches = recommend_products(
            products,
            preferences.get("skin_type"),
            preferences.get("skin_concerns"),
            preferences.get("budget"),
            preferences.get("avoid_ingredients"),
        )

        self.current_recommendations = matches

        routine = generate_skincare_routine(matches)
        self.current_routine = routine

        for routine_type, title in [
            ("AM", "Morning Routine"),
            ("PM", "Evening Routine"),
        ]:

            frame = ttk.LabelFrame(
                content,
                text=title,
                padding=15,
            )
            frame.pack(fill="x", pady=12)

            for index, step in enumerate(routine[routine_type], start=1):
                ttk.Label(
                    frame,
                    text=f"{index}. {step}",
                    wraplength=800,
                ).pack(anchor="w", pady=5)

        self.create_button(
            content,
            "Save My Routine",
            self.save_routine,
        ).pack(anchor="w", pady=15)

        ttk.Label(
            content,
            text=(
                "Skincare suggestions are informational only. "
                "Check product labels, patch-test new products, "
                "and consult a dermatologist for persistent skin concerns."
            ),
            wraplength=850,
            foreground=MUTED,
        ).pack(anchor="w", pady=10)

        ttk.Button(
            content,
            text="View Saved Routines",
            command=self.show_saved_routines,
        ).pack(anchor="w", pady=5)

        ttk.Button(
            content,
            text="Back to Dashboard",
            command=self.show_dashboard,
        ).pack(anchor="w", pady=8)

    def save_routine(self):

        if not self.current_routine:
            messagebox.showwarning(
                "No Routine",
                "Generate a routine before saving.",
            )
            return

        routines = [
            (
                "AM",
                "Personalized Morning Routine",
                "\n".join(self.current_routine["AM"]),
            ),
            (
                "PM",
                "Personalized Evening Routine",
                "\n".join(self.current_routine["PM"]),
            ),
        ]

        result = save_skincare_routines(
            self.current_user["user_id"],
            routines,
        )

        if database_operation_succeeded(result):
            messagebox.showinfo(
                "Saved",
                "Your AM and PM routines have been saved.\n"
                "Your previous saved AM/PM routines were updated.",
            )
        else:
            messagebox.showerror(
                "Error",
                "Unable to save your routines. "
                "No partial routine was saved.",
            )

    # ------------------------------------------------
    # VIEW SAVED ROUTINES
    # ------------------------------------------------

    def show_saved_routines(self):

        self.clear_window()

        self.create_header(
            "My Saved Routines",
            "Your latest saved morning and evening routines",
        )

        content = self.get_scrollable_page()

        routines = get_skincare_routines(
            self.current_user["user_id"]
        )

        if routines is DATABASE_ERROR:
            self.show_database_error()

        elif not routines:

            ttk.Label(
                content,
                text="You haven't saved any skincare routines yet.",
            ).pack(pady=30)

        else:

            for routine in routines:

                routine_type = (
                    routine.get("routine_type") or ""
                ).upper()

                title = routine.get("routine_name") or (
                    "Morning Routine"
                    if routine_type == "AM"
                    else "Evening Routine"
                )

                frame = ttk.LabelFrame(
                    content,
                    text=title,
                    padding=15,
                )
                frame.pack(fill="x", pady=10)

                steps = routine.get("routine_steps") or ""

                for index, step in enumerate(steps.splitlines(), start=1):

                    if step.strip():
                        ttk.Label(
                            frame,
                            text=f"{index}. {step}",
                            wraplength=800,
                        ).pack(anchor="w", pady=4)

                created_at = routine.get("created_at")

                if created_at:
                    ttk.Label(
                        frame,
                        text=f"Last saved: {created_at}",
                        foreground=MUTED,
                    ).pack(anchor="w", pady=(8, 0))

        ttk.Button(
            content,
            text="Back to Dashboard",
            command=self.show_dashboard,
        ).pack(anchor="w", pady=12)

    # ------------------------------------------------
    # RECOMMENDATION HISTORY
    # ------------------------------------------------

    def show_history(self):

        self.clear_window()

        self.create_header(
            "Recommendation History",
            "Your recommendations, organized by session",
        )

        content = self.get_scrollable_page()

        history = get_recommendation_history(
            self.current_user["user_id"]
        )

        if history is DATABASE_ERROR:

            self.show_database_error()

        elif not history:

            ttk.Label(
                content,
                text="You don't have any recommendation history yet.",
            ).pack(pady=25)

        else:

            # Group products by recommendation date and time.
            sessions = {}

            for item in history:
                timestamp = item["recommended_at"]
                sessions.setdefault(timestamp, []).append(item)

            columns = (
                "Product",
                "Brand",
                "Category",
                "Price",
                "Score",
            )

            for timestamp, products in sessions.items():

                if hasattr(timestamp, "strftime"):
                    date_text = timestamp.strftime(
                        "%d %b %Y, %I:%M:%S %p"
                    )
                else:
                    date_text = str(timestamp)

                session_frame = ttk.LabelFrame(
                    content,
                    text=f"  Recommended on: {date_text}  ",
                    padding=10,
                )

                session_frame.pack(
                    fill="x",
                    expand=True,
                    pady=10,
                )

                tree = ttk.Treeview(
                    session_frame,
                    columns=columns,
                    show="headings",
                    height=min(len(products), 8),
                )

                column_widths = {
                    "Product": 220,
                    "Brand": 140,
                    "Category": 140,
                    "Price": 100,
                    "Score": 100,
                }

                for column in columns:
                    tree.heading(column, text=column)
                    tree.column(
                        column,
                        width=column_widths[column],
                        anchor="center",
                    )

                for item in products:
                    tree.insert(
                        "",
                        "end",
                        values=(
                            item["product_name"],
                            item["brand"] or "-",
                            item["category"] or "-",
                            item["price"],
                            item["score"],
                        ),
                    )

                tree.pack(fill="x", expand=True)

                ttk.Label(
                    session_frame,
                    text=f"{len(products)} product(s) recommended",
                ).pack(anchor="w", pady=(8, 0))

        ttk.Button(
            content,
            text="Back to Dashboard",
            command=self.show_dashboard,
        ).pack(pady=15)

    # ------------------------------------------------
    # ADMIN LOGIN
    # ------------------------------------------------

    def show_admin_login(self):

        self.clear_window()

        self.create_header(
            "Administrator Login",
            "Manage the GlowGuide product catalogue",
        )

        container = ttk.Frame(self.root, padding=35)
        container.pack(expand=True)

        ttk.Label(container, text="Username").pack(anchor="w")

        self.admin_username = ttk.Entry(container, width=38)
        self.admin_username.pack(pady=6)

        ttk.Label(container, text="Password").pack(anchor="w")

        self.admin_password = ttk.Entry(
            container,
            width=38,
            show="*",
        )
        self.admin_password.pack(pady=6)

        self.create_button(
            container,
            "Admin Login",
            self.admin_login,
        ).pack(fill="x", pady=12)

        ttk.Button(
            container,
            text="First-Time Admin Setup",
            command=self.setup_first_admin,
        ).pack(fill="x", pady=4)

        ttk.Button(
            container,
            text="Back",
            command=self.show_login,
        ).pack(fill="x", pady=4)

    def setup_first_admin(self):

        result = execute_query(
            "SELECT COUNT(*) AS total FROM admins",
            fetch=True,
        )

        if result is DATABASE_ERROR:
            messagebox.showerror(
                "Database Error",
                "Could not check administrator accounts.",
            )
            return

        if result[0]["total"] > 0:
            messagebox.showwarning(
                "Setup Unavailable",
                "An administrator account already exists.",
            )
            return

        username = simpledialog.askstring(
            "Admin Setup",
            "Choose an administrator username:",
            parent=self.root,
        )

        if username is None:
            return

        username = username.strip()

        if not username:
            messagebox.showwarning(
                "Invalid Username",
                "Administrator username cannot be empty.",
            )
            return

        password = simpledialog.askstring(
            "Admin Setup",
            "Choose an administrator password:",
            show="*",
            parent=self.root,
        )

        if password is None:
            return

        if len(password) < 8:
            messagebox.showwarning(
                "Weak Password",
                "Use at least 8 characters.",
            )
            return

        result = create_admin(username, hash_password(password))

        if database_operation_succeeded(result):
            messagebox.showinfo(
                "Success",
                "Administrator account created.",
            )
        else:
            messagebox.showerror(
                "Error",
                "Unable to create administrator account.",
            )

    def admin_login(self):

        username = self.admin_username.get().strip()
        password = self.admin_password.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Details",
                "Enter your administrator credentials.",
            )
            return

        admin = get_admin_by_username(username)

        if admin is DATABASE_ERROR:
            self.show_database_error()
            return

        if not admin or not verify_password(
            password,
            admin.get("password_hash"),
        ):
            messagebox.showerror(
                "Login Failed",
                "Invalid administrator credentials.",
            )
            return

        self.show_admin_dashboard()

    # ------------------------------------------------
    # ADMIN DASHBOARD
    # ------------------------------------------------

    def show_admin_dashboard(self):

        self.clear_window()

        self.create_header(
            "Admin Dashboard",
            "Manage your product catalogue",
        )

        container = ttk.Frame(self.root, padding=30)
        container.pack(expand=True)

        self.create_button(
            container,
            "View Products",
            self.admin_view_products,
        ).pack(fill="x", pady=8)

        self.create_button(
            container,
            "Add New Product",
            self.admin_add_product,
        ).pack(fill="x", pady=8)

        ttk.Button(
            container,
            text="Logout",
            command=self.show_login,
        ).pack(fill="x", pady=15)

    def admin_view_products(self):

        self.clear_window()

        self.create_header(
            "Manage Products",
            "View, edit or deactivate catalogue products",
        )

        content = self.get_scrollable_page()
        products = fetch_active_products()

        if products is DATABASE_ERROR:
            self.show_database_error()
            return

        if not products:
            ttk.Label(
                content,
                text="No active products are available.",
            ).pack(pady=20)

        columns = ("ID", "Name", "Brand", "Category", "Price")

        tree = ttk.Treeview(
            content,
            columns=columns,
            show="headings",
            height=15,
        )

        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=140, anchor="center")

        for product in products:
            tree.insert(
                "",
                "end",
                iid=str(product["product_id"]),
                values=(
                    product["product_id"],
                    product["product_name"],
                    product["brand"] or "",
                    product["category"] or "",
                    product["price"] or 0,
                ),
            )

        tree.pack(fill="both", expand=True, pady=12)

        def selected_product():

            selection = tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Select Product",
                    "Please select a product first.",
                )
                return None

            return int(selection[0])

        def edit_selected():

            product_id = selected_product()

            if product_id is None:
                return

            product = next(
                (
                    item for item in products
                    if item["product_id"] == product_id
                ),
                None,
            )

            if product:
                self.admin_product_form(product=product)

        def deactivate_selected():

            product_id = selected_product()

            if product_id is None:
                return

            if not messagebox.askyesno(
                "Confirm",
                "Deactivate this product?",
            ):
                return

            result = deactivate_product(product_id)

            if database_operation_succeeded(result):
                messagebox.showinfo(
                    "Success",
                    "Product deactivated.",
                )
                self.admin_view_products()
            else:
                messagebox.showerror(
                    "Error",
                    "Unable to deactivate product.",
                )

        buttons = ttk.Frame(content)
        buttons.pack(pady=10)

        self.create_button(
            buttons,
            "Edit Selected",
            edit_selected,
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Deactivate Selected",
            command=deactivate_selected,
        ).pack(side="left", padx=5)

        ttk.Button(
            content,
            text="Back to Admin Dashboard",
            command=self.show_admin_dashboard,
        ).pack(pady=10)

    # ------------------------------------------------
    # ADD / EDIT PRODUCT
    # ------------------------------------------------

    def admin_add_product(self):
        self.admin_product_form()

    def admin_product_form(self, product=None):

        self.clear_window()

        editing = product is not None

        self.create_header(
            "Edit Product" if editing else "Add Product",
            "Enter the product information",
        )

        content = self.get_scrollable_page()

        fields = [
            ("Product Name", "product_name"),
            ("Brand", "brand"),
            ("Category", "category"),
            ("Description", "description"),
            ("Skin Types", "skin_type"),
            ("Skin Concerns", "skin_concerns"),
            ("Ingredients", "ingredients"),
            ("Price", "price"),
            ("Image Path", "image_path"),
            ("Usage Instructions", "usage_instructions"),
        ]

        self.product_entries = {}

        for label, key in fields:

            ttk.Label(
                content,
                text=label,
                style="Heading.TLabel",
            ).pack(anchor="w", pady=(10, 3))

            if key in ("description", "usage_instructions"):
                widget = tk.Text(
                    content,
                    height=3,
                    width=75,
                    wrap="word",
                    font=("Arial", 10),
                )
                widget.pack(fill="x", pady=4)

            else:
                widget = ttk.Entry(content, width=75)
                widget.pack(fill="x", pady=4)

            if product:

                value = product.get(key) or ""

                if isinstance(widget, tk.Text):
                    widget.insert("1.0", value)
                else:
                    widget.insert(0, str(value))

            self.product_entries[key] = widget

        def browse_image():

            path = filedialog.askopenfilename(
                title="Choose Product Image",
                filetypes=[
                    ("Image Files", "*.png *.jpg *.jpeg *.webp")
                ],
            )

            if path:
                entry = self.product_entries["image_path"]
                entry.delete(0, tk.END)
                entry.insert(0, path)

        ttk.Button(
            content,
            text="Browse Image",
            command=browse_image,
        ).pack(anchor="w", pady=8)

        def get_value(key):

            widget = self.product_entries[key]

            if isinstance(widget, tk.Text):
                return widget.get("1.0", "end-1c").strip()

            return widget.get().strip()

        def save():

            data = {
                key: get_value(key)
                for key in self.product_entries
            }

            required_fields = (
                "product_name",
                "category",
                "skin_type",
                "skin_concerns",
                "ingredients",
                "price",
            )

            for key in required_fields:

                if not data[key]:
                    messagebox.showwarning(
                        "Missing Information",
                        f"{key.replace('_', ' ').title()} is required.",
                    )
                    return

            try:
                data["price"] = float(data["price"])

                if not math.isfinite(data["price"]) or data["price"] <= 0:
                    raise ValueError

            except (TypeError, ValueError):
                messagebox.showwarning(
                    "Invalid Price",
                    "Enter a valid price greater than ₹0.",
                )
                return

            image_path = data["image_path"]
            copied_image_path = None

            if image_path:

                path = resolve_image_path(image_path)

                if path is None or not path.is_file():
                    messagebox.showwarning(
                        "Invalid Image",
                        "The selected image file does not exist.",
                    )
                    return

                try:
                    with Image.open(path) as image:
                        image.verify()

                except (OSError, ValueError, UnidentifiedImageError):
                    messagebox.showwarning(
                        "Invalid Image",
                        "Please select a valid image file.",
                    )
                    return

                try:
                    try:
                        relative_path = path.relative_to(BASE_DIR.resolve())
                        data["image_path"] = relative_path.as_posix()

                    except ValueError:

                        images_dir = BASE_DIR / "images"
                        images_dir.mkdir(parents=True, exist_ok=True)

                        filename = (
                            f"{secrets.token_hex(8)}"
                            f"{path.suffix.lower()}"
                        )

                        destination = images_dir / filename
                        shutil.copy2(path, destination)
                        copied_image_path = destination

                        data["image_path"] = (
                            destination.resolve()
                            .relative_to(BASE_DIR.resolve())
                            .as_posix()
                        )

                except OSError:
                    messagebox.showerror(
                        "Image Error",
                        "Unable to copy or save the product image.",
                    )
                    return

            data["is_active"] = (
                bool(product.get("is_active"))
                if editing
                else True
            )

            if editing:
                result = update_product(product["product_id"], data)
            else:
                result = add_product(data)

            if database_operation_succeeded(result):

                messagebox.showinfo(
                    "Success",
                    "Product saved successfully.",
                )

                self.admin_view_products()

            else:

                if copied_image_path and copied_image_path.exists():
                    try:
                        copied_image_path.unlink()
                    except OSError:
                        pass

                messagebox.showerror(
                    "Error",
                    "Unable to save product. Check the database.",
                )

        self.create_button(
            content,
            "Save Product",
            save,
        ).pack(anchor="w", pady=15)

        ttk.Button(
            content,
            text="Back to Product List",
            command=self.admin_view_products,
        ).pack(anchor="w", pady=5)


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    root = tk.Tk()
    app = GlowGuideApp(root)
    root.mainloop()
