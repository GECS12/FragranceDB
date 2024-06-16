import os
from datetime import datetime
import pandas as pd


def save_to_excel(fragrances, base_path, scraper_name):
    timestamp = datetime.now().strftime("%d_%b_%Y %H" + "h" "%M" + "m")
    filename = f'{scraper_name} on {timestamp}.xlsx'
    full_path = os.path.join(base_path, filename)
    os.makedirs(base_path, exist_ok=True)  # Verificar se existe path

    fragrances_data = [fragrance.__dict__ for fragrance in fragrances]
    df = pd.DataFrame(fragrances_data)
    df.to_excel(full_path, index=False)

    print(filename + " has been saved in " + full_path)


