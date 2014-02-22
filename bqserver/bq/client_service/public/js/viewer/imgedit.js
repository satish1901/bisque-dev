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

ImgEdit.prototype.createButtonsDeselect = function() {
    var c=undefined;
    for (var i=0; (c=this.button_controls[i]); i++)
        c.setSelected(false);
},

ImgEdit.prototype.createButton = function(surf, basecls, cls, cb, sel, ctrls, tooltip) {
    var btn = document.createElement('span');

    // temp fix to work similar to panojs3, will be updated to media queries
    var clsa = [basecls];
    if (isClientTouch())
        clsa.push('touch');
    else if (isClientPhone())
        clsa.push('phone');
    clsa.push(cls);
    cls = clsa.join(' ');

    btn.className = cls;
    surf.appendChild(btn);

    btn.selected = false;
    btn.base_cls = cls;
    btn.operation = cb;
    btn.setSelected = function(selected) {
        this.selected = selected;
        if (this.selected)
            this.className = this.base_cls + ' selected';
        else
            this.className = this.base_cls;
    };
    btn.setSelected(sel);

    if (!cb)
        return btn;

    var el = Ext.get(btn);
    el.on('mousedown', function(e, btn) {
        e.preventDefault();
        e.stopPropagation();
        var c=undefined;
        for (var i=0; (c=ctrls[i]); i++)
            c.setSelected(false);
        btn.setSelected(true);
        btn.operation();
    });

    if (tooltip)
    var tip = Ext.create('Ext.tip.ToolTip', {
        target: el,
        html: tooltip,
    });

    return btn;
};

ImgEdit.prototype.createEditMenu = function(surf) {
    if (!this.editbutton)
        this.editbutton = this.createButton(surf, 'editmenu', '');

    if (this.menu) return;
    this.menu = Ext.create('Ext.tip.ToolTip', {
        target: this.editbutton,
        anchor: 'top',
        anchorToTarget: true,
        cls: 'bq-viewer-menu',
        maxWidth: 460,
        anchorOffset: -10,
        autoHide: false,
        shadow: false,
        closable: true,
        layout: {
            type: 'vbox',
            //align: 'stretch',
        },
        defaults: {
            labelSeparator: '',
            labelWidth: 200,
            width: 100,
        },
        items: [{
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
        }],
    });

    var el = Ext.get(this.editbutton);
    var m = this.menu;
    el.on('click', function(){
        if (m.isVisible())
            m.hide();
        else
            m.show();
    });

};

ImgEdit.prototype.createEditControls = function(surf) {
    if (!this.button_controls) {
        this.button_controls = [];
        this.button_controls[0] = this.createButton(surf, 'editcontrol', 'btn-navigate',
            callback(this, this.navigate), true, this.button_controls, 'Pan and zoom the image');
        this.button_controls[1] = this.createButton(surf, 'editcontrol', 'btn-select',
            callback(this, this.select), false, this.button_controls, 'Select a graphical annotation on the screen' );
        this.button_controls[2] = this.createButton(surf, 'editcontrol', 'btn-delete',
            callback(this, this.remove), false, this.button_controls, 'Delete a graphical annotation by selecting it on the screen' );
    }
};

ImgEdit.prototype.updateView = function (view) {
    var v = this.viewer;
    var surf = v.viewer_controls_surface ? v.viewer_controls_surface : this.parent;
    if (surf) {
        if (!v.parameters.hide_create_gobs_menu)
            this.createEditMenu(surf);
        this.createEditControls(surf);
    }
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

    //this.renderer.setmousedown(callback(this, this.mousedown));
    //this.surface_original_onmousedown = this.viewer.viewer_controls_surface.onmousedown;
    //this.viewer.viewer_controls_surface.onmousedown = callback(this, this.mousedown);

    this.renderer.setclick(callback(this, this.mousedown));
    this.surface_original_onclick = this.viewer.viewer_controls_surface.onclick;
    this.viewer.viewer_controls_surface.onclick = callback(this, this.mousedown);


    this.renderer.setkeyhandler(callback(this, "keyhandler"));
    this.renderer.enable_edit (true);
};

