//modification to imageview
function ImgPixelCounter(viewer,name) {
    this.base = ViewerPlugin;
    this.base (viewer, name);

    var p = viewer.parameters || {};
    this.default_threshold        = p.threshold || 0;
    this.default_autoupdate       = false;

    var tb = this.viewer.toolbar;
    if (!tb) return;
    var operations = tb.queryById('menu_viewer_operations');
    if (!operations) return;
    operations.menu.insert(1, {
        xtype  : 'menuitem',
        itemId : 'menu_viewer_pixel_counting',
        text   : 'Pixel counter',
        handler: this.pixelCounter,
        scope  : this,
    });
}


ImgPixelCounter.prototype = new ViewerPlugin();

ImgPixelCounter.prototype.create = function (parent) {

    this.parent = parent;
    return parent;
};

ImgPixelCounter.prototype.pixelCounter = function () {
    if (!this.pixelCounterPanel) { //check if the pixel coutner panel exists
        //var pixelCounterPlugin = this.viewer.plugins_by_name['pixelcounter'];
         //hidding the panel
        var viewerTagPanel = this.viewer.parameters.main.queryById('tabs');
        viewerTagPanel.setVisible(false);
        var pixelcounterButton = this.viewer.toolbar.queryById('menu_viewer_pixel_counting');
        pixelcounterButton.setDisabled(true);
        me = this;
        //disable pixel counter menu
        this.pixelCounterPanel = Ext.create('BQ.Panel.PixelCounter',{
            //width: this.viewer.parameters.main.queryById('tabs').width,
            pixelCounter: this,
            viewer: this.viewer,
            phys: this.viewer.imagephys,
            autoDestroy: false,
            listeners:{
                close: function() {
                    this.destroyCanvas(); //destroys canvas when closed
                    delete this.pixelCounterPanel; //remove the panel from ImgPixelCounter
                    this.changed(); //removes threshold from image
                    viewerTagPanel.setVisible(true);
                    pixelcounterButton.setDisabled(false); //enable pixel counter menu
                    }, //brings back the metadata panel
                scope: this,
            },
        });
        //pixelCounterPanel.removeAll(false);
        //this.viewer.parameters.main.queryById('main_container').removeAll(false);
        this.viewer.parameters.main.queryById('main_container').add(this.pixelCounterPanel); //create panel
        //pixelCounterPlugin.pixelCounterPanel = pixelCounterPanel; //attaching new pixel counter panel to the plugin

    //pixelCounterPlugin
    //switches disable to true
    } //when broken down the item has to be removed from ImgExternal

};


//initalized 2 layers of canvas
//initalized on the creation of the pixel counter panel
ImgPixelCounter.prototype.initCanvas = function() {
    var control_surface_size = this.viewer.viewer_controls_surface.getBoundingClientRect();
    if (!this.canvas_mask) {

        this.canvas_mask = document.createElement('canvas');
        this.canvas_mask.setAttributeNS(null, 'class', 'pixel_counter_canvas_mask');
        this.canvas_mask.setAttributeNS(null, 'id', 'pixel_counter_canvas_mask');
        this.canvas_mask.height = control_surface_size.height;
        this.canvas_mask.width = control_surface_size.width;
        this.canvas_mask.style.zIndex = 305;
        this.canvas_mask.style.top = "0px";
        this.canvas_mask.style.left = "0px";
        this.canvas_mask.style.position = "absolute";
        this.ctx_imgmask = this.canvas_mask.getContext("2d");
        this.canvas_mask.addEventListener("click",this.onClick.bind(this),false);
        this.canvas_mask.style.visibility='hidden';
        this.parent.appendChild(this.canvas_mask);
    }

    if (!this.canvas_image ) {
        this.canvas_image = document.createElement('canvas');
        this.canvas_image.setAttributeNS(null, 'class', 'pixel_counter_canvas_image');
        this.canvas_image.setAttributeNS(null, 'id', 'pixel_counter_canvas_image');
        this.canvas_image.height = control_surface_size.height;
        this.canvas_image.width = control_surface_size.width;
        this.canvas_image.style.zIndex = 300;
        this.canvas_image.style.top = "0px";
        this.canvas_image.style.left = "0px";
        this.canvas_image.style.position = "absolute";
        this.canvas_image.style.visibility='hidden';
        this.ctx_img = this.canvas_image.getContext("2d");
        //this.image = new Image();
        //this.image.addEventListener('load',this.updateCanvas.bind(this),false) //resets canvas onload
        this.parent.appendChild(this.canvas_image);
    }

};


