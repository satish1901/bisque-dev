/*******************************************************************************

  BQWebApp - a prototype of a fully integrated interface for a module

  This class should be inherited as demostrated in the example and extended for
  desired functionality of themodule. This class also expects a certain structure
  of the HTML page it will be operating on. Pages should have certain elements:
  <div id="">
  
  
  Possible configurations:
  
  
  
  
  Example:
  
function MyWebApp (args) {
    this.module_url = '/module_service/SeedSize/';    
    this.label_run = "Run my analysis";    
    
    BQWebApp.call(this, args);
}

MyWebApp.prototype = new BQWebApp();  
  
*******************************************************************************/

function BQWebApp (urlargs) {
  // a simple safeguard to only run this when an inherited class is instantiated
  // this will only work if the constructr was properly overwritten on declaration
  if (this.constructor === BQWebApp) return;    
  
  // arguments that may be defined by inherited classes
  this.module_url = this.module_url || location.pathname;
  this.label_run = this.label_run || "Run analysis";

 
  // create ExtJS place holders for controls
  //this.ui_create_holder('inputs');  
  //this.ui_create_holder('parameters');  

  if (this.module_url)  
      this.ms = new ModuleService(this.module_url, {
          ondone     : callback(this, 'done'), 
          onstarted  : callback(this, 'onstarted'),           
          onprogress : callback(this, 'onprogress'), 
          onerror    : callback(this, 'onerror'),
          onloaded   : callback(this, 'onmoduleloaded'),
      });  
  this.module_defined = true;
  if (this.ms.module) this.setupUI();
  
 
  // construct holders for ExtJs components
  if (document.getElementById("webapp_results_dataset")) {
      this.holder_result = Ext.create('Ext.container.Container', {
          layout: { type: 'fit' },
          renderTo: 'webapp_results_dataset',
          border: 0,
          //height: 500,
          //cls: 'bordered',
      });    
      this.holder_result.hide();
      Ext.EventManager.addListener( window, 'resize', function(e) {
          var w = document.getElementById("webapp_results_dataset").offsetWidth;
          this.holder_result.setSize(w, this.holder_result.height);
      }, this, { delay: 100 } );
  }

 
  // parse URL arguments
  if (!urlargs) urlargs = document.URL;
  var args = parseUrlArguments(urlargs);   
 
  // process arguments
  if ('mex' in args) {
      this.showProgress(null, 'Fetching module execution document');
      BQFactory.request( { uri: args.mex, 
                           cb: callback(this, 'load_from_mex'), 
                           errorcb: callback(this, 'onerror'), 
                           uri_params: {view:'deep'}  }); 
      return;      
  }
  
  if (this.ms.module) this.setupUI_inputs();
  
  // loading resource requires initied input UI renderers
  if ('resource' in args)
      BQFactory.request( { uri:     args.resource, 
                           cb:      callback(this, 'load_from_resource'),
                           errorcb: callback(this, 'onerror'), });
  
}

//------------------------------------------------------------------------------
// Misc
//------------------------------------------------------------------------------

function setInnerHtml(id, html) {
    var element = document.getElementById(id);
    if (element)
        element.innerHTML = html; 
}

function changeVisibility( e, vis ) {
  if (!document.getElementById(e)) return;
  if (vis)
      document.getElementById(e).style.display=''; 
  else
      document.getElementById(e).style.display='none';     
}

function changeDisabled( e, vis ) {
  if (document.getElementById(e))
      document.getElementById(e).disabled = !vis;  
}

function parseUrlArguments(urlargs) {
    var a = urlargs.split('?', 2);
    if (a.length<2) {
        a = urlargs.split('#', 2);
        if (a.length<2) return {};
    }
    
    // see if hash is present
    a = a[1].split('#', 2);  
    if (a.length<2)
        a = a[0];
    else
        a = a[0] +'&'+ a[1];  

    // now parse all the arguments    
    a = a.split('&');
    var d = {};
    for (var i=0; i<a.length; i++) {
        var e = a[i].split('=', 2);
        d[unescape(e[0])] = unescape(e[1]);
    }
    return d;
}

BQWebApp.prototype.mexMode = function () {
    this.mex_mode = true;
    BQ.ui.notification('This application is currently showing previously computed results.<br><br>'+
        '<i>Remove the "mex" url parameter in order to analyse new data.</i>', 20000); 
    document.getElementById("webapp_input").style.display = 'none';
    document.getElementById("webapp_parameters").style.display = 'none';
    document.getElementById("webapp_run").style.display = 'none';
    showTip( 'webapp_results', 'Visualizing results of a selected execution!', {color: 'green', timeout: 10000} );
}

BQWebApp.prototype.showProgress = function (p, s) {
    this.hideProgress();
    this.progressbar = new BQProgressBar(p, s, {"float":true});
}

BQWebApp.prototype.hideProgress = function () {
    if (this.progressbar) {
        this.progressbar.stop();
        delete this.progressbar;
        this.progressbar = null;
    }
}

