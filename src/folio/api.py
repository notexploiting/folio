# --------- FASTAPI BACKEND ---------
# Run with: uv run uvicorn folio.api:app --reload

import os
import json
import shutil
from datetime import datetime
from typing import Literal
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from .schema import ExtractedReceipt
from .extractor import process_receipt_image
from .db import get_payment_methods, fuzzy_match_canonical, ensure_canonical_item, insert_receipt_full, delete_receipt

load_dotenv()

INBOX = os.getenv("RECEIPT_INBOX_PATH")
ARCHIVE = os.getenv("RECEIPT_ARCHIVE_PATH")
JSON_ARCHIVE = os.getenv("JSON_ARCHIVE_PATH")

for path in [INBOX, ARCHIVE, JSON_ARCHIVE]:
    os.makedirs(path, exist_ok=True)

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".pdf")

app = FastAPI()


class SaveReceiptRequest(BaseModel):
    """
    A reviewed receipt sent from the frontend to be saved.
    """
    file_name: str | None                                   # File in the inbox, or None for a manual receipt
    receipt_type: Literal["physical", "digital", "manual"]  # Same choices as the database
    currency: Literal["USD", "CAD"]                         # Same choices as the database
    payment_method_id: int
    receipt: ExtractedReceipt                               # The receipt after review, with confirmed standard names
    ai_receipt: ExtractedReceipt | None                     # The receipt as the AI returned it, or None for a manual receipt


