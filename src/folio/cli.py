# --------- COMMAND LINE INTERFACE ---------

import os, sys, json, shutil, argparse
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from .extractor import process_receipt_image
from .schema import ExtractedReceipt, ExtractedItem
from .db import get_payment_methods, fuzzy_match_canonical, ensure_canonical_item, insert_receipt_full, delete_receipt


console = Console()
from dotenv import load_dotenv; load_dotenv()

INBOX = os.getenv("RECEIPT_INBOX_PATH")
ARCHIVE = os.getenv("RECEIPT_ARCHIVE_PATH")
JSON_ARCHIVE = os.getenv("JSON_ARCHIVE_PATH")

for path in [INBOX, ARCHIVE, JSON_ARCHIVE]:
    os.makedirs(path, exist_ok=True)

def select_payment_method():
    methods = get_payment_methods()
    console.print("\n[bold cyan]Select Payment Method:[/bold cyan]")
    for m in methods: console.print(f"[{m['id']}] {m['name']}")
    return int(Prompt.ask("Enter ID"))

def review_and_insert(parsed_receipt, file_name, file_path, receipt_type, currency, pmt_id):
    console.print(f"\n[bold green]Receipt from {parsed_receipt.store_name} on {parsed_receipt.purchase_date}[/bold green]")
    console.print(f"Total: ${parsed_receipt.total_cost} {currency}\n")
    final_items = []
    
    for item in parsed_receipt.items:
        console.print(f"[yellow]Item:[/yellow] {item.raw_name} -> {item.specific_name}")
        match = fuzzy_match_canonical(item.standard_name)
        
        if match:
            if Confirm.ask(f"Fuzzy match found: [cyan]{match['standard_name']}[/cyan] (Sim: {match['sim']:.2f}). Use this?"):
                canonical_name = match['standard_name']
            else:
                canonical_name = Prompt.ask("Enter new standard name", default=item.standard_name)
        else:
            console.print(f"No close match. Registering new standard name: [cyan]{item.standard_name}[/cyan]")
            if not Confirm.ask("Accept new name?"):
                canonical_name = Prompt.ask("Enter updated standard name")
            else:
                canonical_name = item.standard_name
                
        can_id = ensure_canonical_item(canonical_name, item.category)
        final_items.append({
            'raw_name': item.raw_name,
            'specific_name': item.specific_name,
            'canonical_id': can_id,
            'category': item.category,
            'price': item.price,
            'quantity_purchased': item.quantity_purchased,
            'unit': item.unit,
            'quantity_remaining': item.quantity_purchased,
            'expiration_date': item.expiration_date
        })
        
    console.print("-" * 30)
    if Confirm.ask("\n[bold magenta]Everything looks good. Insert into database?[/bold magenta]"):
        receipt_data = {
            'store_name': parsed_receipt.store_name,
            'purchase_date': parsed_receipt.purchase_date,
            'currency': currency,
            'total_cost': parsed_receipt.total_cost,
            'payment_method_id': pmt_id,
            'receipt_type': receipt_type,
            'file_path': file_name
        }
        rid = insert_receipt_full(receipt_data, final_items)
        console.print(f"[bold green]Success! Inserted as Receipt ID: {rid}[/bold green]")
        return True
    return False

def process_auto():
    files = [f for f in os.listdir(INBOX) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf'))]
    if not files:
        console.print("[yellow]No receipts found in Inbox.[/yellow]")
        return
        
    for file in files:
        file_path = os.path.join(INBOX, file)
        console.print(f"\n[bold blue]Processing {file}...[/bold blue]")
        currency = Prompt.ask("Currency", choices=["USD", "CAD"], default="CAD")
        pmt_id = select_payment_method()
        receipt_type = Prompt.ask("Receipt Type", choices=["physical", "digital"], default="physical")
        
        # with console.status("AI is analyzing the receipt..."):
        #     parsed = process_receipt_image(file_path)

        with console.status("AI is analyzing the receipt..."):
            # Get the exact current local time with the system's timezone
            current_local_time = datetime.now().astimezone().strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
            
            # Pass it to the extractor (requires updating extractor.py to accept this)
            parsed = process_receipt_image(file_path, current_local_time)
            
        json_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file}.json"
        with open(os.path.join(JSON_ARCHIVE, json_filename), 'w') as f:
            f.write(parsed.model_dump_json(indent=2))
            
        if review_and_insert(parsed, file, file_path, receipt_type, currency, pmt_id):
            # Build new archive filename: [store]-[date]-[time].[ext]
            safe_store = parsed.store_name.replace(" ", "_").replace("/", "-")
            purchase_date = parsed.purchase_date  # YYYY-MM-DD
            timestamp = datetime.now().strftime("%H%M%S")

            ext = os.path.splitext(file)[1].lower()
            new_name = f"{safe_store}-{purchase_date}-{timestamp}{ext}"
            new_path = os.path.join(ARCHIVE, new_name)

            shutil.move(file_path, new_path)
            console.print(f"[bold green]Archived as: {new_name}[/bold green]")


def process_manual():
    console.print("\n[bold blue]--- Manual Receipt Entry ---[/bold blue]")
    store = Prompt.ask("Store Name")
    date = Prompt.ask("Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))
    total = float(Prompt.ask("Total Cost"))
    currency = Prompt.ask("Currency", choices=["USD", "CAD"], default="CAD")
    pmt_id = select_payment_method()
    items = []
    
    while Confirm.ask("\nAdd an item?"):
        raw = Prompt.ask("Raw/Specific Name")
        std = Prompt.ask("Standard Generic Name (e.g. Milk)")
        cat = Prompt.ask("Category")
        price = float(Prompt.ask("Price"))
        qty = float(Prompt.ask("Quantity", default="1.0"))
        unit = Prompt.ask("Unit", default="each")
        
        items.append(ExtractedItem(
            raw_name=raw, specific_name=raw, standard_name=std,
            category=cat, price=price, quantity_purchased=qty,
            unit=unit, expiration_date=None
        ))
        
    manual_receipt = ExtractedReceipt(store_name=store, purchase_date=date, total_cost=total, items=items)
    review_and_insert(manual_receipt, None, None, "manual", currency, pmt_id)

def main():
    parser = argparse.ArgumentParser(description="Receipt Processor Pipeline")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("auto", help="Process images in the Inbox using Gemini AI")
    subparsers.add_parser("manual", help="Manually enter a receipt with no file")
    undo_parser = subparsers.add_parser("undo", help="Delete a receipt by ID")
    undo_parser.add_argument("id", type=int)
    args = parser.parse_args()
    
    if args.command == "auto": process_auto()
    elif args.command == "manual": process_manual()
    elif args.command == "undo":
        delete_receipt(args.id)
        console.print(f"[bold red]Receipt {args.id} and all items deleted.[/bold red]")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()