BQWebApp.prototype.onnouser = function () {
    if (!BQSession.current_session || !BQSession.current_session.hasUser()) {
        BQ.ui.warning('You are not logged in! You need to log-in to run any analysis...'); 
    }
}

BQWebApp.prototype.onerror = function (error) {
    var str = error;
    if (typeof(error)=="object") str = error.message;  
    
    this.hideProgress();
    BQ.ui.error(str);
     
    var button_run = document.getElementById("webapp_run_button");
    button_run.childNodes[0].nodeValue = this.label_run;
    button_run.disabled = false;
    
    var result_label = document.getElementById("webapp_results_summary");
    if (result_label)
        result_label.innerHTML = '<h3 class="error">'+str+'</h3>';    
}

BQWebApp.prototype.onmoduleloaded = function (module) {
    if (this.module_defined) {
        this.setupUI();
        this.setupUI_inputs();
    }
}

//------------------------------------------------------------------------------
// loading from
//------------------------------------------------------------------------------

BQWebApp.prototype.load_from_resource = function (R) {
    // find first suitable resource renderer
    var renderer = null;    
    var inputs = this.ms.module.inputs;
    if (inputs && inputs.length>0)
    for (var p=0; (i=inputs[p]); p++) {
        if (!i.renderer) continue;
        var template = i.template || {};
        var accepted_type = template.accepted_type || {};
        accepted_type[i.type] = i.type;

        if (R.resource_type in accepted_type) {
            renderer = i.renderer;
            break;
        }    
    }
    if (renderer && renderer.select)
        renderer.select(R);
}

BQWebApp.prototype.load_from_mex = function (mex) {
    this.hideProgress();
    this.mexMode();
    this.done(mex);
}


//------------------------------------------------------------------------------
// Selections of resources
//------------------------------------------------------------------------------

BQWebApp.prototype.create_renderer = function ( surface, selector, args ) {
    args = args || {};
    var rr = args.definition || args.resource;
    rr.renderer = Ext.create(selector, {
          width: '100%',          
          renderTo: surface,
          definition: args.definition,          
          resource: args.resource,          
    });
    //surface.add(input.renderer);
    
    var c = rr.renderer;    
    Ext.EventManager.addListener( window, 'resize', function(e) {
            var w = document.getElementById(surface);
            var horizontal_padding = 20;
            if (w) c.setWidth(w.clientWidth-horizontal_padding);
        }, this, { delay: 100, } 
    );    
    
}

BQWebApp.prototype.setupUI = function () {
    setInnerHtml('title',       this.ms.module.title);
    setInnerHtml('description', this.ms.module.description);
    setInnerHtml('authors',     'Authors: '+this.ms.module.authors);
    setInnerHtml('version',     'Version: '+this.ms.module.version);
}

BQWebApp.prototype.setupUI_inputs = function () {

    // render input resource pickers
    var inputs = this.ms.module.inputs;
    if (!inputs || inputs.length<=0) return;

    for (var p=0; (i=inputs[p]); p++) {
        var t = i.type;
        if (t in BQ.selectors.resources)
            this.create_renderer( 'inputs', BQ.selectors.resources[t], { resource: i,} );
            
        //if (renderer && this.holders && this.holders['inputs'])
            //renderer( this.holders['inputs'], i );
    }

    // check of there are parameters to acquire
    for (var p=0; (i=inputs[p]); p++) {
        var t = (i.type || i.resource_type).toLowerCase();
        if (t in BQ.selectors.parameters) {
            changeVisibility( "webapp_parameters", true );
            break;
        }
    }    
    
    // render all other prameters    
    for (var p=0; (i=inputs[p]); p++) {
        var t = (i.type || i.resource_type).toLowerCase();
        if (t in BQ.selectors.parameters)
            this.create_renderer( 'parameters', BQ.selectors.parameters[t], { resource: i,} );
            
        //if (renderer && this.holders && this.holders['parameters'])
            //renderer( this.holders['parameters'], i );
    }
}

BQWebApp.prototype.setupUI_outputs = function () {
    var outputs_definitions = this.ms.module.outputs;
    //var mex = this.mex;
    var outputs = this.outputs;
    var outputs_index = this.outputs_index; 
    if (!outputs || !outputs_index) return; 
    if (!outputs_definitions || outputs_definitions.length<=0) return;    
    
    //if (outputs_definitions && outputs_definitions.length>0)
    for (var p=0; (i=outputs_definitions[p]); p++) {
        var n = i.name;
        var t = (i.type || i.resource_type).toLowerCase();
        var r = outputs_index[n];  
        if (t in BQ.renderers.resources) {
            this.create_renderer( 'outputs', BQ.renderers.resources[t], { definition: i, resource: r, } );
        }
    }
}

