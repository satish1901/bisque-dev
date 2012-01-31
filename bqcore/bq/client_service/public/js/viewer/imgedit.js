// Imageviewer plugin enabling gobject editing functions 
/*
  Used input parameters:
    noedit         - read-only view for gobjects
	  alwaysedit     - instantiates editor right away and disables hiding it
	  nosave         - disables saving gobjects
	  editprimitives - only load edit for given primitives, 'editprimitives':'point,polyline'
*/

ImgViewer.BTN_TITLE_ANNOTATE = 'Annotate';
ImgViewer.BTN_TITLE_CANCEL   = 'Cancel';
ImgViewer.BTN_TITLE_SELECT   = 'Select';
ImgViewer.BTN_TITLE_NAVIGATE = 'Navigate';
ImgViewer.BTN_TITLE_SAVE     = 'Save';

ImgViewer.BTN_TITLE_POINT    = 'Point';
ImgViewer.BTN_TITLE_RECT     = 'Rectangle';
ImgViewer.BTN_TITLE_POLYLINE = 'Polyline';
ImgViewer.BTN_TITLE_POLYGON  = 'Polygon';
ImgViewer.BTN_TITLE_CIRCLE   = 'Circle';

ImgViewer.BTN_TITLE_GROUP    = 'Annotations';

function ImgEdit (viewer,name){
  this.base = ViewerPlugin;
  this.base (viewer, name);
  this.gobjects = new Array(0);
  this.mode = null;
  this.current_gob = null;
  
  this.zindex_high = 25;
  this.zindex_low  = 15;  
  
  //parse input parameters
  var primitives = 'Point,Rectangle,Polyline,Polygon,Circle'.toLowerCase().split(',');
  if ('editprimitives' in this.viewer.parameters) 
    primitives = this.viewer.parameters['editprimitives'].toLowerCase().split(',');
  this.editprimitives = {};
  for (var i=0; i < primitives.length; i++)
    this.editprimitives[ primitives[i] ] = '';
	
  // create interface	
  if ( !('noedit' in this.viewer.parameters) )  
    this.bt_edit = this.viewer.addCommand (ImgViewer.BTN_TITLE_ANNOTATE, callback (this, 'editImage'));
  this.edit_buttons = new Array(0);
  
  this.keymap = { 46: callback(this, 'delete_item'),  // key delete
                   8: callback(this, 'delete_item') };
  
  if ('alwaysedit' in this.viewer.parameters)
    this.bt_edit.style.display = "none";
}
ImgEdit.prototype = new ViewerPlugin();

ImgEdit.prototype.newImage = function () {
    this.gobjects = new Array(0);
    this.visit_render = new BQProxyClassVisitor (this.viewer.renderer);

	return;
/*    var gobjects_url = null;


    // Attempt to load gobjects if requested
    if ('nogobjects' in this.viewer.parameters)  {
        return;
    }

    //this.viewer.start_wait();

    // Load gobjects from string and return
    if ('gobjects_xml' in this.viewer.parameters) {
        var gobjects_xml = this.viewer.parameters['gobjects_xml'];
        this.gobjects = BQFactory.parseBQDocument (gobjects_xml);
        this.visit_render.visit_array(this.gobs, [this.viewer.current_view]);
        return this.gobject_done();
    }

    //Load passed in gobjects, otherwise load image gobjects
    if ('gobjects' in this.viewer.parameters)
        gobjects_url = this.viewer.parameters['gobjects'];

    // Load gobjects from net
    this.viewer.start_wait({op: 'gobjects', message: 'Fetching gobjects'});
    this.viewer.loadGObjects(gobjects_url, callback(this,'gobjects_loading'), callback(this,'gobjects_done'));*/
}

ImgEdit.prototype.gobjects_loading = function (g) {
//    while (goblist.length) {
        try {
            //var g = goblist.pop();
            // This render is needed to show slowly arriving gobjects
            // from the server. Often the renderer has completely
            // run before they have arrived.
            this.visit_render.visitall(g, [this.viewer.current_view]);
            this.push_gobject(g);
        } catch (err ) {
            clog ("error in rendering" + err.description);
        }
//    }
}
ImgEdit.prototype.gobjects_done = function () {
    this.gobjects = this.viewer.image.gobjects;
    this.viewer.end_wait({op: 'gobjects', message: 'Fetching gobjects'});    
    //this.viewer.gobjects = this.gobjects;
    //this.viewer.end_wait();
}

ImgEdit.prototype.updateImage = function () {
    //var gobs  = this.gobjects;
    //this.visit_render.visit_array(gobs, [this.viewer.current_view]);
    if ('alwaysedit' in this.viewer.parameters && !this.buttons_created) this.editImage();      
}


