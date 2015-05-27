


function test_visible_dim(pos, pos_view, tolerance ) {
    return !(pos!==undefined && pos!==null && !isNaN(pos) && Math.abs(pos-pos_view)>=tolerance);
}

function test_visible (pos, viewstate, tolerance_z ) {
    if(!pos) return false;
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


function minHeap(compare) {
  var heap = {},
      array = [];

  heap.size = function(){
      return heap.length;
  };

  heap.push = function() {
    for (var i = 0, n = arguments.length; i < n; ++i) {
      var object = arguments[i];
      up(object.heapIndex = array.push(object) - 1);
    }
    return array.length;
  };

  heap.pop = function() {
    var removed = array[0],
        object = array.pop();
    if (array.length) {
      array[object.heapIndex = 0] = object;
      down(0);
    }
    return removed;
  };

  heap.remove = function(removed) {
    var i = removed.heapIndex,
        object = array.pop();
    if (i !== array.length) {
      array[object.heapIndex = i] = object;
      (compare(object, removed) < 0 ? up : down)(i);
    }
    return i;
  };

  function up(i) {
    var object = array[i];
    while (i > 0) {
      var up = ((i + 1) >> 1) - 1,
          parent = array[up];
      if (compare(object, parent) >= 0) break;
      array[parent.heapIndex = i] = parent;
      array[object.heapIndex = i = up] = object;
    }
  }

  function down(i) {
    var object = array[i];
    while (true) {
      var right = (i + 1) << 1,
          left = right - 1,
          down = i,
          child = array[down];
      if (left < array.length && compare(array[left], child) < 0) child = array[down = left];
      if (right < array.length && compare(array[right], child) < 0) child = array[down = right];
      if (down === i) break;
      array[child.heapIndex = i] = child;
      array[object.heapIndex = i = down] = object;
    }
  }

  return heap;
}



function CanvasShape(gob, renderer) {
	this.renderer = renderer;
    if(renderer)
        this.currentLayer = renderer.currentLayer;
    this.gob = gob;
    this.postEnabled = true;
    this.selfAnchor = false;
    this.position = {x: 0, y: 0};

    this.manipulators = [];
    this.shapeCorners = [];
    //this.rotation = 0;
};


CanvasShape.prototype.id = function () {
    return this.sprite._id;
};

CanvasShape.prototype.rescale = function (scale) {
};

CanvasShape.prototype.calcBbox = function () {
};

CanvasShape.prototype.hasOverlap  = function(bbox){
    var overlap = true,
    bb1 = bbox,
    bb2 = this.bbox;
    //for each dimension test to see if axis are seperate
    for(var i = 0; i < 4; i++){
        if (bb1.max[i] <=  bb2.min[i]) overlap = false;
        if (bb1.min[i] >  bb2.max[i]) overlap = false;
    }
    return overlap;
};



CanvasShape.prototype.dragStart = function () {
    if(!this.bboxCache || !this.spriteCache ){
        this.bboxCache = {min: [0,0], max:[0,0]};
        this.spriteCache = [0,0];
    }
    this.spriteCache[0] = this.x();
    this.spriteCache[1] = this.y();

    this.bboxCache.min[0] = this.bbox.min[0];
    this.bboxCache.max[0] = this.bbox.max[0];
    this.bboxCache.min[1] = this.bbox.min[1];
    this.bboxCache.max[1] = this.bbox.max[1];
};

CanvasShape.prototype.getBbox = function () {
    if(!this.bbox)
        this.bbox = this.calcBbox();
    return this.bbox;
};



CanvasShape.prototype.isVisible = function (z,t, tolerance_z) {

    //test visible takes the shape and tests if its bounding box is intersected by
    //the current view plane
    if(!this.visibility) return false; //visibility is a tag passed from the tagger

    var test_visible_dim = function(min, max,  pos_view, tolerance ) {
        return (pos_view >= min && pos_view <= max);
    }

    var viewstate = this.renderer.viewer.current_view;

    //if(!pos) return false;
    var proj = viewstate.imagedim.project,
        proj_gob = viewstate.gob_projection;

    tolerance_z = tolerance_z || viewstate.gob_tolerance.z || 1.0;
    var tolerance_t = viewstate.gob_tolerance.t || 1.0;
    if(!this.bbox)
        this.bbox = this.caclBbox();
    var bbox = this.bbox;
    var min = bbox.min;
    var max = bbox.max;
    var t = t ? t : viewstate.t;
    var z = z ? z : viewstate.z;
    if (proj_gob==='all') {
        return true;
    } else if (proj === 'projectmaxz' || proj === 'projectminz' || proj_gob==='Z') {
        return test_visible_dim(min[3], max[3], t, tolerance_t);
    } else if (proj === 'projectmaxt' || proj === 'projectmint' || proj_gob==='T') {
        return test_visible_dim(min[2], max[2], z, tolerance_z);
    } else if (!proj || proj === 'none') {
        return (test_visible_dim(min[2], max[2], z, tolerance_z) &&
                test_visible_dim(min[3], max[3], t, tolerance_t));
    }
    return true;
}

CanvasShape.prototype.cacheOffset = function(){
    return {x: 0, y: 0};
}

CanvasShape.prototype.clearCache = function(){
    this.cached = false;
    this.sprite.clearCache();
    this.sprite.scale({x: 1.0, y: 1.0});
    this.x(this.position.x); //this updates the sprite to take into account caching offsets
    this.y(this.position.y);
    //this.
    this.bbox = this.calcBbox();
};

CanvasShape.prototype.resetManipulatorSet = function(set){
    set.forEach(function(e){
        e.remove();
        e.off('mousedown');
        e.off('dragmove'); //kill their callbacks
        e.off('mouseup');
        delete e;
    });
};

CanvasShape.prototype.resetManipulators = function(){
    if(this.renderer.colorMenu)
        this.renderer.colorMenu.hide();
    this.resetManipulatorSet(this.shapeCorners); this.shapeCorners = [];
    this.resetManipulatorSet(this.manipulators); this.manipulators = [];
}

CanvasShape.prototype.getColorManipulator = function(){
    var imageObj = new Image();
    var me = this,
    bbox = this.getBbox(),
    x = bbox.max[0],
    y = bbox.min[1],
    renderer = this.renderer,
    viewer = this.renderer.viewer,
    scale = renderer.stage.scale();
    /*
    var image = new Kinetic.Rect({
        x: x + 12/scale.x,
        y: y + 8/scale.x,
        //image: imageObj,
        //fill: "rgba(128,128,128,0.2)",
        stroke: 'red',
        strokeWidth: 1.0/scale.x,

        width: 16/scale.x,
        height: 16/scale.x,
    });
    */
    this.manipulators = [];
    if(!this.colorImage){
        this.colorImage = new Kinetic.Image({
            x: x + 12/scale.x,
            y: y, //+ 2/scale.x,
            image: imageObj,
            width: 16/scale.x,
            height: 16/scale.x
        });

        imageObj.onload = function() {
            me.colorImage.setImage(imageObj);
        };
        imageObj.src = '/images/viewer/color_wheel.png';

    }

    //renderer.colorMenu.hide();
    this.colorImage.on('mousedown', function(evt){
        var e = evt.evt;
        //var ix = image.x();
        //var iy = image.y();
        if(renderer.colorMenu.isVisible()) {
            renderer.colorMenu.hide();
            return;
        }
        var ip = me.colorImage.getAbsolutePosition();
        renderer.colorMenu.currentShape = me;
        renderer.colorMenu.show();
        renderer.colorMenu.setX(ip.x + 22);
        renderer.colorMenu.setY(ip.y + 78);
        var picker = renderer.colorMenu.queryById('picker');
        var c = Kinetic.Util._hexToRgb('#' + me.gob.color_override);
        picker.setColorRgb(c.r/255, c.g/255, c.b/255, 1.0);

    });

    this.manipulators.push(this.colorImage); // right now we have one manipulator...

    if(!renderer.colorMenu)
        renderer.colorMenu = Ext.create('Ext.tip.Tip', {
		    anchor : renderer.viewer.viewer_controls_surface,
		    //itemId : 'viewer_color',
           // anchor : 'right',
		   //anchorToTarget : true,
            cls: 'bq-viewer-menu',
            //autoHide : false,
		    //shadow: false,
            width : 250,
            height: 220,
            //closeable: true,
            //autoDestroy: true,
            //headerPosition: 'right',
            header: {
                title: 'choose color',
                tools:[{
                    type: 'close',
                    handler: function(){
                        renderer.colorMenu.hide();
                    }
                }]},
            layout: {
                type: 'vbox',
                //align: 'stretch',
            },

            listeners: {
                close : function(){
                    debugger;
                },
                show: function(){
                    if(renderer.selectedSet.length === 0) this.hide();
                }
            },

            items: [{xtype: 'excolorpicker',
                     //height: '100%',
                     flex: 1,
                     //width: 250,
                     //height: 200,
                     itemId : 'picker',
                     listeners : {
                         change: function(d, i, a){
                             var rgb = this.getColorRgb();
                             var shape = renderer.colorMenu.currentShape;
                             shape.setColor(Math.floor(rgb[0]),
                                            Math.floor(rgb[1]),
                                            Math.floor(rgb[2]));
                             renderer.drawEditLayer();
                         },
                     }
                     //region: 'west'
                    }]
	    });

    if(renderer.colorMenu.isVisible()) renderer.colorMenu.hide();

    return [this.colorImage];
};

CanvasShape.prototype.getCornerManipulators = function(){
        var me = this,
    renderer = this.renderer,
    points   = this.points(),
    scale = renderer.stage.scale();

    this.shapeCorners = [];

    for(var j = 0; j < points.length; j+=2){
        /*
          var pnt =     new Kinetic.Circle({
          radius: 5/scale.x,
          fill: 'red',
          stroke: 'rgba(255,255,255,0.05)',
          listening: true,

          });
        */
        var pnt = new Kinetic.Image({
            image:     renderer.pointImageCache,
            listening: true,
            width: 8/scale.x,
            height: 8/scale.x,
            offset: {x: 4/scale.x, y: 4/scale.x}
        });

        pnt.gob = this;
        pnt.shapeId = j/2;
        me.shapeCorners.push(pnt);
    }


    this.shapeCorners.forEach(function(e,i,d){
        e.setDraggable(true);
    });

    this.shapeCorners.forEach(function(e,i,d){
        //me.editLayer.add(e);
        e.on('mousedown', function(evt) {
            //me.currentLayer._getIntersection = me.noIntersection;
            //me.editLayer._getIntersection = me.noIntersection;
            //me.selectLayer._getIntersection = me.noIntersection;

        });

        e.on('mouseover', function(evt) {
            //e.fill('rgba(255,128,128,1.0)');
            e.image(me.pointImageCacheOver);
            if(i===0)
                renderer.drawEditLayer();
        });


        e.on('mouseleave', function(evt) {
            //e.fill('red');
            e.image(me.pointImageCache);
            if(i===0)
                renderer.drawEditLayer();

        });

        e.on('dragmove', function(evt) {
            //me.editBbox(gobs,i,evt, e)
            //if(me.mode != 'edit') return;;
            var i = this.shapeId;
            this.gob.drag(evt, this);

            e.moveToTop();
            renderer.drawEditLayer();
        });

        e.on('mouseup',function(evt){
            //me.currentLayer._getIntersection = me.defaultIntersection;
            //me.editLayer._getIntersection = me.defaultIntersection;
            //me.selectLayer._getIntersection = me.defaultIntersection;

            renderer.selectedSet.forEach(function(e,i,d){
                renderer.move_shape(e.gob);
                /*
                e.dirty = true;

                me.selectedSet.forEach(function(e,i,d){
                    if(e.dirty)

                });*/
            });
        })

    });
    return this.shapeCorners;
};

CanvasShape.prototype.getManipulators = function(mode){

    var manipulators = [];
    //var corners = this.getCornerManipulators();
    if(mode === 'single'){
        manipulators = manipulators.concat(this.getColorManipulator());
        manipulators = manipulators.concat(this.getCornerManipulators());
    }
    if(mode === 'multiple'){
        manipulators = manipulators.concat(this.getCornerManipulators());
    }

    if(mode === 'many'){
    }
    return manipulators;
}


CanvasShape.prototype.updateCorners = function(){
    //if(!shapes) return;

    var me = this,
    renderer = this.renderer,
    scale = renderer.stage.scale();

    var points = this.points();
    var x  = this.x();
    var y  = this.y();
    var sx = this.sprite.scaleX();
    var sy = this.sprite.scaleY();
    var l = points.length;

    for(var j = 0; j < points.length; j+=2){
        if(!me.shapeCorners[j/2]) continue;
        me.shapeCorners[j/2].x(x + sx*points[j + 0]);
        me.shapeCorners[j/2].y(y + sy*points[j + 1]);

        me.shapeCorners[j/2].width(8/scale.x);
        me.shapeCorners[j/2].height(8/scale.x);
    };
}

CanvasShape.prototype.updateManipulators = function(){
    //if(!shapes) return;

    var me = this,
    renderer = this.renderer,
    scale = renderer.stage.scale();

    var points = this.points();
    var x  = this.x();
    var y  = this.y();
    var sx = this.sprite.scaleX();
    var sy = this.sprite.scaleY();

    var bbox = this.getBbox(),
    x = bbox.max[0],
    y = bbox.min[1];

    for(var j = 0; j < this.manipulators.length; j++){
        this.manipulators[j].x(x + 12/scale.x);
        this.manipulators[j].y(y + 2/scale.x);
    }
}

CanvasShape.prototype.cacheSprite = function(){
    if(!this.bbox){
      return;
    }


    //this.cached = false;
    //this.sprite.clearCache();

    this.clearCache();
    var me = this;
    var phi = this.sprite.rotation();
    this.sprite.rotation(0);

    //var bb = this.bbox;
    var bb = this.calcBbox();

    //console.log(this.bbox);
    var w = bb.max[0] - bb.min[0];
    var h = bb.max[1] - bb.min[1];
    w = w < 0 ? 0:w; // just in case the bb is garbage
    h = h < 0 ? 0:h;

    var off = this.cacheOffset();
    //var w = this.sprite.width();
    //var h = this.sprite.height();

    //this.imgCache;
    var scale = this.renderer.stage.scale();

    //kinetics cacheing system is pretty bad.  It doesn't behave how you'd really expect,
    //so we really have to hack it so it works a bit better:
    //Scale, then cache, then scale back, then translate
    this.sprite.scale(scale);
    var cache = this.sprite.cache({

        x: -w/2*scale.x,
        y: -h/2*scale.y,
        width: w*scale.x,
        height:h*scale.y,
        //offset: ,
        //drawBorder:true
    });

    //this.sprite.offset({x: w/2*scale.x, y: h/2*scale.y});
    this.sprite.scale({x: 1.0/scale.x, y: 1.0/scale.y});
    this.sprite.rotation(phi);
    //this.rotation(this.rotation);
    this.cached = true;
    this.x(this.position.x); //this updates the sprite to take into account caching offsets
    this.y(this.position.y);

};

CanvasShape.prototype.setXY = function(field, input){
    if(input){
        this.position[field] = input;

        var bb = this.bbox;
        var index = field === 'x' ? 0:1;
        var offset = this.cacheOffset();
        var offSetIn = this.cached ? input - offset[field]/2 : input;

        if(this.sprites){
            this.sprites.forEach(function(e){
                e[field](offSetIn);
            });
        }
        else
            this.sprite[field](offSetIn);

        return;
    }
    else
        return this.position[field];
}

CanvasShape.prototype.x = function(input){
    return this.setXY('x', input);
};

CanvasShape.prototype.y = function(input){
    return this.setXY('y', input);
};
/*
CanvasShape.prototype.rotation = function(input){
    if(input){
        this.rotation = input;
        if(!this.cached)
            this.sprite.rotation(input);

    }
    else return this.rotation;
};
*/

CanvasShape.prototype.setStroke = function(sw){
    if(sw) this.strokeWidth = sw;
    else if(!this.strokeWidth) this.strokeWidth = 1.0;

    var scale = this.renderer.stage.scale();
    this.sprite.strokeWidth(1.25*this.strokeWidth/scale.x); //reset the moves to zero
};


CanvasShape.prototype.update = function () {
    //this.sprite.clearCache();

    //var z = this.renderer.viewer.tiles.cur_z;
    //if(z != this.gob.vertices[0].z) return;

    this.clearCache();
    this.updateLocal();
    //if(!this.bbox) this.bbox = this.calcBbox();
    //this.cache();
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
    if(this.isVisible())
        this.currentLayer.add(this.sprite);
};

CanvasShape.prototype.getSprites = function (collection) {
    if(this.isVisible()){
        return[this.sprite];
    }
    else return [];
};

CanvasShape.prototype.move = function () {
    if(!this.postEnabled) return;
    this.moveLocal();

    this.dirty = false;
};

CanvasShape.prototype.setColor = function (r,g,b) {
    var h = Kinetic.Util._rgbToHex(r,g,b);
    this.gob.color_override = h;
    var me = this;
    var    color = 'rgba('+
            r+','+
            g+','+
            b+','+
            0.5+')';
    var  strokeColor = 'rgba('+
            r+','+
            g+','+
            b+','+
            1.0+')';

    if(this.colorTimeout) clearTimeout(this.colorTimeout);
    this.colorTimeout = setTimeout( function(){
        me.renderer.viewer.color_gobject(me.gob, h);
    }, 100);

    this.sprite.fill(color);
    this.sprite.stroke(strokeColor);
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

CanvasPolyLine.prototype.cacheOffset = function(){
    var me = this;
    var bb = this.bbox;
    //console.log(this.bbox);
    var w = bb.max[0] - bb.min[0];
    var h = bb.max[1] - bb.min[1];
    return {x: w, y: h};
}

CanvasPolyLine.prototype.calcBbox = function () {
    var min = [ 9999999, 9999999, 9999999, 9999999];
    var max = [-9999999,-9999999,-9999999,-9999999];

    var points = this.sprite.points();

    if(points.length === 0) return {min: min, max: max};

    var x = this.x();
    var y = this.y();

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

    for(var z = 0; z < this.gob.vertices.length; z++){
        var pz = this.gob.vertices[z].z;
        min[2] = Math.min(min[2], pz);
        max[2] = Math.max(max[2], pz);
    }

    for(var t = 0; t < this.gob.vertices.length; t++){
        var pt = this.gob.vertices[t].t;
        min[3] = Math.min(min[3], pt);
        max[3] = Math.max(max[3], pt);
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
    this.sprite.shapeId = 0;

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


CanvasPolyLine.prototype.setStroke = function(sw){
    var scale = this.renderer.stage.scale();
    if(sw) this.strokeWidth = sw;
    else if(!this.strokeWidth) this.strokeWidth = 1.0;

    if(this._closed)
        this.sprite.strokeWidth(1.25*this.strokeWidth/scale.x); //reset the moves to zero
    else
        this.sprite.strokeWidth(2.5*this.strokeWidth/scale.x); //reset the moves to zero
};

CanvasPolyLine.prototype.updateLocal = function () {
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

        //if (!test_visible(pnt, viewstate))
        //    continue;

        vertices.push(pnt.x, pnt.y);
    }

  var min = [ 9999999, 9999999];
    var max = [-9999999,-9999999];
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

    this.setStroke();
    this.sprite.points(vertices);
    this.bbox = this.calcBbox();
    this.x(mx); //reset the moves to zero
    this.y(my); //reset the moves to zero

    this.sprite.scaleX(1.0);
    this.sprite.scaleY(1.0);
    //this.currentLayer.add(this.sprite);


    if(gob.dirty)
        this.renderer.stage.draw();
}

CanvasPolyLine.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    var points = sprite.points();
    points[2*i+0] = corner.x() - this.x();
    points[2*i+1] = corner.y() - this.y();
    sprite.points(points);
    this.bbox = this.calcBbox();

}

CanvasPolyLine.prototype.onDragCreate = function(e){
    e.evt.cancelBubble = true;

    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var me = this.shape;
    var g = me.gob;
    var v = me.renderer.viewer.current_view;
    var cx = me.x();
    var cy = me.y();
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
        me.shapeCorners[0].fill('rgba(0,255,0,1)');
    } else{
        me.shapeCorners[0].fill('rgba(255,0,0,1)');
    }

    me.bbox = me.calcBbox();
    me.renderer.drawEditLayer();

    //console.log(g);
}


CanvasPolyLine.prototype.onDragFree = function(e){
    e.evt.cancelBubble = true;

    //this is a callback with a uniqe scope which defines the shape and the start of the bounding box
    var start = this.start;

    var me = this.shape;

    var v = me.renderer.viewer.current_view;

    var g = me.gob;
    var v = me.renderer.viewer.current_view;
    var cx = me.x();
    var cy = me.y();
    var index = g.vertices.length;

    var points = me.sprite.points();
    var ept = me.renderer.getUserCoord(e);
    var pte = v.inverseTransformPoint(ept.x, ept.y);

    var ex = pte.x - cx;
    var ey = pte.y - cy;
    points.push(ex,ey);
    //points[2*index + 0] = ex;
    //points[2*index + 1] = ey;

    var bx = points[2*index - 2];
    var by = points[2*index - 1];
    //var bx = points[0];
    //var by = points[1];
    var dx = ex - bx;
    var dy = ey - by;

    //var n = g.vertices.length;
    //var dx = start.x - pte.x;
    //var dy = start.y - pte.y;
    var dp = dx*dx + dy*dy;
    if(dp < 100){
        points.push(ex,ey);
        //start = [cex,ey];
        //g.vertices.push (new BQVertex (cx + ex, cy + ey, v.z, v.t, null, index));
    }

    me.bbox = me.calcBbox();
    me.renderer.drawEditLayer();
    //console.log(g);
};

CanvasPolyLine.prototype.visvalingamSimplify = function(){
    var points = this.sprite.points();
    var heap = new minHeap(function(x,y){
        if(x === undefined) debugger;
        return x.area - y.area;
    });

    var areas = [];
    //the goal is to calculate the area of each point prior to its removal as the minimal area in the set
    //we'll use a min heap to keep the current smallest triangle at the top.  Once we're done we can choose
    //a threshold and pull only triangles that are above that threshold for display.
    var area = function(A,B,C){
        return Math.abs((B[0] - A[0])*(C[1] - A[1]) - (C[0] - A[0])*(B[1] - A[1]));
    };

    var triArea = function(tri){
        var i = tri.index;
        var p = tri.prev;
        var n = tri.next;
        var a = points.slice(2*p, 2*p + 2);
        var b = points.slice(2*i, 2*i + 2);
        var c = points.slice(2*n, 2*n + 2);
        return area(a,b,c);
    };

    //we create a linked list of triangles so that we can efficiently remove them
    //without
    var triangles = [];
    for(var i = 0; i < points.length; i+=2){
        var tri = {index: i/2, prev: i/2-1, next: i/2+1};
        tri.area = triArea(tri);
        triangles.push(tri);
    };

    for(var i = 1; i < triangles.length-1; i++){
        heap.push(triangles[i]);
    };

    while(heap.size() > 3){
        var tri = heap.pop();
        var index = tri.index;

        var next = tri.next;
        var prev = tri.prev;
        var hSize = heap.size();

        //if(triN === undefined || triP === undefined) debugger;
        //console.log(index,triN.index, triP.index, triN.heapIndex, triP.heapIndex);
        console.log(tri);
        if(next < points.length/2-1){
            var triN = triangles[next];

            var nArea = triArea(triN);
            triP.area = nArea > triArea(triN) ? nArea : triArea(triN);

            heap.sinkDown(triN.heapIndex);
            triN.prev = prev;
        }

        if(prev - 1 > 0){
            var triP = triangles[prev];
            var nArea = triArea(triP);
            triP.area = nArea > triArea(triP) ? nArea : triArea(triP);
            heap.down(triP.heapIndex);
            //if(triN.prev === next) debugger;
            triP.next = next;
        }

    }
    var thresh = 1.0/this.renderer.stage.scale().x;
    var pointsNew = [points[0], points[1]];
    for(var i = 1; i < triangles.length-1; i++){
        if(triangles[i].area > thresh){
            var id = triangles[i].index;
            pointsNew.push(points[2*id + 0]);
            pointsNew.push(points[2*id + 1]);
        };
    }
    this.sprite.points(pointsNew);
};


CanvasPolyLine.prototype.moveLocal = function(){
    var points = this.sprite.points();
    var offx = this.x();
    var offy = this.y();
    var sx = this.sprite.scaleX();
    var sy = this.sprite.scaleY();
    var z = this.gob.vertices[0].z;
    var t = this.gob.vertices[0].t;
    for(var i=0;i<points.length-1;i+=2){
        var x = points[i];
        var y = points[i+1];
        if (i % 2 == 0) {
            //var np = view.inverseTransformPoint (x, y);
            if (i/2 >= this.gob.vertices.length)
                this.gob.vertices[i/2] = new BQVertex();
            this.gob.vertices[i/2].x = sx*x + offx;
            this.gob.vertices[i/2].y = sy*y + offy;
            this.gob.vertices[i/2].z = z;
            this.gob.vertices[i/2].t = t;
        }
    }
}

CanvasPolyLine.prototype.points = function(){
    var points = this.sprite.points();
    var output = [];

    var scale;
    if(this.cached)
        scale = this.renderer.stage.scale();
    else
        scale = {x: 1, y: 1};

    for(var i = 0; i < points.length; i+=2){
        output[i] = points[i]*scale.x;
        output[i+1] = points[i+1]*scale.y;
    }
    return output;
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
    this.sprite.shapeId = 0;

    ellipse.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_ellipse'),
                             callback(this,'select_ellipse'));
*/
}

