console.log('cc_plugin inject!');

global_msg = {
    'uuid':'',
    'type':'',
    'param':''
}

let port = chrome.runtime.connect();

console.log = (function(o){
    return function(...argvs){
        global_msg.type = 'console_log';
        global_msg.param = JSON.stringify(argvs);
        // o.call(console,global_msg.param);
        port.postMessage(global_msg);
    }
})(console.log);

function execute_js(msg){
    eval(msg.param);
}

chrome.runtime.onMessage.addListener((msg)=>{
    global_msg.uuid = msg.uuid;
    switch(msg.type){
        case 'client_execute_js':{
            execute_js(msg);
            break
        }
        case 'set_uuid':{
            global_msg['uuid'] = msg.param;
        }
    }
});