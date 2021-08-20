console.log('cc_plugin background!');
global_msg = {
    'uuid':'',
    'type':'',
    'param':''
}
let portToNative = chrome.runtime.connectNative("chrome_commucation");

function SendMsgToContent(tabId, msg) {
    chrome.tabs.sendMessage(tabId, msg);
}

function execute_js(msg){
    
    chrome.tabs.query({active:true},(tabs)=>{
        global_msg.uuid = msg.uuid;
        global_msg.type = 'set_uuid'
        global_msg.param = msg.uuid
        chrome.tabs.sendMessage(tabs[0].id, global_msg);
        chrome.tabs.executeScript(
            tabs[0].id,
            {code:msg['param']});
    });
}

portToNative.onMessage.addListener((response) => {
    let msg = JSON.parse(response);
    switch(msg['type']){
        case 'client_execute_js':{
            execute_js(msg);
            break
        }
    }
});

chrome.runtime.onConnect.addListener(
function (ScriptPort) {
    console.log("Connected with " + ScriptPort.sender.url);
    ScriptPort.onMessage.addListener((msg) =>{
        // console.log("FromScript: " + JSON.stringify(msg));
        portToNative.postMessage(msg);
    });
    ScriptPort.onDisconnect.addListener(function (sender) {
        //disconnect
    });
});

function all_page_reload(){
    chrome.tabs.query({},function(tabs){
        for(let i=0; i<tabs.length; i++){
            if(tabs[i].url.indexOf("http") != 0)continue;
            chrome.tabs.executeScript(tabs[i].id,{code:'document.location.reload();'})
        }
    });
}
all_page_reload();