CanvasEllipse.prototype.calcBbox = function () {
    var ellipse = this.sprite;
    var px = this.x();
    var py = this.y();
    var rx = ellipse.radiusX();
    var ry = ellipse.radiusY();
    var phi = Math.PI/180*ellipse.rotation();

    var ux = rx*Math.cos(phi);
    var uy = rx*Math.sin(phi);

    var vx = ry*Math.cos(phi + Math.PI/2);
    var vy = ry*Math.sin(phi + Math.PI/2);

    var bbhw = Math.sqrt(ux*ux + vx*vx);
    var bbhh = Math.sqrt(uy*uy + vy*vy);

    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }

    return {min: [px - bbhw, py - bbhh, minz, mint],
            max: [px + bbhw, py + bbhh, maxz, maxt]};
};


CanvasEllipse.prototype.cacheOffset = function(){
    var me = this;
    //var bb = this.bbox;
    //console.log(this.bbox);
    var w = 2.0*this.sprite.radiusX();
    var h = 2.0*this.sprite.radiusY();

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);

    var p = [w*cost - h*sint, w*sint + h*cost];
    return {x: p[0], y: p[1]};
}


CanvasEllipse.prototype.updateLocal = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];
    var pnt3 = this.gob.vertices[2];
    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */

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

    this.x(p1.x);
    this.y(p1.y);
    ellipse.radiusX(rx);
    ellipse.radiusY(ry);
    ellipse.rotation(ang);
    this.setStroke();
    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
}


