import requests
import sys

# sys.path.append(".")

from utils import read_auth, im_url_def

def im_get_infrastructures(im_auth_path_def):
    auth_data = read_auth(im_auth_path_def)
    headers = {"Authorization": auth_data}
    try:
        resp = requests.request("GET", "%s/infrastructures" % im_url_def, headers = headers)
        return resp.text.split("\n")
    except Exception as ex:
        print(str(ex))
        return False, str(ex)

def im_get_tosca(id, im_auth_path_def):
    auth_data = read_auth(im_auth_path_def)
    headers = {"Authorization": auth_data}
    try:
        resp = requests.request("GET","%s/infrastructures/%s/tosca" % (im_url_def,id), headers = headers)
        return resp.text
    except Exception as ex:
        print(str(ex))
        return False, str(ex)

def im_get_outputs(id, im_auth_path_def):
    auth_data = read_auth(im_auth_path_def)
    headers = {"Authorization": auth_data}
    try:
        resp = requests.request("GET","%s/infrastructures/%s/outputs" % (im_url_def,id), headers = headers)
        return resp.text
    except Exception as ex:
        print(str(ex))
        return False, str(ex)

def im_post_infrastructures(im_auth_path_def, tosca):
    auth_data = read_auth(im_auth_path_def)
    headers = {"Authorization": auth_data, 'Content-Type': 'text/yaml'}
    print(headers)
    print(tosca)

    with open(tosca, 'rb') as f:
        data = f.read()
        #print(data)
    try:
        resp = requests.request("POST", "%s/infrastructures" % im_url_def, headers = headers, data = data)
        print(resp.text)
        success = resp.status_code == 200
        return success, resp.text
    except Exception as ex:
        return False, str(ex)

def im_get_state(inf_id, im_auth_path_def):
    auth_data = read_auth(im_auth_path_def)
    headers = {"Authorization": auth_data}
    headers["Content-Type"] = "application/json"
    try:
        resp = requests.request("GET", "%s/state" % inf_id, headers=headers)
        success = resp.status_code == 200
        if success:
            return success, resp.json()["state"]["state"]
        else:
            return success, resp.text
    except Exception as ex:
        return False, str(ex)