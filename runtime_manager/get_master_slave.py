import asyncio
import os
import requests
import subprocess
import sys
sys.path.append("./")
sys.path.append("../")
from im_interface import  *
from utils import *
from config import update_app_dir
import config as cfg

def get_master_slave(application_dir):
    update_app_dir(application_dir)
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
            print("%s SLAVE OSCAR URL: %s\n" % (slave_component_url))
        if(item == master_component):
            output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
            master_component_url = item, yaml.safe_load(output)['outputs']['oscar_service_url']
            print("%s MASTER OSCAR URL: %s\n" % (master_component_url))
    
    return (slave_component, slave_component_url, master_component, master_component_url)

get_master_slave("/aisprint/apps/app_demo_mon_OK_6_1/")