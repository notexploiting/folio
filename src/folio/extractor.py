# --------- AI OCR & DATA STRUCTURING ---------
# Use in tangent with Pydantic schema in schema.py to validate data extracted from receipts

import os
from google import genai
from google.genai import types
from .schema import ExtractedReceipt
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def process_receipt_image(file_path: str, current_local_time: str) -> ExtractedReceipt:
    """
    Process a receipt image using Google Gemini API and return structured data as an ExtractedReceipt object.
    
    Args:
        file_path (str): The path to the receipt image file.
    """
    uploaded_file = client.files.upload(file=file_path)
    prompt = """
    You are an expert receipt data extractor. Analyze this receipt. Extract the store name, date, prices, and all individual items.

    CRITICAL DATE AND TIME INSTRUCTIONS: The exact current time and date on the user's computer is: {current_local_time}. Base all ambiguous dates on this current date. If you see a two-digit year (e.g., "24", "25", "26"), interpret it relative to the current year. Do NOT default to past years like 2014. Ensure the purchase date is not logically impossible (e.g., a purchase date in the future).

    For each item, determine a canonical generic name (e.g. 'Milk', 'Eggs').
    Estimate an expiration date based on the purchase date if the item is perishable. Expiry dates for groceries or perishables will almost always be in the future relative to the purchase date.
    """
    response = client.models.generate_content(      # Start request to Gemini API
        model='gemini-3.6-flash',                   # Choose model for analysis
        contents=[uploaded_file, prompt],           # Send both image and prompt
        config=types.GenerateContentConfig(         # Configure response settings
            response_mime_type="application/json",  # Return JSON instead of prose
            response_schema=ExtractedReceipt,       # Format to Pydantic schema
            temperature=0.0                         # Deterministic, no creativity
        )
    )
    return ExtractedReceipt.model_validate_json(response.text) # Parse & Validate