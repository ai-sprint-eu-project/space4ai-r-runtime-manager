import asyncio
import os
import requests
import subprocess

keepalive_time_sec = 10
url_base = '0.0.0.0'
alive_missing_counter = 0
alive_missing_max = 5

role = os.getenv('S4AIR_ROLE')
print("Role: %s" % role)

url_master = os.getenv('S4AIR_MASTER_URL')
if url_master is None:
    url_master = url_base
print("Master url: %s" % url_master)

url_slave = os.getenv('S4AIR_SLAVE_URL')
if url_slave is None:
    url_slave = url_base
print("Slave url: %s" % url_slave)


if role is None:
   role = 'master'
elif "master" == role:
    url = url_master
else:
    url = url_slave

def setRmOpt(status):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    rm_opt_file = dir_path + "/rm_opt"
    #print(rm_opt_file)
    f = open(rm_opt_file,'w')
    f.write(status)
    f.close()

async def display_date():
    global alive_missing_counter
    global alive_missing_max
    global role
    global url
    vm_off = False
    while True:
        print("***")
        response = os.system("ping -c 1 " + url + " >/dev/null 2>&1")
        #response = subprocess.check_output(["ping", "-c", "1", url])
        #run_cmd = subprocess.run(["echo", url], capture_output=True, text=True)
        #response = run_cmd.stdout
        #print("PING: %s" %response)
        if response == 0:
           print(f"{url} is UP!")
           alive_missing_counter = 0
           if ("master" == role) and (True == vm_off):
                 print("Master is switching on all VMs...")
                 # TODO
                 vm_off = False
                 print("Activating Master...")
                 setRmOpt('ON')
        else:
           print(f"{url} is down!")
           alive_missing_counter = alive_missing_counter + 1
           if alive_missing_counter > alive_missing_max:
              print("PARTNER IS MISSING!!!!")
              if ("master" == role) and (False == vm_off):
                 print("Master is switching off all VMs but 1...")
                 # TODO
                 vm_off = True
                 print("Deactivating Master...")
                 setRmOpt('OFF')
              elif ("master" == role) and (True == vm_off):
                 print("Master is waiting Slave connectivity...")
              else:
                 print("Activating Slave...")
                 # TODO

        await asyncio.sleep(keepalive_time_sec)

asyncio.run(display_date())