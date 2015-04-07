

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


function RTree(renderer){
    this.renderer = renderer;
    this.reset();
    this.maxChildren = 8;
};

RTree.prototype.reset = function(){

    this.nodes = [{
        id: 0,
        parent: null,
        children:[],
        leaves: [],
        bbox: {min: [0,0,0,0], max: [0,0,0,0]}
    }];

}

RTree.prototype.calcBoxVol = function(bb){
    //given two bounding boxes what is the volume
    var d = [0,0,0,0];
    for(var ii = 0; ii < 4; ii++){
        if(bb.max.length > ii)
            d[ii] = bb.max[ii] - bb.min[ii];
        //minimum distance is one unit
        d[ii] = Math.max(d[ii],1);
    }
    var vol = d[0]*d[1]*d[2]*d[3];

    return vol;
};

RTree.prototype.compositeBbox  = function(bbi,bbj){
    //given two bounding boxes what is the volume
    var
    min = [999999,999999,999999,999999],
    max = [-999999,-999999,-999999,-9999990];
    if(!bbi) debugger;
    if(!bbj) debugger;
    var N = Math.min(bbi.min.length, bbj.min.length);
    for(var i = 0; i < N; i++){

        min[i] = Math.min(bbi.min[i], bbj.min[i]);
        max[i] = Math.max(bbi.max[i], bbj.max[i]);
        min[i] = min[i] ? min[i] : 0;
        max[i] = max[i] ? max[i] : 0;
    }
    return {min:min, max:max};
};


RTree.prototype.calcBbox = function(gobs){
    //given a set of stored objects, find the maximum bounding volume
    var
    min = [9999999,9999999,9999999,9999999],
    max = [-9999999,-9999999,-9999999,-9999999];

    var nodei, nodej, maxVol = 0;

    if(!gobs) debugger;
    for(var i = 0; i < gobs.length; i++){
        var gbb = gobs[i].getBbox();
        var iiN = gbb.min.length;
        for(var ii = 0; ii < iiN; ii++){
            min[ii] = Math.min(min[ii], gbb.min[ii]);
            max[ii] = Math.max(max[ii], gbb.max[ii]);
            min[ii] = min[ii] ? min[ii] : 0;
            max[ii] = max[ii] ? max[ii] : 0;
        }
    }
    return {min: min, max: max};
};

RTree.prototype.findMaxVolPairs  = function(gobs){
    //given a set of stored objects, find the maximum bounding volume between pairs in the set
    //return an array of the two indices
    var nodei, nodej, maxVol = 0;
    for(var i = 0; i < gobs.length; i++){
        for(var j = i+1; j < gobs.length; j++){
            //if(i == j) continue;
            var ibb = gobs[i].getBbox();
            var jbb = gobs[j].getBbox();
            var cbb = this.compositeBbox(ibb,jbb);
            var vol = this.calcBoxVol(cbb);
            if(vol > maxVol){
                maxVol = vol;
                nodei = i;
                nodej = j;
            }
        }
    }
    return [gobs[nodei],gobs[nodej]];
};

RTree.prototype.hasOverlap  = function(bbox1, bbox2){
    var overlap = false,
    bb1 = bbox1,
    bb2 = bbox2;
    //for each dimension test to see if axis are seperate
    for(var i = 0; i < 2; i++){
        if      (bb1.max[i] < bb2.min[i]) overlap = false;
        else if (bb2.max[i] < bb1.min[i]) overlap = false;
        else overlap = true;

    }
    return overlap;
};

RTree.prototype.calcVolumeChange  = function(obj, node){
    var nodebb = node.bbox;
    var compbb = this.compositeBbox(obj.bbox, nodebb);

    var nodeVol = this.calcBoxVol(nodebb);
    var compVol = this.calcBoxVol(compbb);
    return Math.abs(nodeVol - compVol);
}