//updates when rescaling the images
//pulls in the tiled images from the tile render
//initalizes only on enable select
//updates new canvas when enable select is disabled and enabled
ImgPixelCounter.prototype.updateCanvas = function() {
    if (!this.canvas_image||!this.canvas_mask) {
        this.initCanvas();
    }

    // load image from data url
    this.canvas_mask.style.visibility='hidden';
    this.viewer.parameters.main.viewerContainer.setLoading(true);
    //var finished = this.constructCanvasFromWell(); //returns false if the image view is not
    var me = this;

    function waitTillFinished() {
        finished = me.constructCanvasFromWell();
        if (finished) {
            me.viewer.parameters.main.viewerContainer.setLoading(false);
            me.canvas_mask.style.visibility='visible';
            me.returnFromCanvas();
        }
        else {
            setTimeout(function(){waitTillFinished();}, 50);
        }
    }
    waitTillFinished();


};

ImgPixelCounter.prototype.returnFromCanvas = function() {
    if (this.ctx_img) {
        this.imageData = this.ctx_img.getImageData(0, 0, this.canvas_image.width, this.canvas_image.height);
        this.imagesrc = this.imageData.data;
    }
    if (this.ctx_imgmask) {
        this.ctx_imgmask.createImageData(this.canvas_mask.height,this.canvas_mask.width);
        this.maskData = this.ctx_imgmask.getImageData(0, 0, this.canvas_mask.width, this.canvas_mask.height);
        this.masksrc = this.maskData.data;
    }
};


ImgPixelCounter.prototype.tilesInTheView = function() {

    return {'inViewImages':inViewImages,'tile_tops':tile_tops,'tile_bottoms':tile_bottoms,'tile_lefts':tile_lefts,'tile_rights':tile_rights};
};

//looks through all the images in the well returns true if all the images where loaded properly
ImgPixelCounter.prototype.constructCanvasFromWell = function() {

    var control_surface_size = this.viewer.viewer_controls_surface.getBoundingClientRect();
    var tiled_viewer = this.viewer.plugins_by_name['tiles'].tiled_viewer; //finding tiled viewer in the plugin list

    //iterorate through all the tiles to find the tiles in the viewer
    var inViewImages = [];
    var tile_tops = [];
    var tile_bottoms = [];
    var tile_rights = [];
    var tile_lefts = [];

    for (var i = 0; i<tiled_viewer.well.childElementCount; i++) {
        var tile_size = tiled_viewer.well.children[i].getBoundingClientRect();
        if (
            //if edge
            ((tile_size.right <= control_surface_size.right && tile_size.right >= control_surface_size.left)||
            (tile_size.left >= control_surface_size.left && tile_size.left <= control_surface_size.right)) &&
            ((tile_size.bottom <= control_surface_size.bottom && tile_size.bottom >= control_surface_size.top) ||
            (tile_size.top >= control_surface_size.top && tile_size.top <= control_surface_size.bottom)) ||
            //if line
            (tile_size.right <= control_surface_size.right && tile_size.right >= control_surface_size.left &&
             tile_size.top <= control_surface_size.top && tile_size.bottom >= control_surface_size.bottom) ||
            (tile_size.bottom <= control_surface_size.bottom && tile_size.bottom >= control_surface_size.top &&
             tile_size.left <= control_surface_size.left && tile_size.right >= control_surface_size.right) ||
            (tile_size.left >= control_surface_size.left && tile_size.left <= control_surface_size.right &&
             tile_size.top <= control_surface_size.top && tile_size.bottom >= control_surface_size.bottom) ||
            (tile_size.top >= control_surface_size.top && tile_size.top <= control_surface_size.bottom &&
             tile_size.left <= control_surface_size.left && tile_size.right >= control_surface_size.right) ||
            //if inside
            (tile_size.right >= control_surface_size.right && tile_size.left <= control_surface_size.left &&
             tile_size.bottom >= control_surface_size.bottom && tile_size.top <= control_surface_size.top)

            ) {

            if (tiled_viewer.well.children[i].className=='tile') {
                inViewImages.push(tiled_viewer.well.children[i]); //add to the list
                tile_tops.push(tile_size.top);
                tile_bottoms.push(tile_size.bottom);
                tile_lefts.push(tile_size.left);
                tile_rights.push(tile_size.right);
            }
        }
    }

    //sizing the canvas
    this.image_view_top = tile_tops.min(); //finding the top most tile
    this.image_view_left = tile_lefts.min();
    this.image_view_right = tile_rights.max();
    this.image_view_bottom = tile_bottoms.max();

    //canvas will be the size of the control surface
    this.canvas_image.width  = control_surface_size.width;
    this.canvas_image.height = control_surface_size.height;
    this.canvas_mask.width  = control_surface_size.width;
    this.canvas_mask.height = control_surface_size.height;

    //draw width offsets on to the canvas
    this.ctx_img.createImageData(this.canvas_mask.height,this.canvas_mask.width);
    this.imageData = this.ctx_img.getImageData(0, 0, this.canvas_image.width, this.canvas_image.height);
    this.imagesrc = this.imageData.data;

    //reset image
    this.resetimage();
    this.ctx_img.putImageData(this.imageData,0,0);

    for (var i = 0; i<inViewImages.length ; i++){
        var yoffset = parseInt(inViewImages[i].style.top);
        var xoffset = parseInt(inViewImages[i].style.left);
        var scaled_imgwidth = inViewImages[i].width;
        var scaled_imgheight = inViewImages[i].height;
        //var scale = this.viewer.view().scale;
        if (location.origin+this.viewer.plugins_by_name['tiles'].tiled_viewer.loadingTile==inViewImages[i].src) { // a tile is not completely loaded
            return false
        }
        this.ctx_img.drawImage(inViewImages[i], xoffset, yoffset,scaled_imgwidth,scaled_imgheight);
    }
    return true
};

