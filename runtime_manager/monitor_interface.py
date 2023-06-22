import requests
import subprocess
import yaml
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
tp_file = dir_path + "/tp"
url = "http://127.0.0.1:5000"
delta = 0.01


def monitor_call():
    print("dir: %s" % dir_path)
    try:
        #resp = requests.request("GET", "%s/alarm" % url)
        #rt = resp.text
        run_cmd = subprocess.run(["curl", "http://ai-sprint-monit-api.ai-sprint-monitoring/monitoring/throughput/"], capture_output=True, text=True)
        out_3 = run_cmd.stdout
        tp = yaml.safe_load(out_3)['throughput']
        print("The throughput is: %s" % tp)
        tp_f = float(tp)
        f = open(tp_file, "r")
        tp_0 = float(f.readline())
        #print("----- %f" % tp_0)
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
        #print("\n%s" % out_3)
        #print("===> ALARM: %s" % rt)
        #return rt.split("\n")
        return True, tp
    except Exception as ex:
        print(str(ex))
        return False, str(ex)

monitor_call()