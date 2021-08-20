
import socket
import _thread
import cc_server_ext as cc_ext
import datetime
import time
import traceback
import json
import copy
import sys
from uuid import uuid4

# todo: record user request time and delete unused user regularly

def write_cc_log(msg):
    with open('cc.log','a',errors='ignore') as f:
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

    # define server quit msg
    quitMsg = {
        'uuid':'last_server',
        'type':'new_server_come_in',
        'param':''
    }

    '''
    # define client infomation save format
    clients = {
        "uuid":{
        "addr":(),
        "last_request_time":16293523587
        }
    }
    '''
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
        write_cc_log("complete send message: "+str(allByteData))

    def get_udp_msg(self):
        # udp get msg
        # get msg from udp client
        data, clientAddr = self._server.recvfrom(65535)
        msgLen = int.from_bytes(data[0:4], 'big')
        if (msgLen <= 0):
            write_cc_log('error occ_extured! msgLen less or equal zero!')
            return
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
        write_cc_log("complete get message: "+str(allMsg))
        
        try:
            jsonMsg = json.loads(allMsg.decode())# decode msg format msg
        except:
            # msg not allow
            write_cc_log(traceback.print_exc())
            return ({},())
        return (jsonMsg, clientAddr)
    
    def send_msg_to_cc_plugin(self, msg):
        # send msg to cc_plugin
        try:
            cc_ext.sendMessage(cc_ext.encodeMessage(json.dumps(msg, separators=',:')))
        except:
            write_cc_log(traceback.print_exc())
    
    def get_msg_from_cc_plugin(self):
        # get msg from cc_plugin
        jsonMsg = {}
        try:
            msg = cc_ext.getMessage()
            decodeMsg = msg.decode()
            # decodeMsg = msg.decode().strip('"')
            # write_cc_log(decodeMsg)
            jsonMsg = json.loads(decodeMsg) # may cause exception...
        except:
            write_cc_log(traceback.print_exc())
            return jsonMsg
        return jsonMsg


    def __init__(self, server):
        self._server = server


class cc_service:
    _clients = {}
    _clients_thread_lock = _thread.allocate_lock() # prevent mutithread fault

    
    def __init__(self, serverAddr = ('127.0.0.1', 54007)):
        '''cc server init'''

        self._serverAddr = serverAddr
        self.clean_socket_bind() # prevent address conflict
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(serverAddr)
        self._msg_engine = msg_manger(self.server)
        write_cc_log('server bind!')
        _thread.start_new_thread(self.cc_plugin_listen_service,())
        self.udp_client_listen_service()

    def clean_socket_bind(self):
        # clean last server prevent address conflict
        socket_tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msg_tmp = msg_manger(socket_tmp)
        msg_tmp.send_udp_msg(socket_tmp, msg_tmp.quitMsg, self._serverAddr)
        socket_tmp.close()
        time.sleep(0.2) # wait a while

    def force_exit(self):
        """
        stop server prevent address conflict
        """
        write_cc_log('server unbind!')
        self.server.close()
        sys.exit(0)

    def add_client(self, jsonMsg, addr):
        # add client and return success msg
        uuid = str(uuid4())
        last_req_time = str(int(time.time()))
        new_client = {
            "addr":addr,
            "last_request_time":last_req_time
        }
        self._clients_thread_lock.acquire()
        self._clients[uuid] = new_client # add client
        self._clients_thread_lock.release()

        success_msg = self._msg_engine.get_blank_msg()
        success_msg['uuid'] = uuid
        success_msg['type'] = 'regist_success'
        success_msg['param'] = ''
        self._msg_engine.send_udp_msg(self.server, success_msg, addr) # tell client register success

    def check_client_msg(self, jsonMsg, clientAddr):
        uuid = jsonMsg.get('uuid')
        if not uuid or not self._clients.get(uuid):
            # do not send uuid or
            # uuid not exist in clients
            need_register_msg = self._msg_engine.get_blank_msg()
            need_register_msg['type'] = 'need_register'
            self._msg_engine.send_udp_msg(self.server, jsonMsg, clientAddr)
            return False
        return True

    def update_client_req_time(self, uuid):
        # should make sure client exist!
        # update client final request time
        self._clients_thread_lock.acquire()
        self._clients[uuid]['last_request_time'] = str(int(time.time()))
        self._clients_thread_lock.release()

    def delete_client(self, uuid):
        # should make sure client exist!
        # delete client
        self._clients_thread_lock.acquire()
        del self._clients[uuid]
        self._clients_thread_lock.release()

    def send_msg_to_client(self, uuid, msg):
        try:
            client = self._clients.get(uuid)
            if not client:
                return (False, 'NO CLIENT FOUND!')

            self._msg_engine.send_udp_msg(self.server,msg,client['addr'])
        except:
            write_cc_log(traceback.print_exc())
            return(False, traceback.print_exc())
        return (True, '')

    def cc_plugin_listen_service(self):
        # listen chrome cc_plugin msg
        while True:
            try:
                jsonMsg = self._msg_engine.get_msg_from_cc_plugin()
                if jsonMsg['uuid'] == 'last_server' and jsonMsg['type'] == 'new_server_come_in':
                    break
                result, reason = self.send_msg_to_client(jsonMsg['uuid'], jsonMsg)
                if not result:
                    write_cc_log(reason)
            except:
                write_cc_log(traceback.format_exc())
                break
        self.force_exit() # if this service failed server exit!

    def check_cc_connect(self, jsonMsg, clientAddr):
        self.check_client_msg(jsonMsg, clientAddr)

    def client_execute_js(self, jsonMsg, clientAddr):
        # send msg to cc_plugin
        if not self.check_client_msg(jsonMsg, clientAddr):
            return
        self._msg_engine.send_msg_to_cc_plugin(jsonMsg)

    def udp_client_listen_service(self):
        # listen udp client msg
        msg_type_func_dic = {
            'new_server_come_in':self.force_exit,
            'register_cc':self.add_client,
            'client_execute_js':self.client_execute_js,
            'check_service_connect':self.check_cc_connect,
        }
        while True:
            try:
                jsonMsg, clientAddr = self._msg_engine.get_udp_msg()
                if len(jsonMsg) == 0:
                    # invalid msg
                    continue
                if jsonMsg['uuid'] == 'last_server' and jsonMsg['type'] == 'new_server_come_in':
                    break
                func = msg_type_func_dic.get(jsonMsg['type']) # get function from msg type
                if func:
                    # equal switch case
                    func(jsonMsg, clientAddr)
            except ConnectionResetError as sb:
                pass
            except:
                write_cc_log(traceback.print_exc())
                break
        self.force_exit() # if this service not exist exit server



if __name__ == '__main__':
    cc_service()