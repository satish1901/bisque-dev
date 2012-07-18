// <![CDATA[
// globals.
var pic_dir = '/static/pics/';
var svgns  = "http://www.w3.org/2000/svg";
var xlinkns  = "http://www.w3.org/1999/xlink";
var xhtmlns = 'http://www.w3.org/1999/xhtml';

// adding it as a prototype object enables it to be used from any array
Array.prototype.removeItems = function(itemsToRemove) {

  if (!/Array/.test(itemsToRemove.constructor)) {
    itemsToRemove = [ itemsToRemove ];
  }

  var j;
  for (var i = 0; i < itemsToRemove.length; i++) {
    j = 0;
    while (j < this.length) {
      if (this[j] == itemsToRemove[i]) {
        this.splice(j, 1);
      } else {
        j++;
      }
    }
  }
}

function findPos  (obj) {
  var curleft = curtop = 0;
  if (obj.offsetParent) {
    curleft = obj.offsetLeft
    curtop = obj.offsetTop
        while ((obj = obj.offsetParent)) {
      curleft += obj.offsetLeft
      curtop += obj.offsetTop
    }
  }
  return [curleft,curtop];
}

function in_array(needle,haystack) {
  var bool = false;
  for (var i=0; i<haystack.length; i++) {
    if (haystack[i]==needle) {
      bool=true;
    }
  }
  return bool;
}

function deleteConfirm( text ) {
var agree=confirm(text);
if (agree)
  return true ;
else
  return false ;
}

