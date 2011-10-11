// Small plugin for scaling images
function ImgScale (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);

    this.viewer.addCommand ('-', callback (this, 'scale', 0.75));
    this.viewer.addCommand ('+', callback (this, 'scale', 1.5));

}
ImgScale.prototype = new ViewerPlugin();

ImgScale.prototype.create = function (parent) {
    this.parent = parent;
    return parent;    
}

ImgScale.prototype.scale = function (scale) {
    this.viewer.current_view.scaleBy (scale);
    this.viewer.need_update();
}

ImgScale.prototype.newImage = function () {
    var view = this.viewer.current_view;
    var win_w = this.parent.offsetWidth;    
    var win_h = this.parent.offsetHeight;  
    var img_w = view.original_width;    
    var img_h = view.original_height; 
    
    // set to a view fitting the initial viewer box
    //this.viewer.current_view.scaleToBox(Math.min(win_w,img_w), Math.min(win_h,img_h)); 
    
    // set to smallest possible view
    this.viewer.current_view.scaleToSmallest();       
}
