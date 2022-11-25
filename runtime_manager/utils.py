import os
import yaml
import copy
import sys
from minio import Minio
import im_interface
import time
import glob

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

def getInfraId(component, dir):
    infraFile = "%s/infras.yaml" % dir
    infrasDict = yaml_as_dict(infraFile)
    infraId = ""
    found = False
    for k, v in infrasDict.items():
        #print(k, v)
        if (k==component):
            found = True
            #print("component: ", k)
            #print("infra: ", infrasDict[k][0])
            #print("status: ", infrasDict[k][1])
            infraId = infrasDict[k][0].rsplit('/', 1)[-1]
            #print("id: ", infraId)
            break
    if (False==found):
        print("No such component (%s) found in infras.dat", component)
    return infraId

def getSelectedResources(component, dic):
    res = []
    for item, values in dic["System"]["Components"][component]["Containers"].items():
        #print(">>>", values['selectedExecutionResources'])
        res.append(values['selectedExecutionResources'])
    return res

def getResourcesType(component, dic):
    returnValue = ""
    el = dic["System"]["Components"][component]['executionLayer'] 
    for item, values in dic["System"]["NetworkDomains"].items():
        for item2, values2 in values["ComputationalLayers"].items():
            if (el == values2['number']):
                returnValue = values2['type']
    return returnValue

def compareExecution(old_dic, new_dic, component):
    returnValue = False

    oldExec = old_dic["System"]["Components"][component]['executionLayer']
    newExec = new_dic["System"]["Components"][component]['executionLayer']

    oldResources = getSelectedResources(component, old_dic)
    newResources = getSelectedResources(component, new_dic)

    # print("Execution layer old:         %s" % oldExec)
    # print("Resources old:               %s" % oldResources)

    # print("Execution layer new:         %s" % newExec )
    # print("Resources new:               %s" % newResources)

    if (oldExec == newExec and set(oldResources) == set(newResources)):
        returnValue = True
    
    return returnValue

def searchExecution(old_dic, new_dic, component):
    returnValue = ""

    newExec = new_dic["System"]["Components"][component]['executionLayer']
    newResources = getSelectedResources(component, new_dic)

    for item, values in old_dic["System"]["toscas"].items():
        oldExec = old_dic["System"]["Components"][item]['executionLayer']
        oldResources = getSelectedResources(item, old_dic)
        if (oldExec == newExec and set(oldResources) == set(newResources)):
            # returnValue = True
            # print(" MATCHED >>>> ", oldExec, oldResources)
            returnValue = item
            break

    return returnValue

def searchLeaf(dic):
    returnValue = ""
    for component_new, values_new in dic["System"]["toscas"].items():
        clu = values_new["topology_template"]["inputs"]["cluster_name"]["default"]
        #print(" >>>%s" % (component_new))
        leaf = True
        for k in values_new["topology_template"]["node_templates"]["oscar_service_"+component_new]["properties"]["output"]:
            # print(" >OUTPUT %s" % (k["storage_provider"]))
            if ("minio" != k["storage_provider"]):
                leaf = False
                break
            #else:
                #print("    >OUTPUT %s" % "minio")
        if (True == leaf):
            returnValue = component_new
            break
    return returnValue

def searchPreviousComponent(dic, component):
    returnValue = ""
    if ("" == component):
        returnValue = searchLeaf(dic)
    else:
        for k in dic["System"]["toscas"][component]["topology_template"]["node_templates"]["oscar_service_"+component]["properties"]["input"]:
                for component_new, values_new in dic["System"]["toscas"].items():
                    for outPath in values_new["topology_template"]["node_templates"]["oscar_service_"+component_new]["properties"]["output"]:
                        inPath = k["path"]
                        if outPath["path"] == inPath:
                            returnValue = component_new
                            break
                if ("" != returnValue):
                    break
    return returnValue