//destroy canvas panel when pixel counter panen is destroy
ImgPixelCounter.prototype.destroyCanvas = function() {
    var pixelCounterCanvasMask = document.getElementById('pixel_counter_canvas_mask');
    var pixelCounterCanvasImage = document.getElementById('pixel_counter_canvas_image');
    if (pixelCounterCanvasMask) {
        pixelCounterCanvasMask.remove();
        delete this.canvas_mask;
    }
    if (pixelCounterCanvasImage){
        pixelCounterCanvasImage.remove();
        delete this.canvas_image;
    }

};

//sets all values in the mask to 0
ImgPixelCounter.prototype.resetmask = function() {
    //
/*
    this.ctx_imgmask.fillStyle = '#000000'; //blank image
    this.ctx_imgmask.globalAlpha = 0;
    this.ctx_imgmask.fillRect(0,0,this.canvas_mask.width,this.canvas_mask.height); //fill on the entire image
    //this.ctx_imgmask.createImageData(this.canvas_mask.height,this.canvas_mask.width);
    this.maskData = this.ctx_imgmask.getImageData(0, 0, this.canvas_mask.width, this.canvas_mask.height);
    this.masksrc = this.maskData.data;
    this.ctx_imgmask.putImageData(this.maskData,0,0);
 */   
        for (var i = 0; i<(this.canvas_mask.width*this.canvas_mask.height*4); i++) {
            this.masksrc[i]   = 0;
        }
    
};

//sets the background to the same color as the tile viewer
ImgPixelCounter.prototype.resetimage = function() {
/*    this.ctx_img.fillStyle = '#434343'; //background color
    this.ctx_img.fillRect(0,0,this.canvas_image.width,this.canvas_image.height); //fill on the entire image
    //this.ctx_img.createImageData(this.canvas_mask.height,this.canvas_mask.width);
    this.imageData = this.ctx_img.getImageData(0, 0, this.canvas_image.width, this.canvas_image.height);
    this.imagesrc = this.imageData.data;
*/    
    
        for (var i = 0; i<(this.canvas_image.width*this.canvas_image.height*4); i+=4) {
            this.imagesrc[i]     = 67; //r
            this.imagesrc[i+1]   = 67; //g
            this.imagesrc[i+2]   = 67; //b
            this.imagesrc[i+3]   = 255;//a
        }
        
};


ImgPixelCounter.prototype.newImage = function () {
    this.phys_inited = false;
};


ImgPixelCounter.prototype.updateImage = function () {
    var view = this.viewer.current_view;
    //check if pixel counter panel is there
    if (this.pixelCounterPanel) {
        if (this.pixelCounterPanel.thresholdMode) {

            //view.addParams('threshold='+this.thresholdValue+',both');
            if (this.pixelCounterPanel.selectMode) {
                //should disable the scroll in selection mode
                this.initCanvas(); //checks to see if canvas exists
                this.updateCanvas(); //if canvas isnt initalized, will initalize canvas
                this.canvas_mask.style.visibility='visible'; //
                this.canvas_image.style.visibility='visible';
                this.pixelCounterPanel.updateRegionPanel();

            } else {
                if (this.canvas_mask) {
                    this.canvas_mask.style.visibility='hidden';
                    this.canvas_image.style.visibility='hidden';
                    this.pixelCounterPanel.regionCount = []; //reset region count table

                }
                this.pixelCounterPanel.lookupThreshold();
            }
        } else {
            this.pixelCounterPanel.lookupThreshold();
            if (this.canvas_mask) {
                this.canvas_mask.style.visibility='hidden';
                this.canvas_image.style.visibility='hidden';
                this.pixelCounterPanel.regionCount = []; //reset region count table
            }
        }
    }
};


ImgPixelCounter.prototype.getParams = function () {
    return this.params || {};
};

//check if threshold mode is on to redraw image
//or if selection mode is on the redraw canvas and push it to the front
ImgPixelCounter.prototype.updateView = function (view) {
    if (this.pixelCounterPanel && this.pixelCounterPanel.thresholdMode)
        view.addParams('threshold='+this.pixelCounterPanel.thresholdValue+',both');
};



