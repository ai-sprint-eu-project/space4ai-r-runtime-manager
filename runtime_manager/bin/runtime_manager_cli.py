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
# from deepdiff import DeepDiff
import json
import glob
import os
import shutil
from datetime import datetime

sys.path.append("../")
from im_interface import  *
from utils import *

def getInfras(application_dir, dir_to_save):
    auth_path = "%s/%s" % (application_dir, im_auth_path_def)
    responses = im_get_infrastructures(auth_path)
    i = 0
    components_deployed = {}
    infras_file = yaml_as_dict("%s/aisprint/deployments/base/im/infras.yaml" % (application_dir))
    infras_old = []
    for item, value in infras_file.items():
        inf_old = value[0].split("/")[-1:][0]
        infras_old.append(inf_old)
    for response in responses:
        InfId = response.split("%s/infrastructures/" % im_url_def)[1]
        if InfId in infras_old:
            print("The Infrastructure %s exist in the IM and in the 'infras.yaml'" % InfId)
            tosca = yaml.safe_load(im_get_tosca(InfId, auth_path))
            tosca["infid"] = InfId
            tosca["type"] = "Virtual"
            tosca = place_name(tosca)
            tosca_path = dir_to_save + "/" + tosca["component_name"] + ".yaml"
            with open(tosca_path, 'w+') as f:
                yaml.safe_dump(tosca, f, indent=2)
            print("DONE. TOSCA files %s.yaml has been saved for the InfId %s" % (tosca["component_name"], InfId))
            print("\n")
            success, state = im_get_state(response, auth_path)
            if success:
                components_deployed[tosca["component_name"]] = (response, state)
            else:
                components_deployed[tosca["component_name"]] = (response, "unknown")
            i += 1
        else:
            print("The Infrastructure %s exist in the IM, but NOT in the 'infras.yaml'" % InfId)
            print("\n")
    if i == len(infras_old):
        print("All the Infrastructures in 'infras.yaml' exists in the IM")
        im_infras = "%s/im/infras.yaml" % application_dir
        with open(im_infras, 'w+') as f:
                yaml.safe_dump(components_deployed, f, indent=2)
    else:
        print("The infras.yaml is not totally updated, take a look to the  'infras.yaml' and compare it with the infrastructures defined in the IM")

@click.group()
def runtime_manager_cli():
    pass
