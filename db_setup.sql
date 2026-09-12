-- Create a dedicated database for folio
CREATE DATABASE receipt_vault;
-- Ensure to connect to the receipt_vault database before running anymore commands
-- The default schema ('public') is fine

-- Enable Trigram extension for fuzzy matching standard names
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create table for payment methods in 'public' schema
CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,              -- Auto-incrementing integer keys
    name VARCHAR(100) UNIQUE NOT NULL,  -- Specific name of the payment method
    type VARCHAR(50) NOT NULL           -- Category: 'Credit', 'Debit', 'Cash'
);

-- Pre-populating payment methods
INSERT INTO payment_methods (name, type) VALUES
    ('CapitalOne Savor Card', 'Credit'),
    ('CapitalOne 360 Checking', 'Debit'),
    ('Cash (USD)', 'Cash');

-- Create table for receipts in 'public' schema
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,                              -- Auto-incrementing integer keys
    store_name VARCHAR(255) NOT NULL,                   -- Store/merchant name
    purchase_date DATE NOT NULL,                        -- YYYY-MM-DD for purchase date
    currency VARCHAR(3)                                 -- 3-character ISO currency code
        CHECK (currency IN ('USD', 'CAD')) NOT NULL,    -- Strictly these currencies
    total_cost NUMERIC(10, 2) NOT NULL,                 -- Up to 10 digits incl. 2 decimals
    payment_method_id INT                               -- Link receipt to payment method
        REFERENCES payment_methods(id),                 -- Foreign key constraint
    receipt_type VARCHAR(20)                            -- Source format of the receipt
        CHECK (receipt_type IN ('physical', 'digital', 'manual')) NOT NULL, -- Validation constraint
    file_path TEXT,                                     -- Link to the image on Synology Drive
    notes TEXT,                                         -- Nullable/optional field for notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP      -- Automatically set current system time
);

-- Create table for master lookup dictionary for standardized (generic) items in 'public' schema
-- e.g. "CHOBANI GRP YOG 0%" -> "Greek Yogurt"
CREATE TABLE canonical_items (
    id SERIAL PRIMARY KEY,                          -- Auto-incrementing integer keys
    standard_name VARCHAR(255) UNIQUE NOT NULL,     -- Normalized name of the item (e.g. "Greek Yogurt")
    default_category VARCHAR(100)                   -- Broad classification
);
