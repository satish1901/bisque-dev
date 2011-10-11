
function ImageRenderer (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.events  = {};
}
ImageRenderer.prototype = new ViewerPlugin();

ImageRenderer.prototype.create = function (parent) {
    this.parent = parent;
    this.image  = document.createElementNS(xhtmlns, "img");
    this.parent.appendChild(this.image);
    return parent;    
}

ImageRenderer.prototype.newImage = function () {
}

ImageRenderer.prototype.updateImage = function (){
    var viewstate = this.viewer.current_view;
    var url = this.viewer.image_url();

    this.image.style.width = viewstate.width+'px';
    this.image.style.height = viewstate.height+'px';

    //Show a waitcursor on long image loads.
    this.image.onload = function () { document.body.style.cursor = 'default'; };
    if (url != this.image.src ) {
        document.body.style.cursor = 'wait'; // Broken On chrome
        this.image.src = url;
    }
    //this.svgimg.setAttributeNS( null, 'x', 0);  
    //this.svgimg.setAttributeNS( null, 'y', 0);  
    //this.svgimg.setAttributeNS( null, 'width', viewstate.width);  
    //this.svgimg.setAttributeNS( null, 'height', viewstate.height);  
}
