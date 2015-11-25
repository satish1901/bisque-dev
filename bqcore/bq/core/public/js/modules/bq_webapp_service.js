/*******************************************************************************

  ModuleService is used by mini-apps for communication with the module server

  Tests the existance of the global var containing module def XML:
      module_definition_xml

  Possible configurations:
    onloaded   -
    onstarted  -
    ondone     -
    onprogress -
    onerror    -

  Example:



*******************************************************************************/


//----------------------------------------------------------------------------------
// misc
//----------------------------------------------------------------------------------

function ensureTrailingSlash(s) {
    if (s[s.length-1] === '/') return s;
    return s+'/';
}

function removeTrailingSlash(s) {
    if (s[s.length-1] != '/') return s;
    return s.substring(0, s.length-1);
}

//----------------------------------------------------------------------------------
// ModuleService - BQModuleConnector
//----------------------------------------------------------------------------------

function ModuleService(module_URI, conf) {
    this.URI = removeTrailingSlash(module_URI);
    this.conf = conf || {};

    // this global variable may be defined by the template and contain the module definition XML
    if (typeof module_definition_xml != 'undefined') {
        this.setModule( BQFactory.parseBQDocument(module_definition_xml) );
    } else {
        // fetch it otherwise
        BQFactory.request({ uri: this.URI+'/definition',
                            cb: callback(this, 'setModule'),
                            errorcb: callback(this, 'onerror'),
                            cache: false });
    }
}

ModuleService.prototype.setModule = function (module) {
    this.module = module;
    if (!this.module) {
        var message = "Module you are trying to load could not be found on the host system!\nPlease inform your bisque sysadmin!";
        this.emit_error(message);
        return;
    }

    if (this.conf.onloaded)
        this.conf.onloaded(this);
};

ModuleService.prototype.run = function (parameters) {

    // dima - needs rewriting according to the module inputs
    /*
    //if ('$gobjects' in parameters) {
    if ('gobject' in this.module.inputs_types) {
        var mex = new BQMex();
        //mex.status = 'PENDING';
        //mex.module = this.URI; //this.module.uri;
        //mex.addtag ({name:'client_server', value:client_server});
        for (var i in parameters) {

            //if (i == '$gobjects')
            if ('gobject' in this.module.inputs_index[i].type)
                mex.addtag({name:i, gobjects:parameters[i]});
            else
                mex.addtag({name:i, value:parameters[i]});
        }
        mex.save_(ensureTrailingSlash(this.URI) + 'execute', callback(this, 'checkMexStatus'), callback(this, 'onerror'));
    } else {
        var a = [];
        for (var i in parameters)
            a.push( ''+i+'='+encodeURIComponent(parameters[i]) );
        var uri = ensureTrailingSlash(this.URI) + 'execute?' + a.join("&");
        BQFactory.request({uri: uri, cb: callback(this, 'checkMexStatus'), errorcb: callback(this, 'onerror'), cache: false});
    }
    */

    var mex = this.module.createMEX();
    //var xml = mex.toXML();
    mex.save_(ensureTrailingSlash(this.URI) + 'execute', callback(this, 'onstarted'), callback(this, 'onerror'));
};

ModuleService.prototype.onstarted = function (mex) {
    if (this.conf.onstarted) this.conf.onstarted(mex);
    this.checkMexStatus(mex);
};

ModuleService.prototype.checkMexStatus = function (mex) {
    if (mex.status=="FINISHED" || mex.status=="FAILED") {
        if (this.conf.ondone) this.conf.ondone(mex);
    } else {
        if (this.conf.onprogress) this.conf.onprogress(mex);
        var me = this;
        setTimeout (function () { me.requestMexStatus(mex.uri); }, 5000);
    }
};

ModuleService.prototype.requestMexStatus = function(mex_uri) {
    BQFactory.request ({uri : mex_uri,
                        uri_params : { view: 'full'},
                        cb : callback(this, 'checkMexStatus'),
                        errorcb: callback(this, 'onerror'),
                        cache : false});
};

ModuleService.prototype.emit_error = function(message) {
    if (this.conf.onerror)
        this.conf.onerror(message);
    else
        alert(message);
};

ModuleService.prototype.onerror = function(o) {
    if (typeof(o)=='string')
        this.emit_error(o);
    else
        this.emit_error(o.message_short || o.message || o['http-error'] || 'communication error');
};

