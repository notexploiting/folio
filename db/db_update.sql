/*
!! IMPORTANT FOR UPDATE OR DELETE OR OTHER MODIFYING STATEMENTS !!
Code should be executed line by line (start with BEGIN, end with ROLLBACK/COMMIT)
Destructive scripts should be wrapped in safe blocks BEGIN and ROLLBACK.
Only change ROLLBACK to COMMIT when confident
*/

/* ----------------------------------------------------------------------
CORRECTING RECEIPTS
*/ ----------------------------------------------------------------------
BEGIN;

UPDATE receipts
SET
    total_cost = 50,
    notes = 'Updated total after being sued adjustment'
WHERE id = 3;

ROLLBACK;

/* ----------------------------------------------------------------------
UPDATING INVENTORY
*/ ----------------------------------------------------------------------
BEGIN;

UPDATE receipt_items
SET quantity_remaining = GREATEST(0, quantity_remaining - 1.00)
WHERE id = 2;

ROLLBACK;

/* ----------------------------------------------------------------------
CATEGORIZING BULK ITEMS
*/ ----------------------------------------------------------------------
BEGIN;

UPDATE receipt_items
SET canonical_id = (SELECT id FROM canonical_items WHERE standard_name = 'Greek Yogurt')
WHERE canonical_id IS NULL
  AND raw_name ILIKE '%CHOBANI%';

ROLLBACK;