import asyncio
import os
import requests

keepalive_time_sec = 10
url = 'http://0.0.0.0:5001/keepalive'
alive_missing_counter = 0
alive_missing_max = 5
role = os.getenv('S4AIR_ROLE')
print("Role: %s" % role)

async def display_date():
    global alive_missing_counter
    global alive_missing_max
    global role
    while True:
        print("***")
        try:
           resp = requests.get(url=url)
        except requests.ConnectionError:
           print(f"{url} is down!")
           alive_missing_counter = alive_missing_counter + 1
           if alive_missing_counter > alive_missing_max:
              print("PARTNER IS MISSING!!!!")
              if "master" == role:
                 print("Master is switching off all VMs but 1...")
                 # TODO
              else:
                 print("Activating Slave...")
                 # TODO
        else:
           print (resp.status_code)
           print(f"{url} is UP!")
           alive_missing_counter = 0
        await asyncio.sleep(keepalive_time_sec)

asyncio.run(display_date())