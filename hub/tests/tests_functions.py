from django.test import TestCase, Client
import requests

class CDClient(TestCase):
    def __init__(self, base_url):
        self.base_url = base_url

    def get_product(self, item):
        response = requests.get(f"{self.base_url}/products/{item}/")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def find_selected_cd(product, quantity, cds):
        selected_cd = {}
        for cd in cds:
            product = cd.get_product(product)
            
            if not selected_cd:
                selected_cd = {"product": product["product"], "quantity": product["quantity"], "price": product["price"]}

            if product["price"] < selected_cd["price"]:
                selected_cd = {"product": product["product"], "quantity": product["quantity"], "price": product["price"]}
        
        return selected_cd