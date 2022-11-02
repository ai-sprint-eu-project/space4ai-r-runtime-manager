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
            "componenet_name": values["name"],
            "exec_layer": values["executionLayer"],
            "resource": values["Containers"]["container1"]["selectedExecutionResources"]
        }
        i += 1
    return dic_new