RTree.prototype.splitNode  = function(node){

    var b12 = this.findMaxVolPairs(node.leaves);

    var newNode0 = {
        parent: node,
        children:[],
        leaves: [b12[0]],
        bbox: this.calcBbox([b12[0]]),
    };

    var newNode1 = {
        parent: node,
        children:[],
        leaves: [b12[1]],
        bbox: this.calcBbox([b12[1]])
    }
    b12[0].page = newNode0;
    b12[1].page = newNode1;

    var id = this.nodes.length;
    newNode0.id = id;
    newNode1.id = id+1;

    this.nodes.push(newNode0, newNode1);
    node.children.push(newNode0,newNode1);
    for(var i = 0; i < node.leaves.length; i++){
        var leaf = node.leaves[i];

        if(leaf.id() === b12[0].id() ||
           leaf.id() === b12[1].id()) continue; //if the leaf == to one of the reference nodes, continue

        var dvol0 = this.calcVolumeChange(leaf, node.children[0]);
        var dvol1 = this.calcVolumeChange(leaf, node.children[1]);
        var bbox = leaf.bbox;
        var bbox0 = node.children[0].bbox;
        var bbox1 = node.children[1].bbox;

        //console.log("l:", bbox.min[0],bbox.min[1],bbox.max[0], bbox.max[1]);
        //console.log("0:", bbox0.min[0],bbox0.min[1],bbox0.max[0], bbox0.max[1], dvol0);
        //console.log("1:", bbox1.min[0],bbox1.min[1],bbox1.max[0], bbox1.max[1], dvol1);

        if(dvol0 < dvol1){
            this.insertInNode(leaf, node.children[0]);
        }
        else {
            this.insertInNode(leaf, node.children[1]);
        }
    }
    node.children[0].bbox = this.calcBbox(node.children[0].leaves);
    node.children[1].bbox = this.calcBbox(node.children[1].leaves);
    this.updateSprite(node.children[0]);
    this.updateSprite(node.children[1]);

    node.leaves = [];
};

RTree.prototype.insertInNode  = function(gob, node){
    node.leaves.push(gob);
    gob.page = node;
    node.bbox = this.calcBbox(node.leaves);
    this.updateSprite(node);

    if(node.leaves.length >= this.maxChildren){
        this.splitNode(node);
    }
};

RTree.prototype.traverseDownBB  = function(node, bb, func){
    var stack = [node];
    while(stack.length > 0){
        var cnode = stack.pop();
        if(!func(cnode)) continue;
        if(cnode.children.length > 0){
            if(this.hasOverlap(bb, cnode.children[0].bbox))
                stack.push(cnode.children[0]);
            if(this.hasOverlap(bb, cnode.children[1].bbox))
                stack.push(cnode.children[1]);
        }
    }
};

RTree.prototype.traverseDown  = function(node, func){
    var stack = [node];
    while(stack.length > 0){
        var cnode = stack.pop();
        func(cnode);
        if(cnode.children.length > 0){
            stack.push(cnode.children[0]);
            stack.push(cnode.children[1]);
        }
    }
};


RTree.prototype.traverseUp  = function(node, func){
    var stack = [node];
    while(stack.length > 0){
        var cnode = stack.pop();
        if(!func(cnode)) continue;
        if(cnode.parent){
            stack.push(cnode.parent);
        }
    }
};

RTree.prototype.insert = function(gob){
    //I like static integer pointer trees, but a dymanic pointer tree seems appropriate here, so
    // we can pull data on and off the tree without having to do our own
    //return;
    var stack = [this.nodes[0]];

    //if(gob.id() === 15) debugger;
    if(gob.page) return;  //if the gobject has a page then we insert it

    gob.bbox = gob.calcBbox();
    //if(this.nodes.length > 10) return;
    while(stack.length > 0){
        //if(l > 18) break;
        var cnode = stack.pop();
        cnode.dirty = true;
        //expand the bounding box of the current node on the stack
        cnode.bbox = this.compositeBbox(gob.bbox, cnode.bbox);
        this.updateSprite(cnode);

        if(cnode.children.length === 0){

            if(cnode.leaves.length < this.maxChildren){
                this.insertInNode(gob,cnode);
            }
        }

        else{
            var mindvol = 999999999, nextNode;
            for(var i = 0; i < cnode.children.length; i++){
                var dvol = this.calcVolumeChange(gob, cnode.children[i]);
                if(dvol < mindvol){
                    mindvol = dvol;
                    nextNode = cnode.children[i];
                }
            }

            stack.push(nextNode);
        }
    }
};


