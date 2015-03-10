

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


function CanvasShape(gob, renderer) {
	this.renderer = renderer;
    if(renderer)
        this.currentLayer = renderer.currentLayer;
    this.gob = gob;
    this.postEnabled = true;
};

CanvasShape.prototype.rescale = function (scale) {
};

CanvasShape.prototype.getBbox = function () {
};

CanvasShape.prototype.update = function () {
};

CanvasShape.prototype.destroy = function () {
    this.isDestroyed = true;
    this.sprite.destroy();
    //delete this.sprite;
    //this.sprite = undefined;
};

CanvasShape.prototype.setLayer = function (layer) {
    this.currentLayer = layer;
    this.sprite.remove();
    this.currentLayer.add(this.sprite);
};


CanvasShape.prototype.move = function () {
    if(!this.postEnabled) return;
    this.moveLocal();
    this.dirty = false;
};



CanvasShape.prototype.applyColor = function () {
    var color = 'rgba(255,0,0,0.5)';
    var strokeColor = 'rgba(255,0,0,1.0)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);
};


function CanvasPolyLine(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasPolyLine.prototype = new CanvasShape();

CanvasPolyLine.prototype.getBbox = function () {
    var min = [ 9999, 9999];
    var max = [-9999,-9999];

    var points = this.sprite.points();
    if(points.length === 0) return null;

    var x = this.sprite.x();
    var y = this.sprite.y();

    var sx = this.sprite.scaleX();
    var sy = this.sprite.scaleY();


    for(var xy = 0; xy < points.length; xy+=2){
        var px = x + sx*points[xy + 0];
        var py = y + sy*points[xy + 1];
        min[0] = min[0] < px ? min[0] : px;
        min[1] = min[1] < py ? min[1] : py;
        max[0] = max[0] > px ? max[0] : px;
        max[1] = max[1] > py ? max[1] : py;
    }

    return {min: min, max: max};
};

CanvasPolyLine.prototype.init = function(gob){
    var color = 'rgba(255,0,0)';


    var scale = this.renderer.stage.scale();
    var vertices = [];
    this._closed = false;
    var poly = new Kinetic.Line({
        points: vertices,
        closed: this._closed,
        fill: color,
        fillAlpha: 0.5,
        stroke: 'red',
        strokeWidth: 1/scale.x,
    });

    gob.shape = this; //we store a reference to the shape on the gobject
    this.gob = gob;   //and extend the shape to have a reference back to the gobject
    this.sprite = poly;
    poly.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_poly'),
                             callback(this,'select_poly'));
    */
   /*if (gob.shape == null ) {

    }*/
}

CanvasPolyLine.prototype.closed = function(setter){
    this._closed = setter;
    this.sprite.closed(setter);
},

CanvasPolyLine.prototype.update = function () {
    //if(this.destroy)
    var vertices = [];
    var points = "";

    var gob = this.gob;
    var scale = this.renderer.stage.scale();
    var viewstate = this.renderer.viewer.current_view;
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

        vertices.push(pnt.x, pnt.y);
    }

    var min = [ 9999, 9999];
    var max = [-9999,-9999];
    for(var xy = 0; xy < vertices.length; xy+=2){
        var px = vertices[xy + 0];
        var py = vertices[xy + 1];
        min[0] = min[0] < px ? min[0] : px;
        min[1] = min[1] < py ? min[1] : py;
        max[0] = max[0] > px ? max[0] : px;
        max[1] = max[1] > py ? max[1] : py;
    }

    var mx = 0.5*(min[0] + max[0]);
    var my = 0.5*(min[1] + max[1]);

    for(var xy = 0; xy < vertices.length; xy+=2){
        vertices[xy + 0] -= mx;
        vertices[xy + 1] -= my;
    }

    this.applyColor();
    /*
    var color = 'rgba(255,0,0,0.5)';
    var strokeColor = 'rgba(255,0,0,1.0)';
    if(this.gob.color_override){
        c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        //color = ;
    }
    */

    //this.sprite.fill(color);
    //this.sprite.stroke(strokeColor);

    if(this._closed)
        this.sprite.strokeWidth(1.0/scale.x); //reset the moves to zero
    else
        this.sprite.strokeWidth(2.5/scale.x); //reset the moves to zero

    this.sprite.x(mx); //reset the moves to zero
    this.sprite.y(my); //reset the moves to zero
    this.sprite.scaleX(1.0);
    this.sprite.scaleY(1.0);

    this.sprite.points(vertices);
    this.currentLayer.add(this.sprite);

    if(gob.dirty)
        this.renderer.stage.draw();
}

CanvasPolyLine.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    var points = sprite.points();
    points[2*i+0] = corner.x() - sprite.x();
    points[2*i+1] = corner.y() - sprite.y();
    sprite.points(points);
}

CanvasPolyLine.prototype.onDragCreate = function(e){
    e.evt.cancelBubble = true;

    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var me = this.shape;
    var g = me.gob;
    var v = me.renderer.viewer.current_view;
    var cx = me.sprite.x();
    var cy = me.sprite.y();
    var index = g.vertices.length;

    var points = me.sprite.points();
    var ept = me.renderer.getUserCoord(e);
    var pte = v.inverseTransformPoint(ept.x, ept.y);

    var ex = pte.x - cx;
    var ey = pte.y - cy;
    points[2*index + 0] = ex;
    points[2*index + 1] = ey;

    var bx = points[0];
    var by = points[1];
    var dx = ex - bx;
    var dy = ey - by;
    if(dx*dx + dy*dy < 16){
        me.renderer.shapeCorners[0].fill('rgba(0,255,0,1)');
    } else{
        me.renderer.shapeCorners[0].fill('rgba(255,0,0,1)');
    }

    me.renderer.editLayer.batchDraw();
    //console.log(g);
}


CanvasPolyLine.prototype.moveLocal = function(){
    var points = this.sprite.points();
    var offx = this.sprite.x();
    var offy = this.sprite.y();
    var sx = this.sprite.scaleX();
    var sy = this.sprite.scaleY();
    for(var i=0;i<points.length-1;i+=2){
        var x = points[i];
        var y = points[i+1];
        if (i % 2 == 0) {
            //var np = view.inverseTransformPoint (x, y);
            if (i/2 >= this.gob.vertices.length)
                this.gob.vertices[i/2] = new BQVertex();
            this.gob.vertices[i/2].x = sx*x + offx;
            this.gob.vertices[i/2].y = sy*y + offy;
        }
    }
}

CanvasPolyLine.prototype.points = function(){
    return this.sprite.points();
}



///////////////////////////////////////////////
// ellipse:
// /--*--\
// |  *  *
// \-----/
///////////////////////////////////////////////

function CanvasEllipse(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasEllipse.prototype = new CanvasShape();

CanvasEllipse.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
    var ellipse = new Kinetic.Ellipse({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        fill: color,
        stroke: 'red',
        strokeWidth: 1/scale.x,
    });

    gob.shape = this;
    this.gob = gob;
    this.sprite = ellipse;
    ellipse.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_ellipse'),
                             callback(this,'select_ellipse'));
*/
}

CanvasEllipse.prototype.getBbox = function () {
    var ellipse = this.sprite;
    var px = ellipse.x();
    var py = ellipse.y();
    var rx = ellipse.radiusX();
    var ry = ellipse.radiusY();
    var phi = Math.PI/180*ellipse.rotation();

    var ux = rx*Math.cos(phi);
    var uy = rx*Math.sin(phi);

    var vx = ry*Math.cos(phi + Math.PI/2);
    var vy = ry*Math.sin(phi + Math.PI/2);

    var bbhw = Math.sqrt(ux*ux + vx*vx);
    var bbhh = Math.sqrt(uy*uy + vy*vy);

    return {min: [px - bbhw, py - bbhh],
            max: [px + bbhw, py + bbhh]};
};

