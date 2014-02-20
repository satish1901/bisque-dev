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

  this.keymap = { 46: callback(this, 'delete_item'),  // key delete
                   8: callback(this, 'delete_item') };
}
ImgEdit.prototype = new ViewerPlugin();

ImgEdit.prototype.newImage = function () {
    this.renderer = this.viewer.renderer;
    this.renderer.set_select_handler( callback(this, this.on_selected) );
    this.renderer.set_move_handler( callback(this, this.on_move) );
    this.gobjects = this.viewer.image.gobjects;
    this.visit_render = new BQProxyClassVisitor (this.renderer);
};

ImgEdit.prototype.updateImage = function () {

};

ImgEdit.prototype.updateView = function (view) {
    if (!this.viewer.parameters.external_edit_controls && !this.menu) {
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
                iconCls: 'icon-navigate',
                handler: this.navigate,
                scope: this,
                tooltip: 'Pan and zoom the image',
            }, {
                xtype: 'button',
                itemId: 'btnSelect',
                text: ImgViewer.BTN_TITLE_SELECT,
                scale: 'small',
                iconCls: 'icon-select',
                handler: this.select,
                scope: this,
                tooltip: 'Select a graphical annotation on the screen',
            }, {
                xtype: 'button',
                itemId: 'btnDelete',
                text: ImgViewer.BTN_TITLE_DELETE,
                scale: 'small',
                iconCls: 'icon-delete',
                handler: this.remove,
                scope: this,
                tooltip: 'Delete a graphical annotation by selecting it on the screen',
            },{
                xtype: 'displayfield',
                fieldLabel: 'Annotations:',
                cls: 'spacer',
            }, {
                xtype: 'button',
                itemId: 'btnPoint',
                hidden: !('point' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_POINT,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode('point', callback(this,'newPoint', null)); },
                scope: this,
            }, {
                xtype: 'button',
                itemId: 'btnRectangle',
                hidden: !('rectangle' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_RECT,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode('rectangle', callback(this,'newRect', null)); },
                scope: this,
            }, {
                xtype: 'button',
                itemId: 'btnPolyline',
                hidden: !('polyline' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_POLYLINE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode('polyline', callback(this,'newPolyline', null)); },
                scope: this,
            }, {
                xtype: 'button',
                itemId: 'btnPolygon',
                hidden: !('polygon' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_POLYGON,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode('polygon', callback(this,'newPolygon', null)); },
                scope: this,
            }, {
                xtype: 'button',
                itemId: 'btnCircle',
                hidden: !('circle' in this.editprimitives),
                text: ImgViewer.BTN_TITLE_CIRCLE,
                scale: 'small',
                //iconCls: 'icon-add',
                handler: function() { this.setmode('circle', callback(this,'newCircle', null)); },
                scope: this,
            });

        }
    };

};

ImgEdit.prototype.onCreateGob = function (type) {
    if (type in ImgViewer.gobFunction) {
        this.mode_primitive = null;
        var f = ImgViewer.gobFunction[type];
        this.setmode(type, callback(this, f, null));
    } else { // creating a complex gob
        // With a little more work here, we could have nested
        // complex objects.. It's hard to decide when the user
        // is nesting vs choosing a new top-level complex object.
        // for now we allow only simply objects to be nested.
        var internal_gob = callback(this, 'newPoint');
        if (this.mode_type in ImgViewer.gobFunction) {
            var f = ImgViewer.gobFunction[this.mode_type];
            internal_gob = callback(this, f);
        }
        this.setmode('complex', callback(this, 'newComplex', type, internal_gob, null));
    }
};

ImgEdit.prototype.cancelEdit = function () {
    this.endEdit();
    this.viewer.need_update();
};

ImgEdit.prototype.startEdit = function () {
    if (this.editing_gobjects) return;
    this.editing_gobjects = true;
    this.renderer.svgdoc.style.zIndex = this.zindex_high;
    this.viewer.viewer_controls_surface.style.zIndex = this.zindex_low;

    this.renderer.setmousedown(callback(this, "mousedown"));
    this.surface_original_onmousedown = this.viewer.viewer_controls_surface.onmousedown;
    this.viewer.viewer_controls_surface.onmousedown = callback(this, "mousedown");

    this.renderer.setkeyhandler(callback(this, "keyhandler"));
    this.renderer.enable_edit (true);
};