RTree.prototype.remove = function(gob){
    //I like static integer pointer trees, but a dymanic pointer tree seems appropriate here, so
    // we can pull data on and off the tree without having to do our own
    //return;

    //if(gob.id() === 15) debugger;
    var node = gob.page;
    var leaves = node.leaves;
    var pos = 0;
    for(var i= 0; i < leaves.length; i++){
        if(leaves[i].id() === gob.id()) pos = i;
    }
    leaves.splice(pos,1);
    node.bbox = this.calcBbox(node.leaves);
    //this.updateSprite(node);
    node = node.parent;
    while(node){
        //if(node.parent === null) break;
        if(!node.children)       continue;
        var cnode0 = node.children[0];
        var cnode1 = node.children[1];
        node.bbox = this.compositeBbox(cnode0.bbox, cnode1.bbox);
        this.updateSprite(node);
        node.dirty = true;
        node = node.parent;
    }
    gob.page = null;
};


RTree.prototype.collectObjectsInRegion = function(frust, node){
    var me = this;
    var collection = [];
    var renderer = this.renderer;

    var collectSprite = function(node){
        if(node.leaves.length > 0){
            for(var i = 0; i < node.leaves.length; i++){
                if(me.hasOverlap(frust, node.leaves[i].bbox)){
                    collection.push(node.leaves[i]);
                }
            }
        }
        return true;
    };
    this.traverseDownBB(node, frust, collectSprite);
    return collection;
};

RTree.prototype.cull = function(frust){
    var me = this;
    var renderer = this.renderer;
    renderer.currentLayer.removeChildren();

    var leaves = this.collectObjectsInRegion(frust, this.nodes[0]);
    leaves.forEach(function(e){
        renderer.currentLayer.add(e.sprite);
    });
};

RTree.prototype.cullAndCache = function(frust){
    var me = this;
    var fArea = this.calcBoxVol(frust);
    var me = this;
    var collection = [];
    var renderer = this.renderer;
    var scale = renderer.stage.scale().x;
    var collectSprite = function(node){
        var nArea = me.calcBoxVol(node.bbox);
        var cache = null;

        if(node.leaves.length > 0){
            for(var i = 0; i < node.leaves.length; i++){
                if(me.hasOverlap(frust, node.leaves[i].bbox)){
                    collection.push(node.leaves[i].sprite);
                }
            }
            return false;
        }

        else if(nArea < fArea) {
            if(!node.imageCache ||
               scale != node.scale)
                me.cacheChildSprites(node);
            /*
              if the node is dirty, then rather than update the cache and redraw
              the image which is an asynchronis call, its better to just redraw the
              the whole branch of the tree.
            */
            if(node.dirty){
                me.cacheChildSprites(node);
                var leaves = me.collectObjectsInRegion(node.bbox, node);
                leaves.forEach(function(e){
                    collection.push(e.sprite);
                });
                return false;
            }

            collection.push(node.imageCache);
            return false;
        }

        else return true;
    };
    this.traverseDownBB(this.nodes[0], frust, collectSprite);

    renderer.currentLayer.removeChildren();
    collection.forEach(function(e){
        renderer.currentLayer.add(e);
    });
};

RTree.prototype.cacheScene = function(frust){
    var me = this;
    var fArea = this.calcBoxVol(frust);
    var collectSprite = function(node){
        var nArea = me.calcBoxVol(node.bbox);
        if(nArea < fArea) {
            me.cacheChildSprites(node);
            return false;
        }
        else return true;
    };
    this.traverseDownBB(this.nodes[0], frust, collectSprite);
};

RTree.prototype.cacheChildSprites = function(node, scale){
    //delete cache if it exists
    if(node.image) delete node.image;
    if(node.imageCache) delete node.imageCage;

    //initialize a few variables;
    var me = this;
    var renderer = this.renderer;
    var bbox = node.bbox;
    var w = bbox.max[0] - bbox.min[0];
    var h = bbox.max[1] - bbox.min[1];
    var scale = renderer.stage.scale().x;

    node.scale = scale;

    var buffer = renderer.getPointSize();

    //create a new image
    node.imageCache = new Kinetic.Image({
    });

    //create a temp layer to capture the appropriate objects
    var layer = new Kinetic.Layer({
        scaleX: scale,
        scaleY: scale,
        width: w*scale,
        height: h*scale
    });

    //fetch the objects in the tree that are in that node
    var leaves = this.collectObjectsInRegion(bbox, node);
    leaves.forEach(function(e){
        e.updateLocal();
        layer.add(e.sprite);
    });
    layer.draw();

    //create a new image, in the async callback assign the image to the node's imageCache
    //scale the image region
    var image = layer.toImage({
        callback: function(img){
            node.image = img;
            node.imageCache.setImage(img);
            node.dirty = false;
        },

        x: bbox.min[0]*scale - buffer,
        y: bbox.min[1]*scale - buffer,
        width: w*scale + 2.0*buffer,
        height: h*scale + 2.0*buffer,
    });
    node.imageCache.x(bbox.min[0] - buffer/scale);
    node.imageCache.y(bbox.min[1] - buffer/scale);
    node.imageCache.width(w + 2.0*buffer/scale);
    node.imageCache.height(h + 2.0*buffer/scale);
};