BQWebApp.prototype.clearUI_outputs = function () {
    var outputs_definitions = this.ms.module.outputs;
    if (outputs_definitions && outputs_definitions.length>0)
    for (var p=0; (i=outputs_definitions[p]); p++) {
        if (i.renderer) {
            i.renderer.destroy();
            i.renderer = undefined;
        }
    }
}

BQWebApp.prototype.updateResultsVisibility = function (vis) {
    if (!vis) {
        if (this.holder_result) this.holder_result.hide();                    
        var result_label = document.getElementById("webapp_results_summary");
        if (result_label) result_label.innerHTML = '<h3>No results yet...</h3>';
    }  
}

//------------------------------------------------------------------------------
// Run
//------------------------------------------------------------------------------

BQWebApp.prototype.run = function () {
    
    if (!BQSession.current_session || !BQSession.current_session.hasUser()) {
        BQ.ui.warning('You are not logged in! You need to log-in to run any analysis...');      
        BQ.ui.tip('webapp_run_button', 'You are not logged in! You need to log-in to run any analysis...'); 
        return;           
    }
    
    var valid=true;
    var inputs = this.ms.module.inputs;
    if (inputs && inputs.length>0)
    for (var p=0; (i=inputs[p]); p++) {
        var renderer = i.renderer;
        if (renderer) 
            valid = valid && renderer.validate();
    }    
    if (!valid) return;
    
  
    this.clearUI_outputs();    
    this.updateResultsVisibility(false);

    var button_run = document.getElementById("webapp_run_button");
    button_run.disabled=true;    
    button_run.childNodes[0].nodeValue = "Running ...";
    
    this.ms.run();
}

BQWebApp.prototype.onstarted = function (mex) {
    if (!mex) return;
    window.location.hash = 'mex=' + mex.uri;
    //window.location.hash
    //history.pushState({mystate: djksjdskjd, }, "page 2", "bar.html");
}

BQWebApp.prototype.onprogress = function (mex) {
    if (!mex) return;
    var button_run = document.getElementById("webapp_run_button");    
    if (mex.status != "FINISHED" && mex.status != "FAILED") {
        button_run.childNodes[0].nodeValue = "Progress: " + mex.status;
        button_run.disabled = true;
    }
}

//------------------------------------------------------------------------------
// getting results
//------------------------------------------------------------------------------

BQWebApp.prototype.done = function (mex) {
    var button_run = document.getElementById("webapp_run_button");
    button_run.childNodes[0].nodeValue = this.label_run;
    button_run.disabled = false;
    this.mex = mex;
      
    if (mex.status == "FINISHED") {
        this.parseResults(mex);
    } else {
        var message = "Module execution failure:<br>" + mex.toXML(); 
        if ('error_message' in mex.dict && mex.dict.error_message!='') 
            message = "The module reported an internal error:<br>" + mex.dict.error_message;
        
        BQ.ui.error(message);
        var result_label = document.getElementById("webapp_results_summary");
        if (result_label)
            result_label.innerHTML = '<h3 class="error">'+ message+'</h3>';
    }      
}

BQWebApp.prototype.getRunTimeString = function (tags) {
  var time_string='a couple of moments';
  if (tags['start-time'] && tags['end-time']) {
    var start = new Date();
    var end   = new Date();    
    start.setISO8601(tags['start-time']);
    end.setISO8601(tags['end-time']);      
    var elapsed = new DateDiff(end - start);
    time_string = elapsed.toString();
  }
  return time_string;
}

BQWebApp.prototype.parseResults = function (mex) {
    // Update module run info
    var result_label = document.getElementById("webapp_results_summary");
    if (result_label) {
        result_label.innerHTML = '<h3 class="good">The module ran in ' + this.getRunTimeString(mex.dict)+'</h3>';
    }
    if (!this.mex_mode) BQ.ui.notification('Analysis done! Verify results...');

    // if mex contains sub-runs, show dataset picker
    if (mex.iterables) {
        if (this.holder_result) {
            var name = mex.dict['execute_options/iterable'];              
            this.holder_result.show();        
            if (this.resultantResourcesBrowser) this.resultantResourcesBrowser.destroy();
            this.resultantResourcesBrowser = Ext.create('BQ.renderers.Dataset', {
                resource: mex.iterables[name]['dataset'],
                title: 'This module ran in parallel over the following dataset, pick an element to see individual results:',
                listeners: { 'selected': function(resource) { 
                                 var suburl = resource.uri;
                                 var submex = mex.iterables[name][suburl];
                                 this.showOutputs(submex);
                             }, scope: this },
            });    
            this.holder_result.add(this.resultantResourcesBrowser);          
        }    
    } else {
        this.showOutputs(mex);
    }
}

BQWebApp.prototype.showOutputs = function (mex) {
    var outputs = mex.find_tags('outputs');
    if (outputs && outputs.tags) {
        this.outputs = outputs.tags; // dima - this should be children in the future   
        this.outputs_index  = outputs.create_flat_index();          
    }   
    
    // setup output renderers
    this.clearUI_outputs();
    this.setupUI_outputs();
}