ImgEdit.prototype.editImage = function () {
  
    if (this.bt_edit.innerHTML != ImgViewer.BTN_TITLE_ANNOTATE) {
      this.cancelEdit();
      return;
    }
    
    if (!(this.viewer.user_uri && (this.viewer.image.owner == this.viewer.user_uri)))
        if (!('nosave' in this.viewer.parameters)) {
            alert ("You are not the owner the image and may not save graphical annotations");
        }      
    
    var bt = this.edit_buttons;
    var v = this.viewer;    
    // For SOME weird reseaon this does not seem to work.
    //this.gobject_backup = deep_clone (this.viewer.gobjects);
    
    this.bt_edit.innerHTML = ImgViewer.BTN_TITLE_CANCEL;
    
    if (!('nosave' in this.viewer.parameters)) 
      bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_SAVE, callback(this, "save_edit")));	

    //bt.push(v.addCommandGroup("edit", ImgViewer.BTN_TITLE_SELECT, callback(this, "setmode", callback(this, 'select'), "help me")));
    bt.push( v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_NAVIGATE, callback(this, 'navigate')) );
    bt.push( v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_SELECT, callback(this, 'select')) );
    
    if ('point' in this.editprimitives)
      bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_POINT, callback(this, "setmode", callback(this, 'newPoint'))));
    if ('rectangle' in this.editprimitives)
      bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_RECT, callback(this, "setmode", callback(this,'newRect'))));
    if ('polyline' in this.editprimitives)
      bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_POLYLINE, callback(this, "setmode", callback(this,'newPolyline'))));
    if ('polygon' in this.editprimitives)      
      bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_POLYGON, callback(this, "setmode", callback(this,'newPolygon'))));
    if ('circle' in this.editprimitives)      
      bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_CIRCLE, callback(this, "setmode", callback(this,'newCircle'))));
    
    this.buttons_created = true;
}

ImgEdit.prototype.cancelEdit = function () {
    this.viewer.remCommandGroup(ImgViewer.BTN_TITLE_GROUP);
    this.endEdit();
    this.bt_edit.innerHTML = ImgViewer.BTN_TITLE_ANNOTATE;      
    this.viewer.need_update();
}

ImgEdit.prototype.startEdit = function () {
    if (this.editing_gobjects) return;
    this.editing_gobjects = true;
    this.viewer.renderer.svgdoc.style.zIndex = this.zindex_high;    
    this.viewer.viewer_controls_surface.style.zIndex = this.zindex_low;
    
    var v = this.viewer;
    v.renderer.setmousedown(callback(this, "mousedown"));
    this.surface_original_onmousedown = this.viewer.viewer_controls_surface.onmousedown;
    this.viewer.viewer_controls_surface.onmousedown = callback(this, "mousedown");
     
    v.renderer.setkeyhandler(callback(this, "keyhandler"));
    
    //v.renderer.setmouseup(callback(this, "mouseup"));
    //this.renderer.setmousemove(callback(this, "mousemove"));
    //v.current_view.edit_graphics = true;
    this.viewer.renderer.enable_edit (true);
}

ImgEdit.prototype.endEdit = function () {
    this.viewer.renderer.svgdoc.style.zIndex = this.zindex_low;
    this.viewer.viewer_controls_surface.style.zIndex = this.zindex_high;          
    if (this.surface_original_onmousedown)
      this.viewer.viewer_controls_surface.onmousedown = this.surface_original_onmousedown;
    
    this.viewer.renderer.setmousedown(null);
    //this.viewer.renderer.setmousemove(null);
    this.viewer.renderer.setkeyhandler(null);
    this.viewer.renderer.enable_edit (false);

    this.mode = null;
    this.current_gob = null;
    //this.viewer.current_view.edit_graphics = false;

    if (this.tageditor) {
        this.tageditor.destroy();
        delete this.tageditor;
    }
    this.editing_gobjects = false;     
}

ImgEdit.prototype.dochange = function () {
    if (this.viewer.parameters.gobjectschanged) 
        this.viewer.parameters.gobjectschanged(this.gobjects);
}


ImgEdit.prototype.save_edit = function (mode) {

    this.endEdit();
    //alert('saving ' + this.gobjects.length + ' gobjects');	

    this.viewer.image.gobjects = this.gobjects;
    this.viewer.image.save_gobjects();
}

ImgEdit.prototype.gobjectSelected = function (gob) {
    
    
    //var tg= new Tagger( , this.viewer.imageuri+'/tag' , "gobject tags", true  );
    //tg.load();
    //tg.renderHTML();
}

ImgEdit.prototype.keyhandler = function (e) {
	var unicode=e.keyCode? e.keyCode : e.charCode;
    if (unicode in this.keymap) 
        this.keymap[unicode] (e);
}
ImgEdit.prototype.delete_item =  function (e){
    var r = this.viewer.renderer;
    for (var gi = 0; gi < this.gobjects.length; gi++) {
        var gob = this.gobjects[gi];
        if (r.is_selected(gob)) {
            if (gob.uri != null 
                && !confirm( "This graphical annotation is registered in the Database.\n  Really Delete?"))   return;
            r.hideShape (this.viewer.current_view, gob);
            this.gobjects.splice(gi,1);
            gob.delete_();
            this.tageditor.destroy();
            this.tageditor = null;
        }
    }
    this.dochange();
}

