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

sys.path.append("../")
from im_interface import  *
from utils import im_auth_path_def, im_url_def, place_name, yaml_as_dict, dic_creation

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
        tosca_path = dir_to_save + "/" + tosca["component_name"] + "-" + str(i) + ".yaml"
        with open(tosca_path, 'w+') as f:
            yaml.safe_dump(tosca, f, indent=2)
        print("DONE. TOSCA files %s has been saved for the InfId %s" % (tosca["component_name"] + "-" + str(i) + ".yaml", InfId))
        i += 1

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--old_dir", help="Path to read the old toscas", default=None)
@click.option("--new_dir", help="Path to read the new toscas", default=None)
def difference(application_dir, old_dir, new_dir):   
    dic_old = {}
    dic_new = {}
    production_old_dic = yaml_as_dict("%s/aisprint/deployments/base/production_deployment.yaml" % (application_dir))
    production_new_dic = yaml_as_dict("%s/aisprint/deployments/optimal_deployment/production_deployment.yaml" % (application_dir))
    dic_old = dic_creation(production_old_dic)
    dic_new = dic_creation(production_new_dic)
    ddiff = DeepDiff(dic_old, dic_new, ignore_order=True)
    #assuing that the files are correctlly configured

    if "dictionary_items_added" in ddiff:
        print("new cluster addes")
    elif "dictionary_item_removed" in ddiff:
        print("cluster deleted")
    elif "values_changed" in ddiff: 
        print("a valued has been changed")
        for item, values in ddiff["values_changed"].items():
            print(item)
            print(values)
    else:
        print("nothing has been changed")
    
    # print(ddiff)
    # for items_old, values_old in dic_old.items():
    #     for items_new, values_new in dic_new.items():
    #         print(values_old)
    #         print(values_new)
    # 


    # # corregir
    # dic_old["executionLayer"] = production_old_dic["System"]["Components"]["component1"]["executionLayer"]
    # dic_old["executionLayer"] = production_old_dic['System']['NetworkDomains']['ND1']['ComputationalLayers']['computationalLayer1']['Resources']['resource1']['totalNodes']
    
    # ddiff = DeepDiff(production_old_dic, production_new_dic, ignore_order=True)
    # changes = ddiff["values_changed"].items()
    # print(changes)
    # print(ddiff["values_changed"][0])

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