CanvasEllipse.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        this.x(corner.x());
        this.y(corner.y());
    }
    else {

        var p1 = [this.x(), this.y()];
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
        this.x(p1[0]);
        this.y(p1[1]);
        ellipse.radiusX(rx);
        ellipse.radiusY(ry);
        ellipse.rotation(ang + 180);
    }
    this.bbox = this.calcBbox();

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

    me.bbox = me.calcBbox();
    me.renderer.drawEditLayer();

    //console.log(g);
}

CanvasEllipse.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];


    p1.x = this.x();
    p1.y = this.y();

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);
    var r = this.sprite.radius();
    var px = [r.x*cost, r.x*sint];
    var py = [-r.y*sint, r.y*cost];

    var p2 = this.gob.vertices[1];
    var p3 = this.gob.vertices[2];

    p2.x = px[0] + this.x();
    p2.y = px[1] + this.y();

    p3.x = py[0] + this.x();
    p3.y = py[1] + this.y();

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
    this.sprite.shapeId = 0;

    sprite.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasCircle.prototype.calcBbox = function () {
    var sprite = this.sprite;
    var px = this.x();
    var py = this.y();
    var r = sprite.radius();


    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }

    return {min: [px - r, py - r, minz, mint],
            max: [px + r, py + r, maxz, maxt]};
};


