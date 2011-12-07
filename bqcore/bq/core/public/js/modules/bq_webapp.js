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

  this.require_geometry = this.require_geometry || null;// enforce input image geometry, not used for datasets, 
  // ex: { z: 'stack', t:'single', fail_message: 'Only supports 3D images!' };
  // fail_message - message that will be displayed if failed the check
  // z or t       - specify dimension to be checked
  // here the z or t value may be:
  //     null or undefined - means it should not be enforced
  //     'single' - only one plane is allowed
  //     'stack'  - only stack is allowed  
  
  this.require_gobjects = this.require_gobjects || null; // enforce selection of graphical objects
  // ex: { gobject: ['point'], amount: 'many', fail_message: 'You must select some root tips!' }; 
  // fail_message - message that will be displayed if failed the check
  // gobject      - a vector of types of gobjects that can be collected
  // amount       - constraint on the amount of objects of allowed type
  // here the amount value can be:
  //     null or undefined - means it should not be enforced
  //     'single' - only one object is allowed
  //     'many'   - only more than one object allowed
  //     'oneornone' - only one or none
  //     number   - exact number of objects allowed

  this.bq_resource = null;
  this.bq_image = null;
  this.bq_user = new BQUser();
  
  
  // create ExtJS place holders for controls
  //this.ui_create_holder('inputs');  
  //this.ui_create_holder('parameters');  
 
  
  
  
  
  
  

  if (this.module_url)  
      this.ms = new ModuleService(this.module_url, {
          ondone     : callback(this, 'done'), 
          onprogress : callback(this, 'progress_check'), 
          onerror    : callback(this, 'onerror'),
          onloaded   : callback(this, 'onmoduleloaded'),          
      });  
  this.module_defined = true;
  if (this.ms.module) this.setupUI();
  
 
  // construct holders for ExtJs components
  /*
  this.holder_selection = Ext.create('Ext.container.Container', {
      layout: { type: 'fit' },
      renderTo: 'webapp_input_thumbnail',
      width: '100%',    
      border: 0,
  });
  */  
  
  if (document.getElementById("webapp_results_dataset")) {
      this.holder_result = Ext.create('Ext.container.Container', {
          layout: { type: 'fit' },
          renderTo: 'webapp_results_dataset',
          height: 250,
          cls: 'bordered',
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
  if ('resource' in args)
      BQFactory.request( {uri: args.resource, cb: callback(this, 'onResourceSelected') });
       
  if ('mex' in args) {
      this.showProgress(null, 'Fetching module execution document');
      BQFactory.request( {uri: args.mex, cb: callback(this, 'load_from_mex'), uri_params: {view:'deep'}  }); 
      return;      
  }
  
  if (this.ms.module) this.setupUI_inputs();
}

//------------------------------------------------------------------------------
// Misc
//------------------------------------------------------------------------------

function setInnerHtml(id, html) {
    var element = document.getElementById(id);
    if (element)
        element.innerHTML = html; 
}

function parseUrlArguments(urlargs) {
    var a = urlargs.split('?', 2);
    if (a.length<2) return {};
    a = a[1].split('&');
    var d = {};
    for (var i=0; i<a.length; i++) {
        var e = a[i].split('=', 2);
        d[unescape(e[0])] = unescape(e[1]);
    }
    return d;
}

BQWebApp.prototype.showNotification = function (s) {
    //var e = document.getElementById("webapp_notification");
    //e.innerHTML = '<p>'+s+'</p>'; 
    //e.style.display = '';
    
    BQ.ui.notification(s, 20000); 
}

BQWebApp.prototype.mexMode = function () {
    this.showNotification('This application is currently showing previously computed results.<br><br>'+
        '<i>Remove the "mex" url parameter in order to analyse new data.</i>'); 
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

BQWebApp.prototype.onerror = function (str) {
    BQ.ui.error(str);
     
    var button_run = document.getElementById("webapp_run_button");
    button_run.childNodes[0].nodeValue = this.label_run;
    button_run.disabled = false;
}

BQWebApp.prototype.onmoduleloaded = function (module) {
    if (this.module_defined) {
        this.setupUI();
        this.setupUI_inputs();
    }
}

//------------------------------------------------------------------------------
// Selections of resources
//------------------------------------------------------------------------------

BQWebApp.prototype.create_renderer = function ( surface, selector, args ) {
    args = args || {};
    args.resource.renderer = Ext.create(selector, {
          width: '100%',          
          renderTo: surface,
          definition: args.definition,          
          resource: args.resource,          
    });
    //surface.add(input.renderer);
    
    var c = args.resource.renderer;    
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

    if (inputs && inputs.length>0)
    for (var p=0; (i=inputs[p]); p++) {
        var t = i.type;
        if (t in BQ.selectors.resources)
            this.create_renderer( 'inputs', BQ.selectors.resources[t], { resource: i,} );
            
        //if (renderer && this.holders && this.holders['inputs'])
            //renderer( this.holders['inputs'], i );
    }

    // render all other prameters
    if (inputs && inputs.length>0)
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
    
    if (outputs_definitions && outputs_definitions.length>0)
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

/*
BQWebApp.prototype.ui_create_holder = function (surf) {
  if (!this.holders) this.holders = {};
  if (document.getElementById(surf)) {
      this.holders[surf] = Ext.create('Ext.container.Container', {
          //layout: { type: 'vbox', align: 'stretch', pack: 'start', },
          //layout: 'anchor',
          layout: 'auto',
          renderTo: surf,
          cls: 'box',
          border: 0,
      });    
      var c = this.holders[surf];
      Ext.EventManager.addListener( window, 'resize', function(e) {
          var o = this;
          setTimeout(function() { 
              var w = document.getElementById(surf).offsetWidth;
              c.setWidth(w);
          }, 100);          
      }, this );
  } 
}
*/

//------------------------------------------------------------------------------
// Selections of resources
//------------------------------------------------------------------------------
BQWebApp.prototype.selectFile = function (input) {

    var uploader = Ext.create('BQ.upload.Dialog', {   
        //title: 'my upload',
        //maxFiles: 1,
        //dataset_configs: BQ.upload.DATASET_CONFIGS.PROHIBIT, 
        listeners: {  'uploaded': function(reslist) { 
                       this.onResourceSelected(reslist[0], input);
                }, scope: this },              
    });
}

BQWebApp.prototype.selectImage = function (input) {
    var rb  = new Bisque.ResourceBrowser.Dialog({
        'height' : '85%',
        'width' :  '85%',
        listeners: {  'Select': function(me, resource) { 
                       this.onResourceSelected(resource, input);
                       //setInterval(function() { me.destroy(); }, 1000);
                }, scope: this },
        
    });
}

BQWebApp.prototype.selectDataset = function (input) {
    var rb  = new Bisque.DatasetBrowser.Dialog({
        'height' : '85%',
        'width' :  '85%',
        listeners: {  'DatasetSelect': function(me, resource) { 
                       //this.onResourceSelected(resource);
                       // onResourceSelected dies and so browser is never closed
                       var i = this; var r = resource;
                       setTimeout(function() { i.onResourceSelected(r, input); }, 100);
                }, scope: this },
    });
}




//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

BQWebApp.prototype.onResourceSelected = function (R, input_key) {
    this.updateResultsVisibility(false);
    this.bq_user.load (R.uri, null );
    this.bq_resource = R;
    this.run_arguments = {};

    var e = document.getElementById("webapp_input_description");    
    if (R.resource_type == 'image') {
        var s = '<p>You have selected an individual "<a href="'+R.uri+'">image</a>"</p>';
        e.innerHTML = s; 
        this.bq_image = R;
        
        // dima - funct test 
        //BQFactory.load( '/xml/seedszie_image_mex.xml', callback(this, this.done) );           
    }
    else if (R.resource_type == 'dataset') {
        if (this.require_gobjects) {
            BQ.ui.error('Improper module configuration, graphical annotations cannont be required on a dataset!'); 
            this.bq_resource = null;
            return;
        }
        
        var s = '<p>You have selected a "<a href="'+R.uri+'">group of images</a>" or a dataset. ';
        s += 'This means that all the images will be used for this execution.</p>';
        e.innerHTML = s;    
        
        // dima - funct test 
        //BQFactory.load( '/xml/seedszie_dataset_mex.xml', callback(this, this.done) );           
    }

    // show the preview thumbnail of the selected resource, 
    // if gobjects are required the image viewer will be shown, so no need for the preview
    if (!this.require_gobjects) {
        var e = document.getElementById("webapp_input_thumbnail");
        e.style.display = '';        
        if (this.resourceContainer) { this.resourceContainer.destroy(); }
        this.resourceContainer = Bisque.ResourceBrowser.ResourceFactoryWrapper( {resource:R} );
        this.holder_selection.add(this.resourceContainer);
    }
        
    // show image viewer and allow gobject selection        
    if (this.require_gobjects) {
        var viewer_div = document.getElementById("webapp_input_viewer");
        viewer_div.style.display = '';
    
        if (this.image_viewer != null) { 
             this.image_viewer.cleanup();
             delete this.image_viewer;
        }
        var viewer_params = {'nogobjects':'', 'nosave':'', 'alwaysedit':'', 'onlyedit':''};
        if (this.require_gobjects.gobject)
            viewer_params.editprimitives = this.require_gobjects.gobject;
        this.image_viewer = new ImgViewer ("webapp_input_viewer", this.bq_resource, this.bq_user.user_name, viewer_params );
    } 
}

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
    
    
    
    /*
    
    if (!this.bq_resource || !this.bq_resource.uri) {
        BQ.ui.attention('Select an input first!');      
        BQ.ui.tip('webapp_input', 'Select an input first!'); 
        return;
    }

    // check for image geometry if requested    
    if ( this.bq_resource && this.bq_resource.resource_type == 'image' && this.require_geometry && (
         (this.require_geometry.z && this.require_geometry.z=='single' && this.bq_resource.z>1) ||
         (this.require_geometry.z && this.require_geometry.z=='stack'  && this.bq_resource.z<=1) ||
         (this.require_geometry.t && this.require_geometry.t=='single' && this.bq_resource.t>1) ||
         (this.require_geometry.t && this.require_geometry.t=='stack'  && this.bq_resource.t<=1)
    )) {
        var msg = this.require_geometry.fail_message || 'Image geometry check failed!';
        BQ.ui.attention(msg);
        BQ.ui.tip('webapp_input_viewer', msg);        
        return;
    }
    
    // if requested, check if gobjects are present 
    if (this.require_gobjects) {
        var msg = this.require_gobjects.fail_message || 'Graphical annotations check failed!';
        var gobs = this.image_viewer ? this.image_viewer.gobjects() : null;
        if (!gobs || // gobs.length<=0 || 
            ( this.require_gobjects.amount && this.require_gobjects.amount=='single'    && gobs.length!=1 ) ||
            ( this.require_gobjects.amount && this.require_gobjects.amount=='many'      && gobs.length<1 ) ||
            ( this.require_gobjects.amount && this.require_gobjects.amount=='oneornone' && gobs.length>1 ) ||
            ( this.require_gobjects.amount && parseInt(this.require_gobjects.amount)>0 && gobs.length!=parseInt(this.require_gobjects.amount) )
        ) {
            BQ.ui.attention(msg);
            BQ.ui.tip('webapp_input_viewer', msg);
            return;
        }  
    }  
    */
    
    this.clearUI_outputs();    
    this.updateResultsVisibility(false);

    var button_run = document.getElementById("webapp_run_button");
    button_run.disabled=true;    
    button_run.childNodes[0].nodeValue = "Running ...";
    
    this.ms.run();
}

//------------------------------------------------------------------------------

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

BQWebApp.prototype.updateResultsVisibility = function (vis, onlybuttons) {
  changeDisabled("webapp_result_view", vis);
  changeDisabled("webapp_result_plot", vis);
  changeDisabled("webapp_result_xml",  vis);
  changeDisabled("webapp_result_csv",  vis);  
  changeDisabled("webapp_result_excel", vis);
  changeDisabled("webapp_result_gdocs", vis);

  if (!vis && !onlybuttons) {
    changeVisibility("webapp_results_viewer", false); 
    changeVisibility("webapp_results_plotter", false);
    if (this.holder_result) this.holder_result.hide();                    
  }
}

//------------------------------------------------------------------------------

BQWebApp.prototype.progress_check = function (mex) {
    if (!mex) return;
    var button_run = document.getElementById("webapp_run_button");    
    if (mex.status != "FINISHED" && mex.status != "FAILED") {
        button_run.childNodes[0].nodeValue = "Progress: " + mex.status;
        button_run.disabled = true;
    }
}

BQWebApp.prototype.load_from_mex = function (mex) {
    this.hideProgress();
    this.mexMode();
    this.done(mex);
    
    // fetch requested mex
    /*
    this.mexdict = mex.toDict(true);       
    var me = this;
    BQFactory.request( { uri: this.mexdict['image_url'], 
                         uri_params: {view:'deep'}, 
                         cb: function (r) { me.bq_resource = r; me.done(mex); } });
    */
}


BQWebApp.prototype.done = function (mex) {
    var button_run = document.getElementById("webapp_run_button");
    button_run.childNodes[0].nodeValue = this.label_run;
    button_run.disabled = false;
    this.mexdict = mex.toDict(true);  
      
    if (mex.status == "FINISHED") {
        this.parseResults(mex);
    } else {
        if ('message' in this.mexdict) 
            //alert("The module reported an internal error:\n\n" + this.mexdict.message);
            BQ.ui.error("The module reported an internal error:<br>" + this.mexdict.message);
        else
            //alert("Module execution failure:\n\n" + mex.toXML());
            BQ.ui.error("Module execution failure:<br>" + mex.toXML());
    }      
}

//------------------------------------------------------------------------------
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

BQWebApp.prototype.renderSummaryTag = function (tag, name, url, descr) {
    if (tag in this.mexdict) {
        if (url && descr)       
            return '<li>'+name +': '+this.mexdict[tag]+' [<a href="'+url+'">'+descr+'</a>]</li>';
        else
            return '<li>'+name +': '+this.mexdict[tag]+'</li>';
    } else
        return '';
}

BQWebApp.prototype.createSumary = function () {
    return '';
}

BQWebApp.prototype.parseResults = function (mex) {
    this.mex = mex;    
    var outputs = mex.find_tags('outputs');
    if (outputs && outputs.tags) {
        this.outputs = outputs.tags; // dima - this should be children in the future   
        this.outputs_index  = outputs.create_flat_index();          
    } 
    this.setupUI_outputs();
    
    return;
    
    
    // here do a test if the input is a dataset or an image
    this.gobjectURL = null;
    
    document.getElementById("webapp_result_description").innerHTML = '';
    var result_label = document.getElementById("webapp_results_summary");
    var summary = this.createSumary();
    this.mexURI = mex.uri;
   
    if (this.bq_resource.resource_type == 'image') {
        //this.bq_image = this.bq_resource;
        result_label.innerHTML = '<h3>The image was processed in ' + this.getRunTimeString(this.mexdict)+'</h3>'+this.createSumary();
        this.selectResultantResource(mex);
    }
    else if (this.bq_resource.resource_type == 'dataset') {
        // create a list of image urls and mex urls 
        
        var mexes = this.mexdict['submex/mex_url'];
        var images = this.mexdict['submex/image_url'];
        if (typeof mexes == 'string') mexes = [mexes];
        if (typeof images == 'string') images = [images];           
        var results = {}; 
        for (var i=0; i<mexes.length; i++)
            results[images[i]] = mexes[i];
        
        // dima - funct test 
        //for (var i=0; i<mexes.length; i++)
        //    results[images[i]] = '/xml/seedszie_image_submex.xml';
        
        result_label.innerHTML = '<h3>The dataset was processed in ' + this.getRunTimeString(this.mexdict)+'</h3>'+this.createSumary()+
          '<p>You can now verify the results for each individual image by selecting one in the dataset browser below:</p>';            
      
        if (this.holder_result) {
            this.holder_result.show();        
            if (this.resultantResourcesBrowser) this.resultantResourcesBrowser.destroy();
            this.resultantResourcesBrowser = new Bisque.ResourceBrowser.Browser({
                //dataset: this.bq_resource.tags[0].uri+'/values',
                dataset: this.bq_resource.getMembers().uri+'/value',
                height: '100%',   
                selType: 'SINGLE',
                viewMode : 'ViewerOnly',
                listeners: {  'Select': function(me, resource) { 
                               var uri = results[resource.uri];
                               this.bq_image = resource.uri;
                               if (uri) {
                                   this.updateResultsVisibility(false, true);
                                   this.showProgress('webapp_results_content', 'Fetching results for the selected image');                               
                                   BQFactory.request( {uri: uri, uri_params: {view:'deep'}, cb: callback(this, this.selectResultantResource) }); 
                               } else
                                   alert('This image does not have any results associated! An error?');
                        }, scope: this },
            });    
            this.holder_result.add(this.resultantResourcesBrowser);          
        }
    } 
    
}

BQWebApp.prototype.selectResultantResource = function (resource) {

    var md = resource.toDict();
    this.bq_image = md['image_url'];

    this.gobjectURL = null;
    document.getElementById("webapp_results_viewer").style.display = 'none'; 
    document.getElementById("webapp_results_plotter").style.display = 'none'; 
    this.hideProgress();
    
    if ( resource.gobjects.length>=1 )
        this.gobjectURL = resource.gobjects[0].uri;    

    var result_label = document.getElementById("webapp_result_description");
    if (this.gobjectURL && this.gobjectURL != '') {
        this.updateResultsVisibility(true);     
        result_label.innerHTML = '<h2>Here are the results for your image:</h2>';
        showTip( 'webapp_result_view', 'Analysis done! Verify results...', {color: 'green', timeout: 10000} );
        BQ.ui.notification('Analysis done! Verify results...');
    } else {
        this.updateResultsVisibility(false);
        result_label.innerHTML = 'Nothing was found in the image or some problem occured.';
    }

    var results_div = document.getElementById("webapp_results_content");
    results_div.style.display = '';
}

//------------------------------------------------------------------------------
// Exporting results
//------------------------------------------------------------------------------

BQWebApp.prototype.exportToXML = function() {
    if (!this.gobjectURL) {
      //showTip( 'webapp_result_xml', 'No resulting gobjects found yet...', {color: 'red', timeout: 10000} );
      BQ.ui.warning('No resulting graphical annotations found yet. Please, run the module first or change parameters.');
      return; 
    }  
    var url = this.gobjectURL + '?view=deep';
    window.open(url);
}

BQWebApp.prototype.exportToExcel = function() {
    if (!this.gobjectURL) {
      BQ.ui.warning('No resulting graphical annotations found yet. Please, run the module first or change parameters.');    
      return; 
    }  
    var url = this.gobjectURL + '?view=deep&format=csv';
    window.open(url);
}

BQWebApp.prototype.exportToCSV = function() {
    // before we provide config for this, through an error
    BQ.ui.warning('This method needs to be overwritten by a developer of a module in order to provide proper function'); 
    /* 
    if (!this.gobjectURL) {
      BQ.ui.warning('No resulting graphical annotations found yet. Please, run the module first or change parameters.');    
      return; 
    }  
    
    var url = '/stats/csv?url=' + this.gobjectURL;
    url += '&xpath=' + escape("//tag[@name='area']");
    url += '&xpath1=' + escape("//tag[@name='major']");
    url += '&xpath2=' + escape("//tag[@name='minor']");
    url += '&xmap=tag-value-number&xreduce=vector';
            
    window.open(url);*/
}

BQWebApp.prototype.exportToGDocs = function() {
    if (!this.gobjectURL) {
      //showTip( 'webapp_result_xml', 'No resulting gobjects found yet...', {color: 'red', timeout: 10000} );      
      BQ.ui.warning('No resulting graphical annotations found yet. Please, run the module first or change parameters.');
      return; 
    }
    var url = '/export/to_gdocs?url='+this.gobjectURL;
    window.open(url);
}

BQWebApp.prototype.view = function() {
    var viewer_div = document.getElementById("webapp_results_viewer"); 
    
    if (viewer_div.style.display == 'none') {
        viewer_div.style.display = '';

        if (this.result_viewer != null) { 
            this.result_viewer.cleanup();
            delete this.result_viewer;
        }
        
        var viewer_params = {'gobjects':this.gobjectURL, 'simpleview':''};          
        this.result_viewer = new ImgViewer ("webapp_results_viewer", this.bq_image, this.bq_user.user_name, viewer_params );
    } else {
        viewer_div.style.display = 'none'; 
    }
}

BQWebApp.prototype.plot = function() {
    // before we provide config for this, through an error
    BQ.ui.warning('This method needs to be overwritten by a developer of a module in order to provide proper function'); 
    /* 
    var plotter_div = document.getElementById("webapp_results_plotter"); 
    
    if (plotter_div.style.display == 'none') {
      plotter_div.style.display = '';
      removeAllChildren(plotter_div);        

      var url = this.gobjectURL;
      var xmap = 'tag-value-number';
      var xreduce = 'histogram';
    
      var surface_area = document.createElementNS(xhtmlns,'div');
      plotter_div.appendChild(surface_area);
      var xpath1 = '//tag[@name="area"]';      
      var opts = { title: 'Distribution of seed areas', height:500, args: {numbins: 18} };
      this.plotter1 = new BQStatisticsVisualizer( surface_area, url, xpath1, xmap, xreduce, opts );

      var surface_major = document.createElementNS(xhtmlns,'div');
      plotter_div.appendChild(surface_major);
      var xpath2 = '//tag[@name="major"]';      
      var opts = { title: 'Distribution of major axis', height:500, args: {numbins: 18} };
      this.plotter2 = new BQStatisticsVisualizer( surface_major, url, xpath2, xmap, xreduce, opts );

      var surface_minor = document.createElementNS(xhtmlns,'div');
      plotter_div.appendChild(surface_minor);
      var xpath3 = '//tag[@name="minor"]';      
      var opts = { title: 'Distribution of minor axis', height:500, args: {numbins: 18} };
      this.plotter3 = new BQStatisticsVisualizer( surface_minor, url, xpath3, xmap, xreduce, opts );
    } else {
        plotter_div.style.display = 'none';      
    }
    */
}

