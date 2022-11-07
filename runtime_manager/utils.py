import os
import yaml

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
def mix_toscas(correct_name, toscas_old, tosca_new):
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
                print("uno")
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
    return tosca_new

def component_name_verification(dic_old, dic_new):
    count_components = 0
    for component_new, value_new in dic_new.items():
        if component_new in dic_old:
            if dic_new[component_new]["name"] == dic_old[component_new]["name"]:
                count_components += 1
            else:
                print("The component name on '%s' on the new production does not match with the component name on old production" %(component_new))
                break
        else:
            print("The component '%s' in new production does not exist in old production, check the component assignation" % (component_new))
            break
    if count_components == len(dic_old):
        components_same = True
        print("all Components have the same name")
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
        machines_same = True
        print("All the infrastructures are the same")
    elif count_machines == 0:
        machines_same = False
        print("All the infrastructures are different")
    else:
        machines_same = False
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
    fdl = {}

    done = []
    # for tosca_file in tosca_files:
    # if "infras.yaml" not in tosca_file:
    # with open(tosca_file) as f:
        # tosca = yaml.safe_load(f)
    oscar_name = None
    # Name in already deployed cluster
    if "oscar_name" in tosca["topology_template"]["inputs"]:
        oscar_name = tosca["topology_template"]["inputs"]["oscar_name"]["default"]
    # Name in IM generated cluster
    elif "cluster_name" in tosca["topology_template"]["inputs"]:
        oscar_name = tosca["topology_template"]["inputs"]["cluster_name"]["default"]
    for node_name, node in tosca["topology_template"]["node_templates"].items():
        if node["type"] == "tosca.nodes.aisprint.FaaS.Function":
            service = get_oscar_service_json(node["properties"])
            if service["name"] not in done:
                cluster_name = oscar_name if oscar_name else node_name
                fdl[cluster_name] = service
                # fdl["functions"]["oscar"].append({cluster_name: service})
                # done.append(service["name"])

    return fdl