CanvasCircle.prototype.cacheOffset = function(){
    var me = this;
    //var bb = this.bbox;
    //console.log(this.bbox);
    var w = 2.0*this.sprite.radius();
    var h = 2.0*this.sprite.radius();

    var t = Math.PI*this.sprite.rotation()/180;
    var cost =  Math.cos(t);
    var sint =  Math.sin(t);

    var p = [w*cost - h*sint, w*sint + h*cost];
    return {x: p[0], y: p[1]};
}

CanvasCircle.prototype.updateLocal = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];
    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */
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

    this.x(p1.x);
    this.y(p1.y);
    sprite.radius(r);
    sprite.rotation(ang + 180);
    this.setStroke();
    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
}


CanvasCircle.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        this.x(corner.x());
        this.y(corner.y());
    }
    else if (i === 1){

        var p1 = [this.x(), this.y()];
        var p2 = [corner.x(), corner.y()];
        //viewstate.transformPoint (pnt3.x, pnt3.y);
        var r =  Math.sqrt( (p1[0] - p2[0])*(p1[0] - p2[0]) + (p1[1] - p2[1])*(p1[1] - p2[1]));
        var ang = Math.atan2(p1[1]-p2[1], p1[0]-p2[0]) * 180.0/Math.PI;
        var scale = this.renderer.stage.scale();

        var sprite = this.sprite;
        this.x(p1[0]);
        this.y(p1[1]);
        sprite.radius(r);
        sprite.rotation(ang + 180);
        //ellipse.rotation(ang + 180);
    }
    this.bbox = this.calcBbox();
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
    me.bbox = me.calcBbox();
    me.renderer.drawEditLayer();
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

    p1.x = this.x();
    p1.y = this.y();

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

    this.pointSize = 2.5;
    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';

    this.sprite = new Kinetic.Circle({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        radius: this.pointSize/scale.x,
        fill: color,
        stroke: 'red',
        strokeWidth: 2.0*this.pointSize/scale.x,
    });

    gob.shape = this;
    this.gob = gob;
    this.sprite.shapeId = 0;

    this.sprite.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}