CanvasEllipse.prototype.update = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];
    var pnt3 = this.gob.vertices[2];

    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var p2 = pnt2;//viewstate.transformPoint (pnt2.x, pnt2.y);
    var p3 = pnt3;//viewstate.transformPoint (pnt3.x, pnt3.y);
    var rx =  Math.sqrt( (p1.x - p2.x)*(p1.x - p2.x) + (p1.y - p2.y)*(p1.y - p2.y));
    var ry =  Math.sqrt( (p1.x - p3.x)*(p1.x - p3.x) + (p1.y - p3.y)*(p1.y - p3.y));
    var ang = Math.atan2(p1.y-p2.y, p1.x-p2.x) * 180.0/Math.PI;
    //var circ = gob.shape.svgNode;

    var scale = this.renderer.stage.scale();


    var color = 'rgba(255,0,0,0.5)';
    var strokeColor = 'rgba(255,0,0,1.0)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);

    var ellipse = this.sprite;

    ellipse.x(p1.x);
    ellipse.y(p1.y);
    ellipse.radiusX(rx);
    ellipse.radiusY(ry);
    ellipse.rotation(ang);
    ellipse.strokeWidth(1.0/scale.x);
    this.currentLayer.add(this.sprite);
}


CanvasEllipse.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        sprite.x(corner.x());
        sprite.y(corner.y());
    }
    else {

        var p1 = [sprite.x(), sprite.y()];
        var p2, p3;

        var t = Math.PI*this.sprite.rotation()/180;
        var cost =  Math.cos(t);
        var sint =  Math.sin(t);
        var r = this.sprite.radius();
        var px = [p1[0] + r.x*cost, p1[1] + r.x*sint];
        var py = [p1[0] - r.y*sint, p1[1] + r.y*cost];

        if(i===1){
            p2 = [corner.x(), corner.y()];
            p3 = py;
        }

        if(i===2){
            p2 = px;
            p3 = [corner.x(), corner.y()];
        }
        //viewstate.transformPoint (pnt3.x, pnt3.y);
        var rx =  Math.sqrt( (p1[0] - p2[0])*(p1[0] - p2[0]) + (p1[1] - p2[1])*(p1[1] - p2[1]));
        var ry =  Math.sqrt( (p1[0] - p3[0])*(p1[0] - p3[0]) + (p1[1] - p3[1])*(p1[1] - p3[1]));
        var ang = Math.atan2(p1[1]-p2[1], p1[0]-p2[0]) * 180.0/Math.PI;
        //var circ = gob.shape.svgNode;

        var scale = this.renderer.stage.scale();

        var ellipse = this.sprite;
        ellipse.x(p1[0]);
        ellipse.y(p1[1]);
        ellipse.radiusX(rx);
        ellipse.radiusY(ry);
        ellipse.rotation(ang + 180);
    }
}

CanvasEllipse.prototype.onDragCreate = function(e){
    e.evt.cancelBubble = true;
    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var me = this.shape;
    var g = me.gob;

    var v = me.renderer.viewer.current_view;

    var ept = me.renderer.getUserCoord(e);
    var spt = this.start;

    var pts = v.inverseTransformPoint(spt[0], spt[1]);
    var pte = v.inverseTransformPoint(ept.x, ept.y);

    var ptc = [0.5*(pts.x + pte.x), 0.5*(pts.y + pte.y)];
    var dpt = [(pte.x - pts.x), (pte.y - pts.y)];

    g.vertices[0].x = ptc[0];
    g.vertices[0].y = ptc[1];

    g.vertices[1].x = ptc[0] + 0.5*dpt[0];
    g.vertices[1].y = ptc[1];

    g.vertices[2].x = ptc[0];
    g.vertices[2].y = ptc[1] + 0.5*dpt[1];
    g.shape.update();
    me.renderer.updateBbox(me.renderer.selectedSet);
    me.renderer.editLayer.batchDraw();
    //console.log(g);
}

CanvasEllipse.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];


    p1.x = this.sprite.x();
    p1.y = this.sprite.y();

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);
    var r = this.sprite.radius();
    var px = [r.x*cost, r.x*sint];
    var py = [-r.y*sint, r.y*cost];

    var p2 = this.gob.vertices[1];
    var p3 = this.gob.vertices[2];

    p2.x = px[0] + this.sprite.x();
    p2.y = px[1] + this.sprite.y();

    p3.x = py[0] + this.sprite.x();
    p3.y = py[1] + this.sprite.y();

}

CanvasEllipse.prototype.points = function(){

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);
    var p = this.sprite.radius();
    var px = [p.x*cost, p.x*sint];
    var py = [-p.y*sint, p.y*cost];

    return [0,0, px[0], px[1], py[0], py[1]];
};



///////////////////////////////////////////////
// circle:
// /---\
// | * *
// \---/
///////////////////////////////////////////////

function CanvasCircle(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasCircle.prototype = new CanvasShape();

CanvasCircle.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
    var sprite = new Kinetic.Circle({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        fill: color,
        stroke: 'red',
        strokeWidth: 1/scale.x,
    });

    gob.shape = this;
    this.gob = gob;
    this.sprite = sprite;
    sprite.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasCircle.prototype.getBbox = function () {
    var sprite = this.sprite;
    var px = sprite.x();
    var py = sprite.y();
    var r = sprite.radius();
    return {min: [px - r, py - r],
            max: [px + r, py + r]};
};

CanvasCircle.prototype.update = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];

    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var p2 = pnt2;//viewstate.transformPoint (pnt2.x, pnt2.y);
    var r =  Math.sqrt(
        (p1.x - p2.x)*(p1.x - p2.x) +
            (p1.y - p2.y)*(p1.y - p2.y)
    );
    var ang = Math.atan2(p1.y-p2.y, p1.x-p2.x) * 180.0/Math.PI;

    //var p3 = {x: p1.x + r, y: p1.y};//viewstate.transformPoint (pnt2.x, pnt2.y);

//var circ = gob.shape.svgNode;

    var scale = this.renderer.stage.scale();


    var color = 'rgba(255,0,0,0.5)';
    var strokeColor = 'rgba(255,0,0,1.0)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);

    var sprite = this.sprite;

    sprite.x(p1.x);
    sprite.y(p1.y);
    sprite.radius(r);
    sprite.rotation(ang + 180);
    sprite.strokeWidth(1.0/scale.x);
    this.currentLayer.add(this.sprite);
}


CanvasCircle.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        sprite.x(corner.x());
        sprite.y(corner.y());
    }
    else if (i === 1){

        var p1 = [sprite.x(), sprite.y()];
        var p2 = [corner.x(), corner.y()];
        //viewstate.transformPoint (pnt3.x, pnt3.y);
        var r =  Math.sqrt( (p1[0] - p2[0])*(p1[0] - p2[0]) + (p1[1] - p2[1])*(p1[1] - p2[1]));
        var ang = Math.atan2(p1[1]-p2[1], p1[0]-p2[0]) * 180.0/Math.PI;
        var scale = this.renderer.stage.scale();

        var sprite = this.sprite;
        sprite.x(p1[0]);
        sprite.y(p1[1]);
        sprite.radius(r);
        sprite.rotation(ang + 180);
        //ellipse.rotation(ang + 180);
    }
}