@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--dir_to_save", help="Path to save the toscas requested", default=None)
def infras(application_dir, dir_to_save):
    if None ==  dir_to_save:
        dir_to_save = application_dir + "/aisprint/deployments/base/im"
    getInfras(application_dir, dir_to_save)

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--old_dir", help="Path to read the old toscas", default=None)
@click.option("--new_dir", help="Path to read the new toscas", default=None)
@click.option("--update_infras", help="Enable the update of the infras at the start", default=False)
@click.option("--swap_deployments", help="Enable the swap of base and optimal deployments", default=False)
@click.option("--remove_bucket", is_flag = True,  help="Flag to remove buckets from minio")
def difference(application_dir, old_dir, new_dir, update_infras, remove_bucket, swap_deployments):
    if None == old_dir:
        old_dir = application_dir+"/aisprint/deployments/base/im"

    if None == new_dir:
        new_dir = application_dir+"/aisprint/deployments/optimal_deployment/im"

    if (True == update_infras):
        getInfras(old_dir+"/..", application_dir+"/tmp")

    # Processing production files
    production_old_dic = yaml_as_dict("%s/aisprint/deployments/base/production_deployment.yaml" % (application_dir))
    production_new_dic = yaml_as_dict("%s/aisprint/deployments/optimal_deployment/production_deployment.yaml" % (application_dir))

    # Temporary production dictionary for internal use.
    filedictionary = {}

    # Creation completed old/new-production dictionaries and relate them with their respective InfID
    # We append to the old/ne dictionaries the key "toscas" that includes the old/new components

    # Parse old toscas.
    # files = glob.glob("%s/*.yaml" % old_dir)
    files = list(set(glob.glob("%s/*.yaml" % old_dir)) - set(glob.glob("%s/infras.yaml" % old_dir)))
    production_old_dic["System"]["toscas"] = {}
    i = 0
    for one_file in files:
        tosca_old_dic = yaml_as_dict(one_file)
        if not("component_name") in tosca_old_dic.keys():
            input_ext = os.path.splitext(os.path.basename(one_file))[0]
            tosca_old_dic["component_name"] = input_ext
        if ("type") in tosca_old_dic.keys():
            if not("infid") in tosca_old_dic.keys():
                infraId = getInfraId(tosca_old_dic["component_name"], old_dir)
                tosca_old_dic["infid"] = infraId
        else:
            tosca_old_dic["type"] = "PhysicalAlreadyProvisioned"
            if not("infid") in tosca_old_dic.keys():
                tosca_old_dic["infid"] = "AlreadyProvisioned%s" % i
                i += 1

        print("============================================")
        print("Deployed component:      %s" % tosca_old_dic["component_name"])
        print("Deployed infrastructure: %s" % tosca_old_dic["infid"])
        print("Deployed cluster:        %s" % tosca_old_dic["topology_template"]["inputs"]["cluster_name"]["default"])
        print("Execution layer:         %s" % production_old_dic["System"]["Components"][tosca_old_dic["component_name"]]['executionLayer'] )
        print("Resources:               %s" % getSelectedResources(tosca_old_dic["component_name"], production_old_dic))
        print("============================================\n")
        production_old_dic["System"]["toscas"][tosca_old_dic["component_name"]] = tosca_old_dic
        #ADD a component that overwrite the component "component1" for "component_name(blurryfaces or mask-detector)"
        if tosca_old_dic["component_name"] in production_old_dic["System"]["Components"]:
            production_old_dic["System"]["Components"][tosca_old_dic["component_name"]]["infid"] = tosca_old_dic["infid"]
    
    # files = glob.glob("%s/*.yaml" % new_dir)
    files = list(set(glob.glob("%s/*.yaml" % new_dir)) - set(glob.glob("%s/infras.yaml" % new_dir)))
    production_new_dic["System"]["toscas"] = {}
    for one_file in files:
        name_component = one_file.split("/")[-1].split(".")[0]
        tosca_new_dic = yaml_as_dict(one_file)
        # tosca_new_dic = place_name(tosca_new_dic)
        tosca_new_dic["component_name"] = name_component
        # print(tosca_new_dic["component_name"])
        production_new_dic["System"]["toscas"][name_component] = tosca_new_dic
    
    config_dir = "%s/production/fdl" % (new_dir)
    config = {"oscar": {}}
    with open("%s/config.yaml" % (config_dir), 'w+') as f:
            yaml.safe_dump(config, f, indent=2)

    # Make a verification of the case
    # --------------------------------------------
    # Simplified Version
    # case = "D"
    # # component_name_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])    
    # # infrastructures_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])
    # production_new_dic["System"]["toscas"] = iteration_toscas(production_old_dic, production_new_dic, application_dir, case)
    # print("DONE exchange the infrastructures of each cluster")
    # fdls = save_toscas_fdl(new_dir, production_new_dic["System"]["toscas"], case)
    # oscar_cli(new_dir, fdls, case)
    # ------------------------------------------------
    # Check if the number of the components are the same
    if len(production_old_dic["System"]["Components"]) == len(production_new_dic["System"]["Components"]):
        print("the number of clusters are the same")
        components_same = component_name_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])    
        machines_same = infrastructures_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])
        if components_same == 1 and machines_same == 1:
            # Case C
            case = "C"
            print("We are in case C")
            print("Case: same machines and cluster, it is just to exchange the infrastructures between each component")
            production_new_dic["System"]["toscas"] = iteration_toscas(production_old_dic, production_new_dic, application_dir, case)
            print("DONE exchange the infrastructures of each cluster")
        elif components_same == 3  and machines_same == 1:
            # Case E
            print("We are in case E")
            case = "E"
            production_new_dic["System"]["toscas"] = iteration_toscas(production_old_dic, production_new_dic, application_dir, case)
            print("DONE place partitioning of one component on the same infrastructure")
    elif len(production_old_dic["System"]["Components"]) < len(production_new_dic["System"]["Components"]):
        print( "increase the number of clusters")
        components_same = component_name_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])    
        machines_same = infrastructures_verification(production_old_dic["System"]["Components"],production_new_dic["System"]["Components"])
        if components_same == 2 and machines_same == 2:
            #Case A
            print("We are at case A")
            case = "A"
            production_new_dic["System"]["toscas"] = iteration_toscas(production_old_dic, production_new_dic, application_dir, case)
            print("DONE place partitioning of one component on the same infrastructure")
        elif components_same == 2 and machines_same == 3:
            #Case B
            print("We are at case B")
            case = "B"

            ####################
            # UPDATE FDLs/TOSCAs
            ####################
            filedata = json.dumps(production_new_dic)
            filedictionary = json.loads(filedata)

            for component_new, values_new in production_new_dic["System"]["Components"].items():
                tosca_new = production_new_dic["System"]["toscas"][values_new["name"]]

                print("-----------------------")
                print("--> %s" % component_new)
                se = searchExecution(production_old_dic, production_new_dic, component_new)
                if (se):
                    tosca_old = production_old_dic["System"]["toscas"][se]
                    #print((" >Component new runs on SAME CLUSTER than OLD"))
                    nc = tosca_new["topology_template"]["inputs"]["cluster_name"]["default"]
                    oc = tosca_old["topology_template"]["inputs"]["cluster_name"]["default"]
                    print(" >NEW CLUSTER: %s " % (nc))
                    print(" >OLD CLUSTER: %s (%s)" % (oc, se))
                    # ACTION: EXCHANGE CLUSTER
                    filedata = filedata.replace(nc, oc)
                    filedictionary = json.loads(filedata)
                    
                    # ACTION: EXCHANGE PASSWORDS
                    at_old = production_old_dic["System"]["toscas"][se]["topology_template"]["inputs"]["admin_token"]["default"]
                    op_old = production_old_dic["System"]["toscas"][se]["topology_template"]["inputs"]["oscar_password"]["default"]
                    mp_old = production_old_dic["System"]["toscas"][se]["topology_template"]["inputs"]["minio_password"]["default"]

                    at_new = filedictionary["System"]["toscas"][component_new]["topology_template"]["inputs"]["admin_token"]["default"]
                    op_new = filedictionary["System"]["toscas"][component_new]["topology_template"]["inputs"]["oscar_password"]["default"]
                    mp_new = filedictionary["System"]["toscas"][component_new]["topology_template"]["inputs"]["minio_password"]["default"]

                    filedata = filedata.replace(at_new, at_old)
                    filedata = filedata.replace(op_new, op_old)
                    filedata = filedata.replace(mp_new, mp_old)
                    filedictionary = json.loads(filedata)

                else:
                    #print((" >Component new runs on DIFFERENT CLUSTER than OLD"))
                    print(" >NEW CLUSTER: %s" % (tosca_new["topology_template"]["inputs"]["cluster_name"]["default"]))

                # ACTION: REPLACE SCRIPTs
                old_script = filedictionary["System"]["toscas"][component_new]["topology_template"]["node_templates"]["oscar_service_"+component_new]["properties"]["script"]
                new_script = application_dir+"/aisprint/designs/"+ component_new + "/base/script.sh"
                filedata = filedata.replace(old_script, new_script)
                filedictionary = json.loads(filedata)

                print(" >SCRIPT: %s" % (filedictionary["System"]["toscas"][component_new]["topology_template"]["node_templates"]["oscar_service_"+component_new]["properties"]["script"]))

                print("-----------------------")
                print("\n")

                production_new_dic = filedictionary

        elif components_same == 3 and machines_same == 2:
            #Case D
            print("We are at case D")
            case = "D"
            production_new_dic["System"]["toscas"] = iteration_toscas(production_old_dic, production_new_dic, application_dir, case)
            print("DONE place partitioning of one component on the same infrastructure")
    else:
        print( "decrease the number of clusters")

    ##################
    # SAVE FDLs/TOSCAs
    ##################
    print("=====> SAVING FDLs/TOSCAs <=====")
    fdls = save_toscas_fdl(new_dir, production_new_dic["System"]["toscas"], case)
    print("\n")

    ###################
    # REMOVE COMPONENTS
    ###################
    print("=====> REMOVE DELETED COMPONENTS <=====")
    cleanDeletedComponent(production_new_dic, production_old_dic)
    print("\n")

    ###################
    # CLEAN COMPONENTS
    ###################
    print("=====> CLEAN COMPONENTS <=====")
    # We do clean up starting from root component (entry point)
    rootComponent = searchNextComponent(production_new_dic, "")
    while("" != rootComponent):
        cleanComponentDeployment(production_new_dic, rootComponent, production_old_dic)
        rootComponent = searchNextComponent(production_new_dic, rootComponent)
    print("\n")

    ###################
    # UPDATE DEPLOYMENTS
    ###################
    print("=====> UPDATE DEPLOYMENTS <=====")
    # We do update components starting from leaf component (exit point).
    # TODO: CREATE DUMMY CLUSTER (Infrastructure) with no buckets and no services
    #       In this case we do not care about creation order.
    #       TO BE CHECKED!
    leafComponent = searchPreviousComponent(production_new_dic, "")
    while("" != leafComponent):
        updateComponentDeployment(production_new_dic, leafComponent, production_old_dic, new_dir, old_dir, case)
        leafComponent = searchPreviousComponent(production_new_dic, leafComponent)
    print("\n")

    ###################
    # APPLY FDLs/TOSCAs
    ###################
    print("=====> UPDATE COMPONENTS <=====")
    oscar_cli(new_dir, fdls, case, remove_bucket)
    print("\n")
    
    ###################
    # SAVE PRODUCTION FILES
    ###################
    if not os.path.isdir("%s/production/" % old_dir):
        os.makedirs("%s/production/" % old_dir)
    if not os.path.isdir("%s/production/" % new_dir):
        os.makedirs("%s/production/" % new_dir)
    with open("%s/production/production_old.yaml" % old_dir, 'w+') as f:
            yaml.safe_dump(production_old_dic, f, indent=2)
    with open("%s/production/production_new.yaml" % new_dir, 'w+') as f:
            yaml.safe_dump(production_new_dic, f, indent=2)

   ###################
    # SWAP BASE and PROD
    ###################
    if (True == swap_deployments):
        if not os.path.isdir("%s/bck/" % application_dir):
            os.makedirs("%s/bck/" % application_dir)

        f_path = "%s/aisprint/deployments/base" % application_dir

        now = datetime.now()

        sn = now.strftime("%Y-%m-%d-%H-%M-%S-%f")

        os.rename(f_path, f_path + '_' + sn)

        src_path = "%s/aisprint/deployments/optimal_deployment" % application_dir
        dst_path = "%s/aisprint/deployments/base" % application_dir
        shutil.copytree(src_path, dst_path)


