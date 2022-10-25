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

import requests

try:
    # To avoid annoying InsecureRequestWarning messages in some Connectors
    import requests.packages
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

def getImCredential():
    with open("auth.dat", 'r') as fp:
        for line in fp.readlines():
            line.split(";")
            line = line.strip()
            d = dict(x.split("=") for x in line.split(";"))
            d = {
                key.replace(' ', ''): value.replace(' ', '') for key, value in d.items()
            }
            for k, v in d.items():
                if (v=="InfrastructureManager"):
                    return d['username'],d['password']
            return -1

def getAuthorization():
    auth = ''
    with open("auth.dat", 'r') as fp:
        for line in fp.readlines():
            auth = auth + line.replace('\r', '').replace('\n', '') + '\\n'
        return auth

def getInfrastructures

if __name__ == '__main__':
    imCredentials = getImCredential()
    print("IM credentials: ", imCredentials)

    authorization = getAuthorization()
    print("Authorization: ", authorization)

    # Infrastructure
    headers = {"Authorization": authorization}
    url = "https://appsgrycap.i3m.upv.es:31443/im/infrastructures"
    resp = requests.request("POST", url, verify=False, headers=headers, data="")
    print(resp, resp.text)

    # Tosca

    # Parsing tosca
    # (nome_service, infId)

    # Production_deplyments_NEW.yaml

    # Production_deplyments_NEW.yaml -> tosca_NEW.yaml (toscarizer)


