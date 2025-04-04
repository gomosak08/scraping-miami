from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import base64
import json
import time
from csv_library import add_registers_to_csv
from create_csv_db import create_database_if_not_exists
import os


def initialize_driver():
    """
    Initializes the Selenium WebDriver with necessary options.

    Returns:
        webdriver.Chrome: Initialized WebDriver instance.
    """
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument(f"--user-data-dir=/tmp/selenium_user_data_{time.time()}")  # Unique directory
    driver = webdriver.Chrome(options=options)
    return driver

def find_request(driver, last_processed_index):
    """
    Finds the request to the target URL from the intercepted requests.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        last_processed_index (int): Index of the last processed request.

    Returns:
        tuple: Response text and updated index.
    """
    for request in driver.requests[last_processed_index:]:
        if "CFNDetailsPDF.aspx/GetData" in request.url and request.response:
            try:
                response_text = request.response.body.decode("utf-8")
                last_processed_index = len(driver.requests)
                return response_text, last_processed_index
            except Exception as e:
                print(f"Failed to decode response body: {e}")
                return None, last_processed_index
    print("No matching request found.")
    return None, last_processed_index

def scrape_data(start_date, end_date,captcha_time):
    """
    Main function to scrape data from the specified website.
    """
    driver = initialize_driver()
    pdf_data = None
    export_data = []
    list_specific_field = []
    last_processed_index = 0
    file_path = "data/data.txt"

    # Read existing data from file
    with open(file_path, "r") as file:
        values = [value.strip() for value in file.read().split(",")]

    try:
        driver.get("https://onlineservices.miamidadeclerk.gov/officialrecords/StandardSearch.aspx")

        # Fill out the search form
        #element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Last Name First Name Middle Initial OR Company Name']")))
        party_name_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Last Name First Name Middle Initial OR Company Name']")
        party_name_field.send_keys(" ")  # Replace with actual name
        driver.find_element(By.ID, "prec_date_from").send_keys(start_date) #"11/25/2024")
        driver.find_element(By.ID, "prec_date_to").send_keys(end_date)#"9/12/2024")
        Select(driver.find_element(By.ID, "pdoc_type")).select_by_visible_text("LIEN - LIE")

        print("Solve the CAPTCHA manually in the browser.")
        time.sleep(captcha_time)  # Wait for CAPTCHA resolution

        driver.find_element(By.ID, "btnNameSearch").click()
        page = 1
        while True:
            page += 1
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            print(f"Found {len(rows)} rows.")

            filtered_rows = []
            for i, row in enumerate(rows):
                specific_field = row.find_element(By.XPATH, f'//*[@id="tableSearchResults"]/tbody/tr[{i+1}]/td[1]/strong').text
                if specific_field not in list_specific_field and specific_field not in values:
                    filtered_rows.append(row)
                    list_specific_field.append(specific_field)

            values.extend(list_specific_field)
            with open(file_path, "w") as file:
                file.write(", ".join(values))

            for row in filtered_rows:
                row.click()
                driver.requests.clear()
                driver.switch_to.window(driver.window_handles[-1])

                FirstParty = driver.find_element(By.XPATH, '//*[@id="pnlCFNDetails"]/div[2]/div/table/tbody/tr[1]/td[2]').text
                SecondParty = driver.find_element(By.XPATH, '//*[@id="pnlCFNDetails"]/div[2]/div/table/tbody/tr[1]/td[4]').text
                RecDate = driver.find_element(By.XPATH, '//*[@id="pnlCFNDetails"]/div[2]/div/table/tbody/tr[1]/td[8]').text
                Clerks_File_No = driver.find_element(By.XPATH, '//*[@id="lblHeader"]').get_attribute("textContent").split("Clerk's File No.: ")[1].split(",")[0].strip()
                print(f"First Party: {FirstParty}\nSecond Party: {SecondParty}\nRecording Date: {RecDate}\nClerks_File_No: {Clerks_File_No}")
                pdf_button = driver.find_element(By.ID, "btnImage")
                pdf_button.click()
                time.sleep(10)

                response_body, last_processed_index = find_request(driver, last_processed_index)
                if response_body:
                    pdf_data = json.loads(response_body).get("d")
                    if pdf_data:
                        pdf_bytes = base64.b64decode(pdf_data)
                        response = Clerks_File_No.replace(" ", "")
                        pdf_name = f"pdf/document_{SecondParty}_{response}.pdf"
                        with open(pdf_name, "wb") as pdf_file:
                            pdf_file.write(pdf_bytes)
                        data = {"Clerks_File_No": Clerks_File_No, "RecDate": RecDate, "FirstParty": FirstParty, "SecondParty": SecondParty, "pdf_name": f"document_{SecondParty}_{response}.pdf"}
                        export_data.append(data)
                        print(f"PDF saved successfully for {SecondParty}!")
                    else:
                        print(f"PDF data not captured for {SecondParty}.")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            next_button = driver.find_elements(By.XPATH, f'//*[@id="content"]/div[1]/div[9]/div/div/div[4]/div/div[2]/ul/li[{page}]')
            if next_button:
                pass
                next_button[0].click()
                time.sleep(5)
            else:
                break

    finally:
        print(export_data)
        add_registers_to_csv('db.csv', export_data)
        driver.quit()

if __name__ == "__main__":
    if not os.path.exists('data/db.csv'):
        create_database_if_not_exists()

    star_date = input("Ingresa la fecha de inicio en el formato mm/dd/yyyy: ")
    end_date = input("Ingresa la fecha de fin en el formato mm/dd/yyyy: ")
    captcha_time = int(input("Ingresa el tiempo para resolver el captcha: "))
    scrape_data(star_date, end_date,captcha_time)