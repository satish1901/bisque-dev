var mouser=null;

function test_visible_dim(pos, pos_view, tolerance ) {
    return !(pos!==undefined && pos!==null && !isNaN(pos) && Math.abs(pos-pos_view)>=tolerance);
}

function test_visible (pos, viewstate, tolerance_z ) {
    var proj = viewstate.imagedim.project,
        proj_gob = viewstate.gob_projection;

    tolerance_z = tolerance_z || viewstate.gob_tolerance.z || 1.0;
    tolerance_t = viewstate.gob_tolerance.t || 1.0;

    if (proj_gob==='all') {
        return true;
    } else if (proj === 'projectmaxz' || proj === 'projectminz' || proj_gob==='Z') {
        return test_visible_dim(pos.t, viewstate.t, tolerance_t);
    } else if (proj === 'projectmaxt' || proj === 'projectmint' || proj_gob==='T') {
        return test_visible_dim(pos.z, viewstate.z, tolerance_z);
    } else if (!proj || proj === 'none') {
        return (test_visible_dim(pos.z, viewstate.z, tolerance_z) &&
                test_visible_dim(pos.t, viewstate.t, tolerance_t));
    }
    return true;
}

function SVGRenderer (viewer,name) {
    var p = viewer.parameters || {};
    //this.default_showOverlay           = p.rotate          || 0;   // values: 0, 270, 90, 180
    this.default_overlayPref  = {
        enable    :false,
        position  : '',
        shape     : 'dots',
    };
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.events  = {};
    
    //overlay Editor
    var me = this;
    if (this.viewer.toolbar) { //required toolbar to initialize
        var operation_menu = this.viewer.toolbar.queryById('menu_viewer_operations')
        if (operation_menu) {
            var image = this.viewer.image;
            var resource = image ? image.uri : '';
            operation_menu.menu.add({
                    xtype  : 'menuitem',
                    itemId : 'menu_viewer_operation_overlayEditor',
                    text   : 'Overlay Editor',
                    handler: function() {
                        if (!me.overlayEditorWin) {
                            var image = this.viewer.image;
                            var resource = image? image.uri : ''
                            me.overlayEditorWin = Ext.create('BQ.overlayEditor.Window',{
                                title: 'Overlay Editor',
                                height: '80%',
                                width: '80%',
                                modal: true,
                                closeAction:'hide',
                                viewer: me.viewer,
                                phys: me.viewer.imagephys,       
                                image_resource:resource,
                            });
                        }
                        me.overlayEditorWin.show();
                    },
            });
        }
    }
}
SVGRenderer.prototype = new ViewerPlugin();

SVGRenderer.prototype.create = function (parent) {
    /*this.svgdoc = document.createElementNS(svgns, "svg");
    this.svgdoc.setAttributeNS(null, 'class', 'gobjects_surface');
    this.svgdoc.setAttributeNS(null, 'id', 'gobjects_surface');
    parent.appendChild(this.svgdoc);
    this.svgdoc.style.position = "absolute";
    this.svgdoc.style.top = "0px";
    this.svgdoc.style.left = "0px";*/

    this.overlay = document.createElementNS(svgns, "svg");
    this.overlay.setAttributeNS(null, 'class', 'gobjects_overlay');
    this.overlay.setAttributeNS(null, 'id', 'overlay');
    parent.appendChild(this.overlay);
    this.overlay.style.position = "absolute";
    this.overlay.style.top = "0px";
    this.overlay.style.left = "0px";

    this.parent = parent;
    // KGK
    // KGK THESE ARE GLOBAL Variables REQUIRED CURRENTLY BY 2D.js
    // KGK Please REVIEW and REMOVE if possible.
    //_svgElement = this.svgdoc;
    return parent;
};

SVGRenderer.prototype.onPreferences = function(pref) {
    this.loadPreferences(pref);
    var view = this.viewer.view();
    if (this.showOverlay !== 'false' && view)
        this.populate_overlay();    
};

SVGRenderer.prototype.enable_edit = function (enabled) {
    if (enabled && mouser == null) {
        mouser = new Mouser(this.svgdoc);
    } else
    if (mouser) {
        mouser.unregisterShapes();
        delete mouser;
        mouser = null;
    }

    this.viewer.current_view.edit_graphics = enabled?true:false;
    var gobs =  this.viewer.image.gobjects;
    this.visit_render.visit_array(gobs, [this.viewer.current_view]);
    this.rendered_gobjects = gobs;
};


SVGRenderer.prototype.getUserCoord = function (e ){
	return mouser.getUserCoordinate(this.svgimg, e);
};

SVGRenderer.prototype.addHandler = function (ty, cb){
    //console.log ("addHandler " + ty + " func " + cb);
    if (cb) {
        this.svgimg.addEventListener (ty, cb, false);
        this.events[ty] = cb;
    }else{
        this.svgimg.removeEventListener (ty, this.events[ty], false);
    }
};

SVGRenderer.prototype.setmousedown = function (cb ){
    this.addHandler ("mousedown", cb );
};

SVGRenderer.prototype.setmouseup = function (cb, doadd ){
    this.addHandler ("mouseup", cb);
};

SVGRenderer.prototype.setmousemove = function (cb, doadd ){
    this.addHandler ("mousemove",cb );
};

SVGRenderer.prototype.setclick = function (cb, doadd ){
    this.addHandler ("click", cb);
};

SVGRenderer.prototype.setdblclick = function (cb, doadd ){
    this.addHandler ("dblclick", cb);
};

SVGRenderer.prototype.setkeyhandler = function (cb, doadd ){
   var ty = 'keydown';
   if (cb) {
        document.documentElement.addEventListener(ty,cb,false);
        this.events[ty] = cb;
   } else {
       document.documentElement.removeEventListener(ty, this.events[ty],false);
   }
};