CanvasCircle.prototype.onDragCreate = function(e){
    e.evt.cancelBubble = true;
    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var me = this.shape;
    var g = me.gob;

    var v = me.renderer.viewer.current_view;

    var ept = me.renderer.getUserCoord(e);
    var spt = this.start;

    var pts = v.inverseTransformPoint(spt[0], spt[1]);
    var pte = v.inverseTransformPoint(ept.x, ept.y);

    g.vertices[0].x = pts.x;
    g.vertices[0].y = pts.y;

    g.vertices[1].x = pte.x;
    g.vertices[1].y = pte.y;

    g.shape.update();
    me.renderer.updateBbox(me.renderer.selectedSet);
    me.renderer.editLayer.batchDraw();
    //console.log(g);
}

CanvasCircle.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];
    var p2 = this.gob.vertices[1];

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);
    var r = this.sprite.radius();
    var px = [r*cost, r*sint];
    //var py = [-r.y*sint, r.y*cost];

    p1.x = this.sprite.x();
    p1.y = this.sprite.y();

    p2.x = p1.x + px[0];
    p2.y = p1.y + px[1];
}

CanvasCircle.prototype.points = function(){

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);
    var r = this.sprite.radius();
    var px = [r*cost, r*sint];
    //var py = [-r*sint, r*cost];

    return [0,0, px[0], px[1]];
}



///////////////////////////////////////////////
// Point
//
//  *
//
///////////////////////////////////////////////

function CanvasPoint(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasPoint.prototype = new CanvasShape();

CanvasPoint.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
    var sprite = new Kinetic.Circle({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        fill: color,
        stroke: 'red',
        strokeWidth: 1.5/scale.x,
    });

    gob.shape = this;
    this.gob = gob;
    this.sprite = sprite;
    sprite.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasPoint.prototype.getBbox = function () {
    var sprite = this.sprite;
    var px = sprite.x();
    var py = sprite.y();
    var r = 2.0/this.renderer.stage.scale().x;
    return {min: [px - r, py - r],
            max: [px + r, py + r]};
};

CanvasPoint.prototype.update = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];

    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    var scale = this.renderer.stage.scale();

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var r = 3.0/scale.x;

    var color = 'rgba(255,0,0,1.0)';
    var strokeColor = 'rgba(255,0,0,0.5)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);

    var sprite = this.sprite;

    sprite.x(p1.x);
    sprite.y(p1.y);
    sprite.radius(r);
    sprite.strokeWidth(6.0/scale.x);
    this.currentLayer.add(this.sprite);
}


CanvasPoint.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;

    var sprite = this.sprite;
    //var points = sprite.points();

    sprite.x(corner.x());
    sprite.y(corner.y());
}


CanvasPoint.prototype.moveLocal = function(){
    var p1 = this.gob.vertices[0];
    p1.x = this.sprite.x();
    p1.y = this.sprite.y();
}

CanvasPoint.prototype.points = function(){
    return [0,0];
}


///////////////////////////////////////////////
// label
//
//  *
//   \_____label
///////////////////////////////////////////////

function CanvasLabel(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasLabel.prototype = new CanvasShape();

CanvasLabel.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
    this.sprite = new Kinetic.Circle({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        fill: color,
        stroke: 'red',
        strokeWidth: 1.5/scale.x,
    });
    this.text = new Kinetic.Text({
        text: gob.value,
        fontSize: 14/scale.x,
        fill: 'red',
    });;
    gob.shape = this;
    this.gob = gob;
    this.sprite.shape = this;
    this.text.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}


CanvasLabel.prototype.setLayer = function (layer) {
    this.currentLayer = layer;
    this.sprite.remove();
    this.text.remove();
    this.arrow.remove();

    this.currentLayer.add(this.sprite);
    this.currentLayer.add(this.text);
    this.currentLayer.add(this.arrow);

    this.sprite.shapeId = 0;
    this.text.shapeId = -1;

};


CanvasLabel.prototype.getBbox = function () {
    var sprite = this.sprite;
    var px = sprite.x();
    var py = sprite.y();
    var r = 2.0/this.renderer.stage.scale().x;
    var w = this.text.width();
    var h = this.text.height();
    var x0 = px;
    var x1 = px + this.offset.x;
    var x2 = px + this.offset.x + w;
    var xmin = Math.min(x0, Math.min(x1, x2));
    var xmax = Math.max(x0, Math.max(x1, x2));

    var y0 = py;
    var y1 = py + this.offset.y;
    var y2 = py + this.offset.y + h;
    var ymin = Math.min(y0, Math.min(y1, y2));
    var ymax = Math.max(y0, Math.max(y1, y2));

    return {min: [xmin, ymin],
            max: [xmax, ymax]};
};

CanvasLabel.prototype.updateArrow = function(){
    var scale = this.renderer.stage.scale();

    if(!this.arrow)
        this.arrow = new Kinetic.Line({
            points: [0,0, 1,0, 1,1],
            closed: false,
            stroke: 'red',
            strokeWidth: 1/scale.x,
        });

    var dx = this.offset.x;
    var dy = this.offset.y;
    var w = this.text.width();
    if(this.offset.x + 0.5*w < 0)
        dx += w;
    var tip = 0.75*dx;
    if (this.offset.x < 0 && this.offset.x + 0.5*w > 0)
        tip -= 10;
    else if (this.offset.x < 0 && this.offset.x + w > 0)
        tip += 10;

    if(dx*dx + dy*dy > 25){
        this.currentLayer.add(this.arrow);
        this.arrow.moveToBottom();
        var points = this.arrow.points();
        points[0] = this.sprite.x();
        points[1] = this.sprite.y();

        points[2] = this.sprite.x() + tip;
        points[3] = this.sprite.y() + dy + 0.5*this.text.height();

        points[4] = this.sprite.x() + dx;
        points[5] = this.sprite.y() + dy + 0.5*this.text.height();
    }

    else this.arrow.remove();
};

CanvasLabel.prototype.update = function () {
    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];

    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    var scale = this.renderer.stage.scale();

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var r = 3.0/scale.x;

    var color = 'rgba(255,0,0,1.0)';
    var strokeColor = 'rgba(255,0,0,0.5)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);

    var sprite = this.sprite;
    var text = this.text;
    if(!this.offset)
        this.offset = {x: 4, y: 0};

    if(this.gob.vertices.length > 1){
        var p2 = this.gob.vertices[1];
        this.offset.x = (p2.x - p1.x);
        this.offset.y = (p2.y - p1.y);
    }


    text.x(p1.x + this.offset.x);
    text.y(p1.y + this.offset.y);

    text.fontSize(14/scale.x);
    sprite.x(p1.x);
    sprite.y(p1.y);
    sprite.radius(r);
    sprite.strokeWidth(6.0/scale.x);
    this.updateArrow();
    this.currentLayer.add(this.sprite);
    this.currentLayer.add(this.text);
}


CanvasLabel.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    //var points = sprite.points();
    var text = this.text;

    var p1 = this.gob.vertices[0];
    console.log('drag');
    if(i == -1){ //this means the text itself is being passed as a manipulator

        text.x(corner.x());
        text.y(corner.y());

        sprite.x(corner.x() - this.offset.x);
        sprite.y(corner.y() - this.offset.y);
    }

    if(i == 0){
        text.x(corner.x() + this.offset.x);
        text.y(corner.y() + this.offset.y);

        sprite.x(corner.x());
        sprite.y(corner.y());
    }

    if(i == 1){

        text.x(this.sprite.x() + this.offset.x);
        text.y(this.sprite.y() + this.offset.y);

        this.offset.x = corner.x() - this.sprite.x();
        this.offset.y = corner.y() - this.sprite.y();
    }
    this.updateArrow();
}


