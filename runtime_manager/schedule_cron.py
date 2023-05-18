import os
from crontab import CronTab

#Getting the real paths of python executor and current path
current_path = os.getcwd()
command =  "which python"
stream = os.popen(command) 
python_command = stream.read().split("\n")[0]

#Crontab definition
empty_cron = CronTab(user = "root")

command = '%s %s/monitor_interface.py' % (python_command, current_path)

job = empty_cron.new(command= command)
job.minute.every(1)
empty_cron.write()