SVGRenderer.prototype.newImage = function () {
    var me = this;
    if (me.overlayEditorWin) {
        this.phys_inited = false;
        var image = this.viewer.image;
        var resource = image? image.uri : ''
        me.overlayEditorWin.miniViewer.resource = resource;
    }
};
/*
SVGRenderer.prototype.newImage = function () {
    removeAllChildren (this.svgdoc);
    //this.svgimg = document.createElementNS(svgns, "image");
    //this.svgdoc.appendChild(this.svgimg);

    // marker definition for vertices in polygons and polylines
    var defs = document.createElementNS(svgns, 'defs');
    var marker = document.createElementNS(svgns, 'marker');
    marker.setAttributeNS(null, 'id', 'VertexMarker');
    marker.setAttributeNS(null, 'markerWidth', '10');
    marker.setAttributeNS(null, 'markerHeight', '10');
    marker.setAttributeNS(null, "fill", 'red');
    marker.setAttributeNS(null, 'fill-opacity', '1.0');
    marker.setAttributeNS(null, 'stroke', 'white');
    marker.setAttributeNS(null, 'stroke-width', '1');
    marker.setAttributeNS(null, 'markerUnits', 'userSpaceOnUse');
    marker.setAttributeNS(null, 'refX', '3');
    marker.setAttributeNS(null, 'refY', '3');
    var circle = document.createElementNS(svgns, 'circle');
    circle.setAttributeNS(null, 'cx', '3');
    circle.setAttributeNS(null, 'cy', '3');
    circle.setAttributeNS(null, 'r', '3');
    marker.appendChild(circle);
    defs.appendChild(marker);
    this.svgdoc.appendChild(defs);
    
    // define global g object for all svg elements
    this.svggobs = document.createElementNS(svgns, "g");
    this.svgdoc.appendChild(this.svggobs);
    this.rendered_gobjects = [];

    this.svgimg = this.svgdoc;

    this.visit_render = new BQProxyClassVisitor (this);
};
*/

SVGRenderer.prototype.updateView = function (view) {
    if (this.initialized) return;
    this.initialized = true;
    this.loadPreferences(this.viewer.preferences);
    if (this.showOverlay !== 'false')
        this.populate_overlay();
        
};

SVGRenderer.prototype.appendSvg = function (gob){
    if (gob.shape)
        this.svggobs.appendChild(gob.shape.svgNode);
};


SVGRenderer.prototype.updateImage = function () {
    var viewstate = this.viewer.current_view;
    var url = this.viewer.image_url();

    /*this.svgdoc.setAttributeNS( null, 'width', viewstate.width);
    this.svgdoc.setAttributeNS( null, 'height', viewstate.height);*/

    this.overlay.setAttributeNS( null, 'width', viewstate.width);
    this.overlay.setAttributeNS( null, 'height', viewstate.height);
    this.updateTransform();
};

SVGRenderer.prototype.rerender = function (gobs, params) {
    if (!gobs)
        gobs = this.viewer.image.gobjects;
    if (!params)
        params = [this.viewer.current_view];
    this.visit_render.visit_array(gobs, params);
};

SVGRenderer.prototype.visitall = function (gobs, show) {
    params = [this.viewer.current_view, show];
    this.visit_render.visit_array(gobs, params);
};

SVGRenderer.prototype.is_selected = function (gob){
    if (gob.shape)
        return gob.shape.selected;
    return false;
};

SVGRenderer.prototype.set_select_handler = function (callback){
    this.select_callback = callback;
};

SVGRenderer.prototype.set_move_handler = function (callback){
    this.callback_move = callback;
};

SVGRenderer.prototype.default_select = function (gob) {
    if (this.select_callback)
        this.select_callback(gob);
};

SVGRenderer.prototype.default_move = function (gob) {
    if (this.callback_move)
        this.callback_move(gob);
};

SVGRenderer.prototype.viewShape = function (view, gob, move, select){
    var svgNode = gob.shape.svgNode;
    var r = this;
    var g = gob;

    this.appendSvg ( gob );
    gob.shape.init(svgNode);
    gob.shape.update_callback = move;
    gob.shape.select_callback = select;
    gob.shape.callback_data = { view:view, gob:g };
    gob.shape.show(true);
    if (view.edit_graphics === true)
        gob.shape.realize();
    gob.shape.editable(view.edit_graphics);
} ;

SVGRenderer.prototype.hideShape = function (gob, view) {
    var shape = gob.shape;
    gob.shape = undefined;
    if (shape) {
        shape.editable(false);
        shape.update_callback = null;
        shape.select_callback = null;

        shape.select(false);
        if (!view || view.edit_graphics === true) {
            shape.showHandles(false);
            shape.unrealize();
        }
        shape.show(false);
        delete shape;
    }
};

SVGRenderer.prototype.highlight = function (gob, selection) {
    // visitall to enhance on the node and its children
    visit_all(gob, function(g, args) {
        if (g.shape)
            g.shape.enhance(args[0]);
    }, selection );
};

SVGRenderer.prototype.setcolor = function (gob, color) {
    // visitall to enhance on the node and its children
    visit_all(gob, function(g, args) {
            g.color_override = args[0];
    }, color );
    this.rerender([gob]);
};

//----------------------------------------------------------------------------
// graphical primitives
//----------------------------------------------------------------------------

SVGRenderer.prototype.polygon = function (visitor, gob , viewstate, visibility) {
    this.polyline (visitor, gob, viewstate, visibility);
};

SVGRenderer.prototype.line = function (visitor, gob , viewstate, visibility) {
    this.polyline (visitor, gob, viewstate, visibility);
};

