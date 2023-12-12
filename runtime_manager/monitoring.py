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
OPTIMIZER_FOLDER = "/home/SPACE4AI-R/optimiser/"
RUNTIMEMANAGER_FOLDER = "/home/SPACE4AI-R/runtime_manager/runtime_manager/bin"

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
    print("working dir: %s" % dir_path)
    print("application dir: %s" % app_dir)
    while(True):
        status = getRmOpt()
        print("-%s-\n" % status)
        if "ON" == status:
            try:
                cmd = ["curl", "http://ai-sprint-monit-api.ai-sprint-monitoring/monitoring/throughput/"]
                print(cmd)
                #run_cmd = subprocess.run(cmd, capture_output=True, text=True)
                #out_3 = run_cmd.stdout
                #tp = yaml.safe_load(out_3)['throughput']
                tp = 0.1
                ct = datetime.datetime.now()
                print(f"The throughput @ {ct} is: " + '\x1b[0;30;47m' + f"{tp}"  + '\x1b[0m')
                tp_f = float(tp)
                f = open(tp_file, "r")
                tp_0 = float(f.readline())
                f.close()
                f = open("tp", "w")
                f.write(str(tp))
                f.close()
                tpx = tp_0 - (delta * tp_0)
                tpy = tp_0 + (delta * tp_0)
                print("%f -[%f]- %f" % (tpx, tp_0, tpy))
                if tpx <= tp_f <= tpy:
                    print('\x1b[0;30;47m' + f"<<< Throughput is in the acceptance range. No optimization/reconfiguration is required >>>"  + '\x1b[0m')
                else:
                    if (tp != 0):
                       print("Optimizing...")
                       print("@@@@@@@@@@@@@@@@@@@@@@@@@")
                       start = time.time()
                       cmd = ['/bin/sh', '-c' , 'cd ' + OPTIMIZER_FOLDER + ' && python3 s4ai-r-opt.py --application_dir ' + app_dir + ' --RG_n_iterations 10 --LS_n_iterations 2 --load ' + str(tp)]
                       print(cmd)
                       #run_cmd = subprocess.run(cmd, capture_output=True, text=True)
                       #out_3 = run_cmd.stdout
                       #print(out_3, end="")
                       end = time.time()
                       print("~~~ ELAPSED optimizer %f ~~~" % (end-start))
                       print("@@@@@@@@@@@@@@@@@@@@@@@@@")

                       print("Apply changes...")
                       print("#########################")
                       start = time.time()
                       cmd = ["/bin/sh", "-c" , "cd " + RUNTIMEMANAGER_FOLDER + " && python3 runtime_manager_cli.py difference --application_dir " + app_dir + " --apply_diff --swap_deployments"]
                       print(cmd)
                       #run_cmd = subprocess.run(cmd, capture_output=True, text=True)
                       #out_3 = run_cmd.stdout
                       #print(out_3, end="")
                       end = time.time()
                       print("~~~ ELAPSED switching %f ~~~" % (end-start))
                       print("#########################")
                    else:
                       print("No opt, througput is 0")


            except Exception as ex:
                print(str(ex))
                return False, str(ex)
        await asyncio.sleep(keepalive_time_sec)

asyncio.run(run_monitoring())
