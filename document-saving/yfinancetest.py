import pandas as pd
import yfinance as yf
import json
import os

def main():

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)

    sp500_table = tables[0]

    sp500_table = sp500_table[['Symbol', 'Security']]

    file_list = sp500_table['Symbol'].tolist()[:200]

    directory = "tickers/"

    existing_files = {os.path.splitext(f)[0] for f in os.listdir(directory)}

    filtered_list = [item for item in file_list if item not in existing_files]

    print(filtered_list)

    input_csv = "for-team/log.csv"            # Path to your CSV file
    output_csv = "for-team/newlog.csv"    # Output CSV file after removal
    target_column = "Symbol"      # Column to check for matches

    df = pd.read_csv(input_csv)

    df_filtered = df[df[target_column].isin(filtered_list)]

    df_filtered.to_csv(output_csv, index=False)

    print(f"Filtered CSV saved to {output_csv}")



if __name__ == "__main__":
    main()