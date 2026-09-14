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
    purchase_date: str = Field(description="YYYY-MM-DD")
    # `currency`
    total_cost: float
    # `payment_method_id`
    # `receipt_type`
    # `file_path`
    # `notes`
    # `created_at`
    items: list[ExtractedItem]