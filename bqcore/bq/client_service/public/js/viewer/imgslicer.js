/*
  Slice a multiplane image while keeping a few frames around.
*/


function ImgSlicer (viewer, name){
  
    // default values for projection are: '', 'projectmax', 'projectmin' 
    // only in the case of 5D image: 'projectmaxt', 'projectmint', 'projectmaxz', 'projectminz'
    this.default_projection  = '';  
    this.plane_buffer_sz = 7;
    this.update_delay_ms = 250;  // Delay before requesting new frames
    this.cache_delay_ms = 1000;  // Delay before pre-caching new frames
  
    this.base = ViewerPlugin;
    this.base (viewer, name);
    
    this.menu = null;
    this.menu_elements = {};
    
    this.viewer.addCommand ('Planes', callback (this, 'toggleMenu'));        
}

ImgSlicer.prototype = new ViewerPlugin();

ImgSlicer.prototype.create = function (parent) {
    this.parent = parent;  
    this.div  = document.createElementNS(xhtmlns, "div");
    this.div.id =  'imgviewer_slicer';
    this.div.className = "image_viewer_slicer";
    this.tslider = null;
    this.zslider = null;
    this.t = 0;
    this.z = 0;
    this.buffer_len=this.plane_buffer_sz;            // Buffer X images 
    this.dim = null;           // Last loaded image dimensions

    // pre-cache buffers for both Z and T dimensions 
    this.image_buffer_z  = new Array (0);
    for (var i=0; i<this.buffer_len; i++){
        var I = new Image();
        I.validate = "never";
        this.image_buffer_z.push( I );        
    }
    this.image_buffer_t  = new Array (0);
    for (var i=0; i<this.buffer_len; i++){
        var I = new Image();
        I.validate = "never";
        this.image_buffer_t.push( I );       
    }

    this.image_urls = null;
    this.base_url = null;

    parent.appendChild(this.div);
    return this.div;
}

ImgSlicer.prototype.createUrls  =function (view){
    var dim = view.imagedim;
    this.image_urls = new Array (dim.z);
    var save_z = this.z
    var save_t = this.t;

    for (var z=0;z < dim.z; z++) {
        this.image_urls[z] = new Array (dim.t);
        this.z = z;
        for (var t=0;  t < dim.t; t++) {
            this.t = t;
            this.image_urls[z][t] = this.viewer.image_url ();
        }
    }
    this.t = save_t;
    this.z = save_z;
}

//ImgSlicer.prototype.showSlider = function ( item, visible ) {
//    if (item) item.show(visible);
//}

ImgSlicer.prototype.updateView = function (view) {
    view.z = this.z;
    view.t = this.t;
    
    var projection = this.default_projection;
    if (!this.menu) this.createMenu();     
    if (this.menu) {
        cb = this.menu_elements['Intensity projection'];
        if (cb) projection = cb.value;
    }

    // '', 'projectmax', 'projectmin', 'projectmaxt', 'projectmint', 'projectmaxz', 'projectminz'
    if (projection == '') {
        view.addParams ( 'slice=,,'+(view.z+1)+','+(view.t+1) );
        if (this.zslider) this.zslider.show();
        if (this.tslider) this.tslider.show();    
    } else {
        var showzslider = false;
        var showtslider = false;
        var newdimz = 1;
        var newdimt = 1;                
        var prjtype = projection;
        if (prjtype.match('^projectmax')=='projectmax' ) projection = 'projectmax';       
        if (prjtype.match('^projectmin')=='projectmin' ) projection = 'projectmin';

        // now take care of required pre-slicing for 4D/5D cases
        var dim = view.imagedim;
        if (prjtype=='projectmaxz' || prjtype=='projectminz') {
            view.addParams ( 'slice=,,1-'+(dim.z)+','+(view.t+1) );
            showtslider = true;
            newdimt = dim.t;    
        } else 
        if (prjtype=='projectmaxt' || prjtype=='projectmint') {                 
            view.addParams ( 'slice=,,'+(view.z+1)+',1-'+(dim.t) );
            showzslider = true;              
            newdimz = dim.z;    
        }
        
        view.addParams (projection);
        view.imagedim.t = newdimt;
        view.imagedim.z = newdimz;
        if (this.zslider) this.zslider.setVisible(showzslider);
        if (this.tslider) this.tslider.setVisible(showtslider);                        
    }
}

ImgSlicer.prototype.updateImage = function () {
    var view = this.viewer.current_view;
    var dim = view.imagedim.clone();

    var imgphys = this.viewer.imagephys;  

    if (!this.pixel_info_z) {  
      this.pixel_info_z = [undefined,undefined];
      if (imgphys) this.pixel_info_z = imgphys.getPixelInfoZ();
    }
    if (!this.pixel_info_t) {  
      this.pixel_info_t = [undefined,undefined];
      if (imgphys) this.pixel_info_t = imgphys.getPixelInfoT();
    }
    
    // recompute sliders    
    if (this.dim == null || this.dim.t != dim.t) {
        if (this.tslider) {
            this.tslider.destroy();
            this.tslider=null;
        }
        if (dim.t<=1) {
            if (this.tslider) { this.tslider.destroy(); this.tslider=null; }
            this.t = 0;
        }
    }
    if (this.dim == null || this.dim.z != dim.z) {
        if (this.zslider) {
            this.zslider.destroy();
            this.zslider=null;            
        }
        if (dim.z<=1) {
            if (this.zslider) { this.zslider.destroy(); this.zslider=null; }
            this.z = 0;
        }

    }
   
    
    this.dim = dim;
    if (this.base_url != this.viewer.image_url () ){
        this.createUrls(view);
        this.base_url = this.viewer.image_url ();
    }
   
    if (this.cache_timeout) clearTimeout (this.cache_timeout);
    this.cache_timeout = setTimeout(callback(this, 'preCacheNeighboringImages'), this.cache_delay_ms);
}

