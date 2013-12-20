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
ImgViewer.BTN_TITLE_DELETE   = 'Delete';
ImgViewer.BTN_TITLE_NAVIGATE = 'Navigate';
ImgViewer.BTN_TITLE_SAVE     = 'Save';

ImgViewer.BTN_TITLE_POINT    = 'Point';
ImgViewer.BTN_TITLE_RECT     = 'Rectangle';
ImgViewer.BTN_TITLE_POLYLINE = 'Polyline';
ImgViewer.BTN_TITLE_POLYGON  = 'Polygon';
ImgViewer.BTN_TITLE_CIRCLE   = 'Circle';
ImgViewer.BTN_TITLE_LABEL    = 'Label';

ImgViewer.BTN_TITLE_GROUP    = 'Annotations';

ImgViewer.gobFunction = {
    'point'   : 'newPoint',
    'rect'    : 'newRect',
    'polyline': 'newPolyline',
    'polygon' : 'newPolygon',
    'circle'  : 'newCircle',
    //'label'   : 'newLabel', // not implemented
};

function ImgEdit (viewer,name){
  this.base = ViewerPlugin;
  this.base (viewer, name);
  this.gobjects = new Array(0);
  this.mode = null;
  this.current_gob = null;
  
  this.zindex_high = 25;
  this.zindex_low  = 15;  
  
  //parse input parameters
  var primitives = 'Point,Rectangle,Polyline,Polygon,Circle,Label'.toLowerCase().split(',');
  if ('editprimitives' in this.viewer.parameters && this.viewer.parameters.editprimitives) 
    primitives = this.viewer.parameters.editprimitives.toLowerCase().split(',');
  this.editprimitives = {};
  for (var i=0; i < primitives.length; i++)
    this.editprimitives[ primitives[i] ] = '';
	
  // create interface	
  if (!this.viewer.gob_annotator)
  if ( !('noedit' in this.viewer.parameters) ) {
      //this.bt_edit = this.viewer.addCommand (ImgViewer.BTN_TITLE_ANNOTATE, callback (this, 'editImage'));
  }
  this.edit_buttons = new Array(0);
  
  this.keymap = { 46: callback(this, 'delete_item'),  // key delete
                   8: callback(this, 'delete_item') };
  
  //if ('alwaysedit' in this.viewer.parameters)
  //  this.bt_edit.style.display = "none";
}
ImgEdit.prototype = new ViewerPlugin();

ImgEdit.prototype.newImage = function () {
    this.gobjects = new Array(0);
    this.visit_render = new BQProxyClassVisitor (this.viewer.renderer);
    if ( !('noedit' in this.viewer.parameters) )
        this.editImage();   
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
};

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
            console.log ("error in rendering" + err.description);
        }
//    }
};

ImgEdit.prototype.gobjects_done = function () {
    this.gobjects = this.viewer.image.gobjects;
    this.viewer.end_wait({op: 'gobjects', message: 'Fetching gobjects'});    
    //this.viewer.gobjects = this.gobjects;
    //this.viewer.end_wait();
};

ImgEdit.prototype.updateImage = function () {
    //var gobs  = this.gobjects;
    //this.visit_render.visit_array(gobs, [this.viewer.current_view]);
    if ('alwaysedit' in this.viewer.parameters && !this.buttons_created) 
        this.editImage();      
};

ImgEdit.prototype.updateView = function (view) {
    if (!this.viewer.gob_annotator && !this.menu) {
        var v = this.viewer;
        var surf = v.viewer_controls_surface ? v.viewer_controls_surface : this.parent;
        if (surf) {
            this.menu = v.createEditMenu();
            surf.appendChild(v.editbutton);
                   
            this.menu.add({
                xtype: 'button',
                itemId: 'btnNavigate',
                text: ImgViewer.BTN_TITLE_NAVIGATE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: this.navigate,
                scope: this,            
            }, {
                xtype: 'button',                
                itemId: 'btnSelect',
                text: ImgViewer.BTN_TITLE_SELECT,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: this.select,
                scope: this,            
            }, {
                xtype: 'button',
                itemId: 'btnSave',
                hidden: ('nosave' in v.parameters),
                text: ImgViewer.BTN_TITLE_SAVE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: this.save_edit,
                scope: this,            
            }, {
                xtype: 'button',                
                itemId: 'btnDelete',
                text: ImgViewer.BTN_TITLE_DELETE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: this.delete_item,
                scope: this,           
            },{
                xtype: 'displayfield',
                fieldLabel: 'Annotations:',
                //cls: 'heading',
            }, {
                xtype: 'button',                
                itemId: 'btnPoint',
                hidden: !('point' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_POINT,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode(callback(this,'newPoint')); },
                scope: this,          
            }, {
                xtype: 'button',                
                itemId: 'btnRectangle',
                hidden: !('rectangle' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_RECT,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode(callback(this,'newRect')); },
                scope: this,          
            }, {
                xtype: 'button',                
                itemId: 'btnPolyline',
                hidden: !('polyline' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_POLYLINE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode(callback(this,'newPolyline')); },
                scope: this,          
            }, {
                xtype: 'button',                
                itemId: 'btnPolygon',
                hidden: !('polygon' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_POLYGON,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode(callback(this,'newPolygon')); },
                scope: this,          
            }, {
                xtype: 'button',                
                itemId: 'btnCircle',
                hidden: !('circle' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_CIRCLE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode(callback(this,'newCircle')); },
                scope: this,          
            });  
              
        } 
    };    
    
};

