import asyncio
import os
import requests

keepalive_time_sec = 10
hostname = "google.com" #example
url = 'http://0.0.0.0:5000/keepalive'
alive_missing_counter = 0
alive_missing_max = 5
async def display_date():
    global alive_missing_counter
    global alive_missing_max
    while True:
        print("***")
        try:
           resp = requests.get(url=url)
        except requests.ConnectionError:
           print(f"{url} is down!")
           alive_missing_counter = alive_missing_counter + 1
           if alive_missing_counter > alive_missing_max:
              print("PARTNER IS MISSING!!!!")
        else:
           print (resp.status_code)
           print(f"{url} is UP!")
           #if (200 == resp.status_code):
           #   print("XXXXXXXXXXX")
           alive_missing_counter = 0
        await asyncio.sleep(keepalive_time_sec)

asyncio.run(display_date())