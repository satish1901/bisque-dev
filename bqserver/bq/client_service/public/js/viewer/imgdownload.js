function ImgDownload (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.menu = null;
    this.menu_elements = {};
    this.viewer.addCommand ('Download', callback (this, 'toggleMenu'));
}
ImgDownload.prototype = new ViewerPlugin();

ImgDownload.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
}

ImgDownload.prototype.newImage = function () {
}
ImgDownload.prototype.updateImage = function () {
}


ImgDownload.prototype.createButton = function (name, cb){
    var bt= document.createElementNS(xhtmlns, 'button');
    bt.innerHTML = name;
    bt.setAttribute('id', name);
    bt.onclick = cb;
    this.menu.appendChild (bt);
    //this.menu_elements[name] = combo;
    return bt;
}

ImgDownload.prototype.toggleMenu = function () {

    if (this.menu == null) {
        this.menu = document.createElementNS(xhtmlns, "div");
        this.menu.className = "imgview_opdiv";

        this.createButton('Original image', callback (this, 'downloadOriginal'));
        /*
        this.createButton('Graphical objects', callback (this, 'downloadGObjects'));
        this.createButton('Graphical objects as CSV', callback (this, 'downloadGObjectsCSV'));        
        this.createButton('Tags', callback (this, 'downloadTags'));
        this.createButton('Tags as CSV', callback (this, 'downloadTagsCSV'));        
        this.createButton('Embedded metadata', callback (this, 'downloadMetadata'));        
        this.createButton('Convert format', callback (this, 'toggleImageConvert'));
        */
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
    } else
        this.menu.style.display = "none";
}

ImgDownload.prototype.downloadOriginal = function () {
    //window.location = this.viewer.imagesrc;
    window.open( this.viewer.imagesrc );
}

ImgDownload.prototype.downloadGObjects = function () {
    //window.location = this.viewer.imageuri + "/gobject?view=deep";
    window.open( this.viewer.imageuri + "/gobject?view=deep" );    
}

ImgDownload.prototype.downloadGObjectsCSV = function () {
    //window.location = this.viewer.imageuri + "/gobject?view=deep&format=csv";
    window.open( this.viewer.imageuri + "/gobject?view=deep&format=csv" );        
}

ImgDownload.prototype.downloadTags = function () {
    //window.location = this.viewer.imageuri + "/tag?view=deep";
    window.open( this.viewer.imageuri + "/tag?view=deep" );        
}

ImgDownload.prototype.downloadTagsCSV = function () {
    //window.location = this.viewer.imageuri + "/tag?view=deep&format=csv";
    window.open( this.viewer.imageuri + "/tag?view=deep&format=csv" );        
}

ImgDownload.prototype.downloadMetadata = function () {
    //window.location = this.viewer.imagesrc + "?meta";
    window.open( this.viewer.imagesrc + "?meta" );        
}

ImgDownload.prototype.toggleImageConvert = function () {
    if (this.imgcnv == null) {
        this.imgcnv = new ImageConverter (this.viewer.imageuri);
        this.imgcnv.GetImageInfo (this.viewer.imagesrc);
        this.menu.appendChild (this.imgcnv.maindiv);

        this.imgcnv.maindiv.style.display = "none";
    }

    if (this.imgcnv.maindiv.style.display  == "none" ) 
        this.imgcnv.maindiv.style.display = "";
    else
        this.imgcnv.maindiv.style.display = "none";
}
