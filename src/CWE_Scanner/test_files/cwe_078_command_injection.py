
# 命令注入測試
import os
import subprocess

user_command = input("Enter command: ")
os.system("ls " + user_command)
subprocess.call("ping " + user_command, shell=True)
