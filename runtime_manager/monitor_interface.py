import requests

url = "http://127.0.0.1:5000"


def monitor_call():
    try:
        resp = requests.request("GET", "%s/alarm" % url)
        return resp.text.split("\n")
    except Exception as ex:
        print(str(ex))
        return False, str(ex)

monitor_call()