/*******************************************************************************
  ImgInfoBar - creates text about an image
  
  GSV 3.0 : PanoJS3
  @author Dmitry Fedorov  <fedorov@ece.ucsb.edu>   
  
  Copyright (c) 2010 Dmitry Fedorov, Center for Bio-Image Informatics
  
  using: isClientTouch() and isClientPhone() from utils.js

*******************************************************************************/

ImgViewer.INFO_CONTROL_STYLE = "padding: 5px; text-shadow: 1px 1px 1px #000000; font-size: 12px;";

if (isClientTouch())
  ImgViewer.INFO_CONTROL_STYLE = "padding: 10px; text-shadow: 2px 2px 2px #000000; font-size: 18px;";

if (isClientPhone())
  ImgViewer.INFO_CONTROL_STYLE   = "padding: 10px; text-shadow: 6px 6px 6px #000000; font-size: 40px;";

function ImgInfoBar (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
}

ImgInfoBar.prototype = new ViewerPlugin();
ImgInfoBar.prototype.create = function (parent) {
    this.parentdiv = parent;
    this.infobar = null;
    return parent;
}

ImgInfoBar.prototype.newImage = function () {

}

ImgInfoBar.prototype.updateImage = function () {

    // create info bar
    if (!this.infobar) {
      var surf = this.parentdiv;
      if (this.viewer.viewer_controls_surface) surf = this.viewer.viewer_controls_surface;
        
      this.infobar = document.createElement('span');
      this.infobar.className = 'info';
      this.infobar.setAttribute("style", ImgViewer.INFO_CONTROL_STYLE );
      this.infobar.style.cssText = ImgViewer.INFO_CONTROL_STYLE;
      surf.appendChild(this.infobar);
    }
    
    // update inforamtion string
    var view = this.viewer.current_view;  
    var dim = view.imagedim;
    var imgphys = this.viewer.imagephys;  


    if (this.infobar) {
      var s = 'Image: '+dim.x+'x'+dim.y;
      if (dim.z>1) s += ' Z:'+dim.z;
      if (dim.t>1) s += ' T:'+dim.t;      
      s += ' ch: '+ dim.ch;
      if (imgphys && imgphys.pixel_depth) s += '/'+ imgphys.pixel_depth +'bits';
      s += ' Scale: '+ view.scale*100 +'%';   
      this.infobar.innerHTML = s;
    }
}

ImgInfoBar.prototype.updatePosition = function () {
    //if (this.scalebar == null) return;
    //var view = this.viewer.current_view;  
    //var imgphys = this.viewer.imagephys;  
    //this.scalebar.setValue( imgphys.pixel_size[0]/view.scale );   
}
