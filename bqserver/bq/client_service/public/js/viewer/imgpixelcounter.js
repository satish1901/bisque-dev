//modification to imageview
function ImgPixelCounter(viewer,name) {
    var p = viewer.parameters || {};
        
    this.default_threshold        = p.threshold || 0;
    this.default_autoupdate       = false;
        
    this.base = ViewerPlugin;
    this.base (viewer, name);
}


ImgPixelCounter.prototype = new ViewerPlugin();

ImgPixelCounter.prototype.create = function (parent) {
    
    this.parent = parent;
    return parent;
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
        this.canvas_mask.style.visibility='hidden'
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
    if (!this.loading_canvas ) {
        this.loading_canvas = document.createElement('canvas');
        this.loading_canvas.setAttributeNS(null, 'class', 'pixel_counter_loading_canvas');
        this.loading_canvas.setAttributeNS(null, 'id', 'pixel_counter_loading_image');
        this.loading_canvas.height = control_surface_size.height;
        this.loading_canvas.width = control_surface_size.width;
        this.loading_canvas.style.zIndex = 310;
        this.loading_canvas.style.top = "0px";
        this.loading_canvas.style.left = "0px";
        this.loading_canvas.style.position = "absolute";
        this.loading_canvas.style.visibility='hidden';
        this.ctx_load = this.loading_canvas.getContext("2d");
        //this.image = new Image();
        //this.image.addEventListener('load',this.updateCanvas.bind(this),false) //resets canvas onload
        this.parent.appendChild(this.loading_canvas);
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
    
    //must wait till all tiles are loaded
    
    
    // load image from data url
    this.constructCanvasFromWell();

    //this.ctx_img.drawImage(this.image, 0, 0);
    this.imageData = this.ctx_img.getImageData(0, 0, this.canvas_image.width, this.canvas_image.height);
    this.imagesrc = this.imageData.data;
    
    this.ctx_imgmask.createImageData(this.canvas_mask.height,this.canvas_mask.width);
    this.maskData = this.ctx_imgmask.getImageData(0, 0, this.canvas_mask.width, this.canvas_mask.height);
    this.masksrc = this.maskData.data;
    
    this.current_scale = tiled_viewer.currentScale //scale the pixels based on the size of the image being displayed
    
};

//looks through all the images in the well 
ImgPixelCounter.prototype.constructCanvasFromWell = function() {
    var control_surface_size = this.viewer.viewer_controls_surface.getBoundingClientRect();
    var tiled_viewer = this.viewer.plugins_by_name['tiles'].tiled_viewer; //finding tiled viewer in the plugin list
    
    //iterorate through all the tiles to find the tiles in the viewer
    var inViewImages = [];
    var tile_tops = [];
    var tile_bottoms = [];
    var tile_lefts = [];
    var tile_rights = [];
    
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
    this.loading_canvas.width = control_surface_size.width;
    this.loading_canvas.height = control_surface_size.height;
    
    //draw width offsets on to the canvas
    this.ctx_img.createImageData(this.canvas_mask.height,this.canvas_mask.width);

    this.imageData = this.ctx_img.getImageData(0, 0, this.canvas_image.width, this.canvas_image.height);
    this.imagesrc = this.imageData.data;
    
    this.ctx_load.createImageData(this.loading_canvas.height,this.loading_canvas.width);
    this.loadData = this.ctx_load.getImageData(0, 0, this.loading_canvas.width, this.loading_canvas.height);
    this.loadsrc = this.loadData.data;
        
    this.resetimage();
    this.resetloadingcanvas()
    this.ctx_img.putImageData(this.imageData,0,0);  
    this.ctx_load.putImageData(this.loadData,0,0);
    
    for (var i = 0; i<inViewImages.length ; i++){
        var yoffset = parseInt(inViewImages[i].style.top);
        var xoffset = parseInt(inViewImages[i].style.left);
        var scaled_imgwidth = inViewImages[i].width;
        var scaled_imgheight = inViewImages[i].height;
        //var scale = this.viewer.view().scale;
        this.ctx_img.drawImage(inViewImages[i], xoffset, yoffset,scaled_imgwidth,scaled_imgheight);
    }    
}

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
}

