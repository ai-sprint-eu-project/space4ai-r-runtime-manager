import os

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