SVGRenderer.prototype.polyline = function (visitor, gob,  viewstate, visibility) {

    // Construct a SVG path element based on the visible vertices of the GOB
    var points = "";
    var ctor = Polyline;
    //if (gob.type == "polyline" )
    //    ctor = Polyline;
    if ( gob.type == "polygon" )
        ctor = Polygon;
    for (var i=0; i < gob.vertices.length; i++) {
        var pnt = gob.vertices[i];
        if (!pnt || isNaN(pnt.x) || isNaN(pnt.y) ) {
            console.log("Null vertex in gob "+gob.type+":"+gob.name);
            console.log("vertex  "+i+" of "+gob.vertices.length);
            continue;
        }

        if (!test_visible(pnt, viewstate))
            continue;

        var p = viewstate.transformPoint (pnt.x, pnt.y);
        points += p.x + ","+p.y+" ";
    }


    if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    // check points
    if (points && gob.visible ) {
        var poly = null;
        if (!gob.shape) {
            poly = document.createElementNS(svgns, gob.type==='line'?'polyline':gob.type);
            poly.setAttributeNS(null, "stroke-width", "1");
            poly.setAttributeNS(null, 'fill-opacity', 0.4);
            poly.setAttributeNS(null, 'marker-start', 'url(#VertexMarker)');
            poly.setAttributeNS(null, 'marker-mid', 'url(#VertexMarker)');
            poly.setAttributeNS(null, 'marker-end', 'url(#VertexMarker)');
            gob.shape = new ctor( poly );
        }

        poly = gob.shape.svgNode;
        poly.setAttributeNS(null, "points", points);
        if (gob.color_override) {
            poly.setAttributeNS(null, "stroke", '#'+gob.color_override);
            if (gob.type === "polygon")
                poly.setAttributeNS(null, "fill", '#'+gob.color_override);
        } else {
            poly.setAttributeNS(null, "stroke", "red");
            if (gob.type === "polygon")
                poly.setAttributeNS(null, "fill", "red");
            else
                poly.setAttributeNS(null, "fill", "none");
        }
        this.viewShape (viewstate, gob,
                        callback(this,'move_poly'),
                        callback(this,'select_poly'));
    } else {
        this.hideShape (gob, viewstate);
    }
};

SVGRenderer.prototype.move_poly = function ( state ) {
    // Extract the vertices of the gobject
    var gob = state.gob;
    var view = state.view;

    var points=gob.shape.svgNode.getAttributeNS(null,"points").split(/[\s,]+/);

    for(var i=0;i<points.length-1;i+=2){
        var x=parseInt(points[i]);
        var y=parseInt(points[i+1]);
        if (i % 2 == 0) {
            var np = view.inverseTransformPoint (x, y);
            if (i/2 >= gob.vertices.length)
                gob.vertices[i/2] = new BQVertex();
            gob.vertices[i/2].x = np.x;
            gob.vertices[i/2].y = np.y;
        }
    }
    this.default_move(gob);
};

SVGRenderer.prototype.select_poly = function ( state ) {
    var gob = state.gob;
    this.default_select(gob);
};



// SVGRenderer.prototype.path = function (visitor, gob,  viewstate) {

//     // Construct a SVG path element based on the visible vertices of the GOB
//     var d = null;
//     if (gob.type != "path" || gob.type != "polygon" )
//         return;

//     for (var i=0; i < gob.vertices.length; i++) {
//         var pnt = gob.vertices[i];
//         if (pnt == null) {
//             console.log("Null vertex in gob "+gob.type+":"+gob.name);
//             console.log("vertex  "+i+" of "+gob.vertices.length);
//             continue;
//         }
//         if (pnt.z  && pnt.z > viewstate.z )
//             continue;
//         if (pnt.t  && pnt.t > viewstate.t)
//             continue;

//         var p = viewstate.transformPoint (pnt.x, pnt.y);
//         if (d ==null)
//             d = "M" + p.x + "," +p.y;
//         else
//             d += "L" + p.x + "," +p.y;
//     }


//     // check points
//     if (d != null ) {
//         var poly = null;
//         if (gob.shape == null) {
//             poly = document.createElementNS(svgns, "path");
//             poly.setAttributeNS(null, "stroke", "red");
//             poly.setAttributeNS(null, "stroke-width", "1");
//             if ( gob.type == "polygon")
//                 poly.setAttributeNS(null, "fill", "red");
//             else
//                 poly.setAttributeNS(null, "fill", "none");
//             poly.setAttributeNS(null, 'fill-opacity', 0.4);
//             gob.shape = new Path( poly );
//         }
//         poly = gob.shape.svgNode;
//         if (gob.type== 'polygon') d+= 'Z'; // Close Path
//         poly.setAttributeNS(null, "d", d);
//         this.viewShape (viewstate, gob,
//                         callback(this,'move_path'),
//                         callback(this,'select_path'));
//     } else {
//         this.hideShape (gob, viewstate)
//     }
// }



// SVGRenderer.prototype.move_path = function ( state ) {
//     // Extract the vertices of the gobject
//     var gob = state.gob;
//     var view = state.view;


//     var path=gob.shape.svgNode.getAttributeNS(null,"d");
//     alert("PAth element needs parsing");

//     for(var i=0;i<points.length-1;i+=2){
//         var x=parseInt(points[i]);
//         var y=parseInt(points[i+1]);
//         if (i % 2 == 0) {
//             var np = view.inverseTransformPoint (x, y);
//             if (i/2 >= gob.vertices.length)
//                 gob.vertices[i/2] = new BQVertex()
//             gob.vertices[i/2].x = np.x;
//             gob.vertices[i/2].y = np.y;
//         }
//     }
//     default_move
// };

// SVGRenderer.prototype.select_path = function ( state ) {
//     var gob = state.gob;
//     var view = state.view;
//     this.default_select(gob, view) ;
// }





SVGRenderer.prototype.point = function ( visitor, gob, viewstate, visibility) {

    // Visibility of this gob (create/destroy gob.shape)
    // Create or destroy SVGElement for 2D.js
    // Update SVGElement with current view state ( scaling, etc )

    // viewstate
    // scale  : double (current scaling factor)
    // z, t, ch: current view planes (and channels)
    // svgdoc : the SVG document
    var offset_x  = viewstate.offset_x;
    var offset_y  = viewstate.offset_y;

    var pnt = gob.vertices[0];
    var visible = test_visible(pnt, viewstate);

    if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var rect = document.createElementNS(svgns, "rect");
            rect.setAttributeNS(null, "width", "8");
            rect.setAttributeNS(null, "height", "8");
            rect.setAttributeNS(null, "display", "none");
            rect.setAttributeNS(null, 'fill-opacity', 1.0);
            rect.setAttributeNS(null, 'stroke', 'black');
            rect.setAttributeNS(null, 'stroke-width', 1);
            rect.setAttributeNS(null, 'rx', 4);
            rect.setAttributeNS(null, 'ry', 4);
            gob.shape = new Pnt(rect);
        }

		// scale to size
        var p = viewstate.transformPoint (pnt.x, pnt.y);
        var rect = gob.shape.svgNode;
        if (gob.color_override)
            rect.setAttributeNS(null, "fill", '#'+gob.color_override);
        else
            rect.setAttributeNS(null, "fill", 'orangered');
		rect.setAttributeNS(null, "x", p.x -4);
		rect.setAttributeNS(null, "y", p.y -4);
        this.viewShape (viewstate, gob,
                        callback(this,"move_point"),
                        callback(this,"select_point"));

    } else {
        this.hideShape (gob, viewstate);
    }
};

