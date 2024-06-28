import os
import pandas as pd
import re
from classes.classes import *
import random

#Read Excel
def read_excel(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)
    return df

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


def get_brand_from_fragrance_name(fragrance_name):
    # Define a dictionary of known brands and match against the fragrance name
    known_brands = ['ANTÓNIO BANDERAS', 'Jovan', 'Parfums Bleu Limited', 'Paco Rabanne', 'Baldessarini', 'Oscar De La Renta', 'Kenzo',
                    'Missoni', 'Alexandre.J', 'Issey Miyake', 'Bvlgari', 'COLLISTAR', 'Mugler', 'Hugo Boss', 'Jacques Bogart',
                    'Tommy Hilfiger', 'Lacoste', 'Afnan Perfumes', 'Azzaro', 'Old Spice', 'Rayhaan', 'Estee Lauder',
                    'Benetton', 'Diesel', 'Coty', 'Antonio Puig', 'Lattafa Perfumes', 'Acqua di Parma',
                    'Yves Saint Laurent', 'Gisada', 'Police', 'Joop!', 'Aramis', 'Giorgio Armani', 'Al Haramain',
                    'Dolce & Gabbana', 'Cristiano Ronaldo', 'DKNY', 'Ralph Lauren', 'Guy Laroche', 'Jimmy Choo',
                    'Armaf', 'Jaguar', 'S.T. Dupont', 'Clinique', 'Laura Biagiotti', 'Lanvin', 'Liz Claiborne',
                    'Calvin Klein', 'Giorgio Beverly Hills', 'Jean-Louis Scherrer', 'Pierre Cardin',
                    'Abercrombie & Fitch', 'Acca Kappa', 'Adidas', 'Adolfo Dominguez', 'Alyssa Ashley', 'Annayake',
                    'Annick Goutal', 'Antonio Banderas', 'Armand Basi', 'Banana Republic', 'Batman', 'Ben Sherman',
                    'Bentley', 'Bottega Veneta', 'Boucheron', 'Brioni', 'Bruno Banani', 'Brut', 'Burberry', 'By Kilian',
                    'Cacharel', 'Caesars', 'Carolina Herrera', 'Cartier', 'Carven', 'Cerruti', 'Chanel', 'Chopard',
                    'Clive Christian', 'Christian Dior', 'Christine Darvin', 'Coach', 'Creed', 'Cuba', 'DSquared2',
                    'Dana', 'David & Victoria Beckham', 'Davidoff', 'Delroba Parfums', 'Disney', 'Dunhill', 'EPL',
                    'Ed Hardy', 'Eden Classics', 'Elizabeth Taylor', 'Etat Libre d`Orange', 'Etienne Aigner', 'Evaflor',
                    'FCUK', 'Floris', 'Franck Olivier', 'Gai Mattiolo', 'GAS', 'Givenchy', 'GIVENCHI' 'Geoffrey Beene', 'Gucci',
                    'Guerlain', 'Guess', 'Halston', 'Hermes', 'Hollister', 'Hâttric', 'Iceberg', 'Instituto Español',
                    'Izod', 'James Bond', 'Jasper Conran', 'Jean Paul Gaultier', 'Jeanne Arthes', 'Jesus del Pozo',
                    'Jil Sander', 'Jivago', 'John Varvatos', 'Juicy Couture', 'Kanon', 'Kappa', 'Karl Lagerfeld',
                    'Kenneth Cole', 'Korloff Paris', 'Korres', "L'Occitane en Provence", 'Lalique', 'Lamborghini',
                    'Lambretta', 'Le Chameau', 'Lionel Richie', 'Loewe', 'Lolita Lempicka', 'Lomani', 'Lotto Sport',
                    'Louis Cardin', 'M. Micallef', 'Maison Alhambra', 'Mandarina Duck', 'Marvel', 'Mexx',
                    'Michael Jordan', 'Michael Kors', 'Milton Lloyd', 'Moncler', 'Mont Blanc', 'Montale', 'Montana',
                    'Moschino', 'Mossimo', 'MotoGP', 'Mustang', 'Mäurer & Wirtz', 'Narciso Rodriguez', 'Nautica',
                    'Nikos', 'Paloma Picasso', 'Parfums de Marly', 'Paul Smith', "Penhaligon's", "Perfumer's Choice",
                    'Perry Ellis', 'Philipp Plein', 'Pino Silvestre', 'Playboy', 'Prada', 'Prism Parfums',
                    "Ralf's Mejia", 'Rance 1795', 'Rave', 'Replay', 'Reuzel', 'Reyane Tradition', 'Riiffs', 'Rituals',
                    'Roberto Cavalli', 'Roccobarocco', 'Rochas', 'Royal Copenhagen', 'STR8', 'Salvador Dali',
                    'Salvatore Ferragamo', 'Sergio Tacchini', 'Shanghai Tang', 'Sisley', 'SoulCal & Co', 'Star Wars',
                    'Style Parfum', 'Superman', 'Swiss Arabian', 'Swiss Army', 'Ted Baker', 'Ted Lapidus',
                    'The Merchant of Venice', 'The Woods Collection', 'Tom Ford', 'Tom Prune', 'Top Gun', 'Topman',
                    'Tous', 'Trussardi', 'Twisted Soul', 'Tyson Fury', 'Emanuel Ungaro', 'Valentino', 'Versace',
                    'Victor', "Victoria's Secret", 'Victorinox Swiss Army', 'Viktor & Rolf', 'Vince Camuto',
                    'Visconti di Modrone', 'Voi Jeans', 'Warner Bros.', 'Xerjoff', 'Yardley', 'Yohji Yamamoto',
                    'Zadig & Voltaire', 'Zippo', 'Zirh', 'Escada', 'Elizabeth Arden', 'Jade Goody', 'Fila',
                    'Jean Patou', 'Sarah Jessica Parker', 'Britney Spears', 'Ariana Grande', 'Courreges',
                    'Gres Parfums', 'Worth', 'Kylie Minogue', 'Nina Ricci', 'Lancôme', 'Jennifer Lopez', 'Accessorize',
                    'Agatha Paris', 'Agent Provocateur', 'Ajmal', 'Angel Schlesser', 'Anna Sui', 'Anne Klein',
                    'Kent Cosmetics Limited', 'Aquolina', 'Asdaaf', 'Atkinsons', 'Aubusson', 'Barbie', 'Beyonce',
                    'Bill Blass', 'Billie Eilish', 'Blue Stratos', 'Blumarine', 'Bob Mackie', 'Bois 1920', 'Borghese',
                    'Byblos', 'Byredo', 'Cafe Parfums', 'Cofinluxe', 'Caron', 'Carthusia', 'Caudalie',
                    'Chantal Thomass', 'Charles Jourdan', 'Cher', 'Cheryl', 'Chloé', 'Christina Aguilera', 'Clarins',
                    'Clean', 'Coleen Rooney', 'Concept V Design', 'Cosmopolitan', 'Costume National', 'Dear Rose',
                    'Derek Lam 10 Crosby', 'Desigual', 'Diptyque', 'Dora the Explorer', 'Eau Jeune', 'Eight & Bob',
                    'Elie Saab', 'Elle', 'Ellen Tracy', 'Emporio Armani', 'Faconnable', 'Fendi', 'Firetrap',
                    'Frédéric Malle', 'Furla', 'Ghost', 'Gloria Vanderbilt', 'Gwen Stefani', 'Houbigant',
                    'Indulgent Moments', 'Jason Wu', 'Jenny Glow', 'Jo Malone', 'Jojo Siwa', 'John Richmond',
                    'Juliette Has A Gun', 'Kate Spade', 'Katy Perry', 'Kim Kardashian', 'Krizia', 'La Perla',
                    'Lancaster', 'Lentheric', 'Leonard Paris', 'Liu Jo', 'Louis Feraud', 'MCM', 'Mancera', 'Mango',
                    'Marc Jacobs', 'Mayfair', 'Memo', 'Michael Buble', 'Miu Miu', 'Naomi Campbell', 'Nasomatto',
                    'Nicole Scherzinger', 'Nuxe', 'One Direction', 'Orlov Paris', 'Paris Hilton', 'Paul Lawrence',
                    'Philosophy', 'Pink Soda', 'Pressit', 'Proenza Schouler', 'Puma', 'Reminiscence', 'Repetto',
                    'Revlon', 'Rihanna', 'Roger & Gallet', 'Romeo Gigli', 'Roos & Roos', 'Scotch & Soda', 'Sean John',
                    'Seksy', 'Shakira', 'Shiseido', 'Simply', 'Slava Zaitsev', 'Sofia Vergara', 'Stella McCartney',
                    'Superdry', 'Swarovski', 'Taylor of London', 'Terry de Gunzburg', 'The Big Apple', 'Tiffany & Co',
                    'Travalo', 'Ulric de Varens', 'United Colors & Prestige Beauty', 'Usher', 'Van Cleef & Arpels',
                    'Vera Wang', 'Whatever It Takes', 'Whitney Houston', 'Woods of Windsor', 'Estée Lauder',
                    'Yacht Man', 'Gres', 'Vanderbilt', 'Puig', 'Armani', 'Bultaco', 'Montblanc', 'Aristocrazy',
                    'Lattafa', 'Scalpers', 'Adolfo Domínguez', 'Dior', 'Hermès', 'Alvarez Gomez', 'Hannibal Laguna',
                    'El Ganso', 'Saphir', "Chanson d'Eau", "Women'secret", 'Thierry Mugler', 'Monotheme',
                    'Mercedes-Benz', 'Pacha Ibiza', 'Dsquared2', 'Vicky Martín Berrocal', 'Teaology',
                    'Juliette Has a Gun', 'Blood Concept', '4711', 'Nenuco', 'Hackett London', 'Courrèges',
                    'Serge Lutens', 'Halloween', 'Giorgio Beverly', 'Ferrari', 'Tabac Original', 'Faberge',
                    'Don Algodon', 'Bien-Etre', 'Heno de Pravia', 'Agatha Ruiz de la Prada', 'Real Madrid',
                    'Victorio & Lucchino', 'Tiziana Terenzi', 'Jean Louis Scherrer', 'Crossmen', 'Nike', 'Mustela',
                    'Rasasi', 'Legrain', 'Pertegaz', 'Coronel Tapiocca', 'Springfield', 'Acqua di Selva',
                    'Ministry Of Oud', 'Seven Cosmetics', 'Coquette', 'Tartine et Chocolat', 'Real Madrid C.F.',
                    'Titto Bluni', 'Quorum', 'Prêt à Porter', "L'Occitane", 'Reebok', 'Denenes', 'Brummel',
                    'Agua de Sevilla', 'Roger&Gallet', 'Varon Dandy', 'Natural Honey', 'Mauboussin', 'Pocoyo',
                    'Eau My Unicorn', 'Le Couvent', 'Munich', 'Afnan', 'Pepe Jeans', 'Biotherm', 'Hello Kitty',
                    'Martinelia', 'Klorane', 'Façonnable', 'Mickey Mouse', 'Etro', 'Nickelodeon', 'Escentric',
                    'Minnie Mouse', 'Sophie La Girafe', 'Euroluxe', 'Lorenay', 'Helene Fischer', 'Fred Hayman',
                    'Naf Naf', 'Eau my BB', 'Sportman', 'Amouage', 'Spiderman', 'Sensai', 'Liu·Jo', 'Marbert',
                    'Alqvimia', "Jacq's", 'Eau My Planet', 'Farala', 'Agatha', 'Alejandro Sanz', 'DC', 'Aigner',
                    'Barbour', 'Maja', 'Jacomo', 'Avril Lavigne', 'Pino silvestre', 'David Beckham', 'Frozen',
                    'Leonard', 'Cry Babies', 'Casamorati', 'Mistral', 'Chevignon', 'F.C. Barcelona',
                    'Gabriela Sabatini', 'Axe', 'Christian Lacroix', 'Luxana', 'VARIOS', 'RAMON MOLVIZAR', 'GIVENCHY',
                    'DON ALGODON', 'Pacha', 'ANTONIO PUIG', 'GUILLAB', 'AGATHA RUIZ DE LA PRADA', 'GRES', 'ADIDAS',
                    'SAPHIR', 'ALVAREZ GOMEZ', 'AIRE DE SEVILLA', 'COTY', 'DAVID BUSTAMANTE', 'MYRURGIA', 'SHISEIDO',
                    'BLOOD CONCEPT', 'DIESEL', 'GENESSE', 'ULRIC DE VARENS', 'NIKE', 'JIMMY CHOO', 'Donna Karan',
                    'KENZO', 'POLICE', 'Jesus Del Pozo', 'DANA', 'CHRISTIAN DIOR', 'CONCEPT V DESIGN', 'CHLOE',
                    'GUERLAIN', 'Joop', 'ABERCROMBIE', 'BENETTON', 'JULIETTE HAS A GUN', 'DSQUARED', 'MONTALE',
                    'ZADIG & VOLTAIRE', 'Gianni Versace', 'HERMÉS', 'ISSEY MYAKE', 'CERRUTI', 'PEDRO DEL HIERRO', 'PRADA', 'TITTO BLUNI',
                    'Y.S.LAURENT', 'Lancome', 'VIKTOR Y ROLPH', 'DAVID BECKHAM', 'SHAKIRA', 'Hombre', 'HANNIBAL LAGUNA',
                    'EL GANSO', 'UNISEX', 'TOM FORD', 'ANNE MÖLLER', 'Niños', 'ARISTOCRAZY', 'ELIE SAAB',
                    'ACQUA DI PARMA', 'LE COUVENT', 'TRUSSARDI', 'EMANUEL UNGARO', 'Herm√®s', 'LANCOME', 'TIFFANY&CO',
                    'ZARKO', 'SERGE LUTENS', 'PHILIPP PLEIN', 'NARCISO RODRIGUEZ', 'varios', 'SISLEY', 'PLAYBOY',
                    'TORRE OF TUSCANY', 'CUSTO BARCELONA', 'THE DIFFERENT COMPANY', 'LALIQUE', 'JOAQUIN CORTES',
                    'LINARI', 'THE FRUIT COMPANY', 'LUBIN', 'CARTHUSIA', 'PROFUMI DEL FORTE', 'LORENZO VILLORESI',
                    'CLARINS', 'STARCK', 'ANNICK GOUTAL', 'Mujer', 'MARC JACOBS', 'ARMAND BASI', 'TONINO LAMBORGHINI',
                    'DESIGUAL', 'HERMES', 'UMBRO', 'JAMES BOND', 'GUESS', 'BEYONCE', 'MTV', 'AGUA DE SEVILLA',
                    'ROGER & GALLET', 'CRISTINA PEDROCHE', 'BIOTHERM', 'LAGERFELD', 'JIL SANDER', 'GAI MATTIOLO',
                    'JUICE COUTURE', 'BEJAR SIGNATURE', 'CLEAN', 'REPETTO', 'DIADORA', 'Roberto Verino',
                    'Oscar de la Renta', 'LIU JO', 'ACQUA DI PORTOFINO', 'REPLAY', 'STAR NATURE', 'MASSIMO DUTTI',
                    'DAVID BISBAL', 'BYBLOS', 'VERA WANG', 'ED HARDY', 'ALYSSA ASHLEY', 'STELL MC CARTNEY', 'ARAMIS',
                    'LA MARTINA', 'PERRY ELLIS', 'MISS SIXTY', 'CHEVIGNON', 'CHARRO', 'PENHALIGON`S',
                    'GIANFRANCO FERRE', 'CHOPARD', 'LA PERLA', 'M.MICALLEF', 'BALMAIN', 'CUBA', 'AGENT PROVOCATEUR',
                    'REMINISCENCE', 'WORKSHOP', 'AIGNEER', 'LAPIDUS', 'DALI', 'BLUMARINE', 'MONTANA', 'BREIL',
                    'VAN GILS', 'CARRERA', 'BRUT FABERGE', 'EUROLUXE', 'ETRO', 'ARROGANCE', 'AUBADE', 'DUCATI',
                    'ANIMALE BLACK', 'AMOUAGE', 'ROBERTO CAPUCCI', 'GILLES CANTUEL', 'LAROME', 'FRANCK OLIVIER',
                    'RODWAY', 'PAUL SMITH', 'PAOLO GIGLI', 'PARFUM COLLECTION', 'PAL ZILERI', 'JUSTIN BIEBER',
                    'MOMO DESIGN', 'CARON', 'MAUBOUSSIN', 'ALVIERO MARTINI', 'KITON', 'LIZ CLAIBORNE', 'ANNA SUI',
                    'JEAN LOUIS SCHERRER', 'FRANK APPLE', 'FIORUCCI', 'MORGAN', 'AXE', 'BEST COMPANY', 'MANDATE',
                    'GUY LAROCHE', 'POMELLATO', 'BRUNO BANANI', 'CARMEN SEVILLA', 'ELLEN TRACY', 'DUPONT', 'ZUMA',
                    'FTI', 'MADONNA', 'BONGO', 'JACQUES BOGART', 'LUCIANO SOPRANI', 'MONELLA VAGABONDA', 'WHISKY',
                    'ALESSANDRO DELLA TORRE', 'BOND Nº 9', 'LAMBRETTA', 'PETER ANDRE', 'CHARRIOL', 'LES COPAINS',
                    'YARDLEY', 'ISOTTA FRASCHINI', 'NAOMI CAMPBELL', 'MONSOON', 'JHON RICHMON', 'CHARLIE REVLON',
                    'BODY-X', 'SWISS ARMY', 'OMAR SHARIF', 'LOFT MONACO', 'ICEBERG', 'MARIA CAREY', 'KRIZIA',
                    'COSTUME NATIONAL', 'Oleg Cassini', 'HUMMER', 'JEAN-CHARLES BROSSEAU', 'FUJIYAMA',
                    'ROYAL COPENHAGEN', 'IKKS', 'PARIS HILTON', 'CAFE', 'VISCONTI DI MODRONE', 'GEOFFEY BEENE',
                    'SEAN JOHN', 'KYLIE MINOGUE', 'GHOST', 'CHRISTINA AGUILERA', 'Maurer & Wirtz', 'SERGIO TACCHINI',
                    'Armand basi', 'James Bond 007', 'Angel schlesser', 'Biotherm Homme', 'Bulgari', 'Calvin klein',
                    'Dolce gabbana', 'Emporio armani', 'Estee lauder', 'Gianfranco ferre', 'Giorgio armani',
                    'Hugo boss', 'Issey miyake', 'Jean-paul gaultier', 'Laura biagiotti', 'Mont blanc', 'Nivea Men',
                    'Ralph lauren', 'Roberto cavalli', 'Salvatore ferragamo', 'Yves saint laurent', 'Helena Rubinstein',
                    'Lolita lempicka', 'Ach Brito', 'Antonio banderas', 'B.U.', 'Britney spears', 'Dkny',
                    'Elizabeth arden', 'Jacadi', 'Michael kors', 'Nina ricci', 'P.gres', 'Tiffany & Co.Parfum',
                    'Women secret']
    for brand in known_brands:
        if brand.lower() in fragrance_name.lower():
            return brand
    return "Unknown"


