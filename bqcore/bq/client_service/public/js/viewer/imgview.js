/*
  Image Viewer shell for Bisquik viewer
  The viewer can contain plugins that may modify the 
  the image src and the current image contents (i.e the view)
  
  
  Example call:
     var viewer_params = {'gobjects':'http://gobejcts_url', 'noedit':''};        
     var image_viewer = new ImgViewer ("parent_div_id", 'http://image_url', 'user_name', viewer_params );  
        
  Available parameters:
    simpleviewer   - sets a minimal set of plug-ins and also read-only view for gobjects
    onlyedit       - only sets plug-in needed for editing of gobjects 

    nogobects      - disable loading gobjects by default
    gobjects       - load gobjects from the givel URL, 'gobjects':'http://gobejcts_url'

    noedit         - read-only view for gobjects
	  alwaysedit     - instantiates editor right away and disables hiding it
	  nosave         - disables saving gobjects
	  editprimitives - only load edit for given primitives, 'editprimitives':'point,polyline'
	                   can be one of: 'Point,Rectangle,Polyline,Polygon,Circle'
	                       
    gobjectschanged - callback to call when graphical objects have changed
	                   
*/


var imgview_min_width = 400;


////////////////////////////////////////////////////////////
// ImageDim
// Maintain a record of image imagedimensions

function ImageDim (x, y, z, t, ch){
    this.x = x; 
    this.y = y;
    this.z = z;
    this.t = t;
    this.ch = ch;
}
ImageDim.prototype.clone = function () {
    return new ImageDim(this.x, this.y, this.z, this.t, this.ch);
};

////////////////////////////////////////////////////////////
// Viewstate
// Current viewer properties (viewed dimensions)

function Viewstate (w, h, z, t, scale, rot, offx, offy,origw,origh) {
    
    
    this.width = w;
    this.height = h;
    this.z = z;
    this.t = t;
    this.scale = scale;
    this.rotation = rot || 0;
    this.offset_x = offx || 0;
    this.offset_y = offy || 0;
    this.original_width = origw || w;
    this.original_height = origh|| h;    

    this.imagedim = null;
    this.imagesrc = null;

    this.src_args = [];         // Array of arguments
}

Viewstate.prototype.clone = function  () {
    var v =  new Viewstate (this.width, this.height, this.z, this.t, 
                            this.scale, this.rotation,
                            this.offset_x, this.offset_y);
    if (this.imagedim) 
        v.imagedim = this.imagedim.clone();
    v.imagesrc = this.imagesrc;
    return v;
}


Viewstate.prototype.setSizeTo = function  (w, h) {
    this.width = w;
    this.height = h;
    this.original_width = w;
    this.original_height = h; 
    this.scaleBy(1);   
}

Viewstate.prototype.scaleBy = function  (scale_by) {
    if (scale_by<1 && Math.min(this.width*scale_by, this.height*scale_by) < imgview_min_width )
        scale_by = Math.max(imgview_min_width/this.width, imgview_min_width/this.height);
        
    this.scale *= scale_by;
    this.width *= scale_by;
    this.height *= scale_by;
}

Viewstate.prototype.scaleToBox = function  (bound_w, bound_h) {
    bound_w = Math.max(bound_w, imgview_min_width);
    bound_h = Math.max(bound_h, imgview_min_width);
    var scale = Math.max(bound_w/this.original_width, bound_h/this.original_height);    
        
    this.scale  = scale;
    this.width  = scale*this.original_width;
    this.height = scale*this.original_height;
}

Viewstate.prototype.scaleTo = function  (new_scale) {
    this.scale  = new_scale;
    this.width  = this.scale*this.original_width;
    this.height = this.scale*this.original_height;
}

Viewstate.prototype.scaleToSmallest = function  () {
    this.scaleToBox(imgview_min_width, imgview_min_width);
}

