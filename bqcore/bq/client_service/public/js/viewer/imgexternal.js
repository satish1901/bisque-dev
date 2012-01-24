function ImgExternal (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.menu = null;
    //this.menu_elements = {};
    this.viewer.addCommand ('External', callback (this, 'toggleMenu'));    
}
ImgExternal.prototype = new ViewerPlugin();

ImgExternal.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
}

ImgExternal.prototype.newImage = function () {

}

ImgExternal.prototype.updateImage = function () {
}

ImgExternal.prototype.createButton = function (name, cb){
    var bt= document.createElementNS(xhtmlns, 'button');
    bt.innerHTML = name;
    bt.setAttribute('id', name);
    bt.onclick = cb;
    this.menu.appendChild (bt);
    return bt;
}

ImgExternal.prototype.toggleMenu = function () {
    if (this.menu == null) {
        this.menu = document.createElementNS(xhtmlns, "div");
        this.menu.className = "imgview_opdiv";

        this.bt_bv   = this.createButton('bioView', callback (this, 'launchBioView'));
        this.bt_bv3d = this.createButton('bioView3D', callback (this, 'launchBioView3D'));

        this.bt_expGobs = this.createButton('Export GObjects to Google Docs', callback (this, 'exportGObjectsToGoogle'));
        this.bt_expTags = this.createButton('Export Tags to Google Docs', callback (this, 'exportTagsToGoogle'));

        this.menu.style.display = "none";
        this.viewer.imagediv.appendChild(this.menu);
    } 

    this.viewer.active_submenu(this.menu);
    if (this.menu.style.display  == "none" ) {
        this.menu.style.display = "";
        
        //var view_top = this.parent.offsetTop;
        //var view_left = this.parent.offsetLeft; 
	      //this.menu.style.left = view_left+10 + "px";
	      //this.menu.style.top = view_top+10 + "px";
	      
        var num_pages = this.viewer.imagedim.z * this.viewer.imagedim.t;
        if (this.bt_bv3d)
          this.bt_bv3d.style.display = (num_pages <= 1)?"none":"";    	      
	               
    } else
        this.menu.style.display = "none";
}


ImgExternal.prototype.launchBioView = function () {
    var user = this.viewer.bq_user.credentials.user;
    var pass = this.viewer.bq_user.credentials.pass;  
    var new_url = 'bioview://resource/?user='+user+'&pass='+pass+'&url='+this.viewer.imageuri;  
    //window.location = new_url;
    window.open( new_url );      
}

ImgExternal.prototype.launchBioView3D = function () {
    if (this.viewer.imagedim.z * this.viewer.imagedim.t <= 1) {
        alert ("Image is not a 3D stack (multiplane image)");
        return;
    }
    var user = this.viewer.bq_user.credentials.user;
    var pass = this.viewer.bq_user.credentials.pass;  
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
