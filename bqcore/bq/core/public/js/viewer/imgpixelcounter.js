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
        });
        this.pixelCounterPanel.on('close',function() {
            this.resetPixelRegionCounter();
            this.destroyPixelCounterDisplay(); //destroys display when closed
            delete this.pixelCounterPanel; //remove the panel from ImgPixelCounter
            this.changed(); //removes threshold from image
            viewerTagPanel.setVisible(true);
            pixelcounterButton.setDisabled(false); //enable pixel counter menu
            //brings back the metadata panel            
        },this)
        this.viewer.parameters.main.queryById('main_container').add(this.pixelCounterPanel); //create panel

    //pixelCounterPlugin
    //switches disable to true
    } //when broken down the item has to be removed from ImgExternal

};


//initalized 2 layers of canvas
//initalized on the creation of the pixel counter panel
//iinitlizs the pixel counter overlay
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
        this.parent.appendChild(this.canvas_image);
    }

    //marking of the ids
    //needs to be above everything
    if (!this.svgdoc) {
        this.svgdoc = document.createElementNS('http://www.w3.org/2000/svg', "svg");
        this.svgdoc.setAttributeNS(null, 'class', 'pixel_counter_svg_id_label_surface');
        this.svgdoc.setAttributeNS(null, 'id', 'pixel_counter_svg_id_label_surface');
        this.svgdoc.setAttribute('height', control_surface_size.height);
        this.svgdoc.setAttribute('width', control_surface_size.width);
        this.svgdoc.style.position = "absolute";
        this.svgdoc.style.top = "0px";
        this.svgdoc.style.left = "0px";
        this.svgdoc.style.visibility='hidden';
        this.svgdoc.style.zIndex = 310;
        this.svgdoc.addEventListener("click",this.onClick.bind(this),false);
        this.parent.appendChild(this.svgdoc);
    }
};

