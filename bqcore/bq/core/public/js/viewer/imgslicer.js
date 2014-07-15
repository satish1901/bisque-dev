/*
  Slice a multiplane image while keeping a few frames around.
*/


function ImgSlicer (viewer, name){
    var p = viewer.parameters || {};
    // default values for projection are: '', 'projectmax', 'projectmin'
    // only in the case of 5D image: 'projectmaxt', 'projectmint', 'projectmaxz', 'projectminz'
    this.default_projection  = p.projection || '';
    this.plane_buffer_sz = 9;
    this.update_delay_ms = 250;  // Delay before requesting new frames
    this.cache_delay_ms = 700;  // Delay before pre-caching new frames

    this.base = ViewerPlugin;
    this.base (viewer, name);
}

ImgSlicer.prototype = new ViewerPlugin();

ImgSlicer.prototype.create = function (parent) {
    this.parent = parent;
    this.div  = document.createElementNS(xhtmlns, "div");
    this.div.id =  'imgviewer_slicer';
    this.div.className = "image_viewer_slicer";
    this.tslider = null;
    this.zslider = null;
    this.t = -1;
    this.z = -1;
    this.buffer_len = this.plane_buffer_sz; // Buffer X images
    this.dim = null;           // Last loaded image dimensions

    // pre-cache buffers for both Z and T dimensions
    this.image_buffer_z = [];
    for (var i=0; i<this.buffer_len; i++) {
        this.image_buffer_z[i] = [];
    }
    this.image_buffer_t = [];
    for (var i=0; i<this.buffer_len; i++) {
        this.image_buffer_t[i] = [];
    }

    parent.appendChild(this.div);
    return this.div;
};

ImgSlicer.prototype.getParams = function () {
    return this.params || {};
};

ImgSlicer.prototype.updateView = function (view) {
    if (this.z<0 && this.t<0) {
        this.z = view.z;
        this.t = view.t;
    } else {
        view.z = this.z;
        view.t = this.t;
    }
    if (this.prev) {
        view.z = this.z = this.prev.z;
        view.t = this.t = this.prev.t;
    }

    var projection = this.default_projection;
    if (!this.menu) this.createMenu();
    if (this.menu) {
        projection = this.projection_combo.getValue();
    }

    this.params = {};

    // '', 'projectmax', 'projectmin', 'projectmaxt', 'projectmint', 'projectmaxz', 'projectminz'
    if (!projection || projection=='') {
        if (this.prev)
            this.prev = undefined;
        this.params.z1 = view.z+1;
        this.params.t1 = view.t+1;
        view.addParams ( 'slice=,,'+(view.z+1)+','+(view.t+1) );
        if (this.zslider) this.zslider.show();
        if (this.tslider) this.tslider.show();
    } else {
        var showzslider = false;
        var showtslider = false;
        var newdimz = 1;
        var newdimt = 1;
        var prjtype = projection;
        if (!this.prev)
            this.prev = {z: view.z, t: view.t};

        if (prjtype.match('^projectmax')=='projectmax' ) projection = 'projectmax';
        if (prjtype.match('^projectmin')=='projectmin' ) projection = 'projectmin';

        // now take care of required pre-slicing for 4D/5D cases
        var dim = view.imagedim;

        if (prjtype=='projectmaxz' || prjtype=='projectminz') {
            this.params.z1 = 1;
            this.params.z2 = dim.z;
            this.params.t1 = view.t+1;
            view.addParams ( 'slice=,,1-'+(dim.z)+','+(view.t+1) );
            showtslider = true;
            newdimt = dim.t;
        } else
        if (prjtype=='projectmaxt' || prjtype=='projectmint') {
            this.params.z1 = dim.z+1;
            this.params.t1 = 1;
            this.params.t2 = view.t;
            view.addParams ( 'slice=,,'+(view.z+1)+',1-'+(dim.t) );
            showzslider = true;
            newdimz = dim.z;
        }
        this.params.projection = projection;

        view.addParams (projection);
        view.imagedim.t = newdimt;
        view.imagedim.z = newdimz;
        view.imagedim.project = prjtype;
        if (this.zslider) this.zslider.setVisible(showzslider);
        if (this.tslider) this.tslider.setVisible(showtslider);
    }
};

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

    if (this.cache_timeout) clearTimeout (this.cache_timeout);
    if (this.dim.z>1 || this.dim.t>1)
        this.cache_timeout = setTimeout(callback(this, 'preCacheNeighboringImages'), this.cache_delay_ms);
};

ImgSlicer.prototype.updatePosition = function () {
    var view = this.viewer.current_view;
    var dim = view.imagedim.clone();
    var surf = this.viewer.viewer_controls_surface ? this.viewer.viewer_controls_surface : this.div;

    if (!this.tslider && dim.t>1) {
        this.tslider = Ext.create('BQ.slider.TSlider', {
            renderTo: surf,
            autoShow: true,
            hysteresis: this.update_delay_ms,
            value: view.t,
            minValue: 0,
            maxValue: dim.t-1,
            listeners: {
                scope: this,
                change: function(newValue) {
                    this.sliceT(newValue);
                },
            },
            resolution: this.pixel_info_t[0],
            unit: this.pixel_info_t[1],
        });
    }

    if (!this.zslider && dim.z>1) {
        this.zslider = Ext.create('BQ.slider.ZSlider', {
            renderTo: surf,
            autoShow: true,
            hysteresis: this.update_delay_ms,
            value: view.z,
            minValue: 0,
            maxValue: dim.z-1,
            listeners: {
                scope: this,
                change: function(newValue) {
                    this.sliceZ(newValue);
                },
            },
            resolution: this.pixel_info_z[0],
            unit: this.pixel_info_z[1],
        });
    }

};

