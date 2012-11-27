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
}
ImgExternal.prototype = new ViewerPlugin();

ImgExternal.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
}

ImgExternal.prototype.newImage = function () {
    if (this.viewer.toolbar) {
        //var num_pages = this.viewer.imagedim.z * this.viewer.imagedim.t;
        var m = this.viewer.toolbar.queryById('menu_viewer_external_bioView3D');
        if (m) m.setDisabled(this.viewer.imagedim.z<2);
    }
}

ImgExternal.prototype.updateImage = function () {
}

ImgExternal.prototype.launchBioView = function () {
    var user = this.viewer.user.credentials.user;
    var pass = this.viewer.user.credentials.pass;  
    var new_url = 'bioview://resource/?user='+user+'&pass='+pass+'&url='+this.viewer.imageuri;  
    //window.location = new_url;
    window.open( new_url );      
}

ImgExternal.prototype.launchBioView3D = function () {
    if (this.viewer.imagedim.z * this.viewer.imagedim.t <= 1) {
        alert ("Image is not a 3D stack (multiplane image)");
        return;
    }
    var user = this.viewer.user.credentials.user;
    var pass = this.viewer.user.credentials.pass;  
    var new_url = 'bioview3d://resource/?user='+user+'&pass='+pass+'&url='+this.viewer.imageuri;  
    //window.location = new_url;
    window.open( new_url );      
}

ImgExternal.prototype.exportGObjectsToGoogle = function () {
    //window.location = '/export/to_gdocs?url=' + this.viewer.imageuri + "/gobject";
    window.open( '/export/to_gdocs?url=' + this.viewer.imageuri + "/gobject" );      
}

ImgExternal.prototype.exportTagsToGoogle = function () {
    //window.location = '/export/to_gdocs?url=' + this.viewer.imageuri + "/tag";  
    window.open( '/export/to_gdocs?url=' + this.viewer.imageuri + "/tag" );        
}

ImgExternal.prototype.exportCurrentView = function () {
    var args = this.viewer.updateView().src_args;
    args.push('format=jpeg,stream');
    args = args.join('&').replace('&tile=0,0,0,256', '');
    var url = '/image_service/images/'+this.viewer.image.resource_uniq+'?'+args;    
    window.location = url;  
}