RTree.prototype.setDirty = function(node){
    var me = this;
    var dirtFunc = function(node){
        node.dirty = true;
        return true;
    };
    this.traverseUp(node, dirtFunc);
};


RTree.prototype.updateSprite = function(node){
    var bbox = node.bbox;
    var w = bbox.max[0] - bbox.min[0];
    var h = bbox.max[1] - bbox.min[1];
    if(!node.sprite)
        node.sprite = new Kinetic.Rect({
            x: bbox.min[0],
            y: bbox.min[1],
            width: w,
            height: h,
            hasFill: false,
            listening: false,
            //fill: "rgba(128,128,128,0.2)",
            stroke: "rgba(128,255,255,0.4)",
            strokeWidth: 1.0,
        });

    node.sprite.x(bbox.min[0]);
    node.sprite.y(bbox.min[1]);
    node.sprite.width(w);
    node.sprite.height(h);
};

////////////////////////////////////////////////////////////////
//Controller
////////////////////////////////////////////////////////////////

function CanvasControl(viewer, element) {
    this.viewer = viewer;

    if (typeof element == 'string')
        this.svg_element = document.getElementById(element);
    else
        this.svg_element = element;

    this.viewer.viewer.tiles.tiled_viewer.addViewerZoomedListener(this);
    this.viewer.viewer.tiles.tiled_viewer.addViewerMovedListener(this);

}

CanvasControl.prototype.setFrustum = function(e, scale){
    var dim = this.viewer.viewer.imagedim;
    var
    cw = this.viewer.viewer.imagediv.clientWidth/scale.x,
    ch = this.viewer.viewer.imagediv.clientHeight/scale.y,
    x = e.x < 0 ? -e.x/scale.x : 0,
    y = e.y < 0 ? -e.y/scale.y : 0,
    w = e.x < 0 ? dim.x + e.x/scale.x : cw - e.x/scale.x;
    h = e.y < 0 ? dim.y + e.y/scale.y : ch - e.y/scale.y;
    w = Math.min(cw, w);
    w = Math.min(dim.x, w);
    h = Math.min(ch, h);
    h = Math.min(dim.y, h);
    this.viewer.setFrustum({
        min: [x,y],
        max: [x+w, y+h]
    });
};

CanvasControl.prototype.viewerMoved = function(e) {
    //this.viewer.stage.setPosition({x: e.x, y: e.y});
    //var canvas = this.viewer.currentLayer.getCanvas()._canvas;
    var scale = this.viewer.stage.scale();
    this.setFrustum(e, scale);

    this.viewer.stage.x(e.x);
    this.viewer.stage.y(e.y);
    var frust = this.viewer.viewFrustum;
    //var w = frust.max[0] - frust.min[0];
    //var h = frust.max[1] - frust.min[1];
    //this.viewer.stage.width(w*scale.x);
    //this.viewer.stage.height(h*scale.y);

    this.viewer.updateVisible();
    var me = this;
    /*
    var draw = function(){
        if(!me.timeout)
            me.viewer.draw();
        me.timeout = null;
    };
    setTimeout(draw, 100);
    */
    this.viewer.draw();
    //this.viewer.stage.content.style.left = e.x + 'px';
    //this.viewer.stage.content.style.top = e.y + 'px';

};

CanvasControl.prototype.viewerZoomed = function(e) {
    //this.viewer.stage.content.style.left = e.x + 'px';
    //this.viewer.stage.content.style.top = e.y + 'px';

    this.viewer.stage.scale({x:e.scale,y:e.scale});

    this.setFrustum(e, {x: e.scale, y: e.scale});

    this.viewer.stage.x(e.x);
    this.viewer.stage.y(e.y);
    this.viewer.updateVisible();
    this.viewer.draw();
};

