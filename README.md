# RUNTIME-MANAGER

## Quick-Start

### Step1: Install RUNTIME-MANAGER

```sh
git clone https://gitlab.cefriel.it/ai-sprint/runtime-manager.git
cd runtime-manager/runtime-manager/bin
```

#### Install Go
Follow the instructions on [go web page](https://go.dev/doc/install) for the respective computer's operating system.

#### Install Oscar-cli
To install oscar client tool it is necessary to execute:
```sh
go install github.com/grycap/oscar-cli@latest
```
and run 
```sh
oscar-cli --help
```
to verify if it has been installed correctly. For more information see the [documentation](https://docs.oscar.grycap.net/oscar-cli/) 

#### Install minio-cli

follow the steps explained on [minio web page](https://min.io/docs/minio/linux/reference/minio-mc.html#) 


### Step2: Try --help

```sh
python3 runtime_manager_cli.py --help
```
### Step 3: copy auth.dat 
Copy the file *auth.dat* in the application directory with the same format explained on [IM](https://imdocs.readthedocs.io/en/latest/gstarted.html?highlight=auth#authentication-file).

```sh
type = InfrastructureManager; username = user; password = pass
id = ec2; type = EC2; username = AK; password = SK
```
### Step 4: parcer the tosca

The following command goes to the IM and get the toscas of all the available infrastructures. Then it relates it with the respective InfID and the component name related.

```sh
python3 runtime_manager_cli.py infras --application_dir <APPLICATION DIR> --dir_to_save <DIR TO SAVE THE TOSCA FILES>
```
- application_dir: it is the default folder of the application
- dir_to_save: it is folder to save the tosca files gotten from the IM

### Step 4: Evaluate production and apply the differences.

This command will read the production_deployment files, make a comparison between them and make the respective actions about it. (for now only related with the services of the clusters)

```sh
python3 runtime_manager_cli.py difference --application_dir  <APPLICATION DIR>  --old_dir <OPTIONAL DIR TO READ THE OLD TOSCA FILES>  --new_dir <OPTIONAL DIR TO READ THE OLD TOSCA FILES>
```
- application_dir: it is the default folder of the application
- old_dir: directory to read the old tosca files (OPTIONAL)
- new_dir: directory to read the old tosca files (OPTIONAL)

### Read OUTPUTS of the infrastructures

```sh
python3 runtime_manager_cli.py outputs --application_dir  <APPLICATION DIR> --dir_to_save <DIR TO SAVE THE OUTPUT FILES>
```