def searchNextComponent(dic, component):
    returnValue = ""
    if ("" == component):
        returnValue = searchRoot(dic)
    else:
        for k in dic["System"]["toscas"][component]["topology_template"]["node_templates"]["oscar_service_"+component]["properties"]["output"]:
            # if ("minio" != k["storage_provider"]):
            #     clu = k["storage_provider"].split(".")[1]

            #     for component_new, values_new in dic["System"]["toscas"].items():
            #         clu_new = values_new["topology_template"]["inputs"]["cluster_name"]["default"]
            #         if (clu_new == clu):
            #             returnValue = component_new
            #             break
            # else:
                for component_new, values_new in dic["System"]["toscas"].items():
                    for inPath in values_new["topology_template"]["node_templates"]["oscar_service_"+component_new]["properties"]["input"]:
                        outPath = k["path"]
                        if inPath["path"] == outPath:
                            returnValue = component_new
                            break
                if ("" != returnValue):
                    break
    return returnValue

def searchRoot(dic):
    returnValue = ""
    for component_new, values_new in dic["System"]["toscas"].items():
        clu = values_new["topology_template"]["inputs"]["cluster_name"]["default"]
        if len(values_new["topology_template"]["node_templates"]["oscar_service_"+component_new]["properties"]["input"]) == 1:
            returnValue = component_new
        # root = True
        # for component_new2, values_new2 in dic["System"]["toscas"].items():

        #     for k in values_new2["topology_template"]["node_templates"]["oscar_service_"+component_new2]["properties"]["output"]:
        #         if ("minio" != k["storage_provider"]):
        #             cluOut = k["storage_provider"].split(".")[1]
        #             if (cluOut == clu):
        #                 root = False
        #                 break

        #     if (False == root):
        #         break
        # if (True == root):
        #     returnValue = component_new
        #     break
    return returnValue

def searchRootCluster(fdls):
    returnValue = ""
    for fdl in fdls["functions"]["oscar"]:
            identifier = list(fdl.keys())[0]
            value = list(fdl.values())[0]
            root = True
            #print(identifier)
            for fdl2 in fdls["functions"]["oscar"]:
                identifier2 = list(fdl2.keys())[0]
                value2 = list(fdl2.values())[0]
                for outputs in value2["output"]:
                    #print(outputs["storage_provider"])
                    if ("minio" != outputs["storage_provider"]):
                        cluOut = outputs["storage_provider"].split(".")[1]
                        if (cluOut == identifier):
                            root = False
                            break
                if (False == root):
                    break
            if (True == root):
                returnValue = identifier
                break
    return returnValue

def searchRootFdl(fdls):
    returnValue = {}
    for fdl in fdls["functions"]["oscar"]:
            identifier = list(fdl.keys())[0]
            value = list(fdl.values())[0]
            component = value["name"]
            root = True
            #print(identifier)
            for fdl2 in fdls["functions"]["oscar"]:
                identifier2 = list(fdl2.keys())[0]
                value2 = list(fdl2.values())[0]
                for outputs in value2["output"]:
                    #print(outputs["storage_provider"])
                    if ("minio" != outputs["storage_provider"]):
                        cluOut = outputs["storage_provider"].split(".")[1]
                        if (cluOut == identifier):
                            root = False
                            break
                if (False == root):
                    break
            if (True == root):
                returnValue = fdl
                break
    return returnValue

def getComponentFdl(fdls, component):
    returnValue = {}
    for fdl in fdls["functions"]["oscar"]:
        identifier = list(fdl.keys())[0]
        value = list(fdl.values())[0]
        if component == value["name"]:
            returnValue = fdl
            break
    return returnValue

def searchNextFdl(fdls, fdlRoot):
    returnValue = {}
    if ({} == fdlRoot):
        rv = searchRootFdl(fdls)
        returnValue = rv
    else:
        identifierRoot = list(fdlRoot.keys())[0]
        valueRoot = list(fdlRoot.values())[0]
        componentRoot = valueRoot["name"]
        for outputsRoot in valueRoot["output"]:
            if ("minio" != outputsRoot["storage_provider"]):
                    clusterRoot = outputsRoot["storage_provider"].split(".")[1]
                    #print("xxxxx", clusterRoot)
                    break

        for fdl in fdls["functions"]["oscar"]:
            identifier = list(fdl.keys())[0]
            value = list(fdl.values())[0]
            for input in value["input"]:
                for outputsRoot in valueRoot["output"]:
                    if outputsRoot["path"] == input["path"]:
                        returnValue = fdl
                        break
            if ({} != returnValue):
                break
            
    return returnValue