SVGRenderer.prototype.move_point = function (state){
    var gob = state.gob;
    var v   = state.view;
    //gob.shape.refresh();
    var x = gob.shape.svgNode.getAttributeNS(null,"x");
    var y = gob.shape.svgNode.getAttributeNS(null,"y");

    var newpnt = v.inverseTransformPoint (x, y);
    var pnt = gob.vertices[0] ;
    pnt.x = newpnt.x;
    pnt.y = newpnt.y;
    this.default_move(gob);
};

SVGRenderer.prototype.select_point = function (state){
    var gob = state.gob;
    this.default_select(gob);
};

////////////////////////////////////////////////////////////
SVGRenderer.prototype.rectangle = function ( visitor, gob,  viewstate, visibility) {

    // Visibility of this gob (create/destroy gob.shape)
    // Create or destroy SVGElement for 2D.js
    // Update SVGElement with current view state ( scaling, etc )

    // viewstate
    // scale  : double (current scaling factor)
    // z, t, ch: current view planes (and channels)
    // svgdoc : the SVG document
    var offset_x  = viewstate.offset_x;
    var offset_y  = viewstate.offset_y;

    var pnt1 = gob.vertices[0];
    var pnt2 = gob.vertices[1];
    if (!pnt1 || !pnt2) return;
    var visible = test_visible(pnt1, viewstate);

    if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var rect = document.createElementNS(svgns, "rect");
            rect.setAttributeNS(null, 'stroke-width', 1);
            rect.setAttributeNS(null,"display", "none");
            rect.setAttributeNS(null, 'fill-opacity', 0.4);
            gob.shape = new Rectangle(rect);
        }
		// scale to size
        var p1 = viewstate.transformPoint (pnt1.x, pnt1.y);
        var p2 = viewstate.transformPoint (pnt2.x, pnt2.y);
        var rect = gob.shape.svgNode;
        rect.setAttributeNS(null, "x", p1.x);
        rect.setAttributeNS(null, "y", p1.y);
        rect.setAttributeNS(null, "width", Math.abs(p1.x-p2.x));
        rect.setAttributeNS(null, "height", Math.abs(p1.y-p2.y));
        if (gob.color_override) {
            rect.setAttributeNS(null, "stroke", '#'+gob.color_override);
            rect.setAttributeNS(null, "fill", '#'+gob.color_override);
        } else {
            rect.setAttributeNS(null, "fill", "red");
            rect.setAttributeNS(null, 'stroke', "red");
        }
        this.viewShape (viewstate, gob,
                        callback(this,'move_rectangle'),
                        callback(this,'select_rectangle'));
    } else {
        this.hideShape (gob, viewstate);
    }
};

SVGRenderer.prototype.move_rectangle = function (state){
    var gob = state.gob;
    var v   = state.view;
    //gob.shape.refresh();
    var x1 = parseInt(gob.shape.svgNode.getAttributeNS(null,"x"));
    var y1 = parseInt(gob.shape.svgNode.getAttributeNS(null,"y"));
    var w = parseInt(gob.shape.svgNode.getAttributeNS(null,"width"));
    var h = parseInt(gob.shape.svgNode.getAttributeNS(null,"height"));

    var newpnt = v.inverseTransformPoint (x1, y1);
    var pnt = gob.vertices[0] ;
    pnt.x = newpnt.x;
    pnt.y = newpnt.y;

    newpnt = v.inverseTransformPoint (x1+w, y1+h);
    pnt = gob.vertices[1] ;
    pnt.x = newpnt.x;
    pnt.y = newpnt.y;
    this.default_move(gob);
};

SVGRenderer.prototype.select_rectangle = function (state){
    var gob = state.gob;
    this.default_select(gob);
};

////////////////////////////////////////////////////////////
SVGRenderer.prototype.square = function ( visitor, gob,  viewstate, visibility) {

    // Visibility of this gob (create/destroy gob.shape)
    // Create or destroy SVGElement for 2D.js
    // Update SVGElement with current view state ( scaling, etc )

    // viewstate
    // scale  : double (current scaling factor)
    // z, t, ch: current view planes (and channels)
    // svgdoc : the SVG document
    var offset_x  = viewstate.offset_x;
    var offset_y  = viewstate.offset_y;

    var pnt1 = gob.vertices[0];
    var pnt2 = gob.vertices[1];
    if (!pnt1 || !pnt2) return;
    var visible = test_visible(pnt1, viewstate);

    if (visibility!=undefined)
        gob.visible=visibility;
    else if (gob.visible==undefined)
        gob.visible=true;

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var rect = document.createElementNS(svgns, "rect");
            rect.setAttributeNS(null, 'stroke-width', 1);
            rect.setAttributeNS(null, "display", "none");
            rect.setAttributeNS(null, 'fill-opacity', 0.4);
            gob.shape = new Square(rect);
        }
        // scale to size
        var p1 = viewstate.transformPoint (pnt1.x, pnt1.y);
        var p2 = viewstate.transformPoint (pnt2.x, pnt2.y);
        var rect = gob.shape.svgNode;
        rect.setAttributeNS(null, "x", p1.x);
        rect.setAttributeNS(null, "y", p1.y);
        rect.setAttributeNS(null, "width", Math.abs(p1.x-p2.x));
        rect.setAttributeNS(null, "height", Math.abs(p1.y-p2.y));
        if (gob.color_override) {
            rect.setAttributeNS(null, "stroke", '#'+gob.color_override);
            rect.setAttributeNS(null, "fill", '#'+gob.color_override);
        } else {
            rect.setAttributeNS(null, "fill", "red");
            rect.setAttributeNS(null, 'stroke', "red");
        }
        this.viewShape (viewstate, gob,
                        callback(this,'move_rectangle'),
                        callback(this,'select_rectangle'));
    } else {
        this.hideShape (gob, viewstate);
    }
};


