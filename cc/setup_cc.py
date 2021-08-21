import os
import sys
import json
def setup():
	'''
	取当前目录生成chrome配置文件 cc_config.json
	'''
	with open('ID.txt','r') as f:
		chrome_ext_id = f.read()
	chrome_ext_id = "chrome-extension://%s/"%chrome_ext_id
	Value={
	  "name": "chrome_commucation",
	  "description": "native messaging host",
	  "path": "",
	  "type": "stdio",
	  "allowed_origins": [chrome_ext_id]
	}
	Value['path']=os.getcwd()+'\\cc.bat'
	with open('cc_config.json', 'w') as f:
	    json.dump(Value,f)
setup()