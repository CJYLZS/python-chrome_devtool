import time
import cc.cc_client as ccc

if __name__ == '__main__':
    import os
    os.system('cls')
    def console_log(jsonMsg):
        if jsonMsg['type'] == 'console_log':
            for item in jsonMsg['param']:
                print(item, end=' ')
            print()
        elif jsonMsg['type'] == 'client_execute_js_result':
            print(jsonMsg['param'])
    ccf = ccc.cc_func()
    ccf.add_msg_server_callback(console_log)
    while 1:
        js_code = input('js>')
        if len(js_code) == 0:
            continue
        elif js_code == 'exit':
            break
        ccf.execute_js(js_code)
        time.sleep(0.2)