/*
ImgPixelCounter.prototype.updataGlobalPixelCounterCanvas = function() {
    var control_surface_size = this.viewer.viewer_controls_surface.getBoundingClientRect();
    if (!this.canvas_image) {
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
        this.parent.appendChild(this.canvas_image);
    }
    var me = this;
    function waitTillFinished() {
        var finished = me.constructCanvasFromWell();
        if (finished) {
            
            me.imageData = me.ctx_img.getImageData(0, 0, me.canvas_image.width, me.canvas_image.height);
            me.imagesrc = me.imageData.data;
            
            //background of the image viewer
            var globalThresholdCount = {r:{a:0,b:0},g:{a:0,b:0},b:{a:0,b:0}};
            
            for (var i = 0; i<(me.canvas_image.width*me.canvas_image.height*4); i+=4) {
                if (me.pixelCounterPanel.thresholdValue>me.imagesrc[i]) globalThresholdCount['r']['a']+=1;
                else globalThresholdCount['r']['b']+=1;
                if (me.pixelCounterPanel.thresholdValue>me.imagesrc[i+1]) globalThresholdCount['b']['a']+=1;
                else globalThresholdCount['b']['b']+=1;
                if (me.pixelCounterPanel.thresholdValue>me.imagesrc[i+2]) globalThresholdCount['g']['a']+=1;
                else globalThresholdCount['g']['b']+=1;
            } 
        
            me.pixelCounterPanel.updataGlobalPanel(globalThresholdCount);
        }
        else {
            setTimeout(function(){waitTillFinished();}, 50);
        }
    }
    waitTillFinished();
    

    
}
*/

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
        var finished = me.constructCanvasFromWell();
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

    //draw width offsets on to the canvas
    this.ctx_img.createImageData(this.canvas_image.height,this.canvas_image.width);
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
ImgPixelCounter.prototype.destroyPixelCounterDisplay = function() {
    var pixelCounterCanvasMask = document.getElementById('pixel_counter_canvas_mask');
    var pixelCounterCanvasImage = document.getElementById('pixel_counter_canvas_image');
    var pixelCounterSGVOverlay = document.getElementById('pixel_counter_svg_id_label_surface');
    
    if (pixelCounterCanvasMask) {
        pixelCounterCanvasMask.remove();
        delete this.canvas_mask;
    }
    if (pixelCounterCanvasImage){
        pixelCounterCanvasImage.remove();
        delete this.canvas_image;
    }
    if (pixelCounterSGVOverlay){
        pixelCounterSGVOverlay.remove();
        delete this.svgdoc;
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

            if (this.pixelCounterPanel.selectMode) {
                this.updateCanvas(); //if canvas isnt initalized, will initalize canvas
                this.canvas_mask.style.visibility = 'visible'; //
                this.canvas_image.style.visibility = 'visible';
                this.svgdoc.style.visibility = 'visible';
                this.pixelCounterPanel.updateRegionPanel();

            } else {
                if (this.canvas_mask) {
                    this.canvas_mask.style.visibility = 'hidden';
                    this.canvas_image.style.visibility = 'hidden';
                    this.svgdoc.style.visibility = 'hidden';
                    this.resetPixelRegionCounter();

                }
                this.pixelCounterPanel.lookupThreshold();
            }
        } else {
            this.pixelCounterPanel.lookupThreshold();
            if (this.canvas_mask) {
                this.canvas_mask.style.visibility = 'hidden';
                this.canvas_image.style.visibility = 'hidden';
                this.svgdoc.style.visibility = 'hidden';
                this.resetPixelRegionCounter();
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
    
    var xClick = e.pageX-parseInt(this.canvas_mask.style.left)-this.viewer.plugins_by_name['tiles'].tiled_viewer.left; //clicks mapped to canvas
    var yClick = e.pageY-parseInt(this.canvas_mask.style.top)-this.viewer.plugins_by_name['tiles'].tiled_viewer.top; //clicks mapped to canvas

    if(!(!(this.image_view_top<e.pageY&&this.image_view_bottom>e.pageY)||!(this.image_view_left<e.pageX&&this.image_view_right>e.pageX))){ //check if the click is on the image
        if (this.masksrc[4*(yClick*this.canvas_mask.width+xClick)+3]!=255) { //check to see if region has already been selected
            this.canvas_mask.style.visibility = 'hidden';
            this.viewer.parameters.main.viewerContainer.setLoading(true);
            var me = this;
            setTimeout(function(){ //set time out to allow for the loading screen to be shown
               me.connectedComponents(xClick,yClick);
               me.viewer.parameters.main.viewerContainer.setLoading(false);
               me.canvas_mask.style.visibility = 'visible';
               
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

ImgPixelCounter.prototype.setText2SVG = function(text,id,x,y) {
    var textelement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    textelement.setAttribute("id", id);
    textelement.setAttribute("x", x);
    textelement.setAttribute("y", y);
    textelement.setAttribute('style', "font-family:Arial;font-size: 14; fill:blue; text-shadow: #FFFFFF 1px 1px 1px ;");//rgba(0,0,0,0.1) #FFFFFF
    textelement.textContent = text;
    this.svgdoc.appendChild(textelement);
    //textelement.addEventListener("click", svgclick, false);
    //textelement.addEventListener("keypress", onkeypress, false);
};

ImgPixelCounter.prototype.removeTextFromSVG = function(id){
    var svgTextElement = this.svgdoc.getElementById(id);
    
    if(svgTextElement) this.svgdoc.removeChild(svgTextElement);
};

ImgPixelCounter.prototype.connectedComponents = function(x,y) {

    var maskColor = {r:255,g:0,b:255}; //magenta
    var transparency = 255;

    //this.resetmask();
    this.masksrc = this.maskData.data;


    var edge_points_queue = new Array();

    var seed = 4*(y*this.canvas_image.width+x); //enforce channel zero

    edge_points_queue.push(seed);
    var label_list = {
        r:(this.imagesrc[seed]>=128),
        g:(this.imagesrc[seed+1]>=128),
        b:(this.imagesrc[seed+2]>=128)
    };
    var label = this.imagesrc[seed];
    if (
        typeof label_list.r === "undefined"||
        typeof label_list.g === "undefined"||
        typeof label_list.b === "undefined"
        ){
        return
    }
    var count = 0;
    while (edge_points_queue.length>0) {
        this.checkNeighbors(edge_points_queue,label_list,transparency, maskColor);
        count+=1;
    }

    this.ctx_imgmask.putImageData(this.maskData,0,0);
    // remap
    var tiled_viewer = this.viewer.plugins_by_name['tiles'].tiled_viewer; //finding tiled viewer in the plugin list
    var p = tiled_viewer.toImageFromViewer({x: x - tiled_viewer.x, y: y - tiled_viewer.y});
    
    //scaling the counts
    var scale = this.viewer.view().scale;
    var scaled_count = (count/(scale*scale)).toFixed(0);
    var phys = this.viewer.imagephys;
    
    if (phys.isPixelResolutionValid()) {
        var area = (parseFloat(scaled_count)*parseFloat(phys.pixel_size[0])*parseFloat(phys.pixel_size[1])).toFixed(2);
        this.pixelCounterPanel.regionCount.push({index:this.pixelCounterPanel.idCount, pixels:scaled_count, x:p.x, y:p.y, xclick:x,yclick:y,svgid:'svg_text_element_'+(this.pixelCounterPanel.idCount), area:area});
    } else {
        this.pixelCounterPanel.regionCount.push({index:this.pixelCounterPanel.idCount, pixels:scaled_count, x:p.x, y:p.y, xclick:x,yclick:y,svgid:'svg_text_element_'+(this.pixelCounterPanel.idCount)});        
    }
    
    //update svg element    
    this.setText2SVG((this.pixelCounterPanel.idCount).toString(),'svg_text_element_'+(this.pixelCounterPanel.idCount),x,y)
    this.pixelCounterPanel.idCount+=1; //setting for the next region
    this.pixelCounterPanel.updateRegionPanel();
};


//removing the connected component marked region
ImgPixelCounter.prototype.undoConnectedComponents = function(x,y,id) {

    var transparency = 0; //making mask transparent
    var maskColor = {r:0,g:0,b:255,a:0}; //set to black

    //this.resetmask();
    this.maskData = this.ctx_imgmask.getImageData(0, 0, this.canvas_mask.width, this.canvas_mask.height);
    this.masksrc = this.maskData.data;

    var edge_points_queue = new Array();

    var seed = 4*(y*this.canvas_image.width+x); //enforce channel zero

    edge_points_queue.push(seed);
    var label_list = {
        r:(this.imagesrc[seed]>=128),
        g:(this.imagesrc[seed+1]>=128),
        b:(this.imagesrc[seed+2]>=128)
    };
    var label = this.imagesrc[seed];
    if (
        typeof label_list.r === "undefined"||
        typeof label_list.g === "undefined"||
        typeof label_list.b === "undefined"
        ){
        return
    }
    //var count = 0;
    while (edge_points_queue.length>0) {
        this.checkNeighbors(edge_points_queue,label_list,transparency,maskColor);
        //this.ctx_imgmask.putImageData(this.maskData,0,0);
        //count+=1;
    }
    this.removeTextFromSVG(id);
    this.ctx_imgmask.putImageData(this.maskData,0,0);
    this.pixelCounterPanel.updateRegionPanel();
};


ImgPixelCounter.prototype.checkNeighbors = function(edge_points_queue,label_list, transparency, maskColor) {
    //Find the connected component
    //uses the transparency as a marker for past check pixels
    
    var edge_index = parseInt(edge_points_queue.shift());
    
    //set color of the mask
    this.masksrc[edge_index]   = maskColor.r;
    this.masksrc[edge_index+1] = maskColor.g;
    this.masksrc[edge_index+2] = maskColor.b;
    //this.masksrc[edge_index+3] = 255; //set transparency

    edge_value = this.index2xy(edge_index);

    //check neighbors
    x = edge_value.x;
    y = edge_value.y;
    var control_surface_size =  this.viewer.viewer_controls_surface.getBoundingClientRect();
    if (x+1 < this.canvas_image.width && x+1 < this.image_view_right-control_surface_size.left) { //check if out of the image
        var new_edge_index = edge_index+4; //check on pixel infont
        if ((this.imagesrc[new_edge_index]>=128) == label_list.r &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list.g &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list.b &&
            this.masksrc[new_edge_index+3] != transparency ) { //has been put in the queue at sometime
            edge_points_queue.push(new_edge_index); //check transparency to see if it
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }

    if (0 <= x-1 && x-1 >= this.image_view_left-control_surface_size.left) { //check if out of the image
        var new_edge_index = edge_index-4; //check on pixel behind
        if ((this.imagesrc[new_edge_index]>=128) == label_list.r &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list.g &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list.b &&
            this.masksrc[new_edge_index+3] != transparency ) {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }

    if (y+1 < this.canvas_image.height && y+1 < this.image_view_bottom-control_surface_size.top) { //check if out of the image
        var new_edge_index = edge_index+this.canvas_image.width*4; //check on pixel above
        if ((this.imagesrc[new_edge_index]>=128) == label_list.r &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list.g &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list.b &&
            this.masksrc[new_edge_index+3] != transparency  ) {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }

    if (0 <= y-1 && y-1 >= this.image_view_top-control_surface_size.top) { //check if out of the image
        var new_edge_index = edge_index-this.canvas_image.width*4; //check on pixel below
        if ((this.imagesrc[new_edge_index]>=128) == label_list.r &&
            (this.imagesrc[new_edge_index+1]>=128) == label_list.g &&
            (this.imagesrc[new_edge_index+2]>=128) == label_list.b &&
            this.masksrc[new_edge_index+3] != transparency )  {
            edge_points_queue.push(new_edge_index);
            this.masksrc[new_edge_index+3] = transparency; //set transparency
        }
    }
};


//resets all the elements to the base level
ImgPixelCounter.prototype.resetPixelRegionCounter = function() {
    this.resetsvg();
    this.resetmask();
    if(this.pixelCounterPanel.regionCount) this.pixelCounterPanel.regionCount = []; //reset region counter table
    this.pixelCounterPanel.idCount = 0; //resets the ids
};


//sets the background to the same color as the tile viewer
ImgPixelCounter.prototype.resetimage = function() {
    
    //background of the image viewer
    var imgViewerBackground = {r:67, g:67, b:67, a:255};
    
    for (var i = 0; i<(this.canvas_image.width*this.canvas_image.height*4); i+=4) {
        this.imagesrc[i]     = imgViewerBackground.r; //r
        this.imagesrc[i+1]   = imgViewerBackground.g; //g
        this.imagesrc[i+2]   = imgViewerBackground.b; //b
        this.imagesrc[i+3]   = imgViewerBackground.a;//a
    }
};


//removes all child elements
ImgPixelCounter.prototype.resetsvg = function() {
    if(this.svgdoc) {
        while(this.svgdoc.firstChild) {this.svgdoc.removeChild(this.svgdoc.firstChild);}
    }
};


//sets all values in the mask to 0
ImgPixelCounter.prototype.resetmask = function() {
    if (this.masksrc) {
        this.masksrc = this.maskData.data;
        for(var i = 0; i<(this.canvas_mask.width*this.canvas_mask.height*4); i++) {this.masksrc[i] = 0;}
        this.ctx_imgmask.putImageData(this.maskData,0,0);
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
    layout: { type: 'vbox', pack: 'start', align: 'stretch' },
    viewer: null,//requiered viewer initialized object
    activeTab : 0,
    //border : false,
    bodyBorder : 0,
    split : true,
    width : 400,
    plain : true,
    autoScroll: true,
    thresholdMode: true,
    selectMode : false,
    thresholdValue: 128,
    channel_names: { 0: 'red', 1: 'green', 2: 'blue' },
    regionCount: [],
    idCount: 0, //keeps track of the ids for each region
   
    initComponent : function() {

        this.items = []; //reset panel items
        this.regionCount = []; //reset regionCount

        var thresholdSlider = Ext.create('Ext.slider.Single',{
            width: '85%',
            fieldLabel: 'Threshold Value',
            value: this.thresholdValue,
            increment: 1,
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

        this.thresholdPanel = Ext.create('Ext.container.Container',{
            itemId : 'px_threshold_panel',
            borders: false,
            frame: false,
            cls: 'thresholdelements',
            items: [{
                    xtype: 'box',
                    html: '<h2>Global Counts</h2><p>Move the slider to set a threshold value. The pixel counts above and below the threshold will be computed from the fused RGB image in the viewer per channel.</p>',
                    cls: 'threshold',
                },{ //threshold checkbox
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
                },
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
        
        
        //GRID
        var fieldList = ['index','x','y','pixels'];
        var columns = [{
            header: 'id',
            dataIndex: 'index',
        },{
            header: 'x',
            dataIndex: 'x',
        },{
            header: 'y',
            dataIndex: 'y',
        },{
            header: 'pixels',
            dataIndex: 'pixels',
        }];
        var fields = [
            {name: 'index', type: 'float'},
            {name: 'x', type: 'float'},
            {name: 'y', type: 'float'},
            {name: 'pixels', type: 'float'}
        ]
        if (this.phys.isPixelResolutionValid()) {
            fieldList.push('area');
            columns.push({
                header: this.phys.pixel_units[0]+'<sup>2</sup>',
                dataIndex: 'area',
            });
            fields.push({name: 'area', type: 'float'});
        }
        
        

        Ext.define('bq.pixelcount.RegionCounts', {
            extend: 'Ext.data.Model',
            fields: fields,
        });        
        
        this.regionCountStore = Ext.create('Ext.data.Store', {
            model: 'bq.pixelcount.RegionCounts',
            storeId: 'regionCountStore',
            fields: fieldList,
            allowDeslect: true,
            proxy: {
                type: 'memory',
                reader: {
                    root: 'items'
                }
            },
            sorters: [{
                property: 'index',
                direction: 'desc'
            }]
        });
        
        this.regionCountGrid = Ext.create('Ext.grid.Panel', {
            //title: 'regionCountGrid',
            itemId : 'px_regioncount_grid',
            store: this.regionCountStore,
            multiSelect: true,
            
            columns: {
                items: columns,
                defaults: {flex: 1},
            },
            
            flex: 2,
            hidden: true,
            border : false,
            renderTo: Ext.getBody(),
            tbar: [{ //Delete button
                itemId : 'px_delete_button',
                xtype: 'button',
                text: 'Delete',
                iconCls: 'icon-delete', 
                scale: 'large',
                disabled: true,    
                listeners : {
                    scope: this,
                    click: function() {
                        //deletes selected elements
                        var grid = this.queryById('px_regioncount_grid');
                        var selectedRecord = grid.getSelectionModel().getSelection()
                        var deleteRows = [];
                        for (var i = 0; i<selectedRecord.length; i++){
                            deleteRows.push(selectedRecord[i].data.index);
                        }
                        var regionCountDeletes = [];
                        var regionCount = [];
                        for (var i = 0; i<this.regionCount.length;i++) {
                            if (deleteRows.indexOf(this.regionCount[i].index) >= 0) {
                                regionCountDeletes.push(this.regionCount[i])
                            }
                            else {
                                regionCount.push(this.regionCount[i])
                            }
                        }
                        
                        //delete all the rows at once
                        this.pixelCounter.canvas_mask.style.visibility = 'hidden';
                        this.viewer.parameters.main.viewerContainer.setLoading(true);
                        var me = this;
                        var regionCountElement = this.regionCount[i];
                        setTimeout(function(){ //set time out to allow for the loading screen to be shown
                           for (var i=0; i<regionCountDeletes.length; i++) { 
                               me.pixelCounter.undoConnectedComponents(regionCountDeletes[i].xclick,regionCountDeletes[i].yclick,regionCountDeletes[i].svgid);
                           }    
                           me.viewer.parameters.main.viewerContainer.setLoading(false);
                           me.pixelCounter.canvas_mask.style.visibility = 'visible';
                        },5);
                        this.regionCount = regionCount;
                        this.updateRegionPanel();

                    }
                },        
            },
            { //Resets Button
                itemId : 'px_reset_button',
                iconCls: 'converter', 
                xtype: 'button',
                text: 'Reset',
                scale: 'large',
                disabled: true,
                //hidden: true,
                listeners : {
                    scope: this,
                    click: function() {
                        //clears table and displayed segmentation
                        this.pixelCounter.resetPixelRegionCounter();
                        this.pixelCounter.changed();
                    }
                }
            },
            '->',            
            { //Export Button
                itemId : 'px_export_button',
                xtype: 'button',
                text: 'Export CSV',
                iconCls: 'external',
                scale: 'large',
                disabled: true,
                listeners : {
                    scope: this,
                    click: function() {
                        if(this.regionCount.length>0) {
                            this.exportCSV();
                        }
                    },
                },
            }],  
        });

        this.tbar= [{//toggle button
                xtype:'button',
                itemId : 'select_region_toggle_button',
                scale: 'large',
                text: 'Regional counts',
                iconCls: 'icon-pipette',
                enableToggle: true,
                //pressedCls: 'px-PressedStyle',
                listeners: {
                    scope: this,
                    click : function() {
                       this.selectMode = !this.selectMode;
                       if(this.selectMode) this.queryById('threshold_checkbox').setValue(true);
                       if(!this.selectMode) this.pixelCounter.resetPixelRegionCounter()
                       this.pixelCounter.changed();
                    },
                }
            },'->',{//close button
                xtype: 'button',
                text: 'Close',
                scale: 'large',
                iconCls: 'icon-close',
                itemId : 'pixelcounter_close_button',
                listeners: {
                    scope: this,
                    click: function() {
                        this.close(); //closes panel
                    }
                },
            },
        ];

        this.items.push(this.thresholdPanel);
        this.items.push(this.selectPanel);
        this.items.push(this.thresholdInfoPanel);
        this.items.push(this.regionCountGrid);
        
        //beforeresize

        this.pixelCounter.changed(); //initialize threshold
        
        
        return this.callParent(arguments);
    },
    
    listeners: {
        resize: function(){ //returns to global count mode
            if(this.selectMode){ //disables select mode
                this.selectMode = false; //reset flag
                this.queryById('select_region_toggle_button').toggle(false);
                this.pixelCounter.changed();
            }
        }
    },
    
    lookupThreshold : function() {
        //parsing the request
        
        //set limit on the global counts if image is too large
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
/*

    updataGlobalPanel : function(globalThresholdCount) {
        this.queryById('px_selectinfo_panel').setVisible(false);
        this.queryById('px_threshold_panel').setVisible(true);
        this.queryById('px_regioncount_grid').setVisible(false);
        
        var globalTitle = '<tr><th>channel</th><th >threshold</th><th>pixels</th>';

        if (this.phys.isPixelResolutionValid()) {
            globalTitle += '<th>'+this.phys.pixel_units[0]+'<sup>2</sup>'+'</th>';
        }
        globalTitle = globalTitle + '</tr>';
        var globalRows = '';
        var channels = ['r','g','b'];
        for (var c = 0; c<3; c++) { //updates panel values
            
            var scale = this.viewer.view().scale;              
            var above = globalThresholdCount[channels[c]].a/(scale*scale);
            var below = globalThresholdCount[channels[c]].b/(scale*scale);

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
        var html = '<table>'+globalTitle+globalRows+"</table>";

        this.thresholdInfoPanel.update(html);
    },
*/
    //parses xml of the document, creates and html page and write it to panel
    updataGlobalPanel : function(xmlDoc) {
        this.queryById('px_selectinfo_panel').setVisible(false);
        this.queryById('px_threshold_panel').setVisible(true);
        this.queryById('px_regioncount_grid').setVisible(false);
        

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
        
        var regionCountGrid = this.queryById('px_regioncount_grid').setVisible(true);
        
        var html = '';
        this.thresholdInfoPanel.update(html);
        regionCountGrid.store.loadData(this.regionCount);
        regionCountGrid.getView().refresh();
        
        //set usability of the buttons
        if (this.regionCount.length>0){
            this.queryById('px_reset_button').setDisabled(false);
            this.queryById('px_export_button').setDisabled(false);
            this.queryById('px_delete_button').setDisabled(false);
        } else {
            this.queryById('px_reset_button').setDisabled(true); 
            this.queryById('px_export_button').setDisabled(true); 
            this.queryById('px_delete_button').setDisabled(true);         
        }
    },
    
    exportCSV : function() {
        //writes the region count info to csv
        if (this.regionCount.length>0) {
            var scale = this.viewer.view().scale;
            var CsvDocument = '';
            CsvDocument +=  'index,x,y,pixels'//title
            if (this.phys.isPixelResolutionValid()) {
                CsvDocument += ','+this.phys.pixel_units[0]+'^2';
            }
            CsvDocument += '\r\n';
            for (var r = 0; r<this.regionCount.length; r++) {
                //row
                CsvDocument += this.regionCount[r].index + ',' + this.regionCount[r].x + ',' + this.regionCount[r].y + ',' + this.regionCount[r].pixels;
                if (this.phys.isPixelResolutionValid()) {
                    CsvDocument += ','+this.regionCount[r].area;;
                }
                CsvDocument += '\r\n';
            }   
           
            window.open('data:text/csv;charset=utf-8,' + encodeURIComponent(CsvDocument), 'areas.csv'); //download
            
        }
    },
});

