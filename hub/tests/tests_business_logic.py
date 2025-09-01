from django.test import TestCase
from unittest.mock import Mock
from .tests_functions import CDClient


class CDCLientTest(TestCase):
    def test_find_selected_cd_returns_cheapest(self):
        cd1 = Mock()
        cd1.get_product.return_value = {"product": "computer", "quantity": 12, "price": 100.50}

        cd2 = Mock()
        cd2.get_product.return_value = {"product": "computer", "quantity": 100, "price": 39.50}

        cd3 = Mock()
        cd3.get_product.return_value = {"product": "computer", "quantity": 1, "price": 100.50}

        selected = CDClient.find_selected_cd("computer", 5, [cd1, cd2, cd3])

        self.assertEqual(selected["price"], 39.50)
        self.assertEqual(selected["product"], "computer")
        self.assertEqual(selected["quantity"], 100)
