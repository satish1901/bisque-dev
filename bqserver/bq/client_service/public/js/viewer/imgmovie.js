function ImgMovie (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.bt = this.viewer.addCommand ('View as movie', callback (this, 'showMovie'));
}
ImgMovie.prototype = new ViewerPlugin();

ImgMovie.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
}

ImgMovie.prototype.newImage = function () {
    if (this.viewer.imagedim.z * this.viewer.imagedim.t <= 1) {
        this.bt.style.display="none";
    } else {
        this.bt.style.display="";
    }
}
ImgMovie.prototype.updateImage = function () {
}

ImgMovie.prototype.showMovie = function () {
    if (this.viewer.imagedim.z * this.viewer.imagedim.t <= 1) {
        alert ("Image is not a movie (multiplane image)");
        return;
    }

    //window.location = '/bisquik/movieplayer?resource='+this.viewer.imageuri;
    window.open( '/client_service/movieplayer?resource='+this.viewer.imageuri );         
}