CanvasPoint.prototype.setPointSize = function(size){
    this.pointSize = size;
};

CanvasPoint.prototype.clearCache = function(){};
CanvasPoint.prototype.cacheSprite = function(){};

CanvasPoint.prototype.calcBbox = function () {
    var sprite = this.sprite;
    var px = this.x();
    var py = this.y();

    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }


    return {min: [px, py, minz, mint],
            max: [px, py, maxz, maxt]};
};


CanvasPoint.prototype.setStroke = function(sw){
    if(sw) this.strokeWidth = sw;
    else if(!this.strokeWidth) this.strokeWidth = 1.0;
    if(!this.pointSize) this.pointSize = 2.5;
    //this.pointSize = 2.5*this.strokeWidth;

    var scale = this.renderer.stage.scale();
    var r = this.pointSize*this.strokeWidth/scale.x;
    this.sprite.radius(r);
    this.sprite.strokeWidth(2.0*this.pointSize/scale.x);
};

CanvasPoint.prototype.updateStroke = function(){
    var scale = this.renderer.stage.scale();
    var r = this.pointSize/scale.x;
    this.sprite.radius(r);
    this.sprite.strokeWidth(2.0*this.pointSize/scale.x);
};

CanvasPoint.prototype.updateLocal = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */
    var scale = this.renderer.stage.scale();

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var r = this.pointSize/scale.x;

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

    this.x(p1.x);
    this.y(p1.y);
    //this.sprite.scale({x: 1.0/scale.x, y: 1.0/scale.y });
    sprite.radius(r);
    this.setStroke();

    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
}


