import subprocess
import yaml
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
tp_file = dir_path + "/tp"
delta = 0.01

def getRmOpt():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    rm_opt_file = dir_path + "/rm_opt"
    f = open(rm_opt_file,'r')
    status = f.readline().replace('\n','').replace('\t','')
    f.close()
    return status

def monitor_call():
    status = getRmOpt()
    print("-%s-" % status)
    # TODO: add monitoring here!

monitor_call()