Viewstate.prototype.rotateTo = function(alfa) {
    this.rotation = alfa;
    
    var ow = this.original_width * this.scale;
    var oh = this.original_height * this.scale;    
    var wp = ow;
    var hp = oh;         
    
    var a = this.rotation * ( Math.PI/180.0 );
    var sina = Math.sin(a);
    var cosa = Math.cos(a);   
    if (sina*cosa < 0) {
      wp = Math.abs(ow*cosa - oh*sina);
      hp = Math.abs(ow*sina - oh*cosa);
    } else {
      wp = Math.abs(ow*cosa + oh*sina);
      hp = Math.abs(ow*sina + oh*cosa);
    }    
    
    this.width = wp;
    this.height = hp;
}

Viewstate.prototype.transformPoint = function  (ix, iy) {
    var x = ix * this.scale + this.offset_x;
    var y = iy * this.scale + this.offset_y;
    
    var ow = this.original_width * this.scale;
    var oh = this.original_height * this.scale;       
    x = x - ow/2.0;
    y = y - oh/2.0;    
    var a = this.rotation * ( Math.PI/180.0 );
    var sina = Math.sin(a);
    var cosa = Math.cos(a);   
    var xp = x*cosa - y*sina;
    var yp = x*sina + y*cosa;
    xp += this.width/2.0;
    yp += this.height/2.0; 
        
    return { x:xp, y:yp };
};

Viewstate.prototype.inverseTransformPoint = function  (ix, iy) {

    var x = (ix - this.offset_x - this.width/2.0) / this.scale;
    var y = (iy - this.offset_y - this.height/2.0) / this.scale;
    
    var a = (360-this.rotation) * ( Math.PI/180.0 );
    var sina = Math.sin(a);
    var cosa = Math.cos(a);   
    var xp = x*cosa - y*sina;
    var yp = x*sina + y*cosa;
    xp += this.original_width/2.0;
    yp += this.original_height/2.0;
             
    return { x:xp, y:yp };
}


Viewstate.prototype.addParams = function (params) {
    params = params || [];
    if ( params instanceof Array ) {
        for (var  i =0;  params.length ; i++) 
            this.src_args.push (params[i]);
        return;
    }
    this.src_args.push (params);
}

 
Viewstate.prototype.image_url = function (auxparams) {
    var url = this.imagesrc;
    var params = auxparams || [];

    var args = null;
    var arglist = this.src_args.concat();
    //for (var x in params) arglist.push (params[x]);
    for (var i=0; i<params.length; i++)
      arglist.push (params[i]);
      
    arglist.push ('format=jpeg');

    for (var i = 0; i < arglist.length; i++) {
        if (args == null) 
            args = "?" + arglist[i];
        else 
            args += "&" + arglist[i];
    }
    return url + args;
}



////////////////////////////////////////////////////////////
// ImagePhys
// Maintain a record of image physical parameters
function ImagePhys () {
    this.pixel_size = new Array (0); 
    this.channel_names = new Array (0);     
    this.display_channels = new Array (0);         
}

ImagePhys.prototype.setPixelSize = function ( x, y, z, t ) {
    this.pixel_size[0] = x;
    this.pixel_size[1] = y;
    this.pixel_size[2] = z;
    this.pixel_size[3] = t;            
};
////////////////////////////////////////////////////////////
// ViewerPlugin  
// ImgViewer extensions are plugins that are arranged as pipeline
//      ImageViewer
//  P1 -> P2 -> P3 -> P4

function ViewerPlugin (viewer, name) {
    this.child = null;          // Next in line viewer or html element
    this.viewer= viewer || null;   // The top level viewer 
    this.name  = name || "";    // name for logging and such
}
ViewerPlugin.prototype.create = function (parent){
    return parent;
}
ViewerPlugin.prototype.newImage = function (){
}
ViewerPlugin.prototype.updateImage = function (){
}
ViewerPlugin.prototype.updateView = function (view){
}

// this will be called after all updateImage were called, if any elements are to be positioned
// relative to elements resized later in updateImage queue
ViewerPlugin.prototype.updatePosition = function (){
}