ImgPixelCounter.prototype.onClick = function(e) {

    //find the offsets to canvas
    //set loading when clicked
    //this.loading_canvas.style.visibility='visible';
    //this.viewer.start_wait({op: 'gobjects', message: 'Fetching gobjects'})
    
    //this.masksrc = this.maskData.data;
    
    var xClick = e.pageX-parseInt(this.canvas_mask.style.left)-this.viewer.plugins_by_name['tiles'].tiled_viewer.left; //clicks mapped to canvas
    var yClick = e.pageY-parseInt(this.canvas_mask.style.top)-this.viewer.plugins_by_name['tiles'].tiled_viewer.top; //clicks mapped to canvas

    if(!(!(this.image_view_top<e.pageY&&this.image_view_bottom>e.pageY)||!(this.image_view_left<e.pageX&&this.image_view_right>e.pageX))){ //check if the click is on the image
        if (this.masksrc[4*(yClick*this.canvas_mask.width+xClick)+3]!=255) { //check to see if region has already been selected
            this.canvas_mask.style.visibility='hidden';
            this.viewer.parameters.main.viewerContainer.setLoading(true);
            var me = this;
            setTimeout(function(){ //set time out to allow for the loading screen to be shown
               me.connectedComponents(xClick,yClick);
               me.viewer.parameters.main.viewerContainer.setLoading(false);
               me.canvas_mask.style.visibility='visible';
            },5);
        }
    }
};


/*************************************
 *
 *      Connected components
 *
 *************************************/
ImgPixelCounter.prototype.index2xy = function(index) {

    index = parseInt(index);
    var x = parseInt(parseInt(index)/4)%this.canvas_image.width;
    var y = parseInt(parseInt(parseInt(index)/4)/this.canvas_image.width)%this.canvas_image.height;
    return {x:x,y:y};

};

ImgPixelCounter.prototype.connectedComponents = function(x,y) {

    //this.resetmask();
    this.masksrc = this.maskData.data;


    var edge_points_queue = new Array();

    var seed = 4*(y*this.canvas_image.width+x); //enforce channel zero

    edge_points_queue.push(seed);
    var label_list = [
        (this.imagesrc[seed]>=128),
        (this.imagesrc[seed+1]>=128),
        (this.imagesrc[seed+2]>=128)
    ];
    var label = this.imagesrc[seed];
    if (
        typeof label_list[0] === "undefined"||
        typeof label_list[1] === "undefined"||
        typeof label_list[2] === "undefined"
        ){
        return
    }
    var count = 0;
    while (edge_points_queue.length>0) {
        this.checkNeighbors(edge_points_queue,label_list);
        count+=1;
    }

    this.ctx_imgmask.putImageData(this.maskData,0,0);
    // remap
    var tiled_viewer = this.viewer.plugins_by_name['tiles'].tiled_viewer; //finding tiled viewer in the plugin list
    var p = tiled_viewer.toImageFromViewer({x: x - tiled_viewer.x, y: y - tiled_viewer.y});
    this.pixelCounterPanel.regionCount.push({count:count, x:p.x, y:p.y, xclick:x,yclick:y});
    //this.ctx_imgmask.font = "Bold Text, 20px, sans-serif";
    //this.ctx_imgmask.strokeText((this.pixelCounterPanel.regionCount.length-1).toString(), x, y);
    this.pixelCounterPanel.updateRegionPanel();
};


//ImgPixelCounter.prototype.complimentaryColor function(r,g,b) {
//    return {cr:cr,cg:cg,cb:cb}
//};

ImgPixelCounter.prototype.checkNeighbors = function(edge_points_queue,label_list) {


    var edge_index = parseInt(edge_points_queue.shift());
    
    //set color of the mask
    this.masksrc[edge_index]   = 0;
    this.masksrc[edge_index+1] = 255; //set green
    this.masksrc[edge_index+2] = 0;
    //this.masksrc[edge_index+3] = 255; //set transparency

    edge_value = this.index2xy(edge_index);

    //check neighbors
    x = edge_value.x;
    y = edge_value.y;
    var control_surface_size =  this.viewer.viewer_controls_surface.getBoundingClientRect();
    if (x+1 < this.canvas_image.width && x+1 < this.image_view_right-control_surface_size.left) { //check if out of the image
        var new_edge_index = edge_index+4; //check on pixel infont
        var check = this.masksrc[new_edge_index+3]; //check transparency to see if it
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            check != 255 ) { //has been put in the queue at sometime
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = 255; //set transparency
        }
    }

    if (0 <= x-1 && x-1 >= this.image_view_left-control_surface_size.left) { //check if out of the image
        var new_edge_index = edge_index-4; //check on pixel behind
        var check = this.masksrc[new_edge_index+3];
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            check != 255 ) {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = 255; //set transparency
        }
    }

    if (y+1 < this.canvas_image.height && y+1 < this.image_view_bottom-control_surface_size.top) { //check if out of the image
        var new_edge_index = edge_index+this.canvas_image.width*4; //check on pixel above
        var check = this.masksrc[new_edge_index+3];
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            check != 255 ) {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = 255; //set transparency
        }
    }

    if (0 <= y-1 && y-1 >= this.image_view_top-control_surface_size.top) { //check if out of the image
        var new_edge_index = edge_index-this.canvas_image.width*4; //check on pixel below
        var check = this.masksrc[new_edge_index+3];
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            check != 255)  {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = 255; //set transparency
        }
    }
};


