import requests

def cd_running(cd_url):
    try:
        response = requests.get(cd_url+"info/", timeout=5)
        if response.status_code != 200:
            return False
        return True
    except Exception as e:
        print(str(e))
        return None