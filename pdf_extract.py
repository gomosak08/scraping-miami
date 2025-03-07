import re
import pandas as pd
from pdf_library import find_files, extract_images_from_pdf, extract_document_details_without_saving, get_first_second_party
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pdfs = find_files("pdf", "pdf")

def extract_information(text):
    logging.info("Extracting information from text.")
    try:
        owner_match = re.search(r'(OWNED BY|PROPERTY OWNER:|RE:)\s*(.*)', text, re.IGNORECASE)
        owner = owner_match.group(2).strip() if owner_match else "Owner not found"

        lien_type_match = re.search(r'(CLAIM OF LIEN|NOTICE OF TAX LIEN|NOTICE OF LIEN|.*?LIEN)', text, re.IGNORECASE)
        lien_type = lien_type_match.group(1).strip() if lien_type_match else "Lien type not found"

        address_match = re.search(
            r'(ADDRESS:\s*([\d\s\w.,-]+)|RE:\s.*\n(.*)|\d{1,5}[\w\s.,]+(?:Street|Avenue|Drive|Boulevard|Road), [\w\s]+, Florida)', 
            text, 
            re.IGNORECASE
        )
        address = address_match.group(2) if address_match and address_match.group(2) else (
            address_match.group(3) if address_match and address_match.group(3) else "Address not found"
        )

        unpaid_amount_match = re.search(
            r'(unpaid\s*)?\$\s*([\d,\.]+)|TOTAL AMOUNT OF TAX LIEN\s+([\d,\.]+)', 
            text, 
            re.IGNORECASE
        )
        unpaid_amount = unpaid_amount_match.group(2) if unpaid_amount_match and unpaid_amount_match.group(2) else (
            unpaid_amount_match.group(3) if unpaid_amount_match and unpaid_amount_match.group(3) else "Unpaid amount not found"
        )

        reporting_period_match = re.search(r'(\d{2}/\d{2}/\d{2}\s*-\s*\d{2}/\d{2}/\d{2})', text)
        reporting_period = reporting_period_match.group(1).strip() if reporting_period_match else "Reporting period not found"

        details = {
            "RT Account": re.search(r'RT Account #\s*[:;]?\s*(\d+)', text),
            "Business Partner": re.search(r'Business Partner #\s*[:;]?\s*(\d+)', text),
            "Contract Object": re.search(r'Contract Object#\s*[:;]?\s*(\d+)', text),
        }
        details = {key: match.group(1) if match else "Not found" for key, match in details.items()}

        return {
            "Owner": owner,
            "Lien Type": lien_type,
            "Address": address,
            "Unpaid Amount": unpaid_amount,
            "Reporting Period": reporting_period,
            "Details": details
        }
    except Exception as e:
        logging.error(f"Error during information extraction: {e}")
        return None


def delete_png_files(directory):
    """
    Deletes all PNG files in the specified directory.

    Parameters:
    - directory (str): The path to the directory from which PNG files will be removed.
    """
    # Check if the directory exists
    if not os.path.exists(directory):
        print("Directory does not exist.")
        return

    # List all files in the directory
    files = os.listdir(directory)

    # Loop through the files, removing those that end with .png
    for file in files:
        if file.endswith(".png"):
            file_path = os.path.join(directory, file)
            os.remove(file_path)  # Remove the file
            print(f"Deleted {file_path}")



export_data = []
for pdf in pdfs:
    try:
        logging.info(f"Processing PDF: {pdf}")
        extract_images_from_pdf(pdf)
        img = find_files("/home/gomosak/scraping/tmp", "png")
        text = ""
        for image in img:
            t = extract_document_details_without_saving(image)
            text += t
        info = extract_information(text)
        delete_png_files("/home/gomosak/scraping/tmp")

        info['pdf_name'] = pdf
        try:
            first, second = get_first_second_party("/home/gomosak/scraping/db.csv", pdf.split("/")[-1])
            if first and second:  # Only add to info if both are not None
                info['FirstParty'] = first
                info['SecondParty'] = second
        except ValueError as e:
            print(f"Error retrieving party information: {e}")

        if info:
            export_data.append(info)
    except Exception as e:
        logging.error(f"Failed to process PDF {pdf}: {e}")

# Normalize and save data
normalized_data = []
for item in export_data:
    details = item.pop('Details')  # Extract Details
    normalized_item = {**item, **details}  # Merge Details into the main dictionary
    normalized_data.append(normalized_item)

df = pd.DataFrame(normalized_data)
logging.info("DataFrame created.")

df.to_csv('lien_data.csv', index=False)
logging.info("Data exported to CSV.")