ImgEdit.prototype.endEdit = function () {
    this.renderer.svgdoc.style.zIndex = this.zindex_low;
    this.viewer.viewer_controls_surface.style.zIndex = this.zindex_high;

    //if (this.surface_original_onmousedown)
    //    this.viewer.viewer_controls_surface.onmousedown = this.surface_original_onmousedown;
    //this.renderer.setmousedown(null);

    if (this.surface_original_onclick)
        this.viewer.viewer_controls_surface.onclick = this.surface_original_onclick;
    this.renderer.setclick(null);


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
    if (e.target !== this.renderer.svgdoc) return;

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

    var uri = this.viewer.image.uri + '/gobject';
    if (gob.parent && (gob.parent instanceof BQGObject) && gob.parent.uri)
        uri = gob.parent.uri;

    var me = this;
    gob.save_reload(
        uri,
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
    this.visit_render.visitall(gob, [this.viewer.current_view, false]); // make sure to hide all the children if any

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
    if (type)
        this.createButtonsDeselect();
};

ImgEdit.prototype.select = function (e, x, y) {
    this.setmode (null);
    this.mode_type = 'select';
    this.current_gob = null;
    this.startEdit();
    if (this.viewer.parameters.oneditcontrols)
        this.viewer.parameters.oneditcontrols();
};

ImgEdit.prototype.remove = function (e, x, y) {
    this.setmode (null);
    this.mode_type = 'delete';
    this.current_gob = null;
    this.startEdit();
    if (this.viewer.parameters.oneditcontrols)
        this.viewer.parameters.oneditcontrols();
};

ImgEdit.prototype.navigate = function (e, x, y) {
    this.setmode (null);
    this.endEdit();
    if (this.viewer.parameters.oneditcontrols)
        this.viewer.parameters.oneditcontrols();
};

ImgEdit.prototype.newPoint = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('point');
    parent = parent || this.global_parent;

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject ((parent && !parent.uri) ? parent : g);
};

ImgEdit.prototype.newRect = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('rectangle');
    parent = parent || this.global_parent;

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new BQVertex (pt.x+50/v.scale, pt.y+50/v.scale, v.z, v.t, null, 1));

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject ((parent && !parent.uri) ? parent : g);
};

ImgEdit.prototype.newPolygon = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    parent = parent || this.global_parent;

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
        this.store_new_gobject ((g.edit_parent && !g.edit_parent.uri) ? g.edit_parent : g);
};


ImgEdit.prototype.newPolyline = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = this.current_gob;
    parent = parent || this.global_parent;

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
        this.store_new_gobject ((g.edit_parent && !g.edit_parent.uri) ? g.edit_parent : g);
};

ImgEdit.prototype.newCircle = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('circle');
    parent = parent || this.global_parent;

    if (parent)
        parent.addgobjects(g);
    else
        this.viewer.image.addgobjects(g); //this.gobjects.push(g);

    var pt = v.inverseTransformPoint(x,y);
    g.vertices.push (new BQVertex (pt.x, pt.y, v.z, v.t, null, 0));
    g.vertices.push (new BQVertex (pt.x+50/v.scale, pt.y+50/v.scale, v.z, v.t, null, 1));

    this.current_gob = null;
    this.visit_render.visitall(g, [v]);
    this.store_new_gobject ((parent && !parent.uri) ? parent : g);
};

ImgEdit.prototype.newLabel = function (parent, e, x, y) {
    var v = this.viewer.current_view;
    var g = new BQGObject('label');
    parent = parent || this.global_parent;

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
    this.store_new_gobject ((parent && !parent.uri) ? parent : g);
};

ImgEdit.prototype.newComplex = function (type, internal_gob, parent, e, x, y) {
    parent = parent || this.global_parent;
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
