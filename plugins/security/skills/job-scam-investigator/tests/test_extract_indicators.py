import unittest
from scripts.extract_indicators import extract


class ExtractIndicatorsTests(unittest.TestCase):
    def test_emails_and_links(self):
        result = extract('Escreva para rh@example.org; veja https://example.org/vaga.')
        self.assertEqual(result['emails'], ['rh@example.org'])
        self.assertEqual(result['urls'], ['https://example.org/vaga'])

    def test_phone_br(self):
        self.assertEqual(extract('WhatsApp (11) 90000-0000')['phones_br'], ['+5511900000000'])

    def test_handle(self):
        self.assertEqual(extract('Fale com @Equipe_RH_Teste')['handles'], ['@Equipe_RH_Teste'])

    def test_deduplicates(self):
        self.assertEqual(len(extract('a@example.com a@example.com')['emails']), 1)

    def test_empty(self):
        self.assertTrue(all(not values for values in extract('').values()))


if __name__ == '__main__':
    unittest.main()
