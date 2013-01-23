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
                    
                BQ.ui.error(error_str);
                
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
