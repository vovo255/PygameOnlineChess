import requests
from time import sleep

while True:
    try:
        requests.get('http://127.0.0.1:1654/tick')
    except Exception:
        pass
    sleep(1)
