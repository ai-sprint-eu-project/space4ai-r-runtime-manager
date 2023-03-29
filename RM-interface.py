from flask import Flask, jsonify
from flask import request
import requests
import os



###############
# Definitions #
###############
app = Flask("IM-interface")
# sys.path.append("./")
# from im_interface import  *
# from utils import *

#################
# API functions #
#################

@app.route("/alarm", methods=['GET', 'POST'])
def infrastructures():
    if request.method == 'GET':
        return im_get_infrastructures()
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