CanvasLabel.prototype.moveLocal = function(){
    var p1 = this.gob.vertices[0];
    p1.x = this.sprite.x();
    p1.y = this.sprite.y();
    if(this.gob.vertices[0].length > 1){
        var p2 = this.gob.vertices[1];
        p2.x = this.sprite.x() + this.offset.x;
        p2.y = this.sprite.y() + this.offset.y;
    }
}

CanvasLabel.prototype.points = function(){
    return [0,0, this.offset.x, this.offset.y];
}


///////////////////////////////////////////////
// rectangle:
// *------------
// |           |
// ------------*
///////////////////////////////////////////////

function CanvasRectangle(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasRectangle.prototype = new CanvasShape();

CanvasRectangle.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
    var rect = new Kinetic.Rect({
        fill: color,
        stroke: 'red',
        strokeWidth: 1/scale.x,
    });

    gob.shape = this;
    this.gob = gob;
    this.sprite = rect;
    rect.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasRectangle.prototype.getBbox = function () {
    var rect = this.sprite;
    var px = rect.x();
    var py = rect.y();
    var w = rect.width();
    var h = rect.height();
    var xmin = Math.min(px, px + w);
    var xmax = Math.max(px, px + w);
    var ymin = Math.min(py, py + h);
    var ymax = Math.max(py, py + h);

    return {min: [xmin, ymin],
            max: [xmax, ymax]};
};

CanvasRectangle.prototype.update = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];


    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var p2 = pnt2;//viewstate.transformPoint (pnt2.x, pnt2.y);
    var w = p2.x - p1.x;
    var h = p2.y - p1.y;
    this.sprite.x(p1.x);
    this.sprite.y(p1.y);
    this.sprite.width(w);
    this.sprite.height(h);

    var scale = this.renderer.stage.scale();


    var color = 'rgba(255,0,0,0.5)';
    var strokeColor = 'rgba(255,0,0,1.0)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);

    this.sprite.strokeWidth(1.0/scale.x);
    this.currentLayer.add(this.sprite);
}


CanvasRectangle.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;

    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        sprite.x(corner.x());
        sprite.y(corner.y());
    }
    else if (i === 1){


        var p1 = [sprite.x(), sprite.y()];
        var dim = [corner.x() - sprite.x(),
                   corner.y() - sprite.y()];
        var rect = this.sprite;
        rect.x(p1[0]);
        rect.y(p1[1]);
        rect.width(dim[0]);
        rect.height(dim[1]);
    }
}


CanvasRectangle.prototype.onDragCreate = function(e){
    e.evt.cancelBubble = true;
    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var me = this.shape;
    var g = me.gob;

    var v = me.renderer.viewer.current_view;

    var ept = me.renderer.getUserCoord(e);
    var spt = this.start;

    var pts = v.inverseTransformPoint(spt[0], spt[1]);
    var pte = v.inverseTransformPoint(ept.x, ept.y);

    var ptc = [0.5*(pts.x + pte.x), 0.5*(pts.y + pte.y)];
    var dpt = [(pte.x - pts.x), (pte.y - pts.y)];

    g.vertices[0].x = pts.x;
    g.vertices[0].y = pts.y;

    g.vertices[1].x = ptc[0] + 0.5*dpt[0];
    g.vertices[1].y = ptc[1] + 0.5*dpt[1];

    g.shape.update();
    me.renderer.updateBbox(me.renderer.selectedSet);
    me.renderer.editLayer.batchDraw();
    //console.log(g);
}

CanvasRectangle.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];
    var p2 = this.gob.vertices[1];


    p1.x = this.sprite.x();
    p1.y = this.sprite.y();

    p2.x = p1.x + this.sprite.width();
    p2.y = p1.y + this.sprite.height();

}

CanvasRectangle.prototype.points = function(){
    return [0,0, this.sprite.width(),this.sprite.height()];
}



///////////////////////////////////////////////
// sqyare:
// *-----
// |    |
// -----*
///////////////////////////////////////////////

function CanvasSquare(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasSquare.prototype = new CanvasShape();

CanvasSquare.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
    var rect = new Kinetic.Rect({
        fill: color,
        stroke: 'red',
        strokeWidth: 1/scale.x,
    });

    gob.shape = this;
    this.gob = gob;
    this.sprite = rect;
    rect.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasSquare.prototype.getBbox = function () {
    var rect = this.sprite
    var px = rect.x();
    var py = rect.y();
    var w = rect.width();
    var h = rect.height();
    var xmin = Math.min(px, px + w);
    var xmax = Math.max(px, px + w);
    var ymin = Math.min(py, py + h);
    var ymax = Math.max(py, py + h);

    return {min: [xmin, ymin],
            max: [xmax, ymax]};

};

CanvasSquare.prototype.update = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];


    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var p2 = pnt2;//viewstate.transformPoint (pnt2.x, pnt2.y);
    var w = p2.x - p1.x;
    var h = p2.y - p1.y;
    var min = Math.min(w, h);
    this.sprite.x(p1.x);
    this.sprite.y(p1.y);
    this.sprite.width(min);
    this.sprite.height(min);

    var scale = this.renderer.stage.scale();


    var color = 'rgba(255,0,0,0.5)';
    var strokeColor = 'rgba(255,0,0,1.0)';
    if(this.gob.color_override){
        var c = Kinetic.Util._hexToRgb('#' + this.gob.color_override);
        color = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            0.5+')';
        strokeColor = 'rgba('+
            c.r+','+
            c.g+','+
            c.b+','+
            1.0+')';
        //color = ;
    }

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);

    this.sprite.strokeWidth(1.0/scale.x);
    this.currentLayer.add(this.sprite);
}


CanvasSquare.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    //if(!i) return;
    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        sprite.x(corner.x());
        sprite.y(corner.y());
    }
    else if (i === 1){
        var p1 = [sprite.x(), sprite.y()];
        var dim = [corner.x() - sprite.x(),
                   corner.y() - sprite.y()];
        var rect = this.sprite;
        var min = Math.min(dim[0],dim[1]);
        rect.x(p1[0]);
        rect.y(p1[1]);
        rect.width(min);
        rect.height(min);
    }
}


CanvasSquare.prototype.onDragCreate = function(e){
    e.evt.cancelBubble = true;
    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var me = this.shape;
    var g = me.gob;

    var v = me.renderer.viewer.current_view;

    var ept = me.renderer.getUserCoord(e);
    var spt = this.start;

    var pts = v.inverseTransformPoint(spt[0], spt[1]);
    var pte = v.inverseTransformPoint(ept.x, ept.y);

    var ptc = [0.5*(pts.x + pte.x), 0.5*(pts.y + pte.y)];
    var dpt = [(pte.x - pts.x), (pte.y - pts.y)];

    var min = Math.min(dpt[0],dpt[1]);
    g.vertices[0].x = pts.x;
    g.vertices[0].y = pts.y;

    g.vertices[1].x = ptc[0] + 0.5*min;
    g.vertices[1].y = ptc[1] + 0.5*min;

    g.shape.update();
    me.renderer.updateBbox(me.renderer.selectedSet);
    me.renderer.editLayer.batchDraw();
    //console.log(g);
}

CanvasSquare.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];
    var p2 = this.gob.vertices[1];


    p1.x = this.sprite.x();
    p1.y = this.sprite.y();

    p2.x = p1.x + this.sprite.width();
    p2.y = p1.y + this.sprite.height();

}

