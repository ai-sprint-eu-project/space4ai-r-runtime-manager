import asyncio
import os
import subprocess
import shutil
import sys
sys.path.append("./")
sys.path.append("../")
from im_interface import *
from utils import *
from config import update_app_dir
import config as cfg


keepalive_time_sec = 10
url_base = '0.0.0.0'
alive_missing_counter = 0
alive_missing_max = 5

role = os.getenv('S4AIR_ROLE')
appdir = os.getenv('S4AIR_APP')
print("Role: %s" % role)
print("App dir: %s" % appdir)

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

    slave_component = ""
    master_component = ""
    slave_component_url = ""
    master_component_url = ""
    slave_im = ""
    master_im = ""

    rootComponent = searchNextComponent(pd, "")
    while("" != rootComponent):
        for item, value in pd["System"]["Components"].items():
           print(item, value['name'])
           if rootComponent == value['name']:
              el = pd["System"]["Components"][item]['executionLayer']

        for item, values in pd["System"]["NetworkDomains"].items():
           for item2, values2 in values["ComputationalLayers"].items():
              if (el == values2['number']):
                rt = values2['type']
        #rt = getResourcesType(rootComponent, pd)
        print("Root component: %s" % rootComponent)
        print("ExecutionLayer: %s" % el)
        print("Resourcetype: %s" % rt)

        if "PhysicalAlreadyProvisioned" == rt:
            slave_component = rootComponent
        else:
            master_component = rootComponent
            break

        if ("" == master_component):
            master_component = slave_component
            slave_component = ""

        rootComponent = searchNextComponent(pd, rootComponent)
        print("\n")

    for item, value in infras_file.items():

        if(item == slave_component):
            output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
            slave_component_url = item, yaml.safe_load(output)['outputs']['oscar_service_url']
            print("SLAVE OSCAR URL: %s\n" % slave_component_url[1])
        if(item == master_component):
            output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
            master_component_url = item, yaml.safe_load(output)['outputs']['oscar_service_url']
            print("MASTER OSCAR URL: %s" % master_component_url[1])

            # for item, value in infras_file.items():
            #    if master_component == item:
            #       master_im = value[0].split("/")[-1:][0]
            #       print("MASTER IM: %s" % master_im)
            #       break
            # print("%s MASTER FE ip: %s\n" % (item, yaml.safe_load(output)['outputs']['fe_node_ip']))

    # with open("key_fe.pem", 'w') as f:
    #     f.write(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
    # f.close()
    # run_cmd = subprocess.run(["chmod", "600", "key_fe.pem"])
    # run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "less", "/var/tmp/.im/"+master_im+"/oscar_front_conf.yml"], capture_output=True, text=True)
    # out_2 = run_cmd.stdout
    # if "" != out_2:
    #     role = 'master'
    #     print("CONFIG OSCAR: %s" % yaml.safe_load(out_2)[0]['vars']['dns_host'])
    # else:
    # #     role = 'slave'

    # return (slave_component, slave_component_url[1].replace('https://', ''), master_component, master_component_url[1].replace('https://', ''), role)

    return (slave_component, slave_component_url[1].replace('https://', ''), master_component, master_component_url[1].replace('https://', ''))

########################################################################


if sys.argv[1]:
    application_location = sys.argv[1]
else:
    application_location = appdir

s, su, m, mu, r = get_master_slave(application_location)


role = os.getenv('S4AIR_ROLE')
appdir = os.getenv('S4AIR_APP')
print("Role: %s" % role)
print("App dir: %s" % appdir)

print(" --%s -->%s\n --%s -->%s\n --role -->%s\n" %(s, su, m, mu, role))

if "master" == role:
    url = su
else:
    url = mu

running = ("" != su)

def setRmOpt(status):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    rm_opt_file = dir_path + "/rm_opt"
    #print(rm_opt_file)
    f = open(rm_opt_file,'w')
    f.write(status)
    f.close()

async def run_keep_alive():
    global alive_missing_counter
    global alive_missing_max
    global role
    global url
    global running
    vm_off = False
    slave_activate = False
    setRmOpt('OFF')
    while running:
        print("***")
        try:
           r = requests.head("https://" + url.split(":")[0], timeout=1.50)
           print("------ %s" %r.status_code)
        #response = r.status_code
        #if response == 0:
           print(f"{url} is UP!")
           alive_missing_counter = 0
           # MASTER
           if ("master" == role):
                # VMs were OFF, let's switch them all ON
                if (True == vm_off):
                    print("Master is switching on all VMs...")
                    # TODO
                    vm_off = False
                    print("Activating Master...")
                    setRmOpt('ON')
            # SLAVE
            else:
                if (True == slave_activate):
                    print("Dectivating Slave...")
                    slave_activate = False
        #else:
        except Exception as ex:
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
              elif ("slave" == role) and (False == slave_activate):
                    print("Activating Slave...")
                    # TODO
                    slave_activate = True
              elif ("slave" == role) and (True == slave_activate):
                 print("Slave is waiting Master connectivity...")
                    

        await asyncio.sleep(keepalive_time_sec)

asyncio.run(run_keep_alive())