"""Database access layer for GlowGuide."""

import os
from pathlib import Path

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


DB_CONFIG = {
    "host": os.getenv("GLOWGUIDE_DB_HOST", "localhost"),
    "user": os.getenv("GLOWGUIDE_DB_USER", "root"),
    "password": os.getenv("GLOWGUIDE_DB_PASSWORD", ""),
    "database": os.getenv("GLOWGUIDE_DB_NAME", "glowguide"),
    "autocommit": False,
}

# Distinguishes a database failure from a successful query
# that returned no matching records.
DATABASE_ERROR = object()


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    """Return a connected MySQL connection or None."""

    connection = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

        connection.close()

    except Error as exc:
        print(f"Database connection error: {exc}")

        if connection is not None:
            try:
                connection.close()
            except Error:
                pass

    return None


# --------------------------------------------------
# GENERAL QUERY EXECUTION
# --------------------------------------------------

def execute_query(query, values=None, fetch=False):
    """
    Execute one SQL statement.

    SELECT:
        Returns a list of dictionaries.

    INSERT / UPDATE / DELETE:
        Returns the inserted ID or affected row count.

    Failure:
        Returns DATABASE_ERROR.
    """

    connection = get_connection()

    if connection is None:
        return DATABASE_ERROR

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            query,
            values if values is not None else ()
        )

        if fetch:
            return cursor.fetchall()

        connection.commit()

        if cursor.lastrowid:
            return cursor.lastrowid

        return cursor.rowcount

    except Error as exc:
        try:
            connection.rollback()
        except Error:
            pass

        print(f"Database query error: {exc}")
        return DATABASE_ERROR

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Error:
                pass

        try:
            connection.close()
        except Error:
            pass


# --------------------------------------------------
# MULTIPLE INSERTS IN ONE TRANSACTION
# --------------------------------------------------

def execute_many(query, values):
    """Execute multiple statements in one transaction."""

    if not values:
        return 0

    connection = get_connection()

    if connection is None:
        return DATABASE_ERROR

    cursor = None

    try:
        cursor = connection.cursor()
        cursor.executemany(query, values)

        affected_rows = cursor.rowcount

        connection.commit()
        return affected_rows

    except Error as exc:
        try:
            connection.rollback()
        except Error:
            pass

        print(f"Database transaction error: {exc}")
        return DATABASE_ERROR

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Error:
                pass

        try:
            connection.close()
        except Error:
            pass


# --------------------------------------------------
# USER OPERATIONS
# --------------------------------------------------

def register_user(username, email, password_hash):
    return execute_query(
        """
        INSERT INTO users
        (username, email, password_hash)
        VALUES (%s, %s, %s)
        """,
        (username, email, password_hash)
    )


def get_user_by_email(email):
    rows = execute_query(
        """
        SELECT user_id, username, email, password_hash
        FROM users
        WHERE email = %s
        """,
        (email,),
        fetch=True
    )

    if rows is DATABASE_ERROR:
        return DATABASE_ERROR

    return rows[0] if rows else None


def get_user_by_id(user_id):
    rows = execute_query(
        """
        SELECT user_id, username, email
        FROM users
        WHERE user_id = %s
        """,
        (user_id,),
        fetch=True
    )

    if rows is DATABASE_ERROR:
        return DATABASE_ERROR

    return rows[0] if rows else None


# --------------------------------------------------
# PRODUCT OPERATIONS
# --------------------------------------------------

def fetch_active_products():
    return execute_query(
        """
        SELECT *
        FROM products
        WHERE is_active = TRUE
        ORDER BY product_name
        """,
        fetch=True
    )


def get_product_by_id(product_id):
    rows = execute_query(
        """
        SELECT *
        FROM products
        WHERE product_id = %s
        """,
        (product_id,),
        fetch=True
    )

    if rows is DATABASE_ERROR:
        return DATABASE_ERROR

    return rows[0] if rows else None


