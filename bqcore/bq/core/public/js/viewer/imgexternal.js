function ImgExternal (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    

    this.viewer.addMenu([{
        itemId: 'menu_viewer_external',
        xtype:'button',
        text: 'Export',
        iconCls: 'external',
        needsAuth: false,
        scope: this,
        tooltip: 'Export current image to external applications',
        menu: {
            defaults: {
                scope: this,
            },
            items: [{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_export_view',
                text   : 'Export current view',
                scale  : 1,
                border: true, //default
                showGobjects: true,
                handler: function() {
                    this.exportCurrentView(1);
                    },
                    /*
                menu   : {
                    hidden: true,
                    handler: function() {return false;},
                    items   : [
                    '<b class="menu-title">Choose a Scale</b>',
                    {
                        text: '100%',
                        handler: function() {this.exportCurrentView(1);},
                        scope: this,
                        checked: false,
                        hideOnClick : false,
                        group: 'scale',
                        tooltip: 'Download current view scaled at 100%',
                    }, {
                        text: '200%',
                        handler: function(){this.exportCurrentView(2);},
                        scope: this,
                        checked: true,
                        hideOnClick : false,
                        group: 'scale',
                        tooltip: 'Download current view scaled at 200%',
                    }, {
                        text: '400%',
                        handler: function(){this.exportCurrentView(4);},
                        scope: this,
                        checked: false,
                        hideOnClick : false,
                        group: 'scale',
                        tooltip: 'Download current view scaled at 400%',
                }]},
                */
            },{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_external_bioView',
                text   : 'View in bioView',
                handler: this.launchBioView,
            }, {
                xtype  : 'menuitem',
                itemId : 'menu_viewer_external_bioView3D',
                text   : 'View in bioView3D',
                handler: this.launchBioView3D,
            }, {
                xtype  : 'menuitem',
                itemId : 'menu_viewer_export_gobs_gdocs',
                text   : 'Export GObjects to Google Docs',
                handler: this.exportGObjectsToGoogle,
            },{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_export_tags_gdocs',
                text   : 'Export Tags to Google Docs',
                handler: this.exportTagsToGoogle,
            }]
        },
    }]);

    this.viewer.addMenu([{
        itemId: 'menu_viewer_operations',
        xtype:'button',
        text: 'Operations',
        iconCls: 'converter',
        needsAuth: false,
        scope: this,
        //tooltip: 'Export current image to external applications',
        menu: {
            defaults: {
                scope: this,
            },
            items: [{
                itemId: 'menu_viewer_converter',
                text: 'Convert',
                iconCls: 'converter',
                tooltip: 'Convert and download the current image',
                scope: this,
                handler: this.convert,
            }, /*{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_pixel_counting',
                text   : 'Pixel counter',
                //disabled: true,
                handler: this.pixelCounter,
            },*/ {
                xtype  : 'menuitem',
                itemId : 'menu_viewer_calibrate_resolution',
                text   : 'Calibrate image resolution',
                disabled: true,
                handler: this.calibrateResolution,
            }/*, {
                xtype  : 'menuitem',
                itemId : 'menu_viewer_precache',
                text   : 'Pre-cache current view',
                disabled: true,
                handler: this.calibrateResolution,
            }*/]
        },
    }]);
};

ImgExternal.prototype = new ViewerPlugin();

ImgExternal.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
};

ImgExternal.prototype.newImage = function () {
    if (this.viewer.toolbar) {
        var m = this.viewer.toolbar.queryById('menu_viewer_external_bioView3D');
        if (m) m.setDisabled(this.viewer.imagedim.z<2);
    }
};

ImgExternal.prototype.updateImage = function () {
};

ImgExternal.prototype.launchBioView = function () {
    var url = 'bioview://resource/?url='+this.viewer.image.uri;
    if (this.viewer.user) {
        var user = this.viewer.user.credentials.user;
        var pass = this.viewer.user.credentials.pass;
        url += '&user='+user+'&pass='+pass;
    }
    //window.location = url;
    window.open( url );
};

ImgExternal.prototype.launchBioView3D = function () {
    if (this.viewer.imagedim.z * this.viewer.imagedim.t <= 1) {
        BQ.ui.notification ("Image is not a 3D stack (multiplane image)");
        return;
    }
    var url = 'bioview3d://resource/?url='+this.viewer.image.uri;
    if (this.viewer.user) {
        var user = this.viewer.user.credentials.user;
        var pass = this.viewer.user.credentials.pass;
        url += '&user='+user+'&pass='+pass;
    }
    //window.location = url;
    window.open( url );
};

ImgExternal.prototype.exportGObjectsToGoogle = function () {
    window.open( '/export/to_gdocs?url=' + this.viewer.image.uri + "/gobject" );
};

ImgExternal.prototype.exportTagsToGoogle = function () {
    window.open( '/export/to_gdocs?url=' + this.viewer.image.uri + "/tag" );
};

/*
 * Downloads a scaled view of the view currently being presented in the
 * viewer.
 */
