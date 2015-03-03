function ImgExternal (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    
	this.imgCurrentView = new ImgCurrentView(viewer)

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
						var level = this.imgCurrentView.getCurrentLevel();
						this.imgCurrentView.setLevel(level);
						
						function callback(canvas_view) {
							var url = canvas_view.toDataURL("image/png");
							window.open(url);
						}
						
						var canvas_view = this.imgCurrentView.returnCurrentView(callback);

                    },
                
                menu   : {
                    //hidden: true,
                    handler: function() {return false;},
                    items   : [
                    //'<b class="menu-title">Choose a Scale</b>',
					{
						//hidden: true,
                        text: '100%',
						itemId : 'menu_viewer_export_view_button_100',
                        handler: function() {
							var level = this.imgCurrentView.getCurrentLevel();
							this.imgCurrentView.setLevel(level);
							
							function callback(canvas_view) {
								var url = canvas_view.toDataURL("image/png");
								window.open(url);
							}
							
							var canvas_view = this.imgCurrentView.returnCurrentView(callback);
						},
                        scope: this,
                        //checked: false,
                        //hideOnClick : false,
                        group: 'scale',
                        tooltip: 'Download current view scaled at 100%',
                    }, {
						//hidden: true,
                        text: '200%',
						itemId : 'menu_viewer_export_view_button_200',
                        handler: function(){
							var level = this.imgCurrentView.getCurrentLevel();
							this.imgCurrentView.setLevel(level - 1);
							
							function callback(canvas_view) {
								var url = canvas_view.toDataURL("image/png");
								window.open(url);
							}
							
							var canvas_view = this.imgCurrentView.returnCurrentView(callback);
						},
                        scope: this,
                        //checked: true,
                        //hideOnClick : false,
                        group: 'scale',
                        tooltip: 'Download current view scaled at 200%',
                    }, {
						//hidden: true,
                        text: '400%',
						itemId : 'menu_viewer_export_view_button_400',
                        handler: function(){
							var level = this.imgCurrentView.getCurrentLevel();
							this.imgCurrentView.setLevel(level - 2);
							
							function callback(canvas_view) {
								var url = canvas_view.toDataURL("image/png");
								window.open(url);
							}
							
							var canvas_view = this.imgCurrentView.returnCurrentView(callback);
						},
                        scope: this,
                        //checked: false,
                        //hideOnClick : false,
                        group: 'scale',
                        tooltip: 'Download current view scaled at 400%',
                }]},
				
                
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
            }, /*{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_export_gobs_gdocs',
                text   : 'Export GObjects to Google Docs',
                handler: this.exportGObjectsToGoogle,
            },{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_export_tags_gdocs',
                text   : 'Export Tags to Google Docs',
                handler: this.exportTagsToGoogle,
            }*/]
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
            }, {
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

    // Add download graphical annotations as KML
    var phys = this.viewer.imagephys,
        download = BQApp.getToolbar().queryById('button_download'),
        url = this.viewer.image.uri,
        url_kml = url.replace('/data_service/', '/export/') + '?format=kml',
        url_geojson = url.replace('/data_service/', '/export/') + '?format=geojson';
    if (phys.geo && download && phys.geo.proj4 && phys.geo.res && phys.geo.top_left) {
        download.menu.add(['-', {
            itemId: 'download_annotations_as_kml',
            text: 'Graphical annotations as KML',
            handler: function() {
                window.open(url_kml);
            },
        }, {
            itemId: 'download_annotations_as_geojson',
            text: 'Graphical annotations as GeoJson',
            handler: function() {
                window.open(url_geojson);
            },
        }]);
    };

};


ImgExternal.prototype.updateImage = function () {

	//set the options for the export at different scales
	if (this.imgCurrentView) {
		var level = this.imgCurrentView.getCurrentLevel(); //level can not drop below 0
		var m200 = this.viewer.toolbar.queryById('menu_viewer_export_view_button_200');
		var m400 = this.viewer.toolbar.queryById('menu_viewer_export_view_button_400');
		if (level) {
			if (level<1) m200.setDisabled(true);
			else m200.setDisabled(false);

			if (level<2) m400.setDisabled(true);
			else m400.setDisabled(false);
		} else {
			m200.setDisabled(true);
			m400.setDisabled(true);
		}
	}
	
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

