# RUNTIME-MANAGER

## Quick-Start

### Step1: Install RUNTIME-MANAGER

```sh
git clone https://gitlab.cefriel.it/ai-sprint/runtime-manager.git
cd runtime-manager/runtime-manager/bin
```

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

```sh
python3 runtime_manager_cli.py infras --application_dir <APPLICATION DIR> --dir_to_save <DIR TO SAVE THE TOSCA FILES>
```


### Read OUTPUTS of the infrastructures

```sh
python3 runtime_manager_cli.py outputs --application_dir  <APPLICATION DIR> --dir_to_save <DIR TO SAVE THE OUTPUT FILES>
```