ImgEdit.prototype.editImage = function () {
  
    if (!this.viewer.gob_annotator && this.bt_edit) {  
        if (this.bt_edit.innerHTML != ImgViewer.BTN_TITLE_ANNOTATE) {
          this.cancelEdit();
          return;
        }
    }
    
    if (!(this.viewer.user_uri && (this.viewer.image.owner == this.viewer.user_uri)))
        if (!('nosave' in this.viewer.parameters)) {
            BQ.ui.notification('You are not the owner the image and may not save graphical annotations'); 
        }      
    
    var bt = this.edit_buttons;
    var v = this.viewer;    
    // For SOME weird reseaon this does not seem to work.
    //this.gobject_backup = deep_clone (this.viewer.gobjects);
    
    if (!this.viewer.gob_annotator && this.bt_edit) {      
    this.bt_edit.innerHTML = ImgViewer.BTN_TITLE_CANCEL;
    }
    
    if (this.viewer.gob_annotator) {
        if (!('nosave' in this.viewer.parameters)) 
            this.viewer.gob_annotator.on('btnSave', this.save_edit, this);        
        this.viewer.gob_annotator.on('btnNavigate', this.navigate, this);
        this.viewer.gob_annotator.on('btnSelect', this.select, this);
        this.viewer.gob_annotator.on('btnDelete', this.delete_item, this);
        this.viewer.gob_annotator.on('createGob', this.onCreateGob, this);
    } else {
        /* 
        bt.push( v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_SAVE, callback(this, "save_edit")));          
        bt.push( v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_NAVIGATE, callback(this, 'navigate')) ); 
        bt.push( v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_SELECT, callback(this, 'select')) );
        bt.push( v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_DELETE, callback(this, 'delete_item')) );       
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
        //if ('label' in this.editprimitives)
        //  bt.push(v.addCommandGroup(ImgViewer.BTN_TITLE_GROUP, ImgViewer.BTN_TITLE_LABEL, callback(this, "setmode", callback(this, 'newLabel'))));
        */    
    };
    //this.setmode(callback(this, 'newPoint'));
    this.buttons_created = true;
};

ImgEdit.prototype.onCreateGob = function (type) {
    this.gob_type = type;
    if (type in ImgViewer.gobFunction) {
        this.mode_primitive = null;
        var f = ImgViewer.gobFunction[type];
        this.setmode(callback(this, f));
    } else { // creating a complex gob
        this.mode_primitive = this.mode ? this.mode : callback(this, 'newPoint');
        this.setmode(callback(this, 'newComplex'));
    }
};

ImgEdit.prototype.cancelEdit = function () {
    this.viewer.remCommandGroup(ImgViewer.BTN_TITLE_GROUP);
    this.endEdit();
    if (!this.viewer.gob_annotator && this.bt_edit)
        this.bt_edit.innerHTML = ImgViewer.BTN_TITLE_ANNOTATE;      
    this.viewer.need_update();
};

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
};

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
};

ImgEdit.prototype.dochange = function () {
    if (this.viewer.parameters.gobjectschanged) 
        this.viewer.parameters.gobjectschanged(this.gobjects);
};


ImgEdit.prototype.save_edit = function (mode) {

    this.endEdit();
    //alert('saving ' + this.gobjects.length + ' gobjects');
    
    function findDirty(gobjects)
    {
        var dirty = [];
        
        for (var i=0; i<gobjects.length; i++)
            if (gobjects[i].dirty)
                dirty.push(gobjects[i]);
        
        return dirty;
    }
    var pars = this.viewer.parameters;
    if (pars.onworking)
        pars.onworking('Saving annotations...');
    this.viewer.image.gobjects = this.viewer.image.gobjects.concat(findDirty(this.gobjects));
    this.viewer.image.save_gobjects(pars.ondone, undefined, undefined, pars.onerror);
};

ImgEdit.prototype.gobjectSelected = function (gob) {
    
    
    //var tg= new Tagger( , this.viewer.imageuri+'/tag' , "gobject tags", true  );
    //tg.load();
    //tg.renderHTML();
};

ImgEdit.prototype.keyhandler = function (e) {
	var unicode=e.keyCode? e.keyCode : e.charCode;
    if (unicode in this.keymap) 
        this.keymap[unicode] (e);
};

ImgEdit.prototype.delete_item1 =  function (e){
    var r = this.viewer.renderer;
    var found = false;
    for (var gi = 0; gi < this.gobjects.length; gi++) {
        var gob = this.gobjects[gi];
        if (r.is_selected(gob)) {
            found = true;
            if (gob.uri != null 
                && !confirm( "This graphical annotation is registered in the Database.\n  Really Delete?"))   return;
            r.hideShape (this.viewer.current_view, gob);
            this.remove_gobject(gi);
            gob.delete_();
            //this.tageditor.destroy();
            this.tageditor = null;
        }
    }
    if (!found) confirm("You must select an object to delete");
    this.dochange();
};

