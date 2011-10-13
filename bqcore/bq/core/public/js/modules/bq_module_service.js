//  ModuleService is used by mini-apps for communication with the module server
//

function ensureTrailingSlash(s) {
    if (s[s.length-1] === '/') return s;
    return s+'/';
}

function removeTrailingSlash(s) {
    if (s[s.length-1] != '/') return s;
    return s.substring(0, s.length-1);
}

function ModuleService(module_URI, callbackDone, callbackProgress, callbackError) {
    this.URI = removeTrailingSlash(module_URI);
    this.callbackDone = callbackDone;
    this.callbackProgress = callbackProgress;
    this.callbackError = callbackError;
    //BQModule.queryModuleByName(this.name, callback(this, 'onModuleFound'));
    BQFactory.request({uri: this.URI+'/definition', cb: callback(this, 'setModule'), cache: false});
}

ModuleService.prototype.setModule = function (module) {
    this.module = module;
    if (this.module == null)
        alert( "No "+this.name+" found on host system!\nServer may need to be restarted\nPlease inform your bisque sysadmin!" );
}

ModuleService.prototype.run = function (parameters) {
  
//    if (this.module == null) {
//        alert('Module was not found on the host system, can not continue...');
//        return
//    }
//    var module = this.module.uri;
//    var rExp = /(http:\/\/.*\/)ds\/modules\/([0-9]+)/;
//    var module_host = module.replace(rExp, '$1');
//    var module_id   = module.replace(rExp, '$2');
//    var rExp2 = /\/*$/; //*/ // dmitry - my editor is dumb
//    var client_server = module_host.replace(rExp2,'');
    
   if ('$gobjects' in parameters) {
       var mex = new BQMex();
       //mex.status = 'PENDING';
       //mex.module = this.URI; //this.module.uri;
       //mex.addtag ({name:'client_server', value:client_server});
        for (var i in parameters) {
            if (i == '$gobjects') 
                mex.addtag({name:'$gobjects', gobjects:parameters[i]});
            else
                mex.addtag({name:i, value:parameters[i]});
        }
        mex.save_(ensureTrailingSlash(this.URI) + 'execute', callback(this, 'checkMexStatus'), callback(this, 'onerror'));
    } else {
        var a = [];       
        for (var i in parameters) a.push( ''+i+'='+encodeURIComponent(parameters[i]) );
        var uri = ensureTrailingSlash(this.URI) + 'execute?' + a.join("&");
        BQFactory.request({uri: uri, cb: callback(this, 'checkMexStatus'), errorcb: callback(this, 'onerror'), cache: false});
    }
}

ModuleService.prototype.checkMexStatus = function (mex) {
    if (mex.status=="FINISHED" || mex.status=="FAILED") {
        this.callbackDone(mex);
    } else {
        this.callbackProgress(mex);
        var me = this;
        setTimeout (function () { me.requestMexStatus(mex.uri); }, 5000);
    }
}

ModuleService.prototype.requestMexStatus = function(mex_uri) {
    BQFactory.request ({uri : mex_uri, 
                        cb : callback(this, 'checkMexStatus'),
                        cache : false});
}

ModuleService.prototype.onerror = function(o) {
    
    if (this.callbackError) 
        this.callbackError(o.message_short);
    else
        alert('Error occured while attempting an execution: \n'+o.message_short);
}