@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--dir_to_save", help="Path to save the toscas requested", default=None)
def outputs(application_dir, dir_to_save):
    auth_path = "%s/%s" % (application_dir, im_auth_path_def)
    responses = im_get_infrastructures(auth_path)
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


@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--tosca_dir", help="Path to installed toscarizer", default=None)
def tosca(application_dir, tosca_dir):
    current_path = os.path.abspath(os.getcwd())
    #os.chdir('%s' % tosca_dir)
    #command = "pip install ."
    #stream = os.popen(command) 
    #output = stream.read()
    # print(output)
    if (tosca_dir):
        print("Custom Toscarizer")
        os.chdir('%s/toscarizer/bin' % tosca_dir)
        tosca = "python3 toscarizer_cli.py"
        startDir = application_dir.split("/")
        if startDir[0] == "." or startDir[0] == "..":
            app_dir = current_path + "/" + application_dir
        else:
            app_dir = application_dir
    else:
        print("Default Toscarizer")
        tosca = "toscarizer"
        app_dir = application_dir
    stream = os.popen(tosca) 
    output = stream.read()
    print(output)
    if "Commands" in output:
        print("Toscarizer is installed")
        command = "%s tosca --optimal --application_dir %s" % (tosca, app_dir)
        print("Toscarizer command: %s" % command)
        stream = os.popen(command)
        output = stream.read()
        print(output)
        if "DONE. TOSCA file" in output:
            print("NEW TOSCAS: have been generated and placed in the 'optimal_deploymets/im' folder")
            os.chdir(current_path)
        else:
            print("NEW TOSCAS: There has been a problem to generated the new toscas")
    else:
        print("Toscarizer is not installed")
    

runtime_manager_cli.add_command(infras)
runtime_manager_cli.add_command(difference)
runtime_manager_cli.add_command(outputs)
runtime_manager_cli.add_command(tosca)
if __name__ == '__main__':
    runtime_manager_cli()


