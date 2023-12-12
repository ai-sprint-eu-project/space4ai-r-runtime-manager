from flask import Flask, jsonify
from flask import request
import requests
import os
import sys
import json
from werkzeug.utils import secure_filename
import subprocess
import logging


###############
# Definitions #
###############
app = Flask("rm_api")
print(sys.path.append("./"))
from config import runtime_cli_cmd

#################
# API functions #
#################
@app.route("/keepalive", methods=['GET'])
def ka():
    if request.method == 'GET':
        return jsonify("ALIVE", 200)
    else:
        return jsonify("ERROR", 404)

@app.route("/krake", methods=['POST'])
def krake():
    if request.method == 'POST':
        with open("/mnt/config.json") as c:
            cfg= json.load(c)

        content_type = request.headers.get('Content-Type') 
        if  'multipart/form-data' in content_type:
            f = request.files['file']
            f.save(secure_filename(f.filename))
            OPTIMIZER_FOLDER = "/home/SPACE4AI-R/optimiser/"
            RUNTIMEMANAGER_FOLDER = "/home/SPACE4AI-R/runtime_manager/runtime_manager/"
            cmd = ['/bin/sh', '-c' , 'cd ' + \
                                     OPTIMIZER_FOLDER + \
                                     ' && python3 estimate_CPUs.py ' + \
                                     RUNTIMEMANAGER_FOLDER + f.filename + ' ' + \
                                     str(cfg['reconfiguration_time']) + ' ' + \
                                     str(cfg['total_execution_time_constraint']) + ' ' +\
                                     '/mnt/' + cfg['profiling_data'] + ' ' +\
                                     str(cfg['min_cores']) + ' ' + \
                                     str(cfg['max_cores']) \
                  ]
            run_cmd = subprocess.run(cmd, capture_output=True, text=True)
            out_3 = run_cmd.stdout
            app.logger.info(cmd)
            app.logger.info(out_3)

            with open(OPTIMIZER_FOLDER + "/out.json") as c:
                o= json.load(c)
        else:
            return 'Content-Type not supported!' 

        return jsonify("KRAKE", o, 200)
    else:
        return jsonify("ERROR", 404)

@app.route("/ams-alert", methods=['POST'])
def ams():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json_body = request.json
            if "Throughput" in json_body:
                Throughput = json_body["Throughput"]
            else:
                Throughput = None
            return "the Throughput is: " + str(Throughput)
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
