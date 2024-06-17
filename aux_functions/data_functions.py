import os
from datetime import datetime
import pandas as pd
import re

def save_to_excel(fragrances, base_path, scraper_name):
    timestamp = datetime.now().strftime("%d_%b_%Y %H" + "h" "%M" + "m")
    filename = f'{scraper_name} on {timestamp}.xlsx'
    full_path = os.path.join(base_path, filename)
    os.makedirs(base_path, exist_ok=True)  # Verificar se existe path

    fragrances_data = [fragrance.__dict__ for fragrance in fragrances]
    df = pd.DataFrame(fragrances_data)
    df.to_excel(full_path, index=False)

    print(filename + " has been saved in " + full_path)

BRAND_NAME_MAPPING = {
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
    'dsquared': 'Dsquared2',
    'duck': 'Mandarina Duck',
    'emporio armani': 'Giorgio Armani',
    'estee lauder': 'Estée Lauder',
    'ferragamo': 'Salvatore Ferragamo',
    'gianfranco ferre': 'Gianfranco Ferré',
    'gianni versace': 'Gianni Versace',
    'giorgio beverly': 'Giorgio Beverly Hills',
    'gualtier': 'Jean Paul Gaultier',
    'guerlain': 'Guerlain',
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
    'ysl': 'Yves Saint Laurent',
    'zegna': 'Ermenegildo Zegna'
}

def standardize_brand_name(brand_name):
    # Convert the brand name to lower case
    lower_case_brand_name = brand_name.lower()
    # Use the dictionary to map the brand name to the standard name if it exists
    return BRAND_NAME_MAPPING.get(lower_case_brand_name, brand_name)

def standardize_strings(string):
    string = string.replace('`', "'")
    return string.title()

def fragrance_type_cleaner(string):
    # Replace full phrases with abbreviations
    string = re.sub(r'\beau de toilette\b', 'EDT', string, flags=re.IGNORECASE)
    string = re.sub(r'\beau de parfum\b', 'EDP', string, flags=re.IGNORECASE)
    string = re.sub(r'\beau de cologne\b', 'EDC', string, flags=re.IGNORECASE)

    # Ensure existing abbreviations are uppercase
    string = re.sub(r'\bedt\b', 'EDT', string, flags=re.IGNORECASE)
    string = re.sub(r'\bedp\b', 'EDP', string, flags=re.IGNORECASE)
    string = re.sub(r'\bedc\b', 'EDC', string, flags=re.IGNORECASE)

    return string




