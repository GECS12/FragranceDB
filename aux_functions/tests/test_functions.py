# Test Functions
import pandas as pd
from aux_functions.data_functions import extract_random_fragrance_names, standardize_fragrance_names, get_brands_from_excel

if __name__ == "__main__":
    file_path = 'D:\\Drive Folder\\Fragrances_DB\\my_flask_app\\data\\All_Fragrances.xlsx'
    # brand = "brand"
    #
    # # Extract fragrance names and their websites
    # fragrance_names, websites = extract_random_fragrance_names(file_path, num_samples_per_website=200, total_websites=4)
    #
    # # Clean the fragrance names
    # clean_names = [standardize_fragrance_names(name, brand) for name in fragrance_names]
    #
    # # Create a DataFrame to save to Excel
    # output_df = pd.DataFrame({
    #     'website_clean_fragrance_name': fragrance_names,
    #     'clean_name': clean_names,
    #     'website': websites
    # })
    #
    # # Save the DataFrame to an Excel file
    # output_file_path = r'D:\Drive Folder\Fragrances_DB\test_clean_fragrances.xlsx'
    # output_df.to_excel(output_file_path, index=False)
    #
    # print(f"Data saved to {output_file_path}")
    known_brands = []
    print(get_brands_from_excel(file_path))