CanvasSquare.prototype.points = function(){
    return [0,0, this.sprite.width(),this.sprite.height()];
}


function CanvasControl(viewer, element) {
  this.viewer = viewer;

  if (typeof element == 'string')
    this.svg_element = document.getElementById(element);
  else
    this.svg_element = element;

  this.viewer.viewer.tiles.tiled_viewer.addViewerZoomedListener(this);
  this.viewer.viewer.tiles.tiled_viewer.addViewerMovedListener(this);
}

CanvasControl.prototype.viewerMoved = function(e) {
    //this.viewer.stage.setPosition({x: e.x, y: e.y});
    //var canvas = this.viewer.currentLayer.getCanvas()._canvas;
    this.viewer.stage.content.style.left = e.x + 'px';
    this.viewer.stage.content.style.top = e.y + 'px';

};

CanvasControl.prototype.viewerZoomed = function(e) {
    this.viewer.stage.content.style.left = e.x + 'px';
    this.viewer.stage.content.style.top = e.y + 'px';
    this.viewer.stage.scale({x:e.scale,y:e.scale});
    //this.viewer.stage.batchDraw();
    //this.viewer.stage.removeChildren();


    //this.viewer.stage.setScale(e.scale);

    /*
    this.svg_element.style.left = e.x + 'px';
    this.svg_element.style.top  = e.y + 'px';

    var current_size = this.viewer.currentImageSize();
    this.svg_element.style.width  = current_size.width + 'px';
    this.svg_element.style.height = current_size.height + 'px';
    */
    //var svgembed = document.getElementById( 'svgembed' );
    //svgembed.style.width = level.width + 'px';
    //svgembed.style.height  = level.height + 'px';
};


function CanvasRenderer (viewer,name) {
    var p = viewer.parameters || {};
    //this.default_showOverlay           = p.rotate          || 0;   // values: 0, 270, 90, 180
    this.default_showOverlay   = false;

    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.events  = {};
}
CanvasRenderer.prototype = new ViewerPlugin();

CanvasRenderer.prototype.create = function (parent) {

    //this.canvas = document.createElement("canvas");
    //parent.appendChild(this.canvas);
    this.mode = 'select';
    this.shapes = {
        'ellipse': CanvasEllipse,
        'circle': CanvasCircle,
        'point': CanvasPoint,
        'polygon': CanvasPolyLine,
        'rectangle': CanvasRectangle,
        'square': CanvasSquare,
        'label': CanvasLabel,
    };

    this.stage = new Kinetic.Stage({
        container: parent,
        width: 100,
        height: 100, //set these later
    });

    this.stage.content.style.setProperty('z-index', 15);

    this.initShapeLayer();
    this.initEditLayer();
    this.initSelectLayer();
};


CanvasRenderer.prototype.initShapeLayer = function(){
    this.currentLayer = new Kinetic.Layer();
    this.stage.add(this.currentLayer);
};

CanvasRenderer.prototype.initEditLayer = function(){
    var me = this;
    this.editLayer = new Kinetic.Layer();
    this.stage.add(this.editLayer);
    this.editLayer.moveToTop();
    this.initUiShapes();
};

CanvasRenderer.prototype.initSelectLayer = function(){
    var me = this;
    this.selectLayer = new Kinetic.Layer();
    this.stage.add(this.selectLayer);
    this.selectLayer.moveToBottom();

    this.selectedSet = [];

    this.lassoRect = new Kinetic.Rect({
        fill: 'rgba(200,200,200,0.1)',
        stroke: 'grey',
        strokeWidth: 1,
        listening: false,
    });

    this.selectRect = new Kinetic.Rect({
        fill: 'rgba(0,0,0,0.0)',
        stroke: 'none',
        width: this.stage.width(),
        height: this.stage.height(),
        listening: true,
    });
    this.selectLayer.add(this.selectRect);


    var mousemove = function(e) {
        if(me.mode != 'edit') return;
        var evt = e.evt;
        var scale = me.stage.scale();
        var x = evt.offsetX/scale.x;
        var y = evt.offsetY/scale.y;
        var x0 = me.lassoRect.x();
        var y0 = me.lassoRect.y();

        me.lassoRect.width((x - x0));
        me.lassoRect.height((y - y0));
        var lassoRect = me.lassoRect;
        me.editLayer.draw();
    };

    var mousedown = function(e){
        if(me.mode != 'edit') return;
        me.unselect(me.selectedSet);

        var evt = e.evt;
        var scale = me.stage.scale()
        var x = evt.offsetX/scale.x;
        var y = evt.offsetY/scale.y;
        me.currentLayer.draw();
        me.editLayer.draw();
        me.selectedSet = []; //clear out current selection set

        me.editLayer.add(me.lassoRect);
        me.selectLayer.moveToTop();

        me.lassoRect.width(0);
        me.lassoRect.height(0);
        me.lassoRect.x(x);
        me.lassoRect.y(y);

        me.selectRect.on('mousemove', mousemove);
    }

    var mouseup = function(e) {
        console.log('up');
        if(me.mode != 'edit') return;
        me.selectRect.off('mousemove');
        me.lassoRect.remove();
        me.selectLayer.moveToBottom();

        var x0 = me.lassoRect.x();
        var y0 = me.lassoRect.y();
        var x1 = me.lassoRect.width() + x0;
        var y1 = me.lassoRect.height() + y0;
        me.lassoSelect(x0,y0,x1,y1);
        me.select(me.selectedSet);
        me.default_select(me.selectedSet);
        me.editLayer.draw();

    } ;

    this.selectRect.on('mousedown', mousedown);
    this.selectRect.on('mouseup', mouseup);

    this.selectLayer.draw();
};

CanvasRenderer.prototype.lassoSelect = function(x0,y0, x1,y1){
    var me = this;
    var shapes = this.currentLayer.getChildren();
    shapes.forEach(function(e,i,d){
        var x = e.x();
        var y = e.y();
        if(!e.shape) return;
        var bbox = e.shape.getBbox();
        if(!bbox) return;
        if(bbox.min[0] > x0 && bbox.min[1] > y0 &&
           bbox.max[0] < x1 && bbox.max[1] < y1){
            me.addToSelectedSet(e.shape);
        }
    });
}

CanvasRenderer.prototype.initUiShapes = function(){

    this.bbRect = new Kinetic.Rect({
        fill: 'rgba(255,255,255,0.0)',
        stroke: 'grey',
        strokeWidth: 1,
        listening: false,
    });
    this.bbCorners = []
    for(var i = 0; i < 4; i++){
        this.bbCorners.push(
        new Kinetic.Rect({
            width: 6,
            height: 6,
            fill: 'grey',
            listening: true
        }));
    }
    this.bbCorners.forEach(function(e,i,d){
        e.setDraggable(true);
    });
};


CanvasRenderer.prototype.enable_edit = function (enabled) {

    this.viewer.current_view.edit_graphics = enabled?true:false;
    var gobs =  this.viewer.image.gobjects;
    this.visit_render.visit_array(gobs, [this.viewer.current_view]);

    this.editLayer.moveToTop();
    this.rendered_gobjects = gobs;
};


CanvasRenderer.prototype.getUserCoord = function (e ){
    if(e.evt)
        return {x: e.evt.offsetX, y: e.evt.offsetY}
    return {x: e.offsetX, y: e.offsetY};
	//return mouser.getUserCoordinate(this.svgimg, e);
    //the old command got the e.x, e.y and applied a transform to localize them to the svg area using a matrix transform.
};

