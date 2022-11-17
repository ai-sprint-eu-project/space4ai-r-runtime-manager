import os
import yaml
import glob
import copy

im_auth_path_def = "/im/auth.dat"
im_url_def = "https://appsgrycap.i3m.upv.es:31443/im"
# tosca_file_dir = "tosca_files"
def read_auth(im_auth_path):
    # if not im_auth and application_dir:
    #     im_auth = "%s/im/auth.dat" % application_dir
    if not os.path.isfile(str(im_auth_path)):
        print("IM auth data does not exit." % im_auth_path)
        sys.exit(-1)
    with open(im_auth_path, 'r') as f:
        auth_data = f.read().replace("\n", "\\n") 
    return auth_data

def place_name(tosca):
    oscar_service = tosca["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
    tosca["component_name"] = tosca["topology_template"]["node_templates"][oscar_service]["properties"]["env_variables"]["COMPONENT_NAME"]
    return tosca



def yaml_as_dict(my_file):
    my_dict = {}
    with open(my_file, 'r') as fp:
        docs = yaml.safe_load_all(fp)
        for doc in docs:
            for key, value in doc.items():
                my_dict[key] = value
    return my_dict

def dic_creation(dic):
    dic_new = {}
    i = 0
    for item, values in dic["System"]["Components"].items():
        dic_new[values["name"]] =  { 
        # dic_new[item] =  { 

            # "component_name": values["name"],
            "exec_layer": values["executionLayer"],
            "resource": values["Containers"]["container1"]["selectedExecutionResources"]
        }
        i += 1
    return dic_new

def mix_toscas(correct_name, toscas_old, tosca_new, application_dir, case):
    if case == "C":
        tosca_new["topology_template"]["inputs"] = toscas_old[correct_name]["topology_template"]["inputs"]
        oscar_service_old = toscas_old[correct_name]["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
        oscar_service_new = tosca_new["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
        tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["env_variables"]["KCI"] = toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["env_variables"]["KCI"]
        if len(tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["output"]) > len(toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["output"]):
            i  = 0
            cluster_name = toscas_old[tosca_new["component_name"]]["topology_template"]["inputs"]["cluster_name"]["default"]
            tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["output"] = toscas_old[tosca_new["component_name"]]["topology_template"]["node_templates"][oscar_service_new]["properties"]["output"]
            for output in tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["output"]:
                if output["storage_provider"] != "minio":
                    tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["output"][i]["storage_provider"] = "minio.%s" % (cluster_name)
                i += 1
            tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["storage_providers"].pop("minio", None)
            tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["storage_providers"]["minio"] = {
                cluster_name:{
                    "access_key": "minio",
                    "endpoint": "https://minio.%s.%s" % (cluster_name, tosca_new["topology_template"]["inputs"]["domain_name"]["default"]),
                    "region": "us-east-1",
                    "secret_key": toscas_old[tosca_new["component_name"]]["topology_template"]["inputs"]["minio_password"]["default"],   
                }
            }
        tosca_new["topology_template"]["node_templates"][oscar_service_new]["properties"]["script"] = "%s/aisprint/designs/%s/base/script.sh" % (application_dir, tosca_new["component_name"])
    elif case == "A":
        tosca_new["topology_template"]["inputs"] = copy.deepcopy(toscas_old[correct_name]["topology_template"]["inputs"])
        oscar_service_old = toscas_old[correct_name]["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
        oscar_service_new = tosca_new["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
        for item, values in tosca_new["topology_template"]["node_templates"].items():
            if "oscar_service_" in item:
                tosca_new["topology_template"]["node_templates"][item]["properties"]["env_variables"]["KCI"] = toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["env_variables"]["KCI"]
                if len(tosca_new["topology_template"]["node_templates"][item]["properties"]["output"]) > 1:
                    cluster_name = toscas_old[correct_name]["topology_template"]["inputs"]["cluster_name"]["default"]
                    for output_new in tosca_new["topology_template"]["node_templates"][item]["properties"]["output"]:
                        for output_old in toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["output"]:
                            if output_new["storage_provider"] != "minio" and output_old["storage_provider"] != "minio" :
                                output_new["storage_provider"] = output_old["storage_provider"]
                                tosca_new["topology_template"]["node_templates"][item]["properties"]["storage_providers"] = copy.deepcopy(toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["storage_providers"])
                tosca_new["topology_template"]["node_templates"][item]["properties"]["script"] = "%s/aisprint/designs/%s/base/script.sh" % (application_dir, tosca_new["topology_template"]["node_templates"][item]["properties"]["name"])
    return tosca_new

    
# def mix_toscas_A(correct_name, toscas_old, tosca_new, application_dir):
#     tosca_new["topology_template"]["inputs"] = copy.deepcopy(toscas_old[correct_name]["topology_template"]["inputs"])
#     oscar_service_old = toscas_old[correct_name]["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
#     oscar_service_new = tosca_new["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
#     for item, values in tosca_new["topology_template"]["node_templates"].items():
#         if "oscar_service_" in item:
#             tosca_new["topology_template"]["node_templates"][item]["properties"]["env_variables"]["KCI"] = toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["env_variables"]["KCI"]
#             if len(tosca_new["topology_template"]["node_templates"][item]["properties"]["output"]) > 1:
#                 cluster_name = toscas_old[correct_name]["topology_template"]["inputs"]["cluster_name"]["default"]
#                 for output_new in tosca_new["topology_template"]["node_templates"][item]["properties"]["output"]:
#                     for output_old in toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["output"]:
#                         if output_new["storage_provider"] != "minio" and output_old["storage_provider"] != "minio" :
#                             output_new["storage_provider"] = output_old["storage_provider"]
#                             tosca_new["topology_template"]["node_templates"][item]["properties"]["storage_providers"] = copy.deepcopy(toscas_old[correct_name]["topology_template"]["node_templates"][oscar_service_old]["properties"]["storage_providers"])
#             tosca_new["topology_template"]["node_templates"][item]["properties"]["script"] = "%s/aisprint/designs/%s/base/script.sh" % (application_dir, tosca_new["topology_template"]["node_templates"][item]["properties"]["name"])
#     return tosca_new




def component_name_verification(dic_old, dic_new):
    count_components = 0
    for component_new, value_new in dic_new.items():
        if component_new in dic_old:
            if dic_new[component_new]["name"] == dic_old[component_new]["name"]:
                count_components += 1
            else:
                print("The component name on '%s' on the new production does not match with the component name on old production" %(component_new))
                # break
        else:
            print("The component '%s' in new production does not exist in old production, check the component assignation" % (component_new))
            # break
    if count_components == len(dic_old):
        # It is part of case C
        components_same = 1
        print("All Components have the same name")
    elif count_components >= 1:
        # It is part of case A
        components_same = 2
        print("At least one Component is the same name")
    elif count_components == 0:
        components_same = 3
        print("All the components are different")
    else:
        components_same = False
        print("Not all the components have the same name")
    return components_same

def infrastructures_verification(dic_old, dic_new):
    count_machines = 0
    for component_new, values_new in dic_new.items():
        for component_old, values_old in dic_old.items():
            if values_new["executionLayer"] == values_old["executionLayer"]  and values_new["Containers"]["container1"]["selectedExecutionResources"] == values_old["Containers"]["container1"]["selectedExecutionResources"]:
                count_machines += 1
                values_new["infid"] = values_old["infid"]
    if count_machines == len(dic_old):
        # It is part of case C
        if count_machines == len(dic_new):
            machines_same = 1
            print("All the infrastructures are the same")
        elif count_machines < len(dic_new):
            machines_same = 3
            print("There are '%s' number of new infrastructures" % (len(dic_new)-count_machines))
    elif count_machines == len(dic_new):
        # It is part of case A
        machines_same = 2
        print("All the infrastructures in production_new are defined in pproduction_old")
    elif count_machines == 0:
        machines_same = 0
        print("All the infrastructures are different")
    else:
        machines_same = 0
        print("The infrastructures are not the same the same")
    return machines_same


def get_oscar_service_json(properties):
    """Get the OSCAR service json"""
    res = {}
    for prop, value in properties.items():
        if value not in [None, [], {}]:
            if prop in ['name', 'script', 'alpine', 'input', 'output', 'storage_providers', 'image', 'memory']:
                res[prop] = value
            elif prop== 'cpu':
                res['cpu'] = "%g" % value
            elif prop == 'env_variables':
                res['environment'] = {'Variables': value}
            elif prop == 'image_pull_secrets':
                if not isinstance(value, list):
                    value = [value]
                res['image_pull_secrets'] = value
    return res



def generate_fdl(tosca):
    fdl = {"functions": {"oscar": []}}
    done = []
    # for name, tosca in toscas.items():
    oscar_name = None
    if "inputs" in tosca["topology_template"]:
        inputs = tosca["topology_template"]["inputs"]
    # Name in already deployed cluster
    if "oscar_name" in tosca["topology_template"]["inputs"]:
        oscar_name = tosca["topology_template"]["inputs"]["oscar_name"]["default"]
    # Name in IM generated cluster
    elif "cluster_name" in tosca["topology_template"]["inputs"]:
        oscar_name = tosca["topology_template"]["inputs"]["cluster_name"]["default"]
    for node_name, node in tosca["topology_template"]["node_templates"].items():
        if node["type"] == "tosca.nodes.aisprint.FaaS.Function":
            service = get_oscar_service_json(node["properties"])
            if "storage_providers" in service:
                fdl["storage_providers"] = copy.deepcopy(service["storage_providers"])
                service.pop("storage_providers", None)
            service["inputs"] = inputs
            if service["name"] not in done:
                cluster_name = oscar_name if oscar_name else node_name
                fdl["functions"]["oscar"].append({cluster_name: service})
                done.append(service["name"])
    return fdl


def save_toscas_fdl(new_dir, toscas, case):
    fdls = []
    for name, tosca in toscas.items():
        fdl = generate_fdl(tosca)
        tosca.pop("component_name", None)
        identifier = list(fdl["functions"]["oscar"][0].keys())[0]
        for service in fdl["functions"]["oscar"]:
            service[identifier].pop("inputs", None)
        fdls.append(generate_fdl(tosca)["functions"]["oscar"][0])
        with open("%s/production/ready-case%s/%s-ready.yaml" % (new_dir, case, name), 'w+') as f:
            yaml.safe_dump(tosca, f, indent=2)
        with open("%s/production/fdl/fdl-%s.yaml" % (new_dir, name), 'w+') as f:
            yaml.safe_dump(fdl, f, indent=2)
    with open("%s/production/fdl/fdl-new.yaml" % (new_dir), 'w+') as f:
        yaml.safe_dump(fdls, f, indent=2)
    print("DONE new TOSCA and FDL saved")
    return fdls


def oscar_cli(new_dir, fdls, component,case):
    oscar_cli = "~/go/bin/oscar-cli"
    new_dir = "%s/production/fdl" % (new_dir)
    config_dir = "%s/config.yaml" % (new_dir)
    stream = os.popen(oscar_cli)
    output = stream.read()
    if "/bin/sh" not in stream.read():
        # FOR NOW IT IS FOR ONLY ONE SERVICE
        for fdl in fdls:
            identifier = list(fdl.keys())[0]
            print(identifier)
            value = list(fdl.values())[0]
            if case == "C":
                if component != value["environment"]["Variables"]["COMPONENT_NAME"]:
                    component_name = value["environment"]["Variables"]["COMPONENT_NAME"]
                    endpoint = "https://%s.%s" % (identifier,  value["inputs"]["domain_name"]["default"])
                    password = value["inputs"]["oscar_password"]["default"]
                    # example oscar-cli  cluster add oscar-cluster-f5vr5dfn https://oscar-cluster-f5vr5dfn.aisprint-cefriel.link oscar 05gwt0zjc88m4udt 
                    command = "%s cluster add  %s %s oscar %s --config %s" % (oscar_cli, identifier, endpoint, password, config_dir)
                    print("CLUSTER ADD " + command)
                    stream = os.popen(command) 
                    output = stream.read()
                    print(output)
                    if "successfully stored" in output:                            
                        command = "%s service list  -c %s --config %s " % (oscar_cli, identifier, config_dir)
                        print("SERVICE LIST: " + command)
                        stream = os.popen(command)
                        output = stream.read()
                        print(output)
                        if "There are no services in the cluster" not in output:
                            command = "%s service remove %s -c %s --config %s" % (oscar_cli, component, identifier, config_dir)
                            print("SERVICE REMOVE: " + command)
                            stream = os.popen(command)
                            output = stream.read()
                            print(output)
                        command = "%s apply %s/fdl-%s.yaml --config %s" % (oscar_cli, new_dir, component_name, config_dir)
                        print("APPLY: " + command)
                        stream = os.popen(command)
                        output = stream.read()
                        if "Applying file" in output:
                            print(output)
                            command = "%s service list  -c %s --config %s " % (oscar_cli, identifier, config_dir)
                            print("SERVICE LIST: " + command)
                            stream = os.popen(command)
                            output = stream.read()
                            print(output)
                            print(component_name)
                            if component_name in output:
                                print("The FDL of %s has been apply correctly" % component_name)
                        else:
                            print(output)
                            print("ERROR applying the FDL")        
                    else:
                        print("Error in the addition of the cluster with oscar_cli at the component %s" % name)
            elif case == "A":
                print("Oscar case A")
        print("DONE Update of cluster images in the infrastructures")
    else:
        print("It is not found oscar-cli path")
    