ViewerPlugin.prototype.setSize = function (size)
{
	if (size.height)
		this.imagediv.style.height = size.height+"px";
	if (size.width)
		this.imagediv.style.width = size.width+"px";
}

////////////////////////////////////////////////////////////
// DefaultPlugin
//  A simple plugin as a example.. Set the view size based 
//  on the image size

function DefaultImgPlugin (viewer, name) {
    this.base = ViewerPlugin;
    this.base (viewer, name);

//    this.viewer.addCommand ('blink', callback (this, 'blink'));
}

DefaultImgPlugin.prototype = new ViewerPlugin();
DefaultImgPlugin.prototype.newImage = function () {
    var d = this.viewer.imagedim;
    var v = this.viewer.current_view;
    v.setSizeTo( d.x, d.y );
    //var view = this.viewer.view();
    //this.viewer.src_args.push ('resize=' + view.width + ',' + view.height );
    //this.viewer.src_args.push ('format=jpeg');
}

DefaultImgPlugin.prototype.blink = function (){
    alert ('blink');
}

//////////////////////////////////////////////////////
//  Image Viewer shell for Bisquik viewer
//  The viewer can contain plugins that may modify the 
//  the image src and the current image contents (i.e the view)

function ImgViewer (parentid, image_or_uri, user_uri, parameters) {
  
    this.update_delay_ms = 50;  // Update the viewer asynchronously 
  
    this.target = getObj(parentid);
    this.user   = user_uri;
    this.imageuri = null;   // Toplevel Image URI
    this.plugins = [];          // Ordered array of plugins to be called
    this.plugins_by_name = {};  // dictionary of plugins
    this.imagedim = null;      // Original Image dimensions
    this.imagesrc = null;       // Constructed image src
    this.imagephys = null;
    this.current_view = null;
    this.groups = {};           // Menu Groups
    this.submenu = null;

    this.parameters = parameters || {};      

    this.menudiv = document.createElementNS (xhtmlns, "div");
    this.menudiv.id =  "imgmenu";
    this.menudiv.className = "buttonbar";

    this.imagediv = document.createElementNS (xhtmlns, "div");
    this.imagediv.id="imgviewer_image";
    this.imagediv.className = "image_viewer_display";

/*
    this.optiondiv = document.createElementNS (xhtmlns, "div");
    this.optiondiv.id="imgviewer_option";
    this.optiondiv.className = "image_viewer_option";
*/

    this.target.appendChild (this.menudiv);
    //this.target.appendChild (this.optiondiv);
    this.target.appendChild (this.imagediv);
    
    var plugin_list = "default,slicer,tiles,ops,download,movie,external,permissions,share,statistics,scalebar,progressbar,infobar,edit,renderer";
    if ('onlyedit' in this.parameters)
        plugin_list = "default,slicer,tiles,ops,scalebar,progressbar,infobar,edit,renderer";
    if ('simpleview' in this.parameters) {
        plugin_list = "default,slicer,tiles,ops,scalebar,progressbar,infobar,edit,renderer";
        this.parameters['noedit'] = '';           
    }

    if (ImgViewer.pluginmap == null) 
        ImgViewer.pluginmap = {
            "default"     : DefaultImgPlugin,
            //"scale"       : ImgScale,
            "download"    : ImgDownload,
            "movie"       : ImgMovie,
            "external"    : ImgExternal,                 
            "permissions" : ImgPermissions,
            "statistics"  : ImgStatistics,
            "scalebar"    : ImgScaleBar,
            "progressbar" : ProgressBar,            
            "infobar"     : ImgInfoBar,
            "slicer"      : ImgSlicer,
            "share"       : ImgShare,
            "edit"        : ImgEdit,
            //"scroller"    : ImgScroller,
            "tiles"       : TilesRenderer, // TILES RENDERER MUST BE BEFORE SVGRenderer  
            "ops"         : ImgOperations, // Ops should be after slicer            
            //"image"       : ImageRenderer, // IMAGE RENDERER MUST BE BEFORE SVGRenderer           
            "renderer"    : SVGRenderer,   // RENDERER MUST BE LAST
        };

    var plugin_names = plugin_list.split(',');
    for (var i=0; i < plugin_names.length; i++) {
        var name = plugin_names[i];
        var ctor = ImgViewer.pluginmap[name];
        if (ctor)
           this.plugins_by_name[name] = this.addPlugin (new ctor(this, name));
    }
    if (this.user) {
        var viewer = this;
        BQFactory.load (this.user, function (user) {
            viewer.bq_user = user;
            user.get_credentials();
        });
    }

    this.renderer = this.plugins_by_name["renderer"];
    this.createPlugins(this.imagediv);
    if (image_or_uri instanceof BQImage)
        this.newImage(image_or_uri);
    else if (image_or_uri instanceof BQObject) 
        throw BQOperationError;
    else if (image_or_uri)
        this.load(image_or_uri);

}