// escape all the wierd characters
function URLencode(sStr) {
        return escape(sStr).
                replace(/\+/g, '%2B').
                replace(/\"/g,'%22').
                replace(/\'/g, '%27').
                replace(/\//g,'%2F');
}

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
function callback (obj, method) {
    var thisobj = obj;
    var thismeth = (typeof method == "string")?thisobj[method]:method;
    var thisextra = Array.prototype.slice.call(arguments,2);
    
    return function () {
        var args = Array.prototype.slice.call(arguments)
        return thismeth.apply (thisobj, thisextra.concat(args));
    };
}


function parseXML(txt) {
    var xmlDoc=null;
    if (window.DOMParser) {
        parser=new DOMParser();
        xmlDoc = parser.parseFromString(txt, "text/xml");
    } else { // Internet Explorer
        xmlDoc = new ActiveXObject("Microsoft.XMLDOM");
        xmlDoc.async="false";
        xmlDoc.loadXML(txt); 
    }
    return xmlDoc; 
}

function evalXpath(node, expression) {
    var xpe = new XPathEvaluator();
    var nsResolver = xpe.createNSResolver(node.ownerDocument == null ? node.documentElement : node.ownerDocument.documentElement);    
    return xpe.evaluate( expression, node, nsResolver, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );     
}

function domTagsToDict(node, deep, found, prefix) {
    deep = deep || false;
    found = found || {};
    prefix = prefix || '';   
    
    var tags = node.getElementsByTagName("tag");
    for (var i=0; i<tags.length; i++) {       
        var name  = attribStr(tags[i], 'name');
        var value = attribStr(tags[i], 'value');
        if (!(prefix+name in found) && value)    
            found[prefix+name] = value;
        else
            if (!found[prefix+name])
                found[prefix+name] = [ value ];            
            else if (typeof found[prefix+name] == 'string')
                found[prefix+name] = [ found[prefix+name], value ];
            else
                found[prefix+name].push(value);
        if (deep) 
            domTagsToDict (tags[i], deep, found, prefix+name+'/');
    }
    return found;
}


// this is needed by selector and region selector to get events 
function createMethodReference(object, methodName) {
  return function (event) {
    return object[methodName].call(object, event || window.event);
  };
}

function displayWaitInfo( thediv, info  ) {
  var waitdiv = document.createElementNS(xhtmlns, 'div');
  waitdiv.style.background ="#fff"
  waitdiv.style.maxWidth = "300px"
  var waitspan = document.createElementNS(xhtmlns, 'span');
  waitspan.className = "infospan" 
  waitspan.innerHTML = info
  var waitimg = document.createElementNS(xhtmlns, 'img');
  waitimg.src= pic_dir + 'mandance.gif';
  
  waitdiv.appendChild(waitimg); 
  waitdiv.appendChild(waitspan);  
  thediv.appendChild(waitdiv);  
};


// clean up an XML/HTML node by removing all its children nodes
function removeAllChildren(element)
{
        while(element.hasChildNodes())
          element.removeChild(element.firstChild);
}

// should we even attempt to support NN4 since it shouldn't be able to 
function getObj(name) {
  if (typeof name != 'string') return name;
  
  if (document.getElementById) {  // (Mozilla, Explorer 5+, Opera 5+, Konqueror, Safari, iCab, Ice, OmniWeb 4.5)
    return document.getElementById(name);
  } else if (document.all) {  // (Explorer 4+, Opera 6+, iCab, Ice, Omniweb 4.2-) fuckos!
    return document.all[name];
  } else {
    alert("looks like your javascript is not standards compliant.");
  }
  // Netscape 4, Ice, Escape, Omniweb 4.2-  || don't think we need this
  // else if (document.layers) {  
  //  this = document.layers[name];
  //  this.style = document.layers[name];
  //  return this;
  //}
    return name;
}

function getX(obj) {
  var curleft = 0;
  while (obj.offsetParent) {
    curleft += obj.offsetLeft
    obj = obj.offsetParent;
  }
  return curleft;
}

function getY(obj) {
  var curtop = 0;
  while (obj.offsetParent) {
    curtop += obj.offsetTop
    obj = obj.offsetParent;
  }
  return curtop;
}

function attribDict (node){
    var d = {};
    var al = node.attributes;
    for (var i = 0; i < al.length; i++)
        d[al[i].name] = al[i].value;
    return d;
}

function attribInt (node, a){
    var v = node.getAttribute(a);
    if (v != null && v != "") {
        v = parseInt (v);
        return v;
    }
    return null;
}
function attribFloat (node, a){
    var v = node.getAttribute(a);
    if (v != null && v != "") {
        v = parseFloat (v);
        return v;
    }
    return null;
}

function attribStr (node, a){
    var v = node.getAttribute(a);
    if (v!=null)
        return v;
    return null;
}


function onenterkey(cb) {
    return function (e) {
        var k;
        if (window.event) k = window.event.keyCode;
        else if (e) k = e.which;
        else return true;
        if (k == 13) {
            cb();
            return false;
        }
        else
            return true;
    }
}



function getElement(event) {
  return event.target || event.srcElement;
}

function isLeftClick (event) {
  return (((event.which) && (event.which == 1)) ||
           ((event.button) && (event.button == 1)));
}

function  pointerX (event) {
  return event.pageX || (event.clientX + 
    (document.documentElement.scrollLeft || document.body.scrollLeft));
}
function pointerY (event) {
  return event.pageY || (event.clientY +
    (document.documentElement.scrollTop || document.body.scrollTop));
}


function printXML( node ) {
  var xml = "";
  
  if (node != null ) { 
    xml = "<" + node.tagName ;
          var at = node.attributes;
    if (at) {
      for (var i=0;i<at.length; i++) {
        xml += " " + at[i].name + "=\"" + at[i].value + "\"";
      }
    }
     if( node.hasChildNodes ) {
      xml += ">\t";
                  for(var m = node.firstChild; m != null; m = m.nextSibling) {
        xml += printXML(m); //m.nodeName +  ";   " ;
      }
      xml += "</" + node.tagName + ">\n";
    } else if ( node.value ) {
      xml += " value=\"" + node.value + "\"/>\n";
    } else if (node.text ) {
      xml += ">"+ node.text + "</" + node.tagName + ">\n";
    } else {
      xml += " />\n";
    }
  }
  return xml;
}

// threadsafe asynchronous XMLHTTPRequest code
function makeRequest ( url, callback, callbackdata, method, postdata, errorcb ) {

    function bindCallback(){
        if (ajaxRequest.readyState == XMLHttpRequest.DONE) {
            //clog ("ajaxRequest.readyState == 4 and status: " + ajaxRequest.status);
            BQSession.reset_timeout();
            if (ajaxRequest.status == 200 || ajaxRequest.status == 0) {
                if (ajaxCallback) {
                    if (ajaxRequest.responseXML != null) { // added to accomodate HTML requests as well as XML requests
                        ajaxCallback( ajaxCallbackData, ajaxRequest.responseXML);
                    } else {
                        ajaxCallback( ajaxCallbackData, ajaxRequest.responseText);
                    }
                } else {
                    clog ("makeRequest - no callback defined: "+url);
                }
            } else {
                var consumed_status = { 401:undefined, 403:undefined, 404:undefined, };
                var error_short = ("There was a problem with the request:\n" + 
                                   ajaxRequest.status + ":\t" + ajaxRequest.statusText + "\n");
                var error_str = (error_short + ajaxRequest.responseText);
                
                if (ajaxRequest.status == 401 || ajaxRequest.status==403 )
                    error_str = "You do not have permission for this operation\nAre you logged in?\n\n"+url;
                else
                if (ajaxRequest.status == 404)
                    error_str = "Requested resource does not exist:\n"+url;
                                 
                if (ajaxCallbackError) {
                    ajaxCallbackError({ request: ajaxRequest, message: error_str, message_short: error_short});
                    //throw(error_str);                    
                    return;
                } 
                
                if (ajaxRequest.status in consumed_status ) {
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
            if ( method == "get" || method == "delete") {
                ajaxRequest.open(method, url , true);
                ajaxRequest.send(null);
            } else {
                ajaxRequest.open(method, url , true);
                //ajaxRequest.setRequestHeader("Content-Type","application/x-www-form-urlencoded; charset=UTF-8");
                ajaxRequest.setRequestHeader("Content-Type","text/xml");
                ajaxRequest.send( postdata );
            }
            return ajaxRequest;
        }
    } catch (e) {
        clog ("Exception in Ajax request: " + e.toString());
    }
}

// Will call on response will call cb (xmldata)
function xmlrequest ( url, cb,  method, postdata, errorcb ) {
    function checkResponse() {
        if (ajaxRequest.readyState == XMLHttpRequest.DONE) {
            BQSession.reset_timeout();
            if (ajaxRequest.status == 200) {
                if (ajaxRequest.callback) {
                    if (ajaxRequest.responseXML != null) { 
                        // added to accomodate HTML requests 
                        // as well as XML requests
                        ajaxRequest.callback(ajaxRequest.responseXML);
                    } else {
                        clog ('WARNING: xmlrequest return text/html');
                        ajaxRequest.callback(ajaxRequest.responseText);
                    }
                } else {
                    clog ("xmlrequest - no callback defined: "+url);
                }
            } else {
                var error_short = "There was a problem with the request:\n";
                if (ajaxRequest.request_url) 
                    error_short += 'URL: ' + ajaxRequest.request_url+'\n';
                error_short += 'Status: ' + ajaxRequest.status+'\n';
                error_short += 'Message: ' + ajaxRequest.statusText+'\n';
                var error_str = (error_short + ajaxRequest.responseText);                
                
                var consumed_status = { 401:undefined, 403:undefined, 404:undefined, };
                if (ajaxRequest.status == 401 || ajaxRequest.status==403 ) {
                    //error_str = "You do not have permission for this operation\nAre you logged in?\n\n"+url;
                    window.location ="/auth_service/login?came_from=" + window.location;
                } else
                if (ajaxRequest.status == 404)
                    error_str = "Requested resource does not exist:\n"+url;
                                 
                if (ajaxRequest.errorcallback) {
                    ajaxRequest.errorcallback({ request : ajaxRequest,
                                                message : error_str, 
                                                message_short: error_short});
                } else {
                    BQ.ui.error(error_str); 
                }
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
            ajaxRequest.open(method, url , true);
            ajaxRequest.setRequestHeader('Accept', 'text/xml');

            if (method == "get" || method == "delete") {
                ajaxRequest.send(null);
            } else {
                //ajaxRequest.setRequestHeader("Content-Type",
                //"application/x-www-form-urlencoded; charset=UTF-8");
                ajaxRequest.setRequestHeader("Content-Type","text/xml");
                ajaxRequest.send( postdata );
            }
            return ajaxRequest;
        } 
    } catch (e) {
        clog ("Exception in Ajax request: " + e.toString());
    }
}

function chainRequest (ajaxRequest, cb) {
    var first = ajaxRequest.callback;
    var second = cb;
    function chain (data) {
        first (data);
        second(data);
    }
    ajaxRequest.callback  = chain;
}


function makeRequestC(url, obj, objmeth, httpmethod, postxml){
    var thisobj = obj;
    var thismeth = objmeth;
    function bindload(ignore, arg) {
        return thisobj[thismeth].call (thisobj, arg);
    };
    makeRequest(url, bindload, null, httpmethod, postxml);
}

function checkErrorXML (data, xmlResource) {
  if (!xmlResource) return "THERE WAS NO RESPONSE!!!\n";
  //////////////
  var errors = xmlResource.getElementsByTagName("error");
  if (errors.length > 0 ) {
    var txt = "THERE WERE SOME ERRORS: \n";
    for (var i=0; i< errors.length; i++) {
      txt += "error " + (i +1) +  ': ' + unescape( errors[i].firstChild.nodeValue ) + "\n";
    }   
    alert( txt );
  }
}
function checkResponseXML(data, xmlResponse) {
    var error_text = xmlResponse.text;

    if (error_text != "") 
        alert ("Response from " + data + " was " + error_text);
}


function clog(str) {
    if (typeof(window['console']) != "undefined") {
        var name = arguments.callee.caller.$name || arguments.callee.caller.name;
        var owner = null;
        try {
            name  = arguments.callee.caller.caller.$name || arguments.callee.caller.caller.name;
            owner = arguments.callee.caller.caller.$owner.$className;
        } catch(err) {
            // do nothing really
        }
        var caller = '';
        if (name) caller = name + ': ';
        if (owner) caller = owner+'.'+caller;
        console.log(caller + str);
    }
}

function deleteNodes(t) {
  if(t.firstChild != null) {
    for(var i=0; i < t.childNodes.length; i++) {
      t.removeChild(t.childNodes[i]);
    }
    if(t.firstChild != null) {
        this.deleteNodes(t);
    }
  }
}

encodeParameters = function  (obj) {
    var params = new Array();
    for (key in obj) {
        if (obj[key]) {
            params.push (key + "=" + encodeURIComponent (obj[key]));
        }
    }
    return params.join('&');
}

/* Call with 
   str =   sprintf  ("Try {0}  {1}", "this", "out" );
*/
sprintf = function() { 
  var num = arguments.length; 
  var oStr = arguments[0];   
  for (var i = 1; i < num; i++) { 
    var pattern = "\\{" + (i-1) + "\\}"; 
    var re = new RegExp(pattern, "g"); 
    oStr = oStr.replace(re, arguments[i]); 
  } 
  return oStr; 
} 


if (!Array.prototype.reduce)
{
  Array.prototype.reduce = function(fun /*, initial*/)
  {
    var len = this.length;
    if (typeof fun != "function")
      throw new TypeError();

    // no value to return if no initial value and an empty array
    if (len == 0 && arguments.length == 1)
      throw new TypeError();

    var i = 0;
    if (arguments.length >= 2)
    {
      var rv = arguments[1];
    }
    else
    {
      do
      {
        if (i in this)
        {
          rv = this[i++];
          break;
        }

        // if array contains no values, no initial value to return
        if (++i >= len)
          throw new TypeError();
      }
      while (true);
    }

    for (; i < len; i++)
    {
      if (i in this)
        rv = fun.call(null, rv, this[i], i, this);
    }

    return rv;
  };
}
if (!Array.prototype.forEach)
{
  Array.prototype.forEach = function(fun /*, thisp*/)
  {
    var len = this.length >>> 0;
    if (typeof fun != "function")
      throw new TypeError();

    var thisp = arguments[1];
    for (var i = 0; i < len; i++)
    {
      if (i in this)
        fun.call(thisp, this[i], i, this);
    }
  };
}

Array.prototype.find = function(searchStr) {
  var returnArray = false;
  for (var i=0; i<this.length; i++) {
    if (typeof(searchStr) == 'function') {
      if (searchStr.test(this[i])) {
        if (!returnArray) { returnArray = [] }
        returnArray.push(i);
      }
    } else {
      if (this[i]===searchStr) {
        if (!returnArray) { returnArray = [] }
        returnArray.push(i);
      }
    }
  }
  return returnArray;
}
if(!String.prototype.startswith){
    String.prototype.startswith = function (input) {
        return this.substr(0, input.length) === input;
    }
}
function extend(child, supertype)
{
    child.prototype.__proto__ = supertype.prototype;
}

function isdefined( variable)
{
    return (typeof(window[variable]) == "undefined")?  false: true;
}


// ]]>
