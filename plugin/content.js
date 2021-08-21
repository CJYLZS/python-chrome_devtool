console.log('cc_plugin inject!');


// global msg define
global_msg = {
    'uuid':'',
    'type':'',
    'param':''
}

// port connect with background.js
let port = chrome.runtime.connect();



function execute_js(msg){
    // execute js in top page
    global_msg.type = msg.type;
    global_msg.param = `(()=>{${msg.param}})();`; // modify to (()=>{/** code */})();
    window.postMessage(global_msg);
}

chrome.runtime.onMessage.addListener((msg)=>{
    global_msg.uuid = msg.uuid;
    switch(msg.type){
        case 'client_execute_js':{
            execute_js(msg);
            break;
        }
    }
});

window.addEventListener('message',(event) => {
    if(event.source == window && event.data.type){
        switch(event.data.type){
            case 'client_execute_js_result':{
                port.postMessage(event.data);
                break
            }
            case 'console_log':{
                event.data.uuid = global_msg.uuid;
                port.postMessage(event.data);
                break
            }
        }
    }
});

let s = document.createElement('script');
s.innerHTML = 
`// global msg define
global_msg = {
    'uuid':'',
    'type':'',
    'param':''
}
console.log = (function(o){
    return function(...argvs){
        o.call(console,argvs);
        global_msg.type = 'console_log';
        global_msg.param = Array.from(argvs);
        window.postMessage(global_msg);
    }
})(console.log);
window.addEventListener('message',(event)=>{
    if(event.source == window && event.data.type == 'client_execute_js'){
        global_msg.uuid = event.data.uuid;
        try{
            global_msg.param = eval(event.data.param);
        }catch(e){
            global_msg.param = e.stack;
        }
        global_msg.type = 'client_execute_js_result';
        if(!global_msg.param)
            global_msg.param = 'undefined';
        window.postMessage(global_msg);
    }
});`
document.head.appendChild(s);