CanvasPoint.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;

    var sprite = this.sprite;
    //var points = sprite.points();

    this.x(corner.x());
    this.y(corner.y());
    this.bbox = this.calcBbox();
}


CanvasPoint.prototype.moveLocal = function(){
    var p1 = this.gob.vertices[0];
    p1.x = this.x();
    p1.y = this.y();
}

CanvasPoint.prototype.points = function(){
    //points don't need to provide any control shapes
    return [];
}


///////////////////////////////////////////////
// ImagePoint
//
//  *
//
///////////////////////////////////////////////

function CanvasImagePoint(gob, renderer) {
	this.renderer = renderer;
    this.gob = gob;
    this.init(gob);
    CanvasShape.call(this, gob, renderer);
};

CanvasImagePoint.prototype = new CanvasShape();

CanvasImagePoint.prototype.init = function(gob){


    var scale = this.renderer.stage.scale();
    var color = 'rgba(255,0,0,0.5)';
/*
    var sprite = new Kinetic.Circle({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        fill: color,
        stroke: 'red',
        strokeWidth: 1.5/scale.x,
    });
*/
/*    var sprite = new Kinetic.Circle({
        //radius: {x: rx, y: ry},
        //x: p1.x,
        //y: p1.y,
        fill: color,
        stroke: 'red',
        strokeWidth: 1.5/scale.x,
    });
*/
    this.sprite = new Kinetic.Image({
        image: this.renderer.pointImageCache,
    });


    gob.shape = this;
    this.gob = gob;
    this.sprite.shapeId = 0;

    this.sprite.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasImagePoint.prototype.clearCache = function(){};
CanvasImagePoint.prototype.cacheSprite = function(){};

CanvasImagePoint.prototype.calcBbox = function () {
    var sprite = this.sprite;
    var px = this.x();
    var py = this.y();


    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }


    return {min: [px+3, py+3, minz, mint],
            max: [px+3, py+3, maxz, maxt]};
};

