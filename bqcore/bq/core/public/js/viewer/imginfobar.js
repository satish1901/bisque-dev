/*******************************************************************************
  ImgInfoBar - creates text about an image

  GSV 3.0 : PanoJS3
  @author Dmitry Fedorov  <fedorov@ece.ucsb.edu>

  Copyright (c) 2010 Dmitry Fedorov, Center for Bio-Image Informatics

  using: isClientTouch() and isClientPhone() from utils.js

*******************************************************************************/

function ImgInfoBar (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
}

ImgInfoBar.prototype = new ViewerPlugin();
ImgInfoBar.prototype.create = function (parent) {
    this.parentdiv = parent;
    this.infobar = null;
    this.namebar = null;
    this.mobile_cls = '';
    if (isClientTouch())
        this.mobile_cls = 'tablet';
    if (isClientPhone())
        this.mobile_cls = 'phone';
    return parent;
};

ImgInfoBar.prototype.newImage = function () {

};

ImgInfoBar.prototype.updateImage = function () {
    var viewer = this.viewer,
        view = viewer.current_view,
        dim = view.imagedim,
        imgphys = viewer.imagephys,
        surf = viewer.viewer_controls_surface ? viewer.viewer_controls_surface : this.parentdiv,
        params = viewer.parameters || {};

    // create info bar
    if (!this.infobar) {
        this.infobar = document.createElement('span');
        this.infobar.className = 'info '+this.mobile_cls;
        surf.appendChild(this.infobar);
    }

    // create name bar
    if (!this.namebar && !(viewer.parameters && viewer.parameters.hide_file_name_osd) ) {
        this.namebar = document.createElement('a');
        this.namebar.className = params.logo ? 'info name logo '+this.mobile_cls : 'info name '+this.mobile_cls;
        surf.appendChild(this.namebar);
    }

    // create position bar
    if (!this.posbar) {
        this.posbar = document.createElement('a');
        this.posbar.className = 'info position '+this.mobile_cls;
        surf.appendChild(this.posbar);
    }

    if (this.infobar) {
        var s = 'Image: '+dim.x+'x'+dim.y;
        if (dim.z>1) s += ' Z:'+dim.z;
        if (dim.t>1) s += ' T:'+dim.t;
        s += ' ch: '+ dim.ch;
        if (imgphys && imgphys.pixel_depth) s += '/'+ imgphys.pixel_depth +'bits';
        s += ' Scale: '+ view.scale*100 +'%';
        this.infobar.innerHTML = s;
    }

    if (this.namebar) {
        this.namebar.href = '/client_service/view?resource='+viewer.image.uri;
        if (!params.logo) {
            this.namebar.innerHTML = viewer.image.name;
        }
    }
};