def searchNextCluster(fdls, cluster):
    returnValue = ""
    if ("" == cluster):
        returnValue = searchRootCluster(fdls)
    else:
        for fdl1 in fdls["functions"]["oscar"]:
            clu = ""
            identifier1 = list(fdl1.keys())[0]
            value1 = list(fdl1.values())[0]
            if (identifier1 == cluster):
                for outputs1 in value1["output"]:
                    if ("minio" != outputs1["storage_provider"]):
                        clu = outputs1["storage_provider"].split(".")[1]
                break
        for fdl in fdls["functions"]["oscar"]:
                identifier = list(fdl.keys())[0]
                value = list(fdl.values())[0]
                if (identifier == clu):
                    returnValue = identifier
                    break
    return returnValue

def deployTosca(comp, new_dir, case, delay=10, max_time=30):

    components_deployed = {}
    end = False
    cont = 0
    while not end and cont < max_time:
        if comp not in components_deployed:
                    success = False
                    num = 1
                    max_count = 3
                    wait_time = 10
                    while not success and num < (max_count+1):
                        success, inf_id = im_interface.im_post_infrastructures(new_dir+"/.."+im_auth_path_def, "%s/production/ready-case%s/%s-ready.yaml" % (new_dir, case, comp))
                        if not success:
                            if (num + 1) < (max_count+1):
                                print("Error launching deployment for component %s. Waiting (%ssec) to retry (%s/%s)." % (comp, wait_time, num, max_count-1))
                                time.sleep(wait_time)
                            else:
                                print("Deploy of component %s FAILED!" % (comp))
                                end = True
                        num += 1
                        state = 'pending' if success else 'failed'
                        components_deployed[comp] = (inf_id, state)
        else:
            # Update deployment state
            inf_id, state = components_deployed[comp]
            if state in ['pending', 'running']:
                pass
                # success, state = get_state(inf_id, auth_data, verify)
                # if success:
                #     components_deployed[comp] = inf_id, state
                #     end = True
        if not end:
            time.sleep(delay)
            cont += delay

    return components_deployed

def updateComponentDeployment(dic, component, production_old_dic, new_dir, case):
    rt = getResourcesType(component, dic)
    se = searchExecution(production_old_dic, dic, component)
    print("Updating deployment of component --> %s (%s)" % (component, rt))
    if ("Virtual" == rt):
        if ("" == (se)):
            print("Creating infrastructure ...")
            #deployTosca(component, new_dir, case)
            #im_interface.im_post_infrastructures(new_dir+"/.."+im_auth_path_def, "%s/production/ready-case%s/%s-ready.yaml" % (new_dir, case, component))
        else:
            print("Virtual resource action ...")
            #oscar_cli(new_dir, dic["System"]["toscas"][component], case)
    else:
        print("Phisical resource action ...")

def cleanComponentDeployment(dic, component, production_old_dic):
    rt = getResourcesType(component, dic)
    se = searchExecution(production_old_dic, dic, component)
    print("Cleaning deployment of component --> %s (%s)" % (component, rt))
    if ("Virtual" == rt):
        if ("" == (se)):
            print("New infrastructure nothing to clean!")
        else:
            print("Virtual resource clean ...")
    else:
        print("Phisical resource clean ...")

def cleanDeletedComponent(dic_new, dic_old):
    for component_old, values_old in dic_old["System"]["Components"].items():
        deletedComponent = True
        for component_new, values_new in dic_new["System"]["Components"].items():
                if (component_new == component_old):
                    deletedComponent = False
                    break
        if (True == deletedComponent):
            print("Deleting removed component %s ..." %(component_old))


