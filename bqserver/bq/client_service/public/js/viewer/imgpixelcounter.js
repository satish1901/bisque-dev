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
    if (!this.pixelCounterPlugin) { //check if the pixel coutner panel exists
        var pixelCounterPlugin = this.viewer.plugins_by_name['pixelcounter'];
         //hidding the panel
        var viewerTagPanel = this.viewer.parameters.main.queryById('tabs');
        viewerTagPanel.setVisible(false);
        var pixelcounterButton = this.viewer.toolbar.queryById('menu_viewer_pixel_counting')
        pixelcounterButton.setDisabled(true);
        me = this;
        //disable pixel counter menu
        this.pixelCounterPanel = Ext.create('BQ.Panel.PixelCounter',{
            //width: this.viewer.parameters.main.queryById('tabs').width,
            pixelCounter: this,
            viewer: this.viewer,
            autoDestroy: false,
            listeners:{
                close: function() {
                    pixelCounterPlugin.destroyCanvas(); //destroys canvas when closed
                    pixelCounterPlugin.changed(); //removes threshold from image
                    viewerTagPanelsetVisible(true);
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
    return {'inViewImages':inViewImages,'tile_tops':tile_tops,'tile_bottoms':tile_bottoms,'tile_lefts':tile_lefts,'tile_rights':tile_rights};
}

//looks through all the images in the well returns true if all the images where loaded properly
ImgPixelCounter.prototype.constructCanvasFromWell = function() {
    /*
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
    }*/
    var control_surface_size = this.viewer.viewer_controls_surface.getBoundingClientRect();
    var tilesinview = this.tilesInTheView();
    var inViewImages = tilesinview.inViewImages;
    //sizing the canvas
    this.image_view_top = tilesinview.tile_tops.min(); //finding the top most tile
    this.image_view_left = tilesinview.tile_lefts.min();
    this.image_view_right = tilesinview.tile_rights.max();
    this.image_view_bottom = tilesinview.tile_bottoms.max();

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
        for (var i = 0; i<(this.canvas_mask.width*this.canvas_mask.height*4); i++) {
            this.masksrc[i]   = 0;
        }
};

//sets the background to the same color as the tile viewer
ImgPixelCounter.prototype.resetimage = function() {
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
                this.pixelCounterPanel.updataRegionPanel();

            } else {
                if (this.canvas_mask) {
                    this.canvas_mask.style.visibility='hidden';
                    this.canvas_image.style.visibility='hidden';
                    if(this.pixelCounterPanel.regionCount){
                        delete this.pixelCounterPanel.regionCount;
                    }
                }
                this.pixelCounterPanel.lookupThreshold();
            }
        } else {
            this.pixelCounterPanel.lookupThreshold();
            if (this.canvas_mask) {
                this.canvas_mask.style.visibility='hidden';
                this.canvas_image.style.visibility='hidden';
                if(this.pixelCounterPanel.regionCount){
                    delete this.pixelCounterPanel.regionCount;
                }
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
        view.addParams('threshold='+this.thresholdValue+',both');
};



ImgPixelCounter.prototype.onClick = function(e) {

    //find the offsets to canvas
    //set loading when clicked
    //this.loading_canvas.style.visibility='visible';
    //this.viewer.start_wait({op: 'gobjects', message: 'Fetching gobjects'})

    xClick = e.pageX-parseInt(this.canvas_mask.style.left)-this.viewer.plugins_by_name['tiles'].tiled_viewer.left;
    yClick = e.pageY-parseInt(this.canvas_mask.style.top)-this.viewer.plugins_by_name['tiles'].tiled_viewer.top;

    if(!(!(this.image_view_top<e.pageY&&this.image_view_bottom>e.pageY)||!(this.image_view_left<e.pageX&&this.image_view_right>e.pageX))){ //check if the click is on the image
        this.canvas_mask.style.visibility='hidden';
        this.viewer.parameters.main.viewerContainer.setLoading(true);
        var me = this;
        setTimeout(function(){ //set time out to allow for the loading screen to be shown
           me.connectedComponents(xClick,yClick);
           me.viewer.parameters.main.viewerContainer.setLoading(false);
           me.canvas_mask.style.visibility='visible';
        },5);
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

    this.resetmask();
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
        //this.ctx_imgmask.putImageData(this.maskData,0,0);
        count+=1;
    }

    this.ctx_imgmask.putImageData(this.maskData,0,0);
    this.pixelCounterPanel.regionCount = {'count':count,'xclick':x,'yclick':y};
    this.pixelCounterPanel.updataRegionPanel();
};


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
    thresholdMode: true,
    selectMode : false,

    initComponent : function() {

        this.items = [];
        var me=this;

        var selectModeToggle = {
            xtype:'button',
            itemId : 'select_region_toggle_button',
            scale: 'large',
            text: 'Regional counts',
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
            width: 60,
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
        

        this.thresholdSlider = Ext.create('Ext.slider.Single',{
            width: '85%',
            fieldLabel: 'Threshold Value',
            value: 128,
            increment: 1,
            //margin: "0 0 5 10",  // (top, right, bottom, left)
            minValue: 0, //needs to adjust with the image
            maxValue: 256,    //needs to adjust with the image
            hysteresis: 100,  // delay before firing change event to the listener
            listeners: {
                scope: this,
                afterrender: function() { //populate panel
                    me.pixelCounter.thresholdValue = me.thresholdSlider.value;
                    me.lookupThreshold();
                },      
                change : function(self,event,thumb){
                    //set a delay to refresh the values on the panel
                    if (this.thresholdSlider.event_timeout) clearTimeout (this.thresholdSlider.event_timeout);
                    me=this;
                    this.thresholdSlider.event_timeout = setTimeout(function(){
                        //this.me.threshold_value.setValue(thumb.value.toString());
                        me.pixelCounter.thresholdValue = thumb.value.toString(); //set pixel counter value
                        me.selectMode = false; //reset flag
                        me.pixelCounter.changed();
                    },  me.thresholdSlider.hysteresis );                      
                }
            }
        });

        this.mainToolbar = Ext.create('Ext.toolbar.Toolbar', {
            //width : 400,
            //width: '100%',
            //layout: 'fit',
            border: false,
            items: [
                selectModeToggle,
                {
                    height: 25,
                    xtype: 'button',
                    text: 'Export',
                    disabled: true,
                    hidden: true,
                },
                '->',
                closePanel,
            ]
        });

        this.thesholdPanel = Ext.create('Ext.container.Container',{
            itemId : 'px_threshold_panel',
            borders: false,
            frame: false,
            cls: 'thresholdelements',
            items: [{
                xtype: 'box',
                html: '<h2>Global Counts</h2><p>In this mode, move the slider to set a threshold value. The counts of pixel values above and below the threshold value are displayed below from the rgb image in the viewer.</p>',
                cls: 'threshold',
                },
                thresholdCheckBox,
                this.thresholdSlider
             ],
        });

        this.selectPanel = Ext.create('Ext.container.Container',{
            layout: 'fit',
            html : '<h2>Regional Counts</h2><p>In this mode, click on any part of the image to segment out a region. The pixel count for the select region will be displayed below.</p>',
            itemId : 'px_selectinfo_panel',
            cls: 'threshold',
        });

        this.thresholdPanel = Ext.create('Ext.container.Container', {
            layout: 'fit',
            html: '',
            cls: 'threshold',
        });


        this.items.push(this.mainToolbar);
        this.items.push(this.thesholdPanel);
        this.items.push(this.selectPanel);
        this.items.push(this.thresholdPanel);

        this.lookupImageMeta(); //find values for the panels
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

    //query image service
    lookupImageMeta : function(image_uri) {

        var image_uri = this.viewer.imagesrc;
        Ext.Ajax.request({
            url: image_uri+'?meta',
            scope: this,
            disableCaching: false,
            timeout: 120000,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    BQ.ui.error(response.responseText);
                    //Ext.Msg.alert(response.responseText);
                else
                    this.updataGlobalPanel(response); //
            },
        });

    },

    lookupThreshold : function() {

        //parsing the request
        var param = {};
        var args = this.viewer.current_view.src_args;
        var request = [];
        var a=undefined;
        for (var i=0; (a=args[i]); i++) {
            if (a.indexOf('threshold=')<0 && a.indexOf('tile=')<0)
                request.push(a);
        }
        request.push('pixelcounter='+this.pixelCounter.thresholdValue);

        var image_uri = this.viewer.imagesrc +'?'+request.join('&');

        if (this.request_uri === image_uri) {
            this.updataGlobalPanel(me.response);
            return
        }
        this.request_uri = image_uri;

        //param['pixelcounter'] = this.threshold_value.value;
        me=this;
        Ext.Ajax.request({
            url: image_uri,
            scope: this,
            disableCaching: false,
            timeout: 120000,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    BQ.ui.error(response.responseText);
                    //Ext.Msg.alert(response.responseText);
                else
                    me.response = response;
                    me.updataGlobalPanel(response);
            },
        });

    },
    /*
    lookupThesholds : function(uri_list){
        
        for (var uri in uri_list) {

            Ext.Ajax.request({
                url: image_uri,
                scope: this,
                disableCaching: false,
                timeout: 120000,
                callback: function(opts, succsess, response) {
                    if (response.status>=400)
                        BQ.ui.error(response.responseText);
                        //Ext.Msg.alert(response.responseText);
                    else
                        me.response = response;
                        me.updataGlobalPanel(response);
                },
            });
            
        }
        
    }*/

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
        if (!xmlDoc.responseXML) { //require xml
            //error
            //alert('Request timeout');
            BQ.ui.error('XML Document not found');
            return;
        }
        this.queryById('px_selectinfo_panel').setVisible(false);
        this.queryById('px_threshold_panel').setVisible(true);

        var pixel_resolution_x = this.evaluateXPath(xmlDoc.responseXML, 'resource/tag[@name="pixel_resolution_x"]/@value');
        var pixel_resolution_y = this.evaluateXPath(xmlDoc.responseXML, 'resource/tag[@name="pixel_resolution_y"]/@value');
        var pixel_resolution_unit_x = this.evaluateXPath(xmlDoc.responseXML, 'resource/tag[@name="pixel_resolution_unit_x"]/@value');
        var pixel_resolution_unit_y = this.evaluateXPath(xmlDoc.responseXML, 'resource/tag[@name="pixel_resolution_unit_y"]/@value');

        if (pixel_resolution_x[0] && pixel_resolution_y[0] && pixel_resolution_unit_x[0] && pixel_resolution_unit_y[0]) {
            //updates the resolution measurements
            this.pixel_resolution_x = pixel_resolution_x[0].value;
            this.pixel_resolution_y = pixel_resolution_y[0].value;
            this.pixel_resolution_unit_x = pixel_resolution_unit_x[0].value;
            this.pixel_resolution_unit_y = pixel_resolution_unit_y[0].value;
        }

        var channels = this.evaluateXPath(xmlDoc.responseXML, 'resource/pixelcounts[@name="channel"]');
        var globalTitle = '<tr><th>channel</th><th >threshold</th><th>pixels</th>';

        if (this.pixel_resolution_x && this.pixel_resolution_y && this.pixel_resolution_unit_x && this.pixel_resolution_unit_y) {
            if (this.pixel_resolution_unit_x==this.pixel_resolution_unit_y) {
                var units = this.pixel_resolution_unit_x+'<sup>2</sup>';
            } else {
                var units = this.pixel_resolution_unit_x+' x '+this.pixel_resolution_unit_y;
            }
            globalTitle = globalTitle + '<th>'+units+'</th>';
        }
        globalTitle = globalTitle + '</tr>';
        var globalRows = '';
        if (channels.length==3) { //check if atleast one value
            for (var c = 0; c<channels.length; c++) { //updates panel values
                var above = self.evaluateXPath(channels[c],'tag[@name="above"]/@value')[0].value;
                var below = self.evaluateXPath(channels[c],'tag[@name="below"]/@value')[0].value;

                var globalRowAbove = '<td>'+(c+1).toString()+'</td><td>above</td><td >'+above.toString()+'</td>';
                var globalRowBelow = '<td>'+(c+1).toString()+'</td><td>below</td><td >'+below.toString()+'</td>';
                //if found resolution points add to panel
                if (this.pixel_resolution_x && this.pixel_resolution_y && this.pixel_resolution_unit_x && this.pixel_resolution_unit_y) {

                    var area_above = (parseFloat(above)*parseFloat(this.pixel_resolution_x)*parseFloat(this.pixel_resolution_y)).toFixed(2);
                    var area_below = (parseFloat(below)*parseFloat(this.pixel_resolution_x)*parseFloat(this.pixel_resolution_y)).toFixed(2);


                    globalRowAbove = globalRowAbove + '<td>'+area_above.toString()+'</td>';
                    globalRowBelow = globalRowBelow + '<td>'+area_below.toString()+'</td>';
                }
            globalRows = globalRows+'<tr>'+globalRowAbove+'</tr><tr>'+globalRowBelow+'</tr>';
            }
        }
        else {
            //error didnt not find image service pixel counter
            //BQ.ui.error('Didnt not find image service pixel counter information from image service');
        }
        var html = '<table>'+globalTitle+globalRows+"</table>";

        this.thresholdPanel.update(html);
    },

    updataRegionPanel : function(){
        this.queryById('px_selectinfo_panel').setVisible(true);
        this.queryById('px_threshold_panel').setVisible(false);

        var html = '';
        if (this.regionCount) { //canvas else set panel to zero

            var regionTitle = '<tr><th>pixels</th>';
            var scale = this.viewer.view().scale;

            if (this.pixel_resolution_x && this.pixel_resolution_y && this.pixel_resolution_unit_x && this.pixel_resolution_unit_y) {
                    if (this.pixel_resolution_unit_x==this.pixel_resolution_unit_y) {
                        var units = this.pixel_resolution_unit_x+'<sup>2</sup>';
                    } else {
                        var units = this.pixel_resolution_unit_x+' x '+this.pixel_resolution_unit_y;
                    }
                    regionTitle = regionTitle + '<th>'+units+'</th>';
                }

            regionTitle = regionTitle + '</tr>';

            var regionRows = '<tr>';
            var count = this.regionCount.count;//this.viewer.view().scale //find scale
            var scaled_count = (count/(scale*scale)).toFixed(0);
            var regionRows = regionRows + '<td >'+scaled_count.toString()+'</td>';
            if (this.pixel_resolution_x && this.pixel_resolution_y && this.pixel_resolution_unit_x && this.pixel_resolution_unit_y) {
                var area = (parseFloat(scaled_count)*parseFloat(this.pixel_resolution_x)*parseFloat(this.pixel_resolution_y)).toFixed(2);
                if (this.pixel_resolution_unit_x==this.pixel_resolution_unit_y) {
                    var units = this.pixel_resolution_unit_x+'<sup>2</sup>';
                } else {
                    var units = this.pixel_resolution_unit_x+' x '+this.pixel_resolution_unit_y;
                }
                var regionRows = regionRows+'<td>'+area.toString()+'</td>';
            }
            regionRows = regionRows+'</tr>';
            var html = '<table>'+regionTitle+regionRows+"</table>";
            //this.thresholdPanel.update(html)
        } else {
            //error no region evaluated
        }
        this.thresholdPanel.update(html);
    },


});