def get_brands_from_excel(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path)

    # Extract the unique brands from the 'original_brand' column, drop NaNs, and convert to a list
    unique_brands = df['original_brand'].dropna().unique().tolist()

    return unique_brands.lower()

# Standardize brand names based on the mapping
def standardize_brand_names(brand_name):
    # Mapping of brand names to their standardized forms
    BRAND_NAME_MAPPING = {
        'afnan perfumes': 'Afnan',
        'abercrombie': 'Abercrombie & Fitch',
        'angel schlesser': 'Angel Schlesser',
        'antónio banderas': 'António Banderas',
        'antonio banderas': 'António Banderas',
        'annick goutal': 'Goutal Paris',
        'aramis': 'Aramis',
        'arden': 'Elizabeth Arden',
        'armani': 'Giorgio Armani',
        'balmain': 'Pierre Balmain',
        'givenchi': 'Givenchy',
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
        'issey myake': "Issey Miyake",
        'duck': 'Mandarina Duck',
        'emporio armani': 'Giorgio Armani',
        'estee lauder': 'Estée Lauder',
        'ferragamo': 'Salvatore Ferragamo',
        'gianfranco ferre': 'Gianfranco Ferré',
        'gianni versace': 'Versace',
        'giorgio beverly': 'Giorgio Beverly Hills',
        'gualtier': 'Jean Paul Gaultier',
        'guerlain': 'Guerlain',
        'gres': 'Grès',
        'hermes': 'Hermès',
        'Herm√®s': 'Hermès',
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
        'viktor and rolf': 'Viktor & Rolf',
        'yslaurent': 'Yves Saint Laurent',
        'swiss army': 'Victorinox Swiss Army',
        'ysl': 'Yves Saint Laurent',
        'zegna': 'Ermenegildo Zegna'
    }
    # Convert the brand name to lower case
    lower_case_brand_name = brand_name.lower()
    # Use the dictionary to map the brand name to the standard name if it exists
    return BRAND_NAME_MAPPING.get(lower_case_brand_name, brand_name.title())


