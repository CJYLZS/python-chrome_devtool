console.log('cc_plugin background!');
let portToNative = chrome.runtime.connectNative("chrome_commucation");

function SendMsgToContent(tabId, msg) {
    chrome.tabs.sendMessage(tabId, msg);
}

function execute_js(msg){
    if(msg.param.page_url){
        // execuet js in first page which found by url
        chrome.tabs.query({},(tabs)=>{
            let i = 0;
            for(; i<tabs.length; i++){
                if(tabs[i].url.indexOf(msg.param.page_url)!=-1){
                    msg.param = msg.param.code; // content js only need js code
                    chrome.tabs.sendMessage(tabs[i].id, msg);
                    break;
                }
            }
            if(i == tabs.length){
                console.error(msg.param.page_url, 'not page found!');
            }
        });
    }
    else{
        // if not refer url then execute js in active page
        chrome.tabs.query({active:true},(tabs)=>{
            chrome.tabs.sendMessage(tabs[0].id, msg);
        });
    }
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
    // console.log("Connected with " + ScriptPort.sender.url);
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