ImgSlicer.prototype.sliceT = function (val) {
    if (this.t === val) return;
    this.t = val;
    this.viewer.need_update();
};

ImgSlicer.prototype.sliceZ = function (val) {
    if (this.z === val) return;
    this.z = val;
    this.viewer.need_update();
};

ImgSlicer.prototype.setPosition = function (z, t) {
    if (z) {
        this.z = z;
        if (this.zslider)
            this.zslider.setValue(z);
    }
    if (t) {
        this.t = t;
        if (this.tslider)
            this.tslider.setValue(t);
    }
    this.viewer.need_update();
};

ImgSlicer.prototype.doCache = function (pos, posmax, buf, bufmax, slice, nslice, tiles) {
    if (pos<0) return;
    if (pos>=posmax) return;
    for (var p=0; p<bufmax; p++) {
        var u = tiles[p].replace(slice, nslice);
        try {
            buf[p].src = u;
        } catch (e) {
            var I = new Image();
            I.validate = "never";
            I.src = u;
            buf[p] = I;
        }
    }
};

ImgSlicer.prototype.preCacheNeighboringImages = function () {
    this.cache_timeout = null;

    var tiles = this.viewer.tiles.getLoadedTileUrls();
    var num_tiles = tiles.length;
    var slice = 'slice=,,'+(this.z+1)+','+(this.t+1);
    var dim = this.dim;

    if (dim.z>1)
    for (var i=0; i<this.buffer_len; i++) {
        var buf = this.image_buffer_z[i];
        var hp = Math.floor(i/2);
        var z = i%2 ? this.z+hp : this.z-hp;
        var nslice = 'slice=,,'+(z+1)+','+(this.t+1);
        this.doCache(z, this.dim.z, buf, num_tiles, slice, nslice, tiles);
    }

    if (dim.t>1)
    for (var i=0; i<this.buffer_len; i++) {
        var buf = this.image_buffer_t[i];
        var hp = Math.floor(i/2);
        var t = i%2 ? this.t+hp : this.t-hp;
        var nslice = 'slice=,,'+(this.z+1)+','+(t+1);
        this.doCache(t, this.dim.t, buf, num_tiles, slice, nslice, tiles);
    }
};

ImgSlicer.prototype.ensureVisible = function (gob) {
    if (!gob.vertices || gob.vertices.length<1) return;
    var z = gob.vertices[0].z;
    var t = gob.vertices[0].t;
    /*var v=undefined;
    if (gob.vertices.length>1 && gob.resource_type in {polyline: undefined, polygon: undefined}) {
        for (var i=1; (v=gob.vertices[i]); i++) {
            z += v.z;
            t += v.t;
        }
        z /= gob.vertices.length;
        t /= gob.vertices.length;
    }*/

    this.setPosition (z, t);
};

//-------------------------------------------------------------------------
// Menu GUI for projections
//-------------------------------------------------------------------------
ImgSlicer.prototype.doUpdate = function () {
    this.viewer.need_update();
};

ImgSlicer.prototype.changed = function () {
  //if (!this.update_check || (this.update_check && this.update_check.checked) )
    this.viewer.need_update();
};

//-------------------------------------------------------------------------
// Menu for projections
//-------------------------------------------------------------------------

ImgSlicer.prototype.createMenu = function () {
    if (this.menu) return;
    //var surf = this.viewer.viewer_controls_surface ? this.viewer.viewer_controls_surface : this.parent;
    this.menu = this.viewer.createViewMenu();

    this.loadPreferences(this.viewer.preferences);

    var dim = this.viewer.imagedim;
    //var planes_title = 'Image planes [W:'+dim.x+', H:'+dim.y+', Z:'+dim.z+', T:'+dim.t+']';
    var planes_title = 'Image planes [Z:'+dim.z+', T:'+dim.t+']';


    var combo_options = [ {'value':'', 'text':'None'} ];

    // only add projection options for 3D images
    if (dim.z>1 || dim.t>1) {
        combo_options.push({'value':'projectmax', 'text':'Max'});
        combo_options.push({'value':'projectmin', 'text':'Min'});
    }

    // only add these additional options for 4D/5D images
    if (dim.z>1 && dim.t>1) {
        combo_options.push({'value':'projectmaxt', 'text':'Max for current Z'});
        combo_options.push({'value':'projectmint', 'text':'Min for current Z'});
        combo_options.push({'value':'projectmaxz', 'text':'Max for current T'});
        combo_options.push({'value':'projectminz', 'text':'Min for current T'});
    }

    this.projection_heading = this.menu.add({
        xtype: 'displayfield',
        fieldLabel: planes_title,
        cls: 'heading',
    });

    this.projection_combo = this.viewer.createCombo( 'Intensity projection', combo_options, this.default_projection, this, this.changed);

    if (dim.z*dim.t===1) {
        this.projection_heading.setVisible(false);
        this.projection_combo.setVisible(false);
    }
};

ImgSlicer.prototype.loadPreferences = function (p) {
    if (!p) return;
    this.default_projection  = 'projection'  in p ? p.projection  : this.default_projection;
};


