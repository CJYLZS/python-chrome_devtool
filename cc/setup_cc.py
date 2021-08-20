import os
import sys
import json
def setup():
	'''
	取当前目录生成chrome配置文件 cc_config.json
	'''
	Value={
	  "name": "chrome_commucation",
	  "description": "native messaging host",
	  "path": "",
	  "type": "stdio",
	  "allowed_origins": ["chrome-extension://mfepiakbogcbfhkcmjdaiaocfnjlghdf/"]
	}
	Value['path']=os.getcwd()+'\\cc.bat'
	with open('cc_config.json', 'w') as f:
	    json.dump(Value,f)
setup()