ImgViewer.prototype = new ViewerPlugin();
ImgViewer.prototype.close = function (){
    history.back();
}

ImgViewer.prototype.cleanup = function() {
    this.target.removeChild (this.menudiv);
    //this.target.removeChild (this.optiondiv);
    this.target.removeChild (this.imagediv);    
};

ImgViewer.prototype.addPlugin = function  (plugin) {
    this.plugins.push (plugin);
    return plugin;
};
////////////////////////////////////////
// Ask each plugin to create the needed structures including divs.
// 
ImgViewer.prototype.createPlugins = function (parent) {
    var currentdiv = parent;
    for (var i = 0; i < this.plugins.length; i++) {
        var plugin = this.plugins[i];
        currentdiv = plugin.create (currentdiv);
    }
}

function XButtonGroup(name, menu){
    this.name = name;
    this.menu = menu;
    this.buttons = {};

    //this.br = document.createElementNS (xhtmlns, "br");
    //this.menu.appendChild(this.br);

    this.head = document.createElementNS (xhtmlns, "span");
    this.head.className = "group";    
    this.head.innerHTML = name + ': ';
    this.menu.appendChild (this.head);
}

XButtonGroup.prototype.selected = function (text, cb){
    for (var bt in this.buttons) {
        this.buttons[bt].setAttribute('id', '');
    }
    this.buttons[text].setAttribute('id','selected');
    if (cb) cb();
}

ImgViewer.prototype.addCommandGroup = function (group, text, cb) {
    var bg = this.groups[group]; 
    if (bg == null) {
        bg = this.groups[group] = new XButtonGroup(group, this.menudiv);
    }
    var newbt = this.addCommand (text, callback (bg, 'selected', text, cb));
    bg.buttons[text] = newbt;
    return newbt;
}

ImgViewer.prototype.remCommandGroup = function (group) {
    var menu = this.menudiv;    
    var bg = this.groups[group]; 
    if (bg != null) {
        for (var bt in bg.buttons) {
            this.remCommand(bg.buttons[bt]);
        }
        if (bg.br) menu.removeChild(bg.br);
        if (bg.head) menu.removeChild(bg.head);        
        this.groups[group] = null;
    }
}

ImgViewer.prototype.addCommand =function (text, callback, helptext){
    var menu = this.menudiv;
    var button = document.createElementNS (xhtmlns, "button");
    button.innerHTML = text;
    button.setAttribute('id', text);
    button.onclick = callback;
    button.className = "imgview_button";
//     if (helptext != null) {
//         button.tooltip = document.createElementNS (xhtmlns, "div");
//         button.tooptip.innerHTML = helptext;
//         button.onmouseover = function (e) {
//             button.tooltip.style.visibility="visible";
//         }
//         button.onmouseout = function (e) {
//             button.tooltip.style.visibility="hidden";
//         }
//     }
    menu.appendChild (button);
    return button;
}