CanvasRenderer.prototype.addHandler = function (ty, cb){
    //console.log ("addHandler " + ty + " func " + cb);
    if (cb) {
        //tremovehis.svgimg.addEventListener (ty, cb, false);
        this.stage.on(ty,cb);
        this.events[ty] = cb;
    }else{
        this.stage.off(ty);
        //this.svgimg.removeEventListener (ty, this.events[ty], false);
    }
};

CanvasRenderer.prototype.setMode = function (mode){
    this.mode = mode;
    if(mode == 'add') {
        this.lassoRect.width(0);
        this.lassoRect.height(0);
        this.selectLayer.moveToBottom();
        this.editLayer.moveToTop();
    }

};

CanvasRenderer.prototype.setmousedown = function (cb ){
    this.addHandler ("mousedown", cb );
};

CanvasRenderer.prototype.setmouseup = function (cb, doadd ){
    this.addHandler ("mouseup", cb);
};

CanvasRenderer.prototype.setmousemove = function (cb, doadd ){
    this.addHandler ("mousemove",cb );
};


CanvasRenderer.prototype.setdragstart = function (cb ){
    this.addHandler ("dragstart", cb );
};

CanvasRenderer.prototype.setdragmove = function (cb ){
    this.addHandler ("dragmove", cb );
};

CanvasRenderer.prototype.setdragend = function (cb ){
    this.addHandler ("dragend", cb );
};

CanvasRenderer.prototype.setclick = function (cb, doadd ){
    this.addHandler ("click", cb);
};

CanvasRenderer.prototype.setdblclick = function (cb, doadd ){
    this.addHandler ("dblclick", cb);
};

CanvasRenderer.prototype.setkeyhandler = function (cb, doadd ){
   var ty = 'keydown';
   if (cb) {
        document.documentElement.addEventListener(ty,cb,false);
        this.events[ty] = cb;
   } else {
       document.documentElement.removeEventListener(ty, this.events[ty],false);
   }
};

CanvasRenderer.prototype.newImage = function () {
    var w = this.viewer.imagediv.offsetWidth;
    var h = this.viewer.imagediv.offsetHeight;

    this.rendered_gobjects = [];
    this.visit_render = new BQProxyClassVisitor (this);
};

CanvasRenderer.prototype.updateView = function (view) {
    if (this.initialized) return;
    this.initialized = true;
//    this.loadPreferences(this.viewer.preferences);
//    if (this.showOverlay !== 'false')
//        this.populate_overlay(this.showOverlay);
};

CanvasRenderer.prototype.appendSvg = function (gob){
    if (gob.shape)
        this.svggobs.appendChild(gob.shape.svgNode);
};


CanvasRenderer.prototype.updateImage = function (e) {
    var viewstate = this.viewer.current_view;
    var url = this.viewer.image_url();
    var scale = this.viewer.current_view.scale;
    var x = this.viewer.tiles.tiled_viewer.x;
    var y = this.viewer.tiles.tiled_viewer.y;
    var z = this.viewer.tiles.cur_z;
    this.stage.scale(scale);

    if(this.selectedSet.length> 0){
        if(this.selectedSet[0].gob.vertices[0].z != z){
            this.unselect(this.selectedSet);
            this.selectedSet = [];
        }
    }
    this.stage.content.style.left = x + 'px';
    this.stage.content.style.top = y + 'px';

    this.stage.setWidth(viewstate.width);
    this.stage.setHeight(viewstate.height);
    //this.stage.content.style.setProperty('z-index', 15);
    this.currentLayer.removeChildren();

    if(!this.addedListeners){
        this.addedListeners = true;
        this.myCanvasListener = new CanvasControl( this, this.stage );
    }

    var gobs = this.viewer.image.gobjects;
    this.visit_render.visit_array(gobs, [this.viewer.current_view]);
    this.rendered_gobjects = gobs;

    this.selectRect.width(this.stage.width());
    this.selectRect.height(this.stage.height());
    this.updateBbox(this.selectedSet);
    this.stage.batchDraw();
};

CanvasRenderer.prototype.editBbox = function(gobs,i, e) {
    this.updatePoints(gobs);
    var scale = this.stage.scale();

    var offx = 8/scale.x;
    var offy = 8/scale.x;

    var me = this;
    //var points = gobs.shape.getAttr('points');

   //ar x0 = shape.x();
    //var y0 = shape.y();
    var px0 = this.bbCorners[0].x() + offx/2;
    var py0 = this.bbCorners[0].y() + offy/2;
    var px1 = this.bbCorners[1].x() + offx/2;
    var py1 = this.bbCorners[1].y() + offy/2;
    var px2 = this.bbCorners[2].x() + offx/2;
    var py2 = this.bbCorners[2].y() + offy/2;
    var px3 = this.bbCorners[3].x() + offx/2;
    var py3 = this.bbCorners[3].y() + offy/2;
    var dx = e.evt.movementX;
    var dy = e.evt.movementY;
    var oCorner;
    if(i == 0){
        this.bbCorners[1].x(px0 - offx/2);
        this.bbCorners[2].y(py0 - offy/2);
        oCorner = [this.bbCorners[3].x() + offx/2,
                   this.bbCorners[3].y() + offy/2];

    }
    if(i == 1){
        this.bbCorners[0].x(px1 - offx/2);
        this.bbCorners[3].y(py1 - offy/2);
        oCorner = [this.bbCorners[2].x() + offx/2,
                   this.bbCorners[2].y() + offy/2];
    }
    if(i == 2){
        this.bbCorners[3].x(px2 - offx/2);
        this.bbCorners[0].y(py2 - offy/2);
        oCorner = [this.bbCorners[1].x() + offx/2,
                   this.bbCorners[1].y() + offy/2];

    }
    if(i == 3){
        this.bbCorners[2].x(px3 - offx/2);
        this.bbCorners[1].y(py3 - offy/2);
        oCorner = [this.bbCorners[0].x() + offx/2,
                   this.bbCorners[0].y() + offy/2];
    }

    var nWidth  = px3-px0;
    var nHeight = py3-py0;
    var sx = nWidth/this.bbRect.width();
    var sy = nHeight/this.bbRect.height();

    //var scale = this.stage.scale();
    //var off = 10/scale.x;

    this.bbRect.x(px0);
    this.bbRect.y(py0);
    this.bbRect.width(px3-px0);
    this.bbRect.height(py3-py0);


    gobs.forEach(function(shape,i,a){
        var sbbox = shape.getBbox();

        var sprite = shape.sprite;
        var x = sprite.x();
        var y = sprite.y();

        var sdx = x - oCorner[0];
        var sdy = y - oCorner[1];

        var nx = oCorner[0] + sx*sdx;
        var ny = oCorner[1] + sy*sdy;

        //KineticJS's scenegraph stretches shapes and outlines.
        //Manually resizing gobs then updating is simpler and I don't have to
        //worry about transforms

        shape.gob.vertices.forEach(function(v){
            var dx = v.x - x;
            var dy = v.y - y;
            v.x = nx + sx*dx;
            v.y = ny + sy*dy;
        });

        /* here is the code that uses KineticJS transform hierarchy
        sprite.scaleX(sprite.scaleX()*sx);
        sprite.scaleY(sprite.scaleY()*sy);

        sprite.x(oCorner[0] + sx*sdx);
        sprite.y(oCorner[1] + sy*sdy);
        */
        shape.dirty = true;
        shape.update();
        //var mx = 0.5*(px0 + px3);
        //var my = 0.5*(py0 + py3);
    });
};

