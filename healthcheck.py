import os
import subprocess

def process_exists(process_name):
    call = 'pgrep -f {}'.format(process_name)
    output = subprocess.check_output(call, shell=True)
    return process_name in output.decode()

if not process_exists("backup_script.py"):
    exit(1)