ImgPixelCounter.prototype.resetloadingcanvas = function() {
        for (var i = 0; i<(this.loading_canvas.width*this.loading_canvas.height*4); i+=4) {
            this.loadsrc[i]     = 255; //r
            this.loadsrc[i+1]   = 255; //g
            this.loadsrc[i+2]   = 255; //b
            this.loadsrc[i+3]   = 128;//a
        }    
}


ImgPixelCounter.prototype.newImage = function () {
    this.phys_inited = false;
};


ImgPixelCounter.prototype.updateImage = function () {
    if (this.viewer.parameters.main.queryById('main_container').queryById('pixelcounter-panel')) {
        var pixelCounterPanel=this.viewer.parameters.main.queryById('main_container').queryById('pixelcounter-panel');
        pixelCounterPanel.lookupThreshold()
    }
    //attach canvus to the viewer
    //this.currentView()
};


ImgPixelCounter.prototype.getParams = function () {
    return this.params || {};
};

//check if threshold mode is on to redraw image 
//or if selection mode is on the redraw canvas and push it to the front
ImgPixelCounter.prototype.updateView = function (view) {
    
    //check if pixel counter panel is there
    
    if (this.viewer.parameters.main.queryById('main_container').queryById('pixelcounter-panel')) {
        var pixelCounterPanel=this.viewer.parameters.main.queryById('main_container').queryById('pixelcounter-panel');
        pixelCounterPanel.lookupThreshold()
        if (pixelCounterPanel.thresholdMode) {
            this.params = {};
            view.addParams('threshold='+this.thresholdValue+',both');
            if (pixelCounterPanel.selectMode) {
                //should disable the scroll in selection mode
                this.initCanvas() //checks to see if canvas exists
                this.updateCanvas(); //if canvas isnt initalized, will initalize canvas
                this.canvas_mask.style.visibility='visible'; //
                this.canvas_image.style.visibility='visible';
                
            } else {
                if (this.canvas_mask) {
                    this.canvas_mask.style.visibility='hidden';
                    this.canvas_image.style.visibility='hidden';
                    if(pixelCounterPanel.regionCount){
                        delete pixelCounterPanel.regionCount;
                    }                
                }
            }
        } else {
            
            this.params = {};
            view.addParams();
            if (this.canvas_mask) {
                this.canvas_mask.style.visibility='hidden';
                this.canvas_image.style.visibility='hidden';
                if(pixelCounterPanel.regionCount){
                    delete pixelCounterPanel.regionCount;
                }
            }
        }
    }    
};



ImgPixelCounter.prototype.onClick = function(e) {
    
    //find the offsets to canvas
    //set loading when clicked
    //this.loading_canvas.style.visibility='visible';
    //this.viewer.start_wait({op: 'gobjects', message: 'Fetching gobjects'})
    
    xClick = e.x-parseInt(this.canvas_mask.style.left)-this.viewer.plugins_by_name['tiles'].tiled_viewer.left;
    yClick = e.y-parseInt(this.canvas_mask.style.top)-this.viewer.plugins_by_name['tiles'].tiled_viewer.top;
    if(!(this.image_view_top<e.y&&this.image_view_bottom>e.y)||!(this.image_view_left<e.x&&this.image_view_right>e.x)) {//if click is outside the image break
       return
    }
    this.connectedComponents(xClick,yClick);
    //this.loading_canvas.style.visibility='hidden';
    //this.viewer.end_wait({op: 'gobjects', message: 'Fetching gobjects'})//disable loading when finished finding the region
    //this.canvas_mask.style.visibility='visible';
    //this.canvas_image.style.visibility='visible'; 
};


/*************************************
 * 
 *      Connected components
 * 
 *************************************/
ImgPixelCounter.prototype.index2xy = function(index) {
    
    //TODO: check for values outside the matrix
    index = parseInt(index);
    var x = parseInt(parseInt(index)/4)%this.canvas_image.width;
    var y = parseInt(parseInt(parseInt(index)/4)/this.canvas_image.width)%this.canvas_image.height;
    return {x:x,y:y}
    
}

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
    var pixelCounterPanel = this.viewer.parameters.main.queryById('main_container').queryById('pixelcounter-panel');
    pixelCounterPanel.regionCount = count;
    pixelCounterPanel.updataRegionPanel();
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
    var control_surface_size =  this.viewer.viewer_controls_surface.getBoundingClientRect()
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