def add_product(product):
    query = """
        INSERT INTO products (
            product_name,
            brand,
            category,
            description,
            skin_type,
            skin_concerns,
            ingredients,
            price,
            image_path,
            usage_instructions,
            is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        product["product_name"],
        product.get("brand"),
        product.get("category"),
        product.get("description"),
        product.get("skin_type"),
        product.get("skin_concerns"),
        product.get("ingredients"),
        product.get("price"),
        product.get("image_path"),
        product.get("usage_instructions"),
        product.get("is_active", True),
    )

    return execute_query(query, values)


def update_product(product_id, product):
    query = """
        UPDATE products SET
            product_name = %s,
            brand = %s,
            category = %s,
            description = %s,
            skin_type = %s,
            skin_concerns = %s,
            ingredients = %s,
            price = %s,
            image_path = %s,
            usage_instructions = %s,
            is_active = %s
        WHERE product_id = %s
    """

    values = (
        product["product_name"],
        product.get("brand"),
        product.get("category"),
        product.get("description"),
        product.get("skin_type"),
        product.get("skin_concerns"),
        product.get("ingredients"),
        product.get("price"),
        product.get("image_path"),
        product.get("usage_instructions"),
        product.get("is_active", True),
        product_id,
    )

    return execute_query(query, values)


def deactivate_product(product_id):
    return execute_query(
        """
        UPDATE products
        SET is_active = FALSE
        WHERE product_id = %s
        """,
        (product_id,)
    )


# --------------------------------------------------
# USER PREFERENCES
# --------------------------------------------------

def save_user_preferences(
    user_id,
    skin_type,
    skin_concerns,
    budget,
    avoid_ingredients
):
    query = """
        INSERT INTO user_preferences (
            user_id,
            skin_type,
            skin_concerns,
            budget,
            avoid_ingredients
        )
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            skin_type = VALUES(skin_type),
            skin_concerns = VALUES(skin_concerns),
            budget = VALUES(budget),
            avoid_ingredients = VALUES(avoid_ingredients)
    """

    return execute_query(
        query,
        (
            user_id,
            skin_type,
            skin_concerns,
            budget,
            avoid_ingredients
        )
    )


def get_user_preferences(user_id):
    rows = execute_query(
        """
        SELECT *
        FROM user_preferences
        WHERE user_id = %s
        """,
        (user_id,),
        fetch=True
    )

    if rows is DATABASE_ERROR:
        return DATABASE_ERROR

    return rows[0] if rows else None


# --------------------------------------------------
# INGREDIENT OPERATIONS
# --------------------------------------------------

def fetch_ingredients():
    return execute_query(
        """
        SELECT *
        FROM ingredients
        ORDER BY ingredient_name
        """,
        fetch=True
    )


def add_ingredient(name, description=None):
    return execute_query(
        """
        INSERT INTO ingredients
        (ingredient_name, description)
        VALUES (%s, %s)
        """,
        (name, description)
    )


# --------------------------------------------------
# RECOMMENDATION HISTORY
# --------------------------------------------------

def save_recommendation(user_id, product_id, reason, score):
    return execute_query(
        """
        INSERT INTO recommendations
        (user_id, product_id, recommendation_reason, score)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, product_id, reason, score)
    )


def save_recommendations(user_id, recommendations):
    """Save a recommendation set in one transaction."""

    values = []

    for item in recommendations:
        product = item["product"]

        values.append((
            user_id,
            product["product_id"],
            item["reason"],
            item["score"]
        ))

    query = """
        INSERT INTO recommendations (
            user_id,
            product_id,
            recommendation_reason,
            score
        )
        VALUES (%s, %s, %s, %s)
    """

    return execute_many(query, values)


def get_recommendation_history(user_id):
    query = """
        SELECT
            r.recommendation_id,
            r.recommendation_reason,
            r.score,
            r.recommended_at,
            p.product_name,
            p.brand,
            p.category,
            p.price
        FROM recommendations r
        JOIN products p
            ON r.product_id = p.product_id
        WHERE r.user_id = %s
        ORDER BY r.recommended_at DESC
    """

    return execute_query(
        query,
        (user_id,),
        fetch=True
    )


# --------------------------------------------------
# SAVED SKINCARE ROUTINES
# --------------------------------------------------

def save_skincare_routine(
    user_id,
    routine_type,
    routine_name,
    routine_steps
):
    return execute_query(
        """
        INSERT INTO skincare_routines (
            user_id,
            routine_type,
            routine_name,
            routine_steps
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            user_id,
            routine_type,
            routine_name,
            routine_steps
        )
    )


def save_skincare_routines(user_id, routines):
    """
    Replace the user's existing routines of the supplied types.

    Deletion and insertion happen in one transaction.
    """

    routines = list(routines or [])

    if not routines:
        return 0

    connection = get_connection()

    if connection is None:
        return DATABASE_ERROR

    cursor = None

    try:
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO skincare_routines (
                user_id,
                routine_type,
                routine_name,
                routine_steps
            )
            VALUES (%s, %s, %s, %s)
        """

        for routine_type, routine_name, routine_steps in routines:

            cursor.execute(
                """
                DELETE FROM skincare_routines
                WHERE user_id = %s
                  AND routine_type = %s
                """,
                (user_id, routine_type)
            )

            cursor.execute(
                insert_query,
                (
                    user_id,
                    routine_type,
                    routine_name,
                    routine_steps
                )
            )

        connection.commit()
        return len(routines)

    except Error as exc:
        try:
            connection.rollback()
        except Error:
            pass

        print(f"Routine save error: {exc}")
        return DATABASE_ERROR

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Error:
                pass

        try:
            connection.close()
        except Error:
            pass


def get_skincare_routines(user_id):
    query = """
        SELECT *
        FROM skincare_routines
        WHERE user_id = %s
        ORDER BY created_at DESC
    """

    return execute_query(
        query,
        (user_id,),
        fetch=True
    )


# --------------------------------------------------
# ADMIN OPERATIONS
# --------------------------------------------------

def create_admin(username, password_hash):
    return execute_query(
        """
        INSERT INTO admins
        (username, password_hash)
        VALUES (%s, %s)
        """,
        (username, password_hash)
    )


def get_admin_by_username(username):
    rows = execute_query(
        """
        SELECT *
        FROM admins
        WHERE username = %s
        """,
        (username,),
        fetch=True
    )

    if rows is DATABASE_ERROR:
        return DATABASE_ERROR

    return rows[0] if rows else None


# --------------------------------------------------
# CONNECTION TEST
# --------------------------------------------------

if __name__ == "__main__":

    connection = get_connection()

    if connection:
        print("GlowGuide database connected successfully!")
        connection.close()
    else:
        print(
            "GlowGuide database connection failed. "
            "Check MySQL and your .env file."
        )