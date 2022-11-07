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
    i = 0
    infras = {}
    for one_file in files:
        tosca_old_dic = yaml_as_dict(one_file)
        production_old_dic["System"]["toscas"][tosca_old_dic["component_name"]] = tosca_old_dic
        infras[i] = {}
        if tosca_old_dic["component_name"] in production_old_dic["System"]["Components"]:
            production_old_dic["System"]["Components"][tosca_old_dic["component_name"]]["infid"] = tosca_old_dic["infid"]
    files = glob.glob("%s/*.yaml" % new_dir)
    production_new_dic["System"]["toscas"] = {}
    for one_file in files:
        tosca_new_dic = yaml_as_dict(one_file)
        tosca_new_dic = place_name(tosca_new_dic)
        production_new_dic["System"]["toscas"][tosca_new_dic["component_name"]] = tosca_new_dic
    
    
    # Make a verification of the case--------------------------------------
    if len(production_old_dic["System"]["Components"]) == len(production_new_dic["System"]["Components"]):
        print("the number of clusters are the same")
        components_same = component_name_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])    
        machines_same = infrastructures_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])
        if components_same == True and machines_same == True:
            print("Case: same machines and cluster, it is just to exchange the infrastructures between each component")
            for components_tosca_old, values_tosca_old in production_old_dic["System"]["toscas"].items():
                for components_new, values_new in production_new_dic["System"]["Components"].items():
                    if values_tosca_old["infid"] == values_new["infid"]:
                        tosca_new = production_new_dic["System"]["toscas"][values_new["name"]]
                        tosca_old = values_tosca_old
                        correct_name = values_tosca_old["component_name"]
                        production_new_dic["System"]["toscas"][values_new["name"]] = mix_toscas(correct_name, production_old_dic["System"]["toscas"], tosca_new)
        print("DONE exchange the infrastructures of each cluster")
        safe_toscas_fdl(new_dir, production_new_dic["System"]["toscas"])

    elif len(production_old_dic["System"]["Components"]) < len(production_new_dic["System"]["Components"]):
        print( "increase the number of clusters")
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





runtime_manager_cli.add_command(infras)
runtime_manager_cli.add_command(difference)
runtime_manager_cli.add_command(outputs)
if __name__ == '__main__':
    runtime_manager_cli()


