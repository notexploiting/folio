# --------- POSTGRESQL DATABASE INTERACTIONS ---------

import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to a database using environment variables and return a new Connection instance
def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        row_factory=dict_row
    )

# Fetch all payment methods from the database and return them as a list of dictionaries
def get_payment_methods():
    with get_db_connection() as conn:
        query = """
        SELECT id, name
        FROM payment_methods
        ORDER BY id
        """
        return conn.execute(query).fetchall()

# Fuzzy match a standard name against canonical items in the database and return the best match if above the threshold
# Threshold 0.4 is chosen since things like SELECT similarity('greek yogurt', 'yogurt') return 0.54
def fuzzy_match_canonical(standard_name: str, threshold: float = 0.4):
    with get_db_connection() as conn:
        query = """
        SELECT id, standard_name, similarity(standard_name, %(standard_name)s) AS sim
        FROM canonical_items
        WHERE similarity(standard_name, %(standard_name)s) >= CAST(%(threshold)s AS DOUBLE PRECISION)
        ORDER BY sim DESC LIMIT 1
        """
        return conn.execute(query, {"standard_name": standard_name, "threshold": threshold}).fetchone()

# If a canonical item with the given standard name exists, return its ID
# Otherwise, insert a new canonical item with the given standard name and category, and return the new ID
# It is important to fuzzy match first to avoid duplicates, but this function does NOT do that
def ensure_canonical_item(standard_name: str, category: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
            SELECT id 
            FROM canonical_items 
            WHERE standard_name = %(standard_name)s
            """
            cur.execute(query, {"standard_name": standard_name})
            existing = cur.fetchone()
            if existing: return existing['id']

            query = """
            INSERT INTO canonical_items (standard_name, default_category) 
            VALUES (%(standard_name)s, %(default_category)s) 
            RETURNING id
            """
            cur.execute(query, {"standard_name": standard_name, "default_category": category})
            return cur.fetchone()['id']

# Add a new receipt and its associated items to the database. 
# receipt_data is a dictionary containing the receipt information
# items_data is a list of dictionaries containing the item information
def insert_receipt_full(receipt_data, items_data):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
INSERT INTO receipts (
                store_name, 
                store_address,
                store_website,
                store_phone,
                purchase_date, 
                purchase_time,
                currency, 
                tax_amount,
                tip_amount,
                total_cost, 
                card_last_four,
                payment_method_id, 
                receipt_type, 
                file_path
            )
            VALUES (
                %(store_name)s, 
                %(store_address)s,
                %(store_website)s,
                %(store_phone)s,
                %(purchase_date)s, 
                %(purchase_time)s,
                %(currency)s, 
                %(tax_amount)s,
                %(tip_amount)s,
                %(total_cost)s,
                %(card_last_four)s,
                %(payment_method_id)s, 
                %(receipt_type)s, 
                %(file_path)s)
            RETURNING id;
            """
            cur.execute(query, receipt_data)
            receipt_id = cur.fetchone()['id']
            
            for item in items_data:
                item['receipt_id'] = receipt_id
                query = """
                INSERT INTO receipt_items (
                    receipt_id, 
                    raw_name, 
                    specific_name, 
                    canonical_id, 
                    category, 
                    price, 
                    quantity_purchased, 
                    unit, 
                    quantity_remaining, 
                    expiration_date)
                VALUES (
                    %(receipt_id)s, 
                    %(raw_name)s, 
                    %(specific_name)s, 
                    %(canonical_id)s, 
                    %(category)s, 
                    %(price)s, 
                    %(quantity_purchased)s, 
                    %(unit)s, 
                    %(quantity_remaining)s, 
                    %(expiration_date)s)
                """
                cur.execute(query, item)
            conn.commit()
            return receipt_id

# For testing purposes, delete a receipt and its associated items from the database.
def delete_receipt(receipt_id: int):
    # ON DELETE CASCADE handles the items automatically
    with get_db_connection() as conn:
        conn.execute("DELETE FROM receipts WHERE id = %(receipt_id)s", {"receipt_id": receipt_id})
        conn.commit()

if __name__ == "__main__":
    # print(fuzzy_match_canonical("iPhones", 0.65))
    # print(ensure_canonical_item("iPad", "Electronics"))


    print(get_payment_methods())

