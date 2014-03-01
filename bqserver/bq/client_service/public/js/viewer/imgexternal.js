function ImgExternal (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);

    this.viewer.addMenu([{
        itemId: 'menu_viewer_external',
        xtype:'button',
        text: 'Export',
        iconCls: 'external',
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
                handler: this.exportCurrentView,
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
            }, {
                xtype  : 'menuitem',
                itemId : 'menu_viewer_pixel_counting',
                text   : 'Pixel counter',
                disabled: true,
                handler: this.pixelCounter,
            },{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_calibrate_resolution',
                text   : 'Calibrate image resolution',
                disabled: true,
                handler: this.calibrateResolution,
            }]
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

ImgExternal.prototype.exportCurrentView = function () {
    var args = this.viewer.updateView().src_args;
    var tile_index=undefined;
    for (var i=0; i<args.length; i++) {
        if (args[i].indexOf('tile=')>=0) {
            tile_index = i;
            break;
        }
    }
    if (tile_index)
        args.splice(tile_index, 1);
    args.push('format=jpeg,stream');
    args = args.join('&');
    var url = '/image_service/images/'+this.viewer.image.resource_uniq+'?'+args;
    window.location = url;
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

ImgExternal.prototype.pixelCounter = function () {

};