////////////////////////////////////////////////////////////////
//Renderer
////////////////////////////////////////////////////////////////


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
    this.mode = 'navigate';
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
        listening: true,
    });

    this.stage.content.style.setProperty('z-index', 15);

    this.initShapeLayer();
    this.initEditLayer();
    this.initSelectLayer();
    this.initPointImageCache();
    this.rtree = new RTree(this);
    this.cur_z = 0;

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
    this.visibleSet = [];

    this.lassoRect = new Kinetic.Rect({
        fill: 'rgba(200,200,200,0.1)',
        stroke: 'grey',
        strokeWidth: 1,
        listening: false,
    });

    this.selectRect = new Kinetic.Rect({
        fill: 'rgba(0,0,0,0.0)',
        strokeWidth: 0,
        width: this.stage.width(),
        height: this.stage.height(),
        listening: true,
    });
    this.selectLayer.add(this.selectRect);

    var
    stage = this.stage,
    lassoRect = this.lassoRect;
    var mousemove = function(e) {
        if(me.mode != 'edit') return;
        var evt = e.evt;
        var scale = stage.scale();

        var stageX = stage.x();
        var stageY = stage.y();
        var x = (evt.offsetX - stageX)/scale.x;
        var y = (evt.offsetY - stageY)/scale.y;

        var x0 = lassoRect.x();
        var y0 = lassoRect.y();

        lassoRect.width((x - x0));
        lassoRect.height((y - y0));
        me.editLayer.draw();
    };

    var mousedown = function(e){
        if(me.mode != 'edit') return;
        me.unselect(me.selectedSet);

        var evt = e.evt;
        var scale = stage.scale();

        var stageX = stage.x();
        var stageY = stage.y();
        var x = (evt.offsetX - stageX)/scale.x;
        var y = (evt.offsetY - stageY)/scale.y;

        //console.log(evt);

        me.currentLayer.draw();
        me.editLayer.draw();
        me.selectedSet = []; //clear out current selection set

        me.editLayer.add(me.lassoRect);
        me.selectLayer.moveToTop();

        lassoRect.width(0);
        lassoRect.height(0);
        lassoRect.x(x);
        lassoRect.y(y);

        me.selectRect.on('mousemove', mousemove);
    }

    var mouseup = function(e) {
        if(me.mode != 'edit') return;
        me.selectRect.off('mousemove');
        me.lassoRect.remove();
        me.selectLayer.moveToBottom();

        var x0t = me.lassoRect.x();
        var y0t = me.lassoRect.y();
        var x1t = me.lassoRect.width() + x0t;
        var y1t = me.lassoRect.height() + y0t;

        var x0 = Math.min(x0t, x1t);
        var y0 = Math.min(y0t, y1t);
        var x1 = Math.max(x0t, x1t);
        var y1 = Math.max(y0t, y1t)

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

CanvasRenderer.prototype.draw = function (){
    this.stage.draw();
};

CanvasRenderer.prototype.drawEditLayer = function (){
    this.updateBbox(this.selectedSet);
    this.editLayer.draw();
};

CanvasRenderer.prototype.enable_edit = function (enabled) {

    this.viewer.current_view.edit_graphics = enabled?true:false;
    var gobs =  this.viewer.image.gobjects;
    this.visit_render.visit_array(gobs, [this.viewer.current_view]);

    this.editLayer.moveToTop();
    this.rendered_gobjects = gobs;
};


CanvasRenderer.prototype.getUserCoord = function (e ){
    var evt;


    if(e.evt)
        evt = e.evt;
    var x = evt.offsetX==undefined?evt.layerX:evt.offsetX;
    var y = evt.offsetY==undefined?evt.layerY:evt.offsetY;
    var scale = this.stage.scale();

    var stageX = this.stage.x();
    var stageY = this.stage.y();
    var x = (x - stageX);
    var y = (y - stageY);

    return {x: x, y: y};
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
    this.unselect(this.selectedSet);
    if(mode == 'add') {
        this.lassoRect.width(0);
        this.lassoRect.height(0);
        this.selectLayer.moveToBottom();
        this.editLayer.moveToTop();
    }
    this.updateVisible();
    this.draw();
};

CanvasRenderer.prototype.initPointImageCache = function () {
    var me = this;
    var point = new Kinetic.Circle({
            //radius: {x: rx, y: ry},
            x: 8,
            y: 8,
            fill:   'rgba(255,,255,1.0)',
            stroke: 'rgba(255,255,255,0.5)',
            radius: 3,
            strokeWidth: 6,
        });
    var layer = new Kinetic.Layer({
        width: 16,
        height: 16
    }).add(point);
    layer.draw();

    this.pointImageCache;
    layer.toImage({
        callback: function(img){
            me.pointImageCache = img;
        }
    });
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

CanvasRenderer.prototype.setFrustum = function(bb){
    if(!this.viewFrustum)
        this.viewFrustum = {min: [0,0], max: [0, 0]};
    if(!this.cursorRect)
        this.cursorRect = new Kinetic.Rect({
            //x: -20,
            //y: -20,
            width: 0,
            height: 0,
            fill: "rgba(128,255,128,0.2)",
            stroke: 'black',
            strokeWidth: 1,
        });
    //this.editLayer.add(this.cursorRect);
    this.viewFrustum.min[0] = bb.min[0];
    this.viewFrustum.min[1] = bb.min[1];
    this.viewFrustum.max[0] = bb.max[0];
    this.viewFrustum.max[1] = bb.max[1];
    this.cursorRect.x(bb.min[0]);
    this.cursorRect.y(bb.min[1]);
    this.cursorRect.width(bb.max[0] - bb.min[0]);
    this.cursorRect.height(bb.max[1] - bb.min[1]);
}

CanvasRenderer.prototype.cacheVisible = function(){
    this.rtree.cacheScene(this.viewFrustum);
};

CanvasRenderer.prototype.updateVisible = function(){
    if(this.mode == 'navigate')
        this.rtree.cullAndCache(this.viewFrustum);
    else
        this.rtree.cull(this.viewFrustum);
};

CanvasRenderer.prototype.drawNodes = function(){
    var me = this;
    var scale = this.stage.scale();
    for(var i = 0; i < this.rtree.nodes.length; i++){

        var node = this.rtree.nodes[i];
        var bbox = node.bbox;
        var pid = node.parent ? node.parent.id : null;

        var w = bbox.max[0] - bbox.min[0];
        var h = bbox.max[1] - bbox.min[1];
        if(!node.sprite)
            node.sprite = new Kinetic.Rect({
                x: bbox.min[0],
                y: bbox.min[1],
                width: w,
                height: h,
                hasFill: false,
                listening: false,
                //fill: "rgba(128,128,128,0.2)",
                stroke: "rgba(128,255,255,0.25)",
                strokeWidth: 1.0,
            });

        node.sprite.visible(true);
        this.currentLayer.add(node.sprite);
    }
    var dim = this.viewer.imagedim;
    this.viewFrustum = {min: [0,0], max: [dim.x, dim.y]};
    if(!this.cursorRect)
        this.cursorRect = new Kinetic.Rect({
            //x: -20,
            //y: -20,
            width: dim.x,
            height: dim.y,
            fill: "rgba(128,255,128,0.2)",
            stroke: 'black',
            strokeWidth: 1,
        });
    this.currentNode = this.rtree.nodes[0];
    this.editLayer.add(this.cursorRect);

    this.selectRect.on('mousemove', function(e){

        var evt = e.evt;
        var scale = me.stage.scale();
        //console.log(e);
        var stageX = me.stage.x();
        var stageY = me.stage.y();
        var x = (evt.offsetX - stageX)/scale.x;
        var y = (evt.offsetY - stageY)/scale.y;

        //me.cursorRect.x(x-1);
        //me.cursorRect.y(y-1);
        var frust = me.viewFrustum;

        //frust.min[0] = x-1;
        //frust.min[1] = y-1;
        //frust.max[0] = x+1;
        //frust.max[1] = y+1;

        me.editLayer.batchDraw();


        var stack = [];

        stack.push(me.currentNode);
        var newCurrentNode;

        var isContained = function(bb1, bb0){
            return (bb0.min[0] < bb1.min[0] && bb0.max[0] > bb1.max[0] &&
                    bb0.min[1] < bb1.min[1] && bb0.max[1] > bb1.max[1]);
        };

        while(stack.length > 0){
            var cnode = stack.pop();
            var nbb = cnode.bbox;
            if(cnode.children.length > 0){
                var ho0 = hasOverlap(frust,cnode.children[0].bbox);
                var ic0 = isContained(frust,cnode.children[0].bbox);
                var ho1 = hasOverlap(frust,cnode.children[1].bbox);
                var ic1 = isContained(frust,cnode.children[1].bbox);

                if(ic0 && !ho1){
                    stack.push(cnode.children[0]);
                }
                else if(ic1 && !ho0){
                    stack.push(cnode.children[1]);
                }
                else {
                    newCurrentNode = cnode;
                }
            }

            else{
                //if we've moved out of the view frustum check the parent
                if(cnode.parent)
                    stack.push(cnode.parent);
            }
        }

        var hideSprite = function(node){
            if(node.sprite)
                node.sprite.visible(false);
        };

        var showSprite = function(node){
            if(node.sprite)
                node.sprite.visible(true);
        };

        if(newCurrentNode.id != me.currentNode.id){
            //see if traversal works
            me.rtree.traverseDown(me.currentNode, hideSprite);
            me.rtree.traverseDownBB(newCurrentNode, frust, showSprite);
            me.currentLayer.batchDraw();
            me.currentNode = newCurrentNode;
        }
    });
};


CanvasRenderer.prototype.resetTree = function (e) {
    //reset the rtree and visible node references to tree
    this.visibleSet.forEach(function(e){
        e.page = null;
    });
    this.visibleSet =[]; //cleare the visible set.
    //rtree reset
    this.rtree.reset();
};

CanvasRenderer.prototype.updateImage = function (e) {
    var me = this;
    var viewstate = this.viewer.current_view;
    var url = this.viewer.image_url();
    var scale = this.viewer.current_view.scale;
    var x = this.viewer.tiles.tiled_viewer.x;
    var y = this.viewer.tiles.tiled_viewer.y;
    var z = this.viewer.tiles.cur_z;
    this.stage.scale(scale);

    /*
    if(this.selectedSet.length> 0){
        if(this.selectedSet[0].gob.vertices[0]){
            if(this.selectedSet[0].gob.vertices[0].z != z){
            }
        }
    }*/

    this.unselect(this.selectedSet);
    this.selectedSet = [];


    //this.stage.content.style.left = x + 'px';
    //this.stage.content.style.top = y + 'px';

    var width = window.innerWidth;
    var height = window.innerHeight;

    if(!this.viewFrustum)
        this.setFrustum({
            min: [0,0],
            max: [x,y]
        });
    this.stage.setWidth(width);
    this.stage.setHeight(height);

    this.selectRect.width(viewstate.width/scale);
    this.selectRect.height(viewstate.height/scale);

    this.lassoRect.strokeWidth(1.0/scale);

    /*
    */

    if(this.cur_z != z)
        this.resetTree();
    this.cur_z = z;

    //dump the currently viewed objects
    this.currentLayer.removeChildren();

    if(!this.addedListeners){
        this.addedListeners = true;
        this.myCanvasListener = new CanvasControl( this, this.stage );
    }

    //get the gobs and walk the tree to rerender them
    var gobs = this.viewer.image.gobjects;
    this.visit_render.visit_array(gobs, [this.viewer.current_view]);
    this.rendered_gobjects = gobs;

    //update visible objects in the tree... next iteration may be 3D.
    this.updateVisible();

    this.updateBbox(this.selectedSet);
    this.draw();
};

CanvasRenderer.prototype.editBbox = function(gobs,i, e) {
    //return;
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
    console.log();
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
        var x = shape.x();
        var y = shape.y();

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
    var pad = 8/scale.x;
    //pad the bbox
    min[0] -=  pad;
    min[1] -=  pad;
    max[0] +=  pad;
    max[1] +=  pad;

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


CanvasRenderer.prototype.updatePoints = function(shapes){
    if(!shapes) return;

    var me = this;
    var totalPoints = 0;
    var scale = this.stage.scale();

    for(var i = 0; i < shapes.length; i++){
        var points = shapes[i].points();
        var x = shapes[i].x();
        var y = shapes[i].y();
        var sx = shapes[i].sprite.scaleX();
        var sy = shapes[i].sprite.scaleY();
        var l = points.length;

        for(var j = 0; j < points.length; j+=2){
            if(!me.shapeCorners[totalPoints + j/2]) continue;
            me.shapeCorners[totalPoints + j/2].radius(3.0/scale.x);
            me.shapeCorners[totalPoints + j/2].strokeWidth(6.0/scale.x);
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

CanvasRenderer.prototype.initPoints = function(shapes){
    var me = this;
    this.shapeCorners = [];
    this.shapeCornerMasks = [];

    var scale = this.stage.scale();
    for(var i = 0; i < shapes.length; i++){
        var points = shapes[i].points();
        for(var j = 0; j < points.length; j+=2){

            var pnt =     new Kinetic.Circle({
                radius: 5/scale.x,
                fill: 'red',
                stroke: 'rgba(255,255,255,0.05)',
                listening: true,

            });

            pnt.gob = shapes[i];
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
            me.drawEditLayer();
        });


        e.on('mouseleave', function(evt) {
            e.fill('red');
            me.drawEditLayer();

        });

        e.on('dragmove', function(evt) {
            //me.editBbox(gobs,i,evt, e)
            //if(me.mode != 'edit') return;;
            var i = this.shapeId;
            this.gob.drag(evt, this);

            me.updateBbox(me.selectedSet);
            e.moveToTop();
            me.drawEditLayer();
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
            me.editLayer.batchDraw(); // don't want to use default draw command, as it updates the bounding box
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
    this.draw();
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
    if(!this.dragCache) this.dragCache = [0,0];
    poly.on('mousedown', function(evt) {
        //select(view, gob);

        if(me.mode != 'edit') return;
        evt.evt.cancelBubble = true;
        poly.shape.clearCache();

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
        me.dragCache[0] = evt.evt.offsetX/scale.x;
        me.dragCache[1] = evt.evt.offsetY/scale.y;

        //me.shapeCache = [];
        for(var j = 0; j < me.selectedSet.length; j++){
            me.selectedSet[j].dragStart();
            me.rtree.remove(me.selectedSet[j]);
        };

    });

    poly.on('dragstart', function() {
    });

    poly.on('dragmove', function(evt) {
        var scale = me.stage.scale();
        var pos = [evt.evt.offsetX/scale.x,
                   evt.evt.offsetY/scale.y];

        poly.shape.position.x = poly.x();
        poly.shape.position.y = poly.y();
        //console.log(pos, poly.x(), poly.y());
        var bbox, bboxCache, shape, shapeCache, gsprite, fsprite;
        var dxy = [0,0];
        for(var j = 0; j < me.selectedSet.length; j++){

            var f = me.selectedSet[j];


            f.dirty = true;
            dxy[0] = pos[0] - me.dragCache[0];
            dxy[1] = pos[1] - me.dragCache[1];

            gsprite = gob.shape.sprite;
            fsprite = f;

            bbox = f.bbox;
            bboxCache = f.bboxCache;
            shapeCache = f.spriteCache;

            bbox.min[0] = bboxCache.min[0] + dxy[0];
            bbox.max[0] = bboxCache.max[0] + dxy[0];
            bbox.min[1] = bboxCache.min[1] + dxy[1];
            bbox.max[1] = bboxCache.max[1] + dxy[1];

            if(fsprite._id != gsprite._id){
                fsprite.x(shapeCache[0] + dxy[0]);
                fsprite.y(shapeCache[1] + dxy[1]);
            }
        }
        me.updateBbox(me.selectedSet);
        if(this.shape.selfAnchor)
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

            //me.rtree.in(f);
            me.rtree.insert(e)
        });
        ;
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
    this.draw();
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


    var visible = test_visible(gob.vertices[0], viewstate);
    if(visible)
        this.visibleSet.push(gob.shape);
    //visible = gob.shape.visible();

    gob.shape.update();
    if(!gob.shape.page && visible)
        this.rtree.insert(gob.shape);
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
    this.pointSize = 2.5;
    this.makeShape(gob, viewstate, 'point');
    if(gob.shape)
        gob.shape.setPointSize(this.pointSize);

};

CanvasRenderer.prototype.label = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'label');
};

CanvasRenderer.prototype.getPointSize = function () {
    return this.pointSize;
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
