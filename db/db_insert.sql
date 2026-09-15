/*
!! IMPORTANT FOR UPDATE OR DELETE OR OTHER MODIFYING STATEMENTS !!
Code should be executed line by line (start with BEGIN, end with ROLLBACK/COMMIT)
Destructive scripts should be wrapped in safe blocks BEGIN and ROLLBACK.
Only change ROLLBACK to COMMIT when confident
*/

/* ----------------------------------------------------------------------
INSERTING NEW PAYMENT METHOD
Avoid duplicates by checking uniqueness or ignoring conflicts
*/ ----------------------------------------------------------------------
BEGIN;

INSERT
INTO payment_methods (name, type)
VALUES ('Apple Card', 'Credit')
ON CONFLICT (name) DO NOTHING
RETURNING *;

SELECT * FROM payment_methods;

INSERT
INTO payment_methods (name, type)
VALUES ('Capital One Venture X', 'Credit')
ON CONFLICT (name) DO NOTHING
RETURNING *;

SELECT * FROM payment_methods;

ROLLBACK;

/* ----------------------------------------------------------------------
INSERTING NEW CANONICAL ITEM
*/ ----------------------------------------------------------------------
BEGIN;

INSERT
INTO canonical_items (standard_name, default_category)
VALUES ('Oat Milk', 'Dairy & Alternatives')
ON CONFLICT (standard_name) DO UPDATE
  SET default_category = EXCLUDED.default_category
RETURNING id;

SELECT * FROM canonical_items;

ROLLBACK;

/* ----------------------------------------------------------------------
INSERTING NEW RECEIPT + ASSOCIATED ITEMS
Utilize a CTE with `RETURNING id` to easily reference newly created primary key
Note that your query doesn't have to include every column
*/ ----------------------------------------------------------------------
BEGIN;

WITH new_receipt AS (
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
        payment_method_id,
        card_last_four,
        receipt_type,
        file_path,
        notes
    ) VALUES (
        'Trader Joe''s',
        '123 Main St',
        'https://www.traderjoes.com',
        '123-456-7890',
        '2026-09-14',
        '14:20:00',
        'USD',
        1.85,
        0.00,
        24.50,
        (SELECT id FROM payment_methods WHERE name = 'CapitalOne Savor Card'),
        '4321',
        'physical',
        'drive/me/traderjoes-2026-09-14-14-20-00',
        'Weekly snack run'
    )
    RETURNING id
)


INSERT
INTO receipt_items (
    receipt_id,
    raw_name,
    specific_name,
    canonical_id,
    category,
    price,
    quantity_purchased,
    unit,
    quantity_remaining,
    expiration_date
) VALUES
(
    (SELECT id FROM new_receipt),
    'TJ ORG OAT BVRG',
    'Trader Joe''s Organic Oat Beverage',
    (SELECT id FROM canonical_items WHERE standard_name = 'Oat Milk'),
    'Groceries',
    3.99,
    2.00,
    'carton',
    2.00,
    '2027-09-09'
);

SELECT * FROM receipts;

ROLLBACK;