# def dic_creation(dic):
#     dic_new = {}
#     for item, values in dic["System"]["Components"].items():
#         dic_new[values["name"]] =  { 
#             "exec_layer": values["executionLayer"],
#             "resource": values["Containers"]["container1"]["selectedExecutionResources"]
#         }
#     return dic_new

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
        else:
            print("The component '%s' in new production does not exist in old production, check the component assignation" % (component_new))
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
            # elif prop == 'image_pull_secrets':
            #     if not isinstance(value, list):
            #         value = [value]
            #     res['image_pull_secrets'] = value
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
    #Create folder if it does not exist
    if os.path.isdir("%s/production/ready-toscas" % (new_dir)):
            print()
    else:
        os.makedirs("%s/production/ready-toscas" % (new_dir))
    
    #Clean folder if there are old files
    files = glob.glob("%s/production/ready-toscas/*.yaml" % (new_dir))
    if files != []:
        for file in files:
            os.remove(file)
    #Create FDL
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

        #Save toscas that have been modified
        with open("%s/production/ready-toscas/%s-ready.yaml" % (new_dir, name), 'w+') as f:
            yaml.safe_dump(tosca, f, indent=2)
    fdls["functions"]["oscar"] = clusters
    #Save FDL
    if not os.path.isdir("%s/production/fdl/" % new_dir):
            os.makedirs("%s/production/fdl/" % new_dir)
    with open("%s/production/fdl/fdl-new.yaml" % (new_dir), 'w+') as f:
        yaml.safe_dump(fdls, f, indent=2)
    print("DONE new TOSCA and FDL saved")
    return fdls


def oscar_cli(new_dir, fdls, case, remove_bucket):
    oscar_cli = "~/go/bin/oscar-cli"
    new_dir = "%s/production/fdl" % (new_dir)
    if not os.path.isdir(new_dir):
        os.makedirs(new_dir)
    config_dir = "%s/config.yaml" % (new_dir)
    if (os.path.exists(config_dir) == False):
        f = open(config_dir, "w")
    config = {"oscar": {}}
    with open(config_dir, 'w+') as f:
        yaml.safe_dump(config, f, indent=2) 
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
                                if remove_bucket:
                                    minio_cli(endpoint_minio, access_key_minio, secret_key_minio, service_old, "DELETE")
            command = "%s apply %s/fdl-new.yaml --config %s" % (oscar_cli, new_dir, config_dir)
            print("APPLY: " + command)
            print("\n")
            stream = os.popen(command)
            output = stream.read()
            print(output)
            if "Applying file" in output:
                print("FDL is being applied")
        elif case == "B":

            nextFdl = searchNextFdl(fdls, {})
            while({} != nextFdl):
                identifier = list(nextFdl.keys())[0]
                print("********************")
                print("%s" % (identifier))
                print("********************")
                value = list(nextFdl.values())[0]
                endpoint = "https://%s.%s" % (identifier,  value["inputs"]["domain_name"]["default"])
                password = value["inputs"]["oscar_password"]["default"]
                endpoint_minio = "https://minio.%s.%s" % (identifier,  value["inputs"]["domain_name"]["default"])
                access_key_minio = "minio"
                secret_key_minio = value["inputs"]["minio_password"]["default"]
                # example oscar-cli  cluster add oscar-cluster-f5vr5dfn https://oscar-cluster-f5vr5dfn.aisprint-cefriel.link oscar 05gwt0zjc88m4udt 
                command = "%s cluster add  %s %s oscar %s --config %s" % (oscar_cli, identifier, endpoint, password, config_dir)
                print("CLUSTER ADD: %s" % command)
                stream = os.popen(command) 
                output = stream.read()
                print(output)
                if "successfully stored" in output:
                    command = "%s service list  -c %s --config %s " % (oscar_cli, identifier, config_dir)
                    print("SERVICE LIST: %s" % command)
                    print("\n")
                    stream = os.popen(command)
                    output = stream.read()
                    print(output)
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
                nextFdl = searchNextFdl(fdls, nextFdl)
                
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

def iteration_toscas(dic_old, dic_new, application_dir, case):
    # This two line are for the simplified version
    # component_name_verification(dic_old["System"]["Components"],dic_new["System"]["Components"])    
    # infrastructures_verification(dic_old["System"]["Components"],dic_new["System"]["Components"])
    for components_tosca_old, values_tosca_old in dic_old["System"]["toscas"].items():
        for components_new, values_new in dic_new["System"]["Components"].items():
            if values_tosca_old["infid"] == values_new["infid"]:
                tosca_new = dic_new["System"]["toscas"][values_new["name"]]
                correct_name = values_tosca_old["component_name"]
                dic_new["System"]["toscas"][values_new["name"]] = mix_toscas(correct_name, dic_old["System"]["toscas"], tosca_new, application_dir, case)
    return dic_new["System"]["toscas"]