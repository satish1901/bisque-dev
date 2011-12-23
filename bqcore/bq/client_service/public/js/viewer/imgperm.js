//  Img Viewer plugin for dealing with image permssions and deletion
//
function ImgPermissions (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.bt_public = this.viewer.addCommand ('Public', callback (this, 'togglePermission'));
    this.bt_delete = this.viewer.addCommand ('Delete', callback (this, 'deleteImage'));

}
ImgPermissions.prototype = new ViewerPlugin();

ImgPermissions.prototype.update_state = function () {
    var perm = this.viewer.image.permission;
    this.bt_public.innerHTML=(perm=='published')?'Published':'Private';    
}
ImgPermissions.prototype.newImage = function () {
    var show = this.viewer.user && (this.viewer.image.owner == this.viewer.user);
    //var show =  (this.viewer.image.owner_id == this.viewer.user_id);
    this.bt_public.style.display = show?"":"none";
    //this.bt_delete.style.display = show?"":"none";

    this.update_state();
}
ImgPermissions.prototype.togglePermission = function () {
    var uri = this.viewer.imageuri;
    var src = this.viewer.imagesrc;
    var perm = this.viewer.image.permission;
    perm = (perm == 'published')?'private':'published';

    // Dataserver 
    var xmldata = '<request>';
    xmldata += '<image uri="' + uri + '" permission="' + perm +'" />';
    xmldata += '</request>';
	makeRequest( uri, callback(this, 'checkPerm'), null, "post", xmldata );

    this.viewer.image.permission = perm;
}
ImgPermissions.prototype.checkPerm = function (ignore, response) {
    this.update_state()
}
ImgPermissions.prototype.deleteImage = function (  ) {
    var ok= window.confirm ("Really delete this image?");
    if (ok) {
      var uri = this.viewer.imageuri;      
      this.viewer.image.delete_(callback(this, 'close_viewer'));
    }
}

ImgPermissions.prototype.close_viewer = function (){
    //history.back();
    window.close();
}


