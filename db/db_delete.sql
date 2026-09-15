/*
!! IMPORTANT FOR UPDATE OR DELETE OR OTHER MODIFYING STATEMENTS !!
Code should be executed line by line (start with BEGIN, end with ROLLBACK/COMMIT)
Destructive scripts should be wrapped in safe blocks BEGIN and ROLLBACK.
Only change ROLLBACK to COMMIT when confident
*/

/* ----------------------------------------------------------------------
DELETING A RECEIPT ENTRY AND ALL ITS LINE ITEMS
Note that `receipt_items` has `ON DELETE CASCADE` on `receipt_id`
*/ ----------------------------------------------------------------------
BEGIN;

DELETE
FROM receipts
WHERE id = 1 OR id = 2 OR id = 3;  -- delete receipt

SELECT *
FROM receipts; -- verify

ROLLBACK;

/* ----------------------------------------------------------------------
DELETING A SINGLE RECEIPT ITEM, LEAVING RECEIPT ENTRY INTACT
Note that `receipt_items` has `ON DELETE CASCADE` on `receipt_id`
*/ ----------------------------------------------------------------------
BEGIN;

DELETE
FROM receipt_items
WHERE id = 2;

-- Recalculate and update the parent receipt total if necessary
-- UPDATE receipts r
-- SET total_cost = COALESCE((
--     SELECT SUM(price)
--     FROM receipt_items
--     WHERE receipt_id = r.id), 0.00) + r.tax_amount + r.tip_amount
-- WHERE r.id = (SELECT receipt_id FROM receipt_items WHERE id = 2);

ROLLBACK;

/* ----------------------------------------------------------------------
DELETING ENTIRE TABLES
Note that `receipt_items` has `ON DELETE CASCADE` on `receipt_id`
If DROP TABLE is hanging, there might be a transaction blocking it. Consider killing blockers, and then dropping
*/ ----------------------------------------------------------------------
BEGIN;

DROP TABLE IF EXISTS receipt_items CASCADE;
SELECT to_regclass('public.receipt_items');
SELECT relname FROM pg_class WHERE relname = 'receipt_items';

DROP TABLE IF EXISTS receipts CASCADE;
SELECT to_regclass('public.receipts');

DROP TABLE IF EXISTS canonical_items CASCADE;
SELECT to_regclass('public.canonical_items');

DROP INDEX IF EXISTS idx_receipt_items_receipt_id;
DROP INDEX IF EXISTS idx_canonical_trgm;

ROLLBACK;

/* ----------------------------------------------------------------------
DELETING CANONICAL ITEMS
receipt_items.canonical_id has a restrictive foreign key constraint (REFERENCES, not CASCADE)
So if we delete an in-use canonical item, PostgreSQL stops the deletion process
We'll have to nullify references first in receipt_items, then we can remove canonical items
*/ ----------------------------------------------------------------------

BEGIN;

UPDATE receipt_items
SET canonical_id = NULL
WHERE canonical_id = 12;

DELETE
FROM canonical_items
WHERE id = 12

ROLLBACK;