ImgEdit.prototype.mousedown = function (e) {
  if (!e) e = window.event;  // IE event model  
  if (e == null) return;   
  if (this.mode) {
      var svgPoint = this.viewer.renderer.getUserCoord(e);
      this.mode (e, svgPoint.x, svgPoint.y);
      
      // this will disable all propagation while in edit selected
      if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
      else e.cancelBubble = true;                 // IE               
  }
}
/*
ImgEdit.prototype.mouseup = function (e) {
  if (!e) e = window.event;  // IE event model  
  if (e == null) return;   
  if (this.mode ) {
      var svgPoint = this.viewer.renderer.getUserCoord(e);
      this.mode (e, svgPoint.x, svgPoint.y);

      // this will disable all propagation while in edit selected      
      //if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
      //else e.cancelBubble = true;                 // IE            
  }
}
ImgEdit.prototype.mousemove = function (e) {
  if (!e) e = window.event;  // IE event model  
  if (e == null) return;   

	var svgp = this.viewer.renderer.getUserCoord(e);
  if (this.current_gob ) {
      index = this.current_gob.vertices.length-1;
      var v = this.viewer.current_view;
      var pt = v.inverseTransformPoint(svgp.x,svgp.y);
      this.current_gob.vertices[index].x = pt.x;
      this.current_gob.vertices[index].y = pt.y;
      this.current_gob.visitall ('render', [ v, this.viewer.renderer ]); 
      
      // this will disable all propagation while in edit selected      
      //if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
      //else e.cancelBubble = true;                 // IE             
  }
}
*/


ImgEdit.prototype.push_gobject = function (gob){
    this.gobjects.push(gob);
    //this.viewer.image.addgobjects(gob);
}

ImgEdit.prototype.setmode = function (mode) {
    if (mode) this.startEdit();  
    this.mode = mode;
}

ImgEdit.prototype.select = function (e, x, y) {
  this.mode = null;
  this.current_gob = null;  
  this.startEdit();   
}

ImgEdit.prototype.navigate = function (e, x, y) {
  this.endEdit();       
}

ImgEdit.prototype.newPoint = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject("point");
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new Vertex (pt.x, pt.y, v.z, v.t, null, 0));
    this.push_gobject (g);

    this.visit_render.visitall(g, [v]);
    this.dochange();
}

ImgEdit.prototype.newRect = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject("rectangle");
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new Vertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new Vertex (pt.x+50, pt.y+50, v.z, v.t, null, 1));
    this.push_gobject (g);
    this.visit_render.visitall(g, [v]);
    this.dochange();
}

ImgEdit.prototype.newPolygon = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    if (g == null) {
        g = new BQGObject("polygon");
        this.push_gobject (g);
    }
    var pt = v.inverseTransformPoint(x,y);
    var index = g.vertices.length;
    g.vertices.push (new Vertex (pt.x, pt.y, v.z, v.t, null, index));
    // Double click ends the object otherwise add points 
    this.current_gob =  (e.detail > 1)?null:g;
    this.visit_render.visitall(g, [v]);
    this.dochange();
}


ImgEdit.prototype.newPolyline = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    if (g == null) {
        g = new BQGObject("polyline");
        this.push_gobject (g);
    }
    var pt = v.inverseTransformPoint(x,y);
    var index = g.vertices.length;
    g.vertices.push (new Vertex (pt.x, pt.y, v.z, v.t, null, index));
    // Double click ends the object otherwise add points 
    this.current_gob =  (e.detail > 1)?null:g;
    this.visit_render.visitall(g, [v]);
    this.dochange();
}


ImgEdit.prototype.newCircle = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject("circle");
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new Vertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new Vertex (pt.x+50, pt.y+50, v.z, v.t, null, 1));
    this.push_gobject (g);

    this.visit_render.visitall(g, [v]);
    this.dochange();
}

/*
ImgEdit.prototype.select_object = function (gob){
    //alert('KK');
    return; // disable for now until we get better window layout
    if (this.tageditor == null) 
        this.tageditor=new TagsetViewer('imgviewer_option', 
                                        gob, 
                                        this.viewer.user_id,
                                        "default,editor(nosave)"
            );
    else
        this.tageditor.load (gob);
    
}
*/

ImgEdit.prototype.helpBox = function () {

    var msg = [ "Click an object to activate object handles",
                "Shift-click to toggle all object handles",
                "White handles move individual points",
                "Black handles move entire object",
                "Delete Key to remove object",
        ];
}