ImgEdit.prototype.endEdit = function () {
    this.renderer.svgdoc.style.zIndex = this.zindex_low;
    this.viewer.viewer_controls_surface.style.zIndex = this.zindex_high;
    if (this.surface_original_onmousedown)
      this.viewer.viewer_controls_surface.onmousedown = this.surface_original_onmousedown;

    this.renderer.setmousedown(null);
    //this.renderer.setmousemove(null);
    this.renderer.setkeyhandler(null);
    this.renderer.enable_edit (false);

    this.mode = null;
    this.current_gob = null;

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

ImgEdit.prototype.keyhandler = function (e) {
	var unicode=e.keyCode? e.keyCode : e.charCode;
    if (unicode in this.keymap)
        this.keymap[unicode] (e);
};

ImgEdit.prototype.mousedown = function (e) {
  if (!e) e = window.event;  // IE event model
  if (e == null) return;
  if (this.mode) {
      var svgPoint = this.renderer.getUserCoord(e);
      this.mode (e, svgPoint.x, svgPoint.y);

      // this will disable all propagation while in edit selected
      if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
      else e.cancelBubble = true;                 // IE
  }
};

ImgEdit.prototype.test_save_permission = function (uri) {
    var pars = this.viewer.parameters || {};
    if ('nosave' in pars)
        return false;

    // dima: a hack to stop writing into a MEX
    if (uri && uri.indexOf('/mex/')>=0) {
        BQ.ui.warning('Can\'t save annotations into a Module EXecution document...');
        return false;
    }

    // dima - REQUIRES CHANGES TO SUPPORT PROPER ACLs!!!!
    /* if (this.viewer.user)
    if (!(this.viewer.user_uri && (this.viewer.image.owner == this.viewer.user_uri))) {
        BQ.ui.notification('You do not the permission to save graphical annotations to this document...');
        // dima: write permissions need to be properly red here
        //return false;
    }*/

    return true;
};

ImgEdit.prototype.store_new_gobject = function (gob) {
    if (this.viewer.parameters.gobjectCreated)
        this.viewer.parameters.gobjectCreated(gob);

    // save to DB
    if (!this.test_save_permission(this.viewer.image.uri + '/gobject'))
        return;

    var pars = this.viewer.parameters || {};
    if (pars.onworking)
        pars.onworking('Saving annotations...');

    // create a temporary backup object holding children in order to properly hide shapes later to prevent blinking
    var bck = new BQGObject ('Temp');
    bck.gobjects = gob.gobjects;

    var me = this;
    gob.save_reload(
        this.viewer.image.uri + '/gobject',
        function(resource) {
            // show the newly returned object from the DB
            me.visit_render.visitall(gob, [me.viewer.current_view]);
            // remove all shapes from old children because save_reload replaces gobjects vector
            me.visit_render.visitall(bck, [me.viewer.current_view, false]);
            pars.ondone();
        },
        pars.onerror
    );
};

ImgEdit.prototype.remove_gobject = function (gob) {
    // dima: a hack to stop writing into a MEX
    if (gob.uri && gob.uri.indexOf('/mex/')>=0) {
        BQ.ui.warning('Can\'t delete annotation from a Module EXecution document...');
        return;
    }

    // remove rendered shape first
    this.renderer.hideShape(gob, this.viewer.current_view);

    // try to find parent gobject and if it have single child, remove parent
    //var p = gob.findParentGobject();
    var p = gob.parent;
    if (p && p instanceof BQGObject && p.gobjects.length === 1)
        gob = p;

    // remove gob
    var v = (gob.parent ? gob.parent.gobjects : undefined) || this.gobjects;
    var index = v.indexOf(gob);
    v.splice(index, 1);
    if (this.viewer.parameters.gobjectDeleted)
        this.viewer.parameters.gobjectDeleted(gob);

    // save to DB
    if (!this.test_save_permission(gob.uri))
        return;

    var pars = this.viewer.parameters || {};
    gob.delete_(pars.ondone, pars.onerror);
};

ImgEdit.prototype.on_selected = function (gob) {
    if (this.mode_type === 'select') {
        if (this.viewer.parameters.onselect)
            this.viewer.parameters.onselect(gob);
    } else if (this.mode_type === 'delete') {
        this.remove_gobject(gob);
    }
};

ImgEdit.prototype.on_move = function (gob) {
    var me = this;
    var pars = this.viewer.parameters || {};
    if (this.saving_timeout) clearTimeout (this.saving_timeout);
    this.saving_timeout = setTimeout( function() {
        me.saving_timeout=undefined;
        if (!me.test_save_permission(gob.uri))
            return;
        gob.save_me(pars.ondone, pars.onerror ); // check why save_ should not be used
    }, 1000 );
};

ImgEdit.prototype.setmode = function (type, mode_fun) {
    if (mode_fun) this.startEdit();
    this.mode = mode_fun;
    this.mode_type = type;
};

ImgEdit.prototype.select = function (e, x, y) {
    this.setmode (null);
    this.mode_type = 'select';
    this.current_gob = null;
    this.startEdit();
};

ImgEdit.prototype.remove = function (e, x, y) {
    this.setmode (null);
    this.mode_type = 'delete';
    this.current_gob = null;
    this.startEdit();
};

ImgEdit.prototype.navigate = function (e, x, y) {
    this.setmode (null);
    this.endEdit();
};

ImgEdit.prototype.newPoint = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject("point");

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g); //this.gobjects.push(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject (parent ? parent : g);
};

