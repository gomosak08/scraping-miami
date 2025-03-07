import pandas as pd
import os

def create_database_if_not_exists():
    if not os.path.exists('data/db.csv'):
        # Define column names
        columns = ['RecDate', 'FirstParty', 'SecondParty','Clerks_File_No', 'pdf_name']
        # Create an empty DataFrame
        empty_df = pd.DataFrame(columns=columns)

        # Save the empty DataFrame to a CSV file
        csv_file_path = "data/db.csv"
        empty_df.to_csv(csv_file_path, index=False, encoding="utf-8")

        print(f"Empty DataFrame saved to '{csv_file_path}'.")
