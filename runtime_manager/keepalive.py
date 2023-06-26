import asyncio
import os
import requests
import subprocess
import shutil
import sys
sys.path.append("./")
sys.path.append("../")
from im_interface import  *
from utils import *
from config import update_app_dir
import config as cfg


keepalive_time_sec = 10
url_base = '0.0.0.0'
alive_missing_counter = 0
alive_missing_max = 5

role = os.getenv('S4AIR_ROLE')
print("Role: %s" % role)

#url_master = os.getenv('S4AIR_MASTER_URL')
#if url_master is None:
#    url_master = url_base
#print("Master url: %s" % url_master)

#url_slave = os.getenv('S4AIR_SLAVE_URL')
#if url_slave is None:
#    url_slave = url_base
#print("Slave url: %s" % url_slave)


#if role is None:
#   role = 'master'
#elif "master" == role:
#    url = url_master
#else:
#    url = url_slave

########################################################################
def get_master_slave(application_dir):
    update_app_dir(application_dir)

    if os.path.exists(application_dir + "/aisprint/deployments/"  + cfg.current_folder):
        print("The Current Deployment folder does exist")
    else:
        print("The Current Deployment folder does not exist, let's proceed with its creation")
        try:
            shutil.copytree(application_dir + "/aisprint/deployments/base", application_dir + "/aisprint/deployments/" + cfg.current_folder)
        except Exception as ex:
            print("The files at '" + application_dir +"/aisprint/deployments/base/src ' could not be copied. %s" % str(ex))

    if not os.path.exists(application_dir + "/aisprint/deployments/"+ cfg.current_folder +"/production_deployment.yaml"):
        print("production_deployment.yaml does not exist")
        create_optimal_deployment(application_dir)



    infras_file = yaml_as_dict("%s/aisprint/deployments/%s/im/infras.yaml" % (application_dir, cfg.current_folder))
    print("Infra content:")
    print(yaml.safe_dump(infras_file, indent=2))

    files = list(set(glob.glob("%s/*.yaml" % (application_dir + "/aisprint/deployments/" + cfg.current_folder + "/im"))) - set(glob.glob("%s/infras.yaml" % (application_dir + "/aisprint/deployments/" + cfg.current_folder + "/im"))))
    pd = yaml_as_dict("%s/aisprint/deployments/%s/production_deployment.yaml" % (application_dir, cfg.current_folder))
    pd["System"]["toscas"] = {}
    for one_file in files:
        name_component = one_file.split("/")[-1].split(".")[0]
        tosca_new_dic = yaml_as_dict(one_file)
        # tosca_new_dic = place_name(tosca_new_dic)
        tosca_new_dic["component_name"] = name_component
        # print(tosca_new_dic["component_name"])
        pd["System"]["toscas"][name_component] = tosca_new_dic



    el_updated = []

    qos_files = list(set(glob.glob("%s/*.yaml" % (application_dir + "/aisprint/deployments/" + cfg.current_folder + "/ams"))))

    slave_component = ""
    master_component = ""
    slave_component_url = ""
    master_component_url = ""

    rootComponent = searchNextComponent(pd, "")
    while("" != rootComponent):
        el = pd["System"]["Components"][rootComponent]['executionLayer']
        rt = getResourcesType(rootComponent, pd)
        print("Root component: %s" % rootComponent)
        print("ExecutionLayer: %s" % el)
        print("Resourcetype: %s" % rt)

        if "PhysicalAlreadyProvisioned" == rt:
            slave_component = rootComponent
        else:
            master_component = rootComponent
            break

        rootComponent = searchNextComponent(pd, rootComponent)
        print("\n")

    for item, value in infras_file.items():

        if(item == slave_component):
            output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
            slave_component_url = item, yaml.safe_load(output)['outputs']['oscar_service_url']
            print("%s SLAVE OSCAR URL: %s\n" % slave_component_url)
        if(item == master_component):
            output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
            master_component_url = item, yaml.safe_load(output)['outputs']['oscar_service_url']
            print("%s MASTER OSCAR URL: %s\n" % master_component_url)

    return (slave_component, slave_component_url[1], master_component, master_component_url[1])


########################################################################


s, su, m, mu = get_master_slave(sys.argv[1])

print("-- %s\n --%s\n --%s\n --%s\n" %(s, su, m, mu))

if role is None:
   role = 'master'
elif "master" == role:
    url = su.replace('https://', '')
else:
    url = mu.replace('https://', '')

running = ("" != su)

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
    global running
    vm_off = False
    while running:
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
