##############################################################################################################
#                                                                                                            
#               ___   ___                                                 ___   ___                          
#     // | |       / /              //   ) )     //   ) )     //   ) )       / /        /|    / /  /__  ___/ 
#    //__| |      / /              ((           //___/ /     //___/ /       / /        //|   / /     / /     
#   / ___  |     / /      ____       \\        / ____ /     / ___ (        / /        // |  / /     / /      
#  //    | |    / /                    ) )    //           //   | |       / /        //  | / /     / /       
# //     | | __/ /___           ((___ / /    //           //    | |    __/ /___     //   |/ /     / /        
#                                                                                                            
#
# Component: RUNTIME-MANAGER
##############################################################################################################

##########################
### GLOBAL DEFINITIONS ###
##########################
app_dir = "./apps/app"
im_auth_path_def = app_dir + "/im/auth.dat"
im_url_def = "https://appsgrycap.i3m.upv.es:31443/im"
oscar_cli_cmd = "~/go/bin/oscar-cli"
minio_cli_cmd = "~/minio-binaries/mc"
runtime_cli_cmd ="bin/runtime_manager_cli.py" 
def update_app_dir(dir):
    global app_dir
    global im_auth_path_def
    app_dir = dir
    im_auth_path_def = app_dir + "/im/auth.dat"
    print("\n====================================")
    print("app_dir: %s" % app_dir)
    print("im_auth_path_def: %s" % im_auth_path_def)
    print("im_url_def: %s" % im_url_def)
    print("oscar_cli_cmd: %s" % oscar_cli_cmd)
    print("minio_cli_cmd: %s" % minio_cli_cmd)
    print("runtime_cli_cmd: %s" % runtime_cli_cmd)
    print("====================================\n")
