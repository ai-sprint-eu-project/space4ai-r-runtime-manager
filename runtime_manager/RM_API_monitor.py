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

keepalive_time_sec = 6
dir_path = os.path.dirname(os.path.realpath(__file__))
tp_file = dir_path + "/tp"
delta = 0.05
app_dir = sys.argv[1]
OPTIMIZER_FOLDER = "/home/SPACE4AI-R/optimiser/"
RUNTIMEMANAGER_FOLDER = "/home/SPACE4AI-R/runtime_manager/runtime_manager/bin"
RUNTIMEMANAGER_FOLDER = "/aisprint/runtime-manager/runtime_manager/bin"

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
    print(" ------------------------------\n")
    print("| Serving Runtime Manager API  |\n")
    print(" ------------------------------\n")
    m0=0
    while(True):
        status = getRmOpt()
        #print("-%s-\n" % status)
        
        if "ON" == status:
            setRmOpt("OFF")
            try:
                # run_cmd = subprocess.run(["curl", "http://ai-sprint-monit-api.ai-sprint-monitoring/monitoring/throughput/"], capture_output=True, text=True)
                # out_3 = run_cmd.stdout
                # tp = yaml.safe_load(out_3)['throughput']
                # ct = datetime.datetime.now()
                # ts = ct.timestamp()
                # print("The throughput @ %s [%s] is: %s" % (ct, ts, tp))
                with open("ams", "r") as f:
                    tp = f.readline().replace('\n','').replace('\t','')
                d = '2023-10-08 15:58:11'
                dt = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                print('\x1b[0;30;47m' + f"AMS alert for VIOLATION --> POST"  + '\x1b[0m')
                print(f"The Execution time @ {dt+datetime.timedelta(minutes=m0)} is: " + '\x1b[0;30;47m' + f"18.8 sec"  + '\x1b[0m')
                print(f"The Execution time constarint is: " + '\x1b[0;30;47m' + f"15.0 sec"  + '\x1b[0m')

                print("Optimizing...")
                print("@@@@@@@@@@@@@@@@@@@@@@@@@")
                start = time.time()
                cmd = ['/bin/sh', '-c' , 'cd ' + OPTIMIZER_FOLDER + ' && python3 s4ai-r-opt.py --application_dir ' + app_dir + ' --RG_n_iterations 10 --LS_n_iterations 2 --load ' + str(tp)]
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
                cmd = ["/bin/sh", "-c" , "cd " + RUNTIMEMANAGER_FOLDER + " && python3 runtime_manager_cli.py difference --application_dir " + app_dir + " --apply_diff --swap_deployments"]
                print(cmd)
                run_cmd = subprocess.run(cmd, capture_output=True, text=True)
                out_3 = run_cmd.stdout
                print(out_3, end="")
                end = time.time()
                print("~~~ ELAPSED switching %f ~~~" % (end-start))
                print("#########################")



            except Exception as ex:
                print(str(ex))
                return False, str(ex)
        #return True
        await asyncio.sleep(keepalive_time_sec)

asyncio.run(run_monitoring())
