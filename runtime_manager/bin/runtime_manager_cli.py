##############################################################################################################
#                                                                                                            
#               ___   ___                                                 ___   ___                          
#     // | |       / /              //   ) )     //   ) )     //   ) )       / /        /|    / /  /__  ___/ 
#    //__| |      / /              ((           //___/ /     //___/ /       / /        //|   / /     / /     
#   / ___  |     / /      ____       \\        / ____ /     / ___ (        / /        // |  / /     / /      
#  //    | |    / /                    ) )    //           //   | |       / /        //  | / /     / /       
# //     | | __/ /___           ((___ / /    //           //    | |    __/ /___     //   |/ /     / /        
#                                                                                                            
#
# Component: RUNTIME-MANAGER
##############################################################################################################

import click
import sys
import yaml
from deepdiff import DeepDiff
import json
import glob

sys.path.append("../")
from im_interface import  *
from utils import *

@click.group()
def runtime_manager_cli():
    pass
# --application_dir /home/bedoya/cefriel/AISprint-test/api_python/runtime-manager
@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--dir_to_save", help="Path to save the toscas requested", default=None)
def infras(application_dir, dir_to_save):
    auth_path = "%s/%s" % (application_dir, im_auth_path_def)
    responses = im_get_infrastructures(auth_path)
    i = 1
    for response in responses:
        InfId = response.split("%s/infrastructures/" % im_url_def)[1]
        tosca = yaml.safe_load(im_get_tosca(InfId, auth_path))
        tosca["infid"] = InfId
        tosca = place_name(tosca)
        # tosca_path = "%s/%s" % (dir_to_save, tosca_file_dir) + "/" + tosca["component_name"] + "-" + str(i) + ".yaml"
        # tosca_path = dir_to_save + "/" + tosca["component_name"] + "-" + str(i) + ".yaml"
        tosca_path = dir_to_save + "/" + tosca["component_name"] + ".yaml"
        with open(tosca_path, 'w+') as f:
            yaml.safe_dump(tosca, f, indent=2)
        print("DONE. TOSCA files %s has been saved for the InfId %s" % (tosca["component_name"] + "-" + str(i) + ".yaml", InfId))
        i += 1

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--old_dir", help="Path to read the old toscas", default=None, required = True)
@click.option("--new_dir", help="Path to read the new toscas", default=None)
def difference(application_dir, old_dir, new_dir):
    # Processing production files
    production_old_dic = yaml_as_dict("%s/aisprint/deployments/base/production_deployment.yaml" % (application_dir))
    production_new_dic = yaml_as_dict("%s/aisprint/deployments/optimal_deployment/production_deployment.yaml" % (application_dir))
    files = glob.glob("%s/*.yaml" % old_dir)
    production_old_dic["System"]["toscas"] = {}

    #Creation completed old/new-production dictionaries and relate them with their respective InfID
    for one_file in files:
        tosca_old_dic = yaml_as_dict(one_file)
        production_old_dic["System"]["toscas"][tosca_old_dic["component_name"]] = tosca_old_dic
        ## ADD a component that overwrite the component "component1" for "component_name(blurryfaces or mask-detector)"
        if tosca_old_dic["component_name"] in production_old_dic["System"]["Components"]:
            production_old_dic["System"]["Components"][tosca_old_dic["component_name"]]["infid"] = tosca_old_dic["infid"]
    
    files = glob.glob("%s/*.yaml" % new_dir)
    production_new_dic["System"]["toscas"] = {}
    for one_file in files:
        name_component = one_file.split("/")[-1].split(".")[0]
        tosca_new_dic = yaml_as_dict(one_file)
        # tosca_new_dic = place_name(tosca_new_dic)
        tosca_new_dic["component_name"] = name_component
        # print(tosca_new_dic["component_name"])
        production_new_dic["System"]["toscas"][name_component] = tosca_new_dic
    
    
    # Make a verification of the case--------------------------------------
    if len(production_old_dic["System"]["Components"]) == len(production_new_dic["System"]["Components"]):
        print("the number of clusters are the same")
        components_same = component_name_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])    
        machines_same = infrastructures_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])
        if components_same == 1 and machines_same == 1:
            # Case C
            case = "C"
            print("We are in case C")
            print("Case: same machines and cluster, it is just to exchange the infrastructures between each component")
            for components_tosca_old, values_tosca_old in production_old_dic["System"]["toscas"].items():
                for components_new, values_new in production_new_dic["System"]["Components"].items():
                    if values_tosca_old["infid"] == values_new["infid"]:
                        tosca_new = production_new_dic["System"]["toscas"][values_new["name"]]
                        correct_name = values_tosca_old["component_name"] 
                        production_new_dic["System"]["toscas"][values_new["name"]] = mix_toscas(correct_name, production_old_dic["System"]["toscas"], tosca_new, application_dir, case)
            print("DONE exchange the infrastructures of each cluster")
            fdls = save_toscas_fdl(new_dir, production_new_dic["System"]["toscas"], case)
            config_dir = "%s/production/fdl" % (new_dir)
            config = {"oscar": {}}
            with open("%s/config.yaml" % (config_dir), 'w+') as f:
                    yaml.safe_dump(config, f, indent=2)
            # for components_tosca_old, values_tosca_old in production_old_dic["System"]["toscas"].items():
            #     oscar_cli(new_dir, fdls, components_tosca_old, case)
            oscar_cli(new_dir, fdls, case)
        elif components_same == 3  and machines_same == 1:
            # Case D
            print("We are in case D")

    elif len(production_old_dic["System"]["Components"]) < len(production_new_dic["System"]["Components"]):
        print( "increase the number of clusters")
        components_same = component_name_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])    
        machines_same = infrastructures_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])
        if components_same == 2 and machines_same == 2:
            #Case A
            print("We are at case A")
            case = "A"
            for components_tosca_old, values_tosca_old in production_old_dic["System"]["toscas"].items():
                for components_new, values_new in production_new_dic["System"]["Components"].items():
                    if values_tosca_old["infid"] == values_new["infid"]:
                        tosca_new = production_new_dic["System"]["toscas"][values_new["name"]]
                        correct_name = values_tosca_old["component_name"]
                        production_new_dic["System"]["toscas"][values_new["name"]] = mix_toscas(correct_name, production_old_dic["System"]["toscas"], tosca_new, application_dir, case)
            print("DONE place partitioning of one component on the same infrastructure")
            fdls = save_toscas_fdl(new_dir, production_new_dic["System"]["toscas"], case)
            # This part can be converted in a function
            config_dir = "%s/production/fdl" % (new_dir)
            config = {"oscar": {}}
            with open("%s/config.yaml" % (config_dir), 'w+') as f:
                    yaml.safe_dump(config, f, indent=2) 
            oscar_cli(new_dir, fdls, case)
        elif components_same == 2 and machines_same == 3:
            #Case B
            print("We are at case B")
    else:
        print( "decrease the number of clusters")
    
    #Save the the production
    with open("%s/production/production_old.yaml" % old_dir, 'w+') as f:
            yaml.safe_dump(production_old_dic, f, indent=2)
    with open("%s/production/production_new.yaml" % new_dir, 'w+') as f:
            yaml.safe_dump(production_new_dic, f, indent=2)

    

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--dir_to_save", help="Path to save the toscas requested", default=None)
def outputs(application_dir, dir_to_save):
    auth_path = "%s/%s" % (application_dir, im_auth_path_def)
    responses = im_get_infrastructures(auth_path)
    i = 1
    for response in responses:
        InfId = response.split("%s/infrastructures/" % im_url_def)[1]
        output = im_get_outputs(InfId, auth_path)
        with open("%s/%s.json" % (dir_to_save, InfId), 'w', encoding='utf-8') as f:
            json.dump(json.loads(output), f, ensure_ascii=False, indent=4)
        print("DONE. OUTPUT json file saved at %s/%s.json" % (dir_to_save, InfId))

        outputDict = json.loads(output)

        admin_token = outputDict["outputs"]["admin_token"]
        print("admin_token:", admin_token)

        console_minio_endpoint = outputDict["outputs"]["console_minio_endpoint"]
        print("console_minio_endpoint:", console_minio_endpoint)

        dashboard_endpoint = outputDict["outputs"]["dashboard_endpoint"]
        print("dashboard_endpoint:", dashboard_endpoint)

        fe_node_creds_user = outputDict["outputs"]["fe_node_creds"]["user"]
        print("fe_node_creds_user:", fe_node_creds_user)

        fe_node_creds_token_type = outputDict["outputs"]["fe_node_creds"]["token_type"]
        print("fe_node_creds_token_type:", fe_node_creds_token_type)

        fe_node_creds_token = outputDict["outputs"]["fe_node_creds"]["token"]
        print("fe_node_creds_token:\n", fe_node_creds_token)

        fe_node_ip = outputDict["outputs"]["fe_node_ip"]
        print("fe_node_ip:", fe_node_ip)

        minio_endpoint = outputDict["outputs"]["minio_endpoint"]
        print("minio_endpoint:", minio_endpoint)

        minio_password = outputDict["outputs"]["minio_password"]
        print("minio_password:", minio_password)

        oscar_password = outputDict["outputs"]["oscar_password"]
        print("oscar_password:", oscar_password)

        oscar_service_cred = outputDict["outputs"]["oscar_service_cred"]
        print("oscar_service_cred:", oscar_service_cred)

        oscar_service_url = outputDict["outputs"]["oscar_service_url"]
        print("oscar_service_url:", oscar_service_url)

        oscarui_endpoint = outputDict["outputs"]["oscarui_endpoint"]
        print("oscarui_endpoint:", oscarui_endpoint)





runtime_manager_cli.add_command(infras)
runtime_manager_cli.add_command(difference)
runtime_manager_cli.add_command(outputs)
if __name__ == '__main__':
    runtime_manager_cli()