////////////////////////////////////////////////////////////
SVGRenderer.prototype.circle = function ( visitor, gob,  viewstate, visibility) {

    var pnt1 = gob.vertices[0] ;
    var pnt2 = gob.vertices[1] ;
    var visible = test_visible(pnt1, viewstate);

	if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var circ = document.createElementNS( svgns, 'circle');
            circ.setAttributeNS(null, 'fill-opacity', 0.4);
            circ.setAttributeNS(null, 'stroke-width', 1);
            circ.setAttributeNS(null,"display", "none");
            gob.shape = new Circle(circ);
        }
		// scale to size
        var p1 = viewstate.transformPoint (pnt1.x, pnt1.y);
        var p2 = viewstate.transformPoint (pnt2.x, pnt2.y);
        var radius =  Math.sqrt( (p1.x - p2.x)*(p1.x - p2.x) + (p1.y - p2.y)*(p1.y - p2.y));

        var circ = gob.shape.svgNode;
        circ.setAttributeNS(null, 'cx', p1.x );
        circ.setAttributeNS(null, 'cy', p1.y);
        circ.setAttributeNS(null, 'r', radius );
        if (gob.color_override) {
            circ.setAttributeNS(null, "stroke", '#'+gob.color_override);
            circ.setAttributeNS(null, "fill", '#'+gob.color_override);
        } else {
            circ.setAttributeNS(null, 'fill', "red");
            circ.setAttributeNS(null, 'stroke', "red");
        }
        this.viewShape (viewstate, gob,
                        callback(this,"move_circle"),
                        callback(this,"select_circle"));
    } else {
        this.hideShape (gob, viewstate);
    }
};

SVGRenderer.prototype.move_circle = function (state){
    var gob = state.gob;
    var v   = state.view;
    //gob.shape.refresh();
    var x = parseInt(gob.shape.svgNode.getAttributeNS(null,"cx"));
    var y = parseInt(gob.shape.svgNode.getAttributeNS(null,"cy"));
    var r = parseInt(gob.shape.svgNode.getAttributeNS(null,"r"));

    var cpnt = v.inverseTransformPoint (x, y);
    var p1 = gob.vertices[0] ;
    p1.x = cpnt.x;
    p1.y = cpnt.y;

    var rpnt = v.inverseTransformPoint (x+r, y);
    var p2 = gob.vertices[1] ;
    p2.x = rpnt.x;
    p2.y = rpnt.y;
    this.default_move(gob);
};

SVGRenderer.prototype.select_circle = function (state){
    var gob = state.gob;
    this.default_select(gob);
};


////////////////////////////////////////////////////////////
SVGRenderer.prototype.ellipse = function ( visitor, gob,  viewstate, visibility) {
    var pnt1 = gob.vertices[0];
    var pnt2 = gob.vertices[1];
    var pnt3 = gob.vertices[2];
    var visible = test_visible(pnt1, viewstate);

    if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var circ = document.createElementNS( svgns, 'ellipse');
            circ.setAttributeNS(null, 'fill-opacity', 0.4);
            circ.setAttributeNS(null, 'stroke-width', 1);
            circ.setAttributeNS(null,"display", "none");
            gob.shape = new Ellipse(circ);
        }
		// scale to size
        var p1 = viewstate.transformPoint (pnt1.x, pnt1.y);
        var p2 = viewstate.transformPoint (pnt2.x, pnt2.y);
        var p3 = viewstate.transformPoint (pnt3.x, pnt3.y);
        var rx =  Math.sqrt( (p1.x - p2.x)*(p1.x - p2.x) + (p1.y - p2.y)*(p1.y - p2.y));
        var ry =  Math.sqrt( (p1.x - p3.x)*(p1.x - p3.x) + (p1.y - p3.y)*(p1.y - p3.y));
        var ang = Math.atan2(p1.y-p2.y, p1.x-p2.x) * 180.0/Math.PI;
        var circ = gob.shape.svgNode;

        circ.setAttributeNS(null, 'cx', p1.x );
        circ.setAttributeNS(null, 'cy', p1.y);
        circ.setAttributeNS(null, 'rx', rx );
        circ.setAttributeNS(null, 'ry', ry );
        circ.setAttributeNS(null, 'transform', "rotate(" + ang + " " + p1.x + " " + p1.y +")");
        if (gob.color_override) {
            circ.setAttributeNS(null, "stroke", '#'+gob.color_override);
            circ.setAttributeNS(null, "fill", '#'+gob.color_override);
        } else {
            circ.setAttributeNS(null, 'fill', "red");
            circ.setAttributeNS(null, 'stroke', "red");
        }
        this.viewShape (viewstate, gob,
                        callback(this,"move_ellipse"),
                        callback(this,"select_ellipse"));
    } else {
        this.hideShape (gob, viewstate);
    }
};

SVGRenderer.prototype.move_ellipse = function (state){
    var gob = state.gob;
    var v   = state.view;

    var p = gob.shape.center.point;
    var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = gob.vertices[0];
    p1.x = cpnt.x;
    p1.y = cpnt.y;

    var p = gob.shape.radiusX.point;
    var rpnt = v.inverseTransformPoint (p.x, p.y);
    var p2 = gob.vertices[1];
    p2.x = rpnt.x;
    p2.y = rpnt.y;

    var p = gob.shape.radiusY.point;
    var rpnt = v.inverseTransformPoint (p.x, p.y);
    var p3 = gob.vertices[2];
    p3.x = rpnt.x;
    p3.y = rpnt.y;

    this.default_move(gob);
};