CanvasRenderer.prototype.updateBbox = function (gobs){

    this.updatePoints(gobs);

    var scale = this.stage.scale();

    var min = [ 9999, 9999];
    var max = [-9999,-9999];

    for(var i = 0; i < gobs.length; i++){

        var shape = gobs[i];
        var bb = shape.getBbox();
        if(!bb) continue;
        min[0] = min[0] < bb.min[0] ? min[0] : bb.min[0];
        min[1] = min[1] < bb.min[1] ? min[1] : bb.min[1];

        max[0] = max[0] > bb.max[0] ? max[0] : bb.max[0];
        max[1] = max[1] > bb.max[1] ? max[1] : bb.max[1];
    }

    //pad the bbox
    min[0] -=  4;
    min[1] -=  4;
    max[0] +=  4;
    max[1] +=  4;

    var offx = 8/scale.x;
    var offy = 8/scale.x;

    this.bbRect.x(min[0]);
    this.bbRect.y(min[1]);

    this.bbWidth  = max[0] - min[0];
    this.bbHeight = max[1] - min[1];

    this.bbRect.width(this.bbWidth);
    this.bbRect.height(this.bbHeight);
    this.bbRect.strokeWidth(1.5/scale.x);

    this.bbCorners.forEach(function(e,i,a){
        e.width(offx);
        e.height(offy);
    });

    //offset the bbox vertices
    min[0] -= offx/2;
    min[1] -= offy/2;
    max[0] -= offx/2;
    max[1] -= offy/2;

    //console.log(scale, off);
    this.bbCorners[0].x(min[0]);
    this.bbCorners[0].y(min[1]);

    this.bbCorners[1].x(min[0]);
    this.bbCorners[1].y(max[1]);

    this.bbCorners[2].x(max[0]);
    this.bbCorners[2].y(min[1]);

    this.bbCorners[3].x(max[0]);
    this.bbCorners[3].y(max[1]);
};


CanvasRenderer.prototype.updatePoints = function(gobs){
    if(!gobs) return;
    var me = this;

    var totalPoints = 0;
    var scale = this.stage.scale();
    for(var i = 0; i < gobs.length; i++){
        var points = gobs[i].points();
        var x = gobs[i].sprite.x();
        var y = gobs[i].sprite.y();
        var sx = gobs[i].sprite.scaleX();
        var sy = gobs[i].sprite.scaleY();
        var l = points.length;
        for(var j = 0; j < points.length; j+=2){
            me.shapeCorners[totalPoints + j/2].radius(3.0/scale.x);
            me.shapeCorners[totalPoints + j/2].strokeWidth(4/scale.x);
            me.shapeCorners[totalPoints + j/2].x(x + sx*points[j + 0]);
            me.shapeCorners[totalPoints + j/2].y(y + sy*points[j + 1]);
        };
        totalPoints += l/2;
    }
};

CanvasRenderer.prototype.mouseUp = function(){
    var me = this;
    this.endMove(this.selectedSet);
    this.selectedSet.forEach(function(e,i,d){
        me.move_poly(e.gob);
    });
};

CanvasRenderer.prototype.resetShapeCornerFill = function(){
    this.shapeCorners.forEach(function(e,i,a){
        e.fill('rgba(255,0,0,1)');
    });
};

CanvasRenderer.prototype.initPoints = function(gobs){
    var me = this;
    this.shapeCorners = [];
    this.shapeCornerMasks = [];

    var scale = this.stage.scale();
    for(var i = 0; i < gobs.length; i++){
        var points = gobs[i].points();
        for(var j = 0; j < points.length; j+=2){

            var pnt =     new Kinetic.Circle({
                radius: 5/scale.x,
                fill: 'red',
                stroke: 'rgba(255,255,255,0.25)',
                listening: true,

            });

            pnt.gob = gobs[i];
            pnt.shapeId = j/2;
            me.shapeCorners.push(pnt);
        }

    }

    this.shapeCorners.forEach(function(e,i,d){
        e.setDraggable(true);
    });

    this.shapeCorners.forEach(function(e,i,d){
        me.editLayer.add(e);
        e.on('mousedown', function(evt) {

        });

        e.on('mouseover', function(evt) {
            e.fill('rgba(255,128,128,1.0)');
            me.editLayer.batchDraw();
        });


        e.on('mouseleave', function(evt) {
            e.fill('red');
            me.editLayer.batchDraw();

        });

        e.on('dragmove', function(evt) {
            //me.editBbox(gobs,i,evt, e)
            //if(me.mode != 'edit') return;;
            var i = this.shapeId;
            this.gob.drag(evt, this);

            me.updateBbox(me.selectedSet);
            e.moveToTop();
            me.editLayer.batchDraw();
        });

        e.on('mouseup',function(evt){
            me.selectedSet.forEach(function(e,i,d){
                e.dirty = true;

                me.selectedSet.forEach(function(e,i,d){
                    if(e.dirty)
                        me.move_shape(e.gob);
                });
            });
        })

    });
};

CanvasRenderer.prototype.resetSelectedSet = function(){
    this.selectedSet = [];
};

CanvasRenderer.prototype.addToSelectedSet = function(shape){
    var inSet = this.inSelectedSet(shape);
    if(!inSet)
        this.selectedSet.push(shape);
};

CanvasRenderer.prototype.inSelectedSet = function(shape){
    var inSet = false;
    for(var i = 0; i < this.selectedSet.length; i++){
        //check _id for now, id() tries to fetch an attribute, which doesn't exist
        if(this.selectedSet[i].sprite._id ===
           shape.sprite._id)
            inSet = true;
    }

    return inSet;
};



CanvasRenderer.prototype.select = function (gobs) {
    var me = this;

    this.editLayer.removeChildren();

    this.initPoints(gobs);
    this.updateBbox(gobs);

    this.bBoxScale = [1,1];

    gobs.forEach(function(e,i,a){
        e.setLayer(me.editLayer);
        e.sprite.moveToBottom();
    });

    this.editLayer.add(this.bbRect);

    this.bbCorners.forEach(function(e,i,d){
        me.editLayer.add(e); //add corners

        e.on('mousedown', function(evt) {

        });

        e.on('dragmove', function(evt) {
            //if(this.mode != 'edit') return;
            me.editBbox(gobs,i,evt, e);
            e.moveToTop();
            me.editLayer.batchDraw();
        });

        e.on('mouseup',function(evt){
            e.dirty = true;

            me.selectedSet.forEach(function(e,i,d){
                if(e.dirty)
                    me.move_shape(e.gob);
            });
        });
    });
    this.currentLayer.draw();
    this.editLayer.draw();
};

CanvasRenderer.prototype.unselect = function (gobs) {
    //var shape = gobs.shape;
    var me = this;

    gobs.forEach(function(e,i,a){
        e.setLayer(me.currentLayer);
        e.sprite.moveToBottom();
    });

    this.bbCorners.forEach(function(e,i,d){
        e.remove(); //remove all current corners
        e.off('mousedown');
        e.off('dragmove');
        e.off('mouseup');
    });

    if(this.shapeCorners){
        this.shapeCorners.forEach(function(e,i,d){
            e.remove(); //remove all current corners
            e.off('mousedown');
            e.off('dragmove'); //kill their callbacks
            e.off('mouseup');
        });
    }
    this.selectedSet.forEach(function(e,i,d){
        if(e.dirty)
            me.move_shape(e.gob);
    });
    this.editLayer.removeChildren();
};

CanvasRenderer.prototype.unselectCurrent = function(){
    this.unselect(this.selectedSet);
};

CanvasRenderer.prototype.rerender = function (gobs, params) {
    if (!gobs)
        gobs = this.viewer.image.gobjects;
    if (!params)
        params = [this.viewer.current_view];
    this.visit_render.visit_array(gobs, params);
    this.stage.batchDraw();
};

