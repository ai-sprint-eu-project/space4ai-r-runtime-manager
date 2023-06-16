from flask import Flask, jsonify
from flask import request
import requests
import os
import sys
import json


###############
# Definitions #
###############
app = Flask("IM-interface")
print(sys.path.append("./"))
from config import runtime_cli_cmd

#################
# API functions #
#################

@app.route("/ams-alert", methods=['POST'])
def infrastructures():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json_body = request.json
            if "Throughput" in json_body:
                Throughput = json_body["Throughput"]
            else:
                Throughput = None
            return "the Throughput is: " + Throughput
        else:
            return 'Content-Type not supported!' 
    else:
        return "<p>ERROR in HTTP request</p>"

# def im_post_infrastructures():
#     try:
#         return "HELLO WORLD POST"
#     except Exception as ex:
#         print(str(ex))
#         return False, str(ex)

# def runtime_manager_cli():
#     """
#     runtime_cli = "python3 %s --help" % (runtime_cli_cmd)
#     stream = os.popen(runtime_cli)
#     output = stream.read()
#     print(output)
#     """
#     return "HELL YEAH!"