ImgExternal.prototype.exportCurrentView = function (scale) {

    var control_surface_size = this.viewer.viewer_controls_surface.getBoundingClientRect();
    
    //create canvas
    var canvas_view = document.createElement('canvas');
    canvas_view.height = control_surface_size.height;
    canvas_view.width = control_surface_size.width;
    ctx_view = canvas_view.getContext("2d");
    ctx_view.fillStyle = 'rgba(67, 67, 67, 1)'//"#FF0000";
    ctx_view.fillRect(0,0,control_surface_size.width,control_surface_size.height); 
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
    
    //draw image blogs with offsets on to the canvas
    ctx_view.createImageData(canvas_view.height, canvas_view.width);
    imageData = ctx_view.getImageData(0, 0, canvas_view.width, canvas_view.height);

    ctx_view.putImageData(imageData, 0, 0);

    for (var i=0; i<inViewImages.length; i++){
        var yoffset = parseInt(inViewImages[i].style.top);
        var xoffset = parseInt(inViewImages[i].style.left);
        var scaled_imgwidth = inViewImages[i].width;
        var scaled_imgheight = inViewImages[i].height;
        //var scale = this.viewer.view().scale;
        if (location.origin+this.viewer.plugins_by_name['tiles'].tiled_viewer.loadingTile==inViewImages[i].src) { // a tile is not completely loaded
            return false
        }
        ctx_view.drawImage(inViewImages[i], xoffset, yoffset, scaled_imgwidth, scaled_imgheight);
    }
    
    showGobjects = true; 
    if (showGobjects) {
        //render svg to canvas
        var renderer = this.viewer.plugins_by_name['renderer'];
        var svgimg = new Image();
        var serializer = new XMLSerializer();
        var svg_data = renderer.svgdoc.cloneNode(true);
        //remove offsets
        var xoffset = svg_data.style.left;
        var yoffset = svg_data.style.top;
        svg_data.setAttribute('style','position: abosulte; top: 0px; left: 0px; width: '+svg_data.style.width+'; height: '+svg_data.style.height);
        
        //svg_data.setAttribute('width',tiled_viewer.width);
        //svg_data.setAttribute('height',tiled_viewer.height);
        svgStr = serializer.serializeToString(svg_data);
        svgimg.src = 'data:image/svg+xml;base64,' + window.btoa(svgStr);
        ctx_view.drawImage(svgimg, parseInt(xoffset), parseInt(yoffset), parseInt(svg_data.style.width), parseInt(svg_data.style.height));
        //ctx_view.drawImage(svgimg, xoffset, yoffset, tiled_viewer.width, tiled_viewer.height);
    }
    
    border = false;
    if (!border) {
        //removes border from the image
        var renderer = this.viewer.plugins_by_name['renderer'];
        var canvas_border = document.createElement('canvas');
        var width = parseInt(renderer.overlay.style.width, 10);
        var height = parseInt(renderer.overlay.style.height, 10);
        
        
        if (parseInt(renderer.overlay.style.left, 10)>0)
            var xoffset = -parseInt(renderer.overlay.style.left, 10);
        else {
            var xoffset = 0;
            width = width + parseInt(renderer.overlay.style.left, 10);
        }
        if (parseInt(renderer.overlay.style.top, 10)>0)
            var yoffset = -parseInt(renderer.overlay.style.top, 10);
        else {
            var yoffset = 0;//arseInt(renderer.overlay.style.top, 10)
            height = height + parseInt(renderer.overlay.style.top, 10);
        }
        
        if ((parseInt(renderer.overlay.style.top, 10) + parseInt(renderer.overlay.style.height, 10)) > tiled_viewer.height) {
            height = height - (parseInt(renderer.overlay.style.top, 10) + parseInt(renderer.overlay.style.height, 10) - tiled_viewer.height);
        }
        
        if ((parseInt(renderer.overlay.style.left, 10) + parseInt(renderer.overlay.style.width, 10)) > tiled_viewer.width) {
            width = width - (parseInt(renderer.overlay.style.left, 10) + parseInt(renderer.overlay.style.width, 10) - tiled_viewer.width);
        }
        
        canvas_border.width = width;
        canvas_border.height = height;
        var ctx_border = canvas_border.getContext('2d');
        ctx_border.drawImage(canvas_view, xoffset, yoffset, tiled_viewer.width, tiled_viewer.height);
        canvas_view = canvas_border;
        delete canvas_border
    }
    
    //scale the canvas
    if (scale!=1) {
        var canvas_scaled = document.createElement('canvas');
        canvas_scaled.width = canvas_view.width*scale;
        canvas_scaled.height = canvas_view.height*scale;
        var ctx_scaled = canvas_scaled.getContext('2d');
        ctx_scaled.drawImage(canvas_view, 0, 0, canvas_view.width*scale, canvas_view.height*scale);
        canvas_view = canvas_scaled
        delete canvas_scaled
    }
    //request canvas
    var url = canvas_view.toDataURL("image/jpeg");
    window.open(url)
    
    //remove canvas
    delete canvas_view

};


ImgExternal.prototype.convert = function () {
    var image = this.viewer.image;
    var phys = this.viewer.imagephys;
    var title = 'Image converter [W:'+phys.x+', H:'+phys.y+', Z:'+phys.z+', T:'+phys.t+' Ch:'+phys.ch+'/'+phys.pixel_depth+'bits'+'] ' + image.name;
    Ext.create('Ext.window.Window', {
        modal: true,
        width: BQApp?BQApp.getCenterComponent().getWidth()/1.6:document.width/1.6,
        height: BQApp?BQApp.getCenterComponent().getHeight()/1.1:document.height/1.1,
        layout: 'fit',
        border: false,
        maxWidth: 600,
        title: title,
        items: [{
            xtype  : 'bqimageconverter',
            image  : this.viewer.image,
            phys   : this.viewer.imagephys,
            slice  : this.viewer.findPlugin('slicer').getParams(),
            view   : this.viewer.findPlugin('ops').getParams(),
        }],
    }).show();
};

ImgExternal.prototype.calibrateResolution = function () {

};