SVGRenderer.prototype.select_ellipse = function (state){
    var gob = state.gob;
    this.default_select(gob);
};

///////////////////////////////////////
// LABEL is not really implemented .. need to extend 2D.js
// with SVG Text tag

SVGRenderer.prototype.label = function ( visitor, gob, viewstate, visibility) {

    // Visibility of this gob (create/destroy gob.shape)
    // Create or destroy SVGElement for 2D.js
    // Update SVGElement with current view state ( scaling, etc )

    // viewstate
    // scale  : double (current scaling factor)
    // z, t, ch: current view planes (and channels)
    // svgdoc : the SVG document
    var offset_x  = viewstate.offset_x;
    var offset_y  = viewstate.offset_y;
    var pnt = gob.vertices[0];

    var visible = test_visible(pnt, viewstate);

    if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    var label_text = gob.value || 'My label';

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var rect = document.createElementNS(svgns, "text");
            var innertext = document.createTextNode(label_text);
            rect.appendChild(innertext);
            rect.setAttributeNS(null, 'fill-opacity', 0.9);
            rect.setAttributeNS(null, "stroke", "black");
            rect.setAttributeNS(null, 'stroke-width', '0.5px');
            rect.setAttributeNS(null, 'stroke-opacity', 0.0);
            rect.setAttributeNS(null, 'font-size', '18px');
            rect.setAttributeNS(null, 'style', 'text-shadow: 1px 1px 4px #000000;');
            gob.shape = new Label(rect);
        }

		// scale to size
        var p = viewstate.transformPoint (pnt.x, pnt.y);
        var rect = gob.shape.svgNode;
		rect.setAttributeNS(null, "x", p.x);
		rect.setAttributeNS(null, "y", p.y);
        if (gob.color_override)
            rect.setAttributeNS(null, "fill", '#'+gob.color_override);
        else
            rect.setAttributeNS(null, "fill", "white");
        this.viewShape (viewstate, gob,
                        callback(this,"move_label"),
                        callback(this,"select_label"));

    } else {
        this.hideShape (gob, viewstate);
    }
};

SVGRenderer.prototype.move_label = function (state){
    var gob = state.gob;
    var v   = state.view;
    //gob.shape.refresh();
    var x = gob.shape.svgNode.getAttributeNS(null,"x");
    var y = gob.shape.svgNode.getAttributeNS(null,"y");

    var newpnt = v.inverseTransformPoint (x, y);
    var pnt = gob.vertices[0] ;
    pnt.x = newpnt.x;
    pnt.y = newpnt.y;
    this.default_move(gob);
};

SVGRenderer.prototype.select_label = function (state){
    var gob = state.gob;
    this.default_select(gob);
};

//----------------------------------------------------------------------------
// preferences and overlays
//----------------------------------------------------------------------------

SVGRenderer.prototype.loadPreferences = function (p) {
    //this.showOverlay  = 'showOverlay' in p ? p.showOverlay  : this.default_showOverlay;
    this.overlayPref = 'Overlay' in p ? p.Overlay  : this.default_overlayPref;
};


/*
*   Functions for finding the homography matrix
*
*/
SVGRenderer.prototype.det2D = function(x) {
    return x[0]*x[3] - x[1]*x[2];
};

SVGRenderer.prototype.det3x3 = function(x) {
    return (x[0]*x[4]*x[8] + x[1]*x[5]*x[6] + x[2]*x[3]*x[7]) - (x[2]*x[4]*x[6] + x[1]*x[3]*x[8] + x[0]*x[5]*x[7]);
};


/*
*   adj3x3
*   3 by 3 Adjugate matrix
*/
SVGRenderer.prototype.adj3x3 = function(x) {
    return [
        this.det2D([x[4],x[5],x[7],x[8]]),
        -this.det2D([x[3],x[5],x[6],x[8]]),
        this.det2D([x[3],x[4],x[6],x[7]]),
        -this.det2D([x[1],x[2],x[7],x[8]]),
        this.det2D([x[0],x[2],x[6],x[8]]),
        -this.det2D([x[0],x[1],x[6],x[7]]),
        this.det2D([x[1],x[2],x[4],x[5]]),
        -this.det2D([x[0],x[2],x[3],x[5]]),
        this.det2D([x[0],x[1],x[3],x[4]]),
    ];
};

SVGRenderer.prototype.scaleMult3x3 = function(scalar, mat) {
    return [
        scalar*mat[0],
        scalar*mat[1],
        scalar*mat[2],
        scalar*mat[3],
        scalar*mat[4],
        scalar*mat[5],
        scalar*mat[6],
        scalar*mat[7],
        scalar*mat[8],
    ];
};

SVGRenderer.prototype.inv3x3 = function(x) {
    return this.scaleMult3x3(1/this.det3x3(x), this.trans3x3(this.adj3x3(x)));
};

SVGRenderer.prototype.trans3x3 = function(x) {
    return [
        x[0],x[3],x[6],
        x[1],x[4],x[7],
        x[2],x[5],x[8],
    ]
};

SVGRenderer.prototype.matMultiply3x3 = function(x, y) {
    var z = Array(9);
    for (var i =0; i<3; ++i) {
        for (var j =0; j<3; ++j) {
            var c = 0;
            for  (var k = 0; k<3; ++k) {
                c += x[3*i + k]*y[3*k + j];
            }
            z[3*i + j] = c;
        }
    }
    return z;
};

SVGRenderer.prototype.mapMat = function(x1,y1,x2,y2,x3,y3,x4,y4) {
    var d = this.det3x3([x1,x2,x3,y1,y2,y3,1.0,1.0,1.0]);
    var x = this.det3x3([x4,x2,x3,y4,y2,y3,1.0,1.0,1.0])/d;
    var y = this.det3x3([x1,x4,x3,y1,y4,y3,1.0,1.0,1.0])/d;
    var z = this.det3x3([x1,x2,x4,y1,y2,y4,1.0,1.0,1.0])/d;
    return [
        x*x1,y*x2,z*x3,
        x*y1,y*y2,z*y3,
        x,y,z
    ];
};

