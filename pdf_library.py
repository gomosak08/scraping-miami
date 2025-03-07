from PIL import Image
import fitz  
import os
from pytesseract import image_to_string
from pdf2image import convert_from_path
import cv2
from PIL import Image
import pytesseract
import cv2
from PIL import Image
import pytesseract
import pandas as pd 



def find_files(path, extention):
    os.chdir(path)
    directory = os.getcwd()
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(f'.{extention}'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files



def extract_images_from_pdf(pdf_path):
    """
    Extracts images from each page of a PDF file and saves them as PNG files.

    Args:
        pdf_path (str): The path to the PDF file from which images need to be extracted.

    Workflow:
    1. Open the PDF file using PyMuPDF (fitz).
    2. Iterate through each page in the PDF.
    3. Retrieve the list of images embedded on the current page.
    4. Extract each image and save it as a PNG file.

    Details:
    - The images are saved in a temporary "tmp" directory with filenames formatted as 
      "page_<page_number>_img_<image_index>.png".
    - The function uses the XREF (cross-reference) number of the image to extract it.

    Notes:
    - Ensure the `tmp` directory exists or handle its creation if necessary.
    - This function does not handle exceptions explicitly; make sure the input PDF path is valid.

    Example Usage:
        extract_images_from_pdf("example.pdf")

    Parameters:
    - pdf_path (str): Path to the PDF file.

    Returns:
    None
    """

    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"] 
            
            with open(f"../tmp/page_{page_num + 1}_img_{img_index + 1}.png", "wb") as img_file:
                img_file.write(image_bytes)
    
    print("Images extracted successfully.")




def extract_document_details_without_saving(image_path, config='--psm 6', lang='eng'):
    """
    Processes an image of a document, extracts text using OCR, and parses relevant details.

    Args:
        image_path (str): Path to the input image.
        config (str): Tesseract OCR configuration options. Default is '--psm 6'.
        lang (str): Language for OCR. Default is 'eng'.

    Returns:
        dict: Extracted details including owner, lien type, address, unpaid amount, reporting period, 
              and other document-specific details.
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    denoised = cv2.GaussianBlur(thresh, (5, 5), 0)
    resized = cv2.resize(denoised, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    text_image = Image.fromarray(resized)

    text = pytesseract.image_to_string(text_image, config=config, lang=lang)

    return text

import pandas as pd

def get_first_second_party(file_path, name):
    """
    Retrieves the 'FirstParty' and 'SecondParty' values from a CSV file for a specified PDF name.

    Parameters:
    - file_path (str): The file path to the CSV where the data is stored.
    - name (str): The name of the PDF to find the corresponding parties for.

    Returns:
    - tuple: A tuple containing the values of 'FirstParty' and 'SecondParty'.

    Raises:
    - ValueError: If the specified file does not exist or the PDF name is not found in the CSV.

    Example:
    >>> get_first_second_party('data.csv', 'example.pdf')
    ('John Doe', 'Jane Smith')
    """

    try:
        # Load the existing CSV file into a DataFrame
        df = pd.read_csv(file_path)
        print("Original DataFrame loaded successfully.")
    except FileNotFoundError:
        raise ValueError("File does not exist.")

    # Find the row where 'pdf_name' matches the provided 'name'
    if name in df['pdf_name'].values:
        row = df.loc[df['pdf_name'] == name]

        # Ensure the row is not empty and contains the required columns
        if not row.empty and {'FirstParty', 'SecondParty'}.issubset(row.columns):
            first_party = row['FirstParty'].iloc[0]  # Get the first instance of 'FirstParty'
            second_party = row['SecondParty'].iloc[0]  # Get the first instance of 'SecondParty'
            return first_party, second_party
        else:
            raise ValueError("Required columns are missing or no data found for the specified PDF.")
    else:
        raise ValueError("PDF name not found in the dataset.")