ImgPixelCounter.prototype.doUpdate = function () {
    this.viewer.need_update();
};
 
ImgPixelCounter.prototype.changed = function () {
  if (!this.update_check || (this.update_check && this.update_check.checked) ) 
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
    collapsible : true,
    split : true,
    width : 400,
    plain : true,
    //closable: true,
    thresholdMode: false,
    selectMode : false,
    
    initComponent : function() {
        
        this.items = [];
        me=this;
        
        this.pixelCounter = this.viewer.plugins_by_name['pixelcounter'];
        
        this.selectModeToggle = Ext.create('Ext.Button',{
            xtype: 'button',
            itemId : 'select_region_toggle_button',
            width: 100,
            height: 25,
            text: 'Enable Select', 
            tooltip: '<h2>Select Mode</h2><p>Enable this mode and click on any part of the image. The connected<br> region will be highlighted the pixel count will be displayed below.</p>',
            //disabled: true,
            flag: 0, //tell the listener if pixel selection is on or off 
        });
        

        
        this.thresholdCheckBox = Ext.create('Ext.form.Panel',{
            //xtype: 'button',
            //boxLabel: 'View Threshold',
            //checked: false,
            //width: 115,
            //height: 25,
            //text: 'Enable Threshold',
            
            itemId : 'threshold_checkbox',
            frame: false,
            border: false,
            margin: "10 0 0 10",  // (top, right, bottom, left)
            items: [
                {
                    xtype: 'fieldcontainer',
                    //fieldLabel: 'Toppings',
                    defaultType: 'checkboxfield',
                    items: [
                        {
                            boxLabel  : 'View Threshold',
                            //padding   : 10,
                            name      : 'topping',
                            inputValue: '1',
                            id        : 'threshold_checkbox',
                            checked   : false,
                        }
                    ]
                }
            ]
        });
        
        
        this.closePanel = Ext.create('Ext.Button',{
            xtype: 'button',
            width: 60,
            height: 25,
            text: 'Close',
            itemId : 'pixelcounter_close_button',
            listeners: {
                click: function() {
                    me.close(); //closes panel
                }
            },
        });        

 
        this.thresholdSlider = Ext.create('Ext.slider.Single',{
            //width: 240,
            width: '85%',
            fieldLabel: 'Threshold Value',
            value: 128,
            increment: 1,
            margin: "0 0 5 10",  // (top, right, bottom, left)  
            minValue: 0, //needs to adjust with the image
            maxValue: 256,    //needs to adjust with the image
            hysteresis: 100,  // delay before firing change event to the listener
            
        });   

        //addlistneres
        this.thresholdCheckBox.queryById("threshold_checkbox").on({
            change: function(e,newValue,oldValue) {
                if (me.thresholdMode==true) {
                    //turns off threshold mode and select mode
                    me.thresholdMode = false; //reset flag  
                    me.selectMode = false; //reset flag
                    //me.selectModeToggle.setDisabled(true);
                    me.pixelCounter.changed();
                    me.selectModeToggle.setText('Enable Select');
                    
                } else {
                    //turns on threshold mode
                    me.thresholdMode = true; //reset flag
                    //me.selectModeToggle.setDisabled(false);
                    me.pixelCounter.changed();
                } 
            }
        })

        this.selectModeToggle.on({
            click : function() {
           
               if (me.selectMode == true) {
                    //turns off select mode
                    me.selectMode = false; //reset flag
                    me.pixelCounter.changed();
                    me.selectModeToggle.setText('Enable Select');

                } else {
                    //turns on select mode
                    me.selectMode = true; //reset flag
                    me.pixelCounter.changed(); //change will be set by the checkbox also
                    me.thresholdCheckBox.queryById("threshold_checkbox").setValue(true);
                    me.selectModeToggle.setText('Disable Select');
                    
                }
            },
            scope: this,           
        })
        
        this.thresholdSlider.on({
            afterrender: function() { //populate panel
                                me.pixelCounter.thresholdValue = me.thresholdSlider.value;
                                me.lookupThreshold();
                            },
            change : function(self,event,thumb){
                //set a delay to refresh the values on the panel
                if (me.thresholdSlider.event_timeout) clearTimeout (me.thresholdSlider.event_timeout);
                //var me = this;
                
                me.thresholdSlider.event_timeout = setTimeout(function(){
                    //this.me.threshold_value.setValue(thumb.value.toString());
                    me.pixelCounter.thresholdValue = thumb.value.toString(); //set pixel counter value
                    me.lookupThreshold();
                    me.selectMode = false; //reset flag
                    me.pixelCounter.changed();
                    me.selectModeToggle.setText('Enable Select');
                    //me.updataRegionPanel()
                },  me.thresholdSlider.hysteresis );
            },
            scope: this,
        })
        
        
        this.on({
            beforecollapse: function(p,direction,animate){
                
                if(me.selectMode){ //disables select mode
                    me.selectMode = false; //reset flag                  
                    me.pixelCounter.changed();
                    me.selectModeToggle.setText('Enable Select');                    
                }                
            },
            resize: function(){
                if(me.selectMode){ //disables select mode
                    me.selectMode = false; //reset flag                  
                    me.pixelCounter.changed();
                    me.selectModeToggle.setText('Enable Select');                  
                }       
            }
        })

        this.mainToolbar = Ext.create('Ext.toolbar.Toolbar', {
            //width : 400,
            width: '100%',
            //layout: 'fit',
            items: [{
                    xtype: 'buttongroup',
                    items: [this.thresholdModeToggle ,this.selectModeToggle]
                } ,{
                    xtype: 'buttongroup',
                    items: [{
                        height: 25,
                        xtype: 'button',
                        text: 'Export',     
                        disabled: true,                   
                    }]
                }, '->',{
                    xtype: 'buttongroup',
                    items:[this.closePanel],
                }]
        });
        
        this.thresholdPanel = Ext.create('Ext.container.Container', {
            layout: 'fit',
            html: '',
            margin: "30 0 0 10",  // (top, right, bottom, left)  
        });
               
        this.items.push(this.mainToolbar);
        this.items.push(this.thresholdCheckBox);
        this.items.push(this.thresholdSlider);
        this.items.push(this.thresholdPanel);
        
        this.lookupImageMeta() //find values for the panels
        
        return this.callParent(arguments); 
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
                    Ext.Msg.alert(response.responseText);
                else
                    this.updataGlobalPanel(response); //
            },
        });    
            
    },

    lookupThreshold : function() {

        //parsing the request
        var param = {};
        var image_uri = this.viewer.imagesrc;
        for (var i = 0; i<this.viewer.current_view.src_args.length;i++) {
    
            key = this.viewer.current_view.src_args[i].split('=')[0]
            value = this.viewer.current_view.src_args[i].split('=')[1]
            if (key!='threshold') { //dont want to include the threshold in the pixel count in the future the threshold will be an overlay
                //param[key]=value;
                
                if (i==0) image_uri+='?'+key+'='+escape(value)
                else image_uri+='&'+key+'='+escape(value)   
            }
        }
        
        if (i==0) image_uri+='?pixelcounter='+this.pixelCounter.thresholdValue
        else image_uri+='&pixelcounter='+this.pixelCounter.thresholdValue
        //param['pixelcounter'] = this.threshold_value.value;
        me=this;
        Ext.Ajax.request({
            url: image_uri,
            scope: this,
            disableCaching: false,            
            timeout: 120000,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    Ext.Msg.alert(response.responseText);
                else
                    me.updataGlobalPanel(response);
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
    
    updataGlobalPanel : function(xmlDoc) {
        if (!xmlDoc.responseXML) { //require xml
            //error
            //alert('Request timeout');
            return;
        }
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
        var globalPanel = "<h2>Global Count</h2>";
        var globalRows = '<tr><td style="padding:0 15px 0 15px;">Channel</td><td style="padding:0 15px 0 15px;">Position</td><td style="padding:0 15px 0 15px;">Amount</td><td style="padding:0 15px 0 15px;">Units</td></tr>';
        if (channels.length==3) { //check if atleast one value
            for (var c = 0; c<channels.length; c++) { //updates panel values
                var above = self.evaluateXPath(channels[c],'tag[@name="above"]/@value')[0].value;
                var below = self.evaluateXPath(channels[c],'tag[@name="below"]/@value')[0].value;
                globalRows = globalRows + '<tr><td ALIGN=Right style="padding:0 15px 0 15px;">'+(c+1).toString()+'</td><td style="padding:0 15px 0 15px;">above</td><td ALIGN=Right style="padding:0 15px 0 15px;">'+above.toString()+'</td><td style="padding:0 15px 0 15px;">px</td></tr>';
                globalRows = globalRows + '<tr><td ALIGN=Right style="padding:0 15px 0 15px;">'+(c+1).toString()+'</td><td style="padding:0 15px 0 15px;">below</td><td ALIGN=Right style="padding:0 15px 0 15px;">'+below.toString()+'</td><td style="padding:0 15px 0 15px;">px</td></tr>';
                //if found resolution points add to panel
                if (this.pixel_resolution_x && this.pixel_resolution_y && this.pixel_resolution_unit_x && this.pixel_resolution_unit_y) {
                    
                    var area_above = (parseFloat(above)*parseFloat(this.pixel_resolution_x)*parseFloat(this.pixel_resolution_y)).toFixed(2);
                    var area_below = (parseFloat(below)*parseFloat(this.pixel_resolution_x)*parseFloat(this.pixel_resolution_y)).toFixed(2);
                    if (this.pixel_resolution_unit_x==this.pixel_resolution_unit_y) {
                        var units = this.pixel_resolution_unit_x+'<sup>2</sup>';
                    } else {
                        var units = this.pixel_resolution_unit_x+' x '+this.pixel_resolution_unit_y;
                    }
                    
                    globalRows = globalRows + '<tr><td ALIGN=Right style="padding:0 15px 0 15px;">'+(c+1).toString()+'</td><td style="padding:0 15px 0 15px;">above</td><td ALIGN=Right style="padding:0 15px 0 15px;">'+area_above.toString()+'</td><td style="padding:0 15px 0 15px;">'+units+'</td></tr>';
                    globalRows = globalRows + '<tr><td ALIGN=Right style="padding:0 15px 0 15px;">'+(c+1).toString()+'</td><td style="padding:0 15px 0 15px;">below</td><td ALIGN=Right style="padding:0 15px 0 15px;">'+area_below.toString()+'</td><td style="padding:0 15px 0 15px;">'+units+'</td></tr>';
                }
            }
        }
        else {
            //error didnt not find image service pixel counter
        }
        var html = globalPanel+'<BLOCKQUOTE><table>'+globalRows+"</table></BLOCKQUOTE>";
        
        this.thresholdPanel.update(html)  
    },
    
    updataRegionPanel : function(){
        var regionPanel = "<h2>Region Count</h2>";
        var regionRows = '<tr><td style="padding:0 15px 0 15px;">Amount</td><td style="padding:0 15px 0 15px;">Units</td></tr>';
        var scale = this.viewer.view().scale;
        if (this.regionCount) { //canvas else set panel to zero
            var count = this.regionCount//this.viewer.view().scale //find scale
            var scaled_count = count/(scale*scale);
            var regionRows = regionRows + '<tr><td ALIGN=Right style="padding:0 15px 0 15px;">'+scaled_count.toString()+'</td><td style="padding:0 15px 0 15px;">px</td></tr>';
            if (this.pixel_resolution_x && this.pixel_resolution_y && this.pixel_resolution_unit_x && this.pixel_resolution_unit_y) {
                var area = (parseFloat(scaled_count)*parseFloat(this.pixel_resolution_x)*parseFloat(this.pixel_resolution_y)).toFixed(2);
                if (this.pixel_resolution_unit_x==this.pixel_resolution_unit_y) {
                    var units = this.pixel_resolution_unit_x+'<sup>2</sup>';
                } else {
                    var units = this.pixel_resolution_unit_x+' x '+this.pixel_resolution_unit_y;
                }
                var regionRows = regionRows+'<tr><td ALIGN=Right style="padding:0 15px 0 15px;">'+area.toString()+'</td><td style="padding:0 15px 0 15px;">'+units+'</td></tr>';
            }
            var html = regionPanel + '<BLOCKQUOTE><table>'+regionRows+'</table></BLOCKQUOTE>';
            this.thresholdPanel.update(html)
        } else {
            //error no region evaluated
        }

    },

})