SVGRenderer.prototype.fourPointsHomographyMat = function(x11,y11,x12,y12,x13,y13,x14,y14,x21,y21,x22,y22,x23,y23,x24,y24) {
    var A = this.mapMat(x11,y11,x12,y12,x13,y13,x14,y14);
    var B = this.mapMat(x21,y21,x22,y22,x23,y23,x24,y24);
    return this.matMultiply3x3(B, this.inv3x3(A));
};


SVGRenderer.prototype.distance = function(x1,y1,x2,y2) {
    return Math.sqrt(Math.pow(x1-x2,2)+Math.pow(y1-y2,2));
};

SVGRenderer.prototype.slope = function(x1,y1,x2,y2) {
    return (y2-y1)/(x2-x1);
};

SVGRenderer.prototype.radian2degrees = function(radians) {
    return radians * 180 / Math.PI;
};

SVGRenderer.prototype.updateTransform = function() {

    var view = this.viewer.view();
    if (this.overlayPref.enable && this.overlayPref.position) {
        var pattern = /([A-Za-z0-9_.]+),([A-Za-z0-9_.]+);([A-Za-z0-9_.]+),([A-Za-z0-9_.]+);([A-Za-z0-9_.]+),([A-Za-z0-9_.]+);([A-Za-z0-9_.]+),([A-Za-z0-9_.]+)/;
        var points = this.overlayPref.position.match(pattern);
        if (points && (points.length == 9)) {
            var h = this.fourPointsHomographyMat(
                0,0,view.width,0,0,view.height,view.width,view.height,
                points[1]*(view.width/view.original_width),points[2]*(view.height/view.original_height),
                points[3]*(view.width/view.original_width),points[4]*(view.height/view.original_height),
                points[5]*(view.width/view.original_width),points[6]*(view.height/view.original_height),
                points[7]*(view.width/view.original_width),points[8]*(view.height/view.original_height)
            );
            
            t = [
                h[0], h[3], 0, h[6],
                h[1], h[4], 0, h[7],
                0,       0, 1,    0,
                h[2], h[5], 0, h[8],
            ];
            
            var transform = 'matrix3d('+t.join(',')+')';
            this.overlay.style['transform-origin'] = '0 0';
            this.overlay.style['transform'] = transform;
            this.overlay.style['-webkit-transform'] = transform;
        }
    }
};

SVGRenderer.prototype.populate_overlay = function () {
    removeAllChildren (this.overlay);
    
    var gobs = document.createElementNS(svgns, "g");
    this.overlay.appendChild(gobs);
    if (this.overlayPref.enable) {
        var dx = 0; // in %
        var dy = 0; // in %    
        if (this.overlayPref.position) { //position reads p1;p2;p3;p4 p=x,y
            this.updateTransform();
        }
        
    
        if (this.overlayPref.shape === 'dots') {
            for (var x=9; x<=95; x+=9)
            for (var y=12; y<=95; y+=9) {
                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'black');
                circ.setAttributeNS(null, 'stroke-width', 2);
                circ.setAttributeNS(null, 'cx', ''+x+'%' );
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);

                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'white');
                circ.setAttributeNS(null, 'stroke-width', 1);
                circ.setAttributeNS(null, 'cx', ''+x+'%' );
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);
            }
        } else if (this.overlayPref.shape === 'dots_medium') {
            for (var x=9; x<=95; x+=9)
            for (var y=15; y<=90; y+=8) {
                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'black');
                circ.setAttributeNS(null, 'stroke-width', 2);
                circ.setAttributeNS(null, 'cx', ''+x+'%' );
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);

                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'white');
                circ.setAttributeNS(null, 'stroke-width', 1);
                circ.setAttributeNS(null, 'cx', ''+x+'%' );
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);
            }
        } else if (this.overlayPref.shape === 'dots_narrow') {
            for (var x=15; x<=90; x+=8)
            for (var y=20; y<=85; y+=7) {
                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'black');
                circ.setAttributeNS(null, 'stroke-width', 2);
                circ.setAttributeNS(null, 'cx', ''+x+'%' );
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);

                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'white');
                circ.setAttributeNS(null, 'stroke-width', 1);
                circ.setAttributeNS(null, 'cx', ''+x+'%' );
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);
            }
        } else if (this.overlayPref.shape === 'dots_custom') {
            for (var x=10; x<=90; x+=10)
            for (var y=10; y<=90; y+=10) {
                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'black');
                circ.setAttributeNS(null, 'stroke-width', 2);
                circ.setAttributeNS(null, 'cx', ''+x+'%');
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);

                var circ = document.createElementNS( svgns, 'circle');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'white');
                circ.setAttributeNS(null, 'stroke-width', 1);
                circ.setAttributeNS(null, 'cx', ''+x+'%');
                circ.setAttributeNS(null, 'cy', ''+y+'%');
                circ.setAttributeNS(null, 'r', '1%' );
                gobs.appendChild(circ);
            } 
        } else if (this.overlayPref.shape === 'grid') {
            for (var y=12; y<=95; y+=9) {
                var circ = document.createElementNS( svgns, 'line');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'black');
                circ.setAttributeNS(null, 'stroke-width', 2);
                circ.setAttributeNS(null, 'x1', '0%' );
                circ.setAttributeNS(null, 'x2', '100%' );
                circ.setAttributeNS(null, 'y1', ''+y+'%');
                circ.setAttributeNS(null, 'y2', ''+y+'%');
                gobs.appendChild(circ);

                var circ = document.createElementNS( svgns, 'line');
                circ.setAttributeNS(null, 'fill-opacity', 0.0);
                circ.setAttributeNS(null, 'fill', 'black');
                circ.setAttributeNS(null, 'stroke', 'white');
                circ.setAttributeNS(null, 'stroke-width', 1);
                circ.setAttributeNS(null, 'x1', '0%' );
                circ.setAttributeNS(null, 'x2', '100%' );
                circ.setAttributeNS(null, 'y1', ''+y+'%');
                circ.setAttributeNS(null, 'y2', ''+y+'%');
                gobs.appendChild(circ);
            }
        }
    }
    //gobs.setAttributesNS(null, )
};