def get_inbox_path(file_name: str) -> str:
    """
    Get the full path of a file in the inbox, making sure the file is really in the inbox.

    Args:
        file_name (str): The name of the file in the inbox.

    Returns:
        The full path to the file.
    """
    if os.path.basename(file_name) != file_name:
        raise HTTPException(status_code=400, detail="Bad file name")
    file_path = os.path.join(INBOX, file_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not in inbox")
    return file_path


@app.get("/payment-methods")
def list_payment_methods():
    """
    List all payment methods.

    Returns:
        A list of dictionaries with the keys id and name.
    """
    return get_payment_methods()


@app.get("/inbox")
def list_inbox():
    """
    List the receipt files in the inbox that have not been saved yet.

    Returns:
        A sorted list of file names.
    """
    files = [f for f in os.listdir(INBOX) if f.lower().endswith(ALLOWED_EXTENSIONS)]
    return sorted(files)


@app.post("/inbox")
def upload_to_inbox(file: UploadFile):
    """
    Save an uploaded receipt file into the inbox.

    The file name gets a timestamp in front so two uploads with the same name do not clash.

    Args:
        file (UploadFile): The receipt image or PDF.

    Returns:
        A dictionary with the file_name it was saved under.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no name")
    original_name = os.path.basename(file.filename)
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type must be one of {ALLOWED_EXTENSIONS}")

    file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_name}"
    file_path = os.path.join(INBOX, file_name)
    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"{file_name} is already in the inbox")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"file_name": file_name}


@app.get("/inbox/{file_name}")
def get_inbox_file(file_name: str):
    """
    Send back a receipt file from the inbox so it can be shown during review.

    Args:
        file_name (str): The name of the file in the inbox.
    """
    return FileResponse(get_inbox_path(file_name))


@app.post("/inbox/{file_name}/extract")
def extract_inbox_file(file_name: str) -> ExtractedReceipt:
    """
    Run AI extraction on a receipt file in the inbox. Nothing is saved.

    Args:
        file_name (str): The name of the file in the inbox.

    Returns:
        The extracted receipt.
    """
    file_path = get_inbox_path(file_name)
    current_local_time = datetime.now().astimezone().strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    try:
        return process_receipt_image(file_path, current_local_time)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {error}")


@app.get("/canonical-items/match")
def match_canonical_item(standard_name: str):
    """
    Find the closest existing canonical item for a standard name.

    Args:
        standard_name (str): The name to look for.

    Returns:
        A dictionary with id, standard_name, and sim, or null if nothing is close enough.
    """
    return fuzzy_match_canonical(standard_name)


@app.post("/receipts")
def save_receipt(request: SaveReceiptRequest):
    """
    Save a reviewed receipt to the database, then archive the file and a JSON snapshot.

    The snapshot keeps both the reviewed receipt and the original AI extraction.

    Args:
        request (SaveReceiptRequest): The reviewed receipt and its details.

    Returns:
        A dictionary with the new receipt_id and the archived file_name.
    """
    receipt = request.receipt

    if request.file_name is None and request.receipt_type != "manual":
        raise HTTPException(status_code=400, detail="A receipt with no file must be manual")
    if request.file_name is not None and request.receipt_type == "manual":
        raise HTTPException(status_code=400, detail="A manual receipt cannot have a file")

    # Name the archived files after the store, date, and time
    safe_store = receipt.store_name.replace(" ", "_").replace("/", "-")
    if receipt.purchase_time:
        time_str = receipt.purchase_time.replace(":", "")   # Cleans "12:29:13" to "122913"
    else:
        time_str = datetime.now().strftime("%H%M%S")
    base_name = f"{safe_store}-{receipt.purchase_date}-{time_str}"

    # Check the files before touching the database so a clash never leaves a half-saved receipt
    inbox_path = None
    archive_name = None
    archive_path = None
    if request.file_name is not None:
        inbox_path = get_inbox_path(request.file_name)
        ext = os.path.splitext(request.file_name)[1].lower()
        archive_name = base_name + ext
        archive_path = os.path.join(ARCHIVE, archive_name)
        if os.path.exists(archive_path):
            raise HTTPException(status_code=409, detail=f"{archive_name} is already in the archive")

    json_path = os.path.join(JSON_ARCHIVE, base_name + ".json")
    if os.path.exists(json_path):
        raise HTTPException(status_code=409, detail=f"{base_name}.json is already in the archive")

    # Make sure each item has a canonical item, then build the item rows
    items_data = []
    for item in receipt.items:
        canonical_id = ensure_canonical_item(item.standard_name, item.category)
        items_data.append({
            'raw_name': item.raw_name,
            'specific_name': item.specific_name,
            'canonical_id': canonical_id,
            'category': item.category,
            'price': item.price,
            'quantity_purchased': item.quantity_purchased,
            'unit': item.unit,
            'quantity_remaining': item.quantity_purchased,
            'expiration_date': item.expiration_date
        })

    receipt_data = {
        'store_name': receipt.store_name,
        'store_address': receipt.store_address,
        'store_website': receipt.store_website,
        'store_phone': receipt.store_phone,
        'purchase_date': receipt.purchase_date,
        'purchase_time': receipt.purchase_time,
        'currency': request.currency,
        'tax_amount': receipt.tax_amount,
        'tip_amount': receipt.tip_amount,
        'total_cost': receipt.total_cost,
        'card_last_four': receipt.card_last_four,
        'payment_method_id': request.payment_method_id,
        'receipt_type': request.receipt_type,
        'file_path': archive_name
    }
    receipt_id = insert_receipt_full(receipt_data, items_data)

    # Archive the file and the snapshot now that the receipt is saved
    if inbox_path is not None:
        shutil.move(inbox_path, archive_path)

    if request.ai_receipt is not None:
        ai_receipt = request.ai_receipt.model_dump()
    else:
        ai_receipt = None

    snapshot = {
        'receipt_id': receipt_id,
        'saved_at': datetime.now().astimezone().isoformat(),
        'file_name': archive_name,
        'original_file_name': request.file_name,
        'receipt_type': request.receipt_type,
        'currency': request.currency,
        'payment_method_id': request.payment_method_id,
        'receipt': receipt.model_dump(),
        'ai_receipt': ai_receipt
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    return {"receipt_id": receipt_id, "file_name": archive_name}


@app.delete("/receipts/{receipt_id}")
def remove_receipt(receipt_id: int):
    """
    Delete a receipt and its items. The archived file and snapshot are kept.

    Args:
        receipt_id (int): The ID of the receipt to delete.

    Returns:
        A dictionary with the deleted receipt_id.
    """
    delete_receipt(receipt_id)
    return {"receipt_id": receipt_id}
