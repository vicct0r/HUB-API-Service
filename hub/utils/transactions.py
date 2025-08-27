import requests

def buy_endpoint(cd_url, product, quantity):
        response = requests.post(url=f"{cd_url}/product/sell/{product}/{quantity}/", timeout=5)
        
        if response.status_code == 200:
            return True
        else:
            return False
        

def sell_endpoint(cd_url, product, quantity):
    response = requests.post(url=f"{cd_url}/product/buy/{product}/{quantity}/", timeout=5)

    if response.status_code == 200:
        return True
    else:
        return False