def fix_contractions(text):
    # Regular expression pattern to find and fix contractions and words ending with 'S
    contractions_pattern = re.compile(r"\b([a-zA-Z]+)\'([a-zA-Z]+)\b")
    words_ending_s_pattern = re.compile(r"\b([a-zA-Z]+)\'S\b")

    # Fix contractions like "don't"
    text = contractions_pattern.sub(lambda x: f"{x.group(1).capitalize()}'{x.group(2).lower()}", text)

    # Ensure words ending in 'S remain lowercase
    text = words_ending_s_pattern.sub(lambda x: f"{x.group(1).capitalize()}'s", text)

    return text


def fix_l_vowel_contractions(text):
    # Fix "L'" or "J'" followed by a vowel or 'H' to "L'" or "J'" and capitalize the vowel or 'H'
    l_vowel_pattern = re.compile(r"\b([LJ])'([aeiouh])", re.IGNORECASE)
    return l_vowel_pattern.sub(lambda x: f"{x.group(1).capitalize()}'{x.group(2).upper()}", text)


# Standardize fragrance names
def standardize_fragrance_names(string, brand):
    # Convert the entire string to lowercase
    string = string.lower()
    string = string.replace('`', "'")
    string = string.replace('´', "'")

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

    # Title-case each word, but keep some in Upper CASE
    title_cased_words = []
    for i, word in enumerate(words):
        if word in {'edt', 'edp', 'edc'}:
            title_cased_words.append(word.upper())
        else:
            if i == 0:
                title_cased_words.append(word.capitalize())
            else:
                title_cased_words.append(word.title())

    # Join the words back into a single string
    title_cased_string = ' '.join(title_cased_words)

    # Fix contractions after title-casing
    title_cased_string = fix_contractions(title_cased_string)

    # Convert 'Ck' to 'CK'
    title_cased_string = re.sub(r'\bCk\b', 'CK', title_cased_string, flags=re.IGNORECASE)

    # Fix "L'" or "J'" followed by a vowel or 'H' to "L'" or "J'" and capitalize the vowel or 'H'
    title_cased_string = fix_l_vowel_contractions(title_cased_string)

    # Ensure "ml" and "g" are maintained in lowercase
    title_cased_string = re.sub(r'(\d+)\s*ml', r'\1ml', title_cased_string, flags=re.IGNORECASE)
    title_cased_string = re.sub(r'(\d+)\s*g', r'\1g', title_cased_string, flags=re.IGNORECASE)
    title_cased_string = re.sub(r'(\d+)\s*th', r'\1th', title_cased_string, flags=re.IGNORECASE)

    title_cased_string = re.sub(r'\s+', ' ', title_cased_string).strip()

    return title_cased_string

