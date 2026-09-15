/*
!! IMPORTANT FOR UPDATE OR DELETE OR OTHER MODIFYING STATEMENTS !!
Code should be executed line by line (start with BEGIN, end with ROLLBACK/COMMIT)
Destructive scripts should be wrapped in safe blocks BEGIN and ROLLBACK.
Only change ROLLBACK to COMMIT when confident
*/

/* ----------------------------------------------------------------------
MANAGING AUTO-INCREMENTING SEQUENCES (SERIAL)
Manual row edits or test data deletions can cause primary key sequences to fall out of sync.
*/ ----------------------------------------------------------------------
BEGIN;

-- Reset all sequence counters to the current table maximum
SELECT setval(pg_get_serial_sequence('payment_methods', 'id'), COALESCE(MAX(id), 1)) FROM payment_methods;
SELECT setval(pg_get_serial_sequence('receipts', 'id'), COALESCE(MAX(id), 1)) FROM receipts;
SELECT setval(pg_get_serial_sequence('canonical_items', 'id'), COALESCE(MAX(id), 1)) FROM canonical_items;
SELECT setval(pg_get_serial_sequence('receipt_items', 'id'), COALESCE(MAX(id), 1)) FROM receipt_items;

-- Check current sequence position vs actual max ID
SELECT
    pg_get_serial_sequence('receipts', 'id') AS seq_name,
    currval(pg_get_serial_sequence('receipts', 'id')) AS current_seq,
    MAX(id) AS actual_max
FROM receipts;

ROLLBACK;

/* ----------------------------------------------------------------------
MANAGING AUTO-INCREMENTING SEQUENCES (SERIAL)
Manual row edits or test data deletions can cause primary key sequences to fall out of sync.
*/ ----------------------------------------------------------------------