CanvasImagePoint.prototype.updateLocal = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */
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

    //this.sprite.fill(color);
    //this.sprite.stroke(strokeColor);

    var sprite = this.sprite;

    this.x(p1.x-6);
    this.y(p1.y-6);
    this.sprite.scale({x: 1.0/scale.x, y: 1.0/scale.y });
    //sprite.radius(r);
    //sprite.strokeWidth(6.0/scale.x);
    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
}


CanvasImagePoint.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;

    var sprite = this.sprite;
    //var points = sprite.points();

    this.x(corner.x());
    this.y(corner.y());
    this.bbox = this.calcBbox();
}


CanvasImagePoint.prototype.moveLocal = function(){
    var p1 = this.gob.vertices[0];
    p1.x = this.x() + 6;
    p1.y = this.y() + 6;
}

CanvasImagePoint.prototype.points = function(){
    return [];
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
    this.selfAnchor = true;
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
    this.sprites = [this.sprite, this.text];
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

    layer.add(this.sprite);
    layer.add(this.text);
    layer.add(this.arrow);

    this.sprite.shapeId = 0;
    this.text.shapeId = -1;

};

CanvasLabel.prototype.getSprites = function (collection) {
    if(this.isVisible()){
        return[this.sprite,
               this.text,
               this.arrow];
    }
    else return [];
};

CanvasLabel.prototype.calcBbox = function () {
    var sprite = this.sprite;
    var px = this.x();
    var py = this.y();
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


    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }


    return {min: [xmin, ymin, minz, mint],
            max: [xmax, ymax, maxz, maxt]};
};

CanvasLabel.prototype.clearCache = function(){};
CanvasLabel.prototype.cacheSprite = function(){};

CanvasLabel.prototype.setStroke = function(sw){
    if(sw) this.strokeWidth = sw;
    else if(!this.strokeWidth) this.strokeWidth = 1.0;
    if(!this.pointSize) this.pointSize = 2.5;
    //this.pointSize = 2.5*this.strokeWidth;

    var scale = this.renderer.scale();
    var r = this.pointSize*this.strokeWidth/scale;
    this.sprite.radius(r);
    this.sprite.strokeWidth(2.0*this.pointSize/scale);
    this.text.fontSize(14/scale);
    if(this.arrow)
        this.arrow.strokeWidth(1.0*this.pointSize/scale);


};

CanvasLabel.prototype.updateStroke = function(){
    var scale = this.renderer.stage.scale();
    var r = this.pointSize/scale;
    this.sprite.radius(r);
    this.sprite.strokeWidth(2.0*this.pointSize/scale);

    this.text.fontSize(14/scale);
    if(this.arrow)
        this.arrow.strokeWidth(1.0*this.pointSize/scale);

};


CanvasLabel.prototype.updateArrow = function(strokeColor){
    var scale = this.renderer.stage.scale();

    if(!this.arrow)
        this.arrow = new Kinetic.Line({
            points: [0,0, 1,0, 1,1],
            closed: false,
            stroke: strokeColor,
            strokeWidth: 1/scale.x,
        });
    this.arrow.stroke(strokeColor);
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
        //this.currentLayer.add(this.arrow);
        this.arrow.moveToBottom();
        var points = this.arrow.points();
        points[0] = this.x();
        points[1] = this.y();

        points[2] = this.x() + tip;
        points[3] = this.y() + dy + 0.5*this.text.height();

        points[4] = this.x() + dx;
        points[5] = this.y() + dy + 0.5*this.text.height();
    }

    else this.arrow.remove();
};

CanvasLabel.prototype.updateLocal = function () {
    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */
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
    this.text.fill(color);

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
    this.x(p1.x);
    this.y(p1.y);

    this.setStroke();

    this.updateArrow(strokeColor);
    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
    //this.currentLayer.add(this.text);
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

        this.x(corner.x() - this.offset.x);
        this.y(corner.y() - this.offset.y);
    }

    if(i == 0){
        text.x(corner.x() + this.offset.x);
        text.y(corner.y() + this.offset.y);

        this.x(corner.x());
        this.y(corner.y());
    }

    if(i == 1){

        text.x(this.sprite.x() + this.offset.x);
        text.y(this.sprite.y() + this.offset.y);

        this.offset.x = corner.x() - this.x();
        this.offset.y = corner.y() - this.y();
    }
    this.bbox = this.calcBbox();
    this.updateArrow();
}


CanvasLabel.prototype.moveLocal = function(){
    var p1 = this.gob.vertices[0];
    p1.x = this.x();
    p1.y = this.y();
    if(this.gob.vertices[0].length > 1){
        var p2 = this.gob.vertices[1];
        p2.x = this.x() + this.offset.x;
        p2.y = this.y() + this.offset.y;
    }
}

CanvasLabel.prototype.points = function(){
    return [0,0, this.offset.x, this.offset.y];
}


