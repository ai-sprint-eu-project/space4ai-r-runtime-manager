# RUNTIME-MANAGER

## Quick-Start

### Pre-requirements

#### SPACE4AI-D

It is assumed that all the process with SPACE4AI-D has been done completed and a fully configured AI-SPRINT application is available. For more documentation you can see SPACE4AI-D [documentation](https://gitlab.polimi.it/ai-sprint/space4ai-d) 

#### Toscarizer
The Toscarizer should been downloaded from the [repository](https://gitlab.polimi.it/ai-sprint/toscarizer) and install it following the instructions.

Customize the toscarizer oscar.yaml file (/toscarizer/templates/oscar.yaml) to match the AI-SPRINT application requirements. In particular:
##### set the domain name used for FrontEnd/Oscar and Minio client:
```yaml
    domain_name:
      type: string
      default: aisprint-cefriel.link
```

##### set the AK/SK for DNS repalcing [AK_OMISSIS] and [SK_OMISSIS]:
```yaml
    dns_reg_console_minio:
      type: tosca.nodes.ec3.DNSRegistry
      properties:
        record_name: { concat: [ "console.minio.", get_input: cluster_name ] }
        domain_name: { get_input: domain_name }
        dns_service_credentials:
          token_type: password
          token: "[AK_OMISSIS]:[SK_OMISSIS]"
      requirements:
        - host: front

    dns_reg_minio:
      type: tosca.nodes.ec3.DNSRegistry
      properties:
        record_name: { concat: [ "minio.", get_input: cluster_name ] }
        domain_name: { get_input: domain_name }
        dns_service_credentials:
          token_type: password
          token: "[AK_OMISSIS]:[SK_OMISSIS]"
      requirements:
        - host: front

    dns_reg:
      type: tosca.nodes.ec3.DNSRegistry
      properties:
        record_name: { get_input: cluster_name }
        domain_name: { get_input: domain_name }
        dns_service_credentials:
          token_type: password
          token: "[AK_OMISSIS]:[SK_OMISSIS]"
      requirements:
        - host: front
 
[...]
    lrms_front_end:
      type: tosca.nodes.indigo.LRMS.FrontEnd.Kubernetes
      capabilities:
        endpoint:
          properties:
            port: 30443
            protocol: tcp
      properties:
        admin_username:  kubeuser
        admin_token: { get_input: admin_token }
        install_kubeapps:  false
        install_metrics: true
        install_nfs_client: true
        install_ingress: true
        version: 1.23.6
        cert_manager: true
        cert_user_email: { get_input: cert_user_email }
        public_dns_name: { concat: [ get_property: [dns_reg, record_name], '.', get_property: [dns_reg, domain_name] ] }
        cert_manager_challenge: dns01
        cert_manager_challenge_dns01_domain: { get_property: [dns_reg, domain_name] }
        cert_manager_challenge_dns01_ak: AK_OMISSIS
        cert_manager_challenge_dns01_sk: SK_OMISSIS
      requirements:
        - host: front

```

#### Install Go
Follow the instructions on [go web page](https://go.dev/doc/install) for the relevant operating system.

#### Install Oscar-cli
To install oscar client tool it is necessary to execute:
```sh
go install github.com/grycap/oscar-cli@latest
```
and run 
```sh
oscar-cli --help
```
to verify if it has been installed correctly.
For more information see oscar-cli [documentation](https://docs.oscar.grycap.net/oscar-cli/) 

#### Install minio-cli

Follow the steps explained on [minio web page](https://min.io/docs/minio/linux/reference/minio-mc.html#) 

#### Install Anaconda

Follow the steps explained on [anaconda web page](https://docs.anaconda.com/anaconda/install/linux/) 

#### Flask server
Go to the directory *runtime_manager*
- Create *.flaskenv* with 
```
FLASK_APP=RM_interface.py
FLASK_ENV=development
FLASK_RUN_HOST=<HOST> (127.0.0.1 -- local for now)
FLASK_RUN_PORT=<PORT> (5000 by default)
```

- Verify that flask is installed with the code:
```sh
flask -e
```
it should print the options of flask.

- If flask is installed you can run flask and the server will be activated
```sh
flask run
```
#### Crontab task
To create a cron task of the file *monitor_interface.py*, go to the directory *runtime_manager* and execute the command 
```sh
python3 schedule_cron.py
```
To see if the task was schedule correctly, write the command 
```sh
crontab -l
```
Note: For now, it is programmed to make request to the flask server

### RUNTIME-MANAGER
```sh
git clone https://gitlab.cefriel.it/ai-sprint/runtime-manager.git
cd runtime-manager/
```
#### Set up with python enviroment
It is necessary to create the enviroment and activate it to properly work with the runtime manager.

To create the enviroment from RUNTIME-MANAGER root folder:
```sh
conda env create -f environment.yml
```
To activate enviorment:
```sh
conda activate runtime-manager
```
To deactivate enviroment (if needed):
```sh
conda deactivate
```

#### Set up with python requirements.txt
Install libraries 

```sh
pip install -r /requirements.txt
```

#### Check everything is installed corerctly
Go to the folder *runtime-manager/bin*

```sh
python3 runtime_manager_cli.py --help
```
#### RUNTIME-MANAGER cli

##### Command: infras

```sh
python3 runtime_manager_cli.py infras --application_dir <APPLICATION DIR> --dir_to_save <DIR TO SAVE THE TOSCA FILES>
```

The command goes to the IM and get the toscas of all the available infrastructures. Then it relates it with the respective InfID and the component name related

*--application_dir*: the root folder for AI-SPRINT application

*--dir_to_save*: [OPTIONAL] folder where to save the command output
if there is not **dir_to_save**, it will take by default the folder *application_dir/aisprint/deployments/base/im* to save the old toscas

##### Command: tosca

```sh
python3 runtime_manager_cli.py tosca --application_dir <APPLICATION DIR> --tosca_dir <TOSCARIZER DIRECTORY>
```
This command will install all the toscarizer dependencies and create the new toscas using as references the new production_deployment.yaml and application_dag.yaml.
The toscas will be saved at the folder *<APPLICATION DIR>/aisprint/deployments/optimal_deployment/im*

###### Parameters:

*--application_dir*: the root folder for AI-SPRINT application

*--tosca_dir*: directory where toscarizer has been installed


##### Command: difference

This command will read the production_deployment files, make a comparison between them and make the respective actions about it. (for now only related with the services of the clusters and the change of nodes number of each infrastructure)

```sh
python3 runtime_manager_cli.py difference --application_dir  <APPLICATION DIR>  --old_dir <OPTIONAL DIR TO READ THE OLD TOSCA FILES>  --new_dir <OPTIONAL DIR TO READ THE OLD TOSCA FILES> --remove_bucket --update_infras
```
This command evaluates current and optimised production configuration and applies the differences. This command reads the production_deployment files, makes a comparison between them and applies the required actions. 

###### Parameters:

*--application_dir*: the root folder for AI-SPRINT application

*--old_dir*: [OPTIONAL] directory to read the tosca files for the current configuration; if old_dir it is not provided, the default folder for current running application configuration is: application_dir/aisprint/deployments/base/im

*--new_dir*: [OPTIONAL] directory to read the tosca files for the optimised configuration; if new_dir it is not provided, the default folder for the optimised application configuration is: application_dir/aisprint/deployments/optimal_deployment/im

*--remove_bucket*: [OPTIONAL] it is a flag to remove the old buckets related to the Oscar clusters.

*--update_infras*: [OPTIONAL] it is a flag to update the infras.yaml which is located at application_dir/aisprint/deployments/base/im with information gathered from IM.

*--swap_deployments*: [OPTIONAL] it is a flag to back-up base folder to base_TIMESTAMP folder and then copy optimal_deployments to base.



##### Command: outputs

```sh
python3 runtime_manager_cli.py outputs --application_dir  <APPLICATION DIR> --dir_to_save <DIR TO SAVE THE OUTPUT FILES>
```
This command query the IM instances (as in infras.yaml) and retrieve and parse the infrastructures configuration (endpoints, logins and access keys) and save the output to the specified folder.

###### Parameters:
*--application_dir*: the root folder for AI-SPRINT application

*--dir_to_save*: folder where to save the command output