ImgViewer.prototype.remCommand =function (button){
    var menu= this.menudiv;
    var bt = menu.firstChild ;
    while (bt) {
        if (bt == button){
            menu.removeChild(bt);
            return;
        }
        bt = bt.nextSibling;
    }
}

ImgViewer.prototype.active_submenu = function  (menu) {
    if (this.submenu != null && this.submenu != menu) 
        this.submenu.style.display="none";
    this.submenu = menu;
}

ImgViewer.prototype.view = function  () {
    return this.current_view;
 };

ImgViewer.prototype.resize = function  (sz) {
	if (sz && sz.height)
		//this.imagediv.style.height = (sz.height-this.menudiv.clientHeight)+"px";
		this.imagediv.style.height = sz.height+"px";
		
	if (sz && sz.width)
		this.imagediv.style.width = sz.width+"px";    
    
  if ('tiles' in this.plugins_by_name)
    this.plugins_by_name['tiles'].resize();
 };


ImgViewer.prototype.need_update = function () {
//     if (this.update_needed == null) {
//         this.update_needed = setTimeout(callback(this, 'updateImage'), 50);
//     }
    this.updateImage();
}

ImgViewer.prototype.load = function (uri){
    BQFactory.load (uri, callback(this, 'newImage'));
    //var bqimage = new BQImage ();
    //bqimage.load (this.imageuri, callback (this, 'newImage') );
    //makeRequest( this.imageuri, loadViewer, this,  "get");
};


ImgViewer.prototype.newImage = function (bqimage) {
    if (! (bqimage instanceof BQImage) ) {
        throw BQOperationError;
    }
    this.image = bqimage;
    this.imageuri = bqimage.uri;
    this.imagesrc  = this.image.src;
 
    //this.bq_user = new BQUser ();
    //this.bq_user.get_credentials (this.imageuri, null );     

    var bqimagephys = new BQImagePhys (this.image);
    bqimagephys.load (callback (this, 'newPhys') ); 
    
    // this probably should be run after the imagephys is acquired 
    // in order to disable the use of "default" service at all!
    // here we would have to init a certain waiting widget
    //this.updateImage (); // dima


}



ImgViewer.prototype.updateView = function (view) {
    view = view || this.current_view;
    
    view.imagedim = this.imagedim.clone();
    view.src_args = [];

    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.updateView (view);
    }
    return view;
}

ImgViewer.prototype.image_url = function (view, auxparams) {
    view = this.updateView(view);
    return view.image_url(auxparams);
}

ImgViewer.prototype.doUpdateImage = function () {
    // Plugins use current view to calculate actual src url.
    this.update_needed = null;
    this.updateView();
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.updateImage ();
    }
    
    // the new updatePosition call
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.updatePosition ();
    }    


}

ImgViewer.prototype.updateImage = function () {
    if (this.update_needed) clearTimeout(this.update_needed);
    this.update_needed = setTimeout(callback(this, 'doUpdateImage'), this.update_delay_ms);
}

ImgViewer.prototype.findPlugin = function(name) {
    p = null;
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        if (plugin.name == name) {
          p = plugin;
          break;
        }        
    }    
    return p;
}

ImgViewer.prototype.gobjects = function() {
	return this.gObjects || this.plugins_by_name['edit'].gobjects || [];
}

ImgViewer.prototype.loadGObjects = function(gObjects, renderWhileLoading) 
{
    this.visit_render = new BQProxyClassVisitor(this.renderer);
    this.gObjects = [];
    this.renderWhileLoading = renderWhileLoading;

    if (gObjects instanceof Array )
    {
    	this.image.gobjects=gObjects;
    	this.gobjectsLoaded(true, gObjects);
    }
    else if (gObjects instanceof BQGObject)
    {
    	this.image.gobjects=[gObjects];
    	this.gobjectsLoaded(true, gObjects);
    }
    else if (typeof gObjects =='string'){
    	this.start_wait({op: 'gobjects', message: 'Fetching gobjects'});
        //BQFactory.load (gObjects + '?view=deep', callback(this, 'gobjectsLoaded', true));
        BQFactory.request ({ uri :  gObjects, 
                             uri_params: { view : 'deep'}, 
                             cache:false,
                             cb: callback(this, 'gobjectsLoaded', true)});
    }else {
    	this.start_wait({op: 'gobjects', message: 'Fetching gobjects'});
		this.image.load_gobjects(callback(this, 'gobjectsLoaded'), gObjects, callback(this, 'gobjectsLoadProgress'));
    }
}