ImgSlicer.prototype.updatePosition = function () {
    var view = this.viewer.current_view;
    var dim = view.imagedim.clone();    
    var surf = this.div;
    if (this.viewer.viewer_controls_surface) surf = this.viewer.viewer_controls_surface;
    
    if (!this.tslider && dim.t>1) {
        this.tslider = Ext.create('BQ.slider.TSlider', {
            renderTo: surf,
            autoShow: true,
            hysteresis: this.update_delay_ms,
            minValue: 0,
            maxValue: dim.t-1,
            listeners: { scope: this, change: function(newValue) { 
              this.sliceT(newValue); 
            } },
            resolution: this.pixel_info_t[0],
            unit: this.pixel_info_t[1],                 
        });            
    }

    if (!this.zslider && dim.z>1) {
        this.zslider = Ext.create('BQ.slider.ZSlider', {
            renderTo: surf,
            autoShow: true,
            hysteresis: this.update_delay_ms,
            minValue: 0,
            maxValue: dim.z-1,
            listeners: { scope: this, change: function(newValue) { 
              this.sliceZ(newValue); 
            } },
            resolution: this.pixel_info_z[0],
            unit: this.pixel_info_z[1],                 
        });                
    }
 
}

ImgSlicer.prototype.sliceT = function (val) {
    this.t = val;
    this.viewer.need_update();
}

ImgSlicer.prototype.sliceZ = function (val) {
    this.z = val;
    this.viewer.need_update();
}

ImgSlicer.prototype.preCacheNeighboringImages = function () {
    this.cache_timeout = null;  
    if (this.dim.z>1)
    for (var i=0; i<this.buffer_len; i++) {
        z = this.z-Math.floor(this.buffer_len/2) + i; 
        if (z<0) continue;
        if (z>=this.dim.z) continue;
        this.image_buffer_z[i].src = this.image_urls[z][this.t];        
    }
    if (this.dim.t>1)
    for (var i=0; i<this.buffer_len; i++) {
        t = this.t-Math.floor(this.buffer_len/2) + i; 
        if (t<0) continue;
        if (t>=this.dim.t) continue;
        this.image_buffer_t[i].src = this.image_urls[this.z][t];        
    }
}


//-------------------------------------------------------------------------
// Menu GUI for projections
//-------------------------------------------------------------------------
ImgSlicer.prototype.doUpdate = function () {
    this.viewer.need_update();
}

ImgSlicer.prototype.changed = function () {
  //if (!this.update_check || (this.update_check && this.update_check.checked) ) 
    this.viewer.need_update();
}

ImgSlicer.prototype.createCombo = function (name, items, defval, parentdiv){
    var combo= document.createElementNS(xhtmlns, 'select');

    for (var i=0; i< items.length; i++) {
        var option = document.createElementNS(xhtmlns, 'option');
        option.text =  items[i][0];
        option.value = items[i][1];
        option.selected = (option.value == defval);
        combo.appendChild (option);
    }
    
    var div = document.createElementNS(xhtmlns, 'div');
    
    var label = document.createElementNS(xhtmlns, 'label');
    label.textContent = name;
   
    div.appendChild (label);
    div.appendChild (combo);    
    parentdiv.appendChild (div);
   
    this.menu_elements[name] = combo;
  	combo.onchange = callback(this, "changed", name);
    return combo;
}

ImgSlicer.prototype.createGroup = function (name, parentdiv){
    var group = document.createElementNS(xhtmlns, 'div');
    group.setAttribute('id', 'group');

    var label = document.createElementNS(xhtmlns, 'h3');
    label.textContent = name;
    group.appendChild (label);   

    parentdiv.appendChild (group);
    return group;
}

//-------------------------------------------------------------------------
// Menu for projections
//-------------------------------------------------------------------------

ImgSlicer.prototype.createMenu = function () {
    if (this.menu != null) return;
    
    this.menu = document.createElementNS(xhtmlns, "div");
    this.menu.className = "imgview_opdiv";
    //this.menu.style.left = this.parent.offsetLeft +10+ "px";
    //this.menu.style.top = this.parent.offsetTop +10+ "px";       
    
    var dim = this.viewer.imagedim;
    var planes_title = 'Image planes [W:'+dim.x+', H:'+dim.y+', Z:'+dim.z+', T:'+dim.t+']';
    var group_planes = this.createGroup (planes_title, this.menu);                            

    var combo_options = [ ["None", ""] ];
    
    // only add projection options for 3D images                        
    if (dim.z>1 || dim.t>1) { 
        combo_options.push(["Max", "projectmax"]);    
        combo_options.push(["Min", "projectmin"]);  
    }                        
                        
    // only add these additional options for 4D/5D images
    if (dim.z>1 && dim.t>1) { 
        combo_options.push(["Max for current Z", "projectmaxt"]);    
        combo_options.push(["Min for current Z", "projectmint"]);  
        combo_options.push(["Max for current T", "projectmaxz"]);
        combo_options.push(["Min for current T", "projectminz"]);
    }
    this.createCombo ('Intensity projection', combo_options, this.default_projection, group_planes);
                        
    this.menu.style.display = "none";
    this.viewer.imagediv.appendChild(this.menu);    
}

ImgSlicer.prototype.toggleMenu = function () {
    var need_update = false;
    if (this.menu == null) {
        this.createMenu();
        need_update =true;
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

    //if (need_update) 
    //    this.viewer.need_update();        

}