//removing the connected component marked region
ImgPixelCounter.prototype.undoConnectedComponents = function(x,y) {

    //this.resetmask();
    this.maskData = this.ctx_imgmask.getImageData(0, 0, this.canvas_mask.width, this.canvas_mask.height);
    this.masksrc = this.maskData.data;

    var edge_points_queue = new Array();

    var seed = 4*(y*this.canvas_image.width+x); //enforce channel zero

    edge_points_queue.push(seed);
    var label_list = [
        (this.imagesrc[seed]>=128),
        (this.imagesrc[seed+1]>=128),
        (this.imagesrc[seed+2]>=128)
    ];
    var label = this.imagesrc[seed];
    if (
        typeof label_list[0] === "undefined"||
        typeof label_list[1] === "undefined"||
        typeof label_list[2] === "undefined"
        ){
        return
    }
    //var count = 0;
    while (edge_points_queue.length>0) {
        this.undoCheckNeighbors(edge_points_queue,label_list);
        //this.ctx_imgmask.putImageData(this.maskData,0,0);
        //count+=1;
    }

    this.ctx_imgmask.putImageData(this.maskData,0,0);
    this.pixelCounterPanel.updateRegionPanel();
};

ImgPixelCounter.prototype.undoCheckNeighbors = function(edge_points_queue,label_list) {

    var transparency = 0 //making mask transparent
    var edge_index = parseInt(edge_points_queue.shift());
    
    //set color of the mask
    this.masksrc[edge_index]   = 0;
    this.masksrc[edge_index+1] = 0; //set to black
    this.masksrc[edge_index+2] = 255;
    //this.masksrc[edge_index+3] = 255; //set transparency

    edge_value = this.index2xy(edge_index);

    //check neighbors
    x = edge_value.x;
    y = edge_value.y;
    var control_surface_size =  this.viewer.viewer_controls_surface.getBoundingClientRect();
    if (x+1 < this.canvas_image.width && x+1 < this.image_view_right-control_surface_size.left) { //check if out of the image
        var new_edge_index = edge_index+4; //check on pixel infont
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            this.masksrc[new_edge_index+3] != transparency) {
            //( this.masksrc[new_edge_index] != 0 || this.masksrc[new_edge_index+1] != 0 || this.masksrc[new_edge_index+2] != 255)) { //has been put in the queue at sometime
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }

    if (0 <= x-1 && x-1 >= this.image_view_left-control_surface_size.left) { //check if out of the image
        var new_edge_index = edge_index-4; //check on pixel behind
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            this.masksrc[new_edge_index+3] != transparency) {
            //( this.masksrc[new_edge_index] != 0 || this.masksrc[new_edge_index+1] != 0 || this.masksrc[new_edge_index+2] != 255)){
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }

    if (y+1 < this.canvas_image.height && y+1 < this.image_view_bottom-control_surface_size.top) { //check if out of the image
        var new_edge_index = edge_index+this.canvas_image.width*4; //check on pixel above
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            this.masksrc[new_edge_index+3] != transparency) {
            //( this.masksrc[new_edge_index] != 0 || this.masksrc[new_edge_index+1] != 0 || this.masksrc[new_edge_index+2] != 255)){
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }

    if (0 <= y-1 && y-1 >= this.image_view_top-control_surface_size.top) { //check if out of the image
        var new_edge_index = edge_index-this.canvas_image.width*4; //check on pixel below
        if ((this.imagesrc[new_edge_index]>=128) == label_list[0] &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list[1] &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list[2] &&
            this.masksrc[new_edge_index+3] != transparency) {
            //( this.masksrc[new_edge_index] != 0 || this.masksrc[new_edge_index+1] != 0 || this.masksrc[new_edge_index+2] != 255))  {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }
};



ImgPixelCounter.prototype.onError = function(error) {
    //BQApp.setLoading(false);
    BQ.ui.error('Error fetching resource: <br>' + error.message);
    //this.initPixelCounter();
};

ImgPixelCounter.prototype.changed = function () {
    this.viewer.need_update();
};


ImgPixelCounter.prototype.loadPreferences = function (p) {
    this.default_threshold      = 'threshold'      in p ? p.threshold      : this.default_threshold;
};



Ext.define('BQ.Panel.PixelCounter', {
    extend: 'Ext.Panel',
    itemId: 'pixelcounter-panel',
    title : 'Pixel Counter',
    region : 'east',

    viewer: null,//requiered viewer initialized object
    activeTab : 0,
    border : false,
    bodyBorder : 0,
    //collapsible : true,
    split : true,
    width : 400,
    plain : true,
    //closable: true,
    autoScroll: true,
    thresholdMode: true,
    selectMode : false,
    thresholdValue: 128,
    channel_names: { 0: 'red', 1: 'green', 2: 'blue' },
    regionCount: [],
   
    initComponent : function() {

        this.items = [];
        this.tbar = [];
        var me=this;

        var selectModeToggle = {
            xtype:'button',
            itemId : 'select_region_toggle_button',
            scale: 'large',
            text: 'Regional counts',
            iconCls: 'icon-pipette',
            enableToggle: true,
            //pressedCls: 'px-PressedStyle',
            //disabled: true,
            listeners: {
                scope: this,
                click : function() {
                   this.selectMode = !this.selectMode;
                   if(this.selectMode) this.queryById('threshold_checkbox').setValue(true);
                   this.pixelCounter.changed();
                },
            }
        };


        var closePanel = {
            xtype: 'button',
            text: 'Close',
            scale: 'large',
            //width: 60,
            iconCls: 'icon-close',
            itemId : 'pixelcounter_close_button',
            listeners: {
                scope: this,
                click: function() {
                    this.close(); //closes panel
                }
            },
        };

        var thresholdCheckBox = {
            itemId : 'threshold_checkbox',
            xtype: 'checkbox',
            fieldLabel: 'View Threshold',
            checked   : true,
            listeners: {
                scope: this,
                change: function(self,newValue,oldValue) {
                    this.thresholdMode = !this.thresholdMode;
                    this.pixelCounter.changed();
                }
            },
        };


        var thresholdSlider = Ext.create('Ext.slider.Single',{
            width: '85%',
            fieldLabel: 'Threshold Value',
            value: this.thresholdValue,
            increment: 1,
            //margin: "0 0 5 10",  // (top, right, bottom, left)
            minValue: 0, //needs to adjust with the image
            maxValue: 256,    //needs to adjust with the image
            hysteresis: 100,  // delay before firing change event to the listener
            listeners: {
                scope: this,
                afterrender: function() { //populate panel
                    this.lookupThreshold();
                },
                change : function(self,event,thumb){
                    //set a delay to refresh the values on the panel
                    if (thresholdSlider.event_timeout) clearTimeout (thresholdSlider.event_timeout);
                    var me=this;
                    thresholdSlider.event_timeout = setTimeout(function(){
                        //this.me.threshold_value.setValue(thumb.value.toString());
                        me.thresholdValue = thumb.value.toString(); //set pixel counter value
                        me.selectMode = false; //reset flag
                        me.pixelCounter.changed();
                    },  thresholdSlider.hysteresis );
                }
            }
        });

        this.mainToolbar = Ext.create('Ext.toolbar.Toolbar', {
            border: false,
            items: [
                selectModeToggle,
                { //Undo Button
                    itemId : 'px_undo_button',
                    xtype: 'button',
                    text: 'Undo',
                    scale: 'large',
                    disabled: true,     
                    listeners : {
                        scope: this,
                        click: function() { //undo runs the connected components in reverse from the last regionCount x,y
                            //clears table and displayed segmentation
                            if(this.regionCount.length) {
                                var regionCount = this.regionCount.pop(); //reset region counter table
                                this.pixelCounter.canvas_mask.style.visibility='hidden';
                                this.viewer.parameters.main.viewerContainer.setLoading(true);
                                var me = this;
                                setTimeout(function(){ //set time out to allow for the loading screen to be shown
                                   me.pixelCounter.undoConnectedComponents(regionCount.xclick,regionCount.yclick);
                                   me.viewer.parameters.main.viewerContainer.setLoading(false);
                                   me.pixelCounter.canvas_mask.style.visibility='visible';
                                },5);
                            }
                            //this.pixelCounter.changed();
                        }
                    }          
                },
                { //Resets Button
                    itemId : 'px_reset_button',
                    xtype: 'button',
                    text: 'Reset',
                    scale: 'large',
                    disabled: true,
                    //hidden: true,
                    listeners : {
                        scope: this,
                        click: function() {
                            //clears table and displayed segmentation
                            this.pixelCounter.resetmask();
                            if(this.regionCount) this.regionCount = []; //reset region counter table
                            this.pixelCounter.changed();
                        }
                    }
                },
                { //Export Button
                    itemId : 'px_export_button',
                    xtype: 'button',
                    text: 'Export CSV',
                    scale: 'large',
                    disabled: true,
                    //hidden: true,
                    listeners : {
                        scope: this,
                        click: function() { //undo runs the connected components in reverse from the last regionCount x,y
                            //clears table and displayed segmentation
                            if(this.regionCount.length>0) {
                                this.exportCSV();
                                //export csv
                            }
                        },
                    },
                },
                '->',
                closePanel,
            ]
        });

        this.thresholdPanel = Ext.create('Ext.container.Container',{
            itemId : 'px_threshold_panel',
            borders: false,
            frame: false,
            cls: 'thresholdelements',
            items: [{
                xtype: 'box',
                html: '<h2>Global Counts</h2><p>Move the slider to set a threshold value. The pixel counts above and below the threshold will be computed from the fused RGB image in the viewer per channel.</p>',
                cls: 'threshold',
                },
                thresholdCheckBox,
                thresholdSlider
             ],
        });

        this.selectPanel = Ext.create('Ext.container.Container',{
            layout: 'fit',
            html : '<h2>Regional Counts</h2><p>Click on any part of the image to segment out a region. The pixel count will be displayed below.</p>',
            itemId : 'px_selectinfo_panel',
            cls: 'threshold',
        });

        this.thresholdInfoPanel = Ext.create('Ext.container.Container', {
            //layout: 'fit',
            html: '',
            cls: 'threshold',
            //ayout: 'anchor',
        });
        

        this.tbar.push(this.mainToolbar)
        //this.items.push(this.mainToolbar);
        this.items.push(this.thresholdPanel);
        this.items.push(this.selectPanel);
        this.items.push(this.thresholdInfoPanel);

        this.pixelCounter.changed(); //initialize threshold
        return this.callParent(arguments);
    },

    listeners : {
        scope: this,
        beforecollapse: function(p,direction,animate){

            if(this.selectMode){ //disables select mode
                this.selectMode = false; //reset flag
                this.pixelCounter.changed();
                //me.selectModeToggle.setText('Regional counts');
            }
        },
        resize: function(){
            if(this.selectMode){ //disables select mode
                this.selectMode = false; //reset flag
                this.pixelCounter.changed();
                //me.selectModeToggle.setText('Regional counts');
            }
        }
    },

    lookupThreshold : function() {

        //parsing the request
        if(this.viewer.imagedim.x>10000&&this.viewer.imagedim.y>10000) {
            this.thresholdPanel.update('<h2>Image is too large</h2>');
            return;
        }
        var param = {};
        var args = this.viewer.current_view.src_args;
        var request = [];
        var a=undefined;
        for (var i=0; (a=args[i]); i++) {
            if (a.indexOf('threshold=')<0 && a.indexOf('tile=')<0)
                request.push(a);
        }
        request.push('pixelcounter='+this.thresholdValue);

        var image_uri = this.viewer.imagesrc +'?'+request.join('&');

        if (this.request_uri === image_uri) {
            this.updataGlobalPanel(this.response_doc);
            return;
        }
        this.request_uri = image_uri;

        //param['pixelcounter'] = this.threshold_value.value;
        //me=this;
        Ext.Ajax.request({
            url: image_uri,
            scope: this,
            disableCaching: false,
            timeout: 120000,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    BQ.ui.error(response.responseText);
                else if (response.responseXML) {
                    this.response_doc = response.responseXML;
                    this.updataGlobalPanel(response.responseXML);
                }
            },
        });

    },

    //stolen from bigmapPanel
    evaluateXPath: function(aNode, aExpr) {
        var xpe = new XPathEvaluator();
        var nsResolver = xpe.createNSResolver(aNode.ownerDocument == null ?
          aNode.documentElement : aNode.ownerDocument.documentElement);
        var result = xpe.evaluate(aExpr, aNode, nsResolver, 0, null);
        var found = [];
        var res;
        while (res = result.iterateNext())
          found.push(res);
        return found;
    },

    //parses xml of the document, creates and html page and write it to panel
    updataGlobalPanel : function(xmlDoc) {
        this.queryById('px_selectinfo_panel').setVisible(false);
        this.queryById('px_threshold_panel').setVisible(true);
        
        this.queryById('px_undo_button').setDisabled(true);
        this.queryById('px_reset_button').setDisabled(true);
        this.queryById('px_export_button').setDisabled(true);

        var channels = this.evaluateXPath(xmlDoc, 'resource/pixelcounts[@name="channel"]');
        var globalTitle = '<tr><th>channel</th><th >threshold</th><th>pixels</th>';

        if (this.phys.isPixelResolutionValid()) {
            globalTitle += '<th>'+this.phys.pixel_units[0]+'<sup>2</sup>'+'</th>';
        }
        globalTitle = globalTitle + '</tr>';
        var globalRows = '';
        if (channels.length==3) { //check if atleast one value
            for (var c = 0; c<channels.length; c++) { //updates panel values
                var above = self.evaluateXPath(channels[c],'tag[@name="above"]/@value')[0].value;
                var below = self.evaluateXPath(channels[c],'tag[@name="below"]/@value')[0].value;

                var channel_name = this.channel_names[c];
                var globalRowAbove = '<td>'+channel_name+'</td><td>above</td><td >'+above.toString()+'</td>';
                var globalRowBelow = '<td>'+channel_name+'</td><td>below</td><td >'+below.toString()+'</td>';
                //if found resolution points add to panel
                if (this.phys.isPixelResolutionValid()) {
                    var area_above = (parseFloat(above)*parseFloat(this.phys.pixel_size[0])*parseFloat(this.phys.pixel_size[1])).toFixed(2);
                    var area_below = (parseFloat(below)*parseFloat(this.phys.pixel_size[0])*parseFloat(this.phys.pixel_size[1])).toFixed(2);
                    globalRowAbove += '<td>'+area_above.toString()+'</td>';
                    globalRowBelow += '<td>'+area_below.toString()+'</td>';
                }
                globalRows += '<tr>'+globalRowAbove+'</tr><tr>'+globalRowBelow+'</tr>';
            }
        }
        else {
            //error didnt not find image service pixel counter
            //BQ.ui.error('Didnt not find image service pixel counter information from image service');
        }
        var html = '<table>'+globalTitle+globalRows+"</table>";

        this.thresholdInfoPanel.update(html);
    },

    updateRegionPanel : function(){
        this.queryById('px_selectinfo_panel').setVisible(true);
        this.queryById('px_threshold_panel').setVisible(false);

        
        
        //set usability of the buttons
        if (this.regionCount.length>0){
            this.queryById('px_undo_button').setDisabled(false);
            this.queryById('px_reset_button').setDisabled(false);
            this.queryById('px_export_button').setDisabled(false);
        } else {
            this.queryById('px_undo_button').setDisabled(true);
            this.queryById('px_reset_button').setDisabled(true); 
            this.queryById('px_export_button').setDisabled(true);           
        }
        

        var html = '';
        if (this.regionCount.length>0) { //canvas else set panel to zero
            var regionTitle = '<tr><th>index</th><th>centroid</th><th>pixels</th>';
            var scale = this.viewer.view().scale;

            if (this.phys.isPixelResolutionValid()) {
                regionTitle += '<th>'+this.phys.pixel_units[0]+'<sup>2</sup>'+'</th>';
            }
            regionTitle = regionTitle + '</tr>';
            var regionRows = '';
            for (var r = 0; r<this.regionCount.length; r++) {
                regionRows += '<tr><td>'+r.toString()+'</td>';
                regionRows += '<td>'+this.regionCount[r].x + ','+ this.regionCount[r].y+'</td>';
                var count = this.regionCount[r].count;//this.viewer.view().scale //find scale
                var scaled_count = (count/(scale*scale)).toFixed(0);
                regionRows += '<td >'+scaled_count.toString()+'</td>';
                if (this.phys.isPixelResolutionValid()) {
                    
                    var area = (parseFloat(scaled_count)*parseFloat(this.phys.pixel_size[0])*parseFloat(this.phys.pixel_size[1])).toFixed(2);
                    regionRows += '<td>'+area+'</td>';
                }
            }
            
            regionRows += '</tr>';
            var html = '<table>'+regionTitle+regionRows+'</table>'+'<br><br>';
            //this.thresholdInfoPanel.update(html)
        } else {
            //error no region evaluated
        }
        this.thresholdInfoPanel.update(html);
    },
    
    exportCSV : function() {
        if (this.regionCount.length>0) {
            var scale = this.viewer.view().scale;
            var CsvDocument = '';
            CsvDocument +=  'index,centroid,pixels'//title
            if (this.phys.isPixelResolutionValid()) {
                CsvDocument += ','+this.phys.pixel_units[0]+'^2';
            }
            CsvDocument += '\n';
            for (var r = 0; r<this.regionCount.length; r++) {
                var count = this.regionCount[r].count;//this.viewer.view().scale //find scale
                var scaled_count = (count/(scale*scale)).toFixed(0);
                
                //row
                CsvDocument += r.toString() + ',"' + this.regionCount[r].x + ',' + this.regionCount[r].y + '",' + scaled_count.toString()
                if (this.phys.isPixelResolutionValid()) {
                    
                    var area = (parseFloat(scaled_count)*parseFloat(this.phys.pixel_size[0])*parseFloat(this.phys.pixel_size[1])).toFixed(2);
                    CsvDocument += ','+area;
                }
                CsvDocument += '\n';
            }   
           
            window.open('data:text/csv;charset=utf-8,' + escape(CsvDocument)); //download
            
        }
    },
});

