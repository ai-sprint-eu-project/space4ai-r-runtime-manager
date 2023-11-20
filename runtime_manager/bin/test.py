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
sys.path.append("./")
sys.path.append("../")
from im_interface import  *
from utils import *

import subprocess

from config import update_app_dir
import config as cfg

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

@click.group()
def runtime_manager_cli():
    pass


@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
@click.option("--dir_to_save", help="Path to save the toscas requested", default=None)
def outputs(application_dir, dir_to_save):
    update_app_dir(application_dir)
    responses = im_get_infrastructures(cfg.im_auth_path_def)
    for response in responses:
        InfId = response.split("%s/infrastructures/" % cfg.im_url_def)[1]
        output = im_get_outputs(InfId, cfg.im_auth_path_def)
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
@click.option("--domain", help="Domain that will be used for the deployment", default=None)
@click.option("--influxdb_token", help="Influxdb token", default=None)
def tosca(application_dir, tosca_dir, domain, influxdb_token):
    update_app_dir(application_dir)
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
    option_domain = ""
    if None != domain:
        option_domain = "--domain %s" % domain

    option_influx = ""
    if None != influxdb_token:
        option_influx = "--influxdb_token %s" % domain  

    if "Commands" in output:
        print("Toscarizer is installed")
        
        command = "%s tosca --optimal --application_dir %s %s %s" % (tosca, app_dir, option_domain, option_influx)
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

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
def stopallbut1(application_dir):
    update_app_dir(application_dir)

    infras_file = yaml_as_dict("%s/aisprint/deployments/%s/im/infras.yaml" % (application_dir, cfg.current_folder))
    #print(infras_file)
    components_vms = {}
    vm_status = {}
    for item, value in infras_file.items():
        output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
        #print("%s FE ip: %s" % (item, yaml.safe_load(output)['outputs']['oscar_service_cred']))
        if yaml.safe_load(output)['outputs']['oscar_service_cred'] is not None:
            print("%s VMS:" % item)
            #print(value)
            #print(value[0])
            a=im_get_vms(value[0], cfg.im_auth_path_def)
            if(a[0]):
                s=a[1].split("\n")
                for vm in s:
                    print(vm)
                    vm_id=int(vm.split("/")[-1:][0])
                    if vm_id>1:
                        print("Stopping %d" % vm_id)
                        # b=im_put_vm(vm, cfg.im_auth_path_def, "stop")
                        # print(b)
                        # vm_status[vm_id] = "stopping"
                components_vms[item] = (value[0], vm_status)
            else:
                print("-")
        else:
            print("%s is Physical already deployed; no VM action required!" % item)

    # for cmp in components_vms:
    #     print(components_vms[cmp][0])
    #     for vm_id, status in components_vms[cmp][1].items():
    #         print("%s: %s -> %s" % (cmp, vm_id, status))

    # end = False
    # cont = 0
    # max_time=(60*60)
    # delay=30
    # while not end and cont < max_time:
    #     for cmp in components_vms:
    #         #print(components_vms[cmp])
    #         for vm_id, status in components_vms[cmp][1].items():
    #             #print("%s: %s -> %s" % (cmp, vm_id, status))
    #             # Update deployment state
    #             print("Updating Vm state... (%s - %s)" % (cmp, vm_id))
    #             success, state=im_get_vm(components_vms[cmp][0]+"/vms/"+str(vm_id), cfg.im_auth_path_def, "state")
    #             if success:
    #                 print("%s -- vm_id: %s - state: %s" % (cmp, vm_id, state))
    #                 components_vms[cmp][1][vm_id] = state
    #             else:
    #                 print("Cannot update vm state!!!")
    #     for cmp in components_vms:
    #         print(components_vms[cmp])
    #         for vm_id, status in components_vms[cmp][1].items():
    #             if status in ['pending', 'configured', 'stopping']:
    #                 end = False
    #                 break
    #             elif status in ['stopped']:
    #                 end = True
    #         else:
    #             continue
    #         break

    #     if not end:
    #         time.sleep(delay)
    #         cont += delay
    
    # print("vms updated. Elapsed: %d" % (cont))
    # for cmp in components_vms:
    #     print(components_vms[cmp][0])
    #     for vm_id, status in components_vms[cmp][1].items():
    #         print("%s: %s -> %s" % (cmp, vm_id, status))

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
def startall(application_dir):
    update_app_dir(application_dir)

    infras_file = yaml_as_dict("%s/aisprint/deployments/%s/im/infras.yaml" % (application_dir, cfg.current_folder))
    #print(infras_file)
    components_vms = {}
    vm_status = {}
    for item, value in infras_file.items():
        output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
        #print("%s FE ip: %s" % (item, yaml.safe_load(output)['outputs']['oscar_service_cred']))
        if yaml.safe_load(output)['outputs']['oscar_service_cred'] is not None:
            print("%s VMS:" % item)
            #print(value)
            #print(value[0])
            a=im_get_vms(value[0], cfg.im_auth_path_def)
            if(a[0]):
                s=a[1].split("\n")
                for vm in s:
                    print(vm)
                    vm_id=int(vm.split("/")[-1:][0])
                    if vm_id>1:
                        print("Starting %d" % vm_id)
                        # b=im_put_vm(vm, cfg.im_auth_path_def, "start")
                        # print(b)
                        vm_status[vm_id] = "starting"
                components_vms[item] = (value[0], vm_status)
            else:
                print("-")
        else:
            print("%s is Physical already deployed; no VM action required!" % item)
    

    # for cmp in components_vms:
    #     print(components_vms[cmp][0])
    #     for vm_id, status in components_vms[cmp][1].items():
    #         print("%s: %s -> %s" % (cmp, vm_id, status))

    # end = False
    # cont = 0
    # max_time=(60*60)
    # delay=30
    # while not end and cont < max_time:
    #     for cmp in components_vms:
    #         #print(components_vms[cmp])
    #         for vm_id, status in components_vms[cmp][1].items():
    #             #print("%s: %s -> %s" % (cmp, vm_id, status))
    #             # Update deployment state
    #             print("Updating Vm state... (%s - %s)" % (cmp, vm_id))
    #             success, state=im_get_vm(components_vms[cmp][0]+"/vms/"+str(vm_id), cfg.im_auth_path_def, "state")
    #             if success:
    #                 print("%s -- vm_id: %s - state: %s" % (cmp, vm_id, state))
    #                 components_vms[cmp][1][vm_id] = state
    #             else:
    #                 print("Cannot update vm state!!!")
    #     for cmp in components_vms:
    #         print(components_vms[cmp])
    #         for vm_id, status in components_vms[cmp][1].items():
    #             if status in ['pending', 'starting']:
    #                 end = False
    #                 break
    #             elif status in ['configured']:
    #                 end = True
    #         else:
    #             continue
    #         break

    #     if not end:
    #         time.sleep(delay)
    #         cont += delay
    
    # print("vms updated. Elapsed: %d" % (cont))
    # for cmp in components_vms:
    #     print(components_vms[cmp][0])
    #     for vm_id, status in components_vms[cmp][1].items():
    #         print("%s: %s -> %s" % (cmp, vm_id, status))

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
def test(application_dir):
    update_app_dir(application_dir)
    infras_file = yaml_as_dict("%s/aisprint/deployments/%s/im/infras.yaml" % (application_dir, cfg.current_folder))
    print("Infra content:")
    print(yaml.safe_dump(infras_file, indent=2))

    if os.path.exists(application_dir + "/aisprint/deployments/"  + cfg.current_folder):
        print("The Current Deployment folder does exist")
    else:
        print("The Current Deployment folder does not exist, let's proceed with its creation")
        try:
            shutil.copytree(application_dir + "/aisprint/deployments/base", application_dir + "/aisprint/deployments/" + cfg.current_folder)
        except:
            print("The files at '" + application_dir +"/aisprint/deployments/base/src ' could not be copied")
        # shutil.copytree(application_dir + "/aisprint/deployments/base", application_dir + "/aisprint/deployments/" + cfg.current_folder)
    

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
    rootComponent = searchNextComponent(pd, "")
    print("Root component: %s\n" % rootComponent)
    with open("x.yaml", 'w+') as f:
            yaml.safe_dump(pd, f, indent=2)

    for item, value in infras_file.items():
        #print(item)
        #print(value[0])
        if(item == rootComponent):
            output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
            print("%s FE ip: %s" % (item, yaml.safe_load(output)['outputs']['fe_node_ip']))
            #print(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
            with open("key_fe.pem", 'w') as f:
                f.write(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
            f.close()
            run_cmd = subprocess.run(["chmod", "600", "key_fe.pem"])
            
            run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "sudo", "kubectl", "get", "service", "ai-sprint-monit-api", "-n", "ai-sprint-monitoring"], capture_output=True, text=True)
            #print("The exit code was: %d" % run_cmd.returncode)
            out_2 = run_cmd.stdout.splitlines(True)[1].split(" ")
            while("" in out_2):
                out_2.remove("")
            print("%s AMS IP: %s" % (item, out_2[2]))
            run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "curl", "http://"+out_2[2]+"/monitoring/throughput/"], capture_output=True, text=True)
            #print("The exit code was: %d" % run_cmd.returncode)
            out_3 = run_cmd.stdout
            print("The throughput is: %s" % yaml.safe_load(out_3)['throughput'])
            print("\n%s" % out_3)

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
def test2(application_dir):
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

    rootComponent = searchNextComponent(pd, "")
    while("" != rootComponent):
        el = pd["System"]["Components"][rootComponent]['executionLayer']
        rt = getResourcesType(rootComponent, pd)
        print("Root component: %s" % rootComponent)
        print("ExecutionLayer: %s" % el)
        print("Resourcetype: %s" % rt)

        for one_file in qos_files:
            # print("--- %s" %one_file)
            if "qos_constraints.yaml" in one_file:
                print("Global constraints: %s" % one_file)
            if "qos_constraints_L" + str(el) + ".yaml" in one_file:
                print("Level constraints: %s" % one_file)

        for item, value in infras_file.items():
            #print(item)
            #print(value[0])
            if(item == rootComponent):
                output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
                # print("%s OUTPUTS: %s" % (item, yaml.safe_load(output)['outputs']))
                print("%s FE ip: %s" % (item, yaml.safe_load(output)['outputs']['fe_node_ip']))
                print(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
                # with open("key_fe.pem", 'w') as f:
                #     f.write(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
                # f.close()
                # run_cmd = subprocess.run(["chmod", "600", "key_fe.pem"])
                
                # run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "sudo", "kubectl", "get", "service", "ai-sprint-monit-api", "-n", "ai-sprint-monitoring"], capture_output=True, text=True)
                # #print("The exit code was: %d" % run_cmd.returncode)
                # out_2 = run_cmd.stdout.splitlines(True)[1].split(" ")
                # while("" in out_2):
                #     out_2.remove("")
                # print("%s AMS IP: %s" % (item, out_2[2]))
                # run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "curl", "http://"+out_2[2]+"/monitoring/throughput/"], capture_output=True, text=True)
                # #print("The exit code was: %d" % run_cmd.returncode)
                # out_3 = run_cmd.stdout
                # print("The throughput is: %s" % yaml.safe_load(out_3)['throughput'])
                # print("\n%s" % out_3)


        rootComponent = searchNextComponent(pd, rootComponent)
        print("\n")



    # with open("x.yaml", 'w+') as f:
    #         yaml.safe_dump(pd, f, indent=2)

    # for item, value in infras_file.items():
    #     print(item)
    #     print(value[0])
    #     if(item == rootComponent):
    #         output = im_get_outputs_from_url(value[0], cfg.im_auth_path_def)
    #         print("%s FE ip: %s" % (item, yaml.safe_load(output)['outputs']['fe_node_ip']))
    #         print(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
    #         with open("key_fe.pem", 'w') as f:
    #             f.write(yaml.safe_load(output)['outputs']['fe_node_creds']['token'])
    #         f.close()
    #         run_cmd = subprocess.run(["chmod", "600", "key_fe.pem"])
            
    #         run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "sudo", "kubectl", "get", "service", "ai-sprint-monit-api", "-n", "ai-sprint-monitoring"], capture_output=True, text=True)
    #         #print("The exit code was: %d" % run_cmd.returncode)
    #         out_2 = run_cmd.stdout.splitlines(True)[1].split(" ")
    #         while("" in out_2):
    #             out_2.remove("")
    #         print("%s AMS IP: %s" % (item, out_2[2]))
    #         run_cmd = subprocess.run(["ssh", "-oStrictHostKeyChecking=no", "-i", "key_fe.pem", "cloudadm@"+yaml.safe_load(output)['outputs']['fe_node_ip'], "curl", "http://"+out_2[2]+"/monitoring/throughput/"], capture_output=True, text=True)
    #         #print("The exit code was: %d" % run_cmd.returncode)
    #         out_3 = run_cmd.stdout
    #         print("The throughput is: %s" % yaml.safe_load(out_3)['throughput'])
    #         print("\n%s" % out_3)

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True, default=None)
def test3(application_dir):
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

runtime_manager_cli.add_command(infras)
runtime_manager_cli.add_command(difference)
runtime_manager_cli.add_command(outputs)
runtime_manager_cli.add_command(tosca)
runtime_manager_cli.add_command(stopallbut1)
runtime_manager_cli.add_command(startall)
runtime_manager_cli.add_command(test)
runtime_manager_cli.add_command(test2)
runtime_manager_cli.add_command(test3)

# main entry point.
if __name__ == '__main__':
    runtime_manager_cli()


