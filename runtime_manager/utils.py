import os
import yaml
import copy
import sys
from minio import Minio

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
    elif case == "A" or case == "D" or case == "E":
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
        components_same = 0
        print("Not all the components have the same name")
    return components_same

def infrastructures_verification(dic_old, dic_new):
    count_machines = 0
    machines_same = -1
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
        print("All the infrastructures in production_new are defined in production_old")
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
    inputs = {}
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
            service["inputs"] = copy.deepcopy(inputs)
            if service["name"] not in done:
                cluster_name = oscar_name if oscar_name else node_name
                fdl["functions"]["oscar"].append({cluster_name: service})
                done.append(service["name"])
    return fdl

def save_toscas_fdl(new_dir, toscas, case):
    fdls = {
            "functions": {
            },
            "storage_providers": {
                "minio": {
                }
                # It can be added the support for the S3 and Onedata storage providers
            }
         }
    clusters = []
    done = []
    for name, tosca in toscas.items():
        fdl = generate_fdl(tosca)
        identifier = list(fdl["functions"]["oscar"][0].keys())[0]
        if "storage_providers" in fdl:
            if "minio" in fdl["storage_providers"]:
                for cluster, data in fdl["storage_providers"]["minio"].items():
                    fdls["storage_providers"]["minio"][cluster] = data
            elif "s3" in fdl["storage_providers"]:
                print("The 's3' storage provider is not supported yet")
            elif "onedata" in fdl["storage_providers"]:
                print("The 'onedata' storage provider is not supported yet")
            elif  "webdav" in fdl["storage_providers"]:
                print("The 'webdav' storage provider is not supported yet")
            else:
                print("The used storage provider is not supported")
        tosca.pop("component_name", None)
        for service in fdl["functions"]["oscar"]:
            service[identifier].pop("inputs", None)
        generated = generate_fdl(tosca)["functions"]["oscar"]
        if len(generated) != 1:
            for values in generated:
                if identifier not in done:
                        clusters.append(values)   
        else:
            clusters.append(generated[0])
        done.append(identifier)
        with open("%s/production/ready-case%s/%s-ready.yaml" % (new_dir, case, name), 'w+') as f:
            yaml.safe_dump(tosca, f, indent=2)
        # with open("%s/production/fdl/fdl-%s.yaml" % (new_dir, name), 'w+') as f:
        #     yaml.safe_dump(fdl, f, indent=2)
    fdls["functions"]["oscar"] = clusters
    with open("%s/production/fdl/fdl-new.yaml" % (new_dir), 'w+') as f:
        yaml.safe_dump(fdls, f, indent=2)
    print("DONE new TOSCA and FDL saved")
    return fdls


def oscar_cli(new_dir, fdls, case):
    oscar_cli = "~/go/bin/oscar-cli"
    new_dir = "%s/production/fdl" % (new_dir)
    config_dir = "%s/config.yaml" % (new_dir)
    stream = os.popen(oscar_cli)
    output = stream.read()
    if "/bin/sh" not in stream.read():
        if case == "A" or case == "C" or case == "D" or case == "E":
            for fdl in fdls["functions"]["oscar"]:
                identifier = list(fdl.keys())[0]
                value = list(fdl.values())[0]
                endpoint = "https://%s.%s" % (identifier,  value["inputs"]["domain_name"]["default"])
                password = value["inputs"]["oscar_password"]["default"]
                endpoint_minio = "https://minio.%s.%s" % (identifier,  value["inputs"]["domain_name"]["default"])
                access_key_minio = "minio"
                secret_key_minio = value["inputs"]["minio_password"]["default"]
                # example oscar-cli  cluster add oscar-cluster-f5vr5dfn https://oscar-cluster-f5vr5dfn.aisprint-cefriel.link oscar 05gwt0zjc88m4udt 
                command = "%s cluster add  %s %s oscar %s --config %s" % (oscar_cli, identifier, endpoint, password, config_dir)
                print("CLUSTER ADD: %s" % command)
                print("\n")
                stream = os.popen(command) 
                output = stream.read()
                print(output)
                if "successfully stored" in output:                            
                    command = "%s service list  -c %s --config %s " % (oscar_cli, identifier, config_dir)
                    print("SERVICE LIST: %s" % command)
                    stream = os.popen(command)
                    output = stream.read()
                    if "There are no services in the cluster" not in output:
                        output_split = output.split("\n")
                        for line in output_split:
                            if "NAME" not in line and line != "":
                                service_old = line.split("\t")[0]
                                command = "%s service remove %s -c %s --config %s" % (oscar_cli, service_old, identifier, config_dir)
                                print("SERVICE REMOVE: %s" % command)
                                print("\n")
                                stream = os.popen(command)
                                output = stream.read()
                                print(output)
                                minio_cli(endpoint_minio, access_key_minio, secret_key_minio, service_old, "DELETE")
            command = "%s apply %s/fdl-new.yaml --config %s" % (oscar_cli, new_dir, config_dir)
            print("APPLY: " + command)
            print("\n")
            stream = os.popen(command)
            output = stream.read()
            print(output)
            if "Applying file" in output:
                print("FDL is being applied")
    else:
        print("It is not found oscar-cli path")
    
def minio_cli(endpoint, access_key, secret_key, service_old, action):
    minio_cli = "~/minio-binaries/mc"
    command = "%s alias set %s %s %s %s" % (minio_cli, service_old, endpoint, access_key, secret_key)
    stream = os.popen(command) 
    output = stream.read()
    print("MINIO ALIAS SET: %s" % command)
    print("\n")
    print(output)
    if action == "DELETE":
        if  "Add" in output and "successfully" in output:
            print("MINIO BUCKET %s -----------------------------" % action)
            # #List Buckets
            # command = "%s ls --recursive %s" % (minio_cli, service_old)
            # print(command)
            # stream = os.popen(command) 
            # output = stream.read()
            # print(output)
            # #Remove info inside bucket
            # outputs = output.split("\n")
            # for buckets in outputs:
            #     bucket = buckets.split("STANDARD ")
            #     if "" not in bucket:
            #         command = "%s rm --force %s/%s" % (minio_cli, service_old,bucket[1])
            #         print(command)
            #         stream = os.popen(command) 
            #         output = stream.read()
            #         print(output)
            #Remove general bucket
            command = "%s ls %s" % (minio_cli, service_old)
            print("MINIO LIST: %s" % command)
            print("\n")
            stream = os.popen(command) 
            output = stream.read()
            print(output)
            outputs = output.split("\n")
            for buckets in outputs:
                bucket = buckets.split("B ")
                if "" not in bucket:
                    command = "%s rb --force %s/%s" % (minio_cli, service_old, bucket[1])
                    print("MINIO REMOVE BUCKET: %s" % command)
                    print("\n")
                    stream = os.popen(command) 
                    output = stream.read()
                    print(output)
