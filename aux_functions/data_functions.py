import os
from datetime import datetime
import pandas as pd
import re
from classes.classes import *


# Save fragrance data to an Excel file
def save_to_excel(fragrances, base_path, scraper_name):
    # Create timestamp for the filename
    timestamp = datetime.now().strftime("%d_%b_%Y %H" + "h" "%M" + "m")
    filename = f'{scraper_name} on {timestamp}.xlsx'
    full_path = os.path.join(base_path, filename)
    os.makedirs(base_path, exist_ok=True)  # Ensure the directory exists

    # Convert fragrance data to dictionary and save as Excel file
    fragrances_data = [fragrance.to_dict() for fragrance in fragrances]
    df = pd.DataFrame(fragrances_data)
    df.to_excel(full_path, index=False)
    print(filename + " has been saved in " + full_path)


# Mapping of brand names to their standardized forms
BRAND_NAME_MAPPING = {
    'afnan perfumes': 'Afnan',
    'abercrombie': 'Abercrombie & Fitch',
    'angel schlesser': 'Angel Schlesser',
    'annick goutal': 'Goutal Paris',
    'aramis': 'Aramis',
    'arden': 'Elizabeth Arden',
    'armani': 'Giorgio Armani',
    'balmain': 'Pierre Balmain',
    'beckham': 'David Beckham',
    'biagiotti': 'Laura Biagiotti',
    'boss': 'Hugo Boss',
    'bulgari': 'Bvlgari',
    'by kilian': 'Kilian',
    'ck': 'Calvin Klein',
    'comme des garcons': 'Comme des Garçons',
    'couture': 'Juicy Couture',
    'cavalli': 'Roberto Cavalli',
    'dior': 'Christian Dior',
    'dolce gabbana': 'Dolce & Gabbana',
    'donna karan': 'Dkny',
    'dsquared': 'Dsquared²',
    'dsquared2': 'Dsquared²',
    'duck': 'Mandarina Duck',
    'emporio armani': 'Giorgio Armani',
    'estee lauder': 'Estée Lauder',
    'ferragamo': 'Salvatore Ferragamo',
    'gianfranco ferre': 'Gianfranco Ferré',
    'gianni versace': 'Gianni Versace',
    'giorgio beverly': 'Giorgio Beverly Hills',
    'gualtier': 'Jean Paul Gaultier',
    'guerlain': 'Guerlain',
    'gres': 'Grès',
    'hermes': 'Hermès',
    'hilfiger': 'Tommy Hilfiger',
    'hugo': 'Hugo Boss',
    'issey': 'Issey Miyake',
    'jean paul': 'Jean Paul Gaultier',
    'jean-paul gaultier': 'Jean Paul Gaultier',
    'jessica parker': 'Sarah Jessica Parker',
    'jimmy choo': 'Jimmy Choo',
    'joop': 'Joop!',
    'kors': 'Michael Kors',
    'lapidus': 'Ted Lapidus',
    'laura biagiotti': 'Laura Biagiotti',
    'lagerfeld': 'Karl Lagerfeld',
    'lamborghini': 'Tonino Lamborghini',
    'lancome': 'Lancôme',
    'lauder': 'Estée Lauder',
    'lauren': 'Ralph Lauren',
    'lempicka': 'Lolita Lempicka',
    'malone': 'Jo Malone',
    'margiela': 'Maison Margiela',
    'mont blanc': 'Montblanc',
    'mugler': 'Thierry Mugler',
    'nina': 'Nina Ricci',
    'p.gres': 'Grès',
    'paco': 'Paco Rabanne',
    'puig': 'Antonio Puig',
    'rodriguez': 'Narciso Rodriguez',
    'saint laurent': 'Yves Saint Laurent',
    'tiffany & co.parfum': 'Tiffany & Co.',
    'tommy': 'Tommy Hilfiger',
    'vanderbilt': 'Gloria Vanderbilt',
    'viktor y rolph': 'Viktor & Rolf',
    'varvatos': 'John Varvatos',
    'versace': 'Gianni Versace',
    'viktor and rolf': 'Viktor & Rolf',
    'yslaurent': 'Yves Saint Laurent',
    'swiss army': 'Victorinox Swiss Army',
    'ysl': 'Yves Saint Laurent',
    'zegna': 'Ermenegildo Zegna'
}


# Standardize brand names based on the mapping
def standardize_brand_names(brand_name):
    # Convert the brand name to lower case
    lower_case_brand_name = brand_name.lower()
    # Use the dictionary to map the brand name to the standard name if it exists
    return BRAND_NAME_MAPPING.get(lower_case_brand_name, brand_name.title())


# Standardize fragrance names
def standardize_fragrance_names(string, brand):
    # Convert the entire string to lowercase
    string = string.lower()
    string = string.replace('`', "'")
    string = string.replace('´', "'")
    string = string.replace('¬≤', '²')

    # Replace "eau de toilette", "eau de parfum", "eau de cologne" with "edt", "edp", "edc" respectively
    string = re.sub(r'\beau de toilette\b', 'edt', string)
    string = re.sub(r'\beau de parfum\b', 'edp', string)
    string = re.sub(r'\beau de cologne\b', 'edc', string)

    # Convert strings like "75 G" or "75 GR" or "75 GRAMS" to "75g"
    string = re.sub(r'(\d+)\s*(g|gr|grams)', r'\1g', string, flags=re.IGNORECASE)

    # Convert comma to period in numbers like "75,5" to "75.5"
    string = re.sub(r'(\d+),(\d+)', r'\1.\2', string)

    # Replace the non-standardized brand name with the standardized one
    standardized_brand = standardize_brand_names(brand)
    string = re.sub(brand.lower(), standardized_brand.lower(), string, count=1)

    # Split the string into words to process each word separately
    words = string.split()

    # Title case each word, but keep some in Upper CASE
    title_cased_words = []
    for word in words:
        if word in {'edt', 'edp', 'edc'}:
            title_cased_words.append(word.upper())
        else:
            title_cased_words.append(word.title())

    # Join the words back into a single string
    title_cased_string = ' '.join(title_cased_words)

    # Ensure "ml" and "g" are maintained in lowercase
    title_cased_string = re.sub(r'(\d+)\s*ml', r'\1ml', title_cased_string, flags=re.IGNORECASE)
    title_cased_string = re.sub(r'(\d+)\s*g', r'\1g', title_cased_string, flags=re.IGNORECASE)

    # Check if the standardized brand name is at the beginning, add it if not
    if not title_cased_string.lower().startswith(standardized_brand.lower()):
        title_cased_string = f"{standardized_brand} {title_cased_string}"

    return title_cased_string