CanvasLabel.prototype.destroy = function () {
    this.isDestroyed = true;
    this.sprite.destroy();
    this.text.destroy();
    this.arrow.destroy();
    //delete this.sprite;
    //this.sprite = undefined;
};


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
    this.sprite.shapeId = 0;

    rect.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasRectangle.prototype.calcBbox = function () {
    var rect = this.sprite;
    var px = this.x();
    var py = this.y();
    var w = rect.width();
    var h = rect.height();
    var xmin = Math.min(px, px + w);
    var xmax = Math.max(px, px + w);
    var ymin = Math.min(py, py + h);
    var ymax = Math.max(py, py + h);

    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }

    return {min: [xmin, ymin, minz, mint],
            max: [xmax, ymax, maxz, maxt]};
};

CanvasRectangle.prototype.clearCache = function(){};
CanvasRectangle.prototype.cacheSprite = function(){};

CanvasRectangle.prototype.updateLocal = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];

    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var p2 = pnt2;//viewstate.transformPoint (pnt2.x, pnt2.y);
    var w = p2.x - p1.x;
    var h = p2.y - p1.y;
    this.x(p1.x);
    this.y(p1.y);
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
    this.setStroke();
    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
}


CanvasRectangle.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;

    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        this.x(corner.x());
        this.y(corner.y());
    }
    else if (i === 1){


        var p1 = [this.x(), this.y()];
        var dim = [corner.x() - sprite.x(),
                   corner.y() - sprite.y()];
        var rect = this.sprite;
        this.x(p1[0]);
        this.y(p1[1]);
        rect.width(dim[0]);
        rect.height(dim[1]);
    }
    this.bbox = this.calcBbox();
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

    me.bbox = me.calcBbox();
    me.renderer.drawEditLayer();
    //console.log(g);
}


CanvasRectangle.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];
    var p2 = this.gob.vertices[1];


    p1.x = this.x();
    p1.y = this.y();

    p2.x = p1.x + this.sprite.width();
    p2.y = p1.y + this.sprite.height();

}

CanvasRectangle.prototype.points = function(){
    return [0,0, this.sprite.width(),this.sprite.height()];
}



///////////////////////////////////////////////
// square:
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
    this.sprite.shapeId = 0;

    rect.shape = this;
    /*
    this.renderer.viewShape (gob,
                             callback(this,'move_sprite'),
                             callback(this,'select_sprite'));
*/
}

CanvasSquare.prototype.calcBbox = function () {
    var rect = this.sprite
    var px = this.x();
    var py = this.y();
    var w = rect.width();
    var h = rect.height();
    var xmin = Math.min(px, px + w);
    var xmax = Math.max(px, px + w);
    var ymin = Math.min(py, py + h);
    var ymax = Math.max(py, py + h);

    var
    minz =  99999999999,
    maxz = -99999999999,
    mint  = 99999999999,
    maxt = -99999999999;

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pz = this.gob.vertices[i].z;
        minz = Math.min(minz, pz);
        maxz = Math.max(maxz, pz);
    }

    for(var i = 0; i < this.gob.vertices.length; i++){
        var pt = this.gob.vertices[i].t;
        mint = Math.min(mint, pt);
        maxt = Math.max(maxt, pt);
    }

    return {min: [xmin, ymin, minz, mint],
            max: [xmax, ymax, maxz, maxt]};

};

CanvasSquare.prototype.clearCache = function(){};
CanvasSquare.prototype.cacheSprite = function(){};

CanvasSquare.prototype.updateLocal = function () {

    var viewstate = this.renderer.viewer.current_view;

    var pnt1 = this.gob.vertices[0];
    var pnt2 = this.gob.vertices[1];

    /*
    if (!test_visible(pnt1, viewstate)){
        this.sprite.remove();
        return;
    }
    */

    var p1 = pnt1;//viewstate.transformPoint (pnt1.x, pnt1.y);
    var p2 = pnt2;//viewstate.transformPoint (pnt2.x, pnt2.y);
    var w = p2.x - p1.x;
    var h = p2.y - p1.y;
    var min = Math.min(w, h);
    this.x(p1.x);
    this.y(p1.y);
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
    this.setStroke();
    this.bbox = this.calcBbox();
    //this.currentLayer.add(this.sprite);
}


CanvasSquare.prototype.drag = function(evt, corner){
    //me.editBbox(gobs,i,evt, e);
    evt.cancelBubble = true;
    var i = corner.shapeId;
    //if(!i) return;
    var sprite = this.sprite;
    //var points = sprite.points();
    if(i === 0) {
        this.x(corner.x());
        this.y(corner.y());
    }
    else if (i === 1){
        var p1 = [this.x(), this.y()];
        var dim = [corner.x() - sprite.x(),
                   corner.y() - sprite.y()];
        var rect = this.sprite;
        var min = Math.min(dim[0],dim[1]);
        this.x(p1[0]);
        this.y(p1[1]);
        rect.width(min);
        rect.height(min);
    }
    this.bbox = this.calcBbox();
    this.renderer.move_shape(this.gob);
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

    me.bbox = me.calcBbox();
    me.renderer.drawEditLayer();
    //console.log(g);
}

CanvasSquare.prototype.moveLocal = function(){

    //var p = gob.shape.x();
    //var cpnt = v.inverseTransformPoint (p.x, p.y);
    var p1 = this.gob.vertices[0];
    var p2 = this.gob.vertices[1];


    p1.x = this.x();
    p1.y = this.y();

    p2.x = p1.x + this.sprite.width();
    p2.y = p1.y + this.sprite.height();

}

CanvasSquare.prototype.points = function(){
    return [0,0, this.sprite.width(),this.sprite.height()];
}
