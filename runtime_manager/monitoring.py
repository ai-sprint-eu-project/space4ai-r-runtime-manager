import asyncio
import os
import subprocess
import shutil
import sys
sys.path.append("./")
sys.path.append("../")
from im_interface import *
from utils import *
from config import update_app_dir
import config as cfg
import subprocess
import yaml
import os

keepalive_time_sec = 10
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

def setRmOpt(status):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    rm_opt_file = dir_path + "/rm_opt"
    #print(rm_opt_file)
    f = open(rm_opt_file,'w')
    f.write(status)
    f.close()

async def run_monitoring():
    print("dir: %s" % dir_path)
    status = getRmOpt()
    print("-%s-" % status)
    if "ON" == status:
        try:
            run_cmd = subprocess.run(["curl", "http://ai-sprint-monit-api.ai-sprint-monitoring/monitoring/throughput/"], capture_output=True, text=True)
            out_3 = run_cmd.stdout
            tp = yaml.safe_load(out_3)['throughput']
            print("The throughput is: %s" % tp)
            tp_f = float(tp)
            f = open(tp_file, "r")
            tp_0 = float(f.readline())
            f.close()
            f = open("tp", "w")
            #f.truncate(0)
            f.write(str(tp))
            f.close()
            tpx = tp_0 - delta
            tpy = tp_0 + delta
            print("%f - %f" % (tpx, tpy))
            if tpx <= tp_f <= tpy:
                print("SAME")
            else:
                print("DIFFERENT")
                # TODO
            return True, tp
        except Exception as ex:
            print(str(ex))
            return False, str(ex)

        await asyncio.sleep(keepalive_time_sec)

asyncio.run(run_monitoring())