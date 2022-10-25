# RUNTIME-MANAGER

## Quick-Start

### Step1: Install RUNTIME-MANAGER

```sh
git clone https://gitlab.cefriel.it/ai-sprint/runtime-manager.git
cd runtime-manager
python3 -m pip install . 
```

### Step2: Try --help

```sh
runtime --help
```
### Step 3: copy auth.dat 
Copy the file *auth.dat* in the application directory with the same format explained on [IM](https://imdocs.readthedocs.io/en/latest/gstarted.html?highlight=auth#authentication-file).

```sh
type = InfrastructureManager; username = user; password = pass
id = ec2; type = EC2; username = AK; password = SK
```
### Step 4: parcer the tosca

```sh
runtime infras --application_dir
```
