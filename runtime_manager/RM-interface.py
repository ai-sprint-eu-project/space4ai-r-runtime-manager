from flask import Flask, jsonify
from flask import request
import requests
import os
import sys



###############
# Definitions #
###############
app = Flask("IM-interface")
print(sys.path.append("./"))
from config import runtime_cli_cmd

#################
# API functions #
#################

@app.route("/alarm", methods=['GET', 'POST'])
def infrastructures():
    if request.method == 'GET':
        return runtime_manager_cli()
    elif request.method == 'POST':
        return im_post_infrastructures()
    else:
        return "<p>ERROR in HTTP request</p>"

def im_get_infrastructures():
    try:
        return "HELLO WORLD"
    except Exception as ex:
        print(str(ex))
        return False, str(ex)
def im_post_infrastructures():
    try:
        return "HELLO WORLD POST"
    except Exception as ex:
        print(str(ex))
        return False, str(ex)

def runtime_manager_cli():
    runtime_cli = "python3 %s --help" % (runtime_cli_cmd)
    stream = os.popen(runtime_cli)
    output = stream.read()
    print(output)
    return output
