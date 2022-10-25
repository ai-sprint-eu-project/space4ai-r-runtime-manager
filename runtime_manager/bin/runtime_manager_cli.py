import click
import sys
import yaml

sys.path.append("../")
from im_interface import  *
from utils import im_auth_path_def, im_url_def, tosca_file_dir

@click.group()
def runtime_manager_cli():
    pass
# --application_dir /home/bedoya/cefriel/AISprint-test/api_python/runtime-manager
@click.command()
@click.option("--application_dir", help="Path to the RUNTIME-MANAGER application.", default=None)
def infras(application_dir):
    auth_path = "%s/%s" % (application_dir, im_auth_path_def)
    responses = im_get_infrastructures(auth_path)
    i = 1
    for response in responses:
        InfId = response.split("%s/infrastructures/" % im_url_def)[1]
        tosca = yaml.safe_load(im_get_tosca(InfId, auth_path))
        tosca["infid"] = InfId
        oscar_service = tosca["topology_template"]["outputs"]["oscar_service_url"]["value"]["get_attribute"][0] 
        tosca["component_name"] = tosca["topology_template"]["node_templates"][oscar_service]["properties"]["env_variables"]["COMPONENT_NAME"]
        tosca_path = "%s/%s" % (application_dir, tosca_file_dir) + "/" + tosca["component_name"] + "-" + str(i) + ".yaml"
        with open(tosca_path, 'w+') as f:
            yaml.safe_dump(tosca, f, indent=2)
        print("DONE. TOSCA files %s has been saved for the InfId %s" % (tosca["component_name"] + "-" + str(i) + ".yaml", InfId))
        i += 1
    

runtime_manager_cli.add_command(infras)

if __name__ == '__main__':
    runtime_manager_cli()