ImgViewer.prototype.gobjectsLoadProgress = function(gObj)
{
	if (this.renderWhileLoading)
	{
		this.visit_render.visitall(gObj, [this.current_view]);
		this.gObjects.push(gObj);
	}
}

ImgViewer.prototype.gobjectsLoaded = function(render, gObjects)
{
	//this.gObjects = [ gObjects ] ; //this.image.gobjects;
    if (gObjects instanceof Array) 
        Ext.Array.insert(this.gObjects, 0, gObjects);
    else 
        Ext.Array.insert(this.gObjects, 0, [gObjects]);

	this.end_wait({op: 'gobjects', message: 'Fetching gobjects'});
	
    // Update editPlugin's gobjects array
    var editPlgin = this.findPlugin('edit');
    if (editPlgin)
    	Ext.Array.insert(editPlgin.gobjects, 0, this.gObjects);
    if (render)
        this.showGObjects(this.gObjects);
} 

ImgViewer.prototype.showGObjects = function(gObjects)
{
	if (gObjects instanceof Array)
		this.visit_render.visit_array(gObjects, [this.current_view, true]);
	else
		this.visit_render.visitall(gObjects, [this.current_view, true]);
}

ImgViewer.prototype.hideGObjects = function(gObjects)
{
	if (gObjects instanceof Array)
		this.visit_render.visit_array(gObjects, [this.current_view, false]);
	else
		this.visit_render.visitall(gObjects, [this.current_view, false]);
}

ImgViewer.prototype.start_wait = function (o) {
    var p = this.plugins_by_name["progressbar"]; // dima
    if (!p) {  
      document.body.style.cursor= "wait";
    } else {
      p.start(o);
    }    
}

ImgViewer.prototype.end_wait = function (o) {
    var p = this.plugins_by_name["progressbar"]; // dima
    if (!p) {  
      document.body.style.cursor= "default";
    } else {
      p.end(o);      
    }
}


ImgViewer.prototype.newPhys = function (bqimagephys) {

    this.imagephys = bqimagephys;
    
    this.imagedim = new ImageDim (bqimagephys.x, bqimagephys.y, bqimagephys.z, bqimagephys.t, bqimagephys.ch);

    this.current_view = new Viewstate(imgview_min_width, imgview_min_width, 0, 0, 1.0);
    this.current_view.imagesrc = this.imagesrc;
    this.current_view.imagedim = this.imagedim.clone();
    
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.newImage ();
    }   


    this.updateImage ();

    // Load gobjects from string and return
    if ('gobjects_xml' in this.parameters) {
        var gobjects_xml = this.parameters['gobjects_xml'];
        var gobjects = BQFactory.parseBQDocument (gobjects_xml);
        this.loadGObjects(gobjects)
    }else if ('gobjects' in this.parameters){
        var gobjects_url = this.parameters['gobjects'];
        this.loadGObjects(gobjects_url);
    }    

}

////////////////////////////////////////////////
// Simple  renderer for testing

function SimpleImgRenderer (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
}
SimpleImgRenderer.prototype = new ViewerPlugin();
SimpleImgRenderer.prototype.create = function (parent) {
    this.image = document.createElementNS(xhtmlns, "img");
    parent.appendChild(this.image);
    return this.image
}
SimpleImgRenderer.prototype.updateImage = function () {
    var src = this.viewer.image_url();
    this.image.setAttributeNS(null, "src",   src);
}