def convert_df_to_fragrance_items(df):
    fragrances = []
    for _, row in df.iterrows():
        last_updated_at = row['last_updated_at']
        if isinstance(last_updated_at, pd.Timestamp):
            last_updated_at = last_updated_at.strftime("%Y-%m-%d %H:%M:%S")

        fragrance = FragranceItem(
            original_brand=row['original_brand'],
            original_fragrance_name=row['original_fragrance_name'],
            clean_brand=row['clean_brand'],
            website_clean_fragrance_name=row.get('website_clean_fragrance_name'),
            final_clean_fragrance_name=row['final_clean_fragrance_name'],
            quantity=row.get('quantity'),
            price_amount=row['price_amount'],
            price_currency=row['price_currency'],
            link=row['link'],
            website=row['website'],
            country=row['country'].split(',') if isinstance(row['country'], str) else [],
            last_updated_at=datetime.strptime(last_updated_at, "%Y-%m-%d %H:%M:%S"),
            is_set_or_pack=row['is_set_or_pack'],
            page=row.get('page'),
            gender=row.get('gender'),
            price_history=row.get('price_history'),
            price_changed=row.get('price_changed', False),
            price_alert_threshold=row.get('price_alert_threshold'),
            is_in_stock=row.get('is_in_stock')
        )
        fragrances.append(fragrance)
    return fragrances


def extract_random_fragrance_names(file_path, num_samples_per_website=200, total_websites=4):
    # Load the Excel file
    df = pd.read_excel(file_path)

    # Filter the dataframe where is_set_or_pack is False
    filtered_df = df[df['is_set_or_pack'] == False]

    # Get unique websites
    unique_websites = filtered_df['website'].unique()

    # Initialize a list to store the random fragrance names and corresponding websites
    random_fragrance_names = []
    websites = []

    # Loop through each website and extract random samples
    for website in unique_websites[:total_websites]:  # Assuming you want to limit to the first 4 websites
        website_df = filtered_df[filtered_df['website'] == website]
        if len(website_df) >= num_samples_per_website:
            sampled_names = random.sample(list(website_df['website_clean_fragrance_name']), num_samples_per_website)
        else:
            sampled_names = list(website_df['website_clean_fragrance_name'])

        random_fragrance_names.extend(sampled_names)
        websites.extend([website] * len(sampled_names))

    return random_fragrance_names, websites


