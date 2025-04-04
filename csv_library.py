import pandas as pd
import os 

def add_registers_to_csv(file_path, new_registers):
    """
    Adds a list of registers (rows) to an existing CSV file.

    Args:
        file_path (str): Path to the CSV file.
        new_registers (list of dict): List of dictionaries where each dictionary represents a row to add.

    Returns:
        pd.DataFrame: The updated DataFrame after adding the new registers.
    """
    try:
        # Load the existing CSV file into a DataFrame
        df = pd.read_csv(file_path)
        print("Original DataFrame loaded successfully.")
    except FileNotFoundError:
        # If the file doesn't exist, create a new DataFrame with the columns from the first register
        if new_registers:
            df = pd.DataFrame(columns=new_registers[0].keys())
            print("File not found. Creating a new DataFrame.")
        else:
            raise ValueError("No data provided and file does not exist.")

    # Convert the list of dictionaries to a DataFrame
    new_rows_df = pd.DataFrame(new_registers)

    # Append the new rows to the existing DataFrame
    df = pd.concat([df, new_rows_df], ignore_index=True)

    # Save the updated DataFrame back to the file
    df.to_csv(file_path, index=False, encoding="utf-8")
    print(f"New registers added and saved to '{file_path}'.")

    return df

def create_db():
    """
    Creates a new CSV file in a specified directory with predefined column headers.

    The file name is determined based on the number of existing files in the directory.
    It follows the naming convention 'scr_<number>.csv', where <number> is the count of files + 1.

    Args:
        None

    Returns:
        None

    Behavior:
        - Checks the directory `scrapeo/` for the current number of files.
        - Creates a new CSV file with predefined column names:
            ['name_pdf', 'owner', 'lien_type', 'addresses', 'unpaid_amount', 'name']
        - Saves the empty DataFrame to the newly created file.
    """
    cwd = os.getcwd()
    directory = f'{cwd}/data/'

    
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Count the number of files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    num_files = len(files)

    # Generate a new file name based on the number of existing files
    new_file_name = os.path.join(directory, f"scr_{num_files + 1}.csv")

    # Define the columns for the CSV file
    columns = ['name_pdf', 'owner', 'lien_type', 'addresses', 'unpaid_amount', 'name']

    # Create an empty DataFrame
    empty_df = pd.DataFrame(columns=columns)

    # Save the empty DataFrame to a CSV file
    empty_df.to_csv(new_file_name, index=False, encoding="utf-8")
    return new_file_name