CanvasRenderer.prototype.visitall = function (gobs, show) {
    params = [this.viewer.current_view, show];
    this.visit_render.visit_array(gobs, params);
};

CanvasRenderer.prototype.is_selected = function (gob){
    if (gob.shape)
        return gob.shape.selected;
    return false;
};

CanvasRenderer.prototype.set_select_handler = function (callback){
    this.select_callback = callback;
};

CanvasRenderer.prototype.set_move_handler = function (callback){
    this.callback_move = callback;
};

CanvasRenderer.prototype.default_select = function (gob) {
    if (this.select_callback){
        this.select_callback(gob);
    }
};

CanvasRenderer.prototype.default_move = function (view, gob) {
    if (this.callback_move)
        this.callback_move(view, gob);
};

CanvasRenderer.prototype.addSpriteEvents = function(poly, gob){
    var me = this;
    poly.on('mousedown', function(evt) {
        //select(view, gob);

        if(me.mode != 'edit') return;
        evt.evt.cancelBubble = true;

        var inSet = me.inSelectedSet(gob.shape);

        if(!inSet){
            me.unselect(me.selectedSet);
            me.resetSelectedSet();
            me.selectedSet[0] = gob.shape;
        }

        poly.setDraggable(true);
        me.editLayer.moveToTop();

        me.mouseselect = true;
        me.select( me.selectedSet);
        me.default_select(me.selectedSet);

        var scale = me.stage.scale();
        me.dragCache = {x:evt.evt.offsetX/scale.x,
                        y:evt.evt.offsetY/scale.y,};

        me.shapeCache = [];
        for(var j = 0; j < me.selectedSet.length; j++){
            me.shapeCache.push({x: me.selectedSet[j].sprite.x(),
                                y: me.selectedSet[j].sprite.y()});
        };
        //me.clearEdit(view, me.selectedSet);
        //me.beginEdit(view, me.selectedSet);
    });

    poly.on('dragstart', function() {
    });

    poly.on('dragmove', function(evt) {
        var scale = me.stage.scale();
        var pos = {x:evt.evt.offsetX/scale.x,
                   y:evt.evt.offsetY/scale.y,};

        for(var j = 0; j < me.selectedSet.length; j++){

            var f = me.selectedSet[j];
            f.dirty = true;
            var dxy = {x:pos.x - me.dragCache.x,
                       y:pos.y - me.dragCache.y,};
            if(f._id != gob.shape._id){
                f.x(me.shapeCache[j].x + dxy.x);
                f.y(me.shapeCache[j].y + dxy.y);
            }
        }
        me.updateBbox(me.selectedSet);
        this.shape.drag(evt,this);
        //me.currentLayer.draw();
        me.editLayer.draw();
    });

    poly.on('dragend', function() {

    });

    poly.on('mouseup', function() {
        poly.setDraggable(false);

        me.selectedSet.forEach(function(e,i,d){
            if(e.dirty)
                me.move_shape(e.gob);
        });
        //me.selectedSet.forEach(function(e,i,d){
        //     me.move_shape(e.gob);
        //});
    });

};

CanvasRenderer.prototype.viewShape = function (gob, move, select){
    var me = this;
    var r = this;
    var g = gob;
    if(!gob.shape) return;
    var poly = gob.shape.sprite;
    this.currentLayer.add(poly);
    var dragMove = false;
    var dragStart = false;
    var dragEnd = false;
    this.addSpriteEvents(poly, gob);
    if(gob.shape.text)
        this.addSpriteEvents(gob.shape.text, gob);
    /*
    this.appendSvg ( gob );
    gob.shape.init(svgNode);
    gob.shape.update_callback = move;
    gob.shape.select_callback = select;
    gob.shape.callback_data = { view:view, gob:g };
    gob.shape.show(true);
    if (view.edit_graphics === true)
        gob.shape.realize();
    gob.shape.editable(view.edit_graphics);
    */
} ;

CanvasRenderer.prototype.hideShape = function (gob, view) {
    var shape = gob.shape;
    //gob.shape = undefined;


    if (shape) {
        this.unselect(this.selectedSet);
        this.selectedSet = [];
        //shape.sprite.hide();
        shape.destroy();
        //delete shape;
    }

    this.editLayer.batchDraw();
    this.currentLayer.batchDraw();
};

CanvasRenderer.prototype.highlight = function (gob, selection) {
    // visitall to enhance on the node and its children

    var me = this;
    if(!selection){
        this.unselect(this.selectedSet);
        this.selectedSet = [];
        return;
    }
    visit_all(gob, function(g, args) {
        if (g.shape)
            me.addToSelectedSet(g.shape);
    }, selection );

    this.select(this.selectedSet);
};

CanvasRenderer.prototype.setcolor = function (gob, color) {
    // visitall to enhance on the node and its children
    visit_all(gob, function(g, args) {
            g.color_override = args[0];
    }, color );
    this.rerender([gob]);
};

/*
CanvasRenderer.prototype.removeFromLayer = function (gobShape) {

};
*/
//----------------------------------------------------------------------------
// graphical primitives
//----------------------------------------------------------------------------


////////////////////////////////////////////////////////////
CanvasRenderer.prototype.makeShape = function ( gob,  viewstate, shapeDescription) {
    if(gob.shape){ //JD:Don't completely understand deleting process, but: for now deferred cleanup
        if(gob.shape.isDestroyed) {
            var shape = gob.shape
            delete shape;
            gob.shape = undefined;
            return;
        }
    }

    if (gob.shape == null ) {
        var poly = new this.shapes[shapeDescription](gob, this);
        gob.shape.viewstate = viewstate;
        gob.shape = poly;

        this.viewShape (gob,
                        callback(this,'move_shape'),
                        callback(this,'select_shape'));

    }
    //visible = gob.shape.visible();
    gob.shape.update();
    if(gob.dirty)
        this.stage.draw();
};


CanvasRenderer.prototype.move_shape = function ( gob ) {
    gob.shape.move();
    this.default_move(gob);
};

CanvasRenderer.prototype.select_shape = function ( view, gob ) {
    //var gob = state.gob;
    this.default_select(view, gob);
};

////////////////////////////////////////////////////////////
// individual primitives
////////////////////////////////////////////////////////////

CanvasRenderer.prototype.polygon = function (visitor, gob , viewstate, visibility) {
    this.polyline (visitor, gob, viewstate, visibility);
    if(gob.shape)
        gob.shape.closed(true);
};

CanvasRenderer.prototype.polyline = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'polygon');
};

CanvasRenderer.prototype.line = function (visitor, gob , viewstate, visibility) {
    this.polyline (visitor, gob, viewstate, visibility);
    if(gob.shape)
        gob.shape.closed(false);
};

CanvasRenderer.prototype.ellipse = function ( visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'ellipse');
};

CanvasRenderer.prototype.circle = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'circle');
};

CanvasRenderer.prototype.rectangle = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'rectangle');
};


CanvasRenderer.prototype.square = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'square');
};

CanvasRenderer.prototype.point = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'point');
};

CanvasRenderer.prototype.label = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'label');
};

/*
///////////////////////////////////////
// LABEL is not really implemented .. need to extend 2D.js
// with SVG Text tag

CanvasRenderer.prototype.label = function ( visitor, gob, viewstate, visibility) {

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

CanvasRenderer.prototype.move_label = function (state){
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

CanvasRenderer.prototype.select_label = function (state){
    var gob = state.gob;
    this.default_select(gob);
};
*/