ImgEdit.prototype.newRect = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('rectangle');

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g); //this.gobjects.push(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new BQVertex (pt.x+50/v.scale, pt.y+50/v.scale, v.z, v.t, null, 1));

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject (parent ? parent : g);
};

ImgEdit.prototype.newPolygon = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;

    if (g == null) {
        g = new BQGObject('polygon');
        if (parent) {
            parent.addgobjects(g);
            g.edit_parent = parent;
        } else
            this.viewer.image.addgobjects(g);
    }

    var pt = v.inverseTransformPoint(x,y);
    var index = g.vertices.length;
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, index));

    // Double click ends the object otherwise add points
    this.current_gob = (e.detail > 1)?null:g;
    this.visit_render.visitall(g, [v]);
    if (!this.current_gob)
        this.store_new_gobject (g.edit_parent ? g.edit_parent : g);
};


ImgEdit.prototype.newPolyline = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;

    if (g == null) {
        g = new BQGObject('polyline');
        if (parent) {
            parent.addgobjects(g);
            g.edit_parent = parent;
        } else
            this.viewer.image.addgobjects(g);
    }
    var pt = v.inverseTransformPoint(x,y);
    var index = g.vertices.length;
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, index));

    // Double click ends the object otherwise add points
    this.current_gob = (e.detail > 1)?null:g;
    this.visit_render.visitall(g, [v]);
    if (!this.current_gob)
        this.store_new_gobject (g.edit_parent ? g.edit_parent : g);
};


ImgEdit.prototype.newCircle = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('circle');

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g); //this.gobjects.push(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new BQVertex (pt.x+50/v.scale, pt.y+50/v.scale, v.z, v.t, null, 1));

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject (parent ? parent : g);
};

ImgEdit.prototype.newLabel = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('label');

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g); //this.gobjects.push(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));

    //Ext.MessageBox.prompt('Name', 'Please enter your text:');
    g.value = 'SOME TEXT HERE';

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject (parent ? parent : g);
};

ImgEdit.prototype.newComplex = function (type, internal_gob, parent, e, x, y) {
    var v = this.viewer.current_view;
    // Check if we are constructing a polygon or other multi-point object
    // and if so then skip the creation
    if ( this.current_gob == null) {
        var g = new BQGObject (type);
        if (parent)
            parent.addgobjects (g);
        else
            this.viewer.image.addgobjects(g); //this.gobjects.push(g);
    }
    // This is tricky.. if a primitive type then it receives this g as a parent
    // if internal_gob is complex, then callback already has type, and internal_gob
    // as its first arguments
    internal_gob (g, e, x, y);
};
