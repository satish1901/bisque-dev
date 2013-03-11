
// Override several config options for default mask in Bisque
Ext.define('Ext.LoadMask', {
    override: 'Ext.LoadMask',
    
    constructor: function (comp, config) {
        config = Ext.applyIf( config || {}, {shadow: false, floating: true,} );
        this.callParent([comp, config]);
    },
});
      
// ADD SOME GLOBAL VARS HERE TO KEEP OUR FILE LIST SHORT
// for conformity sake:
// paths will NOT end in a '/' slash
//var server = 'arno.ece.ucsb.edu:8080';
//var fullurl = server  + '/bisquik';

var svgns  = "http://www.w3.org/2000/svg";
var xlinkns  = "http://www.w3.org/1999/xlink";
var xhtmlns = 'http://www.w3.org/1999/xhtml';

// <![CDATA[

// Create a method callback on a javascript objects.
// Used for event handlers binding an object instance
// to a method invocation.
// Usage:
//  on_event =  callback (m, 'some_method' [, arg1, ... ])
// When the event fires the callback will be called with
// both the static arguments and the dynamic arguments provided
// by the event
// Example:
//   m.some_method([arg1, arg,..., evt_arg1, evt_arg2, ...])
//
function callback(obj, method) {
    var thisobj = obj;
    var thismeth = ( typeof method == "string") ? thisobj[method] : method;
    var thisextra = Array.prototype.slice.call(arguments, 2);

    return function() {
        var args = Array.prototype.slice.call(arguments);
        return thismeth.apply(thisobj, thisextra.concat(args));
    };
}

function evaluateXPath(aNode, aExpr)
{
    var xpe = new XPathEvaluator();
    var nsResolver = xpe.createNSResolver(aNode.ownerDocument == null ?
      aNode.documentElement : aNode.ownerDocument.documentElement);
    var result = xpe.evaluate(aExpr, aNode, nsResolver, 0, null);
    var found = [];
    var res;
    while (res = result.iterateNext())
      found.push(res);
    return found;
}

function evaluateXPathIE(aNode, aExpr)
{
    var nodes = aNode.selectNodes(aExpr);
    var found = [];

    for (var i=0; i<nodes.length; i++)
        found.push(nodes[i]);

    return found;
}

// Use IE specific code for XPath evaluation
if (Ext.isIE)
    evaluateXPath = evaluateXPathIE; 

// clean up an XML/HTML node by removing all its children nodes
function removeAllChildren(element) {
    while (element.hasChildNodes()) {
        element.removeChild(element.firstChild);
    }
}

// Test if the input object is empty
function isEmptyObject(obj)
{
    return (!Ext.isDefined(obj)) ? true : Object.keys(obj).length === 0;
}


function getX(obj) {
    var curleft = 0;
    while (obj.offsetParent) {
        curleft += obj.offsetLeft;
        obj = obj.offsetParent;
    }
    return curleft;
}

function getY(obj) {
    var curtop = 0;
    while (obj.offsetParent) {
        curtop += obj.offsetTop;
        obj = obj.offsetParent;
    }
    return curtop;
}

function getObj(name)
{
    return document.getElementById(name);
}

function attribDict(node) {
    var d = {};
    var al = node.attributes;
    var i = 0;
    for ( i = 0; i < al.length; i += 1) {
        d[al[i].name] = al[i].value;
    }
    return d;
}

function attribInt(node, a) {
    var v = node.getAttribute(a);
    return v ?  parseInt(v, 10): null;
}

function attribFloat(node, a) {
    var v = node.getAttribute(a);
    return v ? parseFloat(v) : null;
}

function attribStr(node, a) {
    return node.getAttribute(a);
}

function getElement(event) {
    return event.target || event.srcElement;
}

function printXML(node) {
    var xml = "", i = 0, m, at;

    if (node !== null) {
        xml = "<" + node.tagName;
        at = node.attributes;
        if (at) {
            for ( i = 0; i < at.length; i += 1) {
                xml += " " + at[i].name + "=\"" + at[i].value + "\"";
            }
        }
        if (node.hasChildNodes) {
            xml += ">\t";
            for ( m = node.firstChild; m !== null; m = m.nextSibling) {
                xml += printXML(m);
                //m.nodeName +  ";   " ;
            }
            xml += "</" + node.tagName + ">\n";
        } else if (node.value) {
            xml += " value=\"" + node.value + "\"/>\n";
        } else if (node.text) {
            xml += ">" + node.text + "</" + node.tagName + ">\n";
        } else {
            xml += " />\n";
        }
    }
    return xml;
}

// threadsafe asynchronous XMLHTTPRequest code
function makeRequest(url, callback, callbackdata, method, postdata, errorcb) {
    function bindCallback() {
        if (ajaxRequest.readyState === XMLHttpRequest.DONE) {
            //clog ("ajaxRequest.readyState == 4 and status: " + ajaxRequest.status);
            BQSession.reset_timeout();
            if (ajaxRequest.status === 200 || ajaxRequest.status === 0) {
                if (ajaxCallback) {
                    if (ajaxRequest.responseXML !== null) {// added to accomodate HTML requests as well as XML requests
                        ajaxCallback(ajaxCallbackData, ajaxRequest.responseXML);
                    } else {
                        ajaxCallback(ajaxCallbackData, ajaxRequest.responseText);
                    }
                } else {
                    clog("makeRequest - no callback defined: " + url);
                }
            } else {
                var consumed_status = {
                    401 : undefined,
                    403 : undefined,
                    404 : undefined
                };
                var error_short = ("There was a problem with the request:\n" + ajaxRequest.status + ":\t" + ajaxRequest.statusText + "\n");
                var error_str = (error_short + ajaxRequest.responseText);

                if (ajaxRequest.status === 401 || ajaxRequest.status === 403)
                    error_str = "You do not have permission for this operation\nAre you logged in?\n\n" + url;
                else if (ajaxRequest.status === 404)
                    error_str = "Requested resource does not exist:\n" + url;

                if (ajaxCallbackError) {
                    ajaxCallbackError({
                        request : ajaxRequest,
                        message : error_str,
                        message_short : error_short
                    });
                    //throw(error_str);
                    return;
                }

                if (ajaxRequest.status in consumed_status) {
                    //alert(error_str);
                    BQ.ui.error(error_str);
                    return;
                }

                BQ.ui.error(error_str);
                //throw(error_str);
            }
        }
    }

    // use a local variable to hold our request and callback until the inner function is called...
    var ajaxRequest = null;
    var ajaxCallbackData = callbackdata;
    var ajaxCallback = callback;
    var ajaxCallbackError = errorcb;

    try {
        if (window.XMLHttpRequest) {
            ajaxRequest = new XMLHttpRequest();
            ajaxRequest.onreadystatechange = bindCallback;
            if (method == "get" || method == "delete") {
                ajaxRequest.open(method, url, true);
                ajaxRequest.send(null);
            } else {
                ajaxRequest.open(method, url, true);
                //ajaxRequest.setRequestHeader("Content-Type","application/x-www-form-urlencoded; charset=UTF-8");
                ajaxRequest.setRequestHeader("Content-Type", "text/xml");
                ajaxRequest.send(postdata);
            }
            return ajaxRequest;
        }
    } catch (e) {
        clog("Exception in Ajax request: " + e.toString());
    }
}

// Will call on response will call cb (xmldata)

function xmlrequest(url, cb, method, postdata, errorcb) {
    function checkResponse() {
        if (ajaxRequest.readyState === XMLHttpRequest.DONE) {
            BQSession.reset_timeout();
            if (ajaxRequest.status === 200) {
                if (ajaxRequest.callback) {
                    if (ajaxRequest.responseXML !== null) {
                        // added to accomodate HTML requests
                        // as well as XML requests
                        ajaxRequest.callback(ajaxRequest.responseXML);
                    }
                    else {
                        clog('WARNING: xmlrequest return text/html');
                        ajaxRequest.callback(ajaxRequest.responseText);
                    }
                }
                else {
                    clog("xmlrequest - no callback defined: " + url);
                }
            } else {
                var error_short = "There was a problem with the request:\n";
                if (ajaxRequest.request_url)
                    error_short += 'URL: ' + ajaxRequest.request_url + '\n';
                error_short += 'Status: ' + ajaxRequest.status + '\n';
                error_short += 'Message: ' + ajaxRequest.statusText + '\n';
                var error_str = (error_short + ajaxRequest.responseText);

                var consumed_status = {401 : undefined, 403 : undefined, 404 : undefined,};
                if (ajaxRequest.status === 401) {
                    //error_str = "You do not have permission for this operation\nAre you logged in?\n\n"+url;
                    window.location = "/auth_service/login?came_from=" + window.location;
                }  else if (ajaxRequest.status === 403) {
                    error_str = "You do not have permission for this operation:\n" + url;                    
                } else if (ajaxRequest.status === 404) {
                    error_str = "Requested resource does not exist:\n" + url;
                }

                if (ajaxRequest.errorcallback) {
                    ajaxRequest.errorcallback({
                        request : ajaxRequest,
                        message : error_str,
                        message_short : error_short
                    });
                }

                // Utkarsh : This shouldn't be called again if a default_error_callback is configured for all requests
                //           Leads to two error message popups                     
                //BQ.ui.error(error_str);
                
                //throw(error_str);
            }
        }
    }

    var ajaxRequest = null;
    try {
        if (window.XMLHttpRequest) {
            ajaxRequest = new XMLHttpRequest();
            ajaxRequest.onreadystatechange = checkResponse;
            ajaxRequest.callback = cb;
            ajaxRequest.errorcallback = errorcb;
            ajaxRequest.request_url = url;
            method = method || "get";
            ajaxRequest.open(method, url, true);
            ajaxRequest.setRequestHeader('Accept', 'text/xml');

            if (method === "get" || method === "delete") {
                ajaxRequest.send(null);
            } else {
                //ajaxRequest.setRequestHeader("Content-Type",
                //"application/x-www-form-urlencoded; charset=UTF-8");
                ajaxRequest.setRequestHeader("Content-Type", "text/xml");
                ajaxRequest.send(postdata);
            }
            return ajaxRequest;
        }
    } catch (e) {
        clog("Exception in Ajax request: " + e.toString());
    }
}

function chainRequest(ajaxRequest, cb) {
    var first = ajaxRequest.callback;
    var second = cb;
    function chain(data) {
        first(data);
        second(data);
    }
    ajaxRequest.callback = chain;
}

function clog(str) {
    if ( typeof (window['console']) != "undefined") {
        var name = arguments.callee.caller.$name || arguments.callee.caller.name;
        var owner = null;
        try {
            name = arguments.callee.caller.caller.$name || arguments.callee.caller.caller.name;
            owner = arguments.callee.caller.caller.$owner.$className;
        } catch(err) {
            // do nothing really
        }
        var caller = '';
        if (name)
            caller = name + ': ';
        if (owner)
            caller = owner + '.' + caller;
        console.log(caller + str);
    }
}

encodeParameters = function(obj) {
    var params = new Array();
    for (key in obj) {
        if (obj[key]) {
            params.push(key + "=" + encodeURIComponent(obj[key]));
        }
    }
    return params.join('&');
}

if (!Array.prototype.reduce) {
    Array.prototype.reduce = function(fun /*, initial*/) {
        var len = this.length;
        if ( typeof fun != "function")
            throw new TypeError();

        // no value to return if no initial value and an empty array
        if (len == 0 && arguments.length == 1)
            throw new TypeError();

        var i = 0;
        if (arguments.length >= 2) {
            var rv = arguments[1];
        } else {
            do {
                if ( i in this) {
                    rv = this[i++];
                    break;
                }

                // if array contains no values, no initial value to return
                if (++i >= len)
                    throw new TypeError();
            } while (true);
        }

        for (; i < len; i++) {
            if ( i in this)
                rv = fun.call(null, rv, this[i], i, this);
        }

        return rv;
    };
}
if (!Array.prototype.forEach) {
    Array.prototype.forEach = function(fun /*, thisp*/) {
        var len = this.length >>> 0;
        if ( typeof fun != "function")
            throw new TypeError();

        var thisp = arguments[1];
        for (var i = 0; i < len; i++) {
            if ( i in this)
                fun.call(thisp, this[i], i, this);
        }
    };
}

Array.prototype.find = function(searchStr) {
    var returnArray = false;
    for (var i = 0; i < this.length; i++) {
        if ( typeof (searchStr) == 'function') {
            if (searchStr.test(this[i])) {
                if (!returnArray) {
                    returnArray = []
                }
                returnArray.push(i);
            }
        } else {
            if (this[i] === searchStr) {
                if (!returnArray) {
                    returnArray = []
                }
                returnArray.push(i);
            }
        }
    }
    return returnArray;
}
if (!String.prototype.startswith) {
    String.prototype.startswith = function(input) {
        return this.substr(0, input.length) === input;
    }
}
function extend(child, supertype) {
    child.prototype.__proto__ = supertype.prototype;
}

function isdefined(variable) {
    return ( typeof (window[variable]) == "undefined") ? false : true;
}

// ]]>

/*-----------------------------------------------------------------------------
 BQAPI - JavaScript Bisque API
 
 dima: problems i see today
   1) no way to tell if object is completely loaded or needs additional fetches
   2) lot's of repeated functions: load_tags, loadTags, etc...
   3) some objects have non-standard attributes: BQAuth
-----------------------------------------------------------------------------*/

BQTypeError = new Error("Bisque type error");
BQOperationError = new Error("Bisque operation error");

/* //dima - not being used, hiding from the parser
classExtend = function(subClass, baseClass) {
   function inheritance() {}
   inheritance.prototype = baseClass.prototype;

   subClass.prototype = new inheritance();
   subClass.prototype.constructor = subClass;
   subClass.baseConstructor = baseClass;
   subClass.superClass = baseClass.prototype;
}
*/

default_error_callback = function (o) {
    clog(o.message);
    BQ.ui.error(o.message); 
}

//-----------------------------------------------------------------------------
// BQFactory for creating Bisque Objects
//-----------------------------------------------------------------------------

function BQFactory (){}
BQFactory.ctormap =  { 
                       //vertex  : BQVertex, // dima: speed optimization, using xpath for sub vertices is much faster
                       //value   : BQValue,  // dima: speed optimization, using xpath for sub values is much faster
                       tag      : BQTag,
                       image    : BQImage,
                       file     : BQFile,
                       gobject  : BQGObject,
                       point    : BQGObject,
                       rectangle: BQGObject,
                       ellipse  : BQGObject,
                       polygon  : BQGObject,
                       polyline : BQGObject,
                       circle   : BQGObject,
                       label    : BQGObject,
                       module   : BQModule,
                       mex      : BQMex,
                       session  : BQSession,
                       user     : BQUser,
                       auth     : BQAuth,
                       dataset  : BQDataset,
                       resource : BQResource,
                       template : BQTemplate,
};

BQFactory.ignored = {
    vertex  : BQVertex,
    value   : BQValue,
};

BQFactory.escapeXML = function(xml) {
    var specials = [ [ /</g,  "&lt;"],
                     [ />/g,  "&gt;"],
                     [ RegExp("'", 'g') , '&#039;'],
                     [ RegExp('"','g') ,  '&quot;']
                   ] ;
    // Replace Bare & (not followed 
    xml = String(xml).replace (/&/g, '&amp;');
    specials.every (function (pair) {
        xml = xml.replace (pair[0], pair[1]);
        return true;
    });
    return xml;
}

BQFactory.session = {};

BQFactory.make = function(ty, uri, name, value) {
    var ctor = BQResource;
    if (ty in BQFactory.ctormap) 
        ctor = BQFactory.ctormap[ty];
    o =  new ctor(uri);
    if (ctor == BQResource && ty) o.resource_type = ty;
    o.name = name;
    o.value = value;
    return o;
}

BQFactory.createFromXml = function(xmlResource, resource, parent) {
    var stack = [];
    var resources = [];
    //  Initialize stack with a tuple of 
    //    1. The XML node being parsed
    //    2. The current resource being filled out
    //    3. The parent resource if any
    stack.push ([xmlResource, resource, parent]);
    while (stack.length != 0) {
        var elem = stack.shift();
        var node = elem[0];
        var resource  = elem[1];
        var parent = elem[2];
        var type_ = node.nodeName;
        if (resource == null){
            if (type_ == 'resource') 
               type_ = attribStr(node, 'type');
            resource = BQFactory.make(type_);
        }
        resource.initializeXml(node);
        resources.push (resource);
        if (parent) {
            resource.setParent(parent) ;
            resource.doc = parent.doc;
        }
        for (var i=0; i < node.childNodes.length; i++ ) {
            var k = node.childNodes[i];
            if (k.nodeType == 1 &&  ! (k.nodeName in BQFactory.ignored)) // Element nodes ONLY
                stack.push ( [ k, null, resource ]);
            //else
            //    clog ("Got Node type" + k.nodeType + " for " + k.text);
        }
    }

    response = resources[0];

    // dima: do some additional processing after you inited elements    
    var rr = resources.reverse();       
    for (var p=0; (r=rr[p]); p++)
        if (r.afterInitialized) r.afterInitialized(); 
    
    return response;
}


/** 
 * Load a Bisque URL as an object. Calls cb (loaded_object) when done.
 * Checks for both outstanding ajax requests and previously loaded objects.
 */
BQFactory.load = function(uri, cb, progresscb, cache) {
    BQFactory.request({ uri : uri, 
                        cb  : cb,
                        progresscb: progresscb,
                        cache : cache});
};

BQFactory.request = function(params) {
    var uri =  params.uri;
    var url_params = params.uri_params;
    var cb  =  params.cb;
    var progresscb = params.progresscb;
    var cache = (typeof params.cache=="undefined")?true:false;
    var method = params.method || "get";
    var xmldata = params.xmldata;
    params.errorcb = params.errorcb || default_error_callback;    

    if (url_params) {
        var pl = [];
        var v;
        for (var x in url_params) {
            if (url_params[x]) {
                v = encodeURIComponent(url_params[x])
                pl.push(x+'='+v);
            } else {
                pl.push(x);
            }
        }
        if ( uri.indexOf('?')==-1 )
            uri = uri + '?' + pl.join('&');
        else
            uri = uri + '&' + pl.join('&');            
    }

    clog ("Loading: " + uri);
    if (! uri) {
        clog("ERROR: trying to load null uri");
    }
    // if (cache && uri in BQFactory.session) {
    //     var o = BQFactory.session[uri];
    //     if (o instanceof XMLHttpRequest) {
    //         clog ("outstanding request");
    //         if (cb) 
    //             chainRequest(o, callback(BQFactory, 'loaded_callback', uri, cb));
    //     } else {
    //         //clog ("using cache result");
    //         //if (cb) cb(o);
    //         // Just redo the request
    //         clog ('re-issuing cached result ' + uri);
    //         BQFactory.session[uri] = xmlrequest(uri, callback(BQFactory, 'on_xmlresponse', params), method, xmldata, params.errorcb);
    //     }
    // } else {
        BQFactory.session[uri] = xmlrequest(uri, callback(BQFactory, 'on_xmlresponse', params), method, xmldata, params.errorcb);
//}
};

BQFactory.loaded_callback = function (uri, cb, xmldoc) {
    clog ("Loaded callback for " + uri);
    var o = BQFactory.session[uri];
    cb (o);
};

BQFactory.on_xmlresponse = function(params, xmldoc) {
    var uri = params.uri;
    var cb  = params.cb;
    var errorcb = params.errorcb;
    
    clog('Response: ' + uri);
    try { 
        var n = xmldoc.firstChild;
        if (!n) return null;
        if (n.nodeName == 'response') 
        n = n.firstChild;
        if (!n) return null;        
        var ty = n.nodeName;
        if (ty=='resource') ty = attribStr(n, 'type');
        var bq = BQFactory.make (ty, uri);
        BQFactory.createFromXml(n, bq, null);
        bq.doc = bq;
        BQFactory.session[uri] = bq;
    } catch  (err) {
        clog ("on_xmlresponse error" + err);
        if (errorcb) errorcb ({ xmldoc : xmldoc, message : 'parse error in BQFactory.on_xmlresponse' });
        return;
    }
    if (cb)
        return cb(bq);    
}

BQFactory.parseBQDocument = function (xmltxt) {
    var parser  = new DOMParser ();
    xmldoc = parser.parseFromString(xmltxt, "text/xml");
    var n = xmldoc.firstChild;
    if (!n) return null;
    if (n.nodeName == 'response') 
        n = n.firstChild;
    if (!n) return null;        
    var ty = n.nodeName;
    var bq = BQFactory.make (ty);
    BQFactory.createFromXml(n, bq, null);
    bq.doc = bq;
    return bq;
}

//-----------------------------------------------------------------------------
// BQValue
//-----------------------------------------------------------------------------

function parseValueType(v, t) {
    try {
        if (t && typeof v === 'string' && t == 'number') 
            return parseFloat(v);
        else if (t && t == 'boolean') 
            return (v=='true') ? true : false;
    } catch(err) {
        return v;          
    }
    return v;    
}

function BQValue (t, v, i) {
    this.resource_type = "value";
    this.xmlfields = [ 'type', 'index' ];
    if (Ext.isElement(t) && arguments.length==1) {
        this.initializeXml(t);
        return;       
    }

    if (t != undefined) this.type = t;
    if (v != undefined) this.value = parseValueType(v, this.type);    
    if (i != undefined) this.index = i;       
}
BQValue.prototype = new BQXml();

BQValue.prototype.initializeXml = function (node) {
    this.type  = attribStr(node, 'type');
    this.value = parseValueType(node.textContent || node.text, this.type);
    this.index = attribInt(node, 'index');    
}

BQValue.prototype.setParent = function (p) {
    p.values = p.values || [];
    p.values.push(this);
}

BQValue.prototype.xmlNode = function () {
    return BQXml.prototype.xmlNode.call (this, BQFactory.escapeXML(this.value));
}

//-----------------------------------------------------------------------------
// BQVertex
//-----------------------------------------------------------------------------

function BQVertex(x, y, z, t, ch, index) {
    this.resource_type = "vertex";
    this.xmlfields = [ 'x', 'y', 'z', 't', 'ch', 'index' ];
    if (Ext.isElement(x) && arguments.length==1) {
        this.initializeXml(x);
        return;       
    }    
    this.x =x;
    this.y =y;
    this.z =z;
    this.t =t;
    this.ch =ch;
    this.index = index;
}
BQVertex.prototype = new BQXml();

BQVertex.prototype.setParent = function (p) {
    p.vertices = p.vertices || [];
    p.vertices.push(this);
}

BQVertex.prototype.initializeXml = function (node) {
    this.x     = attribFloat(node, "x");
    this.y     = attribFloat(node, "y");
    this.z     = attribFloat(node, "z");
    this.t     = attribFloat(node, "t");
    this.ch    = attribInt(node, "ch");
    this.index = attribInt(node, "index");
}


//-----------------------------------------------------------------------------
// BQXml
//-----------------------------------------------------------------------------

function BQXml() {
    this.resource_type = '';
    this.xmlfields = [];
}

BQXml.prototype.toXML = function (){ 
    return this.xmlNode ();
}

BQXml.prototype.xmlNode = function (content) {
    var v = '<' + this.resource_type + ' ';
    var fields = this.xmlfields;
    for (var f in fields ){
        if (this[fields[f]] != undefined  &&  this[fields[f]] != null )
        v += (fields[f] + '="' + BQFactory.escapeXML(this[fields[f]]) + '" ');
    }
    if (content && content != "") {
        v += ">";
        v += content;
        v += "</" + this.resource_type +">"
    } else {
        v += "/>";
    }

    return v;
}

//-----------------------------------------------------------------------------
// BQObject
// BQObject interface library for Image, Tags and GObjects.
// BQObject is base class for manipulation, and communication with
// the bisque system from javascript.
//-----------------------------------------------------------------------------

function BQObject (uri, doc) {
    BQXml.call(this, uri, doc);
    this.readonly = false;
    this.uri = uri;
    this.doc = doc || this;    
    
    this.children = [];
    this.tags     = [];
    this.gobjects = [];
    
    // object rationalization, any taggable may have values and vertices, use undefined to mark unfetched lists
    this.values   = undefined;
    this.vertices = undefined;

    this.dirty = true;
    this.created = true;
    this.mex = null;
    this.resource_type = 'resource';
    this.xmlfields  = [ 'type', 'name', 'value', 'uri', 'owner', 'permission', 'ts', 'resource_uniq', 'index', 'hidden'];
}
BQObject.prototype = new BQXml();

BQObject.prototype.initializeXml = function (node) {
    
    this.resource_type = attribStr(node, 'resource_type') || node.nodeName;
    this.type          = attribStr(node, 'type');
    this.name          = attribStr(node, 'name');
    this.value         = parseValueType(attribStr(node, 'value'), this.type);
    this.uri           = attribStr(node, 'uri');
    this.owner         = attribStr(node, 'owner');
    this.permission    = attribStr(node, 'permission');
    this.ts            = attribStr(node, 'ts');
    this.resource_uniq = attribStr(node, 'resource_uniq');
    this.index         = attribStr(node, 'index');
    this.hidden        = attribStr(node, 'hidden');
    this.attributes    = attribDict (node);
    this.dirty         = false;
    this.created       = false;
    this.template      = {};
    
    // dima: speed optimization, using xpath for resources with many values is much faster
    // Utkarsh : now uses evaulateXPath from utils.js, which is browser independent
    var values = evaluateXPath(node, 'value');
    this.values = [];
    
    // values should be an array
    for (var i=0; i<values.length; i++)
        this.values.push(new BQValue(values[i]));
    
    if (this.resource_uniq) {
        this.src  = '/blob_service/' + this.resource_uniq;
        // in the case the data is coming from another server, make sure to load proper URL
        this.src = this.uri.replace(/\/data_service\/.*$/i, this.src);
    }
}

BQObject.prototype.afterInitialized = function () {
    // try to set template
    
    // first try to find a resource "template"
    var ta = this.find_children('template');
    if (ta && ta instanceof Array && ta.length>0)
        this.template = ta[0].toDict(true);
    else if (ta)
        this.template = ta.toDict(true);
    
    if (this.template) return;

    // then look for tags "template" - old style
    ta = this.find_tags('template');
    if (ta && ta instanceof Array && ta.length>0)
        this.template = ta[0].toDict(true);
    else if (ta)
        this.template = ta.toDict(true);
}


// dima: this function takes an array of strings or an object value_name - value_type and 
//       sets as a new array of values in the resource
BQObject.prototype.setValues = function (vals) {
    if (this.readonly) 
        throw "This object is read only!";
    
    this.values = [];
    if (vals instanceof Array) {
        for (var i=0; i<vals.length; i++)
            this.values.push(new BQValue(undefined, vals[i]));
    } else {
        for (var i in vals)
            this.values.push(new BQValue(vals[i], i));
    }
}

BQObject.prototype.testReadonly = function () {
  if (this.readonly)
      throw "This object is read only!";
}

BQObject.prototype.setParent = function (p) {
    p.children = p.children || [];
    p.children.push (this);
    this.parent = p;
}

BQObject.prototype.getkids = function (){
    // Note concat make new array
    var allkids = this.children.concat( this.tags, this.gobjects);
    return allkids;
}

BQObject.prototype.load = function (uri, cb) {
    this.uri = uri;
    makeRequest(this.uri, callback(this, 'load_response', cb), null, "get");
}
BQObject.prototype.load_response = function (cb, ign, xmldoc) {
    // Reach past response object.
    //var node = xmldoc.firstChild.firstChild;
    var node = xmldoc.firstChild;
    if (node.nodeName == "response") 
        node = node.firstChild;
    BQFactory.createFromXml(node, this, null)
    if (cb)
        cb(this);
}

BQObject.prototype.toXML = function() {
    var xmlrep = '';
    if (this.values)
        for (var i=0; i < this.values.length; i++ ) 
            xmlrep += this.values[i].xmlNode();
    if (this.vertices)
        for (var i=0; i < this.vertices.length; i++ ) 
            xmlrep += this.vertices[i].xmlNode();            
    if (this.tags)
        for (var i=0; i < this.tags.length; i++ ) 
             xmlrep += this.tags[i].toXML();
    if (this.gobjects)         
        for (var i=0; i < this.gobjects.length; i++ ) 
             xmlrep += this.gobjects[i].toXML();
    if (this.children)
        for (var i=0; i < this.children.length; i++ ) 
            xmlrep += this.children[i].toXML();
    return this.xmlNode(xmlrep);
}

BQObject.prototype.delete_ = function (cb, errorcb) {
    this.testReadonly();
    // Delete object from db
    if (this.uri != null) {
        xmlrequest(this.uri, callback(this, 'response_', 'delete', errorcb, cb), 'delete', null, errorcb);
    }
}

BQObject.prototype.rename = function(newName, cb, errorcb) {
    clog ('BQAPI: BQObject.prototype.rename - Not implemented');
}

BQObject.prototype.deleteTag = function(childTag, cb, errorcb) {
    if (childTag instanceof BQTag)
    {
        this.remove(childTag);
        childTag.delete_(cb, errorcb);
    }
    else
        clog ('BQAPI: deleteTag - Input is not a BQTag.');
}

BQObject.prototype.find_tags  = function (name, deep, found) {
    found = found || [];
    for (var i=0; i < this.tags.length; i++) {
        var t = this.tags[i];
        if (t.name == name) 
            found.push( t );
        if (deep && t.tags.length >0 ) 
            t.find_tags (name, deep, found);
    }
    if (found.length == 0) 
        return null;
    if (found.length == 1) 
        return found[0];
    return found;
}

BQObject.prototype.find_children  = function (type, name, deep, found) {
    found = found || [];
    for (var i=0; i < this.children.length; i++) {
        var t = this.children[i];
        if (t.resource_type == type && (!name || name && t.name == name))
            found.push( t );
        if (deep && t.children.length >0 ) 
            t.find_children (type, name, deep, found);
    }
    if (found.length == 0) 
        return null;
    if (found.length == 1) 
        return found[0];
    return found;
}

// findTags         :   finds tags whose (input) attribute matches an input value
// config params    : 
// attr         =   (required) which attribute to match e.g. name, type, resource_type etc.
// value        =   (required) matched value
// deep         =   (default false) if the search should be deep or not
// returnFirst  =   (default true) True to return first found instance otherwise returns all instances

BQObject.prototype.findTags = function(config)
{
    var found = [], currentObj;
    config.returnFirst = Ext.isDefined(config.returnFirst)?config.returnFirst:true;
    
    for (var i=0; i<this.tags.length; i++)
    {
        currentObj = this.tags[i];
        if (currentObj[config.attr] == config.value)
        {
            found.push(currentObj)
            if (config.returnFirst)
                break;
        }
        else if (config.deep)
            found = found.concat(currentObj.findTags(config))
    }
    
    return found;
}

BQObject.prototype.testAuth = function(user, cb, loaded, authRecord)
{
    if (!loaded)
        if (user == this.owner)
            cb('owner');
        else
            this.getAuth(Ext.bind(this.testAuth, this, [user, cb, true], 0));
    else
    {
        authRecord = authRecord.children;
        
        for (var i=0;i<authRecord.length;i++)
        {
            if (authRecord[i].user == user)
            {
                if (authRecord[i].action=='edit' || authRecord[i].action=='owner')
                    cb(true);
                else
                    cb(false, authRecord[i].action);
                return;
            }
        }
        
        // no user matching the uri was found
        cb(false);
    }
}

BQObject.prototype.getAuth = function(cb, loaded, authRecord)
{
    if (!loaded)
    {
        BQFactory.request({
            uri :   this.uri + '/auth',
            cb  :   Ext.bind(this.getAuth, this, [cb, true], 0)
        });
    }
    else
        cb(authRecord);
}

BQObject.attributes_skip = { 'uri':undefined, 'src':undefined, 'permission':undefined, 
                             'ts':undefined, 'owner':undefined, 'parent':undefined, 
                             'doc':undefined, 'mex':undefined,  };
BQObject.types_skip = { 'template':undefined, };

function clean_resources(resource, skiptemplate) {
    // remove undesired attributes
    for (var i in resource)
        if (i in BQObject.attributes_skip || (skiptemplate && i=='template'))
            delete resource[i];

    // remove old style template - kept for compatibility, should disappear in the future
    if (skiptemplate && resource.tags) {
        var p=resource.tags.length-1;
        while (p>=0) {
            var t = resource.tags[p];
            if (t.type in BQObject.types_skip)
                resource.tags.splice(p, 1);
            p--;
        }
    }

    // remove template objects
    if (skiptemplate && resource.children) {
        var p=resource.children.length-1;
        while (p>=0) {
            var t = resource.children[p];
            if (t.resource_type in BQObject.types_skip)
                resource.children.splice(p, 1);
            p--;
        }
    }
    
    var r = undefined;
    for (var p=0; (r=resource.tags[p]); p++)
        clean_resources(r, skiptemplate);
    
    for (var p=0; (r=resource.gobjects[p]); p++)
        clean_resources(r, skiptemplate);
    
    for (var p=0; (r=resource.children[p]); p++)
        clean_resources(r, skiptemplate);        
}

BQObject.prototype.clone = function (skiptemplate) {
    var resource = Ext.clone(this);
    clean_resources(resource, skiptemplate);
    return resource;
}

BQObject.prototype.toDict  = function (deep, found, prefix) {
    deep = deep || false;
    found = found || {};
    prefix = prefix || '';
    
    var t=null;
    for (var p=0; (t=this.tags[p]); p++) {
        
        var values = undefined;
        if (t.values && t.values.length>0) {
            values = [];
            for (var i=0; (v=t.values[i]); i++)
               values.push(v.value);
        }
        
        if (!(prefix+t.name in found)) {   
            found[prefix+t.name] = values?values:t.value;
        } else {
            if (found[prefix+t.name] instanceof Array) {
                if (!values) 
                    found[prefix+t.name].push(t.value);
                else
                    found[prefix+t.name] = found[prefix+t.name].concat(values);
            } else {
                if (!values)             
                    found[prefix+t.name] = [ found[prefix+t.name], t.value ];
                else {
                    found[prefix+t.name] = [ found[prefix+t.name] ];                    
                    found[prefix+t.name] = found[prefix+t.name].concat(values);
                }                    
            }
        }
                                        
        if (deep && t.tags.length >0 ) 
            t.toDict (deep, found, prefix+t.name+'/');
    }
    return found;
}

BQObject.prototype.toNestedDict1 = function(deep)
{
    var dict = {}, tag;
    
    if (!isEmptyObject(this.template))
        dict['_template'] = this.template;
    
    if (this.tags.length==0)
        return this.value || ''; 
        
    for(var i = 0; i < this.tags.length; i++)
    {
        tag = this.tags[i];
        dict[tag.name] = (deep && tag.tags.length > 0) ? tag.toNestedDict(deep) : (tag.value || '');
    }
    
    return dict;
}

BQObject.prototype.toNestedDict = function(deep)
{
    var data = {}, tags = {};

    Ext.apply(data,
    {
        name        :   this.name,
        value       :   this.value || '',
    });

    if (!isEmptyObject(this.template))
        data['template'] = this.template;   
    
    if (deep)
        for(var i = 0; i < this.tags.length; i++)
            tags[this.tags[i].name] = this.tags[i].toNestedDict(deep);

    return {data:data, tags:tags};
}

BQObject.prototype.fromNestedDict = function(dict)
{
    Ext.apply(this, dict.data);
    
    for (var tag in dict.tags)
        this.addtag().fromNestedDict(dict.tags[tag])
} 

BQObject.prototype.fromNestedDict1 = function(dict)
{
    var value;

    if (dict['_template'])  // check for template entry
    {
        this._template = dict['_template'];
        delete dict['_template'];
    }    
    
    for (var tag in dict)
    {
        value = dict[tag];
        
        if (value instanceof Object)
            this.addtag({name:tag}).fromNestedDict(value);
        else
            this.addtag({name:tag, value:value});
    }
} 

BQObject.prototype.create_flat_index = function ( index, prefix ) {
    index = index || {};
    prefix = prefix || '';
    
    var t=null;
    for (var p=0; (t=this.tags[p]); p++) {
        if (!(prefix+t.name in index))    
            index[prefix+t.name] = t;
        
        if (t.tags.length >0) 
            index = t.create_flat_index(index, prefix+t.name+'/');
    }
    return index;
} 

// dima: not being used
BQObject.prototype.find_resource  = function (ty) {
    for (var i=0; i < this.children.length; i++) 
        if (this.children[i].type == ty) 
            return this.children[i];
    return null;
}

// dima: used in template, needs different name, e.g. remove_resource_by_uri ?
BQObject.prototype.remove_resource = function (uri) {
    for (var i=0; i < this.children.length; i++) 
        if (this.children[i].uri == uri) {
            delete this.children[i];
            this.children.splice(i,1);
        }
    return null;
}

BQObject.prototype.remove = function (o) {
    var index = this.tags.indexOf (o);
    if (index!=-1) this.tags.splice(index,1);
    else {
      index = this.gobjects.indexOf (o);
      if (index!= -1) this.gobjects.splice(index,1);
      else {
          index = this.children.indexOf(o);
          if (index != -1) this.children.splice(index,1);
      }
    }
}

BQObject.prototype.save_ = function (parenturi, cb, errorcb) {
    this.testReadonly();    
    var docobj = this.doc;
    var req = docobj.toXML();
    errorcb = errorcb || default_error_callback;
    if (docobj.uri) {
        xmlrequest(docobj.uri, callback(docobj, 'response_', 'update', errorcb, cb),'put', req, errorcb);
    } else {
        parenturi = parenturi || '/data_service/'+this.resource_type+'/';
        xmlrequest(parenturi, callback(docobj, 'response_', 'created', errorcb, cb),'post', req, errorcb);
    }
}

BQObject.prototype.save_ww = function (parenturi, cb, errorcb) {
    this.testReadonly();    
    var obj = this;
    var req = obj.toXML();
    errorcb = errorcb || default_error_callback;
    if (obj.uri) {
        xmlrequest(obj.uri, callback(obj, 'response_', 'update', errorcb, cb),'put', req, errorcb);
    } else {
        parenturi = parenturi || '/data_service/'+this.resource_type+'/';
        xmlrequest(parenturi, callback(obj, 'response_', 'created', errorcb, cb),'post', req, errorcb);
    }
}


// dima: used in browser factory, same thing as save but always does POST 
BQObject.prototype.append = function (cb, errorcb)
{
    this.testReadonly();
        
    var docobj = this.doc;
    var req = docobj.toXML();
    
    xmlrequest(docobj.uri, callback(docobj, 'response_', 'update', errorcb, cb),'post', req, errorcb);
}

BQObject.prototype.response_ = function (code, errorcb, cb, xmldoc) {
    // The response with FAIL or the save URI is here
    //var  = xmldoc.firstChild.firstChild;

    var node = xmldoc;
    if (node.nodeName == "#document" || node.nodeName == "response") 
        node = node.firstChild;
    if (code == "created") {
        //alert (printXML(respobj));
        //this.uri = attribStr (node, 'uri');
        this.children = [];
        this.tags = [];
        this.gobjects = [];
        try {
            BQFactory.createFromXml(node, this, null)
        } catch  (err) {
            clog ("save_" + err);
            if (errorcb) errorcb ({ xmldoc : xmldoc, message : 'parse error in BQObject.response_' });
            return;
        }
    }
    if (cb != null) {
        cb (this);
    }
}


// Load tags should setup a resource if does not exist and mark
// it top level document.. then should move tags to top level object.
BQObject.prototype.load_tags = function (cb, url, progress) {
    if (!url) {
        if (this.uri)
            url = this.uri + "/tag";
        else {
            if (cb) cb();
            return;
        }
    }
    this.remove_resource (url);
    BQFactory.load (url + "?view=deep", 
                    callback(this, 'loaded_tags', cb), 
                    progress);
}


// load_children : function to facilitate progressive fetching of tags/gobjects etc. 
// config params - 
// attrib -- filter tag or gobject usually
// vector -- where the item are store .. tags, gobjects, or kids
// cb : callback
// progress : progress callback
// depth : 'full', 'deep', 'short' etc.
BQObject.prototype.load_children = function (config)
{
    Ext.apply(config, 
    {
        attrib : config.attrib || 'tag',
        depth : config.depth || 'deep',
        vector : config.vector || 'tags',
        cb : config.cb || Ext.emptyFn
    })
    
    Ext.apply(config,
    {
        uri : config.uri || this.uri+'/'+config.attrib,
    });

    this.remove_resource(config.uri);

    BQFactory.request(
    {
        uri : config.uri+'?view='+config.depth,
        cb : Ext.bind(function(resource, config)
        {
            this[config.vector] = resource[config.vector];
            config.cb(resource[config.vector]);
        }, this, [config], true), 
        progresscb : config.progress
    });
}

// dima: repeated from load_tags
BQObject.prototype.loadTags = function (config)
{
    config.attrib='tag';
    config.vector='tags';
    BQObject.prototype.load_children.call(this, config);
}

// dima: repeated from load_gobjects
BQObject.prototype.loadGObjects = function (config)
{
    config.attrib='gobject';
    config.vector='gobjects';
    BQObject.prototype.load_children.call(this, config);
}

BQObject.prototype.loaded_tags = function (cb, resource) {
    this.tags = resource.tags;
    if (cb) cb(resource.tags);
}

BQObject.prototype.load_gobjects = function (cb, url, progress) {
    if (!url) url = this.uri + "/gobject";
    this.remove_resource (url);
    BQFactory.load (url + "?view=deep", 
                    callback(this, 'loaded_gobjects', cb), 
                    progress);
}

BQObject.prototype.loaded_gobjects = function (cb, resource) {
    this.gobjects = resource.gobjects;
    if (cb) cb(resource.gobjects);
}

BQObject.prototype.save_gobjects = function (cb, url, progress, errorcb) {
    this.testReadonly();    
    if (!url) url = this.uri;
    var resource = new BQResource (url + "/gobject");
    resource.gobjects = this.gobjects;
    resource.created = false;   // HACK 
    resource.save_(resource.uri, cb, errorcb);
}
BQObject.prototype.save_tags = function (cb, url, progress, errorcb) {
    this.testReadonly();    
    if (!url) url = this.uri;
    var resource = new BQResource (url + "/tag");
    resource.tags = this.tags;
    resource.created = false;   // HACK 
    resource.save_(resource.uri, cb, errorcb);
}

BQObject.prototype.dispose = function (){
    visit = new BQVisitor();
    visit.visit = function (n) { n.doc = null;  };
    visit.visitall(this)
};
    
BQObject.prototype.addtag = function (tag, deep){
    if (!(tag instanceof BQTag) || deep) {
        var nt = new BQTag();
        for (var i in tag) {
            nt[i] = tag[i];
        }
        tag = nt;
    }
    tag.setParent(this);
    tag.doc = this.doc;
    this.dirty = true;
    return tag;    
}

BQObject.prototype.addtags = function (tags, deep) {
    for (var i=0; i<tags.length; i++)
        this.addtag(tags[i], deep);   
}

BQObject.prototype.addgobjects=function (gob){
    if (! (gob instanceof BQGObject)) {
        var ng = new BQGObject();
        for (var i in gob) {
            ng[i] = gob[i];
        }
        gob = ng;
    }
    gob.setParent(this);
    gob.doc = this.doc;
    this.dirty = true;
    return gob;
}

BQObject.prototype.addchild = function (kid) {
    kid.setParent(this);
    kid.doc = this.doc;
    this.dirty = true;
}
BQObject.prototype.convert_tags=function (){
     for (var i=0; i < this.tags.length; i++) {
         var tag = this.tags[i];
         var nm  = tag.name.replace(/\W/g, '_');
         var vl  = tag.value;
         if (this[nm] == undefined) {
             this[nm] = vl;
         } else {
             if (!(this[nm] instanceof Array)) {
                 this[nm] = [ this[nm] ];
             }
             this[nm].push (vl);
         }
     }
}

//-----------------------------------------------------------------------------
// BQResource represents an addressable resource.
// It is often used a the top level document of a tag document
// I1  
//  +- R1 == /image/1/tags
//  +- R2 == /image/1/gobjects
//      + G1
//      + G2/R3 == /image/1/gobjects/2  a very large gobject
//-----------------------------------------------------------------------------

function BQResource (uri, doc) {
    BQObject.call(this, uri, doc);
    this.resource_type = 'resource';
}

BQResource.prototype = new BQObject();


//-----------------------------------------------------------------------------
// BQTemplate
//-----------------------------------------------------------------------------

function BQTemplate (uri, doc) {
    BQObject.call(this, uri, doc);
    this.resource_type = 'template';
}
BQTemplate.prototype = new BQObject();


//-----------------------------------------------------------------------------
// BQImage
//-----------------------------------------------------------------------------

function BQImage (uri){
    BQObject.call(this, uri);
    this.resource_type = "image";
}
BQImage.prototype = new BQObject();
//extend(BQImage, BQObject);

BQImage.prototype.initializeXml = function (node) {
    BQObject.prototype.initializeXml.call(this, node);
    if (this.resource_uniq) {
        this.src  = '/image_service/images/' + this.resource_uniq;
        // in the case the the data is coming from another server, make sure to load proper URL
        this.src = this.uri.replace(/\/data_service\/.*$/i, this.src);
    }
    
    /*
    this.x    = attribInt(node,'x');
    this.y    = attribInt(node,'y');
    this.z    = attribInt(node,'z');
    this.t    = attribInt(node,'t');
    this.ch   = attribInt(node,'ch');
    */
}

//-----------------------------------------------------------------------------
// BQFile
//-----------------------------------------------------------------------------

function BQFile (uri){
    BQObject.call(this, uri);
    this.resource_type = 'file';
}
BQFile.prototype = new BQObject();
//extend(BQFile, BQObject);

BQFile.prototype.initializeXml = function (node) {
    BQObject.prototype.initializeXml.call(this, node);
}

//-----------------------------------------------------------------------------
// BQTag
//-----------------------------------------------------------------------------

function BQTag (uri, name, value, type) {
    BQObject.call(this, uri);
    //this.values = [];
    this.resource_type = "tag";
    this.name  = name;
    this.value = value;
    this.type  = type;
}
BQTag.prototype = new BQObject();
//extend(BQTag, BQObject);

BQTag.prototype.setParent = function (p) {
    if (p.tags == this.tags) 
        alert ('Warning - BQTag.prototype.setParent: parent and child are same');
    p.tags = p.tags || [];
    p.tags.push (this);
    this.parent = p;
}

//-----------------------------------------------------------------------------
// BQGObject
//-----------------------------------------------------------------------------

function BQGObject(ty, uri){
    BQObject.call(this, uri);
    this.type = ty;           // one of our registeredTypes: point, polygon, etc.
    this.uri=null;
    this.name = null;
    this.vertices = [];
    this.resource_type = "gobject";
}
BQGObject.prototype = new BQObject();
//extend(BQGObject,BQObject)

BQGObject.prototype.initializeXml = function (node) {
    BQObject.prototype.initializeXml.call(this, node);
    
    this.type  = node.nodeName;
    if (this.type == 'gobject') 
        this.type = attribStr(node, 'type');
    
    // dima: speed optimization, using xpath for resources with many vertices is much faster
    // Utkarsh : now uses evaulateXPath from utils.js, which is browser independent
    var vertices = evaluateXPath(node, 'vertex');
    this.vertices = [];
    
    // vertices should be an array
    for (var i=0; i<vertices.length; i++)
        this.vertices.push(new BQVertex(vertices[i]));

}

BQGObject.prototype.setParent = function (p) {
    p.gobjects = p.gobjects || [];    
    p.gobjects.push (this);
    this.parent = p;    
}

//-----------------------------------------------------------------------------
// BQVisitor
// Simple visitor (mainly for) GObjects
//-----------------------------------------------------------------------------

function BQVisitor () {
}
BQVisitor.prototype.visit_array = function (l, arglist){
    for (var i=0; i < l.length; i++) {
        this.visitall(l[i], arglist);
    }
}
BQVisitor.prototype.visit_special_array = function (l, arglist){
    for (var i=0; i < l.length; i++) {
        this.visit_special(l[i], arglist);
    }
}
BQVisitor.prototype.visit = function(n, arglist) {}
BQVisitor.prototype.start = function(n, arglist) {}
BQVisitor.prototype.finish = function(n, arglist) {}
BQVisitor.prototype.visitall = function (root, arglist) {
    var stack = [];
    stack.push (root);
    while (stack.length != 0) {
        var node = stack.pop();
        this.visit(node,  arglist);
        //for (var i=0; i < kids(node).length; i++ ) 
        //  stack.push (kids(node)[i]);
        var kids  = node.getkids();
        for (var i=0; i < kids.length; i++) 
            stack.push (kids[i]);
    }
}
BQVisitor.prototype.visit_special = function(root,arglist) {
    var stack = [];
    stack.push ([root,null]);
    while (stack.length != 0) {
        var tuple = stack.pop();
        var node = tuple[0];
        var parent = tuple[1];
        if (node == null) {     // found end of parent.
            this.finish(parent, arglist);
            continue;
        }
        var kids  = node.getkids();
        if (kids.length > 0) { // push an end of parent mark/
            stack.push([null, node]);
            this.start (node, arglist)
        }
        this.visit (node,  arglist);
        for (var i=0; i < kids.length; i++ ) 
            stack.push ([kids[i], node]);
    }
}
////////////////////////////////////////////////
// A visitor with nodes on the class
// A visitor supporting type visits 
// The node should have a type field which 
// will be used as a dispatch method on the class
// i.e. GobVisitor.polyine (polynode) when visiting polyline objects
// default_visit will be called  for unknown types.
// Simple Gobject types will not be called with start/finish states
// as they do not have children gobjects.
function BQClassVisitor () {
    this.VISIT = 'visit';
    this.START = 'start';
    this.FINISH = 'finish';
    this.state = null;
}
BQClassVisitor.prototype = new BQVisitor();
BQClassVisitor.prototype.callnode = function (n, arglist){
    var f = this[n.type] || this['default_visit'] || null;
    if (f != null) {
        var args = [n].concat(arglist);
        f.apply (this, args);
    }
}
BQClassVisitor.prototype.visit = function (n, arglist){
    this.state=this.VISIT;
    this.callnode(n, arglist);
}
BQClassVisitor.prototype.start = function (n,arglist){
    this.state=this.START;
    this.callnode(n, arglist);
}
BQClassVisitor.prototype.finish = function (n,arglist){
    this.state=this.FINISH;
    this.callnode(n, arglist);
}
//////////////////////////////////////////////////
// Forward node function to another proxy class
// The node should have a type field which 
// will be used as a dispatch method on the proxy class
// i.e. Proxy.polyine (visitor, polynode) when visiting polyline objects

function BQProxyClassVisitor (visitor) {
    this.proxy = visitor;
}
BQProxyClassVisitor.prototype = new BQClassVisitor();
BQProxyClassVisitor.prototype.callnode = function (n, arglist){
    var f = this.proxy[n.type] || this.proxy['default_visit'] || null;
    if (f != null) {
        var args = [this, n].concat (arglist);
        f.apply (this.proxy, args);
    }
}
//////////////////////////////////////////////////
// Visitor Utility function 
// Usage:   visit_array (some_array, function (n[,args]) {..}[,args]);
// 
function visit_all (node, cb) {
    var args = Array.prototype.slice.call(arguments,2);
    var v = new BQVisitor();
    v.visit = cb;
    v.visitall(node, args);
}
function visit_array (arr, cb) {
    var args = Array.prototype.slice.call(arguments,2);
    var v = new BQVisitor();
    v.visit = cb;
    v.visit_array(arr, args);
}


//-------------------------------------------------------------------------------
// BQImagePhys - maintains a record of image physical parameters
//-------------------------------------------------------------------------------

function BQImagePhys(bqimage) {
    this.num_channels = 0;
    this.pixel_depth = null;    
    this.pixel_size = [];
    this.pixel_units = [];    
    this.channel_names = [];
    this.display_channels = [];
    this.channel_colors = [];

    this.pixel_size_ds = [];
    this.channel_names_ds = [];
    this.display_channels_ds = [];

    this.pixel_size_is = [];
    this.channel_names_is = [];
    this.display_channels_is = [];
     
    // default mapping
    this.channel_colors_default = [
        new Ext.draw.Color( 255,   0,   0 ), // red
        new Ext.draw.Color(   0, 255,   0 ), // green
        new Ext.draw.Color(   0,   0, 255 ), // blue
        new Ext.draw.Color( 255, 255, 255 ), // gray
        new Ext.draw.Color(   0, 255, 255 ), // cyan
        new Ext.draw.Color( 255,   0, 255 ), // magenta
        new Ext.draw.Color( 255, 255,   0 ), // yellow
    ];   
    
    this.pixel_formats = {
        'unsigned integer': 'u',
        'signed integer'  : 's',
        'floating point'  : 'f',
    };
    
    this.is_done = false;
    this.ds_done = false; 
    this.loadcallback = null;
    this.image = bqimage;
    //this.init();
}

BQImagePhys.prototype.init = function () {
  if (!this.image) return;
  this.num_channels = this.ch || this.image.ch;

  //-------------------------------------------------------
  // image physical sizes
  this.pixel_size = [0, 0, 0, 0];
  this.pixel_units = [undefined, undefined, undefined, undefined];
    
  //-------------------------------------------------------
  // image channels to display RGB mapping
  this.display_channels[0] = 0;
  this.display_channels[1] = 1;
  this.display_channels[2] = 2;
  if (this.num_channels == 1) {
    this.display_channels[1] = 0;
    this.display_channels[2] = 0;
  }
  if (this.num_channels == 2)
    this.display_channels[2] = -1;


    this.channel_colors = this.channel_colors_default.slice(0, Math.min(this.num_channels, this.channel_colors_default.length));
    var diff = this.num_channels-this.channel_colors.length;
    for (var i=0; i<diff; i++)
        this.channel_colors.push(new Ext.draw.Color(0,0,0));


  //-------------------------------------------------------
  // channel names
  for (var i=0; i<this.num_channels; i++)
    this.channel_names[i] = 'Ch'+(i+1); 
  if (this.num_channels == 3) {
    this.channel_names[0] = 'Red';
    this.channel_names[1] = 'Green';
    this.channel_names[2] = 'Blue';        
  }             
}

function combineValue( v1, v2, def ) {
  //if (v1 && v1 != undefined && v1 != NaN && v1 != '') return v1;  
  //if (v2 && v2 != undefined && v2 != NaN && v2 != '') return v2;  
  //return def;  
  return v1 || v2 || def;
}

BQImagePhys.prototype.normalizeMeta = function() {
  clog ("BQImagePhys: Aggregate metadata");  

  // ensure values and their types
  for ( var i=0; i<this.pixel_size.length; i++ ) {
    this.pixel_size[i] = combineValue( this.pixel_size_ds[i], this.pixel_size_is[i], this.pixel_size[i] );    
    this.pixel_size[i] = parseFloat( this.pixel_size[i] );
  }

  for ( var i=0; i<this.channel_names.length; i++ ) {
    this.channel_names[i] = combineValue( this.channel_names_ds[i], this.channel_names_is[i], this.channel_names[i] );    
  }

  for ( var i=0; i<this.display_channels.length; i++ ) {
    this.display_channels[i] = combineValue( this.display_channels_ds[i], this.display_channels_is[i], this.display_channels[i] );      
    this.display_channels[i] = parseInt( this.display_channels[i] );      
  }
  
  if (this.channel_colors_ds && this.channel_colors_ds.length===this.num_channels)
      this.channel_colors = this.channel_colors_ds;
  
  this.initialized = true;  
}

BQImagePhys.prototype.load = function(cb) {
    this.initialized = undefined;
    this.loadcallback = cb;   
    BQFactory.load (this.image.src + "?meta", callback(this, 'onloadIS'));
    if (this.image.tags.length==0)
      this.image.load_tags(callback(this, 'onloadDS'));
    else
      this.onloadDS();
}

BQImagePhys.prototype.onload = function() {
  clog ("BQImagePhys: onload test: " + this.is_done + " " + this.ds_done );    
  if (this.is_done==true && this.ds_done==true) {
    this.normalizeMeta();
    if (this.loadcallback != null) this.loadcallback (this);
  }          
}

BQImagePhys.prototype.onloadIS = function (image) {
  clog ("BQImagePhys: Got metadata from IS");   
  var hash = {};
  for (var t in image.tags ) 
      hash[image.tags[t].name] = image.tags[t].value;

  //-------------------------------------------------------
  // image physical sizes
  this.pixel_size_is[0] = hash['pixel_resolution_x'];
  this.pixel_size_is[1] = hash['pixel_resolution_y'];
  this.pixel_size_is[2] = hash['pixel_resolution_z'];
  this.pixel_size_is[3] = hash['pixel_resolution_t'];
  this.x  = hash['image_num_x'];
  this.y  = hash['image_num_y'];
  this.z  = hash['image_num_z'];
  this.t  = hash['image_num_t'];
  this.ch  = hash['image_num_c'];
  
  this.init();   

  //-------------------------------------------------------  
  // units
  var wanted = { 'pixel_resolution_unit_x': 0,
                 'pixel_resolution_unit_y': 1,
                 'pixel_resolution_unit_z': 2,
                 'pixel_resolution_unit_t': 3 };
  for (var v in wanted) {
      if (v in hash) 
          this.pixel_units[wanted[v]] = this.pixel_units[wanted[v]] || hash[v];
  }    
  
  //-------------------------------------------------------
  // image channels to display RGB mapping
  this.display_channels_is[0] = hash['display_channel_red'];      
  this.display_channels_is[1] = hash['display_channel_green'];      
  this.display_channels_is[2] = hash['display_channel_blue'];  

  for (var i=0; i<this.num_channels; i++)
     if (hash['channel_color_'+i])
         this.channel_colors[i] = Ext.draw.Color.fromString('rgb('+hash['channel_color_'+i]+')');
    
  //-------------------------------------------------------
  // image channels to display RGB mapping  
  for (var i=0; i<this.num_channels; i++) {
    var tag_name = 'channel_' + i + '_name';
    this.channel_names_is[i] = hash[tag_name];    
  }  

  //-------------------------------------------------------
  // additional info
  this.pixel_depth = hash['image_pixel_depth'];     
  this.pixel_format = hash['image_pixel_format']; 
    
  //-------------------------------------------------------
  // additional info
  //this.pixel_depth = hash['image_pixel_depth'];     
  
  this.is_done = true; 
  this.onload();
}

BQImagePhys.prototype.onloadDS = function ( ) { 
    clog ("BQImagePhys: Got metadata from DS");  
  
    var image = this.image;
    var ht = {};
    for (var t in image.tags ) 
        ht[image.tags[t].name] = image.tags[t].value;

    //-------------------------------------------------------
    // image physical sizes
    v  = 'pixel_resolution_x_y'; 
    if (v in ht) {
        this.pixel_size_ds[0] = parseFloat(ht[v]);
        this.pixel_size_ds[1] = parseFloat(ht[v]);        
    }
    var wanted = { 'pixel_resolution_x': 0,
                   'pixel_resolution_y': 1,
                   'pixel_resolution_z': 2,
                   'pixel_resolution_t': 3 };
    for (var v in wanted) {
        if (v in ht) 
            this.pixel_size_ds[wanted[v]] = parseFloat(ht[v]);
    }
    
    //-------------------------------------------------------    
    // units
    var wanted = { 'pixel_resolution_unit_x': 0,
                   'pixel_resolution_unit_y': 1,
                   'pixel_resolution_unit_z': 2,
                   'pixel_resolution_unit_t': 3 };
    for (var v in wanted) {
        if (v in ht) 
            this.pixel_units[wanted[v]] = ht[v];
    }    
  
    //-------------------------------------------------------
    // image channels to display RGB mapping
    this.display_channels_ds[0] = ht['display_channel_red'];
    this.display_channels_ds[1] = ht['display_channel_green'];     
    this.display_channels_ds[2] = ht['display_channel_blue'];
    
    this.channel_colors_ds = [];
    for (var i=0; i<this.num_channels; i++)
        if (ht['channel_color_'+i])
            this.channel_colors_ds[i] = Ext.draw.Color.fromString('rgb('+ht['channel_color_'+i]+')');    
    
    //-------------------------------------------------------
    // image channels to display RGB mapping  
    for (var i=0; i<this.num_channels; i++) {
      var tag_name = 'channel_' + i + '_name';
      this.channel_names_ds[i] = ht[tag_name];    
    }  

    this.ds_done = true; 
    this.onload(); 
}

BQImagePhys.prototype.getPixelInfo = function (i) { 
    var r = [undefined, undefined];
    if (this.pixel_size[i]!=undefined && !isNaN(this.pixel_size[i]) && this.pixel_size[i]!=0.0000) {
        r[0] = this.pixel_size[i];
        r[1] = this.pixel_units[i];        
    }
    return r;
}

BQImagePhys.prototype.getPixelInfoZ = function () { 
    return this.getPixelInfo(2);
}

BQImagePhys.prototype.getPixelInfoT = function () { 
    return this.getPixelInfo(3);
}

//-------------------------------------------------------------------------------
// parseUri 
//-------------------------------------------------------------------------------

/* parseUri JS v0.1, by Steven Levithan (http://badassery.blogspot.com)
Splits any well-formed URI into the following parts (all are optional):
----------------------
* source (since the exec() method returns backreference 0 [i.e., the entire match] as key 0, we might as well use it)
* protocol (scheme)
* authority (includes both the domain and port)
    * domain (part of the authority; can be an IP address)
    * port (part of the authority)
* path (includes both the directory path and filename)
    * directoryPath (part of the path; supports directories with periods, and without a trailing backslash)
    * fileName (part of the path)
* query (does not include the leading question mark)
* anchor (fragment)
*/
function parseUri(sourceUri){
    var uriPartNames = ["source","protocol","authority","domain","port","path","directoryPath","fileName","query","anchor"];
    var uriParts = new RegExp("^(?:([^:/?#.]+):)?(?://)?(([^:/?#]*)(?::(\\d*))?)?((/(?:[^?#](?![^?#/]*\\.[^?#/.]+(?:[\\?#]|$)))*/?)?([^?#/]*))?(?:\\?([^#]*))?(?:#(.*))?").exec(sourceUri);
    var uri = {};
    
    for(var i = 0; i < 10; i++){
        uri[uriPartNames[i]] = (uriParts[i] ? uriParts[i] : "");
    }
    
    // Always end directoryPath with a trailing backslash if a path was present in the source URI
    // Note that a trailing backslash is NOT automatically inserted within or appended to the "path" key
    if(uri.directoryPath.length > 0){
        uri.directoryPath = uri.directoryPath.replace(/\/?$/, "/");
    }
    
    return uri;
}

function BQUrl (u){
  this.uri = parseUri(u);
}

BQUrl.prototype.toString = function () {
  return this.uri['source'];
}

BQUrl.prototype.server = function () {
  return this.uri['protocol'] + '://' + this.uri['authority'];
}

//-------------------------------------------------------------------------------
// BQUser
//-------------------------------------------------------------------------------

function BQUser (){
    BQObject.call(this);
    this.resource_type = "user";
}

BQUser.prototype = new BQObject();
//extend(BQUser, BQObject);

BQUser.prototype.initializeXml = function (node) {
    BQObject.prototype.initializeXml.call(this, node);    
    this.user_name     = this.name;
    this.display_name  = this.user_name;
    this.email         = this.value;
    this.email_address = this.email;
}

BQUser.prototype.afterInitialized = function () {
    var display_name  = this.find_tags('display_name');
    this.display_name = (display_name && display_name.value)?display_name.value:this.user_name;
}

BQUser.prototype.get_credentials = function( cb) {
//    var u = new BQUrl(this.uri);
//    this.server_uri = u.server();
//    BQFactory.load (this.server_uri+bq.url("/auth_service/credentials/"), 
//                    callback (this, 'on_credentials', cb));
    BQFactory.load (bq.url('/auth_service/credentials/'));
}

BQUser.prototype.on_credentials = function(cb, cred) {
    this.credentials = cred;
    this.credentials.convert_tags();
    if (cb) cb(cred);
}


//-------------------------------------------------------------------------------
// BQAuth
//-------------------------------------------------------------------------------

function BQAuth (){
    BQObject.call(this);
    this.resource_type = "auth";
    this.xmlfields = [ "action", "user", "email" ] ;
}

BQAuth.prototype = new BQObject();
//extend(BQAuth, BQObject);

BQAuth.prototype.initializeXml = function (node) {
    BQObject.prototype.initializeXml.call(this, node);    

    // dima: DIFFERENT ATTRIBUTES!!!
    this.action = attribStr(node, 'action');
    this.email  = attribStr(node, 'email');
    this.user   = attribStr(node, 'user');
}

BQAuth.prototype.save_ = function (node)
{
    debugger;
}

//-------------------------------------------------------------------------------
// BQModule
// dima: should produce MEX from inputs section, have both input and output trees
// have them indexed in a flat way for easy access to elements
// template parsing?
//-------------------------------------------------------------------------------

function BQModule () {
    this.readonly = true;
    this.reserved_io_types = {'system-input':null, 'template':null, };
    this.configs = { 'help': 'help', 
                     'thumbnail': 'thumbnail', 
                     'title': 'title', 
                     'authors': 'authors', 
                     'description': 'description',
                     'display_options/group': 'group', 
                     'module_options/version': 'version',   
                   };

    BQObject.call(this);
    this.resource_type = "module";
}
BQModule.prototype = new BQObject();

BQModule.prototype.afterInitialized = function () {
    
    // now copy over all other config params
    var dict = this.toDict(true);
    for (var i in this.configs) {
        if (i in dict && !(i in this))
            this[this.configs[i]] = dict[i];
    }    
    
    // define inputs and outputs    
    //BQObject.prototype.afterInitialized.call ();
    var inputs  = this.find_tags('inputs');
    if (inputs && inputs.tags) {
        this.inputs = inputs.tags; // dima - this should be children in the future
        this.inputs_index  = inputs.create_flat_index();    
    }

    var outputs = this.find_tags('outputs');
    if (outputs && outputs.tags) {
        this.outputs = outputs.tags; // dima - this should be children in the future   
        this.outputs_index  = outputs.create_flat_index();
    }
    
    // create sorted iterable resource names
    if ('execute_options/iterable' in dict) {
        this.iterables = [ dict['execute_options/iterable'] ];
        // make sure dataset renderer is there
        var name = this.iterables[0];
        if (!(name in this.outputs_index)) {
            var r = new BQTag(undefined, name, undefined, 'dataset');
            this.outputs.push(r);
            this.outputs_index[name] = r;               
        }
    }
    
    this.updateTemplates();
}

BQModule.prototype.updateTemplates = function () {
    // create accepted_type
    // unfortunately there's no easy way to test if JS vector has an element
    // change the accepted_type to an object adding the type of the resource
    for (var i in this.inputs_index) {
        var e = this.inputs_index[i]; 
        if (e.template) {
            var act = {};
            if (e.type) act[e.type] = e.type;
            if (e.template.accepted_type)
            for (var p=0; (t=e.template.accepted_type[p]); p++) {
                act[t] = t;
            }
            e.template.accepted_type = act;
        }
    }
}


BQModule.prototype.fromNode = function (node) {
    this.initializeXml(node);
}

BQModule.prototype.createMEX = function( ) {
    var mex = new BQMex();

    // create INPUTS block
    var tag_inputs = mex.addtag ({name:'inputs'});
    var i = undefined;
    for (var p=0; (i=this.inputs[p]); p++) {
        var r = i.clone(true);
        tag_inputs.addchild(r);
    }

    // create OUTPUTS block
    //var tag_outputs = mex.addtag ({name:'outputs'}); // dima: the outputs tag will be created by the module?
    
    // dima: the new iterable structure does not require module to post this anymore 
    //       instead MS would look into module definition file for itarables
    // create execute_options block    
    if (this.iterables && this.iterables.length>0) {
        var tag_execute = mex.addtag ({name:'execute_options'});
        var iterable_name = undefined;
        for (var p=0; (iterable_name=this.iterables[p]); p++) {
            var i = this.inputs_index[iterable_name];
            if (!i) continue;
            tag_execute.addtag({ name:'iterable', value:i.name,  });
        }
    }
    
    return mex;
}


//-------------------------------------------------------------------------------
// BQMex
//-------------------------------------------------------------------------------

function BQMex (){
    BQObject.call(this);
    this.resource_type = "mex";
}

BQMex.prototype = new BQObject();
BQMex.prototype.initializeXml = function (node) {
    BQObject.prototype.initializeXml.call(this, node);    
    this.status = this.value;
}

BQMex.prototype.hasIterables = function () {
    if (!this.iterables) return false;
    return (Object.keys(this.iterables).length>0);
}

// creates mapping from iterable resources in sub MEXes to their MEXes
BQMex.prototype.findMexsForIterable = function (name, root) {
    root = root || 'inputs/';
    this.iterables = this.iterables || {};
    if (!name || this.children.length<1) return;
    this.dict = this.dict || this.toDict(true);
        
    var dataset = this.dict[root+name];
    this.iterables[name] = this.iterables[name] || {};
    this.iterables[name]['dataset'] = dataset;
    
    var o=null;
    for (var i=0; (o=this.children[i]); i++) {
        if (o instanceof BQMex) {
            var resource = o.dict[root+name];
            if (resource) this.iterables[name][resource] = o;
        }
    }
}

BQMex.prototype.afterInitialized = function () {
    //BQObject.prototype.afterInitialized.call ();
    
    this.dict = this.dict || this.toDict(true);
  
    var inputs  = this.find_tags('inputs');
    if (inputs && inputs.tags) {
        this.inputs = inputs.tags; // dima - this should be children in the future
        this.inputs_index  = inputs.create_flat_index();    
    }
    
    var outputs = this.find_tags('outputs');    
    if (outputs && outputs.tags) {
        this.outputs = outputs.tags; // dima - this should be children in the future   
        this.outputs_index  = outputs.create_flat_index();
    }    
    
    // check if the mex has iterables
    if (this.dict['execute_options/iterable']) {
        var name = this.dict['execute_options/iterable'];
        this.findMexsForIterable(name, 'inputs/');
        // if the main output does not have a dataset resource, create one
        this.outputs = this.outputs || [];
        this.outputs_index = this.outputs_index || {};        
        if (!(name in this.outputs_index) && this.iterables && name in this.iterables && 'dataset' in this.iterables[name]) {
            var r = new BQTag(undefined, name, this.iterables[name]['dataset'], 'dataset');
            this.outputs.push(r);
            this.outputs_index[name] = r;   
        }
    }    
}


//-------------------------------------------------------------------------------
// BQDataset
// Each dataset has a special tag 'members' that contains a list
// of the dataset's resources/
// BQFactory.load("/ds/datasets/", callback(this, 'datasets_loaded')
// dataset_loaded (dataset)
//    dataset.getMembers (with_members)
// with_member (members)
//    for (var i =0; i<members.children.length;i++)
//       resource = members.children[i]
//       clog(resource.uri)
// }

//-------------------------------------------------------------------------------
function BQDataset (){
    BQObject.call(this);
    this.resource_type = "dataset";
}
BQDataset.prototype = new BQObject();

// dima: some method is required to figure out if an additional fetch is required
BQDataset.prototype.getMembers = function (cb) {
    // Call the callback cb with the members tag when loaded
    /*
    var members = this.find_tags ('members');
    if (!members) {
        this.load_tags (callback(this, 'members_loaded', cb));
    } else {
        if (cb) cb(members);
        return members;
    }
    */
    // we need to make sure we fetched values before we can do this properly
    //this.values = this.values || [];

    if (!this.members) {
        BQFactory.request({ 
            uri: this.uri + '/value',  
            cb: callback(this, '_loaded', cb),
            //uri_params: {view:'deep'}
        });
    } else {
        if (cb) cb(this);
    }
    return this;    
}
BQDataset.prototype._loaded = function (cb, resource) {
    this.members = resource.children || [];
    if (cb) cb(this);
}

BQDataset.prototype.setMembers = function (nvs) {
    this.values = nvs;
}

BQDataset.prototype.appendMembers = function (newmembers, cb) {
    this.getMembers (callback (this, this.appendMembersResp, newmembers, cb))
}
BQDataset.prototype.appendMembersResp = function (newmembers, cb, members_tag) {
    var members = members_tag.values.concat(newmembers);
    this.setMembers (members);
    if (cb) cb();
}

// deleteMembers    : Deletes members of a temporary dataset (which hasn't been saved, hence no URI)
//                  : Calls individual deletes on the resources and collects results
// output           : callback is called with an object summary which has two members, success and failure e.g.
//                  : summary : {success:7, failure:3} 
// temporary until we come up with a permanent (backend?) solution

BQDataset.prototype.tmp_deleteMembers = function(cb)
{
    Ext.apply(this,
    {
        tmp_cb      :   cb,
        tmp_success :   0,
        tmp_failure :   0,
        tmp_final   :   this.tmp_members.length
    })
    
    function result(success)
    {
        success?this.tmp_success++:this.tmp_failure++;
        
        if ((this.tmp_success+this.tmp_failure)==this.tmp_final)
            cb({success:this.tmp_success, failure:this.tmp_failure});
    }
    
    for (var i=0; i<this.tmp_members.length; i++)
        this.tmp_members[i].resource.delete_(Ext.pass(result, [true], this), Ext.pass(result, [false], this));
}

// method for a temporary dataset to set new members
// assumes members are BQResources for now
BQDataset.prototype.tmp_setMembers = function(members)
{
    if (!(members instanceof Array))
        members = [members];
    
    this.tmp_members = members;
}

// method for a temporary dataset to download all member resources into one TARball
BQDataset.prototype.tmp_downloadMembers = function()
{
    var exporter = Ext.create('BQ.Export.Panel'), members=[];
    
    for (var i=0; i<this.tmp_members.length; i++)
        members.push(this.tmp_members[i].resource);
        
    exporter.downloadResource(members, 'tar');
}

// method for a temporary dataset to change permission on all member resources
BQDataset.prototype.tmp_changePermission = function(permission, success, failure)
{
    var no = {count:this.tmp_members.length};
    
    function result(no, success)
    {
        if (--no.count==0) success(); 
    }
    
    for (var i=0; i<this.tmp_members.length; i++)
        this.tmp_members[i].changePrivacy(permission, Ext.pass(result, [no, success]));
}

// method for a temporary dataset to share all member resources
BQDataset.prototype.tmp_shareMembers = function()
{
    var exporter = Ext.create('BQ.ShareDialog.Offline', {resources : this.tmp_members});
}



//-------------------------------------------------------------------------------
// BQSession
//-------------------------------------------------------------------------------

function BQSession () {
    BQObject.call(this);
    this.current_timer = null;
    this.timeout = null;
    this.expires = null;
    this.user = undefined;
    this.user_uri = undefined;    
}

BQSession.prototype= new BQObject();
BQSession.current_session = undefined;

BQSession.reset_timeout  = function (){
    if (BQSession.current_session)
        BQSession.current_session.reset_timeout();
}
BQSession.initialize_timeout = function (baseurl, opts) {
    BQFactory.load (baseurl + bq.url("/auth_service/session"), 
                    function (session) {
                        BQSession.current_session = session;
                        session.set_timeout (baseurl, opts);
                        if (session.onsignedin) session.onsignedin(session); 
                    }, null, false);
}
BQSession.clear_timeout = function (baseurl) {
    if (BQSession.current_session) {
        clearTimeout(BQSession.current_session.current_timer);
        BQSession.current_session = undefined;
    }
}

BQSession.prototype.parseTags  = function (){
    var timeout = this.find_tags ('timeout');
    var expires = this.find_tags ('expires');
    if (expires && timeout) {
        clog ("session (timeout, expires) " + timeout.value + ':' + expires.value);
        this.timeout = parseInt (timeout.value) * 1000;
        this.expires = parseInt (expires.value) * 1000; 
    }

    var user = this.find_tags ('user');
    if (user) {
        this.user_uri = user.value;        
        BQFactory.request({uri: user.value, cb: callback(this, 'setUser'), cache: false, uri_params: {view:'full'}});
    } else {
        this.user = null;
        this.user_uri = null;        
        var sess = this;        
        if (sess.onnouser) sess.onnouser();    
    } 
}

BQSession.prototype.hasUser = function () {
    return this.user ? true : false;
}

BQSession.prototype.setUser = function (user) {
    this.user = user;
    if (this.ongotuser) 
        this.ongotuser(this.user);   
}

BQSession.prototype.set_timeout  = function (baseurl, opts) {
    if (opts) {
      if (opts.onsignedin)  this.onsignedin  = opts.onsignedin; 
      if (opts.onsignedout) this.onsignedout = opts.onsignedout; 
      if (opts.ongotuser)   this.ongotuser   = opts.ongotuser;    
      if (opts.onnouser)    this.onnouser    = opts.onnouser;         
    }
  
    this.parseTags ();
    if (this.timeout) {
        this.callback = callback (this, 'check_timeout', baseurl);
        // tag value  is in seconds while timeout is in milliseconds
        clog ("timeout in " + this.timeout/1000 + " s" );
        this.reset_timeout();
    } else {
        clog ('no expire');
    }
}

BQSession.prototype.reset_timeout  = function (){
    clearTimeout (this.current_timer);
    if (this.timeout)
        this.current_timer = setTimeout (this.callback, this.timeout);
    //clog ('timeout reset:' + this.timeout);
    BQSession.current_session = this;
}
BQSession.prototype.cancel_timeout  = function (){
    clearTimeout (this.current_timer);
}

BQSession.prototype.check_timeout = function (baseurl) {
    BQSession.clear_timeout();
    BQFactory.load (baseurl + bq.url("/auth_service/session"), 
                    function (session){
                        session.session_timeout (baseurl);
                    }, null, false);
}
BQSession.prototype.session_timeout = function (baseurl) {
    this.parseTags();
    // timeout in more than 30 seconds ?  then just reset 
    // as something unexpected has accessed the session (another browser)?
    if (this.expires > 30000) {
        clog ("session timeout is resetting: expires =" + this.expires );
        this.set_timeout(baseurl);
        return;
    }
    if (this.onsignedout) this.onsignedout(); 
    //window.location = baseurl + "/auth_service/logout";
    //alert("Your session has  timed out");
}


//-------------------------------------------------------------------------
// BQQuery - this is something old that probably should gof
//-------------------------------------------------------------------------

function BQQuery(uri, parent, callback) {
    this.parent = parent;
    this.tags = new Array();
    this.callback = callback;  
    makeRequest( uri, this.parseResponse, this , "GET", null ); 
} 

BQQuery.prototype.parseResponse = function(o, data) {
    var tags = data.getElementsByTagName("tag");
    for(var i=0; i<tags.length; i++) {
        o.tags[i] = tags[i].getAttribute('value');
    }
    o.callback(o);
}



/////////////////////////////////////////
// Bisque service and access 

Ext.require(['Ext.util.Observable']);
Ext.require(['Ext.container.Viewport']);

Ext.define('BQ', {
    extend: 'Ext.util.Observable',

    root: '/',
    baseCSSPrefix: 'bq-',

    constructor: function(config) {
        if (typeof(bq) == "undefined")
            bq = {};
        /*
        config = config || {};
        Ext.apply(config, {root: '/'}, bq);
        this.initConfig(config);
        */
        return this.callParent(arguments);        
    },   

    url : function (base, params) {
        if (this.root && this.root != "/")
            return this.root + base;
        return base;
    },
});

// instantiate a global variable, it might get owerwritten later 
bq = Ext.create('BQ');


//--------------------------------------------------------------------------------------
// BQ.Application
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.Application', {
    extend: 'Ext.util.Observable',

    constructor: function(config) {
        this.addEvents({
            "signedin" : true,
            "signedout" : true,
            "gotuser" : true,
            "nouser" : true,                           
        });
        config = config || {};
        this.callParent();

        config.config = config.config || {};                
        this.onReady();        
        this.main = Ext.create('BQ.Application.Window', config.config);
        
        BQSession.initialize_timeout('', { 
            onsignedin: callback(this, this.onSignedIn), 
            onsignedout: callback(this, this.onSignedOut),
            ongotuser: callback(this, this.onGotUser),
            onnouser: callback(this, this.onNoUser),            
        });
        
        return this;
    },
    
    onReady : function()
    {
        // Load user information for all users.
        BQFactory.request({
            uri :   bq.url('/data_service/user?view=deep&wpublic=true'),
            cb  :   Ext.bind(userInfoLoaded, this)
        });
        
        function userInfoLoaded(data)
        {
            this.userList = {};
            
            for (var i=0; i<data.children.length;i++)
                this.userList[data.children[i].uri] = data.children[i];
        }
    },
    
    onSignedIn: function() {
        this.session = BQSession.current_session;
        this.fireEvent( 'signedin', BQSession.current_session);
    },
    
    onSignedOut: function() {
        this.session = undefined;
        this.fireEvent( 'signedout');
        alert("Your session has  timed out");
        window.location = this.url( "/auth_service/logout" );
    },
    
    onGotUser: function() {
        this.user = BQSession.current_session.user;
        this.fireEvent( 'gotuser', BQSession.current_session.user);
        BQ.Preferences.loadUser(BQSession.current_session.user, 'INIT');
    }, 

    onNoUser: function() {
        this.user = null;
        this.fireEvent( 'nouser');
        BQ.Preferences.loadUser(null, 'LOADED');
    }, 

    hasUser: function() {
        return (this.session && this.user);
    },

    getCenterComponent: function() {
        if (this.main)
            return this.main.getCenterComponent();
    },

    setCenterComponent: function(c) {
        if (!this.main) return;
        this.main.setCenterComponent(c);  
    },

    getToolbar: function() {
        if (this.main)
            return this.main.getToolbar();
    },

    setLoading: function(load, targetEl) {
        if (!this.main) return;
        var w = this.getCenterComponent() || this.main;
        w.setLoading(load, targetEl);
    },

});

//--------------------------------------------------------------------------------------
// BQ.Application.Window
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.Application.Window', {
    extend: 'Ext.container.Viewport',
    requires: ['Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],
   
    id : 'appwindow',
    layout : 'border',
    border : false,
    
    /*
    constructor: function(config) {
        this.initConfig(config);
        return this.callParent(arguments);        
    },
    */    

    initComponent : function() {
        Ext.tip.QuickTipManager.init();
        
        var content = document.getElementById('content');
        if (content && content.children.length<1) {
          document.body.removeChild(content);
          content = undefined;
        }
        
        this.toolbar = Ext.create('BQ.Application.Toolbar', { toolbar_opts: bq.toolbar_opts });
        this.items = [
                this.toolbar, { 
                    region : 'center',
                    id: 'centerEl',
                    layout: 'fit',
                    flex: 3,
                    border : false,
                    header : false,
                    contentEl : content,
                    autoScroll: true,
                }, { 
                    id: 'help',
                    region : 'east',
                    collapsible: true,
                    split: true,
                    layout: 'fit',
                    hidden: true,
                    cls: 'help',
                    width: 320,
                    //flex: 1,
                    border : false,
                }, ];
        
        this.callParent();
    },

    // private
    onDestroy : function(){
        this.callParent();
    },
    
    removeWindowContent: function() {
        var c = this.getComponent('centerEl');
        c.removeAll();
        c.update(''); 
    },

    getCenterComponent: function() {
        return this.getComponent('centerEl');  
    },   

    setCenterComponent: function(c) {
        this.removeWindowContent(); 
        this.getComponent('centerEl').add(c);  
    },    
    
    getHelpComponent: function() {
        return this.getComponent('help');  
    },       

    getToolbar: function() {
        return this.toolbar;  
    },  
    
});

BQ.Application.Window.prototype.test = function () {
  alert('test');
}

Ext.define('BisqueServices', {
    singleton : true,
    
    constructor : function()
    {
        BQFactory.request(
        {
            uri : '/services',
            cb : Ext.bind(this.servicesLoaded, this)
        });
    },
    
    servicesLoaded : function(list)
    {
        this.services=[];
        
        for (var i=0;i<list.tags.length;i++)
            this.services[list.tags[i].type.toLowerCase()]=list.tags[i];
    },
    
    getURL : function(serviceName)
    {
        var service = this.services[serviceName];
        return (service)?service.value:'';
    }
})

//--------------------------------------------------------------------------------------
// BisqueService
//-------------------------------------------------------------------------------------- 

BisqueService = function (urllist) {
    this.urls = urllist;
    if (this.urls.length) 
        this.url = this.urls[0];
}

BisqueService.prototype.make_url  = function (path, params) {
    var url = this.url;
    if (path) 
        url = url + '/' + path;
    if (params) 
        url = url + '?' +  encodeParameters (params );
    return url;
}
BisqueService.prototype.xmlrequest  = function (path, params, cb, body) {
    var method = null;
    var url = this.make_url (path, params);
    if (body) 
        method = 'post';
    xmlrequest (url, cb, method, body);
}
BisqueService.prototype.request  = function (path, params, cb, body) {
    var method = null;
    var url = this.make_url (path, params);
    if (body) 
        method = 'post';
    BQFactory.request ({ uri:url, callback:cb, method:method, body:body});
}

Bisque = function () {
    this.services = {};
}

Bisque.prototype.init = function () {
    BQFactory.load ("/services", callback (this, 'on_init'));
}
Bisque.prototype.on_init = function (resource) {
    // Each each tag type to 
    var tags = resource.tags;
    for (var i=0; i<tags.length; i++) {
        var ty = tags[i].type;
        var uri = tags[i].value; 
        Bisque[ty] = new BisqueService (uri);
    }
}

Bisque.onReady  = function (f) {
    Ext.onReady (f);
}
Bisque.init_services = function (services) {
    for (var ty in services) {
        Bisque[ty] = new  BisqueService (services[ty]);
    }
}



//Ext.require(['*']);
Ext.require(['Ext.toolbar.Toolbar']);
Ext.require(['Ext.tip.QuickTip']);
Ext.require(['Ext.tip.QuickTipManager']);

//--------------------------------------------------------------------------------------
// Toolbar actions
//-------------------------------------------------------------------------------------- 

var urlAction = function(url) { 
    window.open(url); 
}; 
  
var pageAction = function(url) { 
    document.location = url; 
};   

var htmlAction = function( url, title ) {
  var c = {
      modal: true,
      //width: '60%',
      //height: '60%',
      width: BQApp?BQApp.getCenterComponent().getWidth()/1.6:document.width/1.6,
      height: BQApp?BQApp.getCenterComponent().getHeight()/1.2:document.height/1.2,
      
      buttonAlign: 'center',
      autoScroll: true,
      loader: { url: url, renderer: 'html', autoLoad: true },
      buttons: [ { text: 'Ok', handler: function () { w.close(); } }]
   };
   if (title && typeof title == 'string') c.title = title;
   
   var w = Ext.create('Ext.window.Window', c);
   w.show();           
}; 

function analysisAction(o, e) {
    //if (typeof BQApp.resource == 'undefined') {
    //    pageAction('/analysis/');
    //    return;
    //}

    var w = Math.round(Math.min(500, BQApp?BQApp.getCenterComponent().getWidth()*0.8:document.width*0.8));    
    var h = Math.round(BQApp?BQApp.getCenterComponent().getHeight()*0.99:document.height*0.99);
    
    //var resourceBrowser  = new Bisque.ResourceBrowser.Dialog({    
    var resourceBrowser  = Ext.create('Bisque.ResourceBrowser.Browser', {
        layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.IconList,
        wpublic: true,
        selType: 'SINGLE',        
        viewMode: 'ModuleBrowser',
        showOrganizer: false,
        dataset : '/module_service/',
        listeners : { 
            'Select' : function(rb, module) {
                if (BQApp.resource) 
                    pageAction('/module_service/' + module.name + '/?resource=' + BQApp.resource.uri)
                else    
                    pageAction('/module_service/' + module.name)
            },
        }
    });

    var tip = Ext.create('Ext.tip.ToolTip', {
        target: o.el,
        anchor: "right",
        width :  w,
        maxWidth: w,
        minWidth: w,
        height:  h,
        layout: 'fit',
        autoHide: false,
        shadow: true,
        items: [resourceBrowser],
                        
    }); 
    tip.show();   
}

//--------------------------------------------------------------------------------------
// Main Bisque toolbar menu
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.Application.Toolbar', {
    extend: 'Ext.toolbar.Toolbar',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    // default toolbar config
    region: 'north', 
    border: false,             
    layout: { overflowHandler: 'Menu',  },
    defaults: { scale: 'large',  },
    cls: 'toolbar-main',
    preferences : {},
    
    title: 'Bisque demo', 
    toolbar_opts: { 'browse':true, 'upload':true, 'download':true, 'services':true, 'query':true },   
    image_query_text: 'Find images using tags',

    tools_big_screen: [ 'button_upload', 'button_download' ],  
    
    tools_none: [ 'menu_user_signin', 'menu_user_register', 'menu_user_register_sep','menu_user_recover' ],    
    tools_user: ['menu_user_name', 'menu_user_profile', 'menu_user_signout', 'menu_user_prefs', 
                 'menu_user_signout_sep', 'menu_resource_template', 'menu_resource_create', ],
    tools_admin: ['menu_user_admin_separator', 'menu_user_admin', 'menu_user_admin_prefs', ],    
    
    initComponent : function() {
        this.images_base_url = this.images_base_url || bq.url('/images/toolbar/');
        this.title = bq.title || this.title;        
        
        Ext.QuickTips.init();
        Ext.tip.QuickTipManager.init();
        var toolbar = this;        
       
        BQ.Preferences.get({
            key : 'Toolbar',
            callback : Ext.bind(this.onPreferences, this),
        });
       
        //--------------------------------------------------------------------------------------
        // Services menu
        //--------------------------------------------------------------------------------------   

        this.menu_services = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{
                text: 'Analysis', 
                handler: analysisAction, 
            }, '-', {
                text: 'Import', 
                iconCls: 'icon-import',
                handler: Ext.Function.pass(pageAction, '/import/'),
            }, {
                text: 'Export', 
                iconCls: 'icon-export',            
                handler: Ext.Function.pass(pageAction, '/export/'),
            }, '-', {
                text: 'Statistics', 
                handler: Ext.Function.pass(pageAction, '/stats/'),
            }],       
        };                       

        //--------------------------------------------------------------------------------------
        // User menu
        //--------------------------------------------------------------------------------------   
        
        // Sign in menu item
        var signin = { 
            itemId: 'menu_user_signin', 
            plain: true,
            xtype: 'form',
            id: 'login_form',
            layout: 'form', // uncomment for extjs 4.1
            cls: 'loginmenu',
            standardSubmit: true,
            border: false,
            bodyBorder: false,            
            url: '/auth_service/login_check',
            width: 350,
            fieldDefaults: {
                msgTarget: 'side',
                border: 0,
            },
            items: [{
                xtype: 'hiddenfield',
                name: 'came_from',
                value: document.location,
                allowBlank: true,
            }, {
                xtype: 'textfield',
                fieldLabel: 'User name',
                name: 'login',
                //id: 'loginusername',
                inputId: 'loginusername',
                allowBlank: false,  
                
                fieldSubTpl: [ // note: {id} here is really {inputId}, but {cmpId} is available
                    '<input id="{id}" type="{type}" {inputAttrTpl}',
                        ' size="1"', // allows inputs to fully respect CSS widths across all browsers
                        '<tpl if="name"> name="{name}"</tpl>',
                        '<tpl if="value"> value="{[Ext.util.Format.htmlEncode(values.value)]}"</tpl>',
                        '<tpl if="placeholder"> placeholder="{placeholder}"</tpl>',
                        '<tpl if="maxLength !== undefined"> maxlength="{maxLength}"</tpl>',
                        '<tpl if="readOnly"> readonly="readonly"</tpl>',
                        '<tpl if="disabled"> disabled="disabled"</tpl>',
                        '<tpl if="tabIdx"> tabIndex="{tabIdx}"</tpl>',
                        '<tpl if="fieldStyle"> style="{fieldStyle}"</tpl>',
                    ' class="{fieldCls} {typeCls} {editableCls}" autocomplete="on" autofocus="true" />',
                    {
                        disableFormats: true,
                    }
                ],                                                       
                            
                listeners: {
                    specialkey: function(field, e){
                        if (e.getKey() == e.ENTER) {
                            var form = field.up('form').getForm();
                            form.submit();
                        }
                    }
                },                                                                                                               
            }],
    
            buttons: [{
                xtype: 'button',
                text: 'Sign in',
                formBind: true, //only enabled once the form is valid
                disabled: true, // uncomment for extjs 4.1
                handler: function() {
                    var form = this.up('form').getForm();
                    if (form.isValid())
                        form.submit();
                }
            }],
            
            autoEl: {
                tag: 'form',
            },
            
            listeners: {
                render: function() {
                    this.el.set({ autocomplete: 'on' });
                },
            },                                    
        };      
        
        this.menu_user = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{
                plain: true,
                cls: 'toolbar-menu',
            }, {
                xtype:'tbtext', 
                itemId: 'menu_user_name', 
                text: 'Sign in', 
                indent: true, 
                hidden: true, 
                cls: 'menu-heading', 
            }, {
                text: 'Profile', 
                itemId: 'menu_user_profile', 
                hidden: true, 
                handler: Ext.Function.pass(pageAction, bq.url('/registration/edit_user')),
            }, { 
                xtype:'menuseparator', 
                itemId: 'menu_user_admin_separator', 
                hidden: true, 
            }, {
                text: 'Website admin', 
                itemId: 'menu_user_admin', 
                hidden: true, 
                handler: Ext.Function.pass(pageAction, bq.url('/admin')), 
            }, { 
                text: 'User preferences', 
                itemId: 'menu_user_prefs', 
                handler: this.userPrefs, 
                scope: this, 
                hidden: true, 
            }, { 
                text: 'System preferences', 
                itemId: 'menu_user_admin_prefs', 
                hidden:true, 
                handler: this.systemPrefs, 
                scope: this, 
            }, {
                xtype: 'menuseparator', 
                itemId: 'menu_user_signout_sep', 
                hidden: true, 
            }, {
                text: 'Sign out', 
                itemId: 'menu_user_signout', 
                hidden: true, 
                handler: Ext.Function.pass(pageAction, bq.url('/auth_service/logout_handler')), 
            }, signin, {
                xtype: 'menuseparator', 
                itemId: 'menu_user_register_sep', 
            }, {
                text: 'Register new user', 
                itemId: 'menu_user_register', 
                handler: Ext.Function.pass(pageAction, bq.url(this.preferences.registration || '/registration')), 
            }, {
                text: 'Recover Password', 
                itemId: 'menu_user_recover', 
                handler: Ext.Function.pass(pageAction, bq.url(this.preferences.registration || '/registration/lost_password')), 
            }],
        };

        //--------------------------------------------------------------------------------------
        // Help menu
        //--------------------------------------------------------------------------------------
        var menu_help = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{ 
                xtype:'tbtext', 
                text: '<img src="'+this.images_base_url+'bisque_logo_white_170.png" style="width: 96px; height: 77px; margin: 10px; margin-left: 30px;" />', 
                indent: true, 
            }, {
                text: 'About Bisque', 
                //handler: Ext.Function.pass(htmlAction, [bq.url('/client_service/public/about/about.html'), 'About Bisque'] ), 
                handler: Ext.Function.pass(htmlAction, [bq.url('/client_service/about'), 'About Bisque'] ), 
            }, {
                text: 'Privacy policy', 
                handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/privacypolicy.html')), 
            }, {
                text: 'Terms of use', 
                handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/termsofuse.html') ),
            }, {
                text: 'License', 
                handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/license.html') ),
            }, '-', {
                text: 'Usage statistics', 
                handler: Ext.Function.pass(pageAction, bq.url('/usage/') ),
            }, '-', {
                text: 'Online Help', 
                handler: Ext.Function.pass(urlAction, bq.url('/client_service/help')),
            }, {
                text: 'Bisque project website', 
                handler: Ext.Function.pass(urlAction, 'http://www.bioimage.ucsb.edu/downloads/Bisque%20Database'), 
            }, '-', {
                xtype:'tbtext', text: 'Problems with Bisque?', 
                indent: true, 
                cls: 'menu-heading', 
            }, {
                text: 'Developers website', 
                handler: Ext.Function.pass(urlAction, 'http://biodev.ece.ucsb.edu/projects/bisquik'),
            }, {
                text: 'Submit a bug or suggestion', 
                handler: Ext.Function.pass(urlAction, 'http://biodev.ece.ucsb.edu/projects/bisquik/newticket'),
            }, {
                text: 'Send us e-mail', 
                handler: Ext.Function.pass(urlAction, 'mailto:bisque-dev@biodev.ece.ucsb.edu,bisque-bioimage@googlegroups.com'),
            }],
        };                                        
        
        
        //--------------------------------------------------------------------------------------
        // Toolbar items
        //-------------------------------------------------------------------------------------- 
        var browse_vis = (this.toolbar_opts && this.toolbar_opts.browse===false) ? false : true;        
        this.items = [{ 
                xtype:'tbtext', 
                text: '<img src="'+this.images_base_url+'bisque_logo_100px.png" style="width: 58px; height: 38px; margin-right: 5px; margin-left: 5px;" />',
            }, { 
                xtype:'tbtext', 
                itemId: 'menu_title', 
                text: '<h3><a href="/">'+this.title+'</a></h3>', 
            }, { 
                xtype: 'tbspacer', 
                width: 40, 
            }, {
                xtype : 'button',
                itemId: 'button_services', 
                menu  : this.menu_services,
                iconCls : 'icon-services', 
                text  : 'Services', 
            }, { 
                text: 'Upload', 
                itemId: 'button_upload', 
                iconCls : 'icon-import',
                handler: Ext.Function.pass(pageAction, bq.url('/import/upload')),
                tooltip: '', 
            }, { 
                text: 'Download', 
                itemId: 'button_download', 
                iconCls : 'icon-export', 
                handler: Ext.Function.pass(pageAction, '/export/'),
                tooltip: '', 
            }, {
                itemId: 'menu_images', 
                xtype:'splitbutton', 
                text: 'Images', 
                iconCls : 'icon-browse', 
                hidden: !browse_vis, 
                tooltip: 'Browse images',
                //menu: [{text: 'Menu Button 1'}], 
                handler: function(c) { 
                    var q = '';
                    var m = toolbar.queryById('menu_query');
                    if (m && m.value != toolbar.image_query_text) { q = '?tag_query='+escape(m.value); }
                    document.location = bq.url('/client_service/browser'+q); 
                },
            }, {
                itemId: 'menu_resources', 
                text: 'Resources', 
                iconCls : 'icon-browse', 
                hidden: browse_vis, 
                tooltip: 'Browse resources',
            }, { 
                xtype: 'tbspacer', 
                width: 10, 
                hidden: !browse_vis,
            }, {
                itemId: 'menu_query', 
                xtype:'textfield', 
                flex: 2, 
                name: 'search', 
                value: this.image_query_text, 
                hidden: !browse_vis,
                minWidth: 60,
                tooltip: 'Query for images using Bisque expressions',  
                enableKeyEvents: true,
                listeners: {
                    focus: function(c) { 
                        if (c.value == toolbar.image_query_text) c.setValue(''); 
                        var tip = Ext.create('Ext.tip.ToolTip', {
                            target: c.el,
                            anchor: 'top',
                            minWidth: 500, 
                            width: 500,                          
                            autoHide: true,
                            dismissDelay: 20000,
                            shadow: true,
                            autoScroll: true,
                            loader: { url: '/html/querying.html', renderer: 'html', autoLoad: true },
                        }); 
                        tip.show();                           
                    },
                    specialkey: function(f, e) { 
                        if (e.getKey()==e.ENTER && f.value!='' && f.value != toolbar.image_query_text) {
                            document.location = bq.url('/client_service/browser?tag_query='+escape(f.value)); 
                        }                         
                    },
                }
            }, '->', { 
                itemId: 'menu_user', 
                menu: this.menu_user, 
                iconCls: 'icon-user', 
                text: 'Sign in', 
                tooltip: 'Edit your user account', 
                plain: true,
            }, { 
                menu: menu_help, 
                iconCls: 'icon-help', 
                tooltip: 'All information about Bisque',
            }, 
        ];

        //--------------------------------------------------------------------------------------
        // final touches
        //--------------------------------------------------------------------------------------         
        this.addListener( 'resize', this.onResized, this);        
        this.callParent();

        // update user menu based on application events
        Ext.util.Observable.observe(BQ.Application);        
        BQ.Application.on('gotuser', function(u) { 
            this.queryById('menu_user').setText( u.display_name );
            this.queryById('menu_user_name').setText( u.display_name+' - '+u.email_address );
            
            // hide no user menus
            for (var i=0; (p=this.tools_none[i]); i++)
                this.setSubMenuVisibility(p, false);

            // show user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.setSubMenuVisibility(p, true);

            // show admin menus
            if (u.user_name == 'admin')
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.setSubMenuVisibility(p, true);

        }, this);

        BQ.Application.on('signedin', function() { 
            //clog('signed in !!!!!');           
        });  
                 
        BQ.Application.on('signedout', function() { 
            // show no user menus
            for (var i=0; (p=this.tools_none[i]); i++)
                this.setSubMenuVisibility(p, true);

            // hide user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.setSubMenuVisibility(p, false);

            // hide user menus
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.setSubMenuVisibility(p, false);    
                         
        }, this);  
        
        this.fetchResourceTypes();        
    },

    setSubMenuVisibility: function(id, v) {
        var m = this.queryById(id);
        if (m) m.setVisible(v);
    },

    onResized: function() {
        //tools_big_screen: [ 'button_upload', 'button_download' ], 
        var w = this.getWidth();
        //var w = document.width;
        if (w<1024) {
            for (var i=0; id=this.tools_big_screen[i]; ++i)
               this.queryById(id).setVisible(false);
        } else {
            for (var i=0; id=this.tools_big_screen[i]; ++i)
               this.queryById(id).setVisible(true);          
        }
    },

    userPrefs : function() {
        var preferences = Ext.create('BQ.Preferences.Dialog');
    },

    systemPrefs : function() {
        var preferences = Ext.create('BQ.Preferences.Dialog', {prefType:'system'});
    },

    fetchResourceTypes : function() {
        BQFactory.request ({uri : '/data_service/', 
                            cb : callback(this, 'onResourceTypes'),
                            cache : false});             
    }, 

    onResourceTypes : function(resource) {
        var menu = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{
                text: 'dataset', 
                handler: Ext.Function.pass(pageAction, '/client_service/browser?resource=/data_service/dataset'),
            }],
        };

        BQApp.resourceTypes = [];
        var r=null;
        for (var i=0; (r=resource.children[i]); i++) {
            BQApp.resourceTypes.push({name:r.name, uri:r.uri});
            if (r.name == 'dataset') continue;
            var name = r.name;
            var uri = r.uri;            
            menu.items.push({
                text: name, 
                handler: Ext.Function.pass(pageAction, '/client_service/browser?resource='+uri),
            });
        }
        
        menu.items.push('-');
        menu.items.push({
            text    : 'Create a new resource', 
            itemId  : 'menu_resource_create', 
            handler : function() {this.createResource(resource);},
            scope   : this, 
            hidden  : !BQApp.hasUser(),
        });
        menu.items.push({
            itemId  : 'menu_resource_template', 
            text    : 'Create resource from template', 
            handler : function() {this.createResourceFromTemplate()},
            scope   : this, 
            hidden  : !BQApp.hasUser()
        });

        menu = Ext.create('Ext.menu.Menu', menu);
        this.queryById('menu_images').menu = menu;
        this.queryById('menu_resources').menu = menu;        
    },
    
    createResourceFromTemplate  :   function(template)
    {
        if (!template)
        {
            BQFactory.request({
                uri     :   '/data_service/template/',
                cb      :   Ext.bind(this.createResourceFromTemplate, this),
                errorcb :   function(error){BQ.ui.error('createResourceFromTemplate: Error occured while fetching list of available templates.'+error.message, 4000)}
                }
            )
            
            return;
        }
        
        var store = Ext.create('Ext.data.Store', {
            fields  :   ['name', 'uri'],
            data    :   template.children
        });
        
        var formPanel = Ext.create('Ext.form.Panel',
        {
            frame           :   true,
            width           :   350,
            defaultType     :   'textfield',
            bodyStyle       :   {
                                    padding         :   '10px'
                                },
            fieldDefaults   :   {
                                    msgTarget       :   'side',
                                    labelWidth      :   100
                                },
            defaults        :   {
                                    anchor          : '100%',
                                    allowBlank      :   false,
                                },
            items           :   [{
                                    xtype           :   'combobox',
                                    name            :   'template',
                                    fieldLabel      :   'Select template',
                                    store           :   store,
                                    displayField    :   'name',
                                    valueField      :   'uri',
                                    editable        :   false
                                }, {
                                    fieldLabel      :   'Name',
                                    name            :   'name'
                                }]
        });
        
           
        var display = Ext.create('Ext.window.Window',
        {
            items       :   formPanel,
            modal       :   true,
            border      :   false,
            title       :   'Create resource from template',
            buttonAlign :   'center',
            buttons     :   [
                                {
                                    text    :   'Create',
                                    scope   :   this,
                                    margin  :   3,
                                    handler :   function(btn)
                                    {
                                        var form = formPanel.getForm();
                                        
                                        if (form.isValid())
                                        {
                                            var input = form.getValues();
                                            BQ.TemplateManager.createResource({name: input.name}, this.onResourceCreated, input.template+'?view=deep');
                                        }
                                    }
                                },
                                {
                                    text    :   'Cancel',
                                    scope   :   this,
                                    margin  :   3,
                                    handler :   function()
                                    {
                                        display.destroy();
                                    }
                                },
                            ]
        }).show();
        
    },
   
    createResource : function(resource) {
        var ignore = { 'mex':null, 'user':null, 'image':null, 'module':null, 'service':null, 'system':null, 'file':null, 'dataset':null, };        
        var mydata = [['dataset']];
        var r=null;
        for (var i=0; (r=resource.children[i]); i++)
            if (!(r.name in ignore))
                mydata.push( [r.name] );   
        delete ignore.dataset;
        
        store_types = Ext.create('Ext.data.ArrayStore', {
            fields: [ {name: 'name',}, ],        
            data: mydata,
        });                
        
        var formpanel = Ext.create('Ext.form.Panel', {
            //url:'save-form.php',
            frame:true,
            bodyStyle:'padding:5px 5px 0',
            width: 350,
            fieldDefaults: {
                msgTarget: 'side',
                labelWidth: 75
            },
            defaultType: 'textfield',
            defaults: {
                anchor: '100%'
            },
    
            items: [{
                xtype : 'combobox',
                fieldLabel: 'Type',
                name: 'type',
                allowBlank: false,
                
                store     : store_types,
                displayField: 'name',
                valueField: 'name',
                queryMode : 'local',
                
                //invalidText: 'This type is not allowed for creation!',
                validator: function(value) { 
                    if (value in ignore) return 'This type is not allowed for creation!';
                    if (/[^\w]/.test(value)) return 'Resource type may only contain word characters: letters, digits, dash and underscore';
                    return true;
                },
            },{
                fieldLabel: 'Name',
                name: 'name',
                allowBlank: false,                
            }],
    
        });
        
        var w = Ext.create('Ext.window.Window', {
            layout : 'fit',
            modal : true,
            border : false,
            title: 'Create new resource',
            buttonAlign: 'center',
            items: formpanel,
            buttons: [{
                text: 'Save',
                scope: this,
                handler: function () {
                    var form = formpanel.getForm();
                    if (form.isValid()) {
                        var v = form.getValues()
                        var resource = BQFactory.make(v.type, undefined, v.name);
                        resource.save_('/data_service/'+v.type, 
                                       callback(this, this.onResourceCreated), 
                                       callback(this, this.onResourceError));
                        formpanel.ownerCt.hide();                    
                    };                    
                }
            }, {
                text: 'Cancel',
                //scope: this,
                handler: function (me) {
                    formpanel.ownerCt.hide();
                }
            }]            
            
        }).show();
    },    

    onResourceCreated: function(resource) {
        document.location = '/client_service/view?resource='+resource.uri;
    },

    onResourceError: function(message) {
        BQ.ui.error('Error creating resource: <br>'+message);
    },
   
    onPreferences: function(pref) {
        this.preferences = pref;  
        
        if (this.preferences.registration === 'disabled')
            this.queryById('menu_user_register').setVisible(false);        
        
        this.queryById('menu_user_register').setHandler( 
            Ext.Function.pass(pageAction, bq.url(this.preferences.registration || '/registration')), 
            this 
        );

        if (this.preferences.title)
            this.queryById('menu_title').setText( '<h3><a href="/">'+this.preferences.title+'</a></h3>' );
        
    },
   
});


/*

Examples:

    BQ.ui.message('Attention', 'I have news', 1000); 
    
    BQ.ui.error('Something happened...'); 
    BQ.ui.warning('You are not logged in! You need to log-in to run any analysis...'); 
    BQ.ui.notification('Seed detection done! Verify results...');

    BQ.ui.tip( 'my_id', 'Verify results...', {color: 'green', timeout: 10000} );
*/


Ext.namespace('BQ.ui');

function showTip( element, text, opts ) {
  opts = opts || {};
  if (!('color' in opts)) opts.color = 'red';
  if (!('timeout' in opts)) opts.timeout = 5000;  
  opts.anchor = opts.anchor || 'top';    
  
  var tip = new Ext.ToolTip({
      target: element,
      anchor: opts.anchor,
      bodyStyle: 'font-size: 160%; color: '+opts.color+';',        
      html: text
  });
  tip.show();
  setTimeout( function () { tip.destroy(); }, opts.timeout );
}

BQ.ui = function(){
    var msgCt;

    function createBox(t, s, c){
       return '<div class="msg '+c+'"><img src="/images/cancel.png" /><h3>' + t + '</h3><p>' + s + '</p></div>';
    }
    return {
        message: function(title, format, delay, css) {
            if (!msgCt) {
                msgCt = Ext.core.DomHelper.insertFirst(document.body, {id:'messagepopup'}, true);
            }
            if (delay == undefined) delay = 3000;
            if (css == undefined) css = '';            
            var s = Ext.String.format.apply(String, Array.prototype.slice.call(arguments, 1));
            var m = Ext.core.DomHelper.append(msgCt, createBox(title, s, css), true);
            m.hide();
            m.on('click', function(){ 
                    this.stopAnimation();
                    //this.fadeOut( {remove: true} );
                    this.destroy(); 
                }, m, { 
                single: true, 
                stopEvent : true, 
            });
            m.slideIn('t').ghost("t", { delay: delay, remove: true});
        },

        popup: function(type, text, delay) {
            var t = BQ.ui.types[type] || BQ.ui.types['notification'];
            BQ.ui.message( t.title, text, delay || t.delay, t.cls );
        },

        notification: function(text, delay) {
            BQ.ui.popup('notification', text, delay );
        },

        attention: function(text, delay) {
            BQ.ui.popup('attention', text, delay );
        },
        
        warning: function(text, delay) {
            BQ.ui.popup('warning', text, delay );            
        },        

        error: function(text, delay) {
            BQ.ui.popup('error', text, delay );
        },
  
        tip: function( element, text, opts ) {
            opts = opts || {};
            if (!('color' in opts)) opts.color = 'red';
            if (!('timeout' in opts)) opts.timeout = 5000;  
            opts.anchor = opts.anchor || 'top';               
            var tip = new Ext.ToolTip({
              target: element,
              anchor: opts.anchor,
              bodyStyle: 'font-size: 160%; color: '+opts.color+';',        
              html: text
            });
            tip.show();
            setTimeout( function () { tip.destroy(); }, opts.timeout );
        },

        highlight: function( element, text, opts ) {
            opts = opts || {};
            opts.timeout = opts.timeout || 5000;  
            opts.anchor = opts.anchor || 'top';    
            
            var w = Ext.create('Ext.ToolTip', Ext.apply({
              target: element,
              anchor: opts.anchor,
              cls: 'highlight',
              html: text,
              autoHide: false,
              shadow: false,
            }, opts));
            w.show();
            w.getEl().fadeOut({ delay: opts.timeout});//.fadeOut({ delay: opts.timeout, remove: true});
        },

    };
}();

BQ.ui.types = {
    'notification': { delay: 5000,  title: '',        cls: 'notification' },
    'attention':    { delay: 10000, title: '',        cls: 'warning' },
    'warning':      { delay: 10000, title: 'Warning', cls: 'warning' },
    'error':        { delay: 50000, title: 'Error',   cls: 'error' },            
};


//  var start = new Date();
//  var end   = new Date();    
//  start.setISO8601('YYYY-MM-DDTHH:mm:SS');
//  end.setISO8601('YYYY-MM-DDTHH:mm:SS');      
//  var time_string = end.diff(start).toString();


      
// extension for Date class to parse ISO8901 variants      
// ex: "2010-10-13T16:52:35" "2010-10-13 16:52:35" 
// ex: "2010-10-13" "2010-10"    
Date.prototype.setISO8601 = function (string) {
    var regexp = "([0-9]{4})(-([0-9]{2})(-([0-9]{2})" +
        "([T|\\s]([0-9]{2}):([0-9]{2})(:([0-9]{2})(\.([0-9]+))?)?" +
        "(Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?";
    var d = string.match(new RegExp(regexp));

    var offset = 0;
    var date = new Date(d[1], 0, 1);

    if (d[3]) { date.setMonth(d[3] - 1); }
    if (d[5]) { date.setDate(d[5]); }
    if (d[7]) { date.setHours(d[7]); }
    if (d[8]) { date.setMinutes(d[8]); }
    if (d[10]) { date.setSeconds(d[10]); }
    if (d[12]) { date.setMilliseconds(Number("0." + d[12]) * 1000); }

    this.setTime(Number(date));
}

Date.prototype.setISO = function (string) {
    return this.setISO8601(string);
}

Date.prototype.toISOString = function () {
    function pad(n){return n<10 ? '0'+n : n};
    return this.getFullYear()+'-'+ 
           pad(this.getMonth()+1)+'-'+
           pad(this.getDate())+' '+
           pad(this.getHours())+':'+
           pad(this.getMinutes())+':'+
           pad(this.getSeconds());
}


Date.prototype.diff = function (another) {
    return new DateDiff(this - another);
}


//------------------------------------------------------------------------------
// Date time difference
//------------------------------------------------------------------------------

function DateDiff(ms) {
    this.weeks = 0; this.days = 0; 
    this.hours = 0; this.mins = 0; this.secs = 0; this.msecs = 0;  
    this.fromMS(ms);    
}

DateDiff.prototype.fromMS = function ( diff ) { 
    if (!diff) return;   
    this.weeks = 0; this.days = 0; 
    this.hours = 0; this.mins = 0; this.secs = 0; this.msecs = 0;  
    
    this.weeks = Math.floor(diff / (1000 * 60 * 60 * 24 * 7));
    diff -= this.weeks * (1000 * 60 * 60 * 24 * 7);

    this.days = Math.floor(diff / (1000 * 60 * 60 * 24)); 
    diff -= this.days * (1000 * 60 * 60 * 24);

    this.hours = Math.floor(diff / (1000 * 60 * 60)); 
    diff -= this.hours * (1000 * 60 * 60);
    
    this.mins = Math.floor(diff / (1000 * 60)); 
    diff -= this.mins * (1000 * 60);
    
    this.secs = Math.floor(diff / 1000); 
    diff -= this.secs * 1000;
    
    this.msecs = diff; 
}

DateDiff.prototype.toString = function () {
  var s = '';
  if (this.weeks>0) s += ''+ this.weeks +' weeks ';
  if (this.days>0)  s += ''+ this.days  +' days ';
  if (this.hours>0) s += ''+ this.hours +' hours ';
  if (this.mins>0)  s += ''+ this.mins  +' minutes ';    
  if (this.secs>0)  s += ''+ this.secs  +' seconds ';  
  if (s=='' && this.msecs>0)  s += ''+ this.msecs  +'ms';  
  return s;
}

/**
 * A Javascript object to encode and/or decode html characters
 * @Author R Reid
 * source: http://www.strictly-software.com/htmlencode
 * Licence: GPL
 * 
 * Revision:
 *  2011-07-14, Jacques-Yves Bleau: 
 *       - fixed conversion error with capitalized accentuated characters
 *       + converted arr1 and arr2 to object property to remove redundancy
 */

Encoder = {

	// When encoding do we convert characters into html or numerical entities
	EncodeType : "entity",  // entity OR numerical

	isEmpty : function(val){
		if(val){
			return ((val===null) || val.length==0 || /^\s+$/.test(val));
		}else{
			return true;
		}
	},
	arr1: new Array('&nbsp;','&iexcl;','&cent;','&pound;','&curren;','&yen;','&brvbar;','&sect;','&uml;','&copy;','&ordf;','&laquo;','&not;','&shy;','&reg;','&macr;','&deg;','&plusmn;','&sup2;','&sup3;','&acute;','&micro;','&para;','&middot;','&cedil;','&sup1;','&ordm;','&raquo;','&frac14;','&frac12;','&frac34;','&iquest;','&Agrave;','&Aacute;','&Acirc;','&Atilde;','&Auml;','&Aring;','&Aelig;','&Ccedil;','&Egrave;','&Eacute;','&Ecirc;','&Euml;','&Igrave;','&Iacute;','&Icirc;','&Iuml;','&ETH;','&Ntilde;','&Ograve;','&Oacute;','&Ocirc;','&Otilde;','&Ouml;','&times;','&Oslash;','&Ugrave;','&Uacute;','&Ucirc;','&Uuml;','&Yacute;','&THORN;','&szlig;','&agrave;','&aacute;','&acirc;','&atilde;','&auml;','&aring;','&aelig;','&ccedil;','&egrave;','&eacute;','&ecirc;','&euml;','&igrave;','&iacute;','&icirc;','&iuml;','&eth;','&ntilde;','&ograve;','&oacute;','&ocirc;','&otilde;','&ouml;','&divide;','&Oslash;','&ugrave;','&uacute;','&ucirc;','&uuml;','&yacute;','&thorn;','&yuml;','&quot;','&amp;','&lt;','&gt;','&oelig;','&oelig;','&scaron;','&scaron;','&yuml;','&circ;','&tilde;','&ensp;','&emsp;','&thinsp;','&zwnj;','&zwj;','&lrm;','&rlm;','&ndash;','&mdash;','&lsquo;','&rsquo;','&sbquo;','&ldquo;','&rdquo;','&bdquo;','&dagger;','&dagger;','&permil;','&lsaquo;','&rsaquo;','&euro;','&fnof;','&alpha;','&beta;','&gamma;','&delta;','&epsilon;','&zeta;','&eta;','&theta;','&iota;','&kappa;','&lambda;','&mu;','&nu;','&xi;','&omicron;','&pi;','&rho;','&sigma;','&tau;','&upsilon;','&phi;','&chi;','&psi;','&omega;','&alpha;','&beta;','&gamma;','&delta;','&epsilon;','&zeta;','&eta;','&theta;','&iota;','&kappa;','&lambda;','&mu;','&nu;','&xi;','&omicron;','&pi;','&rho;','&sigmaf;','&sigma;','&tau;','&upsilon;','&phi;','&chi;','&psi;','&omega;','&thetasym;','&upsih;','&piv;','&bull;','&hellip;','&prime;','&prime;','&oline;','&frasl;','&weierp;','&image;','&real;','&trade;','&alefsym;','&larr;','&uarr;','&rarr;','&darr;','&harr;','&crarr;','&larr;','&uarr;','&rarr;','&darr;','&harr;','&forall;','&part;','&exist;','&empty;','&nabla;','&isin;','&notin;','&ni;','&prod;','&sum;','&minus;','&lowast;','&radic;','&prop;','&infin;','&ang;','&and;','&or;','&cap;','&cup;','&int;','&there4;','&sim;','&cong;','&asymp;','&ne;','&equiv;','&le;','&ge;','&sub;','&sup;','&nsub;','&sube;','&supe;','&oplus;','&otimes;','&perp;','&sdot;','&lceil;','&rceil;','&lfloor;','&rfloor;','&lang;','&rang;','&loz;','&spades;','&clubs;','&hearts;','&diams;'),
	arr2: new Array('&#160;','&#161;','&#162;','&#163;','&#164;','&#165;','&#166;','&#167;','&#168;','&#169;','&#170;','&#171;','&#172;','&#173;','&#174;','&#175;','&#176;','&#177;','&#178;','&#179;','&#180;','&#181;','&#182;','&#183;','&#184;','&#185;','&#186;','&#187;','&#188;','&#189;','&#190;','&#191;','&#192;','&#193;','&#194;','&#195;','&#196;','&#197;','&#198;','&#199;','&#200;','&#201;','&#202;','&#203;','&#204;','&#205;','&#206;','&#207;','&#208;','&#209;','&#210;','&#211;','&#212;','&#213;','&#214;','&#215;','&#216;','&#217;','&#218;','&#219;','&#220;','&#221;','&#222;','&#223;','&#224;','&#225;','&#226;','&#227;','&#228;','&#229;','&#230;','&#231;','&#232;','&#233;','&#234;','&#235;','&#236;','&#237;','&#238;','&#239;','&#240;','&#241;','&#242;','&#243;','&#244;','&#245;','&#246;','&#247;','&#248;','&#249;','&#250;','&#251;','&#252;','&#253;','&#254;','&#255;','&#34;','&#38;','&#60;','&#62;','&#338;','&#339;','&#352;','&#353;','&#376;','&#710;','&#732;','&#8194;','&#8195;','&#8201;','&#8204;','&#8205;','&#8206;','&#8207;','&#8211;','&#8212;','&#8216;','&#8217;','&#8218;','&#8220;','&#8221;','&#8222;','&#8224;','&#8225;','&#8240;','&#8249;','&#8250;','&#8364;','&#402;','&#913;','&#914;','&#915;','&#916;','&#917;','&#918;','&#919;','&#920;','&#921;','&#922;','&#923;','&#924;','&#925;','&#926;','&#927;','&#928;','&#929;','&#931;','&#932;','&#933;','&#934;','&#935;','&#936;','&#937;','&#945;','&#946;','&#947;','&#948;','&#949;','&#950;','&#951;','&#952;','&#953;','&#954;','&#955;','&#956;','&#957;','&#958;','&#959;','&#960;','&#961;','&#962;','&#963;','&#964;','&#965;','&#966;','&#967;','&#968;','&#969;','&#977;','&#978;','&#982;','&#8226;','&#8230;','&#8242;','&#8243;','&#8254;','&#8260;','&#8472;','&#8465;','&#8476;','&#8482;','&#8501;','&#8592;','&#8593;','&#8594;','&#8595;','&#8596;','&#8629;','&#8656;','&#8657;','&#8658;','&#8659;','&#8660;','&#8704;','&#8706;','&#8707;','&#8709;','&#8711;','&#8712;','&#8713;','&#8715;','&#8719;','&#8721;','&#8722;','&#8727;','&#8730;','&#8733;','&#8734;','&#8736;','&#8743;','&#8744;','&#8745;','&#8746;','&#8747;','&#8756;','&#8764;','&#8773;','&#8776;','&#8800;','&#8801;','&#8804;','&#8805;','&#8834;','&#8835;','&#8836;','&#8838;','&#8839;','&#8853;','&#8855;','&#8869;','&#8901;','&#8968;','&#8969;','&#8970;','&#8971;','&#9001;','&#9002;','&#9674;','&#9824;','&#9827;','&#9829;','&#9830;'),
		
	// Convert HTML entities into numerical entities
	HTML2Numerical : function(s){
		return this.swapArrayVals(s,this.arr1,this.arr2);
	},	

	// Convert Numerical entities into HTML entities
	NumericalToHTML : function(s){
		return this.swapArrayVals(s,this.arr2,this.arr1);
	},


	// Numerically encodes all unicode characters
	numEncode : function(s){
		
		if(this.isEmpty(s)) return "";

		var e = "";
		for (var i = 0; i < s.length; i++)
		{
			var c = s.charAt(i);
			if (c < " " || c > "~")
			{
				c = "&#" + c.charCodeAt() + ";";
			}
			e += c;
		}
		return e;
	},
	
	// HTML Decode numerical and HTML entities back to original values
	htmlDecode : function(s){

		var c,m,d = s;
		
		if(this.isEmpty(d)) return "";

		// convert HTML entites back to numerical entites first
		d = this.HTML2Numerical(d);
		
		// look for numerical entities &#34;
		arr=d.match(/&#[0-9]{1,5};/g);
		
		// if no matches found in string then skip
		if(arr!=null){
			for(var x=0;x<arr.length;x++){
				m = arr[x];
				c = m.substring(2,m.length-1); //get numeric part which is refernce to unicode character
				// if its a valid number we can decode
				if(c >= -32768 && c <= 65535){
					// decode every single match within string
					d = d.replace(m, String.fromCharCode(c));
				}else{
					d = d.replace(m, ""); //invalid so replace with nada
				}
			}			
		}

		return d;
	},		

	// encode an input string into either numerical or HTML entities
	htmlEncode : function(s,dbl){
			
		if(this.isEmpty(s)) return "";

		// do we allow double encoding? E.g will &amp; be turned into &amp;amp;
		dbl = dbl || false; //default to prevent double encoding
		
		// if allowing double encoding we do ampersands first
		if(dbl){
			if(this.EncodeType=="numerical"){
				s = s.replace(/&/g, "&#38;");
			}else{
				s = s.replace(/&/g, "&amp;");
			}
		}

		// convert the xss chars to numerical entities ' " < >
		s = this.XSSEncode(s,false);
		
		if(this.EncodeType=="numerical" || !dbl){
			// Now call function that will convert any HTML entities to numerical codes
			s = this.HTML2Numerical(s);
		}

		// Now encode all chars above 127 e.g unicode
		s = this.numEncode(s);

		// now we know anything that needs to be encoded has been converted to numerical entities we
		// can encode any ampersands & that are not part of encoded entities
		// to handle the fact that I need to do a negative check and handle multiple ampersands &&&
		// I am going to use a placeholder

		// if we don't want double encoded entities we ignore the & in existing entities
		if(!dbl){
			s = s.replace(/&#/g,"##AMPHASH##");
		
			if(this.EncodeType=="numerical"){
				s = s.replace(/&/g, "&#38;");
			}else{
				s = s.replace(/&/g, "&amp;");
			}

			s = s.replace(/##AMPHASH##/g,"&#");
		}
		
		// replace any malformed entities
		s = s.replace(/&#\d*([^\d;]|$)/g, "$1");

		if(!dbl){
			// safety check to correct any double encoded &amp;
			s = this.correctEncoding(s);
		}

		// now do we need to convert our numerical encoded string into entities
		if(this.EncodeType=="entity"){
			s = this.NumericalToHTML(s);
		}

		return s;					
	},

	// Encodes the basic 4 characters used to malform HTML in XSS hacks
	XSSEncode : function(s,en){
		if(!this.isEmpty(s)){
			en = en || true;
			// do we convert to numerical or html entity?
			if(en){
				s = s.replace(/\'/g,"&#39;"); //no HTML equivalent as &apos is not cross browser supported
				s = s.replace(/\"/g,"&quot;");
				s = s.replace(/</g,"&lt;");
				s = s.replace(/>/g,"&gt;");
			}else{
				s = s.replace(/\'/g,"&#39;"); //no HTML equivalent as &apos is not cross browser supported
				s = s.replace(/\"/g,"&#34;");
				s = s.replace(/</g,"&#60;");
				s = s.replace(/>/g,"&#62;");
			}
			return s;
		}else{
			return "";
		}
	},

	// returns true if a string contains html or numerical encoded entities
	hasEncoded : function(s){
		if(/&#[0-9]{1,5};/g.test(s)){
			return true;
		}else if(/&[A-Z]{2,6};/gi.test(s)){
			return true;
		}else{
			return false;
		}
	},

	// will remove any unicode characters
	stripUnicode : function(s){
		return s.replace(/[^\x20-\x7E]/g,"");
		
	},

	// corrects any double encoded &amp; entities e.g &amp;amp;
	correctEncoding : function(s){
		return s.replace(/(&amp;)(amp;)+/,"$1");
	},


	// Function to loop through an array swaping each item with the value from another array e.g swap HTML entities with Numericals
	swapArrayVals : function(s,arr1,arr2){
		if(this.isEmpty(s)) return "";
		var re;
		if(arr1 && arr2){
			//ShowDebug("in swapArrayVals arr1.length = " + arr1.length + " arr2.length = " + arr2.length)
			// array lengths must match
			if(arr1.length == arr2.length){
				for(var x=0,i=arr1.length;x<i;x++){
					re = new RegExp(arr1[x], 'g');
					s = s.replace(re,arr2[x]); //swap arr1 item with matching item from arr2	
				}
			}
		}
		return s;
	},

	inArray : function( item, arr ) {
		for ( var i = 0, x = arr.length; i < x; i++ ){
			if ( arr[i] === item ){
				return i;
			}
		}
		return -1;
	}

}
// Declare namespace for the modules in RecourseBrowser package
Ext.namespace('Bisque.ResourceBrowser');
Ext.require(['Ext.tip.*']);
Ext.tip.QuickTipManager.init();

/**
 * Browser: Main ResourceBrowser class which acts as an interface between
 * ResourceBrowser and other Bisque components
 *
 * @param {}
 *            browserParams : Initial config parameters such as URI, Offset etc.
 */

// ResourceBrowser in a Ext.Window container

Ext.define('Bisque.ResourceBrowser.Dialog',
{
    extend : 'Ext.window.Window',

    constructor : function(config)
    {
        config = config ||
        {
        };
        config.height = config.height || '85%';
        config.width = config.width || '85%';
        config.selType = config.selType || 'MULTI';
        config.showOrganizer = ('showOrganizer' in config)? config.showOrganizer: true;

        var bodySz = Ext.getBody().getViewSize();
        var height = parseInt((config.height.toString().indexOf("%") == -1) ? config.height : (bodySz.height * parseInt(config.height) / 100));
        var width = parseInt((config.width.toString().indexOf("%") == -1) ? config.width : (bodySz.width * parseInt(config.width) / 100));

        Ext.apply(this,
        {
            layout : 'fit',
            title : 'Resource Browser',
            modal : true,
            border : false,
            height : height,
            width : width,
            items : new Bisque.ResourceBrowser.Browser(config),
        }, config);

        this.dockedItems = [
        {
            xtype : 'toolbar',
            dock : 'bottom',
            layout :
            {
                type : 'hbox',
                align : 'middle',
                pack : 'center'
            },
            padding : 10,

            items : [
            {
                xtype : 'buttongroup',
                margin : 5,
                items : [
                {
                    text : 'Select',
                    iconCls : 'icon-select',
                    scale : 'medium',
                    width : 90,
                    handler : this.btnSelect,
                    scope : this
                }]
            },
            {
                xtype : 'buttongroup',
                margin : 5,
                items : [
                {
                    text : 'Cancel',
                    iconCls : 'icon-cancel',
                    textAlign : 'left',
                    scale : 'medium',
                    width : 90,
                    handler : this.destroy,
                    scope : this
                }]
            }]
        }];

        this.callParent([arguments]);

        // Relay all the custom ResourceBrowser events to this Window
        //this.relayEvents(this.getComponent(0), ['Select']);

        this.browser = this.getComponent(0);
        this.browser.on('Select', function(resourceBrowser, resource)
        {
            this.destroy();
        }, this);


        this.show();
    },

    btnSelect : function()
    {
        var selectedRes = this.browser.resourceQueue.selectedRes;
        var selection = Ext.Object.getValues(selectedRes);

        if (selection.length)
            if (selection.length==1)
                this.browser.fireEvent('Select', this, selection[0].resource);
            else
            {
                for (var i=0, selectRes=[]; i<selection.length; i++)
                    selectRes.push(selection[i].resource);
                this.browser.fireEvent('Select', this, selectRes);
            }
        else
            BQ.ui.message('Selection empty!', 'Please select an image or press cancel to abort.');
    },
});

// Bisque.QueryBrowser.Dialog is a query select specialization of Bisque.ResourceBrowser.Dialog
Ext.define('Bisque.QueryBrowser.Dialog', {
    extend : 'Bisque.ResourceBrowser.Dialog',

    btnSelect : function() {
        var query = this.browser.commandBar.getComponent('searchBar').getValue();
        if (query && query.length>1)
            this.browser.fireEvent('Select', this, query);
        else
            BQ.ui.message('Query is empty!', 'Please type a query or press cancel to abort.');
    },
});

// ResourceBrowser in a Ext.Panel container
Ext.define('Bisque.ResourceBrowser.Browser',
{
    extend : 'Ext.panel.Panel',
    alias: 'widget.bq-resource-browser',

    constructor : function(config)
    {
        //Prefetch the loading spinner
        var imgSpinner = new Image();
        imgSpinner.src = bq.url('/js/ResourceBrowser/Images/loading.gif');

        this.westPanel = new Ext.panel.Panel(
        {
            region : 'west',
            split : true,
            layout : 'fit',
            cls: 'organizer',
            frame : true,
            header : false,
            hidden : true,
            collapsible: true,
            hideCollapseTool : true,
            listeners : {
                'beforecollapse' : function(me)
                {
                    me.setTitle(me.getComponent(0).title);
                },
            }
        });

        this.centerPanel = new Ext.Panel(
        {
            region : 'center',
            border : false,
            layout : 'fit',
        });
        config = config || {};

        Ext.apply(this,
        {
            browserParams : config,
            layoutKey : parseInt(config.layout),
            viewMgr : Ext.create('Bisque.ResourceBrowser.viewStateManager', config.viewMode),
            organizerCt : null,
            datasetCt : null,
            layoutMgr : null,
            browserState : {},
            resourceQueue : [],
            msgBus : new Bisque.Misc.MessageBus(),
            gestureMgr : null,
            showGroups : false,
            preferenceKey : 'ResourceBrowser',
            
            //bodyCls : 'background-transparent',
            bodyCls : 'browser-main',
            // Panel related config
            border : false,
            title : config.title || '',
            layout : 'border',
            items : [this.westPanel, this.centerPanel],
            listeners : config.listeners || {},
        }, config);

        this.commandBar = new Bisque.ResourceBrowser.CommandBar(
        {
            browser : this
        });
        this.tbar = this.commandBar;

        this.callParent([arguments]);

        this.loadPreferences();

        if (Ext.supports.Touch)
            this.gestureMgr = new Bisque.Misc.GestureManager();
    },

    loadPreferences : function(preferences, tag)
    {
        if(preferences == undefined)
            BQ.Preferences.get(
            {
                type : 'user',
                key : this.preferenceKey,
                callback : Ext.bind(this.loadPreferences, this)
            });
        else
        // preferences loaded
        {
            this.preferences = preferences;
            this.applyPreferences();

            // defaults (should be loaded from system preferences)
            Ext.apply(this.browserParams,
            {
                layout : this.browserParams.layout || 1,
                dataset : this.browserParams.dataset || '/data_service/image/',
                offset : this.browserParams.offset || 0,
                tagQuery : this.browserParams.tagQuery || '',
                tagOrder : this.browserParams.tagOrder || '"@ts":desc',
                wpublic : (this.browserParams.wpublic == 'true' ? true : false),
                selType : (this.browserParams.selType || 'SINGLE').toUpperCase()
            });

            this.browserState['offset'] = this.browserParams.offset;
            this.layoutKey = this.layoutKey || this.browserParams.layout;
            //this.showOrganizer = true;
            //if ('showOrganizer' in this.browserParams) 
            this.showOrganizer = this.browserParams.showOrganizer || false;
            this.selectState = this.browserParams.selectState || 'ACTIVATE';
            this.commandBar.applyPreferences();

            if (this.browserParams.dataset!="None")
            {
                var baseURL = (this.browserParams.dataset instanceof BQDataset)?this.browserParams.dataset.uri+'/value':this.browserParams.dataset;
                
                this.loadData(
                {
                    baseURL : baseURL,
                    offset : this.browserParams.offset,
                    tag_query : this.browserParams.tagQuery,
                    tag_order : this.browserParams.tagOrder
                });
                
                var btnOrganize = this.commandBar.getComponent("btnGear").menu.getComponent("btnOrganize");
                this.showOrganizer?btnOrganize.handler.call(this.commandBar):'';
            }
        }
    },

    applyPreferences : function()
    {
        var browserPref = this.preferences.Browser;

        // Browser preferences
        if(browserPref != undefined && !this.browserParams.viewMode)
        {
            this.browserParams.tagQuery = this.browserParams.tagQuery || browserPref["Tag Query"];
            this.layoutKey = parseInt(this.browserParams.layout || Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS[browserPref["Layout"]]);
            this.browserParams.wpublic = (browserPref["Include Public Resources"] == undefined) ? this.browserParams.wpublic : browserPref["Include Public Resources"];
        }
    },

    loadData : function(uri)
    {
        this.loading = true;
        this.on('afterlayout', function(me){
            me.centerPanel.setLoading(me.loading);
        });
        
        this.centerPanel.setLoading(
        {
            msg : ''
        });
        uri = uri || null;

        if (uri)
        {
            if(uri.tag_query == undefined)
                uri.tag_query = this.browserState.tag_query || '';
            if(uri.tag_order == undefined)
                uri.tag_order = this.browserState.tag_order || '';
            if(uri.offset == undefined)
                uri.offset = this.browserState.offset;

            if(!uri.baseURL)
                uri.baseURL = this.browserState.baseURL;

            uri.wpublic = this.browserParams.wpublic

            function checkTS(tagOrder)
            {
                if (tagOrder.indexOf('@ts')==-1)
                {
                    var ts = this.commandBar.getComponent("btnTS").sortState;
                    tagOrder += (tagOrder) ? ',' : '';
                    tagOrder += (ts=='ASC') ? '"@ts":asc' : '"@ts":desc';
                }
                
                return tagOrder;
            }
            
            uri.tag_order = checkTS.call(this, uri.tag_order);

            this.setBrowserState(uri);
        }
        else
            var uri = this.getURIFromState();

        if(uri.tag_order)
        {
            var tagValuePair = uri.tag_order.split(','), tags = [], values = [], nextPair;

            function unquote(string)
            {
                return (string.length < 2) ? string : string.substring(1, string.length - 1);
            }

            for(var i = 0; i < tagValuePair.length; i++)
            {
                nextPair = tagValuePair[i].split(':');

                if(unquote(nextPair[0]) != "@ts")
                {
                    tags.push(unquote(nextPair[0]));
                    values.push(nextPair[1].toUpperCase());
                }
            }

            uri.view = tags.join(',');
            if(tags.length >= 1)
                this.showGroups =
                {
                    tags : tags,
                    order : values
                };
            else
                this.showGroups = false;
        }
        else
            //this.showGroups is used in LayoutFactory to group resources based on tag order
            this.showGroups = false;

        function loadQueue(membersTag)
        {
            if (membersTag)
                this.uri.baseURL = membersTag.uri + '/value'; 
                this.browserState['baseURL'] = this.uri.baseURL;                
                
            for(var param in this.uri)
                if(this.uri[param].length == 0)
                    delete this.uri[param];
    
            this.resourceQueue = new Bisque.ResourceBrowser.ResourceQueue();
            this.resourceQueue.init({
                callBack : callback(this, 'dataLoaded'),
                browser : this,
                uri : this.uri
            });
        }

        this.uri = uri;
        // if baseURL is typeof BQResource (BQDataset etc.) then load its members
        if (uri.baseURL instanceof BQDataset)
            uri.baseURL.getMembers(Ext.bind(loadQueue, this));
        else
            loadQueue.call(this);
    },

    dataLoaded : function()
    {
        function doLayout()
        {
            this.ChangeLayout(this.layoutKey);

            if(!this.eventsManaged)
                this.ManageEvents();
        }

        this.fireEvent('browserLoad', this, this.resourceQueue);

        if(this.rendered)
            doLayout.call(this);
        else
            this.on('afterlayout', Ext.bind(doLayout, this),
            {
                single : true
            });
    },

    ChangeLayout : function(newLayoutKey, direction)
    {
        //console.time("Browser - ChangeLayout");
        this.loading = false;
        this.centerPanel.setLoading(this.loading);

        direction = direction || 'none';

        if(this.layoutMgr)
            this.layoutMgr.destroy();

        this.layoutKey = newLayoutKey == -1 ? this.layoutKey : newLayoutKey;

        this.layoutMgr = Bisque.ResourceBrowser.LayoutFactory.getLayout(
        {
            browser : this,
            direction : direction
        });

        this.resourceQueue.changeLayout(
        {
            key : this.layoutKey,
            layoutMgr : this.layoutMgr
        });

        this.layoutMgr.Init(this.resourceQueue.getMainQ(this.layoutMgr.getVisibleElements(direction), this.layoutMgr));
        this.centerPanel.add(this.layoutMgr);

        this.updateTbarItemStatus();

        //console.timeEnd("Browser - ChangeLayout");
    },

    /* Custom ResourceBrowser event management */
    ManageEvents : function()
    {
        this.eventsManaged = true;
        this.addEvents('Select');
        this.changeLayoutThrottled = Ext.Function.createThrottled(this.ChangeLayout, 400, this);
        this.centerPanel.on('resize', Ext.bind(this.ChangeLayout, this, [-1]));
        
        this.centerPanel.getEl().on('mousewheel', function(e)
        {
            if (this.layoutMgr.key!=Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Full)
            {
                if(e.getWheelDelta()>0)
                {
                    var btnLeft = this.commandBar.getComponent("btnLeft");
                    if(!btnLeft.disabled)
                        btnLeft.handler.call(btnLeft.scope, btnLeft);
                }
                else
                {
                    var btnRight = this.commandBar.getComponent("btnRight");
                    if(!btnRight.disabled)
                        btnRight.handler.call(btnRight.scope, btnRight);
                }
            }
        }, this);

        Ext.create('Ext.util.KeyMap',
        {
            target  :   Ext.getDoc(),
            binding :   [{
                            key                 :   "aA",
                            ctrl                :   true,
                            handler             :   function(key, e)
                                                    {
                                                        this.layoutMgr.toggleSelectAll();
                                                    },
                            defaultEventAction  :   'stopEvent',
                            scope               :   this
                        }]
        });

        this.msgBus.mon(this.msgBus,
        {
            'ResourceDblClick' : function(resource)
            {
                if(this.browserParams.selType == 'MULTI' && this.selectState == 'ACTIVATE')
                    this.fireEvent('Select', this, resource);
            },

            'ResourceSingleClick' : function(resource)
            {
                if(this.browserParams.selType == 'SINGLE' && this.selectState == 'ACTIVATE')
                    this.fireEvent('Select', this, resource);
            },

            'Browser_ReloadData' : function(uri)
            {
                //var btnOrganize = this.commandBar.getComponent("btnGear").menu.getComponent("btnOrganize");
                //this.showOrganizer?btnOrganize.handler.call(this.commandBar, true):'';

                if(uri == "")
                {
                    this.resourceQueue = new Bisque.ResourceBrowser.ResourceQueue(
                    {
                        callBack : callback(this, 'ChangeLayout', this.layoutKey),
                        browser : this,
                        uri : ""
                    });
                }
                else if(uri == 'ReloadPrefs')
                {
                    var user = BQSession.current_session.user;

                    if(user)
                    {
                        BQ.Preferences.reloadUser(user);
                        this.browserParams =
                        {
                        };
                        this.loadPreferences();
                    }
                }
                else
                    this.loadData(uri);
            },

            scope : this
        });

        // HTML5 Gestures (iPad/iPhone/Android etc.)
        if(this.gestureMgr)
            this.gestureMgr.addListener(
            {
                dom : this.centerPanel.getEl().dom,
                eventName : 'swipe',
                listener : Ext.bind(function(e, params)
                {
                    if(params.direction == "left")
                    {
                        var btnRight = this.commandBar.getComponent("btnRight");
                        if(!btnRight.disabled)
                            btnRight.handler.call(btnRight.scope, btnRight);
                    }
                    else
                    {
                        var btnLeft = this.commandBar.getComponent("btnLeft");
                        if(!btnLeft.disabled)
                            btnLeft.handler.call(btnLeft.scope, btnLeft);
                    }
                }, this),

                options :
                {
                    swipeThreshold : 100
                }
            });
    },

    setBrowserState : function(uri)
    {
        this.browserState['baseURL'] = uri.baseURL;
        this.browserState['tag_query'] = uri.tag_query;
        this.browserState['wpublic'] = this.browserParams.wpublic;
        this.browserState['layout'] = this.layoutKey;
        this.browserState['tag_order'] = uri.tag_order;
    },

    updateTbarItemStatus : function()
    {
        var btnRight = this.commandBar.getComponent("btnRight"), btnLeft = this.commandBar.getComponent("btnLeft");
        var st = this.resourceQueue.getStatus();

        this.commandBar.setStatus(st);

        btnLeft.setDisabled(st.left || st.loading.left);
        btnRight.setDisabled(st.right || st.loading.right);
        
        this.commandBar.slider.slider.setDisabled(btnLeft.disabled && btnRight.disabled);
        this.commandBar.btnTSSetState(this.browserState.tag_order.toLowerCase());
        this.commandBar.btnSearchSetState(this.browserState.tag_query);
        this.commandBar.btnActivateSetState(this.selectState);
    },

    getURIFromState : function()
    {
        var uri =
        {
            baseURL : this.browserState.baseURL,
            offset : this.browserState.offset,
            tag_query : this.browserState.tag_query || '',
            tag_order : this.browserState.tag_order || '',
            wpublic : this.browserParams.wpublic
        };

        for(var param in uri)
        if(uri[param].length == 0)
            delete uri[param];

        return uri;
    },
    
    findRecord : function(uri)
    {
        return this.resourceQueue.find(uri);
    }
});

Ext.define('Bisque.ResourceBrowser.LayoutFactory', {

    statics : {

        baseClass : 'Bisque.ResourceBrowser.Layout',

        getClass : function(layout) {
            var layoutKey = Ext.Object.getKey(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS, layout);
            var className = Bisque.ResourceBrowser.LayoutFactory.baseClass + '.' + layoutKey;
            
            return className;
        },
        
        getLayout : function(config) {
            var className = this.getClass(config.browser.layoutKey);
            
            if (Ext.ClassManager.get(className))
                return Ext.create(className, config);
            else
            {
                Ext.log({
                    msg     :   Ext.String.format('Unknown layout: {0}', className),
                    level   :   'warn',
                    stack   :   true
                });
                return Ext.create(Bisque.ResourceBrowser.Layout+'.Base', config);
            }
        }
    }
})


// Available layout enumerations
Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS = {
	"Compact"    :   1,
	"Card"       :   2,
	"PStrip"     :   3,
	"PStripBig"  :   3.1,
	"Full"       :   4,
	"List"       :   5,
	"IconList"   :   6,
	'Page'       :   7,
	'Grid'       :   8,

    // for backwards compatibility
    "COMPACT"    :   1,
    "CARD"       :   2,
};

Bisque.ResourceBrowser.LayoutFactory.DEFAULT_LAYOUT = Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact;

/**
 * BaseLayout: Abstract base layout from which all other layouts derive
 * 
 * @param {}
 *            configOpts : Layout related options such as type, size etc.
 */
Ext.define('Bisque.ResourceBrowser.Layout.Base',
{
	extend : 'Ext.panel.Panel',
	
	inheritableStatics : 
	{
	    layoutCSS : null,
        readCSS : function()
        {
            var me = {};
            
            me.layoutCSS = this.layoutCSS;
            me.layoutEl = {
                width           :   null,
                height          :   null,
                stdImageHeight  :   280,
                stdImageWidth   :   280,
            };
            
            if (me.layoutCSS)
            {
                me.css=Ext.util.CSS.getRule('.'+me.layoutCSS).style;
                
                me.layoutEl.padding=parseInt(me.css['padding']);
                me.layoutEl.margin=parseInt(me.css['margin']);
                me.layoutEl.border=parseInt(me.css['borderWidth']);
                
                me.layoutEl.width=(me.css['width'].indexOf('%')==-1)?parseInt(me.css['width']):me.css['width'];
                me.layoutEl.height=(me.css['height'].indexOf('%')==-1)?parseInt(me.css['height']):me.css['height'];
        
                me.layoutEl.outerWidth=me.layoutEl.width+(me.layoutEl.padding+me.layoutEl.border+2*me.layoutEl.margin);
                me.layoutEl.outerHeight=me.layoutEl.height+(me.layoutEl.padding+me.layoutEl.border+2*me.layoutEl.margin);
            }
            
            return me;
        }
	},
	
	constructor : function(configOpts)
	{
		Ext.apply(this, 
		{
			browser : configOpts.browser,
			direction : configOpts.direction,
			
			key : configOpts.browser.layoutKey,
			parentCt : configOpts.browser.centerPanel,
			msgBus : configOpts.browser.msgBus,
			showGroups : configOpts.browser.showGroups,
			
			resQ : [],
			layoutEl :{},
			border : false,
			autoScroll : true,
			toggleAll : false,
		});
		
		this.callParent(arguments);
		
        Ext.apply(this, Ext.ClassManager.getClass(this).readCSS());
		this.manageEvents();
	},
	
	manageEvents : function()
	{
		//this.on('afterrender', function(){this.animateIn(this.direction)}, this);

		if (this.browser.selType=='SINGLE')
			this.on(
			{
				'select' : function(resCt)
				{
					if (Ext.Object.getSize(this.browser.resourceQueue.selectedRes)!=0)
						this.browser.resourceQueue.selectedRes.toggleSelect(false);
					this.browser.resourceQueue.selectedRes=resCt;
					
					this.msgBus.fireEvent('ResSelectionChange', [resCt.resource.uri]);
				},
				'unselect' : function(resCt)
				{
					this.browser.resourceQueue.selectedRes={};
					this.msgBus.fireEvent('ResSelectionChange', []);
				},
				scope : this
			});
		else
			this.on(
			{
				'select' : function(resCt)
				{
					this.browser.resourceQueue.selectedRes[resCt.resource.uri]=resCt;
					var selRes=this.browser.resourceQueue.selectedRes;
					var keys=Ext.Object.getKeys(selRes); var selection = [];
		
					for (var i=0;i<keys.length;i++)
						selection.push(keys[i]);
					
					this.msgBus.fireEvent('ResSelectionChange', selection);
				},
				
				'unselect' : function(resCt)
				{
					delete this.browser.resourceQueue.selectedRes[resCt.resource.uri];
					var selRes=this.browser.resourceQueue.selectedRes;
					var keys=Ext.Object.getKeys(selRes); var selection = [];
		
					for (var i=0;i<keys.length;i++)
						selection.push(selRes[i]);
						
					this.msgBus.fireEvent('ResSelectionChange', selection);
				},
				
				scope : this
			});
	},
	
	toggleSelectAll : function()
	{
	    this.toggleAll = !this.toggleAll;
	    
	    if (this.browser.selType!='SINGLE')
	    {
	        for (var i=0; i<this.resQ.length; i++)
	        {
                this.resQ[i].toggleSelect(this.toggleAll);
                this.resQ[i].fireEvent('select', this.resQ[i]);
            }
	    }
	},
	
	Init : function(resourceQueue, thisCt) 
	{
		this.resQ = resourceQueue;
		if (!thisCt)
			thisCt=this;
		
		var resCt=[],resCtSub=[], i=0, currentGrp;
		
		// if no results were obtained for a given query, show a default no-results message
		if (this.resQ.length==0)
		{
            this.noResults();
            return;
		}
		
		// Avoid 'if' in for loop for speed
		if (this.showGroups)
		{
			while(i<this.resQ.length)
			{
				currentGrp=this.getGroup(this.resQ[i]);
				
				while(i<this.resQ.length && (this.getGroup(this.resQ[i])==currentGrp))
				{
					this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
					this.resQ[i].addCls(this.layoutCSS);
					resCtSub.push(this.resQ[i]);
					this.relayEvents(this.resQ[i], ['select', 'unselect']);
					
					i++;
				}
				
				resCt.push(new Ext.form.FieldSet({
					items:resCtSub,
					cls:'fieldSet',
	            	margin:'8 0 0 8',
	            	width: (this.getParentSize().width-30),
	            	//autoScroll:true,
        	    	padding:0,
            		title: '<b>Group </b><i>'+Ext.String.ellipsis(currentGrp, 80)+'</i>',
            		collapsible: true,
            		collapsed: false
				}));
				resCtSub=[];
			}
		}
		else
		{
			// Code for laying out resource containers in this layout container
			for (var i=0; i<this.resQ.length; i++)
			{
				this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
				this.resQ[i].addCls(this.layoutCSS);
				
				if (this.browser.resourceQueue.selectedRes[this.resQ[i].resource.uri])
				    this.resQ[i].cls = 'resource-view-selected';
				
				resCt.push(this.resQ[i]);
				this.relayEvents(this.resQ[i], ['select', 'unselect']);
			}
		}
		thisCt.add(resCt);
	},

    noResults : function()
    {
        this.imgNoResults = Ext.create('Ext.Img', 
        {
            width   :   300,
            margin  :   0,
            padding :   0,
            src     :   bq.url('/js/ResourceBrowser/Images/no-results.png'),
        });
        
        var ct = Ext.create('Ext.panel.Panel', 
        {
            border      :   false,
            layout      :   {
                                type : 'vbox',
                                pack : 'center',
                                align: 'center'
                            },
        });
        
        ct.addListener('afterlayout', function(me) {
            me.add(this.imgNoResults)
        }, this, {single:true});

        this.layout = 'fit';
        this.add(ct);     // "add" calls doLayout internally so 'fit' will be applied
    },
	
	getParentSize : function() 
	{
		return this.browser.centerPanel.getSize();
	},
	
	getVisibleElements : function(direction)
	{
		var ctSize = this.getParentSize();
		
		var nRow = Math.floor(ctSize.height / this.layoutEl.outerHeight);
		var nCol = Math.floor(ctSize.width / this.layoutEl.outerWidth);

		if (this.showGroups)
			return this.getNoGroupedElements(this.browser.resourceQueue.getTempQ(nRow * nCol, direction));
		else
			return nRow * nCol;
	},
	
	getNoGroupedElements : function(resData) 
	{
		var currentGrp, i=0, noGrp=1, grpObj={};
		grpObj[noGrp]=0;
		
		while(i<resData.length && !this.containerFull(grpObj))
		{
			currentGrp=this.getGroup(resData[i]);
			
			while(i<resData.length && !this.containerFull(grpObj) && (this.getGroup(resData[i])==currentGrp))
			{
				grpObj[noGrp]=grpObj[noGrp]+1;
				i++;
			}
			
			if (this.containerFull(grpObj))
			{
				i--;
				break;
			}
			
			noGrp++;
			grpObj[noGrp]=0;
		}
		
		return i;
	},
	
	getGroup : function(res)
	{
		var grp='', tagHash={}, value;
		var tagRef=res.resource.tags;
		var value;
		
		for (var i=0;i<tagRef.length;i++)
			tagHash[tagRef[i].name]=tagRef[i].value;
			
		for (var k=0;k<this.showGroups.tags.length;k++)
		{
		    value = tagHash[this.showGroups.tags[k]];
            grp+=this.showGroups.tags[k]+(value?':'+value:'')+', ';
		}
		
		return grp.substring(0, grp.length-2);
	},
	
	containerFull : function(grpObj)
	{
		var barHeight=42;
		var ctSize = this.getParentSize();

		var bodyHeight=ctSize.height-(Ext.Object.getSize(grpObj)*barHeight);
		
		var nRow = Math.floor(bodyHeight / this.layoutEl.outerHeight);
		var nCol = Math.floor(ctSize.width / this.layoutEl.outerWidth);

		var grpRow=0;
		for (var i in grpObj)
			grpRow+=Math.ceil(grpObj[i]/nCol);

		return (grpRow>nRow);
	},
});

// Compact Layout: Shows resources as thumbnails
Ext.define('Bisque.ResourceBrowser.Layout.Compact',
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',	

    inheritableStatics : {
        layoutCSS : 'ImageCompact'
    },

	constructor : function()
	{
		this.callParent(arguments);
		this.layoutEl.imageWidth=150;
		this.layoutEl.imageHeight=150;
	}
});

// Card Layout: Shows resources as cards (thumbnail + tag/value pairs)
Ext.define('Bisque.ResourceBrowser.Layout.Card',
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',

    inheritableStatics : {
        layoutCSS : 'ImageCard'
    },

	constructor : function()
	{
		this.callParent(arguments);
		this.layoutEl.imageWidth=120;
		this.layoutEl.imageHeight=120;
	}
});

// Full Layout: Shows all the tags assosiated with a resource
Ext.define('Bisque.ResourceBrowser.Layout.Full',
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',

    inheritableStatics : {
        layoutCSS : 'ImageFull'
    },

	constructor : function()
	{
		this.callParent(arguments);

		this.layoutEl.imageHeight=270;
		this.layoutEl.imageWidth=270;
	},
	
	getVisibleElements : function() 
	{
		return 10;
	}
});

// List Layout: Lists the basic information about each resource
Ext.define('Bisque.ResourceBrowser.Layout.List',
{
	extend : 'Bisque.ResourceBrowser.Layout.Full',

    inheritableStatics : {
        layoutCSS : 'ResourceList'
    },

	getVisibleElements : function() 
	{
		return 35;
	}
});

// IconList Layout: Lists the basic information about each resource along with an icon
Ext.define('Bisque.ResourceBrowser.Layout.IconList',
{
    extend : 'Bisque.ResourceBrowser.Layout.List',

    inheritableStatics : {
        layoutCSS : 'ResourceIconList'
    },
    
    constructor : function()
    {
        this.callParent(arguments);

        this.layoutEl.iconHeight=110;
        this.layoutEl.iconWidth=110;
    },
    
    getVisibleElements : function() 
    {
        return 3500;
    }
});

Ext.define('Bisque.ResourceBrowser.Layout.Page',
{
    extend : 'Bisque.ResourceBrowser.Layout.Base',  

    inheritableStatics : {
        layoutCSS : null
    },
});

// Grid layout: Shows resources in a grid
Ext.define('Bisque.ResourceBrowser.Layout.Grid', 
{
    extend : 'Bisque.ResourceBrowser.Layout.Base',
    
    inheritableStatics : {
        layoutCSS : null
    },

    constructor : function() 
    {
        Ext.apply(this, {layout:'fit'});
        this.callParent(arguments);
    },

    Init : function(resourceQueue) 
    {
        // if no results were obtained for a given query, show a default no-results message
        if (resourceQueue.length==0)
        {
            this.noResults();
            return;
        }

        this.layoutConfig = this.browser.layoutConfig || {};
        this.add(this.getResourceGrid());
        
        var resource, list=[];
        for (var i=0;i<resourceQueue.length;i++)
            list.push(resourceQueue[i].getFields())
        this.resourceStore.loadData(list);
        
        var selModel = this.resourceGrid.getSelectionModel();
        this.resQ = resourceQueue;
        
        this.resourceGrid.on('afterrender', function(me)
        {
            var resourceQueue = this.resQ, selModel = this.resourceGrid.getSelectionModel();
            for (var i=0;i<resourceQueue.length;i++)
                if (this.browser.resourceQueue.selectedRes[resourceQueue[i].resource.uri])
                    selModel.select(i, true);
        }, this, {single:true});
    },
    
    getVisibleElements : function(direction) 
    {
        var ctHeight = this.getParentSize().height-22; // height of grid header = 22px 
        var noEl = Math.floor(ctHeight/21)+1; 
        var tempQ = this.browser.resourceQueue.getTempQ(noEl, direction);
        var elHeight, currentHeight = 0;

        for (var i=0;i<tempQ.length;i++)
        {
            elHeight = tempQ[i].getFields()[6].height;
            if (currentHeight + elHeight > ctHeight)
                break;
            else
                currentHeight += elHeight;
        }
        
        return i;
    },
    
    getResourceGrid : function()
    {
        this.resourceGrid = Ext.create('Ext.grid.Panel', {
            store       :   this.getResourceStore(),
            border      :   0,
            multiSelect :   true,
            simpleSelect:   true,
            listeners : 
            {
                scope: this,
                'itemclick' : function(view, record, item, index)
                {
                    var resource = record.get('raw');
                    this.browser.msgBus.fireEvent('ResourceSingleClick', resource.resource);
                    this.fireEvent('select', resource);
                },
                'itemdblclick' : function(view, record, item, index)
                {
                    var resource = record.get('raw');
                    this.browser.msgBus.fireEvent('ResourceDblClick', resource.resource);
                }
            },
            plugins : new Ext.ux.DataTip({tpl:'<div>{name}:{value}</div>'}),
            
            columns : 
            {
                items : [
                {
                    dataIndex: 'icon',
                    menuDisabled : true,
                    sortable : false,
                    align : 'center',
                    maxWidth : this.layoutConfig.colIconWidth || 70,
                    minWidth : 1,
                },
                {
                    text: this.layoutConfig.colNameText || 'Name',
                    dataIndex: 'name',
                    align: 'left',
                    flex : 0.4 
                },
                {
                    text: this.layoutConfig.colValueText || 'Owner',
                    dataIndex: 'value',
                    flex : 0.6
                },
                {
                    text: 'Type',
                    dataIndex: 'type',
                    hidden : true,
                },
                {
                    text : this.layoutConfig.colDateText || 'Date created',
                    dataIndex: 'ts',
                    flex : 0.4 
                }],
                defaults : 
                {
                    tdCls: 'align',
                    align: 'center',
                    sortable : true,
                    flex : 0.4
                }
            }
        });
        
        return this.resourceGrid;
    },
    
    getResourceStore : function()
    {
        this.resourceStore = Ext.create('Ext.data.ArrayStore', {
            fields:  ['icon', 'name', 'value', 'type', {name: 'ts', convert: 
            function(value)
            {
                var created = new Date(), today = new Date();
                created.setISO(value);
                
                var days = Math.round((today-created)/(1000*60*60*24));
                var pattern = (days) ? "n/j/Y" : "g:i A";   

                return Ext.Date.format(created, pattern);
            }}, 'raw']});
        
        return this.resourceStore;
    }
});

// Needs to be rewritten for better generics as and when the specs become clear
Ext.define('Bisque.ResourceBrowser.Organizer',
{
    extend : 'Ext.panel.Panel',
    defaults: { border: 0, },
    constructor : function()
    {
        Ext.apply(this,
        {
            parentCt    : arguments[0].parentCt,
            dataset     : arguments[0].dataset,
            wpublic     : arguments[0].wpublic,
            msgBus      : arguments[0].msgBus,
            uri         : arguments[0].browser.uri,
            tag_order   : arguments[0].browser.uri.tag_order || '',
            tag_query   : arguments[0].browser.uri.tag_query || '',

            title       : 'Organizer',
            width       : 305,
            itemId      : 'organizerCt',
            layout      : 'accordion',
            border      : false,
            tbar        :   {
                                items : [
                                {
                                    iconCls : 'icon-add',
                                    text : 'Add',
                                    tooltip : 'Add new filter',
                                    handler : this.AddFilter,
                                    scope : this
                                },
                                {
                                    iconCls : 'icon-refresh',
                                    text : 'Reset',
                                    tooltip : 'Reset all filters',
                                    handler : this.resetFilters,
                                    scope : this
                                }]
                            },

            existingTags : new Array(),
            items : [],
            tools : [
            {
                type : 'left',
                title : 'Collapse organizer panel',
                tooltip : 'Collapse organizer panel',
                handler : function()
                {
                    this.parentCt.hideCollapseTool = false;
                    this.parentCt.collapse();
                },
                scope : this
            }]
        });

        this.callParent(arguments);
        
        this.on('afterrender', function()
        {
            this.initFilters(this.uri);
            this.ManageEvents();
        }, this, {single : true});
    },
    
    initFilters : function(uri)
    {
        this.tag_order = uri.tag_order || '';
        this.tag_query = uri.tag_query || '';
        
        this.tag_order = this.tag_order.replace(/"/g,'').split(',');
        this.tag_query = this.parseTagQuery(this.tag_query.replace(/"/g,''));

        var filterCount=0;
        
        for(var i=0;i<this.tag_order.length;i++)
        {
            if (this.tag_order[i].indexOf('@ts')!=-1)   // Ignore time-stamp from tag_order
                continue;
                
            filterCount++;
            
            var pair = this.tag_order[i].split(':');
            var filterCt = new Bisque.ResourceBrowser.Organizer.TagFilterCt({parent: this, tag_order: pair, tag_query: this.tag_query[pair[0]] || ''});
            this.add(filterCt);
    
            filterCt.addEvents('onFilterDragDrop');
            this.relayEvents(filterCt, ['onFilterDragDrop']);
            //filterCt.expand(true);
        }
        
        if (filterCount==0) // Add a blank filter if no tag_query was used to initialize the Organizer
            this.AddFilter();
    },
    
    parseTagQuery : function(tag_query)
    {
        var obj={}, arr, pair, pairs, query = tag_query.split(' AND ');
        
        
        for (var i=0;i<query.length;i++)
        {
            pairs = query[i].split(' OR ');
            arr=[];
            for (var j=0;j<pairs.length;j++)
            {
                pair = pairs[j].split(':');
                arr.push(pair[1]);
            }
            obj[pair[0]] = arr || '';
        }
        
        return obj;
    },

    AddFilter : function()
    {
        var filterCt = new Bisque.ResourceBrowser.Organizer.TagFilterCt(
        {
            parent : this
        });
        this.add(filterCt);

        filterCt.addEvents('onFilterDragDrop');
        this.relayEvents(filterCt, ['onFilterDragDrop']);
        filterCt.expand();
    },

    ManageEvents : function()
    {
        this.msgBus.on('Organizer_OnCBSelect', function(args)
        {
            this.CBSelect(args);
            this.ReloadBrowserData();
        }, this);

        this.msgBus.on('Organizer_OnGridSelect', function()
        {
            this.GridSelect();
            this.ReloadBrowserData();
        }, this);

        this.on('onFilterDragDrop', this.ReorderFilters, this);
    },

    ReorderFilters : function(opts)
    {
        var keySource = this.items.keys.indexOf(opts.source), keySink = this.items.keys.indexOf(opts.sink);
        var sourceEl = Ext.fly(opts.source);
        var sinkEl = this.getComponent(keySink).el;

        // If source item (the one being dragged) was below the sink item
        if(this.items.indexOf(keySink) < this.items.indexOf(keySource))
        {
            sourceEl.insertBefore(sinkEl);
            this.items.insert(keySource, this.items.removeAt(keySink));
        }
        else
        {
            sourceEl.insertAfter(sinkEl);
            this.items.insert(keySource + 1, this.items.removeAt(keySink));
        }
        this.ReloadBrowserData();
    },

    CBSelect : function(child)
    {
        this.PopulateGrid(false, child);

        // Add previously selected tag to other child filter containers
        this.AddNewTag(child.oldTag, child.getId());

        // Remove selected tags from other child filter containers
        this.existingTags.push(child.tag);
        this.RemoveExistingTags(child.tag, child.getId());
    },

    GridSelect : function()
    {
        // Repopulate all other grids based on new tag_query
        for(var i = 0; i < this.items.length; i++)
        {
            if(!(this.getComponent(i).value.length > 0))
                this.PopulateGrid(false, this.getComponent(i));
            else
                continue;
        }
    },

    ReloadBrowserData : function()
    {
        var uri =
        {
            offset : 0,
            tag_query : this.GetTagQuery(),
            tag_order : this.GetTagOrder()
        };
        this.msgBus.fireEvent('Browser_ReloadData', uri);
        this.msgBus.fireEvent('SearchBar_Query', this.GetTagQuery());
    },

    PopulateGrid : function(loaded, child, resourceData)
    {
        if(!loaded)
        {
            child.grid.setLoading({msg:''});
            var query = this.GetTagQuery();
            var uri = Ext.String.urlAppend(this.dataset, '{0}=' + child.tag + '&wpublic=' + this.browser.browserParams.wpublic + (query.length?'&tag_query='+query:''));
            var uri = Ext.String.format(uri, (child.tagType=='tag'?'tag_values':'gob_names'));
            
            BQFactory.load(uri, callback(this, 'PopulateGrid', true, child));
        }
        else
        {
            child.grid.setLoading(false);
            // Populate child filter's grid
            var tagArr = [];
            var data=(child.tagType=='tag'?resourceData.tags:resourceData.gobjects);
            
            for(var i = 0; i < data.length; i++)
                tagArr.push(new Ext.grid.property.Property(
                {
                    name : i + 1,
                    value : (child.tagType=='tag'?data[i].value:data[i].name)
                }));

            child.grid.store.loadData(tagArr);
            
            // Initialize the grid with tag_query if provided
            var index, selector = child.grid.getSelectionModel();
            for (var i=0;i<child.tag_query.length;i++)
            {
                index = child.grid.store.findExact('value', child.tag_query[i]);
                selector.select(child.grid.store.getAt(index), true);
                child.OnGridSelect();
            }
        }
    },

    AddNewTag : function(tag, skipCt)
    {
        if(this.existingTags.indexOf(tag) >= 0)
        {
            this.existingTags.splice(this.existingTags.indexOf(tag), 1);
            for(var i = 0; i < this.items.length; i++)
                if(this.getComponent(i).getId() != skipCt)
                {
                    this.getComponent(i).tagCombo.store.loadData([tag], true);
                    this.getComponent(i).SortComboBox('ASC');
                }
        }
    },

    RemoveExistingTags : function(tag, skipCt)
    {
        // Remove currently selected filter tag from all other combo boxes
        for(var i = 0; i < this.items.length; i++)
        {
            if(this.getComponent(i).getId() != skipCt)
            {
                var cb = this.getComponent(i).tagCombo;
                cb.store.remove(cb.findRecord(cb.displayField, tag));
            }
        }
    },

    GetTagOrder : function()
    {
        var tagOrder = "";
        for(var i = 0; i < this.items.length; i++)
        {
            if(this.getComponent(i).tag != "" && this.getComponent(i).tagType=='tag') 
                tagOrder = tagOrder + '"' + encodeURIComponent(this.getComponent(i).tag) + '":' + (this.getComponent(i).sortOrder == "" ? 'asc' : this.getComponent(i).sortOrder) + ",";
            else
                continue;
        }
        return tagOrder.substring(0, tagOrder.length - 1);
    },

    GetTagQuery : function()
    {
        var tagQuery = "";
        for(var i = 0; i < this.items.length; i++)
        {
            var pair = this.getComponent(i).GetTagValuePair()
            if(pair != "")
                tagQuery += pair + " AND ";
        }
        return tagQuery.substring(0, tagQuery.length - 5);
    },

    resetFilters : function()
    {
        while(this.items.length != 0)
            this.getComponent(0).destroy();
    }
});



/**
 * @class Bisque.ResourceBrowser.Organizer.TagFilterCt : Generates tag filters
 *        based on existing tag queries
 * @extends Ext.Panel
 */
Ext.define('Bisque.ResourceBrowser.Organizer.TagFilterCt',
{
    extend : 'Ext.panel.Panel',
    cls: 'organizer-filter',
    constructor : function()
    {
        Ext.apply(this,
        {
            layout :
            {
                type : 'vbox',
                align : 'stretch'
            },
            parent : arguments[0].parent,
            tag_order : arguments[0].tag_order || '',
            tag_query : arguments[0].tag_query || '',
            tag : "",
            oldTag : "",
            sortOrder : "",
            value : new Array(),
            tagCombo : [],
            grid : [],
            
            //bodyStyle : 'background : #D9E7F8',
            titleCollapse : true,
            collapsible : true,
            hideCollapseTool : true,
            frame : true,
            border : false,
            tools : [
            {
                type : 'up',
                tooltip : 'Sort ascending',
                handler : function()
                {
                    this.sortOrder = 'asc';
                    this.SetTitle();
                    this.ownerCt.ReloadBrowserData();
                },

                scope : this
            },
            {
                type : 'down',
                tooltip : 'Sort descending',
                handler : function()
                {
                    this.sortOrder = 'desc';
                    this.SetTitle();
                    this.ownerCt.ReloadBrowserData();
                },

                scope : this
            },
            {
                type : 'close',
                tooltip : 'Close this filter',
                handler : this.destroy,
                scope : this
            }]
        });

        this.callParent(arguments);

        this.on('afterrender', function(thisCt)
        {
            var ds = new Ext.dd.DragSource(thisCt.id,
            {
                dragData : thisCt.id
            });
            ds.setHandleElId(thisCt.header.id);
            var dt = new Ext.dd.DropTarget(thisCt.id,
            {
                filterCt : this,
                notifyDrop : function(source, e, data)
                {
                    this.filterCt.fireEvent('onFilterDragDrop',
                    {
                        source : data,
                        sink : this.id
                    });
                }
            });
        }, this);

        this.GenerateComponents();
        this.GetTagList(false);
    },

    SetTitle : function()
    {
        var tag = this.tag || '';
        tag += this.sortOrder ? ':'+this.sortOrder : '';
        tag += this.value.length!=0 ? ':'+this.value : '';
        
        this.setTitle('<span class="TagStyle">' + tag + '</span>');
    },

    SortComboBox : function(dir)
    {
        this.tagCombo.store.sort(this.tagCombo.displayField, dir);
    },

    GetTagList : function(loaded, type, tagData)
    {
        if(!loaded)
        {
            var query = this.parent.GetTagQuery();
            
            var uri = Ext.String.urlAppend(this.parent.dataset,  
                        '{0}=1&wpublic=' 
                      + this.parent.browser.browserParams.wpublic
                      + (query.length?'&tag_query='+query:'')); 
            
            BQFactory.load(Ext.String.format(uri, 'tag_names'), Ext.bind(this.GetTagList, this, [true, 'tag'], 0));
            BQFactory.load(Ext.String.format(uri, 'gob_types'), Ext.bind(this.GetTagList, this, [true, 'gobject'], 0));
        }
        else if (type=='tag')
        {
            var tagArr = [];
            for( i = 0; i < tagData.tags.length; i++)
                tagArr.push(
                {
                    "name" : (tagData.tags[i].name) ? tagData.tags[i].name.toString() : '',
                    "value": 'tag'
                });
            this.tagArr = tagArr;
            this.tagArrLoaded = true;
        }
        else if (type=='gobject')
        {
            var gobArr = [];
            for( i = 0; i < tagData.gobjects.length; i++){
                var name = tagData.gobjects[i].type || '';
                gobArr.push(
                {
                    "name" : name.toString(),
                    "value": 'gobject'
                });
            }
            this.gobArr = gobArr;
            this.gobArrLoaded = true;
        }
        if (this.tagArrLoaded && this.gobArrLoaded)
        {
            this.tagCombo.store.loadData(this.tagArr.concat(this.gobArr), false);
            this.tagCombo.setLoading(false);

            // Remove already selected tags from the just added filter
            // container
            for(var i = 0; i < this.parent.existingTags.length; i++)
                this.tagCombo.store.remove(this.tagCombo.findRecord(this.tagCombo.displayField, this.parent.existingTags[i]));

            // Initialize the filter if provided with tag_order/tag_query
            if (this.tag_order.length)
            {
                this.tagCombo.select(this.tag_order[0]);
                this.tagCombo.fireEvent('Select', this.tagCombo, true);
            }

            this.SortComboBox('ASC');
        }
    },

    GenerateComponents : function()
    {
        this.tagCombo = Ext.create('Ext.form.field.ComboBox',
        {
            editable : false,
            forceSelection : true,
            displayField : 'name',
            store : Ext.create('Ext.data.Store',
            {
                model   : 'Ext.grid.property.Property',
                sorters :   [{
                                property: 'value',
                                direction: 'DESC'
                            }, {
                                property: 'name',
                                direction: 'ASC'
                            }],           
            }),
            listConfig  :   {
                                getInnerTpl : function()
                                {
                                    return ['<tpl if="value==&quot;gobject&quot;">' +
                                                '<div>' +
                                                    '<p class="alignLeft">{name}</p>' + 
                                                    '<p class="alignRightGobject">gobject</p>' +
                                                    '<div style="clear: both;"></div>' +
                                                '</div>' +
                                            '<tpl else>' +
                                                '<div>' +
                                                    '<p class="alignLeft">{name}</p>' + 
                                                    '<p class="alignRightTag">tag</p>' +
                                                    '<div style="clear: both;"></div>' +
                                                '</div>' +
                                            '</tpl>'];
                                }
                            },
            emptyText : 'Select a tag...',
            queryMode : 'local',
            listeners :
            {
                'select' : this.OnCBSelect,
                scope : this
            }
        });

        this.grid = Ext.create('Ext.grid.Panel',
        {
            store : Ext.create('Ext.data.Store',
            {
                model : 'Ext.grid.property.Property'
            }),
            hideHeaders : true,
            multiSelect : true,
            flex : 1,
            border : 0,

            viewConfig :
            {
                emptyText : 'No data to display',
                forceFit : true,
                scrollOffset : 2
            },

            plugins : new Ext.ux.DataTip(
            {
                tpl : '<div>{value}</div>'
            }),

            listeners :
            {
                'cellclick' : this.OnGridSelect,
                scope : this
            },

            columns : [
            {
                text : 'Tag',
                dataIndex : 'name',
                hidden: true
            },
            {
                text : 'Value',
                flex : 1,
                dataIndex : 'value'
            }]
        });

        this.add([this.tagCombo, this.grid]);
        
    },

    GetSelection : function()
    {
        var selection = this.grid.getSelectionModel().getSelection();

        var dataToSend = new Array();
        for(var i = 0; i < selection.length; i++)
        dataToSend.push(selection[i].data.value);

        return dataToSend;
    },

    GetTagValuePair : function()
    {
        if  (this.tagType=='gobject')
        {
            if (this.value.length>0)
            {
                var str = "";
                for(var i = 0; i < this.value.length; i++)
                    str += '"' + encodeURIComponent(this.tag) + '"::"' + encodeURIComponent(this.value[i]) + '": OR ';
                return str.substring(0, str.length - 4);
            }
            else if (this.tag!="")
                return '"'+encodeURIComponent(this.tag)+'":::';
            else
                return "";
        }
        else
        {
            if(this.value.length > 0)
            {
                var str = "";
                for(var i = 0; i < this.value.length; i++)
                    str += '"' + encodeURIComponent(this.tag) + '":"' + encodeURIComponent(this.value[i]) + '" OR ';
                return str.substring(0, str.length - 4);
            }
            else
                return "";
        }
    },

    Reinitialize : function()
    {
        this.removeAll(true);

        this.ownerCt.AddNewTag(this.tag, this.getId());
        this.tag = "";
        this.oldTag = "";
        this.value = [];

        this.SetTitle();
        this.GenerateComponents();
        this.GetTagList(false);

        this.ownerCt.ReloadBrowserData();
    },

    destroy : function()
    {
        if(this.ownerCt)
            this.ownerCt.AddNewTag(this.tag, this.getId());
        this.removeAll(true);

        this.tag = "";
        this.oldTag = "";
        this.value = [];

        if(this.ownerCt)
            this.ownerCt.ReloadBrowserData();

        this.callParent(arguments);
    },

    /* Event handlers */
    OnCBSelect : function(combo, silent)
    {
        if(this.tag != combo.getRawValue())
        {
            this.oldTag = this.tag;
            this.tag = combo.getRawValue();
            this.tagType = combo.lastSelection[0].data.value;
            this.value = [];
            this.SetTitle();

            if (silent)
                this.parent.msgBus.fireEvent('Organizer_OnCBSelect', this);
        }
    },

    OnGridSelect : function()
    {
        this.value = this.GetSelection();
        this.SetTitle();
        this.parent.msgBus.fireEvent('Organizer_OnGridSelect');
    }
});

Bisque.ResourceBrowser.ResourceQueue = function() {};
Bisque.ResourceBrowser.ResourceQueue.prototype = new Array;

Ext.apply(Bisque.ResourceBrowser.ResourceQueue.prototype, 
{
	init : function(config)
	{
		Ext.apply(this,
		{
			browser          :   config.browser,
			layoutKey        :   config.browser.layoutKey,
			msgBus           :   config.browser.msgBus,
			uri              :   config.uri,
			callBack         :   config.callBack,
			
			prefetchFactor   :   1,	// (prefetchFactor X visibileElements) elements are prefetched 
			dataLimit        :   350,	// Number of resource URIs fetched
			noUnloadClicks   :   5, // Cache of the opposite direction will be unloaded after these many clicks in a given direction (right or left) 
			
			hasMoreData      :   {left:true, right:true},
			loading          :   {left:false, right:false},
			dataHash         :   {},
			list             :   [],
			selectedRes      :   {},
			indRight         :   [],     //Indexes of prefetched items on the right - prefetch cache
			indLeft          :   [],     //Indexes of prefetched items on the left - prefetch cache
			dbOffset         :   {left:0, center:parseInt(config.uri.offset), right:0},
			currentDirection :   1, // 1=Right, 0=Left
			
			clicks           :   {right:0, left:0},
			rqOffset         :   0
		});
		
		this.loadData();
	},

	loadData : function()
	{
		this.dbOffset.left=((this.dbOffset.center-this.dataLimit)>=0)?this.dbOffset.center-this.dataLimit:0;

		var uri = this.uri;
		uri.offset = this.dbOffset.left;
		uri.limit = 2*this.dataLimit;

		BQFactory.request({
			uri:this.generateURI(uri),
			cb:callback(this, 'dataLoaded'),
			cache: false
		});
	},
	
	dataLoaded : function(resourceData)
	{
		this.rqOffset=this.dbOffset.center-this.dbOffset.left;
		this.dbOffset.right=this.dbOffset.left+resourceData.children.length;
		
		for(var i=0;i<resourceData.children.length;i++)
			this.push(Bisque.ResourceFactory.getResource(
			    {
                    resource    :   resourceData.children[i],
    			    layoutKey   :   this.layoutKey,
    			    msgBus      :   this.msgBus, 
    			    resQ        :   this, 
    			    browser     :   this.browser
                }));

		this.hasMoreData.left=(this.dbOffset.left>0)?true:false;
        this.hasMoreData.right = ((this.dbOffset.right - this.dbOffset.center) >= this.dataLimit) ? true : false;
		
		this.callBack();
	},
	
	loadDataRight : function(loaded, data)
	{
		if (!loaded)
		{
			this.loading.right=true;
			var uri=this.browser.getURIFromState();
			uri.offset=this.dbOffset.right;
			uri.limit=this.dataLimit;
			
			BQFactory.request({
				uri:this.generateURI(uri),
				cb:callback(this, 'loadDataRight', true),
				cache: false
			});
			
			this.browser.commandBar.getComponent('btnRight').setDisabled(true);
			this.browser.commandBar.getComponent('btnRight').setLoading({msg:''});
		}
		else
		{
			this.browser.commandBar.getComponent('btnRight').setDisabled(false);
			this.browser.commandBar.getComponent('btnRight').setLoading(false);

			this.dbOffset.right+=data.children.length;
			for(var i=0;i<data.children.length;i++)
				this.push(Bisque.ResourceFactory.getResource({resource:data.children[i], layoutKey:this.layoutKey, msgBus:this.msgBus, resQ:this, browser:this.browser}));
			
			this.hasMoreData.right=(data.children.length==this.dataLimit)?true:false;
			this.loading.right=false;
            this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
		}
	},

	loadDataLeft : function(loaded, data)
	{
		if (!loaded)
		{
			this.loading.left=true;
			var oldLeft=this.dbOffset.left;
			this.dbOffset.left=((this.dbOffset.left-this.dataLimit)>=0)?this.dbOffset.left-this.dataLimit:0;
			
			var uri=this.browser.getURIFromState();
			uri.offset=this.dbOffset.left;
			uri.limit=oldLeft-this.dbOffset.left;
			
			BQFactory.request({
				uri:this.generateURI(uri),
				cb:callback(this, 'loadDataLeft', true),
				cache: false
			});
			
			this.browser.commandBar.getComponent('btnLeft').setDisabled(true);
			this.browser.commandBar.getComponent('btnLeft').setLoading({msg:''});
		}
		else
		{
			this.browser.commandBar.getComponent('btnLeft').setDisabled(false);
			this.browser.commandBar.getComponent('btnLeft').setLoading(false);

			for(var i=0;i<data.children.length;i++)
				this.unshift(Bisque.ResourceFactory.getResource({resource:data.children[i], layoutKey:this.layoutKey, msgBus:this.msgBus, resQ:this, browser:this.browser}));
			
			this.hasMoreData.left=(data.children.length==this.dataLimit)?true:false;
			this.loading.left=false;
            this.rqOffset = this.rqOffset + data.children.length;
            
            this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
		}
	},

	loadPrev : function(visLimit)
	{
		this.currentDirection=0;
		
		if (this.rqOffset-visLimit>0)
			this.rqOffset-=visLimit;
		else
			this.rqOffset=0;

		this.clicks.left+=1;
		this.unloadRight();
	},

	loadNext : function(visLimit)
	{
		var noEl=visLimit || this.visLimit;
		this.currentDirection=1;
		
		if (this.rqOffset+noEl<this.length)
			this.rqOffset+=noEl;

		this.clicks.right+=1;
		this.unloadLeft();
	},
	
	prefetchPrev : function(layoutMgr)
	{
		//var prefetchFactor=(this.currentDirection==0)?this.prefetchFactor+1:this.prefetchFactor;
		var prefetchFactor = this.prefetchFactor;
		
		if (this.rqOffset-prefetchFactor*this.visLimit>0)
			for (i=this.rqOffset-prefetchFactor*this.visLimit;i<this.rqOffset;i++)
			{
				this[i].prefetch(layoutMgr);
				this.indLeft.push(this[i].resource.uri);
			}
		else
		{
			for (i=0;i<this.rqOffset;i++)
			{
				this[i].prefetch(layoutMgr);
				this.indLeft.push(this[i].resource.uri);
			}
			
			if (this.hasMoreData.left && !this.loading.left)
				this.loadDataLeft(false);
		}
	},
	
	prefetchNext : function(layoutMgr)
	{
		//var prefetchFactor=(this.currentDirection==1)?this.prefetchFactor+1:this.prefetchFactor;
		var prefetchFactor = this.prefetchFactor;

		if (this.rqOffset+(prefetchFactor+1)*this.visLimit<this.length)
			for (i=this.rqOffset;i<=this.rqOffset+(prefetchFactor+1)*this.visLimit;i++)
			{
				this[i].prefetch(layoutMgr);
				this.indRight.push(this[i].resource.uri);
			}
		else
		{
			for (i=this.rqOffset;i<this.length;i++)
			{
				this[i].prefetch(layoutMgr);
				this.indRight.push(this[i].resource.uri);
			}
			
			if (this.hasMoreData.right && !this.loading.right)
				this.loadDataRight(false);
		}
	},

	unloadRight : function()
	{
		if (this.clicks.left==this.noUnloadClicks)
		{
			//console.time("unloadRight");
			this.clicks.left=0;	
			var len=Math.floor(this.indRight.length/2)
			for (var i=0;i<len;i++)
				this.dataHash[this.indRight.shift()]={};
		
			//console.timeEnd("unloadRight");
		}
	},

    unloadLeft : function()
    {
        if (this.clicks.right==this.noUnloadClicks)
        {
            //console.time("unloadLeft");
            this.clicks.right=0;
            var len=Math.floor(this.indLeft.length/2);  
            for (var i=0;i<len;i++)
                this.dataHash[this.indLeft.shift()]={};
            
            //console.timeEnd("unloadLeft");
        }
    },

	prefetch : function(layoutMgr)
	{
		//console.time("prefetch");
		
		this.list=this.slice(this.rqOffset, this.rqOffset+this.visLimit);
		
		for(var i=0;i<this.list.length;i++)
		{
			this.splice(i+this.rqOffset, 1, Bisque.ResourceFactory.getResource({resource:this[i+this.rqOffset].resource, layoutKey:this.layoutKey, msgBus:this.msgBus, resQ:this, browser:this.browser}));
			this.list[i].prefetch(layoutMgr);
		}

		if (this.currentDirection)
			window.setTimeout(Ext.bind(this.prefetchNext, this, [layoutMgr]), 400);
		else
			window.setTimeout(Ext.bind(this.prefetchPrev, this, [layoutMgr]), 400);

		//console.timeEnd("prefetch");
		return this.list;
	},
	
	getMainQ : function(visLimit, layoutMgr)
	{
		this.visLimit=visLimit;
		// Browser state change - reflect offset change
		this.browser.browserState['offset']=this.rqOffset+this.dbOffset.left;
		return this.prefetch(layoutMgr);
	},
	
	getTempQ : function(visLimit, direction)
	{
	    var leftOffset=this.rqOffset, tmp;
	    
	    if (direction=='left')
	    {
	       leftOffset=((leftOffset-visLimit)>0)?(leftOffset-visLimit):0;
	       return this.slice(leftOffset, this.rqOffset).reverse();
	    }
	    else
    	    return this.slice(leftOffset, leftOffset+visLimit);
	},

	changeLayout : function(layoutObj)
	{
		//console.time("resourceQueue - changeLayout");
		
		if (this.layoutKey!=layoutObj.key)
		{
			this.layoutKey=layoutObj.key;
			this.dataHash={};
		
			for(i=0;i<this.length;i++)
				this.splice(i, 1, Bisque.ResourceFactory.getResource({resource:this[i].resource, layoutKey:this.layoutKey, msgBus:this.msgBus, resQ:this, browser:this.browser}))
		}

		//console.timeEnd("resourceQueue - changeLayout");
	},
	
	/* Utility functions */
	getStatus : function()
	{
        var left=false, right=false, visLimit=this.visLimit;
		
		if (this.rqOffset==0 && this.dbOffset.left==0)
			left=true;
		if ((this.rqOffset+visLimit>=this.length) && !this.hasMoreData.right)
		{
			right=true;
			visLimit=this.length-this.rqOffset;
		}
		
		var st=Ext.String.format('Showing {0}-{1} of {2} {3}', this.dbOffset.left+this.rqOffset+(this.list.length?1:0), this.dbOffset.left+this.rqOffset+this.list.length, ((this.hasMoreData.left || this.hasMoreData.right)?'atleast ':'total '), this.dbOffset.left+this.length);
		
		var sliderSt=
		{
			left: this.hasMoreData.left,
			right: this.hasMoreData.right,
			min: this.dbOffset.left+1, max:this.dbOffset.left+this.length, value:this.dbOffset.left+this.rqOffset+1
		};

		return {status:st, left:left, right:right, sliderSt:sliderSt, loading: this.loading};
	},
	
	generateURI : function(uriObj)
	{
		var uri='', baseURL=uriObj.baseURL;
		delete uriObj.baseURL;

		function unquote(string)
		{
			return (string.length<2)?string:string.substring(1, string.length-1);
		}
		
		if (uriObj.tag_order)
		{
			var tagValuePair=uriObj.tag_order.split(','), tags=[], values=[], nextPair;
			
			for (var i=0;i<tagValuePair.length;i++)
			{
				nextPair=tagValuePair[i].split(':');
				
				if (unquote(nextPair[0])!="@ts")
					tags.push(unquote(nextPair[0]));
			}
			
			uriObj.view=tags.join(',');
		}

		for (var param in uriObj)
            if(uriObj[param].length == 0)
                delete uriObj[param];
            else
                uri+='&'+param+'='+uriObj[param];
                
        uri = (uri==''?uri:uri.substring(1,uri.length));
        return Ext.urlAppend(baseURL, uri);
	},
	
	uriStateToString : function(uriObj)
	{
		var uri='', baseURL=uriObj.baseURL;
		delete uriObj.baseURL;
		
		for (var param in uriObj)
			uri+='&'+param+'='+uriObj[param];

		var path=window.location.href.substr(0,window.location.href.lastIndexOf(window.location.search));

		if (path[path.length-1]!='?')
			path=path+'?';

		return path+'dataset='+baseURL+uri+'&layout='+this.layoutKey; 
	},
	
	// Stores resource-specific data in a hash table (key on uri)
	storeMyData : function(uri, tag, value)
	{
		if (!Ext.isDefined(this.dataHash[uri]))
			this.dataHash[uri]={};
		
		this.dataHash[uri][tag]=value;
	},
	
	// Retrieves resource-specific data (key on uri)
	getMyData : function(uri, tag)
	{
		if (Ext.isDefined(this.dataHash[uri]))
			if (Ext.isDefined(this.dataHash[uri][tag]))
				return this.dataHash[uri][tag];
		return 0;
	},
	
	find : function(uri)
	{
	    var currentResource = false;
	    for (var i=0; i<this.length; i++)
	    {
	        if (this[i].resource.uri == uri)
	        {
	            currentResource = this[i].resource;
	            break;
	        }
	    }
	    return currentResource;
	}
});

Ext.define('Bisque.ResourceBrowser.DatasetManager',
{
    extend      :   'Ext.grid.Panel',

    constructor : function(config)
    {
        Ext.apply(this, 
        {
            title       :   'Datasets',
            width       :   350,
            padding     :   5,
            autoScroll  :   true,
            store       :   Ext.create('Ext.data.ArrayStore', {fields: ['Raw', 'Name', 'Date']}),
            columns     :   {
                                items : [{
                                    width       :   8,
                                }, {
                                    dataIndex   :   'Name',
                                    text        :   'Dataset',
                                    flex        :   0.5
                                }, {
                                    dataIndex   :   'Date',
                                    text        :   'Date',
                                    align       :   'center',
                                    flex        :   0.5
                                }]
                            },
            listeners   :   {
                                'select' : function(me, record, index, a, b, c)
                                {
                                    var dataset = record.get('Raw');
        
                                    this.msgBus.fireEvent('Browser_ReloadData', {offset : 0, baseURL : dataset.uri+'/value'});
                                    this.msgBus.fireEvent('DatasetSelected', dataset);
                                },
                            },
        });
        
        this.callParent(arguments);
        this.loadDatasets(false);
    },
    
    loadDatasets : function(loaded, datasetList)
    {
        if (!loaded)
            BQFactory.load('/data_service/dataset?view=short&tag_order=@ts:desc', callback(this, 'loadDatasets', true));
        else
        {
            var list = [], date = new Date(), i;

            for (i = 0; i < datasetList.children.length; i++)
            {
                date.setISO(datasetList.children[i].ts);
                list.push([datasetList.children[i], datasetList.children[i].name, Ext.Date.format(date, "m-d-Y")]);
            }
            
            this.store.loadData(list);
        }
    },
});

Ext.define('Bisque.ResourceBrowser.CommandBar',
{
	extend : 'Ext.toolbar.Toolbar',

	constructor : function(configOpts)
	{
		this.viewMgr = configOpts.browser.viewMgr;
        this.slider = new Bisque.Misc.Slider({hidden:this.viewMgr.cBar.slider});

		Ext.apply(this,
		{
			browser : configOpts.browser,
			taqQuery : configOpts.browser.browserParams.tagQuery,
			
			msgBus : configOpts.browser.msgBus,
			westPanel : configOpts.browser.westPanel,
			organizerCt : configOpts.browser.organizerCt,
			datasetCt : configOpts.browser.datasetCt,
			hidden : configOpts.browser.viewMgr.cBar.cbar,
			
			layout :
			{
				type:'hbox',
				align:'middle'
			},
			items :
			[
				{
					xtype : 'tbspacer',
					width : 6
				},
				{
					xtype : 'textfield',
					tooltip : 'Enter a tag query here',
					itemId : 'searchBar',
					flex:7,
					scale:'large',
					height:25,
					boxMinWidth : 100,
					hidden : this.viewMgr.cBar.searchBar,
					value : configOpts.tagQuery,
					listeners :
					{
						specialkey :
						{
							fn : function(field, e)
							{
								if (e.getKey() == e.ENTER)
									this.btnSearch()
							},
	
							scope : this
						},
				        scope : this,
                        focus: function(c) { 
                            var tip = Ext.create('Ext.tip.ToolTip', {
                                target: c.el,
                                anchor: 'top',
                                minWidth: 500, 
                                width: 500,                           
                                autoHide: true,
                                dismissDelay: 20000,
                                shadow: true,
                                autoScroll: true,
                                loader: { url: '/html/querying.html', renderer: 'html', autoLoad: true },
                            }); 
                            tip.show();                           
                        },
					}
				},
				{
					icon : bq.url('/js/ResourceBrowser/Images/search.png'),
					hidden : this.viewMgr.cBar.searchBar,
					tooltip : 'Search',
					scale : 'large',
					handler : this.btnSearch,
					scope : this
				},
				{
					xtype : 'tbseparator',
					hidden : this.viewMgr.cBar.searchBar
				},
				{
					itemId : 'btnThumb',
					icon : bq.url('/js/ResourceBrowser/Images/thumb.png'),
					hidden : this.viewMgr.cBar.btnLayoutThumb,
					tooltip : 'Thumbnail layout',
					toggleGroup : 'btnLayout',
					scale : 'large',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},
                {
                    itemId : 'btnGrid',
                    icon : bq.url('/js/ResourceBrowser/Images/grid.png'),
                    hidden : this.viewMgr.cBar.btnLayoutGrid,
                    tooltip : 'Grid layout',
                    scale : 'large',
                    toggleGroup : 'btnLayout',
                    handler : this.btnLayoutClick,
                    padding : '3 0 3 0',
                    scope : this
                },
				{
					itemId : 'btnCard',
					icon : bq.url('/js/ResourceBrowser/Images/card.png'),
					hidden : this.viewMgr.cBar.btnLayoutCard,
					tooltip : 'Card layout',
					scale : 'large',
					toggleGroup : 'btnLayout',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},
				{
					itemId : 'btnFull',
					icon : bq.url('/js/ResourceBrowser/Images/full.png'),
					hidden : this.viewMgr.cBar.btnLayoutFull,
					tooltip : 'Full layout',
					scale : 'large',
					toggleGroup : 'btnLayout',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},'->',
                {
                    itemId : 'btnActivate',
                    icon : bq.url('/js/ResourceBrowser/Images/activate.png'),
                    tooltip : '(ACTIVATE) Press button to switch to selection mode',
                    state : 'ACTIVATE',
                    hidden : this.viewMgr.cBar.btnActivate,
                    scale : 'large',
                    handler : this.btnActivate,
                    scope : this
                },
                {
                    itemId : 'btnRefresh',
                    icon : bq.url('/js/ResourceBrowser/Images/refresh.png'),
                    tooltip : 'Refresh browser',
                    hidden : this.viewMgr.cBar.btnRefresh,
                    scale : 'large',
                    handler : this.btnRefresh,
                    scope : this
                },
				{
					itemId : 'btnTS',
					icon : bq.url('/js/ResourceBrowser/Images/desc.png'),
					tooltip : 'Sort data ascending by timestamp (current: descending)',
					hidden : this.viewMgr.cBar.btnTS,
					sortState : 'DESC',
					scale : 'large',
					handler : this.btnTS,
					scope : this
				},
                {
                    xtype : 'tbseparator',
                    hidden : this.viewMgr.cBar.btnTS
                },
				{
					tooltip : 'Load more data',
					itemId : 'btnLeft',
					icon : bq.url('/js/ResourceBrowser/Images/left.png'),
					hidden : this.viewMgr.cBar.btnLeft,
					scale : 'large',
					padding : '0 1 0 0',
					handler : function(me)
					{
						//me.stopAnimation();
						//me.el.frame("#B0CEF7");
						this.browser.resourceQueue.loadPrev(this.browser.layoutMgr.getVisibleElements('left'/*direction:left*/));
						this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
					},
					scope : this
				},
				{
					tooltip : 'Load more data',
					itemId :  'btnRight',
					icon : bq.url('/js/ResourceBrowser/Images/right.png'),
					hidden : this.viewMgr.cBar.btnRight,
					scale : 'large',
					padding : '0 0 0 1',
					handler : function(me)
					{
						//me.stopAnimation();
						//me.el.frame("#B0CEF7");
						this.browser.resourceQueue.loadNext();
						this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
					},
	
					scope : this
				},
					
				this.slider,
				
				{
					xtype : 'tbseparator',
					hidden : this.viewMgr.cBar.btnGear
				},
				{
					icon : bq.url('/js/ResourceBrowser/Images/gear.png'),
					hidden : this.viewMgr.cBar.btnGear,
					itemId : 'btnGear',
					scale : 'large',
					tooltip : 'Options',
					menu :
					{
						items : 
						[{
							text : 'Include public resources',
							itemId : 'btnWpublic',
							checked : false,
					 		listeners:
					 		{
							 	checkchange:
						 		{
						 			fn : function(chkbox, value)
				 					{
				 						var uri={offset:0};
						 				configOpts.browser.browserParams.wpublic = value;
						 				configOpts.browser.msgBus.fireEvent('Browser_ReloadData', uri);
						 			},
						 			scope : this
					 			}
					 		}
				 		},'-',
						{
							text : 'Organize',
                            itemId : 'btnOrganize',
							icon : bq.url('/js/ResourceBrowser/Images/organize.png'),
							hidden : true,
				 			handler : this.btnOrganizerClick,
				 			scope : this
				 		},
				 		{
				 			text : 'Datasets',
				 			icon : bq.url('/js/ResourceBrowser/Images/datasets.png'),
							hidden : true,  //this.viewMgr.cBar.btnDataset,
				 			handler : this.btnDatasetClick,
				 			scope : this
				 		},
						{
							text : 'Link',
							icon : bq.url('/js/ResourceBrowser/Images/link.png'),
							hidden : this.viewMgr.cBar.btnLink,
							handler : function()
							{
				 				var val = configOpts.browser.resourceQueue.uriStateToString(configOpts.browser.getURIFromState());
				 				
				 				Ext.Msg.show
				 				({
				 					title : 'Link to this view',
				 					msg : 'Bisque URL:',
				 					modal : true,
				 					prompt : true,
				 					width : 500,
				 					buttons : Ext.MessageBox.OK,
				 					icon : Ext.MessageBox.INFO,
				 					value : val
				 				});
				 			}
				 		}]
					}
				},
				{
					xtype : 'tbspacer',
					flex : 0.2,
					maxWidth : 20
				}
			]
		});

		Bisque.ResourceBrowser.CommandBar.superclass.constructor.apply(this, arguments);
		
		this.manageEvents();
	},
	
	manageEvents : function()
	{
		this.msgBus.on('SearchBar_Query', function(query)
		{
			this.getComponent('searchBar').setValue(decodeURIComponent(query));
		}, this);
		
		this.mon(this, 'afterlayout', this.toggleLayoutBtn, this);
		
        this.slider.on('buttonClick', Ext.Function.createThrottled(function(newOffset)
        {
            var oldOffset = this.browser.resourceQueue.rqOffset + this.browser.resourceQueue.dbOffset.left;
            var diff = newOffset - oldOffset;

            if(diff > 0)
            {
                this.browser.resourceQueue.loadNext(diff);
                this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
            }
            else if(diff < 0)
            {
                this.browser.resourceQueue.loadPrev(-1 * diff);
                this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
            }
        }, 400, this), this);

	},

    btnRefresh : function()
    {
        this.browser.msgBus.fireEvent('Browser_ReloadData', {});
    },
    
    btnActivate : function(btn)
    {
        if (btn.state == 'ACTIVATE')
        {
            btn.setIcon(bq.url('/js/ResourceBrowser/Images/select.png'));
            btn.state='SELECT';
            btn.setTooltip('(SELECT) Press button to switch to activation mode');
        }
        else
        {
            btn.setIcon(bq.url('/js/ResourceBrowser/Images/activate.png'));
            btn.state='ACTIVATE';
            btn.setTooltip('(ACTIVATE) Press button to switch to selection mode');
        }
        this.browser.selectState = btn.state;
        this.browser.fireEvent('SelectMode_Change', btn.state);
    },
    
	btnTS : function(btn)
	{
        var tagOrder = cleanTagOrder(this.browser.browserState.tag_order) || '';
        
		function cleanTagOrder(tagOrder)
		{
			var ind=tagOrder.lastIndexOf('"@ts":desc')
			if (ind!=-1)
				return tagOrder.slice(0, ind);

			ind=tagOrder.lastIndexOf('"@ts":asc')
			if (ind!=-1)
				return tagOrder.slice(0, ind);
			
			return tagOrder;
		}
		
		(tagOrder.length!=0)?((tagOrder[tagOrder.length-1]!=',')?tagOrder+=',':""):"";
		
		if (btn.sortState=='ASC')
		{
			btn.setIcon(bq.url('/js/ResourceBrowser/Images/desc.png'));
			btn.sortState='DESC';
			btn.setTooltip('Sort data ascending by timestamp (current: descending)');
			tagOrder+='"@ts":desc';
		}
		else
		{
			btn.setIcon(bq.url('/js/ResourceBrowser/Images/asc.png'));
			btn.sortState='ASC';
			btn.setTooltip('Sort data descending by timestamp (current: ascending)');
			tagOrder+='"@ts":asc';
		}
		
        this.msgBus.fireEvent('Browser_ReloadData',
        {
            offset:0,
            tag_order:tagOrder
        });
	},

	btnSearch : function()
	{
		var uri =
		{
			offset : 0,
			tag_query : this.getComponent('searchBar').getValue()
		};
		this.msgBus.fireEvent('Browser_ReloadData', uri);
	},

	btnDatasetClick : function()
	{
		this.westPanel.removeAll(false);
		
        this.datasetCt = this.datasetCt || new Bisque.ResourceBrowser.DatasetManager(
        {
            parentCt : this.westPanel,
            browser : this.browser,
            msgBus : this.msgBus
        });
        
        this.westPanel.setWidth(this.datasetCt.width).show().expand();
        this.westPanel.add(this.datasetCt);
        this.westPanel.doComponentLayout(null, null, true);
	},

	btnOrganizerClick : function(reload)
	{
        this.westPanel.removeAll(false);
        
        this.organizerCt = (reload?undefined:this.organizerCt) || new Bisque.ResourceBrowser.Organizer(
        {
            parentCt : this.westPanel,
            dataset : this.browser.browserState['baseURL'],
            wpublic : this.browser.browserParams.wpublic,
            browser : this.browser,
            msgBus : this.msgBus
        });
        
        this.westPanel.setWidth(this.organizerCt.width).show().expand();
        this.westPanel.add(this.organizerCt);
        this.westPanel.doComponentLayout(null, null, true);
	},

	btnLayoutClick : function(item)
	{
		switch (item.itemId)
		{
			case 'btnThumb' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact);
				break;
			case 'btnCard' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Card);
				break;
            case 'btnGrid' :
                this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Grid);
				break;
			case 'btnFull' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Full);
				break;
		}
	},
	
	toggleLayoutBtn : function()
	{
		switch(this.browser.layoutKey)
		{
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact :
				this.getComponent('btnThumb').toggle(true, false);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Card :
				this.getComponent('btnCard').toggle(true, false);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Grid :
				this.getComponent('btnGrid').toggle(true, false);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Full :
				this.getComponent('btnFull').toggle(true, false);
				break;
		}
	},
	
    btnActivateSetState : function(state)
    {
        var btn=this.getComponent('btnActivate');
        btn.state = (state=='ACTIVATE')?'SELECT':'ACTIVATE';
        this.btnActivate(btn);
    },

	btnTSSetState : function(tagOrder)
	{
        var sortState=(tagOrder.indexOf('"@ts":desc')!=-1)?'DESC':((tagOrder.indexOf('"@ts":asc')!=-1)?'ASC':'');
        var btn=this.getComponent('btnTS');

        if (btn.sortState!=sortState)
            if (sortState=='DESC')
            {
                btn.setIcon(bq.url('/js/ResourceBrowser/Images/desc.png'));
                btn.sortState='DESC';
                btn.setTooltip('Sort data ascending by timestamp (current: descending)');
            }
            else
            {
                btn.setIcon(bq.url('/js/ResourceBrowser/Images/asc.png'));
                btn.sortState='ASC';
                btn.setTooltip('Sort data descending by timestamp (current: ascending)');
            }
	},
	
	btnSearchSetState : function(tagQuery)
	{
	    this.getComponent('searchBar').setValue(decodeURIComponent(tagQuery));
	},
	
	setStatus : function(status)
	{
		if (this.slider.rendered)
			this.slider.setStatus(status);	
	},
	
	applyPreferences : function()
	{
	    if (this.rendered)
            this.toggleLayoutBtn();
        this.getComponent('btnGear').menu.getComponent('btnWpublic').setChecked(this.browser.browserParams.wpublic, true);
	}
})
Ext.define('Bisque.ResourceBrowser.viewStateManager',
{
	//	ResourceBrowser view-state 
	constructor : function(mode)
	{
        this.cBar = 
        {
            cbar : false,
            
            searchBar : false,
            
            btnActivate : false,
            btnTS : false,
            btnRefresh : false,
            
            btnLayoutThumb : false,
            btnLayoutCard : false,
            btnLayoutGrid : false,
            btnLayoutFull : false,
    
            btnLayoutLeft : false,
            btnLayoutRight : false,
            
            slider : false,
            
            btnGear : false,
            btnOrganizer : false,
            btnDataset : false,
            btnLink : false,
            btnPreferences : false
        };
	    
		switch(mode)
		{
			case 'MexBrowser':
			case 'ViewerOnly':
			case 'DatasetBrowser':
			{
				this.cBar.searchBar=true;
				
				this.cBar.btnLayoutThumb=true;
				this.cBar.btnLayoutCard=true;
				this.cBar.btnLayoutGrid=true;
				this.cBar.btnLayoutFull=true;
				
				this.cBar.btnGear=true;
				break;
			}
            case 'ViewSearch':
            {
                this.cBar.btnActivate = true;
                this.cBar.btnTS = true;
                this.cBar.btnRefresh = true;

                this.cBar.btnLayoutThumb=true;
                this.cBar.btnLayoutCard=true;
                this.cBar.btnLayoutGrid=true;
                this.cBar.btnLayoutFull=true;
                
                this.cBar.slider = true;
                this.cBar.btnGear = true;
                
                break;
            }
			case 'ViewerLayouts':
			{
                this.cBar.searchBar=true;
                this.cBar.btnGear=true;
			    break;
			}
			case 'ModuleBrowser':
			{
                this.cBar.cbar=true;
                break;
			}
		}
		
		return this;
	}
})

Ext.define('Bisque.ResourceBrowser.OperationBar',
{
    extend      :   'Ext.container.Container',
    floating    :   true,
    
    constructor : function()
    {
        var close = Ext.create('Ext.button.Button', {
            icon    :   bq.url('/js/ResourceBrowser/Images/close.gif'),
            tooltip :   'Delete this resource.',
            handler :   this.close,
            scope   :   this
        });

        var down = Ext.create('Ext.button.Button', {
            icon    :   bq.url('/js/ResourceBrowser/Images/down.png'),
            tooltip :   'Available operations for this resource.',
            handler :   this.menuHandler,
            scope   :   this
        });
        
        this.items = [down, close];
        
        this.callParent(arguments);
    },
    
    close : function(me, e)
    {
        e.stopPropagation();
        var list = Ext.Object.getSize(this.browser.resourceQueue.selectedRes);
        
        if (list>1)
        {
            // Client-side temporary dataset
            var tempDS = new BQDataset(), members = [];
            
            for (var res in this.browser.resourceQueue.selectedRes)
            {
                this.browser.resourceQueue.selectedRes[res].setLoading({msg:'Deleting...'});
                members.push(this.browser.resourceQueue.selectedRes[res]);
            }
            
            tempDS.tmp_setMembers(members);
            
            tempDS.tmp_deleteMembers(Ext.bind(result, this));

            function result(summary)
            {
                BQ.ui.notification(summary.success + ' resources deleted. ' + summary.failure + ' resources failed.');
                this.browser.msgBus.fireEvent('Browser_ReloadData', {});
            }
        }
        else
        {
            me.operation = Ext.pass(this.resourceCt.resource.delete_, [Ext.bind(this.success, this), Ext.Function.pass(this.failure, ['Delete operation failed!'])], this.resourceCt.resource);
            this.resourceCt.setLoading({msg:'Deleting...'});
            this.resourceCt.testAuth1(me);
        }
    },
    
    menuHandler : function(me, e)
    {
        e.stopPropagation();
        this.menu = this.createMenu().showBy(this, "tr-br");
    },
    
    createMenu : function()
    {
        // Look for available resource operations and change menu accordingly
        var list = Ext.Object.getSize(this.browser.resourceQueue.selectedRes);
        
        var items = [
        {
            text    :   'Download',
            iconCls :   'icon-download-small',
            handler :   this.btnMenu,
            scope   :   this
        },
        {
            text    :   'Share',
            iconCls :   'icon-group',
            handler :   this.btnMenu,
            scope   :   this
        }];
        
        
        // Handle resource permission
        if (list>1)
        {
            items.push({
                text    :   'Set all published',
                iconCls :   'icon-eye',
                handler :   this.btnMenu,
                scope   :   this
            }, {
                text    :   'Set all private',
                iconCls :   'icon-eye-close',
                handler :   this.btnMenu,
                scope   :   this
            });
        }
        else
            if (this.resourceCt.resource.permission=='published')
                items.push({
                    text    :   'Published',
                    iconCls :   'icon-eye',
                    handler :   this.btnMenu,
                    scope   :   this
                });
            else
                items.push({
                    text    :   'Private',
                    iconCls :   'icon-eye-close', 
                    handler :   this.btnMenu,
                    scope   :   this
                });
                
        items.push('-', {
            text    :   'Add to dataset',
            iconCls :   'icon-add',
            handler :   this.btnMenu,
            scope   :   this
        });

        return Ext.create('Ext.menu.Menu', {
            items       :   items});
    },
    
    btnMenu : function(btn)
    {
        var list = Ext.Object.getSize(this.browser.resourceQueue.selectedRes);
        var tempDS = new BQDataset(), members = [];

        if (list>1)
        {
            for (var res in this.browser.resourceQueue.selectedRes)
                members.push(this.browser.resourceQueue.selectedRes[res]);
            
            tempDS.tmp_setMembers(members);
        }
        
        switch (btn.text)
        {
            case 'Download':
                (list>1) ? tempDS.tmp_downloadMembers() : this.resourceCt.downloadOriginal();
                break;
            case 'Share':
                (list>1) ? tempDS.tmp_shareMembers() : this.resourceCt.shareResource();
                break;
            case 'Private':
                this.resourceCt.changePrivacy('published', Ext.bind(this.success, this));
                break;
            case 'Published':
                this.resourceCt.changePrivacy('private', Ext.bind(this.success, this));
                break;
            case 'Set all published':
                tempDS.tmp_changePermission('published', Ext.bind(this.success, this));
                break;
            case 'Set all private':
                tempDS.tmp_changePermission('private', Ext.bind(this.success, this));
                break;
            case 'Add to dataset':
            {
                function addToDataset(btn, name)
                {
                    if (btn == 'ok')
                    {
                        var newDS = new BQDataset(), members = [];
                        newDS.name = name;
                        
                        for (var res in this.browser.resourceQueue.selectedRes)
                            members.push(new BQValue('object', res));

                        newDS.setMembers(members);
                        
                        function openDS(dataset)
                        {
                            window.location = bq.url('/client_service/view?resource=' + dataset.uri);
                        }
                        
                        newDS.save_(undefined, openDS, this.failure);
                    }
                }
                
                Ext.MessageBox.prompt('Enter dataset name', 'New name:', addToDataset, this, false, 'NewDataset');
                break;                
            }
        }
    },
    
    success : function(resource, msg)
    {
        //BQ.ui.notification(msg || 'Operation successful.');
        this.browser.msgBus.fireEvent('Browser_ReloadData', {});
    },
    
    failure : function(msg)
    {
        BQ.ui.error(msg || 'Operation failed!');
    },
})
Ext.define('Bisque.ResourceFactory', {

    statics : {

        baseClass : 'Bisque.Resource',

        getResource : function(config) {
            var layoutKey = Ext.Object.getKey(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS, config.layoutKey);
            // resource naming convention : baseClass.resourceType.layoutKey
            var className = Bisque.ResourceFactory.baseClass + '.' + Ext.String.capitalize(config.resource.resource_type.toLowerCase()) + '.' + layoutKey;
            
            if (Ext.ClassManager.get(className))
                return Ext.create(className, config);
            else
            {
                Ext.log({
                    msg     :   Ext.String.format('Unknown class: {0}, type: {1}, layoutKey: {2}. Initializing with base resource class.', className, config.resource.resource_type, layoutKey),
                    level   :   'warn',
                    stack   :   true
                });
                return Ext.create(Bisque.ResourceFactory.baseClass + '.' + layoutKey, config);
            }
        }
    }
})

// Returns standalone resources 
Ext.define('Bisque.ResourceFactoryWrapper',
{
    statics : 
    {
        getResource : function(config)
        {
    		config.resourceManager = Ext.create('Ext.Component', 
    		{
    			store : {},
    			
    			storeMyData : function(uri, tag, value)
    			{
    				this.store[tag]=value;
    			},
    			
    			getMyData : function(uri, tag)
    			{
                    if (this.store[tag])
                        return this.store[tag];
    				return 0;
    			}
    		});
    		
    		Ext.apply(config,
    		{
    			layoutKey    :   config.layoutKey || Bisque.ResourceBrowser.LayoutFactory.DEFAULT_LAYOUT,
    			msgBus       :   config.msgBus || config.resourceManager,
    			resQ         :   config.resQ || config.resourceManager,
    			browser      :   config.browser || {},
    		});
    		
            function preferencesLoaded(preferences, resource, layoutCls)
            {
                Ext.apply(resource, {
                    preferences     :   preferences,
                    getImagePrefs   :   function(key)
                    {
                        if (this.preferences && this.preferences.Images && this.preferences.Images[key])
                            return this.preferences.Images[key];
                        return '';
                    },
                })
                
                resource.prefetch(layoutCls);
            }

            var resource = Bisque.ResourceFactory.getResource(config);
            var layoutCls = Bisque.ResourceBrowser.LayoutFactory.getLayout({browser:{layoutKey: config.layoutKey}});
            resource.setSize({width: layoutCls.layoutEl.width, height: layoutCls.layoutEl.height})
            resource.addCls(layoutCls.layoutCSS);

            BQ.Preferences.get(
            {
                type        :   'user',
                key         :   'ResourceBrowser',
                callback    :   Ext.bind(preferencesLoaded, this, [resource, layoutCls], true)
            });
    			
    		return resource;
        }
    }
});

/**
 * BaseLayout: Abstract base resource, extends Ext.Container, parent of all other
 * resource types
 *
 * @param {}
 *            config : Includes {resource, layoutKey}. Resource: Passed resource
 *            object, layoutKey : layout key according to which the resource
 *            object will be formatted
 */
Ext.define('Bisque.Resource',
{
    extend:'Ext.container.Container',

    constructor : function(config)
    {
        Ext.apply(this,
        {
            resource : config.resource,
            browser : config.browser,
            layoutKey : config.layoutKey,
            msgBus : config.msgBus,
            resQ : config.resQ,

            border : false,
            cls : 'LightShadow',
            overCls : 'resource-view-over',
			style: 'float:left;'
        });
        
        this.callParent(arguments);
        this.manageEvents();
    },
    
    setLoadingMask : function()
    {
        if (this.getData('fetched')!=1)
            this.setLoading({msg:''});
    },
    
    GetImageThumbnailRel : function(params, actualSize, displaySize)
    {
        return  Ext.String.format('<img class="imageCenterHoz" style="\
                    max-width   :   {0}px;  \
                    max-height  :   {1}px;  \
                    margin-top  :   {2}px;" \
                    src         =   "{3}"   \
                    id          =   "{4}"   />', 
                    displaySize.width,
                    displaySize.height,
                    (0.5*displaySize.height/params.height) * (params.height-actualSize.height),
                    this.getThumbnailSrc(params),
                    this.resource.uri);
    },

    getThumbnailSrc : function(params)
    {
        return this.resource.src + this.getImageParams(params);
    },
    
    getImageParams : function(config)
    {
        var prefs = this.getImagePrefs('ImageParameters') || '?slice=,,{sliceZ},{sliceT}&thumbnail={width},{height}&format=jpeg';

        prefs = prefs.replace('{sliceZ}', config.sliceZ || 1);
        prefs = prefs.replace('{sliceT}', config.sliceT || 1);
        prefs = prefs.replace('{width}', config.width || 150);
        prefs = prefs.replace('{height}', config.height || 150);
        
        return prefs;
    },
    
    getImagePrefs : function(key)
    {
        if (this.browser.preferences && this.browser.preferences.Images && this.browser.preferences.Images[key])
            return this.browser.preferences.Images[key];
        return '';
    },

    GetPropertyGrid : function(configOpts, source)
    {
        var propsGrid=Ext.create('Ext.grid.Panel',
        {
            autoHeight : configOpts.autoHeight,
            style : "text-overflow:ellipsis;"+configOpts.style,
            width : configOpts.width,
            store : Ext.create('Ext.data.Store',
            {
                model: 'Ext.grid.property.Property',
                data: source
            }),
            border : false,
            padding : 1,
            multiSelect: true,
            plugins : new Ext.ux.DataTip(
            {
                tpl : '<div>{value}</div>'
            }),

            columns:
            [{
                text: 'Tag',
                flex: 0.8,
                dataIndex: 'name'
            },
            {
                text: 'Value',
                flex: 1,
                dataIndex: 'value'
            }]
        });

        return propsGrid
    },

    getData : function(tag) 
    {
        if (this.resQ)
            return this.resQ.getMyData(this.resource.uri, tag);
    },
    setData : function(tag, value) {this.resQ.storeMyData(this.resource.uri, tag, value)},
    // Resource functions 
    prefetch : function(layoutMgr)	//Code to prefetch resource data
    {
    	this.layoutMgr=layoutMgr;
    },
    loadResource : Ext.emptyFn,	//Callback fn when data is loaded 

    //Render a default resource view into container when resource data is loaded
    //(can be overridden for a customized view of the resource)
    updateContainer : function()
    {
        // default data shown
        var name = Ext.create('Ext.container.Container', {
            cls : 'lblHeading1',
            html : this.resource.name,
        })

        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : this.resource.resource_type,
        })
        
        var owner = BQApp.userList[this.resource.owner] || {};

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : owner.display_name,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
    
    // getFields : returns an array of data used in the grid view
    getFields : function()
    {
        var resource = this.resource, record = BQApp.userList[this.resource.owner];
        var name = record ? record.find_tags('display_name').value : ''
       
        return ['', resource.name || '', name || '', resource.resource_type, resource.ts, this, {height:21}];
    },

    testAuth1 : function(btn, loaded, permission)
    {
        if (loaded!=true)
        {
            var user = BQSession.current_session.user_uri;
            this.resource.testAuth(user, Ext.bind(this.testAuth1, this, [btn, true], 0));            
        }
        else
        {
            if (permission)
                btn.operation.call(this, btn);
            else
                BQ.ui.attention('You do not have permission to perform this action!');
        }
    },
    
    afterRenderFn : function()
    {
        this.updateContainer();
    },

    manageEvents : function()
    {
    	this.on('afterrender', Ext.Function.createInterceptor(this.afterRenderFn, this.preAfterRender, this));
    },
    
    preAfterRender : function()
    {
		this.setLoadingMask();	// Put a mask on the resource container while loading
		var el=this.getEl();

        el.on('mouseenter', Ext.Function.createSequence(this.preMouseEnter, this.onMouseEnter, this), this);
		el.on('mousemove', this.onMouseMove, this);
		el.on('mouseleave', Ext.Function.createSequence(this.preMouseLeave, this.onMouseLeave, this), this);
		el.on('click', Ext.Function.createSequence(this.preClick, this.onClick, this), this);
		el.on('contextmenu', this.onRightClick, this);
		el.on('dblclick', Ext.Function.createSequence(this.preDblClick, this.onDblClick, this), this);
		
		/*
		// dima: taps are really not needed: double should not be needed anymore with edit mode on the browser
		// and single is being imitated as a click, otherwise we're getting multiple clicks...
		if (this.browser.gestureMgr)
			this.browser.gestureMgr.addListener(
			[
				{ 
					dom: el.dom,
					eventName: 'doubletap',
					listener: Ext.bind(Ext.Function.createSequence(this.preDblClick, this.onDblClick, this), this), 
					//options: {holdThreshold:500}
				},
				{
					dom: el.dom,
					eventName: 'singletap',
					listener: Ext.bind(Ext.Function.createSequence(this.preClick, this.onClick, this), this), 
				}
			]);
	   */
    },

    preClick : function()
    {
        this.msgBus.fireEvent('ResourceSingleClick', this.resource);
        if (!this.el) return; // dima: not sure what this is but it may not exist
    	if (this.el.hasCls('resource-view-selected'))
    	{
    		this.toggleSelect(false);
    		this.fireEvent('unselect', this);
    	}
    	else
    	{
    		this.toggleSelect(true);
    		this.fireEvent('select', this);
    	}
    },
    
    toggleSelect : function(state)
    {
    	if (state)
    	{
            this.removeCls('LightShadow');
            this.addCls('resource-view-selected')
        }
    	else
    	{
    		this.removeCls('resource-view-selected');
			this.addCls('LightShadow');
    	}
    },
    
    preDblClick : function()
    {
		this.msgBus.fireEvent('ResourceDblClick', this.resource);
    },

    preMouseEnter : function()
    {
    	this.removeCls('LightShadow');
    	
    	if (this.browser.selectState == 'SELECT')
    	{
            if (!this.operationBar)
            {
                this.operationBar = Ext.create('Bisque.ResourceBrowser.OperationBar', {
                    renderTo    :   this.getEl(),
                    resourceCt  :   this,
                    browser     :   this.browser
                });
    
                this.operationBar.alignTo(this, "tr-tr");
            }

            this.operationBar.setVisible(true);
        }
    },
    
    preMouseLeave : function()
    {
        if (this.browser.selectState == 'SELECT')
            this.operationBar.setVisible(false);

		if (!this.el.hasCls('resource-view-selected'))
			this.addCls('LightShadow');
    },

    onMouseMove : Ext.emptyFn,

    onMouseEnter : Ext.emptyFn,
    onMouseLeave : Ext.emptyFn,
    onDblClick : Ext.emptyFn,
    onClick : Ext.emptyFn,
    onRightClick : Ext.emptyFn,
    

    /* Resource operations */
    shareResource : function()
    {
        var shareDialog = Ext.create('BQ.ShareDialog', {
            resource    :   this.resource
        });
    },

    downloadOriginal : function()
    {
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },
    
    changePrivacy : function(permission, success, failure)
    {
        function loaded(resource, permission, success, failure)
        {
            if  (permission)
                resource.permission = permission;
            else
                resource.permission = (this.resource.permission=='private')?'published':'private';
            
            resource.append(Ext.bind(success, this), Ext.bind(failure, this));
        }
        
        BQFactory.request({
            uri :   this.resource.uri + '?view=short',
            cb  :   Ext.bind(loaded, this, [permission, success, failure], 1) 
        });
    }
});

Ext.define('Bisque.Resource.Compact', {
    extend:'Bisque.Resource'
});

Ext.define('Bisque.Resource.Card', {
    extend:'Bisque.Resource',
    
    constructor : function()
    {
        Ext.apply(this,
        {
            layout : 'fit'
        });
        
        this.callParent(arguments);
    },
    
    prefetch : function(layoutMgr)
    {
        this.callParent(arguments);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);    //Loading
            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this));
        }
    },

    loadResource : function(data)
    {
        this.resource.tags = data.tags;
        var tag, tagProp, tagArr=[], tags = this.getSummaryTags();
        
        // Show preferred tags first
        for (var i=0;i<this.resource.tags.length;i++)
        {
            tag = this.resource.tags[i];
            tagProp = new Ext.grid.property.Property({
                                                        name: tag.name,
                                                        value: tag.value
                                                    });
            (tags[tag.name])?tagArr.unshift(tagProp):tagArr.push(tagProp);
        }
        
        this.setData('tags', tagArr.slice(0, 7));
        this.setData('fetched', 1); //Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
    
    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1 && !this.isDestroyed)
            this.updateContainer();
    },
    
    getSummaryTags : function()
    {
        return {};
    },

    updateContainer : function()
    {
        var propsGrid=this.GetPropertyGrid({/*autoHeight:true}*/}, this.getData('tags'));
        propsGrid.determineScrollbars=Ext.emptyFn;
        
        this.add([propsGrid]);
        this.setLoading(false);
    },
    
    onMouseMove : Ext.emptyFn,
});


Ext.define('Bisque.Resource.PStrip', {
    extend:'Bisque.Resource'
});

Ext.define('Bisque.Resource.PStripBig', {
    extend:'Bisque.Resource',
});

Ext.define('Bisque.Resource.Full', {
    extend:'Bisque.Resource',

    constructor : function()
    {
        Ext.apply(this,
        {
            layout : 'fit'
        });
        
        this.callParent(arguments);
    },
    
    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1 && !this.isDestroyed)
            this.updateContainer();
    },
    
    prefetch : function(layoutMgr)
    {
        this.callParent(arguments);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);    //Loading
            BQFactory.load(this.resource.uri + '/tag?view=deep', Ext.bind(this.loadResource, this));
        }
    },

    loadResource : function(data)
    {
        this.setData('tags', data.tags);
        this.setData('fetched', 1); //Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var propsGrid=this.GetPropertyGrid({/*autoHeight:true}*/}, this.getData('tags'));
        propsGrid.determineScrollbars=Ext.emptyFn;
        
        this.add([propsGrid]);
        this.setLoading(false);
    },

    onMouseMove : Ext.emptyFn,

});

Ext.define('Bisque.Resource.List', {
    extend:'Bisque.Resource'
});

// Default page view is a full page ResourceTagger
Ext.define('Bisque.Resource.Page', 
{
    extend   :'Ext.panel.Panel',
    defaults : { border: false, },
    layout   : 'fit',
        
    constructor : function(config)
    {
        var name = config.resource.name || '';
        var type = config.resource.resource_type || config.resource.type;

        Ext.apply(this,
        {
            border  :   false,
            
            tbar    :   Ext.create('Ext.toolbar.Toolbar', 
                        {
                            defaults    :   {
                                                scale       :   'medium',
                                                scope       :   this,
                                                needsAuth   :   true,
                                            },
                            items       :   this.getOperations(config.resource).concat([
                                                '-', '->',
                                                /*{
                                                    itemId      :   'btnOwner',
                                                    iconCls     :   'icon-owner',
                                                    href        :   '/',
                                                    tooltip     :   'Contact the owner of this resource.',
                                                    hidden      :   true,
                                                    needsAuth   :   false,
                                                }, '-',*/
                                                {
                                                    itemId  :   'btnRename',
                                                    text    :   type + ': <b>' + name + '</b>',
                                                    handler :   this.promptName,
                                                    scope   :   this,
                                                    cls     :   'heading',
                                                },
                                             ])
                        }),
        }, config);
        
        this.callParent(arguments);
        this.toolbar = this.getDockedComponent(0);

        this.testAuth(BQApp.user, false);
        this.addListener('afterlayout', this.onResourceRender, this, {single:true});
    },

    onResourceRender : function() 
    {
        this.setLoading(true);

        var resourceTagger = new Bisque.ResourceTagger(
        {
            itemId      :   'resourceTagger',
            title       :   'Annotations',
            resource    :   this.resource,
            split       :   true,
        });
        
        this.add(resourceTagger);
        this.setLoading(false);
    },
    
    testAuth : function(user, loaded, permission, action)
    {
        function disableOperations(action)
        {
            // user is not authorized
            var tbar = this.getDockedItems('toolbar')[0];
            for (var i=0;i<tbar.items.getCount();i++)
            {
                var cmp = tbar.items.getAt(i);
                if (cmp.needsAuth)
                    cmp.setDisabled(true);
                if (cmp.itemId=='btnDelete' && action=='read')
                    cmp.setDisabled(false);
            }
        }

        if (user)
        {
            /*if (user.uri!=this.resource.owner)
            {
                var btn = this.toolbar.getComponent('btnOwner'); 
                btn.setText(user.display_name || '');
                btn.getEl().down('a', true).setAttribute('href', 'mailto:' + user.email_address);
                btn.setVisible(true);
            }*/
            
            if (!loaded)
                this.resource.testAuth(user.uri, Ext.bind(this.testAuth, this, [user, true], 0));            
            else
                if (!permission)
                    disableOperations.call(this, action);
        }
        else if (user===undefined)
            // User autentication hasn't been done yet
            BQApp.on('gotuser', Ext.bind(this.testAuth, this, [false], 1));
        else if (user == null)
            disableOperations.call(this)
    },
    
    getOperations : function(resource)
    {
        var items=[];

        items.push({
            xtype       :   'button',
            text        :   'Download',
            itemId      :   'btnDownload',
            iconCls     :   'icon-download-small',
            needsAuth   :   false,
            compression :   'tar',
            menu        :   {
                                defaults    :   {
                                                    group       :   'downloadGroup',
                                                    groupCls    :   Ext.baseCSSClass + 'menu-group-icon',
                                                    scope       :   this,
                                                    handler     :   this.downloadResource,
                                                    operation   :   this.downloadResource,
                                                },
                                items       :   [{
                                                    xtype       :   'menuitem',
                                                    compression :   'none',
                                                    text        :   'Original'
                                                }, {
                                                    xtype       :   'menuseparator'
                                                }, {
                                                    compression :   'tar',
                                                    text        :   'as TARball',
                                                },{
                                                    compression :   'gzip',
                                                    text        :   'as GZip archive',
                                                },{
                                                    compression :   'bz2',
                                                    text        :   'as BZip2 archive',
                                                },{
                                                    compression :   'zip',
                                                    text        :   'as (PK)Zip archive',
                                                },]
                            }
        },
        {
            itemId      :   'btnShare',
            text        :   'Share',
            iconCls     :   'icon-group',
            operation   :   this.shareResource,
            handler     :   this.testAuth1
        },
        {
            itemId      :   'btnDelete',
            text        :   'Delete',
            iconCls     :   'icon-delete',
            handler     :   this.deleteResource,
        },
        {
            itemId      :   'btnPerm',
            operation   :   this.changePrivacy,
            handler     :   this.testAuth1,
            setBtnText  :   function(me)
                            {
                                var text = 'Visibility: ';
                                
                                if (this.resource.permission == 'published')
                                {
                                    text += '<span style="font-weight:bold;color: #079E0C">published</span>';
                                    me.setIconCls('icon-eye');
                                }
                                else
                                {
                                    text += 'private';
                                    me.setIconCls('icon-eye-close')
                                }
                                
                                me.setText(text);
                            },
            listeners   :   {
                                'afterrender'   :   function(me)
                                                    {
                                                        me.setBtnText.call(this, me);
                                                    },
                                scope           :   this
                
                            }
        });
        
        
        return items;
    },
    
    testAuth1 : function(btn, loaded, permission)
    {
        if (loaded!=true)
        {
            var user = BQSession.current_session.user_uri;
            this.resource.testAuth(user, Ext.bind(this.testAuth1, this, [btn, true], 0));            
        }
        else
        {
            if (permission)
                btn.operation.call(this, btn);
            else
                BQ.ui.attention('You do not have permission to perform this action!');
        }
    },
    
    /* Resource operations */

    shareResource : function()
    {
        var shareDialog = Ext.create('BQ.ShareDialog', {
            resource    :   this.resource
        });
    },

    deleteResource : function()
    {
        function success()
        {
            this.setLoading(false);
            
            Ext.MessageBox.show({
                title   :   'Success',
                msg     :   'Resource deleted successfully! You will be redirected to your BISQUE homepage.',
                buttons :   Ext.MessageBox.OK,
                icon    :   Ext.MessageBox.INFO,
                fn      :   function(){window.location = bq.url('/')}
            });
        }
        
        function deleteRes(response)
        {
            if (response == 'yes')
            {
                this.setLoading({msg:'Deleting...'});
                this.resource.delete_(Ext.bind(success, this), Ext.Function.pass(this.failure, ['Delete operation failed!']));
            }
        }
        
        Ext.MessageBox.confirm('Confirm operation', 'Are you sure you want to delete ' + this.resource.name + '?', Ext.bind(deleteRes, this));
    },
    
    renameResource : function(btn, name, authRecord)
    {
        function success(msg)
        {
            BQ.ui.notification(msg);
            var type = this.resource.resource_type || this.resource.type;
            this.toolbar.getComponent('btnRename').setText(type + ': <b>' + (this.resource.name || '') + '</b>');
        }
        
        if (btn == 'ok' && this.resource.name != name) {
            var type = this.resource.resource_type || this.resource.type;
            var successMsg = type + ' <b>' + this.resource.name + '</b> renamed to <b>' + name + '</b>.';
            this.resource.name = name;
            this.resource.save_(undefined, success.call(this, successMsg), Ext.bind(this.failure, this));
        }
    },
    
    downloadResource : function(btn)
    {
        if (btn.compression == 'none')
            this.downloadOriginal();
        else
        {
            var exporter = Ext.create('BQ.Export.Panel');
            exporter.downloadResource(this.resource, btn.compression);
        }
    },
    
    downloadOriginal : function()
    {
        if (this.resource.src ) {
            window.open(this.resource.src);
            return;
        }
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },
    
    changePrivacy : function(btn)
    {
        function loaded(resource)
        {
            resource.permission = (this.resource.permission=='private')?'published':'private';
            resource.append(Ext.bind(success, this), Ext.bind(this.failure, this));
        }
        
        function success(resource)
        {
            this.setLoading(false);

            // can also broadcast 'reload' event on the resource, once apps start listening to it.
            this.resource.permission = resource.permission;
            var btnPerm = this.toolbar.getComponent('btnPerm');
            btnPerm.setBtnText.call(this, btnPerm);
        };
        
        this.setLoading({msg:''});
        
        BQFactory.request({
            uri :   this.resource.uri + '?view=short',
            cb  :   Ext.bind(loaded, this)
        });
    },
       
    promptName : function(btn)
    {
        Ext.MessageBox.prompt('Rename "' + this.resource.name+'"', 'Please, enter new name:', this.renameResource, this, false, this.resource.name);
    },

    success : function(resource, msg)
    {
        BQ.ui.notification(msg || 'Operation successful.');
    },
    
    failure : function(msg)
    {
        BQ.ui.error(msg || 'Operation failed!');
    },
    
    prefetch : Ext.emptyFn
});

Ext.define('Bisque.Resource.Grid', {
    extend:'Bisque.Resource',
});

/* Abstract Image resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Image',
{
    extend:'Bisque.Resource',
    
    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1 && !this.isDestroyed)
            this.updateContainer();
    },

    OnDblClick : function()
    {
        this.msgBus.fireEvent('ResourceDblClick', this.resource.uri);
    },

    onMouseEnter : function(e, me)
    {
        Ext.Ajax.request({
            url         :   this.resource.src + '?meta',
            callback    :   function(opts, success, response) {
                                if (response.status>=400)
                                    clog(response.responseText);
                                else
                                    this.onMetaLoaded(response.responseXML);
                            },
            scope       :   this,
            disableCaching  :   false,
        });
    },
    
    onMetaLoaded : function(xmlDoc)
    {
        if(!xmlDoc) return;
        
        this.resource.t = evaluateXPath(xmlDoc, "//tag[@name='image_num_t']/@value")[0].value;
        this.resource.z = evaluateXPath(xmlDoc, "//tag[@name='image_num_z']/@value")[0].value;

        // only 1 frame available
        if (this.resource.t==1 && this.resource.z==1)
            this.mmData={isLoadingImage:true};
        else
        {           
            var el = this.getEl();
            if (this.getData('fetched')==1)
                this.mmData =
                {
                    x : el.getX() + el.getOffsetsTo(this.resource.uri)[0],
                    y : el.getY() + el.getOffsetsTo(this.resource.uri)[1],
                    isLoadingImage : false
                };
        }
    },

    onMouseLeave : function()
    {
        if (this.mmData)
            this.mmData.isLoadingImage = true;
    },

    onMouseMove : function(e, target)
    {
        if (this.mmData && !this.mmData.isLoadingImage)
        {
            this.mmData.isLoadingImage = true;

            var sliceX = Math.ceil((e.getX() - this.mmData.x) * this.resource.t / target.clientWidth);
            var sliceY = Math.ceil((e.getY() - this.mmData.y) * this.resource.z / target.clientHeight);

            if (sliceX > this.resource.t)
                sliceX = this.resource.t
            if (sliceY > this.resource.z)
                sliceY = this.resource.z

            var imgLoader = new Image();
            imgLoader.style.height = this.layoutMgr.layoutEl.imageHeight;
            imgLoader.style.width = this.layoutMgr.layoutEl.imageWidth;
             
            imgLoader.onload = Ext.bind(ImgOnLoad, this);
            imgLoader.onerror = Ext.emtpyFn;

            imgLoader.src = this.resource.src + this.getImageParams({
                sliceZ : sliceY,
                sliceT : sliceX,
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight
            });
            
            function ImgOnLoad()
            {
                if (Ext.isDefined(document.images[this.resource.uri]))
                {
                    document.images[this.resource.uri].src = imgLoader.src;
                    this.mmData.isLoadingImage = false;
                }
            }
        }
    },
    
    /* Resource operations */
    downloadOriginal : function()
    {
        window.open(this.resource.src);
    },
});

Ext.define('Bisque.Resource.Image.Compact',
{
    extend : 'Bisque.Resource.Image',
    
  	afterRenderFn : function(e)
  	{
		if (!this.ttip)
    	{
    		this.mouseIn=false;
	    	this.ttip=Ext.create('Ext.tip.ToolTip', 
	    	{
	    		target: this.id,
	    		anchor: "top",
	    		maxWidth: 600,
	    		width: 555,
	    		cls: 'LightShadow',
	    		dismissDelay: 0,
	    		style: 'background-color:#FAFAFA;border: solid 2px #E0E0E0;',
	    		layout: 'hbox',
	    		autoHide : false,
	    		listeners : 
	    		{
	    			"beforeshow" : function(me){if (!this.tagsLoaded || !this.mouseIn) return false;},
	    			scope : this
	    		}
	    	});
    	}
    	this.callParent(arguments);
  	},
  	
  	onRightClick : function(e)
  	{
  		e.preventDefault();
  		this.mouseIn=true;
		(!this.tagsLoaded)?this.requestTags():this.ttip.show();
  	},
  	
  	onMouseLeave : function(e)
  	{
  		this.mouseIn=false;
  		this.callParent(arguments);
  	},
  	
    requestTags : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this, ['tags'], true)});
    		BQFactory.request({uri: this.resource.src + '?meta', cb: Ext.bind(this.tagData, this, ['meta'], true)});
    	}
    },
    
	tagData : function(data, type)
	{
		this.tagsLoaded=true;
		this.resource.tags=data.tags;
		
		var tagArr=[], tags =
		{
		}, found='';

		for (var i = 0; i < this.resource.tags.length; i++)
		{
			found = this.resource.tags[i].value;
			tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
			tagArr.push(new Ext.grid.property.Property(
			{
				name: this.resource.tags[i].name,
				value: tags[this.resource.tags[i].name]
			}));
		}
        
        var propsGrid=this.GetPropertyGrid({width:270}, tagArr);
        
        if (type=='tags')
        	propsGrid.title='Tag data';
        else
        	propsGrid.title='Metadata';
        
        this.ttip.add(propsGrid);
		this.ttip.show();
	},
	    
    prefetch : function(layoutMgr)
    {
    	this.callParent(arguments);
    	
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload  = Ext.bind(this.loadResource, this, ['image'], true);
            prefetchImg.onerror = Ext.bind(this.resourceError, this);
            prefetchImg.onabort = Ext.bind(this.resourceError, this);
        }
    },
    
    resourceError : function()
    {
        var errorImg = '<img style="display: block; margin-left: auto; margin-right: auto; margin-top: 60px;"'
                            + ' src="' + bq.url('/js/ResourceBrowser/Images/unavailable.png') + '"/>';
        this.setData('image', errorImg);
        this.setData('fetched', 1);
        this.update(errorImg);
        
        if (!this.rendered)
            this.on('afterrender', function(me){
                me.setLoading(false);
            }, this, {single:true});
        else
            this.setLoading(false);
    },

    loadResource : function(data, type)
    {
        if (type=='image')
        {
            this.setData('image', this.GetImageThumbnailRel( 
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            },
            {
                width:data.currentTarget.width,
                height:data.currentTarget.height
            },
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            }));
        }

        if (this.getData('image'))
        {
            this.setData('fetched', 1); //Loaded
    
            var renderedRef=this.getData('renderedRef')
            if (renderedRef)
                renderedRef.updateContainer();
        }
    },

    updateContainer : function()
    {
        var text = Ext.String.ellipsis(this.resource.name, 25) || '';
        this.update('<div class="textOnImage" style="width:'+this.layoutMgr.layoutEl.width+'px;">'+text+'</div>'+this.getData('image'));
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Image.Card',
{
    extend : 'Bisque.Resource.Image',

	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
                type : 'vbox',
                align : 'stretch'
            }
        });
		
		this.callParent(arguments);
	},
	
    prefetch : function(layoutMgr)
    {
    	this.callParent(arguments);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type)
    {
        if (type=='image')
            this.setData('image', this.GetImageThumbnailRel( 
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight
            },
            {
                width: data.currentTarget.width,
                height: data.currentTarget.height
            },
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            }));
        else
        {
            this.resource.tags = data.tags;

            var tag, tagProp, tagArr=[], tags = this.getSummaryTags();
            
            // Show preferred tags first
            for (var i=0;i<this.resource.tags.length;i++)
            {
                tag = this.resource.tags[i];
                tagProp = new Ext.grid.property.Property({
                                                            name: tag.name,
                                                            value: tag.value
                                                        });
                (tags[tag.name])?tagArr.unshift(tagProp):tagArr.push(tagProp);
            }
            
            this.setData('tags', tagArr.slice(0, 7));
        }

        if (this.getData('tags') && this.getData('image'))
        {
            this.setData('fetched', 1);	//Loaded

            var renderedRef=this.getData('renderedRef')
            if (renderedRef	&& !renderedRef.isDestroyed)
                renderedRef.updateContainer();
        }
    },
    
    getSummaryTags : function()
    {
        if(this.browser.preferences["Summary Tags"])
            return this.browser.preferences["Summary Tags"];

        return {
            "filename" : 0,
            "attached-file" : 0,
            "image_type" : 0,
            "imagedate" : 0,
            "experimenter" : 0,
            "dataset_label" : 0,
            "species" : 0
        };
    },

    updateContainer : function()
    {
        var propsGrid=this.GetPropertyGrid({/*autoHeight:true}*/}, this.getData('tags'));
        propsGrid.determineScrollbars=Ext.emptyFn;
        
        var imgCt=new Ext.Component({html:this.getData('image'), height:this.layoutMgr.layoutEl.imageHeight});
        this.add([imgCt, propsGrid]);
        this.setLoading(false);
    },
    
	onMouseMove : Ext.emptyFn,
});

Ext.define('Bisque.Resource.Image.Full',
{
    extend : 'Bisque.Resource.Image',

	constructor : function()
	{
        Ext.apply(this,
        {
            layout:'fit',
        });
		
		this.callParent(arguments);
	},

    prefetch : function(layoutMgr)
    {
    	this.callParent(arguments);
    	
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
            
            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type)
    {
        if (type=='image')
            this.setData('image', this.GetImageThumbnailRel(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight
            },
            {
                width: data.currentTarget.width,
                height: data.currentTarget.height
            },
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
                
            }));
        else
        {
            this.resource.tags = data.tags;
            var tagArr=[], tags =
            {
            }, found='';

            for (var i = 0; i < this.resource.tags.length; i++)
            {
                found = this.resource.tags[i].value;
                tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
                tagArr.push(new Ext.grid.property.Property(
                {
                    name: this.resource.tags[i].name,
                    value: tags[this.resource.tags[i].name]
                }));
            }

            this.setData('tags', tagArr);
        }

        if (this.getData('tags') && this.getData('image'))
        {
            this.setData('fetched', 1);	//Loaded
            if (this.rendered)
                this.updateContainer();
        }
    },

    updateContainer : function()
    {
        this.setLoading(false);

        var propsGrid=this.GetPropertyGrid(
        {
            autoHeight:false
        }, this.getData('tags'));

        propsGrid.setAutoScroll(true);

        Ext.apply(propsGrid, {
            region  :   'center',
            padding :   5,
            style   :   'background-color:#FAFAFA'
            
        });

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.dom.align = "center";
        imgDiv.update(this.getData('image'));

        this.add(new Ext.Panel(
        {
            layout  :   'border',
            border  :   false,
            items   :   [new Ext.Container(
            {
                region  :   'west',
                layout  :
                {
                    type    :   'hbox',
                    pack    :   'center',
                    align   :   'center'
                },
                region  :   'west',
                width   :   this.layoutMgr.layoutEl.imageHeight,
                style   :   'background-color:#FAFAFA',
                contentEl   :   imgDiv
            }), propsGrid]
        }));
    },

    onMouseMove : Ext.emptyFn,
    onMouseEnter : Ext.emptyFn
});


Ext.define('Bisque.Resource.Image.Grid',
{
    extend : 'Bisque.Resource.Image',
    
    prefetch : function(layoutMgr)
    {
        this.callParent(arguments);
        var prefetchImg = new Image();
        
        prefetchImg.src = this.getThumbnailSrc(
        {
            width   :   this.layoutMgr.layoutEl.stdImageWidth,
            height  :   this.layoutMgr.layoutEl.stdImageHeight,
        });
    },
    
    getFields : function(cb)
    {
        var fields = this.callParent();
        
        fields[0] = '<div class="gridCellIcon" >' + this.GetImageThumbnailRel( 
        {
            width   :   280,
            height  :   280
        },
        {
            width   :   280,
            height  :   280
        },
        {
            width   :   40,
            height  :   40,
        }) + '</div>';
        
        fields[6].height = 48;

        return fields;
    },
});



// Page view for an image
Ext.define('Bisque.Resource.Image.Page',
{
    extend : 'Bisque.Resource.Page',
    
    onResourceRender : function()
    {
        this.setLoading(true);
        this.root = '';
        if (this.resource && this.resource.uri)
            this.root = this.resource.uri.replace(/\/data_service\/.*$/i, '');  
        
        var resourceTagger = Ext.create('Bisque.ResourceTagger', 
        {
            resource : this.resource,
            title : 'Annotations',
        });
    
        var embeddedTagger = Ext.create('Bisque.ResourceTagger', {
            resource : this.resource.src + '?meta',
            title           :   'Embedded',
            viewMode        :   'ReadOnly',
            disableAuthTest :   true
        });
    
        var mexBrowser = new Bisque.ResourceBrowser.Browser(
        {
            'layout' : 5,
            'title' : 'Analysis',
            'viewMode' : 'MexBrowser',
            'dataset' : this.root+'/data_service/mex',
            'tagQuery' : '"'+this.resource.uri+'"',
            'wpublic' : true,
            showOrganizer: false, 
    
            mexLoaded : false,
    
            listeners :
            {
                'browserLoad' : function(me, resQ) {
                    me.mexLoaded = true;
                },
                'Select' : function(me, resource) {
                    window.open(bq.url('/module_service/'+resource.name+'/?mex='+resource.uri));
                },
                scope:this
            },
        });
        
        var resTab = Ext.create('Ext.tab.Panel', {
            title : 'Metadata',
            region : 'east',
            activeTab : 0,
            border : false,
            bodyBorder : 0,
            collapsible : true,
            split : true,
            width : 400,
            plain : true,
            bodyStyle : 'background-color:#F00',
            items : [resourceTagger, embeddedTagger, mexBrowser]
        });

        var viewerContainer = Ext.create('BQ.viewer.Image', {
            region      :   'center',
            resource    :   this.resource,
            toolbar     :   this.toolbar,
            parameters  :   {
                                gobjectCreated  :   Ext.bind(function(gob)
                                                    {
                                                        this.gobjectTagger.appendGObjects([gob])
                                                    }, this),
                                
                                gobjectDeleted  :   Ext.bind(function(gi)
                                                    {
                                                        this.gobjectTagger.deleteGObject(gi)
                                                    }, this),
                            },
            listeners   :   {
                                'changed'   :   function(me, gobjects)
                                {
                                    this.gobjectTagger.tree.getView().refresh();
                                },
                                scope       :   this
                            }
        });
    
        this.add({
            xtype : 'container',
            layout : 'border',
            items : [viewerContainer, resTab]
        });
    
        this.gobjectTagger = new Bisque.GObjectTagger(
        {
            resource        :   this.resource,
            imgViewer       :   viewerContainer.viewer,
            mexBrowser      :   mexBrowser,
            title           :   'Graphical',
            viewMode        :   'GObjectTagger',
            readFromMex     :   function(resQ)
                                {
                                    function changeFormat(mex)
                                    {
                                        this.appendFromMex([{resource:mex}]);
                                    } 
                                    
                                    for (var i=0; i<resQ.length; i++)
                                        BQFactory.request({
                                            uri :   resQ[i].resource.uri+'?view=deep',
                                            cb  :   Ext.bind(changeFormat, this)
                                        });
                                },
            
            listeners       :
            {
                'beforeload' : function(me, resource)
                {
                    me.imgViewer.start_wait(
                    {
                        op : 'gobjects',
                        message : 'Fetching gobjects'
                    });
                },
                'onload' : function(me, resource)
                {
                    me.imgViewer.loadGObjects(resource.gobjects, false);
    
                    if(me.mexBrowser.mexLoaded)
                        me.readFromMex(me.mexBrowser.resourceQueue);
                    else
                        me.mexBrowser.on('browserLoad', function(mb, resQ)
                        {
                            me.readFromMex(resQ);
                        }, me);
    
                },
                'onappend' : function(me, gobjects)
                {
                    me.imgViewer.gobjectsLoaded(true, gobjects);
                },
    
                'select' : function(me, record, index)
                {
                    var gobject = (record.raw instanceof BQGObject)?record.raw:record.raw.gobjects;
                    me.imgViewer.showGObjects(gobject);
                },
    
                'deselect' : function(me, record, index)
                {
                    var gobject = (record.raw instanceof BQGObject)?record.raw:record.raw.gobjects;
                    me.imgViewer.hideGObjects(gobject);
                }
            }
        });
        resTab.add(this.gobjectTagger);

        resTab.add({        
            xtype: 'bqgmap',
            title: 'Map',
            url: this.resource.src+'?meta',
            zoomLevel: 16,
            gmapType: 'map',
            autoShow: true,
        });
                
        this.setLoading(false);
    },
    
    downloadOriginal : function()
    {
        window.open(this.resource.src);
    }
});
/* Abstract Mex resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Mex',
{
    extend:'Bisque.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Mex.Compact',
{
    extend : 'Bisque.Resource.Mex',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'vbox',
            	align:'stretch'	
            }
        });
		this.callParent(arguments);
		this.addCls('compact');		
	},
	
    onMouseEnter : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this)});
    	}
    	this.callParent(arguments);
    },
    
	tagData : function(data)
	{
		this.tagsLoaded=true;
		this.resource.tags=data.tags;
		
		var tagArr=[], tags = {}, found='';

		for (var i = 0; i < this.resource.tags.length; i++)
		{
			found = this.resource.tags[i].value;
			tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
			tagArr.push(new Ext.grid.property.Property(
			{
				name: this.resource.tags[i].name,
				value: tags[this.resource.tags[i].name]
			}));
		}
        
        var propsGrid=this.GetPropertyGrid({width:270}, tagArr);
        
        if (tagArr.length>0 && this.ttip)
            this.ttip.add(propsGrid);
        if (this.ttip)            
		    this.ttip.setLoading(false);
	},

    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
            this.loadResource({name:'Module.NoName'});
		}
    },
    
	loadResource : function(moduleInfo)
    {
		this.setData('module', moduleInfo.name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var name = Ext.create('Ext.container.Container', {
            cls : 'lblHeading1',
            html : Ext.String.ellipsis(this.resource.name || 'undefined', 24),
        })

        var date = new Date();
        date.setISO(this.resource.ts);
        
        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : Ext.Date.format(date, "m-d-Y g:i:s a"),
        })

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : this.resource.value,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
});


Ext.define('Bisque.Resource.Mex.Card',
{
    extend : 'Bisque.Resource.Card',
    
    prefetch : function(layoutMgr)
    {
        this.superclass.superclass.prefetch.apply(this, arguments);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);    //Loading
            BQFactory.load(this.resource.uri + '/tag?view=deep', Ext.bind(this.loadResource, this));
        }
    },

    loadResource : function(data)
    {
        this.resource.tags = data.tags;
        var tagProp, tagArr=[], tagsFlat = this.resource.toDict(true);

        // Show preferred tags first
        for (var tag in tagsFlat)
        {
            tagProp = new Ext.grid.property.Property({
                                                        name: tag,
                                                        value: tagsFlat[tag]
                                                    });
            (tag.indexOf('inputs')!=-1 || tag.indexOf('outputs')!=-1)?tagArr.unshift(tagProp):tagArr.push(tagProp);
        }
        
        this.setData('tags', tagArr.slice(0, 12));
        this.setData('fetched', 1); //Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
    
});


Ext.define('Bisque.Resource.Mex.Full',
{
    extend : 'Bisque.Resource.Full',
    
    loadResource : function(data)
    {
        this.resource.tags = data.tags;
        var tagProp, tagArr=[], tagsFlat = this.resource.toDict(true);

        // Show preferred tags first
        for (var tag in tagsFlat)
        {
            tagProp = new Ext.grid.property.Property({
                                                        name: tag,
                                                        value: tagsFlat[tag]
                                                    });
            tagArr.push(tagProp);
        }
        
        this.setData('tags', tagArr);
        this.setData('fetched', 1); //Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
})

Ext.define('Bisque.Resource.Mex.List',
{
    extend : 'Bisque.Resource.Mex',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'hbox',
            	align:'middle'	
            }
        });
		this.callParent(arguments);
		this.addCls('list');			
	},

    afterRenderFn : function(me)
    {
    	if (!this.ttip)
    	{
            this.ttip = Ext.create('Ext.tip.ToolTip', {
                target      :   me.id,
                width       :   278,
                cls         :   'LightShadow',
                layout      :   'hbox',
                style       :   {
                                    'background-color'  :   '#FAFAFA',
                                    'border'            :   'solid 3px #E0E0E0'
                                },
                listeners   :   {
                                    'afterrender'   :   function(me)
                                    {
                                        if (!this.tagsLoaded)
                                            me.setLoading({msg:''})
                                    },
                                    scope   :   this
                                }            
    	   }); 
        }    	
    	
        // HACK to hide session "mex". Come up with better strategy in future
        //if (this.resource.status=='SESSION')
        //    this.setVisible(false);

    	this.callParent(arguments);
    },
    
    onMouseEnter : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this)});
    	}
    	this.callParent(arguments);
    },
    
    onMouseLeave : function(e)
    {
        this.mouseIn=false;
        this.callParent(arguments);
    },
    
	tagData : function(data)
	{
		this.tagsLoaded=true;
		this.resource.tags=data.tags;
		
		var tagArr=[], tags = {}, found='';

		for (var i = 0; i < this.resource.tags.length; i++)
		{
			found = this.resource.tags[i].value;
			tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
			tagArr.push(new Ext.grid.property.Property(
			{
				name: this.resource.tags[i].name,
				value: tags[this.resource.tags[i].name]
			}));
		}
        
        var propsGrid=this.GetPropertyGrid({width:270}, tagArr);
        
        if (tagArr.length>0)
            this.ttip.add(propsGrid);
		this.ttip.setLoading(false);
	},
    
    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
			
			if (this.resource.module && this.resource.module.indexOf(window.location.host)!=-1)	// HACK: Load module names if running on the same host
			{
				BQFactory.request(
				{
					uri:this.resource.module,
					cb:Ext.bind(this.loadResource, this),
					errorcb:Ext.emptyFn
				});
			}
			else
			{
                this.loadResource({name:'Module.NoName'});
			}
		}
    },

	loadResource : function(moduleInfo)
    {
		this.setData('module', this.resource.name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var mexName=new Ext.form.Label({
			text:' '+Ext.String.ellipsis(this.resource.name, 22)+' ',
			padding:'0 8 0 8',
			cls:'lblModuleName',
		})

		var mexStatus=new Ext.form.Label({
			text:this.resource.status,
			padding:'0 0 0 4',
			cls: this.resource.status=='FINISHED'?'lblModuleOwnerFin':(this.resource.status=='FAILED'?'lblModuleOwnerFail':'lblModuleOwner')
		})

		var date=new Date();
		date.setISO(this.resource.ts);
		
		var mexDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			padding:'0 0 0 8',
			//style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
			cls: 'lblModuleDate',
			flex: 1,			
		})

		this.add([mexName, mexStatus, mexDate]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Mex.Grid',
{
    extend : 'Bisque.Resource.Mex',
    
    getFields : function(cb)
    {
        var status = this.resource.status || 'unknown', resource = this.resource;
        var color = (status=='FINISHED') ? '#1C1' : (status=='FAILED') ? '#E11' : '#22F';
       
        return ['', resource.name || '', '<div style="color:'+color+'">'+Ext.String.capitalize(status.toLowerCase())+'</div>' || '', resource.resource_type, resource.ts, this, {height:21}];
    }
});

// Page view for a mex
/*Ext.define('Bisque.Resource.Mex.Page',
{
    extend : 'Bisque.Resource.Page',
    
    constructor : function(config)
    {
        window.location = bq.url('/module_service/'+config.resource.name+'/?mex='+config.resource.uri);
    }
});*/

        


/* Abstract Module resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Module',
{
    extend:'Bisque.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Module.Compact',
{
    extend : 'Bisque.Resource.Module',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'vbox',
            	align:'stretch'	
            }
        });
	
		this.callParent(arguments);
        this.addCls('compact');		
	},

    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
	        
	        BQFactory.request({
	        	uri:this.resource.owner,
	        	cb:Ext.bind(this.loadResource, this),
	        	errorcb:Ext.emptyFn});
		}
    },
    
	loadResource : function(ownerInfo)
    {
		this.setData('owner', ownerInfo.display_name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var name = Ext.create('Ext.container.Container', {
            cls : 'lblHeading1',
            html : this.resource.name,
        })

        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : this.getData('owner'),
        })

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : this.resource.value,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Module.List',
{
    extend : 'Bisque.Resource.Module',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'hbox',
            	align:'middle'	
            }
        });
		
		this.callParent(arguments);
	},
    
    afterRenderFn : function(me)
    {
    	if (!this.ttip)
    	{
	    	this.ttip=Ext.create('Ext.tip.ToolTip', 
	    	{
	    		target: me.id,
	    		width:278,
	    		cls:'LightShadow',
	    		style:'background-color:#FAFAFA;border: solid 3px #E0E0E0;',
	    		layout:'hbox',
                autoHide : false,
	    		listeners : 
	    		{
	    			"afterrender" : function(me){if (!this.tagsLoaded) me.setLoading({msg:''})},
	    			scope : this
	    		}
	    	});
    	}
    	
    	this.callParent(arguments);

    },
    
    onMouseEnter : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this)});
    	}
    	this.callParent(arguments);
    },
    
	tagData : function(data)
	{
		this.tagsLoaded=true;
		this.resource.tags=data.tags;
		
		var tagArr=[], tags =
		{
		}, found='';

		for (var i = 0; i < this.resource.tags.length; i++)
		{
			found = this.resource.tags[i].value;
			tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
			tagArr.push(new Ext.grid.property.Property(
			{
				name: this.resource.tags[i].name,
				value: tags[this.resource.tags[i].name]
			}));
		}
        
        var propsGrid=this.GetPropertyGrid({width:270}, tagArr);
        
        this.ttip.add(propsGrid);
		this.ttip.setLoading(false);
	},
    
    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	// -1 = Loading
	        
            BQFactory.request(
            {
                uri:this.resource.uri+'?view=deep',
                cb:Ext.bind(this.loadResourceTags, this),
                errorcb:Ext.emptyFn
            });
		}
    },
    
    loadResourceTags : function(resource)
    {
      this.setData('tags', resource.tags);

      BQFactory.request(
      {
          uri:this.resource.owner,
          cb:Ext.bind(this.loadResource, this),
          errorcb:Ext.emptyFn
      });
    },
    
	loadResource : function(ownerInfo)
    {
		this.setData('owner', ownerInfo.display_name);
		this.setData('fetched', 1);	// 1 = Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var moduleName=new Ext.form.Label({
			text:' '+this.resource.name+' ',
			//padding:5,
			cls:'lblModuleName',
		})

		var moduleOwner=new Ext.form.Label({
			text:this.getData('owner'),
			//padding:'0 0 0 5',
			cls:'lblModuleOwner'
		})

		var moduleType=new Ext.form.Label({
			text:this.resource.type,
			padding:5,
			style:'color:#444'
		})

		this.add([moduleName, moduleOwner, moduleType]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Module.IconList',
{
    extend : 'Bisque.Resource.Module.List',

    initComponent : function() {
        this.addCls('icon-list');
        this.callParent();
    },	    
    
    afterRenderFn : function()
    {
        this.ttip=1;
        this.tagsLoaded=1;
        this.callParent(arguments);
    },
    
    updateContainer : function()
    {
        var serviceURL = BisqueServices.getURL('module_service') + this.resource.name;
        var tags = this.getData('tags'), description;
        
        for (var i=0;i<tags.length;i++)
            if (tags[i].name=="description")
                description=tags[i].value;

        var imgCt=Ext.create('Ext.container.Container', 
        {
            margin:'0 0 0 4',
            width:110,
            height:110,
            html: '<img style="position:relative;height:100%;width:100%" src="'+serviceURL+'/thumbnail"/>'
        });

        var moduleName=new Ext.form.Label({
            text:this.resource.name,
            //padding:'0 0 1 3',
            cls:'lblModuleName',
        })

        var moduleInfo=new Ext.form.Label({
            html: this.getData('owner')!=0 ? 'Owner: '+this.getData('owner'):'',
            //padding:'0 0 0 3',
            maxHeight:18,
            cls:'lblModuleOwner'
        })

        var moduleDesc=new Ext.form.Label({
            html:description,
            padding:'7 2 0 3',
        })
        
        var rightCt=Ext.create('Ext.container.Container',
        {
            layout:
            {
                type:'vbox',
                align:'stretch'
            },
            margin:'2 0 0 2',
            height:120,
            flex:1,
            
            items: [moduleName, moduleInfo, moduleDesc]
        });
        
        this.add([imgCt, rightCt]);
        this.setLoading(false);
    }
});

// Page view for a module
Ext.define('Bisque.Resource.Module.Page',
{
    extend : 'Bisque.Resource.Page',
    
/*    setDisabled : function(btn)
    {
        
    },
    
    getOperations : function(resource)
    {
        var ops = this.callParent(arguments);
        ops.push({
            itemId      :   'btnDisable',
            operation   :   this.setDisabled,
            handler     :   this.testAuth1,
            setBtnText  :   function(me)
                            {
                                var text = 'Visibility: ';
                                
                                if (this.resource.permission == 'published')
                                {
                                    text += '<span style="font-weight:bold;color: #079E0C">published</span>';
                                    me.setIconCls('icon-eye');
                                }
                                else
                                {
                                    text += 'private';
                                    me.setIconCls('icon-eye-close')
                                }
                                
                                me.setText(text);
                            },
            listeners   :   {
                                'afterrender'   :   function(me)
                                                    {
                                                        me.setBtnText.call(this, me);
                                                    },
                                scope           :   this
                
                            }
        });

        
    }*/
});

/* Abstract Dataset resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Dataset',
{
    extend:'Bisque.Resource',
    
    initComponent : function() {
        this.addCls('dataset');	
        this.callParent();			
	},    

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Dataset.Compact',
{
    extend : 'Bisque.Resource.Dataset',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'vbox',
            	align:'stretch'	
            }
        });
		this.callParent(arguments);
        this.addCls('compact');				
	},
    
    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);    // -1 = Loading
            this.fetchMembers(this.resource);
		}
    },
    
    fetchMembers : function(memberTag)
    {
        BQFactory.request(
        {
            uri:memberTag.uri + '/value?limit=4',
            cb:Ext.bind(this.loadResource, this),
            errorcb:Ext.emptyFn
        });
    },
    
	loadResource : function(resource)
    {
        var imgs = '<div style = "margin-left:4px; margin-top:-1px; width:152px;height:152px">'
        var thumbnail, margin;

        for (var i=0;i<resource.children.length && i<4; i++)
        {
                switch (resource.children[i].resource_type)
                {
                    case 'image':
                    {
                        thumbnail = resource.children[i].src+'?slice=,,0,0&thumbnail=280,280&format=jpeg';
                        break;
                    }
                    case 'dataset':
                    {
                        thumbnail = bq.url('../export_service/public/images/folder-large.png');
                        break; 
                    }
                    default :
                        thumbnail = bq.url('../export_service/public/images/file-large.png') 
                }

            margin = (i==1?'margin:0px 0px 0px 2px;':(i==2?'margin:2px 2px 0px 0px;':'')); 
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src='+ thumbnail + ' />'
        }
        
        imgs += '</div>';

        this.setData('fetched', 1); // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var date = new Date();
        date.setISO(this.resource.ts);
        
        this.update('<div class="labelOnImage" style="width:160px;">'+this.resource.name
        +'<br><span class="smallLabelOnImage">'
        + Ext.Date.format(date, "m/d/Y")+'</span></div>'+this.getData('previewDiv'));       
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Dataset.Card',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
    fetchMembers : function(memberTag)
    {
        BQFactory.request(
        {
            uri:memberTag.uri + '/value?limit=12',
            cb:Ext.bind(this.loadResource, this),
            errorcb:Ext.emptyFn
        });
    },

    loadResource : function(resource)
    {
        var imgs = '<div style = "margin:0px 0px 0px 12px;width:258px;height:310px">'
        var thumbnail, margin;

        for (var i=0;i<resource.children.length && i<12; i++)
        {
                switch (resource.children[i].resource_type)
                {
                    case 'image':
                    {
                        thumbnail = resource.children[i].src + this.getImageParams({width:280, height:280}); 
                        break;
                    }
                    case 'dataset':
                    {
                        thumbnail = bq.url('../export_service/public/images/folder-large.png');
                        break; 
                    }
                    default :
                        thumbnail = bq.url('../export_service/public/images/file-large.png') 
                }

            margin = 'margin:0px 3px 2px 0px;'; 
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src='+ thumbnail + ' />'
        }
        
        imgs += '</div>';

        this.setData('fetched', 1); // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
            renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var date = new Date();
        date.setISO(this.resource.ts);
        
        this.update('<div class="labelOnImage" style="width:260px;">'+this.resource.name
        +'<br><span class="smallLabelOnImage">'
        + Ext.Date.format(date, "m/d/Y")+'</span></div>'+this.getData('previewDiv'));       
        this.setLoading(false);
    },
});


Ext.define('Bisque.Resource.Dataset.Full',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
    constructor : function()
    {
        this.callParent(arguments);

        Ext.apply(this,
        {
            layout: 'fit',
        });
    },
    
    fetchMembers : function(memberTag)
    {
        BQFactory.request(
        {
            uri:memberTag.uri + '/value?limit=12',
            cb:Ext.bind(this.loadResource, this),
            errorcb:Ext.emptyFn
        });
    },
    
    loadResource : function(resource)
    {
        var imgs = '<div style = "margin:0px 0px 0px 12px;width:99%;">'
        var thumbnail, margin;

        for (var i=0;i<resource.children.length; i++)
        {
                switch (resource.children[i].resource_type)
                {
                    case 'image':
                    {
                        thumbnail = resource.children[i].src + this.getImageParams({width:280, height:280}); 
                        break;
                    }
                    case 'dataset':
                    {
                        thumbnail = bq.url('../export_service/public/images/folder-large.png');
                        break; 
                    }
                    default :
                        thumbnail = bq.url('../export_service/public/images/file-large.png') 
                }

            margin = 'margin:0px 3px 2px 0px;'; 
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src='+ thumbnail + ' />'
        }
        
        imgs += '</div>';

        this.setData('fetched', 1); // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
            renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var date = new Date();
        date.setISO(this.resource.ts);

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.update('<div class="labelOnImage" style="width:99%;">'+this.resource.name
        +'<br><span class="smallLabelOnImage">'
        + Ext.Date.format(date, "m/d/Y")+'</span></div>'+this.getData('previewDiv'));
        
        this.add(Ext.create('Ext.panel.Panel', {
            border  :   0,
            autoScroll : true,
            contentEl : imgDiv,
        }));
        

        this.setLoading(false);
        
    },
});


Ext.define('Bisque.Resource.Dataset.List',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
   	constructor : function()
	{
		this.callParent(arguments);
		
        Ext.apply(this,
        {
            layout:
            {
            	type:'hbox',
            	align:'middle'	
            }
        });
        this.addCls('list');        
	},
	
    updateContainer : function()
    {
		var datasetName=new Ext.form.Label({
			text:' '+this.resource.name+' ',
			padding:'0 8 0 8',
			cls:'lblModuleName',
		})
		
		var datasetOwner=new Ext.form.Label({
			text:this.getData('owner'),
			padding:'0 0 0 4',
			cls:'lblModuleOwner',
		})

		var date = new Date();
		date.setISO(this.resource.ts);
		
		var datasetDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			cls: 'lblModuleDate',	
			flex: 1,		
			//padding:'0 0 0 8',
            //style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
		})

		this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});

// Page view for a dataset
Ext.define('Bisque.Resource.Dataset.Page',
{
    extend : 'Bisque.Resource',
    
    constructor : function()
    {
        Ext.apply(this, {
            layout:'fit',
        });
        
        this.callParent(arguments);
    },
    
    updateContainer : function()
    {
        this.setLoading(false);
    
        var renderer = Ext.create('BQ.renderers.dataset', {
            resource: this.resource,
            loadmap: true,
        });
        
        this.add(renderer);
    }
});

// Page view for a File
Ext.define('Bisque.Resource.File.Page',
{
    extend : 'Bisque.Resource.Page',
    
    downloadOriginal : function() {
        window.open(this.resource.src);
    }
});


Ext.define('Bisque.Resource.User.Grid',
{
    extend : 'Bisque.Resource.Grid',
    
    getFields : function(displayName)
    {
        var record = BQApp.userList[this.resource.owner];
        this.displayName = record ? record.find_tags('display_name').value : ''; 

        this.resource.display_name = this.displayName;
        var fields = this.callParent();
        fields[1] = this.displayName;
        fields[2] = record['email'] || '';
            
        return fields;
    }
})

// Page view for a template
Ext.define('Bisque.Resource.Template.Page',
{
    extend : 'Bisque.Resource.Page',
    
    onResourceRender : function()
    {
        this.setLoading(false);
        
        var tplMan = new BQ.TemplateManager.create({resource:this.resource});
        this.add(tplMan);
        
        this.toolbar.insert(0, 
        [{
            xtype   :   'tbspacer',
            width   :   8
        },
        {
            text    :   'Save',
            iconCls :   'icon-save',
            handler :   tplMan.saveTemplate,
            scope   :   tplMan
        },
            '-'
        ]);
    },
});

// Simple MessageBus to facilitate communication between Bisque components
Ext.define('Bisque.Misc.MessageBus', {
	extend : 'Ext.util.Observable',
	
	/*events : 
	{
		// ResourceBrowser
		ResourceDblClick : true,
		PStripResourceClick : true,
			// LayoutManager
		ResSelectionChange : true,
			// Browser
		Browser_ReloadData : true,
		SearchBar_Query : true,
		// Organizer
		Organizer_OnCBSelect : true,
		Organizer_OnGridSelect : true
	}*/
})

Ext.namespace('Bisque.Misc');

Ext.define('Bisque.Misc.Slider',
{
	extend : 'Ext.panel.Panel',
	height:32,
	width:200,
	border:false,
	leftBtn:false,
	rightBtn:false,
	
	label:null,
	slider:null,
	
	bodyStyle: 'background:transparent;',
	layout:
	{
		type:'vbox',
		align:'stretch',
	},
	items:
	[
		{
			xtype: 'tbtext',
			text: 'Showing 0 of total 0',
			style: 'text-align:center'
		},
		{
			xtype: 'slider',
			minValue: 0,
			hideLabel: true,
			maxValue: 100,
			margin:'0 10 10 10',
			cls:'sliderBackground',
			tipText : function(thumb)
			{
				return Ext.String.format('<b>View resource: {0}</b>', thumb.value);
			},
		}
	],
	
	initComponent : function()
	{
		this.callParent(arguments);

		this.label=this.getLabel();
		this.slider=this.getSlider();
		
		this.slider.on("changecomplete", function(me, newValue)
		{
			/*if (newValue==me.maxValue && this.rightBtn)
				this.fireEvent('leftButtonClick', newValue-1);
			else if (newValue==me.minValue && this.leftBtn)
				this.fireEvent('rightButtonClick', newValue-1);
			else*/
				this.fireEvent('buttonClick', newValue-1);
		}, this);
	},

	getLabel : function()
	{
		return this.getComponent(0);
	},

	getSlider : function()
	{
		return this.getComponent(1);
	},


    setStatus : function(st)
    {
        if (!this.hidden)
        {
            var mySt = st.sliderSt;
    
            this.label.setText(st.status);
    
            this.showLeftBtn(mySt.left);
            this.showRightBtn(mySt.right);
    
            this.slider.setMinValue(mySt.min);
            this.slider.setMaxValue(mySt.max);
    
            this.slider.setValue(mySt.value);
        }
    },

	showLeftBtn : function(show)
	{
		if (show)
		{
			this.slider.addCls("sliderLeftButton");

			if (this.rightBtn)
				this.slider.addCls("sliderBothButtons");
			
			this.leftBtn=true;
		}
		else
		{
			if (this.rightBtn)
				this.slider.removeCls("sliderBothButtons");
			
			this.slider.removeCls("sliderLeftButton");
	
			this.leftBtn=false;
		}
	},

	showRightBtn : function(show)
	{
		if (show)
		{
			this.slider.addCls("sliderRightButton");

			if (this.leftBtn)
				this.slider.addCls("sliderBothButtons");
			
			this.rightBtn=true;
		}
		else
		{
			if (this.leftBtn)
				this.slider.removeCls("sliderBothButtons");

			this.slider.removeCls("sliderRightButton");
	
			this.rightBtn=false;
		}
	},
	
	destroy : function()
	{
	    if (this.rendered && !this.hidden)
	       this.callParent(arguments);
	}
});
/**
 * @class Ext.ux.DataTip
 * @extends Ext.ToolTip.
 * <p>This plugin implements automatic tooltip generation for an arbitrary number of child nodes <i>within</i> a Component.</p>
 * <p>This plugin is applied to a high level Component, which contains repeating elements, and depending on the host Component type,
 * it automatically selects a {@link Ext.ToolTip#delegate delegate} so that it appears when the mouse enters a sub-element.</p>
 * <p>When applied to a GridPanel, this ToolTip appears when over a row, and the Record's data is applied
 * using this object's {@link Ext.Component#tpl tpl} template.</p>
 * <p>When applied to a DataView, this ToolTip appears when over a view node, and the Record's data is applied
 * using this object's {@link Ext.Component#tpl tpl} template.</p>
 * <p>When applied to a TreePanel, this ToolTip appears when over a tree node, and the Node's {@link Ext.tree.TreeNode#attributes attributes} are applied
 * using this object's {@link Ext.Component#tpl tpl} template.</p>
 * <p>When applied to a FormPanel, this ToolTip appears when over a Field, and the Field's <code>tooltip</code> property is used is applied
 * using this object's {@link Ext.Component#tpl tpl} template, or if it is a string, used as HTML content.</p>
 * <p>If more complex logic is needed to determine content, then the {@link Ext.Component#beforeshow beforeshow} event may be used.<p>
 * <p>This class also publishes a <b><code>beforeshowtip</code></b> event through its host Component. The <i>host Component</i> fires the
 * <b><code>beforeshowtip</code></b> event.
 */
Ext.ux.DataTip = Ext.extend(Ext.ToolTip, (function() {

//  Target the body (if the host is a Panel), or, if there is no body, the main Element.
    function onHostRender() {
        var e = this.body || this.el;
        if (this.dataTip.renderToTarget) {
            this.dataTip.render(e);
        }
        this.dataTip.setTarget(e);
    }

    function updateTip(tip, data) {
        if (tip.rendered) {
            tip.update(data);
        } else {
            if (Ext.isString(data)) {
                tip.html = data;
            } else {
                tip.data = data;
            }
        }
    }
    
    function beforeTreeTipShow(tip) {
        var e = Ext.fly(tip.triggerElement).findParent('div.x-tree-node-el', null, true),
            node = e ? tip.host.getNodeById(e.getAttribute('tree-node-id', 'ext')) : null;
        if(node){
            updateTip(tip, node.attributes);
        } else {
            return false;
        }
    }

    function beforeGridTipShow(tip) {
        var rec = this.host.getStore().getAt(tip.triggerElement.viewIndex);
        
        if (rec){
            updateTip(tip, rec.data);
        } else {
            return false;
        }
    }

    function beforeViewTipShow(tip) {
        var rec = this.host.getRecord(tip.triggerElement);
        if (rec){
            updateTip(tip, rec.data);
        } else {
            return false;
        }
    }

    function beforeFormTipShow(tip) {
        var el = Ext.fly(tip.triggerElement).child('input,textarea'),
            field = el ? this.host.getForm().findField(el.id) : null;
        if (field && (field.tooltip || tip.tpl)){
            updateTip(tip, field.tooltip || field);
        } else {
            return false;
        }
    }

    function beforeComboTipShow(tip) {
        var rec = this.host.store.getAt(this.host.selectedIndex);
        if (rec){
            updateTip(tip, rec.data);
        } else {
            return false;
        }
    }

    return {
        init: function(host) {
            host.dataTip = this;
            this.host = host;
            if (host instanceof Ext.tree.TreePanel) {
                this.delegate = this.delegate || 'div.x-tree-node-el';
                this.on('beforeshow', beforeTreeTipShow);
            } else if (host instanceof Ext.grid.GridPanel) {
                this.delegate = this.delegate || host.getView().itemSelector;
                this.on('beforeshow', beforeGridTipShow);
            } else if (host instanceof Ext.DataView) {
                this.delegate = this.delegate || host.itemSelector;
                this.on('beforeshow', beforeViewTipShow);
            } else if (host instanceof Ext.FormPanel) {
                this.delegate = 'div.x-form-item';
                this.on('beforeshow', beforeFormTipShow);
            } else if (host instanceof Ext.form.ComboBox) {
                this.delegate = this.delegate || host.itemSelector;
                this.on('beforeshow', beforeComboTipShow);
            }
            if (host.rendered) {
                onHostRender.call(host);
            } else {
                host.onRender = Ext.Function.createSequence(host.onRender, onHostRender);
            }
        }
    };
})());

if(typeof ExtTouch==="undefined"){ExtTouch={}}ExtTouch.apply=(function(){for(var key in {valueOf:1}){return function(object,config,defaults){if(defaults){ExtTouch.apply(object,defaults)}if(object&&config&&typeof config==="object"){for(var key in config){object[key]=config[key]}}return object}}return function(object,config,defaults){if(defaults){ExtTouch.apply(object,defaults)}if(object&&config&&typeof config==="object"){for(var key in config){object[key]=config[key]}if(config.toString!==Object.prototype.toString){object.toString=config.toString}if(config.valueOf!==Object.prototype.valueOf){object.valueOf=config.valueOf}}return object}})();ExtTouch.apply(ExtTouch,{platformVersion:"1.0",platformVersionDetail:{major:1,minor:0,patch:3},userAgent:navigator.userAgent.toLowerCase(),cache:{},idSeed:1000,BLANK_IMAGE_URL:"data:image/gif;base64,R0lGODlhAQABAID/AMDAwAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==",isStrict:document.compatMode=="CSS1Compat",windowId:"ExtTouch-window",documentId:"ExtTouch-document",emptyFn:function(){},isSecure:/^https/i.test(window.location.protocol),isReady:false,enableGarbageCollector:true,enableListenerCollection:true,applyIf:function(object,config){var property,undefined;if(object){for(property in config){if(object[property]===undefined){object[property]=config[property]}}}return object},repaint:function(){var mask=ExtTouch.getBody().createChild({cls:"x-mask x-mask-transparent"});setTimeout(function(){mask.remove()},0)},id:function(el,prefix){el=ExtTouch.getDom(el)||{};if(el===document){el.id=this.documentId}else{if(el===window){el.id=this.windowId}}el.id=el.id||((prefix||"ExtTouch-gen")+(++ExtTouch.idSeed));return el.id},ExtTouchend:function(){var inlineOverrides=function(o){for(var m in o){if(!o.hasOwnProperty(m)){continue}this[m]=o[m]}};var objectConstructor=Object.prototype.constructor;return function(subclass,superclass,overrides){if(ExtTouch.isObject(superclass)){overrides=superclass;superclass=subclass;subclass=overrides.constructor!=objectConstructor?overrides.constructor:function(){superclass.apply(this,arguments)}}if(!superclass){throw"Attempting to ExtTouchend from a class which has not been loaded on the page."}var F=function(){},subclassProto,superclassProto=superclass.prototype;F.prototype=superclassProto;subclassProto=subclass.prototype=new F();subclassProto.constructor=subclass;subclass.superclass=superclassProto;if(superclassProto.constructor==objectConstructor){superclassProto.constructor=superclass}subclass.override=function(overrides){ExtTouch.override(subclass,overrides)};subclassProto.superclass=subclassProto.supr=(function(){return superclassProto});subclassProto.override=inlineOverrides;subclassProto.proto=subclassProto;subclass.override(overrides);subclass.ExtTouchend=function(o){return ExtTouch.ExtTouchend(subclass,o)};return subclass}}(),override:function(origclass,overrides){ExtTouch.apply(origclass.prototype,overrides)},namespace:function(){var ln=arguments.length,i,value,split,x,xln,parts,object;for(i=0;i<ln;i++){value=arguments[i];parts=value.split(".");if(window.ExtTouch){object=window[parts[0]]=Object(window[parts[0]])}else{object=arguments.callee.caller.arguments[0]}for(x=1,xln=parts.length;x<xln;x++){object=object[parts[x]]=Object(object[parts[x]])}}return object},urlEncode:function(o,pre){var empty,buf=[],e=encodeURIComponent;ExtTouch.iterate(o,function(key,item){empty=ExtTouch.isEmpty(item);ExtTouch.each(empty?key:item,function(val){buf.push("&",e(key),"=",(!ExtTouch.isEmpty(val)&&(val!=key||!empty))?(ExtTouch.isDate(val)?ExtTouch.encode(val).replace(/"/g,""):e(val)):"")})});if(!pre){buf.shift();pre=""}return pre+buf.join("")},urlDecode:function(string,overwrite){if(ExtTouch.isEmpty(string)){return{}}var obj={},pairs=string.split("&"),d=decodeURIComponent,name,value;ExtTouch.each(pairs,function(pair){pair=pair.split("=");name=d(pair[0]);value=d(pair[1]);obj[name]=overwrite||!obj[name]?value:[].concat(obj[name]).concat(value)});return obj},htmlEncode:function(value){return ExtTouch.util.Format.htmlEncode(value)},htmlDecode:function(value){return ExtTouch.util.Format.htmlDecode(value)},urlAppend:function(url,s){if(!ExtTouch.isEmpty(s)){return url+(url.indexOf("?")===-1?"?":"&")+s}return url},toArray:function(array,start,end){return Array.prototype.slice.call(array,start||0,end||array.length)},each:function(array,fn,scope){if(ExtTouch.isEmpty(array,true)){return 0}if(!ExtTouch.isIterable(array)||ExtTouch.isPrimitive(array)){array=[array]}for(var i=0,len=array.length;i<len;i++){if(fn.call(scope||array[i],array[i],i,array)===false){return i}}return true},iterate:function(obj,fn,scope){if(ExtTouch.isEmpty(obj)){return}if(ExtTouch.isIterable(obj)){ExtTouch.each(obj,fn,scope);return}else{if(ExtTouch.isObject(obj)){for(var prop in obj){if(obj.hasOwnProperty(prop)){if(fn.call(scope||obj,prop,obj[prop],obj)===false){return}}}}}},pluck:function(arr,prop){var ret=[];ExtTouch.each(arr,function(v){ret.push(v[prop])});return ret},getBody:function(){return ExtTouch.get(document.body||false)},getHead:function(){var head;return function(){if(head==undefined){head=ExtTouch.get(DOC.getElementsByTagName("head")[0])}return head}}(),getDoc:function(){return ExtTouch.get(document)},getCmp:function(id){return ExtTouch.ComponentMgr.get(id)},getOrientation:function(){return window.innerHeight>window.innerWidth?"portrait":"landscape"},isIterable:function(v){if(!v){return false}if(ExtTouch.isArray(v)||v.callee){return true}if(/NodeList|HTMLCollection/.test(Object.prototype.toString.call(v))){return true}return((typeof v.nExtTouchNode!="undefined"||v.item)&&ExtTouch.isNumber(v.length))||false},num:function(v,defaultValue){v=Number(ExtTouch.isEmpty(v)||ExtTouch.isArray(v)||typeof v=="boolean"||(typeof v=="string"&&ExtTouch.util.Format.trim(v).length==0)?NaN:v);return isNaN(v)?defaultValue:v},isEmpty:function(value,allowBlank){var isNull=value==null,emptyArray=(ExtTouch.isArray(value)&&!value.length),blankAllowed=!allowBlank?value==="":false;return isNull||emptyArray||blankAllowed},isArray:function(v){return Object.prototype.toString.apply(v)==="[object Array]"},isDate:function(v){return Object.prototype.toString.apply(v)==="[object Date]"},isObject:function(v){return !!v&&!v.tagName&&Object.prototype.toString.call(v)==="[object Object]"},isPrimitive:function(v){return ExtTouch.isString(v)||ExtTouch.isNumber(v)||ExtTouch.isBoolean(v)},isFunction:function(v){return Object.prototype.toString.apply(v)==="[object Function]"},isNumber:function(v){return Object.prototype.toString.apply(v)==="[object Number]"&&isFinite(v)},isString:function(v){return typeof v==="string"},isBoolean:function(v){return Object.prototype.toString.apply(v)==="[object Boolean]"},isElement:function(v){return v?!!v.tagName:false},isDefined:function(v){return typeof v!=="undefined"},destroy:function(){var ln=arguments.length,i,arg;for(i=0;i<ln;i++){arg=arguments[i];if(arg){if(ExtTouch.isArray(arg)){this.destroy.apply(this,arg)}else{if(ExtTouch.isFunction(arg.destroy)){arg.destroy()}else{if(arg.dom){arg.remove()}}}}}}});ExtTouch.SSL_SECURE_URL=ExtTouch.isSecure&&"about:blank";ExtTouch.ns=ExtTouch.namespace;ExtTouch.ns("ExtTouch.util","ExtTouch.data","ExtTouch.list","ExtTouch.form","ExtTouch.menu","ExtTouch.state","ExtTouch.layout","ExtTouch.app","ExtTouch.ux","ExtTouch.plugins","ExtTouch.direct","ExtTouch.lib","ExtTouch.gesture");ExtTouch.onReady=function(){};ExtTouch.applyIf(Array.prototype,{indexOf:function(o,from){var len=this.length;from=from||0;from+=(from<0)?len:0;for(;from<len;++from){if(this[from]===o){return from}}return -1},remove:function(o){var index=this.indexOf(o);if(index!=-1){this.splice(index,1)}return this},contains:function(o){return this.indexOf(o)!==-1}});(function(){var El=ExtTouch.Element=ExtTouch.ExtTouchend(Object,{defaultUnit:"px",constructor:function(element,forceNew){var dom=typeof element=="string"?document.getElementById(element):element,id;if(!dom){return null}id=dom.id;if(!forceNew&&id&&ExtTouch.cache[id]){return ExtTouch.cache[id].el}this.dom=dom;this.id=id||ExtTouch.id(dom);return this},set:function(o,useSet){var el=this.dom,attr,value;for(attr in o){if(o.hasOwnProperty(attr)){value=o[attr];if(attr=="style"){this.applyStyles(value)}else{if(attr=="cls"){el.className=value}else{if(useSet!==false){el.setAttribute(attr,value)}else{el[attr]=value}}}}}return this},is:function(simpleSelector){return ExtTouch.DomQuery.is(this.dom,simpleSelector)},getValue:function(asNumber){var val=this.dom.value;return asNumber?parseInt(val,10):val},addListener:function(eventName,fn,scope,options){ExtTouch.EventManager.on(this.dom,eventName,fn,scope||this,options);return this},removeListener:function(eventName,fn,scope){ExtTouch.EventManager.un(this.dom,eventName,fn,scope);return this},removeAllListeners:function(){ExtTouch.EventManager.removeAll(this.dom);return this},purgeAllListeners:function(){ExtTouch.EventManager.purgeElement(this,true);return this},remove:function(){var me=this,dom=me.dom;if(dom){delete me.dom;ExtTouch.removeNode(dom)}},isAncestor:function(c){var p=this.dom;c=ExtTouch.getDom(c);if(p&&c){return p.contains(c)}return false},isDescendent:function(p){return ExtTouch.fly(p,"_internal").isAncestor(this)},contains:function(el){return !el?false:this.isAncestor(el)},getAttribute:function(name,ns){var d=this.dom;return d.getAttributeNS(ns,name)||d.getAttribute(ns+":"+name)||d.getAttribute(name)||d[name]},setHTML:function(html){if(this.dom){this.dom.innerHTML=html}return this},getHTML:function(){return this.dom?this.dom.innerHTML:""},hide:function(){this.setVisible(false);return this},show:function(){this.setVisible(true);return this},setVisible:function(visible,animate){var me=this,dom=me.dom,mode=this.getVisibilityMode();switch(mode){case El.VISIBILITY:this.removeCls(["x-hidden-display","x-hidden-offsets"]);this[visible?"removeCls":"addCls"]("x-hidden-visibility");break;case El.DISPLAY:this.removeCls(["x-hidden-visibility","x-hidden-offsets"]);this[visible?"removeCls":"addCls"]("x-hidden-display");break;case El.OFFSETS:this.removeCls(["x-hidden-visibility","x-hidden-display"]);this[visible?"removeCls":"addCls"]("x-hidden-offsets");break}return me},getVisibilityMode:function(){var dom=this.dom,mode=El.data(dom,"visibilityMode");if(mode===undefined){El.data(dom,"visibilityMode",mode=El.DISPLAY)}return mode},setVisibilityMode:function(mode){El.data(this.dom,"visibilityMode",mode);return this}});var Elp=El.prototype;El.VISIBILITY=1;El.DISPLAY=2;El.OFFSETS=3;El.addMethods=function(o){ExtTouch.apply(Elp,o)};Elp.on=Elp.addListener;Elp.un=Elp.removeListener;Elp.update=Elp.setHTML;El.get=function(el){var ExtTouchEl,dom,id;if(!el){return null}if(typeof el=="string"){if(!(dom=document.getElementById(el))){return null}if(ExtTouch.cache[el]&&ExtTouch.cache[el].el){ExtTouchEl=ExtTouch.cache[el].el;ExtTouchEl.dom=dom}else{ExtTouchEl=El.addToCache(new El(dom))}return ExtTouchEl}else{if(el.tagName){if(!(id=el.id)){id=ExtTouch.id(el)}if(ExtTouch.cache[id]&&ExtTouch.cache[id].el){ExtTouchEl=ExtTouch.cache[id].el;ExtTouchEl.dom=el}else{ExtTouchEl=El.addToCache(new El(el))}return ExtTouchEl}else{if(el instanceof El){if(el!=El.docEl){el.dom=document.getElementById(el.id)||el.dom}return el}else{if(el.isComposite){return el}else{if(ExtTouch.isArray(el)){return El.select(el)}else{if(el==document){if(!El.docEl){var F=function(){};F.prototype=Elp;El.docEl=new F();El.docEl.dom=document;El.docEl.id=ExtTouch.id(document)}return El.docEl}}}}}}return null};El.addToCache=function(el,id){id=id||el.id;ExtTouch.cache[id]={el:el,data:{},events:{}};return el};El.data=function(el,key,value){el=El.get(el);if(!el){return null}var c=ExtTouch.cache[el.id].data;if(arguments.length==2){return c[key]}else{return(c[key]=value)}};El.garbageCollect=function(){if(!ExtTouch.enableGarbageCollector){clearInterval(El.collectorThreadId)}else{var id,dom,EC=ExtTouch.cache;for(id in EC){if(!EC.hasOwnProperty(id)){continue}if(EC[id].skipGarbageCollection){continue}dom=EC[id].el.dom;if(!dom||!dom.parentNode||(!dom.offsetParent&&!document.getElementById(id))){if(ExtTouch.enableListenerCollection){ExtTouch.EventManager.removeAll(dom)}delete EC[id]}}}};El.Flyweight=function(dom){this.dom=dom};var F=function(){};F.prototype=Elp;El.Flyweight.prototype=new F;El.Flyweight.prototype.isFlyweight=true;El._flyweights={};El.fly=function(el,named){var ret=null;named=named||"_global";el=ExtTouch.getDom(el);if(el){(El._flyweights[named]=El._flyweights[named]||new El.Flyweight()).dom=el;ret=El._flyweights[named]}return ret};ExtTouch.get=El.get;ExtTouch.fly=El.fly})();(function(){ExtTouch.Element.classReCache={};var El=ExtTouch.Element,view=document.defaultView;El.addMethods({marginRightRe:/marginRight/i,trimRe:/^\s+|\s+$/g,spacesRe:/\s+/,getStyle:function(prop){},})})();ExtTouch.is={init:function(navigator){var me=this,platforms=me.platforms,ln=platforms.length,i,platform;navigator=navigator||window.navigator;for(i=0;i<ln;i++){platform=platforms[i];me[platform.identity]=platform.regex.test(navigator[platform.property])}me.Desktop=me.Mac||me.Windows||(me.Linux&&!me.Android);me.iOS=me.iPhone||me.iPad||me.iPod;me.Standalone=!!navigator.standalone;i=me.Android&&(/Android\s(\d+\.\d+)/.exec(navigator.userAgent));if(i){me.AndroidVersion=i[1];me.AndroidMajorVersion=parseInt(i[1],10)}me.Tablet=me.iPad||(me.Android&&me.AndroidMajorVersion===3);me.Phone=!me.Desktop&&!me.Tablet;me.MultiTouch=!me.Blackberry&&!me.Desktop&&!(me.Android&&me.AndroidVersion<3)},platforms:[{property:"platform",regex:/iPhone/i,identity:"iPhone"},{property:"platform",regex:/iPod/i,identity:"iPod"},{property:"userAgent",regex:/iPad/i,identity:"iPad"},{property:"userAgent",regex:/Blackberry/i,identity:"Blackberry"},{property:"userAgent",regex:/Android/i,identity:"Android"},{property:"platform",regex:/Mac/i,identity:"Mac"},{property:"platform",regex:/Win/i,identity:"Windows"},{property:"platform",regex:/Linux/i,identity:"Linux"}]};ExtTouch.is.init();ExtTouch.supports={init:function(){var doc=document,div=doc.createElement("div"),tests=this.tests,ln=tests.length,i,test;div.innerHTML=['<div style="height:30px;width:50px;">','<div style="height:20px;width:20px;"></div>',"</div>",'<div style="float:left; background-color:transparent;"></div>'].join("");doc.body.appendChild(div);for(i=0;i<ln;i++){test=tests[i];this[test.identity]=test.fn.call(this,doc,div)}doc.body.removeChild(div)},OrientationChange:((typeof window.orientation!="undefined")&&("onorientationchange" in window)),DeviceMotion:("ondevicemotion" in window),Touch:("ontouchstart" in window)&&(!ExtTouch.is.Desktop),tests:[{identity:"Transitions",fn:function(doc,div){var prefix=["webkit","Moz","o","ms","khtml"],TE="TransitionEnd",transitionEndName=[prefix[0]+TE,"transitionend",prefix[2]+TE,prefix[3]+TE,prefix[4]+TE],ln=prefix.length,i=0,out=false;div=ExtTouch.get(div);for(;i<ln;i++){if(div.getStyle(prefix[i]+"TransitionProperty")){ExtTouch.supports.CSS3Prefix=prefix[i];ExtTouch.supports.CSS3TransitionEnd=transitionEndName[i];out=true;break}}return out}},{identity:"RightMargin",fn:function(doc,div,view){view=doc.defaultView;return !(view&&view.getComputedStyle(div.firstChild.firstChild,null).marginRight!="0px")}},{identity:"TransparentColor",fn:function(doc,div,view){view=doc.defaultView;return !(view&&view.getComputedStyle(div.lastChild,null).backgroundColor!="transparent")}},{identity:"SVG",fn:function(doc){return !!doc.createElementNS&&!!doc.createElementNS("http://www.w3.org/2000/svg","svg").createSVGRect}},{identity:"Canvas",fn:function(doc){return !!doc.createElement("canvas").getContExtTouch}},{identity:"VML",fn:function(doc){var d=doc.createElement("div");d.innerHTML="<!--[if vml]><br><br><![endif]-->";return(d.childNodes.length==2)}},{identity:"Float",fn:function(doc,div){return !!div.lastChild.style.cssFloat}},{identity:"AudioTag",fn:function(doc){return !!doc.createElement("audio").canPlayType}},{identity:"History",fn:function(){return !!(window.history&&history.pushState)}},{identity:"CSS3DTransform",fn:function(){return(typeof WebKitCSSMatrix!="undefined"&&new WebKitCSSMatrix().hasOwnProperty("m41"))}},{identity:"CSS3LinearGradient",fn:function(doc,div){var property="background-image:",webkit="-webkit-gradient(linear, left top, right bottom, from(black), to(white))",w3c="linear-gradient(left top, black, white)",moz="-moz-"+w3c,options=[property+webkit,property+w3c,property+moz];div.style.cssTExtTouch=options.join(";");return(""+div.style.backgroundImage).indexOf("gradient")!==-1}},{identity:"CSS3BorderRadius",fn:function(doc,div){var domPrefixes=["borderRadius","BorderRadius","MozBorderRadius","WebkitBorderRadius","OBorderRadius","KhtmlBorderRadius"],pass=false,i;for(i=0;i<domPrefixes.length;i++){if(document.body.style[domPrefixes[i]]!==undefined){return pass=true}}return pass}},{identity:"GeoLocation",fn:function(){return(typeof navigator!="undefined"&&typeof navigator.geolocation!="undefined")||(typeof google!="undefined"&&typeof google.gears!="undefined")}}]};ExtTouch.apply(ExtTouch,{version:"1.1.1",versionDetail:{major:1,minor:1,patch:1},setup:function(config){if(config&&typeof config=="object"){if(config.addMetaTags!==false){this.addMetaTags(config)}if(ExtTouch.isFunction(config.onReady)){var me=this;ExtTouch.onReady(function(){var args=arguments;if(config.fullscreen!==false){ExtTouch.Viewport.init(function(){config.onReady.apply(me,args)})}else{config.onReady.apply(this,args)}},config.scope)}}},getDom:function(el){if(!el||!document){return null}return el.dom?el.dom:(typeof el=="string"?document.getElementById(el):el)},removeNode:function(node){if(node&&node.parentNode&&node.tagName!="BODY"){ExtTouch.EventManager.removeAll(node);node.parentNode.removeChild(node);delete ExtTouch.cache[node.id]}},addMetaTags:function(config){if(!ExtTouch.isObject(config)){return}var head=ExtTouch.get(document.getElementsByTagName("head")[0]),tag,precomposed;if(!ExtTouch.is.Desktop){tag=ExtTouch.get(document.createElement("meta"));tag.set({name:"viewport",content:"width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0;"});head.appendChild(tag)}if(ExtTouch.is.iOS){if(config.fullscreen!==false){tag=ExtTouch.get(document.createElement("meta"));tag.set({name:"apple-mobile-web-app-capable",content:"yes"});head.appendChild(tag);if(ExtTouch.isString(config.statusBarStyle)){tag=ExtTouch.get(document.createElement("meta"));tag.set({name:"apple-mobile-web-app-status-bar-style",content:config.statusBarStyle});head.appendChild(tag)}}if(config.tabletStartupScreen&&ExtTouch.is.iPad){tag=ExtTouch.get(document.createElement("link"));tag.set({rel:"apple-touch-startup-image",href:config.tabletStartupScreen});head.appendChild(tag)}if(config.phoneStartupScreen&&!ExtTouch.is.iPad){tag=ExtTouch.get(document.createElement("link"));tag.set({rel:"apple-touch-startup-image",href:config.phoneStartupScreen});head.appendChild(tag)}if(config.icon){config.phoneIcon=config.tabletIcon=config.icon}precomposed=(config.glossOnIcon===false)?"-precomposed":"";if(ExtTouch.is.iPad&&ExtTouch.isString(config.tabletIcon)){tag=ExtTouch.get(document.createElement("link"));tag.set({rel:"apple-touch-icon"+precomposed,href:config.tabletIcon});head.appendChild(tag)}else{if(!ExtTouch.is.iPad&&ExtTouch.isString(config.phoneIcon)){tag=ExtTouch.get(document.createElement("link"));tag.set({rel:"apple-touch-icon"+precomposed,href:config.phoneIcon});head.appendChild(tag)}}}}});(function(){var initExtTouch=function(){var bd=ExtTouch.getBody(),cls=[];if(!bd){return false}var Is=ExtTouch.is;if(Is.Phone){cls.push("x-phone")}else{if(Is.Tablet){cls.push("x-tablet")}else{if(Is.Desktop){cls.push("x-desktop")}}}if(Is.iPad){cls.push("x-ipad")}if(Is.iOS){cls.push("x-ios")}if(Is.Android){cls.push("x-android","x-android-"+Is.AndroidMajorVersion)}if(Is.Blackberry){cls.push("x-bb")}if(Is.Standalone){cls.push("x-standalone")}if(cls.length){bd.addCls(cls)}return true};if(!initExtTouch()){ExtTouch.onReady(initExtTouch)}})();ExtTouch.util.Observable=ExtTouch.ExtTouchend(Object,{isObservable:true,constructor:function(config){var me=this;ExtTouch.apply(me,config);if(me.listeners){me.on(me.listeners);delete me.listeners}me.events=me.events||{};if(this.bubbleEvents){this.enableBubble(this.bubbleEvents)}},eventOptionsRe:/^(?:scope|delay|buffer|single|stopEvent|preventDefault|stopPropagation|normalized|args|delegate|element|vertical|horizontal)$/,addManagedListener:function(item,ename,fn,scope,options){var me=this,managedListeners=me.managedListeners=me.managedListeners||[],config;if(ExtTouch.isObject(ename)){options=ename;for(ename in options){if(!options.hasOwnProperty(ename)){continue}config=options[ename];if(!me.eventOptionsRe.test(ename)){me.addManagedListener(item,ename,config.fn||config,config.scope||options.scope,config.fn?config:options)}}}else{managedListeners.push({item:item,ename:ename,fn:fn,scope:scope,options:options});item.on(ename,fn,scope,options)}},removeManagedListener:function(item,ename,fn,scope){var me=this,o,config,managedListeners,managedListener,length,i;if(ExtTouch.isObject(ename)){o=ename;for(ename in o){if(!o.hasOwnProperty(ename)){continue}config=o[ename];if(!me.eventOptionsRe.test(ename)){me.removeManagedListener(item,ename,config.fn||config,config.scope||o.scope)}}}managedListeners=this.managedListeners?this.managedListeners.slice():[];length=managedListeners.length;for(i=0;i<length;i++){managedListener=managedListeners[i];if(managedListener.item===item&&managedListener.ename===ename&&(!fn||managedListener.fn===fn)&&(!scope||managedListener.scope===scope)){this.managedListeners.remove(managedListener);item.un(managedListener.ename,managedListener.fn,managedListener.scope)}}},fireEvent:function(){var me=this,a=ExtTouch.toArray(arguments),ename=a[0].toLowerCase(),ret=true,ev=me.events[ename],queue=me.eventQueue,parent;if(me.eventsSuspended===true){if(queue){queue.push(a)}return false}else{if(ev&&ExtTouch.isObject(ev)&&ev.bubble){if(ev.fire.apply(ev,a.slice(1))===false){return false}parent=me.getBubbleTarget&&me.getBubbleTarget();if(parent&&parent.isObservable){if(!parent.events[ename]||!ExtTouch.isObject(parent.events[ename])||!parent.events[ename].bubble){parent.enableBubble(ename)}return parent.fireEvent.apply(parent,a)}}else{if(ev&&ExtTouch.isObject(ev)){a.shift();ret=ev.fire.apply(ev,a)}}}return ret},addListener:function(ename,fn,scope,o){var me=this,config,ev;if(ExtTouch.isObject(ename)){o=ename;for(ename in o){if(!o.hasOwnProperty(ename)){continue}config=o[ename];if(!me.eventOptionsRe.test(ename)){me.addListener(ename,config.fn||config,config.scope||o.scope,config.fn?config:o)}}}else{ename=ename.toLowerCase();me.events[ename]=me.events[ename]||true;ev=me.events[ename]||true;if(ExtTouch.isBoolean(ev)){me.events[ename]=ev=new ExtTouch.util.Event(me,ename)}ev.addListener(fn,scope,ExtTouch.isObject(o)?o:{})}},removeListener:function(ename,fn,scope){var me=this,config,ev;if(ExtTouch.isObject(ename)){var o=ename;for(ename in o){if(!o.hasOwnProperty(ename)){continue}config=o[ename];if(!me.eventOptionsRe.test(ename)){me.removeListener(ename,config.fn||config,config.scope||o.scope)}}}else{ename=ename.toLowerCase();ev=me.events[ename];if(ev.isEvent){ev.removeListener(fn,scope)}}},clearListeners:function(){var events=this.events,ev,key;for(key in events){if(!events.hasOwnProperty(key)){continue}ev=events[key];if(ev.isEvent){ev.clearListeners()}}this.clearManagedListeners()},purgeListeners:function(){console.warn("MixedCollection: purgeListeners has been deprecated. Please use clearListeners.");return this.clearListeners.apply(this,arguments)},clearManagedListeners:function(){var managedListeners=this.managedListeners||[],ln=managedListeners.length,i,managedListener;for(i=0;i<ln;i++){managedListener=managedListeners[i];managedListener.item.un(managedListener.ename,managedListener.fn,managedListener.scope)}this.managedListener=[]},purgeManagedListeners:function(){console.warn("MixedCollection: purgeManagedListeners has been deprecated. Please use clearManagedListeners.");return this.clearManagedListeners.apply(this,arguments)},addEvents:function(o){var me=this;me.events=me.events||{};if(ExtTouch.isString(o)){var a=arguments,i=a.length;while(i--){me.events[a[i]]=me.events[a[i]]||true}}else{ExtTouch.applyIf(me.events,o)}},hasListener:function(ename){var e=this.events[ename];return e.isEvent===true&&e.listeners.length>0},suspendEvents:function(queueSuspended){this.eventsSuspended=true;if(queueSuspended&&!this.eventQueue){this.eventQueue=[]}},resumeEvents:function(){var me=this,queued=me.eventQueue||[];me.eventsSuspended=false;delete me.eventQueue;ExtTouch.each(queued,function(e){me.fireEvent.apply(me,e)})},relayEvents:function(origin,events,prefix){prefix=prefix||"";var me=this,len=events.length,i,ename;function createHandler(ename){return function(){return me.fireEvent.apply(me,[prefix+ename].concat(Array.prototype.slice.call(arguments,0,-1)))}}for(i=0,len=events.length;i<len;i++){ename=events[i].substr(prefix.length);me.events[ename]=me.events[ename]||true;origin.on(ename,createHandler(ename),me)}},enableBubble:function(events){var me=this;if(!ExtTouch.isEmpty(events)){events=ExtTouch.isArray(events)?events:ExtTouch.toArray(arguments);ExtTouch.each(events,function(ename){ename=ename.toLowerCase();var ce=me.events[ename]||true;if(ExtTouch.isBoolean(ce)){ce=new ExtTouch.util.Event(me,ename);me.events[ename]=ce}ce.bubble=true})}}});ExtTouch.override(ExtTouch.util.Observable,{on:ExtTouch.util.Observable.prototype.addListener,un:ExtTouch.util.Observable.prototype.removeListener,mon:ExtTouch.util.Observable.prototype.addManagedListener,mun:ExtTouch.util.Observable.prototype.removeManagedListener});ExtTouch.util.Observable.releaseCapture=function(o){o.fireEvent=ExtTouch.util.Observable.prototype.fireEvent};ExtTouch.util.Observable.capture=function(o,fn,scope){o.fireEvent=ExtTouch.createInterceptor(o.fireEvent,fn,scope)};ExtTouch.util.Observable.observe=function(cls,listeners){if(cls){if(!cls.isObservable){ExtTouch.applyIf(cls,new ExtTouch.util.Observable());ExtTouch.util.Observable.capture(cls.prototype,cls.fireEvent,cls)}if(typeof listeners=="object"){cls.on(listeners)}return cls}};ExtTouch.util.Observable.observeClass=ExtTouch.util.Observable.observe;ExtTouch.util.Event=ExtTouch.ExtTouchend(Object,(function(){function createBuffered(handler,listener,o,scope){listener.task=new ExtTouch.util.DelayedTask();return function(){listener.task.delay(o.buffer,handler,scope,ExtTouch.toArray(arguments))}}function createDelayed(handler,listener,o,scope){return function(){var task=new ExtTouch.util.DelayedTask();if(!listener.tasks){listener.tasks=[]}listener.tasks.push(task);task.delay(o.delay||10,handler,scope,ExtTouch.toArray(arguments))}}function createSingle(handler,listener,o,scope){return function(){listener.ev.removeListener(listener.fn,scope);return handler.apply(scope,arguments)}}return{isEvent:true,constructor:function(observable,name){this.name=name;this.observable=observable;this.listeners=[]},addListener:function(fn,scope,options){var me=this,listener;scope=scope||me.observable;if(!me.isListening(fn,scope)){listener=me.createListener(fn,scope,options);if(me.firing){me.listeners=me.listeners.slice(0)}me.listeners.push(listener)}},createListener:function(fn,scope,o){o=o||{};scope=scope||this.observable;var listener={fn:fn,scope:scope,o:o,ev:this},handler=fn;if(o.delay){handler=createDelayed(handler,listener,o,scope)}if(o.buffer){handler=createBuffered(handler,listener,o,scope)}if(o.single){handler=createSingle(handler,listener,o,scope)}listener.fireFn=handler;return listener},findListener:function(fn,scope){var listeners=this.listeners,i=listeners.length,listener,s;while(i--){listener=listeners[i];if(listener){s=listener.scope;if(listener.fn==fn&&(s==scope||s==this.observable)){return i}}}return -1},isListening:function(fn,scope){return this.findListener(fn,scope)!==-1},removeListener:function(fn,scope){var me=this,index,listener,k;index=me.findListener(fn,scope);if(index!=-1){listener=me.listeners[index];if(me.firing){me.listeners=me.listeners.slice(0)}if(listener.task){listener.task.cancel();delete listener.task}k=listener.tasks&&listener.tasks.length;if(k){while(k--){listener.tasks[k].cancel()}delete listener.tasks}me.listeners.splice(index,1);return true}return false},clearListeners:function(){var listeners=this.listeners,i=listeners.length;while(i--){this.removeListener(listeners[i].fn,listeners[i].scope)}},fire:function(){var me=this,listeners=me.listeners,count=listeners.length,i,args,listener;if(count>0){me.firing=true;for(i=0;i<count;i++){listener=listeners[i];args=arguments.length?Array.prototype.slice.call(arguments,0):[];if(listener.o){args.push(listener.o)}if(listener&&listener.fireFn.apply(listener.scope||me.observable,args)===false){return(me.firing=false)}}}me.firing=false;return true}}})());ExtTouch.util.HashMap=ExtTouch.ExtTouchend(ExtTouch.util.Observable,{constructor:function(config){this.addEvents("add","clear","remove","replace");ExtTouch.util.HashMap.superclass.constructor.call(this,config);this.clear(true)},getCount:function(){return this.length},getData:function(key,value){if(value===undefined){value=key;key=this.getKey(value)}return[key,value]},getKey:function(o){return o.id},add:function(key,value){var me=this,data;if(me.containsKey(key)){throw new Error("This key already exists in the HashMap")}data=this.getData(key,value);key=data[0];value=data[1];me.map[key]=value;++me.length;me.fireEvent("add",me,key,value);return value},replace:function(key,value){var me=this,map=me.map,old;if(!me.containsKey(key)){me.add(key,value)}old=map[key];map[key]=value;me.fireEvent("replace",me,key,value,old);return value},remove:function(o){var key=this.findKey(o);if(key!==undefined){return this.removeByKey(key)}return false},removeByKey:function(key){var me=this,value;if(me.containsKey(key)){value=me.map[key];delete me.map[key];--me.length;me.fireEvent("remove",me,key,value);return true}return false},get:function(key){return this.map[key]},clear:function(initial){var me=this;me.map={};me.length=0;if(initial!==true){me.fireEvent("clear",me)}return me},containsKey:function(key){return this.map[key]!==undefined},contains:function(value){return this.containsKey(this.findKey(value))},getKeys:function(){return this.getArray(true)},getValues:function(){return this.getArray(false)},getArray:function(isKey){var arr=[],key,map=this.map;for(key in map){if(map.hasOwnProperty(key)){arr.push(isKey?key:map[key])}}return arr},each:function(fn,scope){var items=ExtTouch.apply({},this.map),key,length=this.length;scope=scope||this;for(key in items){if(items.hasOwnProperty(key)){if(fn.call(scope,key,items[key],length)===false){break}}}return this},clone:function(){var hash=new ExtTouch.util.HashMap(),map=this.map,key;hash.suspendEvents();for(key in map){if(map.hasOwnProperty(key)){hash.add(key,map[key])}}hash.resumeEvents();return hash},findKey:function(value){var key,map=this.map;for(key in map){if(map.hasOwnProperty(key)&&map[key]===value){return key}}return undefined}});ExtTouch.util.Functions={createInterceptor:function(origFn,newFn,scope,returnValue){var method=origFn;if(!ExtTouch.isFunction(newFn)){return origFn}else{return function(){var me=this,args=arguments;newFn.target=me;newFn.method=origFn;return(newFn.apply(scope||me||window,args)!==false)?origFn.apply(me||window,args):returnValue||null}}},createDelegate:function(fn,obj,args,appendArgs){if(!ExtTouch.isFunction(fn)){return fn}return function(){var callArgs=args||arguments;if(appendArgs===true){callArgs=Array.prototype.slice.call(arguments,0);callArgs=callArgs.concat(args)}else{if(ExtTouch.isNumber(appendArgs)){callArgs=Array.prototype.slice.call(arguments,0);var applyArgs=[appendArgs,0].concat(args);Array.prototype.splice.apply(callArgs,applyArgs)}}return fn.apply(obj||window,callArgs)}},defer:function(fn,millis,obj,args,appendArgs){fn=ExtTouch.util.Functions.createDelegate(fn,obj,args,appendArgs);if(millis>0){return setTimeout(fn,millis)}fn();return 0},createSequence:function(origFn,newFn,scope){if(!ExtTouch.isFunction(newFn)){return origFn}else{return function(){var retval=origFn.apply(this||window,arguments);newFn.apply(scope||this||window,arguments);return retval}}}};ExtTouch.defer=ExtTouch.util.Functions.defer;ExtTouch.createInterceptor=ExtTouch.util.Functions.createInterceptor;ExtTouch.createSequence=ExtTouch.util.Functions.createSequence;ExtTouch.createDelegate=ExtTouch.util.Functions.createDelegate;ExtTouch.util.Point=ExtTouch.ExtTouchend(Object,{constructor:function(x,y){this.x=(x!=null&&!isNaN(x))?x:0;this.y=(y!=null&&!isNaN(y))?y:0;return this},copy:function(){return new ExtTouch.util.Point(this.x,this.y)},copyFrom:function(p){this.x=p.x;this.y=p.y;return this},toString:function(){return"Point["+this.x+","+this.y+"]"},equals:function(p){return(this.x==p.x&&this.y==p.y)},isWithin:function(p,threshold){if(!ExtTouch.isObject(threshold)){threshold={x:threshold};threshold.y=threshold.x}return(this.x<=p.x+threshold.x&&this.x>=p.x-threshold.x&&this.y<=p.y+threshold.y&&this.y>=p.y-threshold.y)},translate:function(x,y){if(x!=null&&!isNaN(x)){this.x+=x}if(y!=null&&!isNaN(y)){this.y+=y}},roundedEquals:function(p){return(Math.round(this.x)==Math.round(p.x)&&Math.round(this.y)==Math.round(p.y))}});ExtTouch.util.Point.fromEvent=function(e){var a=(e.changedTouches&&e.changedTouches.length>0)?e.changedTouches[0]:e;return new ExtTouch.util.Point(a.pageX,a.pageY)};ExtTouch.AbstractManager=ExtTouch.ExtTouchend(Object,{typeName:"type",constructor:function(config){ExtTouch.apply(this,config||{});this.all=new ExtTouch.util.HashMap();this.types={}},get:function(id){return this.all.get(id)},register:function(item){this.all.add(item)},unregister:function(item){this.all.remove(item)},registerType:function(type,cls){this.types[type]=cls;cls[this.typeName]=type},isRegistered:function(type){return this.types[type]!==undefined},create:function(config,defaultType){var type=config[this.typeName]||config.type||defaultType,Constructor=this.types[type];if(Constructor==undefined){throw new Error(ExtTouch.util.Format.format("The '{0}' type has not been registered with this manager",type))}return new Constructor(config)},onAvailable:function(id,fn,scope){var all=this.all;all.on("add",function(index,o){if(o.id==id){fn.call(scope||o,o);all.un("add",fn,scope)}})},each:function(fn,scope){this.all.each(fn,scope||this)},getCount:function(){return this.all.getCount()}});ExtTouch.gesture.Manager=new ExtTouch.AbstractManager({eventNames:{start:"touchstart",move:"touchmove",end:"touchend"},clickMoveThreshold:5,init:function(){this.targets=[];this.followTouches=[];this.currentGestures=[];this.currentTargets=[];this.listenerWrappers={start:ExtTouch.createDelegate(this.onTouchStart,this),move:ExtTouch.createDelegate(this.onTouchMove,this),end:ExtTouch.createDelegate(this.onTouchEnd,this),};this.attachListeners()},freeze:function(){this.isFrozen=true},thaw:function(){this.isFrozen=false},getEventSimulator:function(){if(!this.eventSimulator){this.eventSimulator=new ExtTouch.util.EventSimulator()}return this.eventSimulator},attachListeners:function(){ExtTouch.iterate(this.eventNames,function(key,name){document.addEventListener(name,this.listenerWrappers[key],false)},this)},detachListeners:function(){ExtTouch.iterate(this.eventNames,function(key,name){document.removeEventListener(name,this.listenerWrappers[key],false)},this)},onTouchStart:function(e){var targets=[],target=e.target;if(e.stopped===true){return}if(ExtTouch.is.Android){if(!(target.tagName&&["input","tExtToucharea","select"].indexOf(target.tagName.toLowerCase())!==-1)){e.preventDefault()}}if(this.isFrozen){return}if(this.startEvent){this.onTouchEnd(e)}this.locks={};this.currentTargets=[target];while(target){if(this.targets.indexOf(target)!==-1){targets.unshift(target)}target=target.parentNode;this.currentTargets.push(target)}this.startEvent=e;this.startPoint=ExtTouch.util.Point.fromEvent(e);this.lastMovePoint=null;this.isClick=true;this.handleTargets(targets,e)},onTouchMove:function(e){if(ExtTouch.is.MultiTouch){e.preventDefault()}if(!this.startEvent){return}if(ExtTouch.is.Desktop){e.target=this.startEvent.target}if(this.isFrozen){return}var gestures=this.currentGestures,gesture,touch=e.changedTouches?e.changedTouches[0]:e;this.lastMovePoint=ExtTouch.util.Point.fromEvent(e);if(ExtTouch.supports.Touch&&this.isClick&&!this.lastMovePoint.isWithin(this.startPoint,this.clickMoveThreshold)){this.isClick=false}for(var i=0;i<gestures.length;i++){if(e.stopped){break}gesture=gestures[i];if(gesture.listenForMove){gesture.onTouchMove(e,touch)}}},onTouchEnd:function(e){if(ExtTouch.is.Blackberry){e.preventDefault()}if(this.isFrozen){return}var gestures=this.currentGestures.slice(0),ln=gestures.length,i,gesture,endPoint,needsAnotherMove=false,touch=e.changedTouches?e.changedTouches[0]:e;if(this.startPoint){endPoint=ExtTouch.util.Point.fromEvent(e);if(!(this.lastMovePoint||this.startPoint)["equals"](endPoint)){needsAnotherMove=true}}for(i=0;i<ln;i++){gesture=gestures[i];if(!e.stopped&&gesture.listenForEnd){if(needsAnotherMove){gesture.onTouchMove(e,touch)}gesture.onTouchEnd(e,touch)}this.stopGesture(gesture)}if(ExtTouch.supports.Touch&&this.isClick){this.isClick=false}this.lastMovePoint=null;this.followTouches=[];this.startedChangedTouch=false;this.currentTargets=[];this.startEvent=null;this.startPoint=null},handleTargets:function(targets,e){var ln=targets.length,i;this.startedChangedTouch=false;this.startedTouches=ExtTouch.supports.Touch?e.touches:[e];for(i=0;i<ln;i++){if(e.stopped){break}this.handleTarget(targets[i],e,true)}for(i=ln-1;i>=0;i--){if(e.stopped){break}this.handleTarget(targets[i],e,false)}if(this.startedChangedTouch){this.followTouches=this.followTouches.concat((ExtTouch.supports.Touch&&e.targetTouches)?ExtTouch.toArray(e.targetTouches):[e])}},handleTarget:function(target,e,capture){var gestures=ExtTouch.Element.data(target,"x-gestures")||[],ln=gestures.length,i,gesture;for(i=0;i<ln;i++){gesture=gestures[i];if((!!gesture.capture===!!capture)&&(this.followTouches.length<gesture.touches)&&((ExtTouch.supports.Touch&&e.targetTouches)?(e.targetTouches.length===gesture.touches):true)){this.startedChangedTouch=true;this.startGesture(gesture);if(gesture.listenForStart){gesture.onTouchStart(e,e.changedTouches?e.changedTouches[0]:e)}if(e.stopped){break}}}},startGesture:function(gesture){gesture.started=true;this.currentGestures.push(gesture)},stopGesture:function(gesture){gesture.started=false;this.currentGestures.remove(gesture)},addEventListener:function(target,eventName,listener,options){target=ExtTouch.getDom(target);options=options||{};var targets=this.targets,name=this.getGestureName(eventName),gestures=ExtTouch.Element.data(target,"x-gestures"),gesture;if(!gestures){gestures=[];ExtTouch.Element.data(target,"x-gestures",gestures)}if(!name){throw new Error("Trying to subscribe to unknown event "+eventName)}if(targets.indexOf(target)===-1){this.targets.push(target)}gesture=this.get(target.id+"-"+name);if(!gesture){gesture=this.create(ExtTouch.apply({},options,{target:target,type:name}));gestures.push(gesture)}gesture.addListener(eventName,listener);if(this.startedChangedTouch&&this.currentTargets.contains(target)&&!gesture.started&&!options.subsequent){this.startGesture(gesture);if(gesture.listenForStart){gesture.onTouchStart(this.startEvent,this.startedTouches[0])}}},removeEventListener:function(target,eventName,listener){target=ExtTouch.getDom(target);var name=this.getGestureName(eventName),gestures=ExtTouch.Element.data(target,"x-gestures")||[],gesture;gesture=this.get(target.id+"-"+name);if(gesture){gesture.removeListener(eventName,listener);for(name in gesture.listeners){return}gesture.destroy();gestures.remove(gesture);ExtTouch.Element.data(target,"x-gestures",gestures)}},getGestureName:function(ename){return this.names&&this.names[ename]},registerType:function(type,cls){var handles=cls.prototype.handles,i,ln;this.types[type]=cls;cls[this.typeName]=type;if(!handles){handles=cls.prototype.handles=[type]}this.names=this.names||{};for(i=0,ln=handles.length;i<ln;i++){this.names[handles[i]]=type}}});ExtTouch.regGesture=function(){return ExtTouch.gesture.Manager.registerType.apply(ExtTouch.gesture.Manager,arguments)};ExtTouch.TouchEventObjectImpl=ExtTouch.ExtTouchend(Object,{constructor:function(e,args){if(e){this.setEvent(e,args)}},setEvent:function(e,args){ExtTouch.apply(this,{event:e,time:e.timeStamp});this.touches=e.touches||[e];this.changedTouches=e.changedTouches||[e];this.targetTouches=e.targetTouches||[e];if(args){this.target=args.target;ExtTouch.apply(this,args)}else{this.target=e.target}return this},stopEvent:function(){this.stopPropagation();this.preventDefault()},stopPropagation:function(){this.event.stopped=true},preventDefault:function(){this.event.preventDefault()},getTarget:function(selector,maxDepth,returnEl){if(selector){return ExtTouch.fly(this.target).findParent(selector,maxDepth,returnEl)}else{return returnEl?ExtTouch.get(this.target):this.target}}});ExtTouch.TouchEventObject=new ExtTouch.TouchEventObjectImpl();ExtTouch.gesture.Gesture=ExtTouch.ExtTouchend(Object,{listenForStart:true,listenForEnd:true,listenForMove:true,disableLocking:false,touches:1,constructor:function(config){config=config||{};ExtTouch.apply(this,config);this.target=ExtTouch.getDom(this.target);this.listeners={};if(!this.target){throw new Error("Trying to bind a "+this.type+" event to element that does'nt exist: "+this.target)}this.id=this.target.id+"-"+this.type;ExtTouch.gesture.Gesture.superclass.constructor.call(this);ExtTouch.gesture.Manager.register(this)},addListener:function(name,listener){this.listeners[name]=this.listeners[name]||[];this.listeners[name].push(listener)},removeListener:function(name,listener){var listeners=this.listeners[name];if(listeners){listeners.remove(listener);if(listeners.length==0){delete this.listeners[name]}for(name in this.listeners){if(this.listeners.hasOwnProperty(name)){return}}this.listeners={}}},fire:function(type,e,args){var listeners=this.listeners&&this.listeners[type],ln=listeners&&listeners.length,i;if(!this.disableLocking&&this.isLocked(type)){return false}if(ln){args=ExtTouch.apply(args||{},{time:e.timeStamp,type:type,gesture:this,target:(e.target.nodeType==3)?e.target.parentNode:e.target});for(i=0;i<ln;i++){listeners[i](e,args)}}return true},stop:function(){ExtTouch.gesture.Manager.stopGesture(this)},lock:function(){if(!this.disableLocking){var args=arguments,ln=args.length,i;for(i=0;i<ln;i++){ExtTouch.gesture.Manager.locks[args[i]]=this.id}}},unlock:function(){if(!this.disableLocking){var args=arguments,ln=args.length,i;for(i=0;i<ln;i++){if(ExtTouch.gesture.Manager.locks[args[i]]==this.id){delete ExtTouch.gesture.Manager.locks[args[i]]}}}},isLocked:function(type){var lock=ExtTouch.gesture.Manager.locks[type];return !!(lock&&lock!==this.id)},getLockingGesture:function(type){var lock=ExtTouch.gesture.Manager.locks[type];if(lock){return ExtTouch.gesture.Manager.get(lock)||null}return null},onTouchStart:ExtTouch.emptyFn,onTouchMove:ExtTouch.emptyFn,onTouchEnd:ExtTouch.emptyFn,destroy:function(){this.stop();this.listeners=null;ExtTouch.gesture.Manager.unregister(this)}});ExtTouch.gesture.Touch=ExtTouch.ExtTouchend(ExtTouch.gesture.Gesture,{handles:["touchstart","touchmove","touchend","touchdown"],touchDownInterval:500,onTouchStart:function(e,touch){this.startX=this.previousX=touch.pageX;this.startY=this.previousY=touch.pageY;this.startTime=this.previousTime=e.timeStamp;this.fire("touchstart",e);this.lastEvent=e;if(this.listeners&&this.listeners.touchdown){this.touchDownIntervalId=setInterval(ExtTouch.createDelegate(this.touchDownHandler,this),this.touchDownInterval)}},onTouchMove:function(e,touch){this.fire("touchmove",e,this.getInfo(touch));this.lastEvent=e},onTouchEnd:function(e){this.fire("touchend",e,this.lastInfo);clearInterval(this.touchDownIntervalId)},touchDownHandler:function(){this.fire("touchdown",this.lastEvent,this.lastInfo)},getInfo:function(touch){var time=Date.now(),deltaX=touch.pageX-this.startX,deltaY=touch.pageY-this.startY,info={startX:this.startX,startY:this.startY,previousX:this.previousX,previousY:this.previousY,pageX:touch.pageX,pageY:touch.pageY,deltaX:deltaX,deltaY:deltaY,absDeltaX:Math.abs(deltaX),absDeltaY:Math.abs(deltaY),previousDeltaX:touch.pageX-this.previousX,previousDeltaY:touch.pageY-this.previousY,time:time,startTime:this.startTime,previousTime:this.previousTime,deltaTime:time-this.startTime,previousDeltaTime:time-this.previousTime};this.previousTime=info.time;this.previousX=info.pageX;this.previousY=info.pageY;this.lastInfo=info;return info}});ExtTouch.regGesture("touch",ExtTouch.gesture.Touch);ExtTouch.gesture.Swipe=ExtTouch.ExtTouchend(ExtTouch.gesture.Gesture,{listenForEnd:false,swipeThreshold:35,swipeTime:1000,onTouchStart:function(e,touch){this.startTime=e.timeStamp;this.startX=touch.pageX;this.startY=touch.pageY;this.lock("scroll","scrollstart","scrollend")},onTouchMove:function(e,touch){var deltaY=touch.pageY-this.startY,deltaX=touch.pageX-this.startX,absDeltaY=Math.abs(deltaY),absDeltaX=Math.abs(deltaX),deltaTime=e.timeStamp-this.startTime;if(absDeltaY-absDeltaX>3||deltaTime>this.swipeTime){this.unlock("drag","dragstart","dragend");this.stop()}else{if(absDeltaX>this.swipeThreshold&&absDeltaX>absDeltaY){this.fire("swipe",e,{direction:(deltaX<0)?"left":"right",distance:absDeltaX,deltaTime:deltaTime,deltaX:deltaX});this.stop()}}}});ExtTouch.regGesture("swipe",ExtTouch.gesture.Swipe);ExtTouch.gesture.Tap=ExtTouch.ExtTouchend(ExtTouch.gesture.Gesture,{handles:["tapstart","tapcancel","tap","doubletap","taphold","singletap"],cancelThreshold:10,doubleTapThreshold:800,singleTapThreshold:400,holdThreshold:1000,fireClickEvent:false,onTouchStart:function(e,touch){var me=this;me.startX=touch.pageX;me.startY=touch.pageY;me.fire("tapstart",e,me.getInfo(touch));if(this.listeners.taphold){me.timeout=setTimeout(function(){me.fire("taphold",e,me.getInfo(touch));delete me.timeout},me.holdThreshold)}me.lastTouch=touch},onTouchMove:function(e,touch){var me=this;if(me.isCancel(touch)){me.fire("tapcancel",e,me.getInfo(touch));if(me.timeout){clearTimeout(me.timeout);delete me.timeout}me.stop()}me.lastTouch=touch},onTouchEnd:function(e){var me=this,info=me.getInfo(me.lastTouch);this.fireTapEvent(e,info);if(me.lastTapTime&&e.timeStamp-me.lastTapTime<=me.doubleTapThreshold){me.lastTapTime=null;e.preventDefault();me.fire("doubletap",e,info)}else{me.lastTapTime=e.timeStamp}if(me.listeners&&me.listeners.singletap&&me.singleTapThreshold&&!me.preventSingleTap){me.fire("singletap",e,info);me.preventSingleTap=true;setTimeout(function(){me.preventSingleTap=false},me.singleTapThreshold)}if(me.timeout){clearTimeout(me.timeout);delete me.timeout}},fireTapEvent:function(e,info){this.fire("tap",e,info);if(e.event){e=e.event}var target=(e.changedTouches?e.changedTouches[0]:e).target;if(!target.disabled&&this.fireClickEvent){var clickEvent=document.createEvent("MouseEvent");clickEvent.initMouseEvent("click",e.bubbles,e.cancelable,document.defaultView,e.detail,e.screenX,e.screenY,e.clientX,e.clientY,e.ctrlKey,e.altKey,e.shiftKey,e.metaKey,e.metaKey,e.button,e.relatedTarget);clickEvent.isSimulated=true;target.dispatchEvent(clickEvent)}},getInfo:function(touch){var x=touch.pageX,y=touch.pageY;return{pageX:x,pageY:y,startX:x,startY:y}},isCancel:function(touch){var me=this;return(Math.abs(touch.pageX-me.startX)>=me.cancelThreshold||Math.abs(touch.pageY-me.startY)>=me.cancelThreshold)}});ExtTouch.regGesture("tap",ExtTouch.gesture.Tap);ExtTouch.gesture.Pinch=ExtTouch.ExtTouchend(ExtTouch.gesture.Gesture,{handles:["pinchstart","pinch","pinchend"],touches:2,onTouchStart:function(e){var me=this;if(this.isMultiTouch(e)){me.lock("swipe","scroll","scrollstart","scrollend","touchmove","touchend","touchstart","tap","tapstart","taphold","tapcancel","doubletap");me.pinching=true;var targetTouches=e.targetTouches;me.startFirstTouch=targetTouches[0];me.startSecondTouch=targetTouches[1];me.previousDistance=me.startDistance=me.getDistance(me.startFirstTouch,me.startSecondTouch);me.previousScale=1;me.fire("pinchstart",e,{distance:me.startDistance,scale:me.previousScale})}else{if(me.pinching){me.unlock("swipe","scroll","scrollstart","scrollend","touchmove","touchend","touchstart","tap","tapstart","taphold","tapcancel","doubletap");me.pinching=false}}},isMultiTouch:function(e){return e&&ExtTouch.supports.Touch&&e.targetTouches&&e.targetTouches.length>1},onTouchMove:function(e){if(!this.isMultiTouch(e)){this.onTouchEnd(e);return}if(this.pinching){this.fire("pinch",e,this.getPinchInfo(e))}},onTouchEnd:function(e){if(this.pinching){this.fire("pinchend",e)}},getPinchInfo:function(e){var me=this,targetTouches=e.targetTouches,firstTouch=targetTouches[0],secondTouch=targetTouches[1],distance=me.getDistance(firstTouch,secondTouch),scale=distance/me.startDistance,info={scale:scale,deltaScale:scale-1,previousScale:me.previousScale,previousDeltaScale:scale-me.previousScale,distance:distance,deltaDistance:distance-me.startDistance,startDistance:me.startDistance,previousDistance:me.previousDistance,previousDeltaDistance:distance-me.previousDistance,firstTouch:firstTouch,secondTouch:secondTouch,firstPageX:firstTouch.pageX,firstPageY:firstTouch.pageY,secondPageX:secondTouch.pageX,secondPageY:secondTouch.pageY,midPointX:(firstTouch.pageX+secondTouch.pageX)/2,midPointY:(firstTouch.pageY+secondTouch.pageY)/2};me.previousScale=scale;me.previousDistance=distance;return info},getDistance:function(firstTouch,secondTouch){return Math.sqrt(Math.pow(Math.abs(firstTouch.pageX-secondTouch.pageX),2)+Math.pow(Math.abs(firstTouch.pageY-secondTouch.pageY),2))}});ExtTouch.regGesture("pinch",ExtTouch.gesture.Pinch);
Ext.define('Bisque.Misc.GestureManager', {
    
	constructor : function() { 
	    if (typeof ExtTouch === 'undefined') return;
		ExtTouch.supports.init();
        ExtTouch.gesture.Manager.init();
	},
	
	addListener : function(listenerObj)	{
	    if (typeof ExtTouch === 'undefined') return;	    
		if (Ext.isArray(listenerObj)) {
			Ext.Array.forEach(listenerObj, this.addListener, this);
			return;
		}
		
		if (Ext.getDom(listenerObj.dom))
		    ExtTouch.gesture.Manager.addEventListener(listenerObj.dom, listenerObj.eventName, listenerObj.listener, listenerObj.options);
	},
	
});

Ext.Loader.setConfig({
    enabled: true
});
Ext.Loader.setPath('Ext.ux', bq.url('/js/Share'));

Ext.require([
    'Ext.ux.CheckColumn'
]);

Ext.define('BQ.ShareDialog', {
    
    extend : 'Ext.window.Window',

    constructor : function(config)
    {
        config          =   config || {};
        config.height   =   config.height || '65%';
        config.width    =   config.width || '65%';

        var bodySz      =   Ext.getBody().getViewSize();
        var height      =   parseInt((config.height.toString().indexOf("%") == -1) ? config.height : (bodySz.height * parseInt(config.height) / 100));
        var width       =   parseInt((config.width.toString().indexOf("%") == -1) ? config.width : (bodySz.width * parseInt(config.width) / 100));

        this.eastPanel  =   Ext.create('Ext.panel.Panel', {
            layout      :   {
                                type    :   'vbox',
                                align   :   'stretch'
                            },
            flex        :   4,
            title       :   'Add user',   
            region      :   'east',
            margin      :   '3 3 3 0',
            collapsible :   true,
            frame       :   true,
            split       :   true
        });
        
        this.centerPanel = Ext.create('Ext.panel.Panel', {
            region      :   'center',
            border      :   false,
            flex        :   6,
            margin      :   '3 1 3 3',
            layout      :   'fit',
        });

        Ext.apply(this,
        {
            title       :   'Sharing settings - ' + (config.resource ? config.resource.name : ''),
            modal       :   true,
            height      :   height,
            bodyStyle   :   'border:0px',
            width       :   width,
            layout      :   'border',
            bodyCls     :   'white',
            items       :   [this.centerPanel, this.eastPanel],
            owner       :   undefined,
            bbar :
            {
                xtype   :   'toolbar',
                style   :   {
                                background  :   '#FFF',
                                border      :   0
                            },
                layout:
                {
                    type:'hbox',
                    align:'middle',
                    pack: 'center'
                },
                defaults    :   {
                                    cls         :   'x-btn-default-medium',
                                    scale       :   'medium',
                                    style       :   'border-color:#D1D1D1',   
                                    width       :   85,
                                    margin      :   1,
                                    textAlign   :   'left',
                                    scope       :   this,
                                },
                padding :   '6 6 9 6',
                items   :
                [
                    {
                            text    :   'Save',
                            iconCls :   'icon-select24',
                            handler :   this.btnSave,
                            scope   :   this,
                    },
                    {
                            text    :   'Cancel',
                            iconCls :   'icon-cancel24',
                            handler :   this.btnCancel,
                    }
                ]
            }
                        
        }, config);
        
        this.callParent(arguments);
        
        this.addComponents();
        this.show();
    },
    
    btnSave : function()
    {
        var modified = false;

        for (var i=0;i<this.store.getCount();i++)
        {
            var currentRecord = this.store.getAt(i);
            if (currentRecord.dirty)
            {
                modified = true;
                currentRecord.commit();
                this.authRecord.children[i-1].action = (currentRecord.get('edit')) ? 'edit' : 'read';
            }
        }

        if (modified || this.userModified)
        {
            var notify = this.grid.getDockedItems('toolbar[dock="bottom"]')[0].getComponent('cbNotify').getValue();
            
            if (!notify)
                this.authRecord.uri = Ext.urlAppend(this.authRecord.uri, 'notify=false'); 
            
            this.authRecord.save_();
            BQ.ui.notification('Sharing settings saved!', 2500);
        }
            
        this.close();
    },

    btnCancel : function()
    {
        this.close();
    },
     
    userSelected : function(resourceBrowser, user)
    {
        var recordID = this.store.find('user_name', user.user_name);
        
        if (recordID==-1)
            this.addUser({
                user    :   user.uri,
                email   :   user.email,
                action  :   'read'
            });
        else
            BQ.ui.notification('Selected user already exists in the share list!');
    },
    
    addEmail : function()
    {
        this.addUser({
            email   :   this.txtEmail.getValue(),
            action  :   'read'
        });
        
        this.clearForm();
    },
    
    clearForm : function()
    {
        this.txtEmail.setValue('');
        this.txtEmail.focus();
    },
    
    addUser : function(record)
    {
        this.userModified = true;
        
        var authRecord = new BQAuth();
        Ext.apply(authRecord, record);
        this.authRecord.addchild(authRecord);
        
        this.reloadPermissions(this.authRecord);
    },
    
    reloadPermissions : function(authRecord)
    {
        if (!authRecord)
        {
            this.resource.getAuth(Ext.bind(this.reloadPermissions, this));
            return;
        }
        
        this.store.removeAll(true);
        this.authRecord = authRecord;
        authRecord = this.authRecord.children;
                    
        this.fetchUserInfo(this.resource.owner, 'owner', -1);
        
        for (var i=0; i<authRecord.length; i++)
        {
            if (authRecord[i].user)
                this.fetchUserInfo(authRecord[i].user, authRecord[i].action, i);
            else
                this.store.loadData([['', authRecord[i].email, authRecord[i].action, i, authRecord[i].user_name]], true);
        }
    },
    
    fetchUserInfo : function(uri, permission, sortOrder, user)
    {
        if (!user)
        {
            BQFactory.request({
                uri :   uri,
                cb  :   Ext.bind(this.fetchUserInfo, this, [uri, permission, sortOrder], 0)
            })
        }
        else
            this.store.loadData([[user.display_name, user.email, permission, sortOrder, user.user_name]], true);
    },
    
    addComponents : function()
    {
        
        this.browser = Ext.create('Bisque.ResourceBrowser.Browser',
        {
            showOrganizer   :   false,
            layout          :   Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Grid,
            layoutConfig    :   {
                                    colIconWidth    :   8,
                                    colValueText    :   'Email'
                                },
            flex            :   1,
            frame           :   true,
            region          :   'east',
            viewMode        :   'ViewSearch',
            wpublic         :   'true',
            dataset         :   '/data_service/user?view=full',
            listeners       :   {
                                    scope           :   this,
                                    'Select'        :   this.userSelected,
                                    'browserLoad'   :   Ext.Function.pass(this.reloadPermissions, [undefined], this)
                                }
        });
        
        var label = Ext.create('Ext.form.Label',
        {
            html    :   '<b>- or -</b>',
            margin  :   3,
            style   :   'color:#04408C;text-align:center'
        });
        
        this.form = Ext.create('Ext.form.Panel',
        {
            frame           :   true,
            height          :   110,
            title           :   'Invite a guest',
    
            fieldDefaults   :   {
                                    labelAlign: 'left',
                                    labelWidth: 90,
                                    anchor: '100%'
                                },
    
            items           :   [{
                                    xtype       :   'textfield',
                                    name        :   'email',
                                    fieldLabel  :   'Email address',
                                    vtype       :   'email',
                                    margin      :   '10 5 5 5'
                                }],
            buttonAlign     :   'center',
            buttons         :   {
                                    defaults    :   {
                                                        scope   :   this,
                                                        padding :   5
                                                    },
                                    items       :   [{
                                                        text    :   'Add guest',
                                                        handler :   this.addEmail
                                                    },
                                                    {
                                                        text    :   'Clear',
                                                        handler :   this.clearForm
                                                    }]
                                }
        });
        
        this.txtEmail = this.form.getComponent(0);
        
        this.grid = Ext.create('Ext.grid.Panel',
        {
            store       :   this.getStore(),
            frame       :   true,
            border      :   false,
            dockedItems :   [
                                {
                                    xtype   :   'toolbar',
                                    dock    :   'bottom',
                                    layout  :   {
                                                    type    :   'hbox',
                                                    pack    :   'center'
                                                },
                                    items   :   [{
                                                    xtype           :   'checkbox',
                                                    itemId          :   'cbNotify',
                                                    boxLabel        :   'Notify users.',
                                                    checked         :   true,
                                                    handler         :   Ext.emptyFn,   
                                                }]
                                }
                            ],
            columns     :   {
                                defaults : {
                                    minWidth : 20
                                },
                                items : [
                                {
                                    text: 'Name',
                                    flex: 3,
                                    sortable: false,
                                    dataIndex: 'name',
                                },
                                {
                                    text: 'Email address',
                                    flex: 4,
                                    sortable: false,
                                    align: 'center',
                                    dataIndex: 'value'
                                },
                                {
                                    text    :   'Permission',
                                    defaults:   {
                                                    align       :   'center',
                                                    sortable    :   false,
                                                    minWidth    :   25,
                                                    maxWidth    :   60,
                                                },
                                    columns :   [{
                                                    xtype       :   'checkcolumn',
                                                    text        :   'View',
                                                    dataIndex   :   'view',
                                                },
                                                {
                                                    xtype       :   'checkcolumn',
                                                    text        :   'Edit',
                                                    dataIndex   :   'edit',
                                                }],
                                    flex: 1,
                                    sortable: false,
                                    align: 'center',
                                }, 
                                {
                                    xtype: 'actioncolumn',
                                    itemId: 'colAction',
                                    maxWidth: 60,
                                    menuDisabled : true,
                                    sortable : false,
                                    align: 'center',
                                    items: [
                                    {
                                        icon : bq.url('../export_service/public/images/delete.png'),
                                        align : 'center',
                                        tooltip: 'Remove',
                                        handler: function(grid, rowIndex, colIndex)
                                        {
                                            // Cannot remove owner record
                                            if (rowIndex == 0)
                                            {
                                                BQ.ui.error('Cannot delete owner record!', 3000);
                                                return;
                                            }
    
                                            this.userModified = true;
                                            this.authRecord.children.splice(rowIndex-1, 1);
                                            grid.store.removeAt(rowIndex);
                                        },
                                        scope : this
                                    }]
                                }],
                            }
        });
        
        this.centerPanel.add(this.grid);
        this.eastPanel.add([this.browser, label, this.form]);
    },
    
    getStore : function()
    {
        this.store = Ext.create('Ext.data.ArrayStore', {
            fields: 
            [
                'name',
                'value',
                'permission',
                'viewPriority',
                'user_name',
                {
                    name : 'view',
                    type : 'bool',
                    convert : function(value, record){
                        return true;
                    }
                },
                {
                    name : 'edit',
                    type : 'bool',
                    convert : function(value, record){
                        if (Ext.isEmpty(value))
                            value = (record.data.permission=='edit' || record.data.permission=='owner') ? true : false
                        if (record.data.permission=='owner')
                            value = true;

                        return value;
                    },
                },
            ],
            sorters: 
            [{
                property : 'viewPriority',
                direction : 'ASC'
                
            }],
        });
        
        return this.store;
    }
});

Ext.define('BQ.ShareDialog.Offline', {
    
    extend : 'BQ.ShareDialog',
    
    constructor : function(config)
    {
        var resource = new BQResource();

        Ext.apply(resource,
        {
            owner   :   BQApp.user.uri,
            getAuth :   function(cb)
                        {
                            var resource = new BQResource();
                            cb(resource);
                        }
        });
        
        config.resource = resource;
        
        this.callParent([config]);
    },
    
    btnSave : function()
    {
        var modified = false;

        for (var i=0;i<this.store.getCount();i++)
        {
            var currentRecord = this.store.getAt(i);
            if (currentRecord.dirty)
            {
                modified = true;
                currentRecord.commit();
                this.authRecord.children[i-1].action = (currentRecord.get('edit')) ? 'edit' : 'read';
            }
        }
        
        var notify = this.grid.getDockedItems('toolbar[dock="bottom"]')[0].getComponent('cbNotify').getValue();
        
        if (modified || this.userModified)
            for (var i=0; i<this.resources.length; i++)
                this.resources[i].resource.getAuth(Ext.bind(this.addAuth, this, [notify], 1));
        
        this.close();
    },
    
    addAuth : function(authRecord, notify)
    {
        if (!notify)
            authRecord.uri = Ext.urlAppend(authRecord.uri, 'notify=false'); 
        
        for (var i=0; i<this.authRecord.children.length; i++)
            authRecord.addchild(this.authRecord.children[i]);
        
        authRecord.save_(undefined, this.success, this.failure);
    },
    
    success : function(resource, msg)
    {
        BQ.ui.notification(msg || 'Operation successful.');
    },
    
    failure : function(msg)
    {
        BQ.ui.error(msg || 'Operation failed!');
    },
});


/*
 @class BQ.form.ComboBox
 @extends Ext.form.field.ComboBox
  
 This is just a modification to function as a value box allowing initial values not present in the store
 
 Author: Dima Fedorov 
*/

Ext.define('BQ.form.ComboBox', {
    extend:'Ext.form.field.ComboBox',
    alias: ['widget.bqcombobox', 'widget.bqcombo'],
  
    setValue: function(value, doSelect) {
        this.valueNotFoundText = value;
        if (!this.rawValue)
            this.rawValue = value;
        return this.callParent(arguments);    
    },

});


/*
 @class BQ.grid.plugin.RowEditing
 @extends Ext.grid.plugin.RowEditing
  
 This is just a error fix for original Ext.grid.plugin.RowEditing
 
 Author: Dima Fedorov 
*/
Ext.define('BQ.grid.plugin.RowEditing', {
    extend: 'Ext.grid.plugin.RowEditing',
    alias: 'bq.rowediting',

    requires: [
        'Ext.grid.RowEditor'
    ],

    cancelEdit: function() {
        var me = this;
        me.callParent();
        
        var form = me.getEditor().getForm();
        if (!form.isValid())
            me.fireEvent('canceledit', me.grid, {});
    },

});

Ext.define('Bisque.ResourceTagger',
{
    extend : 'Ext.panel.Panel',

    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(this,
        {
            layout : 'fit',
            padding : '0 1 0 0',
            style : 'background-color:#FFF',
            border : false,

            rootProperty : config.rootProperty || 'tags',
            autoSave : (config.autoSave==undefined) ? true : false,
            resource : {},
            editable : true,
            tree : config.tree || {
                btnAdd : true,
                btnDelete : true,
                btnImport : true,
                //btnExport : true,
            },
            store : {},
            dirtyRecords : []
        });

        this.viewMgr = Ext.create('Bisque.ResourceTagger.viewStateManager', config.viewMode);
        this.populateComboStore();
        this.callParent([config]);
        
        this.setResource(config.resource);
    },
    
    populateComboStore : function()
    {
        // dima - datastore for the tag value combo box
        var TagValues = Ext.ModelManager.getModel('TagValues');
        if (!TagValues) {
            Ext.define('TagValues', {
                extend : 'Ext.data.Model',
                fields : [ {name: 'value', mapping: '@value' } ],
            });
        }
        
        this.store_values = Ext.create('Ext.data.Store', {
            model : 'TagValues', 
            autoLoad : true,
            autoSync : false,
            
            proxy: {
                noCache : false,
                type: 'ajax',
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                
                //url : '/data_service/image?tag_values=mytag',
                url: '/xml/dummy_tag_values.xml', // a dummy document just to inhibit initial complaining
                reader : {
                    type :  'xml',
                    root :  'resource',
                    record: 'tag', 
                },
            },
             
        });
        
        // dima - datastore for the tag name combo box
        var TagNames = Ext.ModelManager.getModel('TagNames');
        if (!TagNames) {
            Ext.define('TagNames', {
                extend : 'Ext.data.Model',
                fields : [ {name: 'name', mapping: '@name' } ],
            });
        }
        this.store_names = Ext.create('Ext.data.Store', {
            model : 'TagNames', 
            autoLoad : true,
            autoSync : false,
            
            proxy: {
                noCache : false,
                type: 'ajax',
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                
                url : '/data_service/image/?tag_names=1',
                reader : {
                    type :  'xml',
                    root :  'resource',
                    record: 'tag', 
                },
            },
        });
    },

    setResource : function(resource, template)
    {
        this.setLoading(true);
        
        if (resource instanceof BQObject)
            this.loadResourceInfo(resource);
        else
            // assume it is a resource URI otherwise
            BQFactory.request(
            {
                uri : resource,
                cb : Ext.bind(this.loadResourceInfo, this)
            });
    },

    loadResourceInfo : function(resource)
    {
        this.fireEvent('beforeload', this, resource);

        this.resource = resource;
        this.editable = false;
        if (!this.disableAuthTest)
            this.testAuth(BQApp.user, false);
        
        if(this.resource.tags.length > 0)
            this.loadResourceTags(this.resource.tags);
        else
            this.resource.loadTags(
            {
                cb: callback(this, "loadResourceTags"),
                depth: 'deep&wpublic=1'
            });
    },

    reload : function()
    {
        this.setResource(this.resource.uri);
    },

    loadResourceTags : function(data, template)
    {
        var type = this.resource.type || this.resource.resource_type;

        // Check to see if resource was derived from a template
        if (type.indexOf('data_service/template')!=-1 && !template && this.rootProperty != 'gobjects')
        {
            BQFactory.request({
                uri :   this.resource.type+'?view=deep',
                cb  :   Ext.bind(this.initCopy, this),
                errorcb : Ext.bind(this.loadResourceTags, this, [this.resource.tags, true])
            });
            
            return;
        }

        this.setLoading(false);

        var root = {};
        root[this.rootProperty] = data;
        
        this.removeAll(true);
        this.add(this.getTagTree(root));
        
        this.fireEvent('onload', this, this.resource);
        this.relayEvents(this.tree, ['itemclick']);
    },

    initCopy : function(template)
    {
        var resource = this.copyTemplate(template, this.resource);
        this.resource = resource;
        this.loadResourceTags(this.resource.tags, template);
    },
        
    copyTemplate : function(template, resource)
    {
        for(var i = 0; i < resource.tags.length; i++)
        {
            var matchingTag = template.findTags({attr:'uri', value: window.location.origin + resource.tags[i].type});
            
            if (!Ext.isEmpty(matchingTag))
            {
                matchingTag = (matchingTag instanceof Array)?matchingTag[0]:matchingTag;
                resource.tags[i].template = matchingTag.template;
                this.copyTemplate(matchingTag, resource.tags[i]);
            }
        }
        
        return resource;
    },

    getTagTree : function(data)
    {
        this.rowEditor = Ext.create('Bisque.ResourceTagger.Editor',
        {
            clicksToMoveEditor  :   1,
            tagger              :   this,
            errorSummary        :   false,

            listeners           :   {
                                        'edit'          :   this.finishEdit,
                                        'cancelEdit'    :   this.cancelEdit,
                                        scope           :   this
                                    },
            
            beforeEdit          :   function(editor)
                                    {
                                        if (this.tagger.editable && !isEmptyObject(editor.record.raw.template) && this.tagger.resource.resource_type!='template')
                                        {
                                            if (editor.record.raw.template.Editable)
                                            {
                                                try {
                                                    this.tagger.tree.columns[1].setEditor(BQ.TagRenderer.Base.getRenderer({tplType:editor.record.get('type'), tplInfo:editor.record.raw.template}));
                                                }
                                                catch(error)
                                                {
                                                    alert(error);
                                                }
                                                return true;
                                            }
                                            else
                                                return false;
                                        }
                                        
                                        if (this.tagger.editable)
                                        {
                                            this.tagger.updateQueryTagValues(editor.record.get('name'));
                                            this.tagger.tree.columns[1].setEditor(BQ.TagRenderer.Base.getRenderer({tplType:'', tplInfo:'', valueStore:this.tagger.store_values}));
                                        }

                                        return this.tagger.editable;
                                    }
        });
        
        this.tree = Ext.create('Ext.tree.Panel',
        {
            useArrows   :   true,
            rootVisible :   false,
            border      :   false,
            columnLines :   true,
            rowLines    :   true,
            lines       :   true,
            iconCls     :   'icon-grid',
            animate     :   this.animate,
            header      :   false,

            store       :   this.getTagStore(data),
            multiSelect :   true,
            tbar        :   this.getToolbar(),
            columns     :   this.getTreeColumns(),

            selModel    :   this.getSelModel(),
            plugins     :   (this.viewMgr.state.editable) ? [this.rowEditor] : null,
            viewConfig  :   {
                                plugins :   {
                                                ptype               :   'treeviewdragdrop',
                                                allowParentInserts  :   true,
                                            }
                            },
            listeners   :
            {
                'checkchange' : function(node, checked)
                {
                    //Recursively check/uncheck all children of a parent node
                    (checked) ? this.fireEvent('select', this, node) : this.fireEvent('deselect', this, node);
                    this.checkTree(node, checked);
                },
                scope :this
            }
        });

        this.store.tagTree = this.tree;

        return this.tree;
    },

    //Recursively check/uncheck all children of a parent node
    checkTree : function(node, checked)
    {
        node.set('checked', checked);

        for(var i=0;i<node.childNodes.length; i++)
            this.checkTree(node.childNodes[i], checked);
    },
    
    toggleTree : function(node)
    {
        node.set('checked', !node.get('checked'));

        for(var i=0;i<node.childNodes.length; i++)
            this.toggleTree(node.childNodes[i]);
    },

    getSelModel : function()
    {
        return null;
    },
    
    updateQueryTagValues: function(tag_name)
    {
        var proxy = this.store_values.getProxy();
        proxy.url = '/data_service/image?tag_values='+encodeURIComponent(tag_name);

        this.store_values.load();
    },

    getTreeColumns : function()
    {
        return [{
            xtype : 'treecolumn',
            dataIndex : 'name',
            text : this.colNameText || 'Name',
            flex : 0.8,
            sortable : true,
            field : {
                        // dima: combo box instead of the normal text edit that will be populated with existing tag names
                        xtype     : 'bqcombobox',
                        tabIndex: 0,  
                        
                        store     : this.store_names,
                        displayField: 'name',
                        valueField: 'name',
                        queryMode : 'local',
                                        
                        allowBlank: false,
                        //fieldLabel: this.colNameText || 'Name',
                        //labelAlign: 'top',    
        
                        validateOnChange: false,
                        blankText: 'Tag name is required!',
                        msgTarget : 'none',
                        listeners   :   {
                                            'change'    :   {
                                                                fn  :   function(field, newValue, oldValue, eOpts)
                                                                {
                                                                    this.updateQueryTagValues(newValue);
                                                                },
                                                                buffer: 250,
                                                            },
                           
                                            scope       :   this,
                                        },
                    }
            },
            {
                text        :   this.colValueText || 'Value',
                itemId      :   'colValue',
                dataIndex   :   'value',
                flex        :   1,
                sortable    :   true,
                editor      :   {
                                    allowBlank: false
                                },
                renderer    :   Bisque.ResourceTagger.BaseRenderer
            }
        ];
    },

    getTagStore : function(data)
    {
        this.store = Ext.create('Ext.data.TreeStore',
        {
            defaultRootProperty : this.rootProperty,
            root : data,

            fields : [
            {
                name : 'name',
                type : 'string',
                convert : function(value, record) {
                    // dima: show type and name for gobjects
                    if (record.raw instanceof BQGObject) {
                        var txt = [];
                        if (record.raw.type && record.raw.type != 'gobject') txt.push(record.raw.type);
                        if (record.raw.name) txt.push(record.raw.name);
                        if (txt.length>0) return txt.join(': ');
                    }
                    return value || record.data.type;
                }
            },
            {
                name : 'value',
                type : 'string'
            },
            {
                name : 'type',
                type : 'string'
            },
            {
                name : 'iconCls',
                type : 'string',
                convert : Ext.bind(function(value, record)
                {
                    if(record.raw)
                        if(record.raw[this.rootProperty].length != 0)
                            return 'icon-folder';
                    return 'icon-tag';
                }, this)

            },
            {
                name : 'qtip',
                type : 'string',
                convert : this.getTooltip
            }, this.getStoreFields()],

            indexOf : function(record)
            {
                return this.tagTree.getView().indexOf(record);
            },

            applyModifications : function()
            {
                var nodeHash = this.tree.nodeHash, status = false;

                for(var node in nodeHash)
                    if(nodeHash[node].dirty)
                    {
                        status = true;
                        Ext.apply(nodeHash[node].raw, {'name': nodeHash[node].get('name'), 'value': nodeHash[node].get('value')});
                        nodeHash[node].commit();
                    }

                if (this.getRemovedRecords().length>0)
                    return true;

                return status;
            },

            /* Modified function so as to not delete the root nodes */
            onNodeAdded : function(parent, node)
            {
                var me = this,
                    proxy = me.getProxy(),
                    reader = proxy.getReader(),
                    data = node.raw || node[node.persistenceProperty],
                    dataRoot;
        
                Ext.Array.remove(me.removed, node);
        
                if (!node.isLeaf()) {
                    dataRoot = reader.getRoot(data);
                    if (dataRoot) {
                        me.fillNode(node, reader.extractData(dataRoot));
                        //delete data[reader.root];
                    }
                }
        
                if (me.autoSync && !me.autoSyncSuspended && (node.phantom || node.dirty)) {
                    me.sync();
                }                
            }
        });

        return this.store;
    },
    
    getTooltip : function(value, record)
    {
        if (record.raw instanceof BQGObject)
        {
            var txt = [];
            if (record.raw.type && record.raw.type != 'gobject') txt.push(record.raw.type);
            if (record.raw.name) txt.push(record.raw.name);                        
            if (txt.length>0) return txt.join(' : ');
        }    
        
        return record.data.name + ' : ' + record.data.value;
    },

    getStoreFields : function()
    {
        return {name : 'dummy', type : 'string'};
    },

    getToolbar : function()
    {
        var tbar = [
        {
            xtype : 'buttongroup',
            itemId : 'grpAddDelete',
            hidden : (this.viewMgr.state.btnAdd && this.viewMgr.state.btnDelete),
            items : [
            {
                itemId : 'btnAdd', 
                text : 'Add',
                hidden : this.viewMgr.state.btnAdd,
                scale : 'small',
                iconCls : 'icon-add',
                handler : this.addTags,
                disabled : this.tree.btnAdd,
                scope : this
            },
            {
                itemId : 'btnDelete', 
                text : 'Delete',
                hidden : this.viewMgr.state.btnDelete,
                scale : 'small',
                iconCls : 'icon-delete',
                handler : this.deleteTags,
                disabled : this.tree.btnDelete,
                scope : this
            }]
        },
        {
            xtype : 'buttongroup',
            itemId : 'grpImportExport',
            hidden : (this.viewMgr.state.btnImport && this.viewMgr.state.btnExport),
            items : [
            {
                itemId : 'btnImport', 
                text : 'Import',
                hidden : this.viewMgr.state.btnImport,
                scale : 'small',
                iconCls : 'icon-import',
                handler : this.importMenu,
                disabled : this.tree.btnImport,
                scope : this
            },
            {
                text : 'Export',
                scale : 'small',
                hidden : this.viewMgr.state.btnExport,
                disabled : this.tree.btnExport,
                iconCls : 'icon-export',
                menu :
                {
                    items : [
                    {
                        text : 'as XML',
                        handler : this.exportToXml,
                        hidden : this.viewMgr.state.btnXML,
                        scope : this
                    },
                    {
                        text : 'as CSV',
                        handler : this.exportToCsv,
                        hidden : this.viewMgr.state.btnCSV,
                        scope : this
                    },
                    {
                        text : 'to Google Docs',
                        handler : this.exportToGDocs,
                        hidden : true,//this.viewMgr.state.btnGDocs,
                        scope : this
                    }]
                }
            }]
        },
        {
            xtype : 'buttongroup',
            hidden : (this.viewMgr.state.btnSave || this.autoSave),
            items : [
            {
                text : 'Save',
                hidden : this.viewMgr.state.btnSave || this.autoSave, 
                scale : 'small',
                iconCls : 'icon-save',
                handler : this.saveTags,
                scope : this
            }]
        }];

        return tbar;
    },
    
    addTags : function()
    {
        var currentItem = this.tree.getSelectionModel().getSelection();
        var editor = this.tree.plugins[0];

        if(currentItem.length)// None selected -> add tag to parent document
            currentItem = currentItem[0];
        else
            currentItem = this.tree.getRootNode();
        
        // Adding new tag to tree
        var child = { name : this.defaultTagName || '', value : this.defaultTagValue || '' };
        child[this.rootProperty] = [];

        var newNode = currentItem.appendChild(child);
        this.newNode = newNode;
        currentItem.expand();
        editor.startEdit(newNode, 0);
    },
    
    cancelEdit : function (grid, eOpts)
    {
        if (eOpts.record && eOpts.record.dirty)
        {
            eOpts.record.parentNode.removeChild(eOpts.record);
        }
    },    
    
    finishEdit : function(_editor, me)
    {
        if (me.record.raw instanceof BQObject)
        {
            if (this.autoSave)
            {
                this.saveTags(me.record.raw, true);
                me.record.data.qtip = this.getTooltip('', me.record);
                me.record.commit();
            }

            return;
        }
        
        this.editing = true;
        var newTag = new BQTag();
        newTag = Ext.apply(newTag,
        {
            name : me.record.data.name,
            value : me.record.data.value,
        });
        var parent = (me.record.parentNode.isRoot()) ? this.resource : me.record.parentNode.raw;
        parent.addtag(newTag);

        if (this.isValidURL(newTag.value))
        {
            newTag.type = 'link';
            me.record.data.type = 'link';
        }
            
        if (this.autoSave)
            this.saveTags(parent, true, newTag);

        me.record.raw = newTag;
        me.record.loaded = true;
        me.record.data.qtip = this.getTooltip('', me.record);
        me.record.commit();

        me.record.parentNode.data.iconCls = 'icon-folder';
        me.view.refresh();

        this.editing = false;
    },
    
    deleteTags : function()
    {
        var selectedItems = this.tree.getSelectionModel().getSelection(), parent;

        var cb = Ext.bind(function(){
            this.tree.setLoading(false);
        }, this);
        
        if(selectedItems.length)
        {
            this.tree.setLoading(true);
            
            for(var i = 0; i < selectedItems.length; i++)
            {
                parent = (selectedItems[i].parentNode.isRoot()) ? this.resource : selectedItems[i].parentNode.raw;
                parent.deleteTag(selectedItems[i].raw, cb, cb);

                if(selectedItems[i].parentNode.childNodes.length <= 1)
                    selectedItems[i].parentNode.data.iconCls = 'icon-tag';

                selectedItems[i].parentNode.removeChild(selectedItems[i], true);
            }

            BQ.ui.message('Resource tagger - Delete', selectedItems.length + ' record(s) deleted!');
            this.tree.getSelectionModel().deselectAll();
        }
    },

    saveTags : function(parent, silent)
    {
        var resource = (typeof parent == BQObject) ? parent  : this.resource;
        
        if(this.store.applyModifications())
        {
            resource.save_(undefined);
            if (!silent) BQ.ui.message('', 'Changes were saved successfully!');
        }
        else
            BQ.ui.message('', 'No records modified!');
    },
    
    importMenu : function(btn, e)
    {
        if (!btn.menu)
        {
            var menuItems = [];
            
            for (var i=0; i<BQApp.resourceTypes.length; i++)
            {
                menuItems.push({
                    text    :   'from <b>'+BQApp.resourceTypes[i].name+'</b>',
                    name    :   '/data_service/'+BQApp.resourceTypes[i].name,
                    handler :   this.importTags,
                    scope   :   this
                })
            }
            
            btn.menu = Ext.create('Ext.menu.Menu', {
                items   :   menuItems
            });
        }
        
        btn.showMenu();
    },
    
    importTags : function(menuItem)
    {
        var rb = new Bisque.ResourceBrowser.Dialog(
        {
            height      :   '85%',
            width       :   '85%',
            dataset     :   menuItem.name,
            viewMode    :   'ViewerLayouts',
            selType     :   'SINGLE',
            listeners   :
            {
                'Select' : function(me, resource)
                {
                    if (resource instanceof BQTemplate)
                    {
                        function applyTemplate(response)
                        {
                            if (response == 'yes')
                                BQ.TemplateManager.createResource({name: '', noSave:true}, Ext.bind(this.onResourceCreated, this), resource.uri+'?view=deep');
                        } 
                        
                        if (this.resource.type)
                            Ext.MessageBox.confirm('Reapply template', 'This resource is already templated. Do you wish to reapply selected template?', Ext.bind(applyTemplate, this));
                        else
                            applyTemplate.apply(this, ['yes']);
                    }
                    else
                        resource.loadTags(
                        {
                            cb : callback(this, "appendTags"),
                        });
                },

                scope : this
            },
        });
    },
    
    onResourceCreated : function(resource, template)
    {
        if (resource.type == this.resource.type)
            this.mergeTags(resource.tags);
        else
        {
            this.resource.type = resource.type;
            this.appendTags(resource.tags);
        }
        
        var resource = this.copyTemplate(template, this.resource);
        this.resource = resource;
    },
    
    mergeTags : function(data)
    {
        this.tree.setLoading(true);
        
        if (data.length>0)
        {
            var cleanData = this.stripURIs(data);

            for (var i=0;i<data.length; i++)
            {
                var matchingTag = this.resource.findTags({attr: 'type', value: data[i].type});
                
                if (Ext.isEmpty(matchingTag))
                {
                    this.resource.tags.push(cleanData[i]);
                    this.addNode(this.tree.getRootNode(), cleanData[i]);
                }
            }

            if (this.autoSave)
                this.saveTags(null, true);
        }
        
        this.tree.setLoading(false);
    },
    
    appendTags : function(data)
    {
        this.tree.setLoading(true);
        
        if (data.length>0)
        {
            data = this.stripURIs(data);
            var currentItem = this.tree.getSelectionModel().getSelection();

            if (currentItem.length)
            {
                currentItem = currentItem[0];
                currentItem.raw.tags = currentItem.raw.tags.concat(data)
            }
            else
            {
                currentItem = this.tree.getRootNode();
                this.resource.tags = this.resource.tags.concat(data);
            }

            this.addNode(currentItem, data);
            currentItem.expand();

            if (this.autoSave)
                this.saveTags(null, true);
        }

        this.tree.setLoading(false);
    },
    
    stripURIs : function(tagDocument)
    {
        var treeVisitor = Ext.create('Bisque.ResourceTagger.OwnershipStripper');
        treeVisitor.visit_array(tagDocument);
        return tagDocument;
    },
    
    updateNode : function(loaded, node, data)
    {
        if (!loaded)
            node.raw.loadTags(
            {
                cb: callback(this, "updateNode", true, node),
                depth: 'full'
            });
        else
            for(var i=0;i<data.length;i++)
                if (data[i].uri!=node.childNodes[i].raw.uri)
                    // Assuming resources come in order
                    alert('Tagger::updateNode - URIs not same!');
                else
                    this.addNode(node.childNodes[i], data[i][this.rootProperty]);
    },
    
    addNode : function(nodeInterface, children)
    {
        var newNode, i;
        
        if (!(children instanceof Array))
            children = [children];
        
        for (i=0;i<children.length;i++)
        {
            //debugger;
            newNode=Ext.ModelManager.create(children[i], this.store.model);
            Ext.data.NodeInterface.decorate(newNode);
            newNode.raw=children[i];
            nodeInterface.appendChild(newNode);

            nodeInterface.data.iconCls = 'icon-folder';
            this.tree.getView().refresh();
        }
    },
    
    testAuth : function(user, loaded, permission)
    {
        if (user)
        {
            if (!loaded)
                this.resource.testAuth(user.uri, Ext.bind(this.testAuth, this, [user, true], 0));            
            else
            {
                if (permission)
                {
                    // user is authorized to edit tags
                    this.tree.btnAdd = false;
                    this.tree.btnDelete = false;
                    this.tree.btnImport = false;
        
                    this.editable = true;
                    
                    if (this.tree instanceof Ext.Component)
                    {
                        var tbar = this.tree.getDockedItems('toolbar')[0];
                        
                        tbar.getComponent('grpAddDelete').getComponent('btnAdd').setDisabled(false);
                        tbar.getComponent('grpAddDelete').getComponent('btnDelete').setDisabled(false);
                        tbar.getComponent('grpImportExport').getComponent('btnImport').setDisabled(false);
                    }
                }
            }
        }
        else if (user===undefined)
        {
            // User autentication hasn't been done yet
            BQApp.on('gotuser', Ext.bind(this.testAuth, this, [false], 1));
        }
    },
    
    isValidURL : function(url)
    {
        var pattern = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/
        return pattern.test(url);        
    },

    exportToXml : function()
    {
        var url = '/export/initStream?urls='
        url += encodeURIComponent(this.resource.uri+'?view=deep');
        url += '&filename='+(this.resource.name || 'document');
        
        window.open(url);
    },

    exportToCsv : function()
    {
        var url = '/stats/csv?url=';
        url += encodeURIComponent(this.resource.uri);
        url += '&xpath=%2F%2Ftag&xmap=tag-name-string&xmap1=tag-value-string&xreduce=vector';
        url += '&title=Name&title1=Value';
        url += '&filename='+(this.resource.name || 'document') + '.csv';
        window.open(url);
    },

    exportToGDocs : function()
    {
        var url = '/export/to_gdocs?url=' + encodeURIComponent(this.resource.uri);
        window.open(url);
    },
});

Ext.define('Bisque.GObjectTagger',
{
    extend  :   'Bisque.ResourceTagger',
    animate :   false,

    constructor : function(config)
    {
        config.rootProperty = 'gobjects';
        config.colNameText = 'GObject';
        config.colValueText = 'Vertices';
        config.tree = {btnExport : true};

        this.callParent(arguments);
    },

    loadResourceInfo : function(resource)
    {
        this.fireEvent('beforeload', this, resource);
        
        this.resource = resource;
        this.resource.loadGObjects(
        {
            cb: callback(this, "loadResourceTags"),
            depth: 'deep&wpublic=1'
        });
    },

    getStoreFields : function()
    {
        return {
            name : 'checked',
            type : 'bool',
            defaultValue : true
        }
    },
    
    getToolbar : function()
    {
        var toolbar = this.callParent(arguments);
        
        var buttons =  
        [{
            xtype : 'buttongroup',
            items : [{
                xtype: 'splitbutton',
                arrowAlign: 'right',
                text : 'Toggle selection',
                scale : 'small',
                iconCls : 'icon-uncheck',
                handler : this.toggleCheckTree,
                checked : true,
                scope : this,
                menu:
                {
                    items: [{
                        check: true,
                        text: 'Check all',
                        handler: this.toggleCheck,
                        scope: this,
                    }, {
                        check: false,
                        text: 'Uncheck all',
                        handler: this.toggleCheck,
                        scope: this,
                    }]
                }
            }]
        }];
        
        return buttons.concat(toolbar);
    },
    
    toggleCheckTree : function(button)
    {
        var rootNode = this.tree.getRootNode(), eventName;
        button.checked = !button.checked;

        if (button.checked)
            button.setIconCls('icon-uncheck')
        else
            button.setIconCls('icon-check')

        for (var i=0;i<rootNode.childNodes.length;i++)
        {
            eventName=(!rootNode.childNodes[i].get('checked'))?'Select':'Deselect';
            this.fireEvent(eventName, this, rootNode.childNodes[i]);
        }

        this.toggleTree(rootNode);
    },
    
    toggleCheck : function(button)
    {
        button.checked = button.check;
        var rootNode = this.tree.getRootNode(), eventName=(button.checked)?'Select':'Deselect';
        
        for (var i=0;i<rootNode.childNodes.length;i++)
            this.fireEvent(eventName, this, rootNode.childNodes[i]);

        this.checkTree(rootNode, button.checked);
    },
    
    appendFromMex : function(resQo) {
        // dima: deep copy the resq array, otherwise messes up with analysis
        var resQ = [];
        for (var i=0; i<resQo.length; i++)
            resQ[i] = resQo[i];
        
        // Only look for gobjects in tags which have value = image_url 
        for (var i=0;i<resQ.length;i++)
        {
            // the mex may have sub mexs
            if (resQ[i].resource.children && resQ[i].resource.children.length>0) {
                for (var k=0; k<resQ[i].resource.children.length; k++)
                    if (resQ[i].resource instanceof BQMex) {
                        var rr = Ext.create('Bisque.Resource.Mex', { resource : resQ[i].resource.children[k], });
                        resQ.push(rr);
                    }
                continue;
            }
                
            var outputsTag = resQ[i].resource.find_tags('outputs');
            
            if (outputsTag)
                this.appendGObjects(this.findGObjects(outputsTag, this.resource.uri), resQ[i].resource);
            else
                resQ[i].resource.loadGObjects({cb: Ext.bind(this.appendGObjects, this, [resQ[i].resource], true)});    
        }
    },
    
    findGObjects : function(resource, imageURI)
    {
        if (resource.value && resource.value == imageURI)
            return resource.gobjects;
            
        var gobjects = null;
        var t = null;
        for (var i=0; (t=resource.tags[i]) && !gobjects; i++)
            gobjects = this.findGObjects(t, imageURI); 

        return gobjects;
    },
    
    deleteGObject : function(index)
    {
        var root = this.tree.getRootNode();
        var g = root.getChildAt(index);
        root.removeChild(g, true);
        this.tree.getView().refresh();
    },
    
    appendGObjects : function(data, mex)
    {
        if (data && data.length>0)
        {
            if (mex)
            {
                var date = new Date();
                date.setISO(mex.ts);
                
                this.addNode(this.tree.getRootNode(), {name:data[0].name, value:Ext.Date.format(date, "F j, Y g:i:s a"), gobjects:data});
                this.fireEvent('onappend', this, data);
            }
            else
            {
                this.addNode(this.tree.getRootNode(), data);
                //this.fireEvent('onappend', this, data);
            }
        }
    },

    exportToXml : function()
    {
        //var gobject=this.tree.getRootNode(), selection = this.tree.getChecked();
        //debugger
        //this.exportTo('xml');
    },
    
    //exportToGDocs : Ext.emptyFn,

    exportToCsv : function()
    {
        //this.exportTo('csv');
    },
    
    exportTo : function(format)
    {
        format = format || 'csv';
        
        var gobject, selection = this.tree.getChecked();
        this.noFiles = 0, this.csvData = '';
        
        function countGObjects(node, i)
        {
            if (node.raw)
                this.noFiles++;
        }
        
        selection.forEach(Ext.bind(countGObjects, this));
        
        for (var i=0;i<selection.length;i++)
        {
            gobject = selection[i].raw;

            if (gobject)
            {
                Ext.Ajax.request({
                    url : gobject.uri+'?view=deep&format='+format,
                    success : Ext.bind(this.saveCSV, this, [format], true),
                    disableCaching : false 
                });
            }
        }
    },
    
    saveCSV : function(data, params, format)
    {
        this.csvData += '\n'+data.responseText;
        this.noFiles--;
        
        if (!this.noFiles)
            location.href = "data:text/attachment," + encodeURIComponent(this.csvData);
    },
    
    updateViewState : function(state)
    {
        
    }
});

Ext.define('Bisque.ResourceTagger.Editor',
{
    extend : 'BQ.grid.plugin.RowEditing',

    completeEdit : function()
    {
        this.callParent(arguments);
        this.finishEdit();
    },
    
    cancelEdit : function()
    {
        this.callParent(arguments);
        this.finishEdit();
    },

    finishEdit : function()
    {
        if (this.context)
            this.context.grid.getSelectionModel().deselect(this.context.record);
    }

});

Ext.define('Bisque.ResourceTagger.OwnershipStripper', 
{
    extend : BQVisitor,
    
    visit : function(node, args)
    {
        Ext.apply(node, 
        {
            uri : undefined,
            ts : undefined,
            owner : undefined,
            perm : undefined,
            index : undefined 
        });
    }
});

Ext.define('Bisque.ResourceTagger.viewStateManager',
{
    constructor : function(mode)
    {
        //  ResourceTagger view-state
        this.state = 
        {
            btnAdd : true,
            btnDelete : true,
            
            btnToggleCheck : true,
            
            btnImport : true,
            btnExport : true,
            btnXML : true,
            btnCSV : true,
            btnGDocs : true,
        
            btnSave : true,
            editable : true,
        };
        
        function setHidden(obj, bool)
        {
            var result={};
            
            for (i in obj)
                result[i]=bool;
            
            return result;
        }
        
        switch(mode)
        {
            case 'ViewerOnly':
            {
                // all the buttons are hidden
                this.state = setHidden(this.state, true);
                this.state.editable = false;
                break;
            }
            case 'PreferenceTagger':
            {
                this.state.btnAdd = false;
                this.state.btnDelete = false;
                break;
            }
            case 'ReadOnly':
            {
                this.state.btnExport = false;
                this.state.btnXML = false;
                this.state.btnCSV = false;
                this.state.btnGDocs = false;
                this.state.editable = false;
                break;
            }
            case 'Offline':
            {
                this.state.btnAdd = false;
                this.state.btnDelete = false;
                this.state.btnImport = false;
                break;
            }
            case 'GObjectTagger':
            {
                // all the buttons are hidden except export
                this.state = setHidden(this.state, true);
                this.state.editable = false;
                
                this.state.btnExport = false;
                this.state.btnCSV = false;
                this.state.btnGDocs = false;
                this.state.btnXML = false;
                
                break;
            }
            default:
            {
                // default case: all buttons are visible (hidden='false')
                this.state = setHidden(this.state, false);
                this.state.editable = true;
            }
        }
        
    }
});
Ext.define('Bisque.ResourceTaggerOffline',
{
    extend : 'Bisque.ResourceTagger',
    
    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(config, 
        {
            viewMode    :   'Offline',
            tree        :   {
                                btnAdd : false,
                                btnDelete : false,
                                btnImport : false
                            }
        });
        
        this.callParent([config]);
    },
    
    setResource : function(resource)
    {
        this.resource = resource || new BQResource();
        this.loadResourceTags(this.resource.tags);
    },
    
    saveTags : function() {
        this.store.applyModifications();
    },
    
    getTagDocument : function() {
        return (this.resource && this.resource.tags) ? this.resource.tags : [];
    },
});



// Renderers are defined here for now
Bisque.ResourceTagger.LinkRenderer = function(value, metaData, record)
{
    return Ext.String.format('<a href={0} target="_blank">{1}</a>', value, value);
};

Bisque.ResourceTagger.ResourceRenderer = function(value, metaData, record)
{
    return Ext.String.format('<a href={0} target="_blank">{1}</a>', bq.url("/client_service/view?resource=" + value), value);
};

Bisque.ResourceTagger.EmailRenderer = function(value, metaData, record)
{
    return Ext.String.format('<a href={0} target="_blank">{1}</a>', 'mailto:'+value, value);
};

Bisque.ResourceTagger.VertexRenderer = function(value, metaData, record)
{
    var comboHtml = '<select>';
    var vertices = record.raw.vertices, vertex;

    for(var i = 0; i < vertices.length; i++)
    {
        vertex = vertices[i];
        comboHtml += '<option>';

        for(var j = 0; j < vertex.xmlfields.length; j++)
        if(vertex[vertex.xmlfields[j]] != null || vertex[vertex.xmlfields[j]] != undefined)
            comboHtml += vertex.xmlfields[j] + ':' + vertex[vertex.xmlfields[j]] + ', ';
        comboHtml += '</option>';
    }
    comboHtml += '</select>';

    return comboHtml
};

Bisque.ResourceTagger.RenderersAvailable =
{
    'file'          :   Bisque.ResourceTagger.LinkRenderer,
    'link'          :   Bisque.ResourceTagger.LinkRenderer,
    'hyperlink'     :   Bisque.ResourceTagger.LinkRenderer,
    'statistics'    :   Bisque.ResourceTagger.LinkRenderer,
    'resource'      :   Bisque.ResourceTagger.ResourceRenderer,
    'bisqueresource':   Bisque.ResourceTagger.ResourceRenderer,
    'image'         :   Bisque.ResourceTagger.ResourceRenderer,
    'email'         :   Bisque.ResourceTagger.EmailRenderer,

    // Gobject renderers
    'point'         :   Bisque.ResourceTagger.VertexRenderer,
    'polyline'      :   Bisque.ResourceTagger.VertexRenderer,
    'polygon'       :   Bisque.ResourceTagger.VertexRenderer,
    'rectangle'     :   Bisque.ResourceTagger.VertexRenderer,
    'square'        :   Bisque.ResourceTagger.VertexRenderer,
    'circle'        :   Bisque.ResourceTagger.VertexRenderer,
    'ellipse'       :   Bisque.ResourceTagger.VertexRenderer
};

Bisque.ResourceTagger.BaseRenderer = function(value, metaData, record)
{
    var renderer = Bisque.ResourceTagger.RenderersAvailable[record.data.type.toLowerCase()];

    if(renderer)
        return renderer.apply(this, arguments);
    else
        return Ext.String.htmlEncode(value);
};

Ext.define('BQ.Preferences.Object', {
    tag : {},
    dictionary : {tags:{}},
    status : undefined,
    exists : undefined,
    object : undefined
});

Ext.define('BQ.Preferences',
{
    singleton : true,
    queue : [],
    
    // load system preferences
    constructor : function()
    {
        this.system = Ext.create('BQ.Preferences.Object');
        this.user = Ext.create('BQ.Preferences.Object');
    
        this.loadSystem(undefined, 'INIT');
    },
    
    loadSystem : function(resource, status)
    {
        this.system.status=status;
        
        if (status=='INIT')
        {
            BQFactory.request(
            {
                uri : bq.url('/data_service/system?wpublic=1&view=deep'),
                cb : Ext.bind(this.loadSystem, this, ['LOADED'], true),
            });
        }
        else if (status=='LOADED')
        {
            resource = resource.children[0];
            this.system.object = resource;
            var tag = resource.find_tags('Preferences', false);
            
            if (tag!=null)
            {
                this.system.tag=tag;
                this.system.dictionary=tag.toNestedDict(true);
            }
            else
            {
                clog('SYSTEM preferences tag not found!\n');
                this.system.exists=false;
            }
        }
        
        this.clearQueue();
    },
    

    // bq_ui_application raises event loadUser 
    loadUser : function(resource, status)
    {
        this.user.status=status;

        // User is signed-in
        if (status=='INIT')
        {
            // Load the user object
            BQFactory.request(
            {
                uri : resource.uri + '?view=deep',
                cb : Ext.bind(this.loadUser, this, ['LOADED'], true)
            });
        }
        else if (status=='LOADED')
        {
            if (resource!=null)
            {
                this.user.object = resource;
                var tag = resource.find_tags('Preferences', false);

                if (tag!=null)
                {
                    this.user.tag=tag;
                    this.user.dictionary=tag.toNestedDict(true);
                }
                else
                {
                    clog('USER preferences tag not found!\n');
                    this.user.exists = true;
                    this.user.tag = resource;
                }
            }
            else
            {
                clog('USER - no user found!\n');
                this.user.exists=false;
            }
        }

        this.clearQueue();
    },
    
    clearQueue : function()
    {
        if (this.system.status=='LOADED' && this.user.status=='LOADED')
            while (this.queue.length!=0)
                this.get(this.queue.pop());
    },

    /*
     * Caller object: 
     * 
     * Caller.key = Component's key e.g. "ResourceBrowser"
     * Caller.type = 'user' or 'system'
     * Caller.callback = Component's callback function when the preferences are loaded
     */
    get : function(caller)
    {
        function fromDictionary(dict)
        {
            var obj = {};
            for (var tag in dict.tags)
                obj[dict.tags[tag].data.name] = fromDictionary(dict.tags[tag])
            return isEmptyObject(obj) ? ( isEmptyObject(dict) ? {} : ( Ext.isString(dict.data.value) ? dict.data.value.trim() : dict.data.value ) ) : obj;                
        }
        caller.type = caller.type || 'user';
        
        if (this.system.status=='LOADED' && this.user.status=='LOADED')
            if (caller.type=='user')
                caller.callback(fromDictionary(Ext.Object.merge(this.system.dictionary.tags[caller.key] || {}, this.user.dictionary.tags[caller.key] || {})));
            else    // return 'system' preferences by default 
                caller.callback(fromDictionary(this.system.dictionary.tags[caller.key] || {data:{value:''}}));
        else
            this.queue.push(caller);
    },
    
    getMerged : function()
    {
        var mergedPrefs = Ext.Object.merge(this.system.dictionary, this.user.dictionary);

        var prefs = new BQObject();
        prefs.name = 'Preferences';
        prefs.fromNestedDict(mergedPrefs);

        return prefs.tags;
    },
    
    reloadUser : function(user)
    {
        this.user = Ext.create('BQ.Preferences.Object');
        this.loadUser(user, 'INIT');
    },
    
    InitFromSystem : function(key)
    {
        var tag = this.stripOwnership([this.preference.systemTag.find_tags(key, false)]);
    },
    
    stripOwnership : function(tagDocument)
    {
        var treeVisitor = Ext.create('Bisque.ResourceTagger.OwnershipStripper');
        treeVisitor.visit_array(tagDocument);
        return tagDocument;
    }
})

Ext.define('BQ.Preferences.Dialog',
{
    extend : 'Ext.window.Window',
    
    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(this, 
        {
            title : 'Set preferences',
            modal : true,
            layout : 'fit',
            height : '70%',
            width : '70%',
            prefType : config.prefType || 'user'
        });
        
        if (this.prefType=='user')
            if (BQ.Preferences.user.status=='LOADED')
            {
                if (BQ.Preferences.user.exists==false)
                {
                    BQ.ui.notification('Guests cannot save preferences! Please login first...',  3000);
                    return;
                }
            }
            else
            {
                BQ.ui.notification('Initializing. Please wait...',  2000);
                return;
            }
                
        this.callParent(arguments);
        BQ.Preferences.reloadUser(BQSession.current_session.user);
        BQ.Preferences.get({key:'', type:'system', callback:Ext.bind(this.addTagger, this, [this.prefType])});

        this.show();
    },
    
    addTagger : function(prefType)
    {
        this.tagger = Ext.create('Bisque.PreferenceTagger',
        {
            viewMode : 'Offline',
            prefType : prefType
        });
    
        this.add(this.tagger);
    }
})

Ext.define('Bisque.PreferenceTagger',
{
    extend : 'Bisque.ResourceTagger',
    
    //autoSave : true,
    
    constructor : function(config)
    {
        config      =   config || {};
        
        config.viewMode =   'PreferenceTagger';
        config.autoSave =   true,
        config.tree     =   config.tree || {
                                btnAdd : false,
                                btnDelete : false,
                            },
        
        this.callParent([config]);
    },

    setResource : function(resource)
    {
        if (this.prefType=='user')
        {
            this.resource = resource || new BQResource();
            this.loadResourceTags(this.resource.tags);
            
            this.appendTags(BQ.Preferences.getMerged());
        }
        else
        {
            this.resource = BQ.Preferences.system.tag;
            this.loadResourceTags(this.resource.tags);
        }

        this.tree.expandAll();
    },
    
    saveTags : function(tag, silent, child)
    {
        if (tag)
            if(this.store.applyModifications())
            {
                if (this.prefType=='user')
                {
                    if (child) tag = child;
                    var parents = this.getTagParents(tag);
                    this.savePrefs(tag, parents); 
                    if (!silent) BQ.ui.message('Save', 'Changes were saved successfully!');
                }
                else
                {
                    this.resource.doc = this.resource;
                    this.resource.save_();
                }
            }
            else
                BQ.ui.message('Save', 'No records modified!');
    },
    
    savePrefs : function(changedTag, parents)
    {
        var root = BQ.Preferences.user.object;

        // Recursively find if the saved tag exist in user preferences or not
        // if not then add it otherwise continue with the search        
        for (var i=parents.length;i>=1;i--)
        {
            var current = parents[i-1];
            var tag = root.find_tags(current.name, false);
            
            root = (!tag)?root.addtag({name:current.name, value:current.value}):tag;
        }
        
        // if the user-changed tag exists already, modify the existing one
        if (root.uri)
        {
            root.name = changedTag.name;
            root.value = changedTag.value || '';
        }

        BQ.Preferences.user.tag.save_();
    },
    
    deleteTags : function()
    {
        var selectedItems = this.tree.getSelectionModel().getSelection(), parent;
        var root = BQ.Preferences.user.tag;
        
        BQ.Preferences.user.object.tags[0].delete_();

        var cb = Ext.bind(function(){
            this.tree.setLoading(false);
        }, this);
        
        if(selectedItems.length)
        {
            this.tree.setLoading(true);
            
            for(var i = 0; i < selectedItems.length; i++)
            {
                var tag = root.findTags({
                    attr    :   'name',
                    value   :   selectedItems[i].get('name'),
                    deep    :   true
                });
                
                if (!Ext.isEmpty(tag))
                    for (var j=0; j<tag.length; j++)
                        if (tag[j].value == selectedItems[i].get('value'))
                        {
                            parent = (selectedItems[i].parentNode.isRoot()) ? root : tag[j].parent;
                            parent.deleteTag(tag[j], cb, cb);

                            if(selectedItems[i].parentNode.childNodes.length <= 1)
                                selectedItems[i].parentNode.data.iconCls = 'icon-tag';
            
                            selectedItems[i].parentNode.removeChild(selectedItems[i], true);

                            break;
                        }
            }

            this.tree.setLoading(false);

            BQ.ui.message('Resource tagger - Delete', selectedItems.length + ' record(s) deleted!');
            this.tree.getSelectionModel().deselectAll();
        }
    },
    
    getTagParents : function(tag)
    {
        var parents = [];
        
        while (tag.parent)
        {
            parents.push(tag);
            tag = tag.parent;
        }
        
        parents.push(tag);
        
        return parents
    }
    
})

Ext.define('Bisque.DatasetBrowser.Dialog', 
{
	extend : 'Ext.window.Window',
	
    constructor : function(config)
    {
        var bodySz=Ext.getBody().getViewSize();
        var height=parseInt((config.height.indexOf("%")==-1)?config.height:(bodySz.height*parseInt(config.height)/100));
        var width=parseInt((config.width.indexOf("%")==-1)?config.width:(bodySz.width*parseInt(config.width)/100));

        Ext.apply(this,
        {
            layout : 'fit',
            title : config.title || 'Select a dataset...',
            modal : true,
            border : false,
            height : height,
            width : width,
            items : new Bisque.DatasetBrowser.Browser(config)
        }, config);

        this.callParent([arguments]);
        this.relayEvents(this.getComponent(0), ['DatasetDestroy']);
        
        this.on('DatasetDestroy', this.destroy, this);
        this.show();
    },
});

Ext.define('Bisque.DatasetBrowser.Browser', 
{
	extend : 'Bisque.ResourceBrowser.Browser',
	
    constructor : function(config)
    {
        Ext.apply(config,
        {
			viewMode: 'DatasetBrowser',
        });

		Ext.apply(this,
		{
			selectedDataset: null,
	      	bbar :
	        {
	        	xtype: 'toolbar',
				layout:
				{
					type:'hbox',
					align:'middle',
					pack: 'center'
				},
				padding: 12,
				items:
				[
	        		{
	        			xtype:'buttongroup',
	        			items:
		       			[{
		        			text: 'Select',
		        			iconCls : 'icon-select',
		        			scale: 'medium',
		        			textAlign: 'left',
		        			width: 75,
		        			handler: this.btnSelect,
		        			scope: this
	        			}]
	        		},
	        		{
	        			xtype:'buttongroup',
	        			items:
	        			[{
		        			text: 'Cancel',
		        			iconCls : 'icon-cancel',
		        			textAlign: 'left',
		        			scale: 'medium',
		        			width: 75,
		        			handler: this.btnCancel,
		        			scope: this
	        			}]
	        		}
	        	]
	        }
		});

		this.callParent(arguments);
		this.commandBar.btnDatasetClick();
		this.manageEvents();
    },
    
    manageEvents : function()
    {
		// Listen to Dataset Change
		this.msgBus.on(
		{
			'DatasetSelected' : function(dataset)
			{
				this.selectedDataset=dataset;
				if (this.ownerCt)
					this.ownerCt.setTitle('Viewing dataset : '+dataset.name);
			},
			'DatasetUnselected' : function()
			{
        		this.selectedDataset=null;
				if (this.ownerCt)
					this.ownerCt.setTitle('Select a dataset...');
        	},
        	scope: this
        });
    },
    
    btnSelect : function()
    {
    	if (this.selectedDataset)
    	{
    		this.fireEvent('DatasetSelect', this, this.selectedDataset);
    		this.fireEvent('DatasetDestroy');
    	}
    	else
    		alert('No dataset selected!');
    },
    
    btnCancel : function()
    {
    	this.fireEvent('DatasetDestroy');
    },
});

Ext.define('Bisque.TemplateTagger',
{
    extend : 'Bisque.ResourceTagger',
    
    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(config, 
        {
            tree            :   {
                                    btnAdd      :   false,
                                    btnDelete   :   false,
                                    btnImport   :   true,
                                    btnExport   :   true,
                                },
            importDataset   :   '/data_service/template',
        });

        this.tagRenderers = Ext.ClassManager.getNamesByExpression('BQ.TagRenderer.*'), this.tagTypes={};
        for (var i=0;i<this.tagRenderers.length;i++)
            if (Ext.ClassManager.get(this.tagRenderers[i]).componentName)
                this.tagTypes[Ext.ClassManager.get(this.tagRenderers[i]).componentName]=this.tagRenderers[i];
        
        this.callParent([config]);
    },
    
    setResource : function(resource)
    {
        this.resource = resource || new BQTemplate();
        this.loadResourceTags(this.resource.tags);
        this.testAuth(BQApp.user, false);
    },
    
    importMenu : function()
    {
        var rb = new Bisque.ResourceBrowser.Dialog(
        {
            height      :   '85%',
            width       :   '85%',
            dataset     :   this.importDataset,
            viewMode    :   'ViewerLayouts',
            selType     :   'SINGLE',
            listeners   :
            {
                'Select' : function(me, resource)
                {
                    resource.loadTags(
                    {
                        depth   :   'deep',   
                        cb      :   Ext.bind(this.appendTags, this),
                    });
                },

                scope : this
            },
        });
    },
    
    saveTags : function()
    {
        this.store.applyModifications();
    },

    updateQueryTagValues : Ext.emptyFn,
    
    // finish editing on a new record
    finishEdit : function(_editor, me)
    {
        this.callParent(arguments);
        
        var tag = me.record.raw;
        var template = tag.find_children('template');

        if ((me.newValues.value != me.originalValues.value) ||  Ext.isEmpty(template))
        {
                if (!Ext.isEmpty(template))
                    tag.remove_resource(template.uri);
                
                var newTemplate = Ext.ClassManager.get(this.tagTypes[me.record.get('value')]).getTemplate();
                tag.addchild(newTemplate);
        }
    },

    populateComboStore : function()
    {
        this.store_names = [];

        this.store_values = Ext.create('Ext.data.ArrayStore', {
            fields  :   [
                            'value'
                        ],
        });
        
        var tagTypes = Ext.Object.getKeys(this.tagTypes);
        Ext.Array.forEach(tagTypes, function(item, index, orgArray){
            orgArray[index] = [item];
        });
        
        this.store_values.loadData(tagTypes);
        this.defaultTagValue = this.store_values.getAt(0).get('value'); 
    },
    
    getTreeColumns : function()
    {
        return [
        {
            xtype       :   'treecolumn',
            text        :   'Field name',
            flex        :   1,
            dataIndex   :   'name',
            field       :   {
                                tabIndex    :   0,  
                                allowBlank  :   false,
                                blankText   :   'Field name is required!',
                            }
        },
        {
            text        :   'Type',
            flex        :   1,
            sortable    :   true,
            dataIndex   :   'value',
            renderer    :   Bisque.ResourceTagger.BaseRenderer,
            field       :   {
                                xtype           :   'combobox',
                                displayField    :   'value',
                                tabIndex        :   1,                
                                store           :   this.store_values,
                                editable        :   false,
                                queryMode       :   'local',
                            },
        }];
    },
});
Ext.define('BQ.TemplateManager', 
{
    statics : 
    {
        create : function(config) 
        {
            return Ext.create('BQ.TemplateManager.Creator', config);
        },
        
        // Create a blank resource from a template
        createResource : function(config, cb, template)
        {
            if (!(template instanceof BQTemplate))
            {
                BQFactory.request({
                    uri     :   template,
                    cb      :   Ext.pass(BQ.TemplateManager.createResource, [config, cb]),
                    cache   :   false,
                });
            }
            else
            {
                // Parse template URL #http://www.joezimjs.com/javascript/the-lazy-mans-url-parsing/
                var parser = document.createElement('a');
                parser.href = template.uri;
                
                // Assume the template is fully loaded
                var resource = new BQResource();
                
                Ext.apply(resource, {
                    resource_type   :   template.name,
                    type            :   parser.pathname,
                }, config)
                
                resource = copyTags.call(this, template, resource);
                
                if (config.noSave)
                    cb(resource, template);
                else
                    resource.save_('/data_service/' + resource.resource_type + '?view=deep', cb, function(msg) {BQ.ui.error('An error occured while trying to create a resource from template: ' + msg)});
            }

            function copyTags(template, resource)
            {
                var parser = document.createElement('a');
                
                for(var i = 0; i < template.tags.length; i++)
                {
                    var tag = template.tags[i];
                    parser.href = tag.uri;
                    copyTags.call(this, tag, resource.addtag({name:tag.name, value:tag.template["Default value"] || '', type: parser.pathname}));
                }
                return resource;
            }
        },
    }
});

Ext.define('BQ.TemplateManager.Creator', 
{
    extend      :   'Ext.panel.Panel',
    border      :   false,
    layout      :   'border',
    heading     :   'Create template',
    bodyCls     :   'white',
        
    constructor : function(config)
    {
        Ext.apply(this,
        {
            centerPanel :   Ext.create('Ext.panel.Panel', {
                                region      :   'center',
                                border      :   false,
                                flex        :   7,
                                title       :   'Editing resource template - ' + config.resource.name || '',
                                layout      :   'fit',
                            }),
                            
            eastPanel   :   Ext.create('Ext.panel.Panel', {
                                region      :   'east',
                                frame       :   true,
                                flex        :   3,
                                title       :   'Properties',
                                layout      :   'fit',
                                collapsible :   true,
                                split       :   true
                            })            
        });
        
        Ext.apply(this,
        {
            items   :   [this.centerPanel, this.eastPanel],
        });
        
        this.callParent(arguments);
    },
    
    initComponent : function()
    {
        this.callParent(arguments);

        this.tagger = Ext.create('Bisque.TemplateTagger',
        {
            resource        :   this.resource,
            listeners       :   {
                                    'itemclick' :   this.onFieldSelect,
                                    scope       :   this
                                },
        });
        
        this.grid = Ext.create('Ext.grid.property.Grid',
        {
            source          :   {},
            listeners       :   {
                                    'edit'          :   this.onPropertyEdit,
                                    scope           :   this
                                },
            customEditors   :   {
                                    'Display values'    :   {
                                                                xtype       :   'textareafield',
                                                                emptyText   :   'Enter comma separated display values e.g. Alabama, Alaska'
                                                            },
                                    'Passed values'     :   {
                                                                xtype       :   'textareafield',
                                                                emptyText   :   'Enter comma separated passed values e.g. AL, AK (defaults to display values)'
                                                            },
                                    'Resource type'     :   {
                                                                xtype       :   'combo',
                                                                store       :   Ext.create('Ext.data.Store', {
                                                                                    fields  :   ['name', 'uri'],
                                                                                    data    :   BQApp.resourceTypes,   
                                                                                }),
                                                                queryMode   :   'local',       
                                                                displayField:   'name',
                                                                editable    :   false
                                                            }
                                }
        });
        
        this.centerPanel.add(this.tagger);
        this.eastPanel.add(this.grid);
    },
    
    saveTemplate : function()
    {
        function success(resource)
        {
            BQ.ui.notification('Changes saved!', 2000);
            this.tagger.setResource(resource);
        }
        
        this.resource.uri = this.resource.uri + '?view=deep';
        this.resource.save_(undefined, Ext.bind(success, this), Ext.pass(BQ.ui.error, ['Save failed!']));
    },
    
    onFieldSelect : function(tree, record)
    {
        this.currentField = record.raw;
        this.currentTemplate = this.currentField.find_children('template');
        this.eastPanel.setTitle('Properties - ' + this.currentField.name);
        this.grid.setSource(BQ.TagRenderer.Base.convertTemplate(this.currentTemplate));
    },
    
    onPropertyEdit : function(editor, record)
    {
        var tagName = record.record.get('name');
        var tag = this.currentTemplate.find_tags(tagName);
        
        if (tag)
            tag.value = record.value.toString();
    }
});
Ext.define('BQ.TagRenderer.Base', 
{
    
    alias               :   'BQ.TagRenderer.Base',
    inheritableStatics  :   {
                                baseClass       :   'BQ.TagRenderer',
                                template        :   {
                                                        'Type'          :   'Base',
                                                        'Default value' :   '',
                                                        'Allow blank'   :   false,
                                                        'Editable'      :   true,
                                                    },

                                /// getRenderer     :   Returns a tag renderer for a given tag type and template information
                                /// inputs -
                                /// config.tplType  :   Type of template (String, Number etc.)
                                /// config.tplInfo  :   Template information    (minValue, maxValue etc.)
                                getRenderer     :   function(config)
                                {
                                    var tplType = config.tplInfo.Type;
                                    var className = BQ.TagRenderer.Base.baseClass + '.' + tplType;
            
                                    if (Ext.ClassManager.get(className))
                                        return Ext.create(className).getRenderer(config);
                                    else
                                    {
                                        Ext.log({
                                            msg     :   Ext.String.format('TagRenderer: Unknown class: {0}, type: {1}. Initializing with default tag renderer.', className, tplType),
                                            level   :   'warn',
                                            stack   :   true
                                        });
                                        return Ext.create(BQ.TagRenderer.Base.baseClass + '.' + 'String').getRenderer(config);
                                    }
                                },
                                
                                getTemplate     :   function()
                                {
                                    var componentTemplate = Ext.clone(this.template || {});
                                    var baseTemplate = Ext.clone(Ext.ClassManager.get('BQ.TagRenderer.Base').template);
                                    return this.convertTemplate(Ext.Object.merge(baseTemplate, componentTemplate));
                                },
                                
                                convertTemplate :   function(template)
                                {
                                    if (template instanceof BQTemplate)
                                    {
                                        var templateObj = {}, template = template.tags;
                                        for (var i=0;i<template.length;i++)
                                            templateObj[template[i].name] = this.parseVariable(template[i]);  
                                        return templateObj;
                                    }
                                    else if (template instanceof Object)
                                    {
                                        var templateRes = new BQTemplate(), newTag;
                                        for (var i in template)
                                            templateRes.addtag({
                                                name    :   i,
                                                value   :   template[i].toString(),
                                                type    :   typeof template[i]
                                            });
                                        templateRes.resource_type = 'template';
                                        return templateRes;
                                    }
                                },
                                
                                parseVariable : function(tag)
                                {
                                    var value;
                                    tag.value = Ext.isEmpty(tag.value)?'':tag.value;
                                    
                                    switch (tag.type)
                                    {
                                        case 'number':
                                            value = parseFloat(tag.value);
                                            break;
                                        case 'boolean':
                                            value = Ext.isBoolean(tag.value) ? tag.value : (tag.value.toLowerCase() === "true");   
                                            break;
                                        default:
                                            value = tag.value;
                                    }
                                    
                                    return value;
                                },
                            },
});

Ext.define('BQ.TagRenderer.String',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.String',
    inheritableStatics  :   {
                                componentName   :   'String',
                                template        :   {
                                                        'Type'                  :   'String',
                                                        'minLength'             :   1,  
                                                        'maxLength'             :   200,
                                                        'RegEx'                 :   ''
                                                    }                    
                        },
                        
    getRenderer         :   function(config)
                            {
                                var valueStore = config.valueStore;
                                
                                if (!valueStore)
                                {
                                    if (!Ext.ModelManager.getModel('TagValues'))
                                    {
                                        Ext.define('TagValues',
                                        {
                                            extend  :   'Ext.data.Model',
                                            fields  :   [ {name: 'value', mapping: '@value' } ],
                                        });
                                    }
            
                                    var valueStore = Ext.create('Ext.data.Store',
                                    {
                                        model       :   'TagValues', 
                                        autoLoad    :   true,
                                        autoSync    :   false,

                                        proxy       :   {
                                                            noCache     :   false,
                                                            type        :   'ajax',
                                                            limitParam  :   undefined,
                                                            pageParam   :   undefined,
                                                            startParam  :   undefined,
                                                            url         :   '/xml/dummy_tag_values.xml',
                                                            reader      :   {
                                                                                type    :   'xml',
                                                                                root    :   'resource',
                                                                                record  :   'tag', 
                                                                            },
                                                        },
                                    });
                                }
                                    
                                return  {
                                            xtype       :   'combobox',
                                            store       :   valueStore,
                                            
                                            displayField:   'value',
                                            valueField  :   'value',
                                            queryMode   :   'local',
                                            typeAhead   :   true,

                                            minLength   :   config.tplInfo.minLength || BQ.TagRenderer.String.template.minLength,
                                            maxLength   :   config.tplInfo.maxLength || BQ.TagRenderer.String.template.maxLength,
                                            regex       :   RegExp(config.tplInfo.RegEx || ''),
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Number', 
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Number',
    inheritableStatics  :   {
                                componentName   :   'Number',
                                template        :   {
                                                        'Type'                  :   'Number',
                                                        'minValue'              :   0,  
                                                        'maxValue'              :   100,
                                                        'allowDecimals'         :   true,
                                                        'decimalPrecision'      :   2,
                                                    }                    
                            },
                               
    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype               :   'numberfield',
                                            
                                            minValue            :   config.tplInfo.minValue || BQ.TagRenderer.Number.template.minValue,
                                            maxValue            :   config.tplInfo.maxValue || BQ.TagRenderer.Number.template.maxValue,
                                            allowDecimals       :   config.tplInfo.allowDecimals || BQ.TagRenderer.Number.template.allowDecimals,
                                            decimalPrecision    :   config.tplInfo.decimalPrecision || BQ.TagRenderer.Number.template.decimalPrecision,
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Boolean',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Boolean',
    inheritableStatics  :   {
                                componentName   :   'Boolean',
                                template        :   {
                                                        'Type'  :   'Boolean'
                                                    }
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype           :   'checkbox',
                                            boxLabel        :   ' (checked = True, unchecked = False)',
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Date',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Date',
    inheritableStatics  :   {
                                componentName   :   'Date',
                                template        :   {
                                                        'Type'      :   'Date',
                                                        'format'    :   'm/d/Y',
                                                    }                    
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'datefield',
                                            format      :   config.tplInfo.format || BQ.TagRenderer.Date.template.format,
                                            getValue    :   function()
                                            {
                                                return this.getRawValue();
                                            }
                                        }
                            }
});

Ext.define('BQ.TagRenderer.ComboBox',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.ComboBox',
    inheritableStatics  :   {
                                componentName   :   'ComboBox',
                                template        :   {
                                                        'Type'              :   'ComboBox',
                                                        'Display values'    :   '',
                                                        'Passed values'     :   ''
                                                    }                    
                        },
                        
    getRenderer         :   function(config)
                            {
                                var values = config.tplInfo['Display values'] || '', passedValues = '';
                                values = values.split(',');
                                
                                if (config.tplInfo['Passed values'])
                                    passedValues = config.tplInfo['Passed values'].split(',');
                                else
                                    passedValues = values;

                                // prepare data to be compatible with store
                                for (var i=0, data=[]; i<values.length; i++)
                                    data.push({'name':values[i], 'value':passedValues[i]});  
                                
                                var store = Ext.create('Ext.data.Store',
                                {
                                    fields  :   ['name', 'value'],
                                    data    :   data
                                });
                                
                                return  {
                                            xtype           :   'combobox',
                                            store           :   store,
                                            displayField    :   'name',
                                            valueField      :   'value',
                                            editable        :   false,
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Hyperlink',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Hyperlink',
    inheritableStatics  :   {
                                componentName   :   'Hyperlink',
                                template        :   {
                                                        'Type'  :   'Hyperlink'
                                                    }
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'textfield',
                                            vtype       :   'url'
                                        }
                            }
});

Ext.define('BQ.TagRenderer.BisqueResource',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.BisqueResource',
    inheritableStatics  :   {
                                componentName   :   'BisqueResource',
                                template        :   {
                                                        'Type'          :   'BisqueResource',
                                                        'Resource type' :   'image',
                                                    }                    
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'BisqueResourcePicker',
                                            dataset     :   config.tplInfo['Resource type'] || BQ.TagRenderer.BisqueResource.template['Resource type'],
                                            editable    :   false,
                                        }
                            }
});

Ext.define('Bisque.Resource.Picker',
{
    extend      :   'Ext.form.field.Picker',
    xtype       :   'BisqueResourcePicker',
    triggerCls  :   Ext.baseCSSPrefix + 'form-date-trigger',
    
    createPicker: function()
    {
        var rb = new Bisque.ResourceBrowser.Dialog(
        {
            height      :   '85%',
            width       :   '85%',
            viewMode    :   'ViewerLayouts',
            selType     :   'SINGLE',
            dataset     :   '/data_service/' + this.dataset,
            listeners   :
            {
                'Select' : function(me, resource)
                {
                    this.setValue(resource.uri);
                },

                scope : this
            },
        });
    },
});


Ext.define('BQ.TagRenderer.Email',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Email',
    inheritableStatics  :   {
                                componentName   :   'Email',
                                template        :   {
                                                        'Type'  :   'Email'
                                                    }
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'textfield',
                                            vtype       :   'email'
                                        }
                            }
});



Ext.define('BQ.Export.Panel',
{
    extend : 'Ext.panel.Panel',
    
    constructor : function()
    {
        Ext.apply(this, {
            heading : 'Download Images',
            layout : 'fit',
        });
        
        this.callParent(arguments);
    },
    
    initComponent : function()
    {
        this.dockedItems = [
        {
            xtype : 'toolbar',
            dock : 'top',
            items : [
            {
                xtype: 'tbtext',
                padding: 10,
                html: '<h2>'+this.heading+':</h2>'
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    xtype: 'splitbutton',
                    arrowAlign: 'right',
                    text: 'Add Images',
                    scale: 'large',
                    width: 140,
                    padding : 3,
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-select-images',
                    resourceType: 'image',
                    handler: this.selectImage,
                    scope: this,
                    menu:
                    {
                        items: [{
                            resourceType: 'file',
                            text: 'Add Files',
                            handler: this.selectImage,
                            scope: this,
                        }]
                    }
                }
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    text: 'Add Dataset',
                    scale: 'large',
                    padding : 3,
                    width: 140,
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-select-dataset',
                    handler: this.selectDataset,
                    scope: this
                }
            }]
        },
        {
            xtype : 'toolbar',
            dock : 'bottom',
            items : [
            {
                xtype : 'tbspacer',
                width : 10,
                padding : 10
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    xtype: 'splitbutton',
                    text: 'Download',
                    scale: 'large',
                    padding : 3,
                    width: 160,
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-download',
                    arrowAlign: 'right',
                    menuAlign: 'bl-tl?',
                    compressionType: 'tar',

                    handler: this.download,
                    scope: this,

                    menu        :   {
                                        defaults    :   {
                                                            xtype       :   'menucheckitem',
                                                            group       :   'downloadGroup',
                                                            groupCls    :   Ext.baseCSSClass + 'menu-group-icon',
                                                            checked     :   false,
                                                            scope       :   this,
                                                            handler     :   this.download,
                                                        },
                                        items       :   [{
                                                            compressionType :   'tar',
                                                            text            :   'as TARball',
                                                            checked         :   true,
                                                        },{
                                                            compressionType :   'gzip',
                                                            text            :   'as GZip archive',
                                                        },{
                                                            compressionType :   'bz2',
                                                            text            :   'as BZip2 archive',
                                                        },{
                                                            compressionType :   'zip',
                                                            text            :   'as (PK)Zip archive',
                                                        }]
                                    }
                }
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    text: 'Export to Google Docs',
                    disabled : true,
                    scale: 'large',
                    padding : 3,
                    width: 160,
                    textAlign: 'left',
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-gdocs'
                }
            }]
        }]
        
        this.callParent(arguments);
        this.add(this.getResourceGrid())
    },
    
    downloadResource : function(resource, compression)
    {
        if (!(resource instanceof Array))
            resource = [resource]

        for (var i=0, type, record=[]; i<resource.length; i++)
        {
            type = resource[i].resource_type;

            if (type!='dataset' || compression=='none') 
                type = 'file';

            record.push(['', '',  type, resource[i].ts, '', resource[i].uri, 0]);
        }
        
        this.resourceStore.loadData(record);
        this.download({compressionType:compression});
    },
    
    download : function(btn)
    {
        if (!this.resourceStore.count())
        {
            BQ.ui.message('Download failed', 'Nothing to download! Please add files or datasets first...');
            return;
        }
       
        function findAllbyType(type)
        {
            var index=0, list=[];
            
            while((index = this.resourceStore.find('type', type, index))!=-1)
            {
                // add quotes to make it work in Safari
                list.push(this.resourceStore.getAt(index).get('uri'));
                index++;
            }

            return list;
        }
        
        Ext.create('Ext.form.Panel',
        {
            url : '/export/initStream',
            defaultType: 'hiddenfield',
            method : 'GET',
            standardSubmit: true,
            items : [
            {
                name : 'compressionType',
                value : btn.compressionType 
            },
            {
                name : 'files',
                value : findAllbyType.call(this, 'image').concat(findAllbyType.call(this, 'file'))
            },
            {
                name : 'datasets',
                value : findAllbyType.call(this, 'dataset')
            }]
        }).submit();
    },
    
    exportResponse : function(response)
    {
    },

    selectImage : function(me)
    {
        var rbDialog = Ext.create('Bisque.ResourceBrowser.Dialog', {
            'height'    : '85%',
            'width'     : '85%',
            dataset     : '/data_service/' + me.resourceType,
            wpublic     : 'true',
            listeners   : 
            {
                'Select': this.addToStore,
                scope: this
            }
        });
    },
        
    selectDataset : function()
    {
        var rbDialog = Ext.create('Bisque.DatasetBrowser.Dialog', {
            'height': '85%',
            'width':  '85%',
            wpublic: 'true',
            listeners : 
            {
                'DatasetSelect' : this.addToStore,
                scope: this
            }
        });
    },

    addToStore : function(rb, resource)
    {
        if (resource instanceof Array)
        {
            for (var i=0;i<resource.length;i++)
                this.addToStore(rb, resource[i]);
            return;
        }

        var record = [], thumbnail, viewPriority;
        
        if (resource.resource_type=='image')
        {
            thumbnail = resource.src;
            viewPriority = 1;
        }
        else if (resource.resource_type=='dataset')
        {
            thumbnail = bq.url('../export_service/public/images/folder.png');
            viewPriority = 0;
        }
        else if (resource.resource_type=='file')
        {
            thumbnail = bq.url('../export_service/public/images/file.png');
            viewPriority = 2;
        }
        
        record.push(thumbnail, resource.name || '', resource.resource_type, resource.ts, resource.permission || '', resource.uri, viewPriority);
        this.resourceStore.loadData([record], true);
    },
    
    getResourceGrid : function()
    {
        this.resourceGrid = Ext.create('Ext.grid.Panel', {
            store : this.getResourceStore(),
            border : 0,
            listeners : 
            {
                scope: this,
                'itemdblclick' : function(view, record, item, index)
                {
                    // delegate resource viewing to ResourceView Dispatcher
                    var newTab = window.open('', "_blank");
                    newTab.location = bq.url('/client_service/view?resource=' + record.get('uri'));
                }
            },
            
            columns : 
            {
                items : [
                {
                    width: 120,
                    dataIndex: 'icon',
                    menuDisabled : true,
                    sortable : false,
                    align:'center',
                    renderer : function(value)
                    {
                        return '<div style="height:40px"><img style="height:40px;width:40px;" src='+value+'?slice=,,0,0&thumbnail=280,280&format=jpeg /></div>'
                    } 
                },
                {
                    text: 'Name',
                    flex: 0.6,
                    maxWidth: 350,
                    sortable: true,
                    dataIndex: 'name' 
                },
                {
                    text: 'Type',
                    flex: 0.4,
                    maxWidth: 200,
                    align: 'center',
                    sortable: true,
                    dataIndex: 'type' 
                },
                {
                    text: 'Date created',
                    flex: 0.5,
                    maxWidth: 250,
                    align: 'center',
                    sortable: true,
                    dataIndex: 'ts',
                },
                {
                    text: 'Published',
                    flex: 0.4,
                    maxWidth: 200,
                    align: 'center',
                    sortable: true,
                    dataIndex: 'public',
                },
                {
                    xtype: 'actioncolumn',
                    maxWidth: 80,
                    menuDisabled : true,
                    sortable : false,
                    align: 'center',
                    items: [
                    {
                        icon : bq.url('../export_service/public/images/delete.png'),
                        align : 'center',
                        tooltip: 'Remove',
                        handler: function(grid, rowIndex, colIndex)
                        {
                            var name = grid.store.getAt(rowIndex).get('name');
                            grid.store.removeAt(rowIndex);
                            BQ.ui.message('Export - Remove', 'File ' + name + ' removed!');
                        }
                    }]
                }],
                defaults : 
                {
                    tdCls: 'align'
                }
            }
        });
        
        return this.resourceGrid;
    },
    
    getResourceStore : function()
    {
        this.resourceStore = Ext.create('Ext.data.ArrayStore', {
            fields: 
            [
                'icon',
                'name',
                {name: 'type', convert: function(value){return Ext.String.capitalize(value)}},  
                {name: 'ts', convert: function(value){return Ext.Date.format(new Date(value), "F j, Y g:i:s a")}},
                {name: 'public', convert: function(value){return (value=='published')?'Yes':'No'}},
                'uri',
                'viewPriority'
            ],
            sorters: 
            [{
                property : 'viewPriority',
                direction : 'ASC'
                
            }]
        });
        
        return this.resourceStore;
    }
})
