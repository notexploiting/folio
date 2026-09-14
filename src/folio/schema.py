# --------- PYDANTIC SCHEMA ---------

from pydantic import BaseModel, Field # Data validation

class ExtractedItem(BaseModel):
    """
    A class to represent an item extracted from a receipt.
    """
    # `id`
    # `receipt_id` INT REFERENCES
    raw_name: str = Field(description="Exact text printed on the receipt")
    specific_name: str = Field(description="Brand name and specific item, e.g. 'Chobani Non-Fat Plain Greek Yogurt'")
    standard_name: str = Field(description="Canonical generic name, e.g. 'Greek Yogurt'")
    category: str = Field(description="General grocery/item category")
    price: float = Field(description="Total price paid for this line item")
    quantity_purchased: float = Field(description="Quantity. Default to 1.0 if not specified.")
    unit: str = Field(description="e.g., 'each', 'lbs', 'oz'")
    # `quantity_remaining`
    expiration_date: str | None = Field(description="Estimate in YYYY-MM-DD based on item perishability and receipt date, or null.")
    # `created_at`

class ExtractedReceipt(BaseModel):
    """
    A class to represent a receipt extracted from a physical, digital, or memory receipt.
    """
    # `id`
    store_name: str
    store_address: str | None = Field(description="Physical address of the store, or null if not found")
    store_website: str | None = Field(description="Website URL of the store, or null if not found")
    store_phone: str | None = Field(description="Phone number of the store, or null if not found")
    purchase_date: str = Field(description="YYYY-MM-DD")
    purchase_time: str | None = Field(description="HH:MM:SS (24-hour format), or null if not found")
    # `currency`
    tax_amount: float = Field(description="Total tax applied to the receipt. Default to 0.0 if not found")
    tip_amount: float = Field(description="Total tip amount. Default to 0.0 if not found")
    total_cost: float
    # `payment_method_id`
    card_last_four: str | None = Field(description="Last four digits of the payment card used, or null if not found")
    # `receipt_type`
    # `file_path`
    # `notes`
    # `created_at`
    items: list[ExtractedItem]