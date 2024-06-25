import unittest
from bs4 import BeautifulSoup
from datetime import datetime
from classes.classes import FragranceItem
from scrapers.PerfumesDigital.main_scraper_perfumesdigital import parse
import html

class TestFragranceItemCreation(unittest.TestCase):

    def setUp(self):
        # Sample HTML input to mock the scraping result
        self.html = '''
        <td align="center" style="width:33%;">
            <table cellpadding="0" cellspacing="5" border="0">
                <tbody>
                    <tr>
                        <td style="height:100px " class="pic">
                            <a href="index.php?op=descripcion&amp;id=34115">
                                <img src="catalog/basilipoe22.jpg" border="0" alt="HERMES EAU DE BASILIQUE POURPRE EAU DE COLOGNE 100 ML @" title=" HERMES EAU DE BASILIQUE POURPRE EAU DE COLOGNE 100 ML @ " width="148" height="125">
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <td style="height:67px " class="vam">
                            <a href="index.php?op=descripcion&amp;id=34115">HERMES EAU DE BASILIQUE POURPRE EAU DE COLOGNE 100 ML @</a> <br>
                            Marca:<i>Hermès</i><br>
                            La colección de colognes de Hermès, un terreno de juego infinito y virtuoso, explora la sensorialidad de las materias primas. Es un signo de placer inmediato y generoso, que aúna más allá de gén
                        </td>
                    </tr>
                    <tr>
                        <td style="height:31px " class="vam">
                            <span class="productSpecialPrice"><s>78.00</s>  46.99 €</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="height:76px ">
                            <a href="index.php?op=descripcion&amp;id=34115"><img src="button_details-2.gif" border="0" alt=""></a><br>
                            <br style="line-height:1px">
                            <a href="index.php?op=procesa&amp;id_producto=34115&amp;unidades=1&amp;ID_FAMILIA_PASE=&amp;PASE=0&amp;buscado=HERMES&amp;marca=&amp;ORDEN=&amp;precio1=&amp;precio2="><img src="button_add_to_cart1-2.gif" tppabs="http://osc3.template-help.com/osc_17382/includes/languages/english/images/buttons/button_add_to_cart1-2.gif" border="0" alt=""></a><br>
                        </td>
                    </tr>
                </tbody>
            </table>
        </td>
        '''
        self.url = "https://perfumedigital.es/index.php?op=descripcion&id=34115"
        self.expected_fragrance = FragranceItem(
            brand="Hermès",
            original_fragrance_name="HERMES EAU DE BASILIQUE POURPRE EAU DE COLOGNE 100 ML @",
            clean_fragrance_name="Hermès Hermes Eau De Basilique Pourpre EDC (Tester)",
            quantity=100.0,
            price_amount=46.99,
            price_currency="€",
            link=self.url,
            website="PerfumeDigital.es",
            country=["PT", "ES"],
            last_updated_at=datetime.now(),
            is_set_or_pack=False,
            gender=None,
            price_alert_threshold=None
        )

    def test_fragrance_item_creation(self):
        # Parse the HTML using the parse function
        fragrances = parse(self.html, self.url)

        # Ensure only one fragrance item is created
        self.assertEqual(len(fragrances), 1)

        fragrance = fragrances[0]

        # Decode HTML entities in the expected and actual links
        decoded_expected_link = html.unescape(self.expected_fragrance.link)
        decoded_actual_link = html.unescape(fragrance.link)

        # Check each attribute of the fragrance item
        self.assertEqual(fragrance.brand, self.expected_fragrance.brand)
        self.assertEqual(fragrance.original_fragrance_name, self.expected_fragrance.original_fragrance_name)
        self.assertEqual(fragrance.clean_fragrance_name, self.expected_fragrance.clean_fragrance_name)
        self.assertEqual(fragrance.quantity, self.expected_fragrance.quantity)
        self.assertEqual(fragrance.price_amount, self.expected_fragrance.price_amount)
        self.assertEqual(fragrance.price_currency, self.expected_fragrance.price_currency)
        self.assertEqual(decoded_actual_link, decoded_expected_link)
        self.assertEqual(fragrance.website, self.expected_fragrance.website)
        self.assertEqual(fragrance.country, self.expected_fragrance.country)
        self.assertEqual(fragrance.is_set_or_pack, self.expected_fragrance.is_set_or_pack)
        self.assertEqual(fragrance.gender, self.expected_fragrance.gender)
        self.assertEqual(fragrance.price_alert_threshold, self.expected_fragrance.price_alert_threshold)

        # Print the attributes used in ID generation for debugging
        print("Attributes for expected ID generation:")
        print(f"Brand: {self.expected_fragrance.brand}")
        print(f"Original Fragrance Name: {self.expected_fragrance.original_fragrance_name}")
        print(f"Quantity: {self.expected_fragrance.quantity}")
        print(f"Link: {self.expected_fragrance.link}")
        print(f"Website: {self.expected_fragrance.website}")

        print("Attributes for actual ID generation:")
        print(f"Brand: {fragrance.brand}")
        print(f"Original Fragrance Name: {fragrance.original_fragrance_name}")
        print(f"Quantity: {fragrance.quantity}")
        print(f"Link: {fragrance.link}")
        print(f"Website: {fragrance.website}")

        # Recreate the expected ID based on the current datetime
        fragrance.last_updated_at = self.expected_fragrance.last_updated_at
        expected_id = self.expected_fragrance.generate_id()
        actual_id = fragrance.generate_id()

        self.assertEqual(actual_id, expected_id)


if __name__ == '__main__':
    unittest.main()
