import requests

def gatherAvailableCDs(cds, origin_cd, product, quantity):
    try:
        for cd in cds:
            if cd.url == origin_cd:
                continue
            lower_price = None
            response = requests.get(url=f"{cd.url}product/request/{product}/{quantity}/", timeout=5)

            if lower_price:
                if response.json()['price'] < lower_price:
                    lower_price = {"name": cd.name, "price": response.json()['price']}
            else:
                lower_price = {"name": cd.name, "price": response.json()['price']}
    
        if lower_price:
            return {"cd_name": lower_price["name"], "product_price": lower_price["price"]}
        else:
            return None
    except Exception as e:
        return None