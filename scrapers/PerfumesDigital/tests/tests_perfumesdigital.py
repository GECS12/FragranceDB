import unittest
from scrapers.PerfumesDigital.main_scraper_perfumesdigital import standardize_brand_names, standardize_fragrance_names, \
    clean_fragrance_name_perfumedigital


class TestPerfumeDigitalScraper(unittest.TestCase):

    def test_standardize_brand_names(self):
        self.assertEqual(standardize_brand_names('Hermes'), 'Hermès')
        self.assertEqual(standardize_brand_names('YSL'), 'Yves Saint Laurent')
        self.assertEqual(standardize_brand_names('Unknown Brand'), 'Unknown Brand')  # No conversion case

    # def test_clean_fragrance_name_perfumedigital(self):
    #     self.assertEqual(clean_fragrance_name_perfumedigital('ARMANI IN LOVE WITH YOU FREEZE EDP 50 REGULAR'),
    #                      'armani in love with you freeze edp 50 ml ')
    #     self.assertEqual(clean_fragrance_name_perfumedigital('CHARLIE REVLON SILVER EDT 100 MLREGULAR'),
    #                      'charlie revlon silver edt 100 ml ')
    #     self.assertEqual(clean_fragrance_name_perfumedigital('LA VIE EST BELLE EDP 15 (QUINCE MILILITROS) ML @'),
    #                      'la vie est belle edp 15 ml (Tester)')
    #     self.assertEqual(clean_fragrance_name_perfumedigital('ARMANI IN LOVE WITH YOU EDP 100 @'),
    #                      'armani in love with you edp 100 ml (Tester)')

    # def test_standardize_fragrance_names(self):
    #     self.assertEqual(standardize_fragrance_names('Swiss Army Altitude Eau de Toilette 100ml Spray', 'Swiss Army'),
    #                      'Victorinox Swiss Army Altitude EDT 100ml')
    #     self.assertEqual(standardize_fragrance_names('Acqua Di Gio Eau de Toilette 50ml Spray', 'Armani'),
    #                      'Giorgio Armani Acqua Di Gio EDT 50ml')
    #     self.assertEqual(standardize_fragrance_names('Opium Eau de Parfum 90ml Spray', 'YSL'),
    #                      'Yves Saint Laurent Opium EDP 90ml')
    #     self.assertEqual(standardize_fragrance_names('Fragrance Without Brand Name 30ml', ''),
    #                      'Fragrance Without Brand Name 30ml')


if __name__ == '__main__':
    unittest.main()
