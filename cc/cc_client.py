import socket
import _thread
import datetime
import time
import traceback
import json
import copy
import queue
import sys
from uuid import uuid4

def write_cc_log(msg):
    with open('cc_client.log','a',errors='ignore') as f:
        strTime = str(datetime.datetime.now())
        try:
            f.write(strTime+'\n'+msg+'\n')
        except:
            write_cc_log(traceback.format_exc())

class msg_manger:
    # define msg protocol format
    msg_blank = {
        'uuid':'',
        'type':'',
        'param':''
    }
    def get_blank_msg(self):
        return copy.deepcopy(self.msg_blank)
    def send_udp_msg(self, port, msg, destination):
        try:
            # udp send msg
            # send msg with my protocol
            msg = json.dumps(msg,separators=',:')
            msg = msg.encode('utf-8')
            msgLen = int(len(msg)).to_bytes(length=4, byteorder='big', signed=True)
            allByteData = msgLen + msg
            hasSend = 0
            lenMsg = len(allByteData)
            while (hasSend < lenMsg):
                nowSend = port.sendto(allByteData[hasSend:min(hasSend + 60000, lenMsg)], destination)
                time.sleep(0.0001)
                hasSend += nowSend
        except:
            write_cc_log(traceback.print_exc())
        # write_cc_log("complete send message: "+str(allByteData))

    def get_udp_msg(self):
        # udp get msg
        # get msg from udp client
        data, clientAddr = self._server.recvfrom(65535)
        msgLen = int.from_bytes(data[0:4], 'big')
        if (msgLen <= 0):
            write_cc_log('error occ_extured! msgLen less or equal zero!')
            return None
        count = len(data) - 4
        allMsg = data[4:len(data)]
        # write_cc_log("start to get message! length:",count)
        while count < msgLen:
            d, c = self._server.recvfrom(65535)
            if not c == clientAddr:
                continue
            nowLength = len(d)
            allMsg += d
            count += nowLength
        # write_cc_log("complete get message: "+str(allMsg))
        
        try:
            jsonMsg = json.loads(allMsg.decode())# decode msg format msg
        except:
            # msg not allow
            write_cc_log(traceback.print_exc())
            return ({},())
        return (jsonMsg, clientAddr)

    def __init__(self, server):
        self._server = server

class cc_func:
    def __init__(self, browser="chrome", server_ip = '127.0.0.1'):
        if (browser == "chrome"):
            self.__portServer = 54007
        elif (browser == "firefox"):
            self.__portServer = 54006
        else:
            print('browser not support!')
            sys.exit(-1)
        self.__addr = server_ip # 127.0.0.1
        self.__msgCallBackLock = _thread.allocate_lock()  # get msg lock
        self.__serverAddr = (self.__addr, self.__portServer)  # define server addr
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # udp socket
        self.__msg_engine = msg_manger(self.__client)
        self.regist_cc()
        self.__msgQueue = queue.Queue() # init msg queue
        self.__msgCallbacks = []
        _thread.start_new_thread(self.server_msg_listen_service, ())# start listen msg from cc server

    def regist_cc(self):
        # regist cc
        regMsg = self.__msg_engine.get_blank_msg()
        regMsg['type'] = 'register_cc'
        self.__msg_engine.send_udp_msg(self.__client, regMsg, self.__serverAddr)
        jsonMsg , addr = self.__msg_engine.get_udp_msg()
        self.__uuid = jsonMsg['uuid']

    def send_msg_to_server(self,msgType,param):
        msg_to_send = self.__msg_engine.get_blank_msg()
        msg_to_send['uuid'] = self.__uuid
        msg_to_send['type'] = msgType
        msg_to_send['param'] = param
        self.__msg_engine.send_udp_msg(self.__client, msg_to_send, self.__serverAddr)
    
    def execute_js(self, code):
        self.send_msg_to_server('client_execute_js',code)
    
    def get_msg_from_server(self, timeout = 0):
        msg = {}
        if timeout <= 0:
            msg = self.__msgQueue.get(block=True)
        else:
            while timeout > 0:
                start = time.time()
                try:
                    msg = self.__msgQueue.get(block=False)
                except queue.Empty:
                    pass
                time.sleep(0.5)
                timeout -= (time.time() - start)
        return msg

    def add_msg_server_callback(self, func):
        # add callback func
        self.__msgCallBackLock.acquire()
        self.__msgCallbacks.append(func)
        self.__msgCallBackLock.release()
    
    def remove_msg_server_callback(self, name, func):
        # remove callback func
        self.__msgCallBackLock.acquire()
        self.__msgCallbacks.remove(func)
        self.__msgCallBackLock.release()
    
    def server_msg_listen_service(self):
        while True:
            jsonMsg, addr = self.__msg_engine.get_udp_msg()
            if len(jsonMsg) > 0:
                self.__msgQueue.put(jsonMsg)
            for callback in self.__msgCallbacks:
                callback(jsonMsg)