Ext.define('BQ.overlayEditor.Window', {
    extend: 'Ext.window.Window',
    image_resource: '',
    layout: 'vbox',
    
    initComponent: function(config) {
        var config = config || {};
        var me = this;
        
        this.miniViewer =  Ext.create('BQ.viewer.Image',{
            width:'100%',
            height: '75%',
            flex: 6,
            resource: me.image_resource,
            parameters: {
                onlyedit: true,
                nosave: true,
                editprimitives: 'Point',
            },
            listeners: {
                'changed': function(el) {
                    var gobs = el.getGobjects();
                    if (gobs.length>4) {
                        var editor   = el.viewer.plugins_by_name.edit;
                        var renderer = el.viewer.plugins_by_name.renderer;

                        editor.remove_gobject(gobs[0]);
                        renderer.updateVisible();
                    }
                }
            },
        });
        var items = [{
            xtype: 'container',
            padding: '10px',
            html: [
                '<h1>Layout Editor</h1>',
                '<p>Place 4 points on the viewer and click Set to place the overlay over the image.</p>',
            ],
            flex: 1,
        },
            this.miniViewer, 
        ];
        
        
        var fbar = [{
            scale: 'large',
            xtype: 'button',
            margin: '0 8 0 8',
            text: 'Set',
            handler: function() {
                var gobs = me.miniViewer.getGobjects();
                var gobs = gobs.slice();
                if (gobs.length!=4) {
                    BQ.ui.notification('For points are required to set the overlay');
                    return
                }
                
                view = me.viewer.view();
                
                corners = [
                    {x:0,y:0},
                    {x:view.original_width,y:0},
                    {x:0, y:view.original_height},
                    {x:view.original_width, y:view.original_height}
                ];
                
                //select and order the points
                var points = gobs;
                /*
                var points = []
                
                for (var c=0; c<4; c++) {
                    var lengths = [];
                    for (var g = 0;g<gobs.length;g++) {
                        lengths.push(Math.sqrt(Math.pow(gobs[g].vertices[0].x-corners[c].x,2) + Math.pow(gobs[g].vertices[0].y-corners[c].y,2)));
                    }
                    var i = lengths.indexOf(Math.min.apply(Math, lengths));
                    points.push(gobs.splice(i, 1)[0]);
                }
                */
                
                //create put to the preference
                var preferenceTag = document.createElement('preference');
                
                var viewerTag = document.createElement('tag');
                viewerTag.setAttribute('name', 'Viewer');
                preferenceTag.appendChild(viewerTag);
                
                var layoutTag = document.createElement('tag');
                layoutTag.setAttribute('name', 'Overlay');
                viewerTag.appendChild(layoutTag);
                
                var enableTag = document.createElement('tag');
                enableTag.setAttribute('name', 'enable');
                enableTag.setAttribute('value', 'true');
                layoutTag.appendChild(enableTag);
                
                var positionTag = document.createElement('tag');
                positionTag.setAttribute('name', 'position');
                positionTag.setAttribute('value', points[0].vertices[0].x+','+points[0].vertices[0].y+';'+points[1].vertices[0].x+','+points[1].vertices[0].y+';'+points[2].vertices[0].x+','+points[2].vertices[0].y+';'+points[3].vertices[0].x+','+points[3].vertices[0].y);
                layoutTag.appendChild(positionTag);
                
                var shapeTag = document.createElement('tag');
                shapeTag.setAttribute('name', 'shape');
                shapeTag.setAttribute('value', 'dots_custom');
                layoutTag.appendChild(shapeTag);
                
                BQ.Preferences.updateResource(me.miniViewer.resource.resource_uniq, preferenceTag.outerHTML);
                
                //remove all the gobjects
                var editor   = me.miniViewer.viewer.plugins_by_name.edit;
                var renderer = me.miniViewer.viewer.plugins_by_name.renderer;
                var gobs = me.miniViewer.getGobjects();
                editor.remove_gobject(gobs[3]);
                editor.remove_gobject(gobs[2]);
                editor.remove_gobject(gobs[1]);
                editor.remove_gobject(gobs[0]);
                renderer.updateVisible();                
            },
        }, { //toggles disable enable of the mask
            scale: 'large',
            margin: '0 8 0 8',
            xtype: 'button',
            text: 'Disable',
            handler: function () {
                var preferenceTag = document.createElement('preference');
                
                var viewerTag = document.createElement('tag');
                viewerTag.setAttribute('name', 'Viewer');
                preferenceTag.appendChild(viewerTag);
                
                var layoutTag = document.createElement('tag');
                layoutTag.setAttribute('name', 'Overlay');
                viewerTag.appendChild(layoutTag);
                var enableTag = document.createElement('tag');
                enableTag.setAttribute('name', 'enable');
                enableTag.setAttribute('value', 'false');
                layoutTag.appendChild(enableTag);
                
                BQ.Preferences.updateResource(me.miniViewer.resource.resource_uniq, preferenceTag.outerHTML);
            },
        }, {
            scale: 'large',
            margin: '0 8 0 8',
            xtype: 'button',
            text: 'Default',
            handler: function () {
                if (BQ.Preferences.resourceXML[me.miniViewer.resource.resource_uniq]) {
                    var resourceDoc = BQ.Preferences.resourceXML[me.miniViewer.resource.resource_uniq]
                    var overlay = BQ.util.xpath_nodes(resourceDoc, '//tag[@name="Viewer"]/tag[@name="Overlay"]');
                    if (overlay.length>0) {
                        var pattern = /preference\/[0-9]+\/(.+)/;
                        var uri = overlay[0].getAttribute('uri');
                        var match = uri.match(pattern);
                        if (match.length == 2) {
                            BQ.Preferences.resetResourceTag(me.miniViewer.resource.resource_uniq, match[1]);
                        }
                    }
                    
                }
            },
        }]
        
        Ext.apply(me, {
            items: items,
            fbar: fbar,
        });
        this.callParent([config]);
        
    },
    
    
});