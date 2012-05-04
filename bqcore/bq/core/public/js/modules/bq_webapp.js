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
  
  this.renderers = {};  

  // parse URL arguments
  if (!urlargs) urlargs = document.URL;
  this.args = parseUrlArguments(urlargs);   

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

  if (this.module_url)  
  this.ms = new ModuleService(this.module_url, {
      ondone     : callback(this, 'done'), 
      onstarted  : callback(this, 'onstarted'),           
      onprogress : callback(this, 'onprogress'), 
      onerror    : callback(this, 'onerror'),
      onloaded   : callback(this, 'init'),
  }); 
  
}

BQWebApp.prototype.init = function (ms) {
    if (ms) this.ms = ms;
    if (!this.ms.module) return;
  
    this.setupUI();
    this.setupUI_inputs();
 
  // process arguments
  if ('mex' in this.args) {
      this.showProgress(null, 'Fetching module execution document');
      BQFactory.request( { uri: this.args.mex, 
                           cb: callback(this, 'load_from_mex'), 
                           errorcb: callback(this, 'onerror'), 
                           uri_params: {view:'deep'}  }); 
      return;      
  }
 
  // loading resource requires initied input UI renderers
  if ('resource' in this.args)
      BQFactory.request( { uri:     this.args.resource, 
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
    //document.getElementById("webapp_input").style.display = 'none';
    //document.getElementById("webapp_parameters").style.display = 'none';
    //document.getElementById("webapp_run").style.display = 'none';
    BQ.ui.tip('webapp_results', 'Visualizing results of a selected execution!',
              {color: 'green', timeout: 10000, anchor:'bottom',}); 
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

BQWebApp.prototype.inputs_from_mex = function (mex) {
    var inputs = this.ms.module.inputs_index;
    var inputs_mex = mex.inputs_index;
    
    for (var n in inputs_mex) {
        if (!(n in inputs)) continue;
        var renderer = inputs[n].renderer;
        var r = inputs_mex[n];  
        if (r && renderer && renderer.select)
            renderer.select(r);
    }
  
}

BQWebApp.prototype.load_from_mex = function (mex) {
    this.hideProgress();
    this.mexMode();
    this.inputs_from_mex(mex);
    this.done(mex);
}


//------------------------------------------------------------------------------
// Selections of resources
//------------------------------------------------------------------------------

BQWebApp.prototype.create_renderer = function ( surface, selector, conf ) {
    conf = conf || {};
    Ext.apply(conf, { width: '100%', renderTo: surface,});
    var renderer = Ext.create(selector, conf);
    var horizontal_padding = 20;
    
    var do_resize = function() {
            var w = document.getElementById(surface);
            if (w) renderer.setWidth(w.clientWidth-horizontal_padding);
    };
    
    Ext.EventManager.addListener( window, 'resize', do_resize, this, { delay: 100, }  );   
    setTimeout(do_resize, 250);    
    
    return renderer;
}

BQWebApp.prototype.setupUI = function () {
    setInnerHtml('title',       this.ms.module.title || this.ms.module.name);
    setInnerHtml('description', this.ms.module.description);
    setInnerHtml('authors',     'Authors: '+this.ms.module.authors);
    setInnerHtml('version',     'Version: '+this.ms.module.version);
}

BQWebApp.prototype.setupUI_inputs = function (my_renderers) {
    //key = key || 'inputs';
    //this.renderers[key] = this.renderers[key] || {};
    //var my_renderers = this.renderers[key];    

    // render input resource pickers
    var inputs = this.ms.module.inputs;
    if (!inputs || inputs.length<=0) return;

    for (var p=0; (i=inputs[p]); p++) {
        var t = i.type;
        if (t in BQ.selectors.resources)
            i.renderer = this.create_renderer( 'inputs', BQ.selectors.resources[t], { resource: i, module: this.ms.module, } );
            //if (my_renderers) my_renderers(i.name) = i.renderer;
    }

    // check if there are parameters to acquire
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
            i.renderer = this.create_renderer( 'parameters', BQ.selectors.parameters[t], { resource: i, module: this.ms.module, } );
            //if (my_renderers) my_renderers(i.name) = i.renderer;
    }
}

// this function needed for proper closure creation
BQWebApp.prototype.setupUI_output = function (i, outputs_index, my_renderers) {
    var n = i.name;
    var r = outputs_index[n]; 
    if (!r) return;
    var t = (r.type || i.type || i.resource_type).toLowerCase();
    if (t in BQ.renderers.resources) {
        var conf = { 
            definition: i, 
            resource: r, 
        };
        
        // special case if the output is a dataset, we expect sub-Mexs
        if (this.mex.iterables && n in this.mex.iterables && r.type=='dataset') {
            this.mex.findMexsForIterable(n, 'outputs/');
            if (Object.keys(this.mex.iterables[n]).length>1) {
                conf.title = 'Select a thumbnail to see individual results:';                  
                conf.listeners = { 'selected': function(resource) { 
                             var suburl = resource.uri;
                             var submex = this.mex.iterables[n][suburl];
                             this.showOutputs(submex, 'outputs-sub');
                        }, scope: this };
            }
        }
        
        my_renderers[n] = this.create_renderer( 'outputs', BQ.renderers.resources[t], conf );
    }
}

BQWebApp.prototype.setupUI_outputs = function (key) {
    key = key || 'outputs';
    this.renderers[key] = this.renderers[key] || {};
    var my_renderers = this.renderers[key];
    
    var outputs_definitions = this.ms.module.outputs;
    var outputs = this.outputs;
    var outputs_index = this.outputs_index; 
    if (!outputs || !outputs_index) return; 
    if (!outputs_definitions || outputs_definitions.length<=0) return;    
    
    // create renderers for each outputs element
    if (outputs_definitions && outputs_definitions.length>0)
    for (var p=0; (i=outputs_definitions[p]); p++) {
        this.setupUI_output(i, outputs_index, my_renderers);
    }
}

BQWebApp.prototype.clearUI_outputs = function (key) {
    key = key || 'outputs'; 
    if (!this.renderers[key]) return;
    var my_renderers = this.renderers[key];    
    for (var p in my_renderers) {
        var i = my_renderers[p];
        if (i) {
            i.destroy();
            delete my_renderers[p];
        }
    }
}

BQWebApp.prototype.clearUI_outputs_all = function () {
    if (!this.renderers) return;
    for (var k in this.renderers) {
        this.clearUI_outputs(k); 
        delete this.renderers[k];
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
            //valid = valid && renderer.validate();
            valid = renderer.validate() && valid; // make this run for all inputs and validate them all
    }    
    if (!valid) return;
    
  
    this.clearUI_outputs_all();    
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
        else
        if ('http-error' in mex.dict) 
            message = "The module reported an internal error:<br>" + mex.dict['http-error'];
        
        BQ.ui.error(message);
        var result_label = document.getElementById("webapp_results_summary");
        if (result_label)
            result_label.innerHTML = '<h3 class="error">'+ message+'</h3>';
    }      
}

BQWebApp.prototype.getRunTimeString = function (tags) {
    if (!tags['start-time'] || !tags['end-time']) 
        return 'a couple of moments';
    
    var t1 = tags['start-time'];
    var t2 = tags['end-time'];
    if (t1 instanceof Array) t1 = t1[0];
    if (t2 instanceof Array) t2 = t2[0];    
    
    var start = new Date();
    var end   = new Date();    
    start.setISO8601(t1);
    end.setISO8601(t2);      
    var elapsed = new DateDiff(end - start);
    return elapsed.toString();
}

BQWebApp.prototype.parseResults = function (mex) {
    // Update module run info
    var result_label = document.getElementById("webapp_results_summary");
    if (result_label) {
        result_label.innerHTML = '<h3 class="good">The module ran in ' + this.getRunTimeString(mex.dict)+'</h3>';
    }
    if (!this.mex_mode) BQ.ui.notification('Analysis done! Verify results...');

    this.showOutputs(mex);
}

BQWebApp.prototype.showOutputs = function (mex, key) {
    if (!mex) { 
        BQ.ui.warning('No outputs to show');
        return;
    }
    var outputs = mex.find_tags('outputs');
    if (outputs && outputs.tags) {
        this.outputs = outputs.tags; // dima - this should be children in the future   
        this.outputs_index  = outputs.create_flat_index();          
    }   
    
    // setup output renderers
    this.clearUI_outputs(key);
    this.setupUI_outputs(key);
}