ImgEdit.prototype.delete_item = function(e) {

    var gobjVisitor = Ext.create('BQGObjectVisitor');
    gobjVisitor.visit_array(this.gobjects, this);

};

Ext.define('BQGObjectVisitor', {
    extend  :   BQVisitor,
    visit   :   function(node, me)
    {
        if (node instanceof BQGObject)
            if (me.viewer.renderer.is_selected(node))
            {
                if (node.uri != null && !confirm( "This graphical annotation is registered in the database. \nReally delete?")) return;
                
                me.viewer.renderer.hideShape(me.viewer.current_view, node);
                me.remove_gobject(node);
                node.delete_();
            }
    }
});


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
};

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
    if (this.viewer.parameters.gobjectCreated) 
        this.viewer.parameters.gobjectCreated(gob);
    
    //this.viewer.image.addgobjects(gob);
};

ImgEdit.prototype.remove_gobject = function (gi){
    this.gobjects.splice(gi,1);
    
    if (this.viewer.parameters.gobjectDeleted) 
        this.viewer.parameters.gobjectDeleted(gi);
    
    //this.viewer.image.addgobjects(gob);
};

ImgEdit.prototype.setmode = function (mode) {
    if (mode) this.startEdit();  
    this.mode = mode;
};

ImgEdit.prototype.select = function (e, x, y) {
  this.mode = null;
  this.current_gob = null;  
  this.startEdit();   
};

ImgEdit.prototype.navigate = function (e, x, y) {
  this.endEdit();       
};

ImgEdit.prototype.newPoint = function (e, x, y) {
    var v = this.viewer.current_view;
    //var g = new BQGObject("point");
    
    var g = this.current_gob;    
    if (!g && !this.mode_primitive) {
        g = new BQGObject('point');
        this.push_gobject (g);
    } else if (this.mode_primitive) {
        g = g.addgobjects(new BQGObject('point'));
    }    
    
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    //this.push_gobject (g);

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.dochange();
};

ImgEdit.prototype.newRect = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;    
    if (!g && !this.mode_primitive) {
        g = new BQGObject('rectangle');
        this.push_gobject (g);
    } else if (this.mode_primitive) {
        g = g.addgobjects(new BQGObject('rectangle'));
    }       
    
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new BQVertex (pt.x+50/v.scale, pt.y+50/v.scale, v.z, v.t, null, 1));
    
    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.dochange();
};

ImgEdit.prototype.newPolygon = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    if (!g && !this.mode_primitive) {
        g = new BQGObject('polygon');
        this.push_gobject (g);
    } else if (g && !g.isPrimitive()) {
        g = g.addgobjects(new BQGObject('polygon'));
    }
    
    var pt = v.inverseTransformPoint(x,y);
    var index = g.vertices.length;
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, index));
    
    // Double click ends the object otherwise add points 
    this.current_gob =  (e.detail > 1)?null:g;
    this.visit_render.visitall(g, [v]);
    this.dochange();
};


ImgEdit.prototype.newPolyline = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    if (!g && !this.mode_primitive) {
        g = new BQGObject('polyline');
        this.push_gobject (g);
    } else if (g && !g.isPrimitive()) {
        g = g.addgobjects(new BQGObject('polyline'));
    }  
    
    var pt = v.inverseTransformPoint(x,y);
    var index = g.vertices.length;
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, index));
    
    // Double click ends the object otherwise add points 
    this.current_gob =  (e.detail > 1)?null:g;
    this.visit_render.visitall(g, [v]);
    this.dochange();
};


ImgEdit.prototype.newCircle = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;    
    if (!g && !this.mode_primitive) {
        g = new BQGObject('circle');
        this.push_gobject (g);
    } else if (this.mode_primitive) {
        g = g.addgobjects(new BQGObject('circle'));
    }        
    
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new BQVertex (pt.x+50/v.scale, pt.y+50/v.scale, v.z, v.t, null, 1));
    
    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.dochange();
};

ImgEdit.prototype.newLabel = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;    
    if (!g && !this.mode_primitive) {
        g = new BQGObject('label');
        this.push_gobject (g);
    } else if (this.mode_primitive) {
        g = g.addgobjects(new BQGObject('label'));
    }      
    
    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    
    //Ext.MessageBox.prompt('Name', 'Please enter your text:');
    g.value = 'SOME TEXT HERE';
    
    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.dochange();
};

ImgEdit.prototype.newComplex = function (e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    if (!g || !g.isPrimitive()) {
        if (!g) {
            g = new BQGObject(this.gob_type);
            this.push_gobject (g);
        } else {
            g = g.addgobjects(new BQGObject(this.gob_type));
        }     
        this.current_gob = g;
    }

    if (this.mode_primitive) 
        this.mode_primitive(e, x, y);
};

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
};


