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
import datetime
import time

keepalive_time_sec = 120
dir_path = os.path.dirname(os.path.realpath(__file__))
tp_file = dir_path + "/tp"
delta = 0.05
app_dir = sys.argv[1]
tp = float(sys.argv[2])

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
    f = open(rm_opt_file,'w')
    f.write(status)
    f.close()

async def run_monitoring():
    global tp
    print("working dir: %s" % dir_path)
    print("application dir: %s" % app_dir)
    while(True):
        status = getRmOpt()
        print("-%s-\n" % status)
        print("tp [req/min]: %s" % tp)
        tp = tp / 60
        print("tp [req/min]: %s" % tp)
        if "ON" == status:
            try:
                if (tp==0):
                    print("0")
                else:
                    print("...")
                    if (tp != 0):
                       print("Optimizing...")
                       print("@@@@@@@@@@@@@@@@@@@@@@@@@")
                       start = time.time()
                       cmd = ['/bin/sh', '-c' , 'cd /home/SPACE4AI-R/optimiser/ && python3 s4ai-r-opt.py --application_dir ' + app_dir + ' --RG_n_iterations 10 --LS_n_iterations 2 --load ' + str(tp)]
                       print(cmd)
                       run_cmd = subprocess.run(cmd, capture_output=True, text=True)
                       out_3 = run_cmd.stdout
                       print(out_3, end="")
                       end = time.time()
                       print("~~~ ELAPSED optimizer %f ~~~" % (end-start))
                       print("@@@@@@@@@@@@@@@@@@@@@@@@@")

                       print("Apply changes...")
                       print("#########################")
                       start = time.time()
                       cmd = ["/bin/sh", "-c" , "cd /home/SPACE4AI-R/runtime_manager/runtime_manager/bin && python3 runtime_manager_cli.py difference --application_dir " + app_dir + " --apply_diff --swap_deployments"]
                       print(cmd)
                       run_cmd = subprocess.run(cmd, capture_output=True, text=True)
                       out_3 = run_cmd.stdout
                       print(out_3, end="")
                       end = time.time()
                       print("~~~ ELAPSED switching %f ~~~" % (end-start))
                       print("#########################")
                    else:
                       print("No opt, througput is 0")
            except Exception as ex:
                print(str(ex))
                return False, str(ex)

        return True
        await asyncio.sleep(keepalive_time_sec)

asyncio.run(run_monitoring())
