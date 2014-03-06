/*******************************************************************************
  ExtJS wrapper for the html5 video player
  Author: Dima Fedorov <dima@dimin.net>

  Configurations:
      resource   - url string or bqimage (required)
      phys       - image phys BQImagePhys (preferred)
      preferences - BQPpreferences object (preferred)

  Events:
      loaded     - event fired when the viewer is loaded
      working
      done
      error

*******************************************************************************/

Ext.define('BQ.viewer.Movie', {
    alias: 'widget.bq_movie_viewer',
    extend: 'Ext.container.Container',
    border: 0,
    cls: 'bq-viewer-movie',

    update_delay_ms: 250,  // Update the viewer asynchronously

    constructor: function(config) {
        this.addEvents({
            'loaded': true,
            'changed': true,
        });
        this.callParent(arguments);
        return this;
    },

    initComponent : function() {
        /*this.addListener( 'resize', function(me, width, height) {
            if (me.viewer) me.viewer.resize();
        });*/
        this.callParent();
        this.plug_ins = [ new PlayerSlice(this), new PlayerSize(this), new PlayerDisplay(this), new PlayerFormat(this) ];
    },

    afterRender : function() {
        this.callParent();
        this.setLoading('Loading...');
        if (this.resource && typeof this.resource === 'string') {
            BQFactory.request({
                uri: this.resource,
                uri_params: {view: 'short'},
                cb: callback(this, this.onImage),
                errorcb: callback(this, this.onerror),
            });
        }
        else
            this.onImage(this.resource);

        /*this.keyNav = Ext.create('Ext.util.KeyNav', document.body, {
            left:     this.onkeyboard,
            right:    this.onkeyboard,
            up:       this.onkeyboard,
            down:     this.onkeyboard,
            pageUp:   this.onkeyboard,
            pageDown: this.onkeyboard,
            scope : this
        });*/
    },

    onDestroy: function() {
        if (this.menu && this.menu.isVisible())
            this.menu.hide();
    },

    onImage: function(resource) {
        if (!resource) return;
        this.resource = resource;
        if (!this.phys) {
            var phys = new BQImagePhys (this.resource);
            phys.load (callback (this, this.onPhys) );
        }
        this.onPartFetch();
    },

    onPhys: function(phys) {
        if (!phys) return;
        this.phys = phys;
        this.onPartFetch();
    },

    onPartFetch: function() {
        if (!this.resource || !this.phys) return;
        this.setLoading(false);
        this.dims = new ImageDim (this.phys.x, this.phys.y, this.phys.z, this.phys.t, this.phys.ch);
        if (!this.viewer)
            this.loadPlayer();
    },

    loadPlayer: function() {
        if (this.viewer) return;

        var id = Ext.getVersion('core').isGreaterThan('4.2.0') ? this.getId()+'-innerCt' : this.getId();
        this.parent = document.getElementById(id);
        this.viewer = document.createElementNS (xhtmlns, 'video');
        this.viewer.setAttribute('controls', '');
        this.viewer.setAttribute('autoplay', '');
        this.viewer.setAttribute('loop', '');
        //this.viewer.id="imgviewer_image";
        //this.viewer.className = "image_viewer_display";

        // create menu
        this.createViewMenu();

        // init plug-ins
        var plugin = undefined;
        for (var i=0; (plugin=this.plug_ins[i]); i++)
            plugin.init();

        this.viewer.setAttribute('poster', this.constructPreviewUrl());

        // dima: image service is serving bad h264 right now
        //this.sourceH264 = document.createElementNS (xhtmlns, 'source');
        //this.sourceH264.setAttribute('src', this.constructMovieUrl('h264'));
        //this.sourceH264.setAttribute('type', 'video/mp4');
        //this.viewer.appendChild(this.sourceH264);

        this.sourceWEBM = document.createElementNS (xhtmlns, 'source');
        this.sourceWEBM.setAttribute('src', this.constructMovieUrl('webm'));
        this.sourceWEBM.setAttribute('type', 'video/webm;codecs="vp8, vorbis"');
        this.viewer.appendChild(this.sourceWEBM);

        this.parent.appendChild(this.viewer);

        this.fireEvent( 'loaded', this );
    },

    constructUrl: function(opts) {
        var command = [];
        var plugin = undefined;
        for (var i=0; (plugin=this.plug_ins[i]); i++)
            plugin.addCommand(command, opts);
        return '/image_service/image/'+this.resource.resource_uniq+'?'+command.join('&');
    },

    constructMovieUrl: function(format) {
        return this.constructUrl({
            format: format,
        });
    },

    constructPreviewUrl: function() {
        return this.constructUrl({
            format: 'jpeg',
            z: 1,
            t: 1,
        });
    },

    export: function (format) {
        window.open( this.constructMovieUrl(format) );
    },

    doUpdate: function () {
        this.update_needed = undefined;
        // dima: image service is serving bad h264 right now
        this.viewer.src = this.constructMovieUrl('webm');

        //this.sourceH264.setAttribute('src', this.constructMovieUrl('h264'));
        //this.sourceWEBM.setAttribute('src', this.constructMovieUrl('webm'));
    },

    needs_update: function () {
        this.requires_update = undefined;
        if (this.update_needed)
            clearTimeout(this.update_needed);
        this.update_needed = setTimeout(callback(this, this.doUpdate), this.update_delay_ms);
    },

    onloaded : function() {
        this.setLoading(false);
    },

    onworking : function(message) {
        if (this.hasListeners.working)
            this.fireEvent( 'working', message );
        else
            this.setLoading(message);
    },

    ondone : function() {
        this.setLoading(false);
        this.fireEvent( 'done', this );
    },

    onerror : function(error) {
        this.setLoading(false);
        if (this.hasListeners.error)
            this.fireEvent( 'error', error );
        else
            BQ.ui.error(error.message_short);
    },

    //----------------------------------------------------------------------
    // view menu
    //----------------------------------------------------------------------

    createCombo : function (label, items, def, scope, cb, id) {
        var options = Ext.create('Ext.data.Store', {
            fields: ['value', 'text'],
            data : items
        });
        var combo = this.menu.add({
            xtype: 'combobox',
            itemId: id ? id : undefined,
            width: 380,
            fieldLabel: label,
            store: options,
            queryMode: 'local',
            displayField: 'text',
            valueField: 'value',
            forceSelection: true,
            editable: false,
            value: def,
            listeners:{
                scope: scope,
                'select': cb,
            },
        });
        return combo;
    },

    createViewMenu: function() {
        if (!this.menubutton) {
            this.menubutton = document.createElement('span');

            // temp fix to work similar to panojs3, will be updated to media queries
            if (isClientTouch())
                this.menubutton.className = 'viewoptions touch';
            else if (isClientPhone())
                this.menubutton.className = 'viewoptions phone';
            else
                this.menubutton.className = 'viewoptions';
            this.parent.appendChild(this.menubutton);
        }

        if (!this.menu) {
            this.menu = Ext.create('Ext.tip.ToolTip', {
                target: this.menubutton,
                anchor: 'top',
                anchorToTarget: true,
                cls: 'bq-viewer-menu',
                maxWidth: 460,
                anchorOffset: -10,
                autoHide: false,
                shadow: false,
                closable: true,
                layout: {
                    type: 'vbox',
                    //align: 'stretch',
                },
                defaults: {
                    labelSeparator: '',
                    labelWidth: 200,
                },
            });
            var el = Ext.get(this.menubutton);
            el.on('click', this.onMenuClick, this);
        }
    },

    onMenuClick: function (e, btn) {
        e.preventDefault();
        e.stopPropagation();
        if (this.menu.isVisible())
            this.menu.hide();
        else
            this.menu.show();
    },

});

//--------------------------------------------------------------------------------------
// BQ.viewer.Movie.Dialog
//--------------------------------------------------------------------------------------

Ext.define('BQ.viewer.Movie.Dialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.bq_movie_dialog',
    border: 0,
    layout: 'fit',
    modal : true,
    border : false,
    width : '85%',
    height : '85%',
    buttonAlign: 'center',
    autoScroll: true,
    title: 'Movie',

    constructor : function(config) {
        config = config || {};
        Ext.apply(this, {
            title: 'Movie for ' + config.resource.name,
            buttons: [{
                text: 'Done',
                scale: 'large',
                scope: this,
                handler: this.close,
            }],
            items: [{
                xtype: 'bq_movie_viewer',
                itemId: 'viewer_movie',
                border: 0,
                resource: config.resource,
            }],
        }, config);

        this.callParent(arguments);
        this.show();
    },

});

//--------------------------------------------------------------------------------------
// Plug-ins - base
//--------------------------------------------------------------------------------------

function PlayerPlugin (player) {
    this.player = player;
};

PlayerPlugin.prototype.init = function () {
};

PlayerPlugin.prototype.addCommand = function (command, pars) {
};

PlayerPlugin.prototype.changed = function () {
  if (!this.update_check || (this.update_check && this.update_check.checked) )
    this.player.needs_update();
};

//--------------------------------------------------------------------------------------
// Plug-ins - slice
//--------------------------------------------------------------------------------------

function PlayerSlice (player) {
    this.base = PlayerPlugin;
    this.base (player);

    // do stuff
};
PlayerSlice.prototype = new PlayerPlugin();

PlayerSlice.prototype.init = function () {
    if (this.menu) return;
    var z = parseInt(this.player.dims.z);
    var t = parseInt(this.player.dims.t);
    if (z<=1 || t<=1) return;
    this.menu = this.player.menu;

    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'Projection',
        cls: 'heading',
    });

    var def_depth = Math.ceil(z/2);
    var depth = [{'value': 0, 'text':'All'}];
    for (var i=1; i<=z; i++)
        depth.push({'value': i, 'text':i});
    this.combo_depth = this.player.createCombo( 'Depth', depth, def_depth, this, this.onDepth, 'combo_depth');

    var time = [{'value': 0, 'text':'All'}];
    for (var i=1; i<=t; i++)
        time.push({'value': i, 'text':i});
    this.combo_time = this.player.createCombo( 'Time', time, 0, this, this.onTime, 'combo_time');
};

PlayerSlice.prototype.onTime = function () {
    var nz = parseInt(this.player.dims.z);
    var nt = parseInt(this.player.dims.t);
    var t = this.combo_time.getValue();
    var z = this.combo_depth.getValue();
    if (t>0) {
        if (z!==0)
            this.combo_depth.setValue(0);
        this.changed();
    } else {
        if (z===0)
            this.combo_depth.setValue(Math.ceil(nz/2));
        this.changed();
    }
},

PlayerSlice.prototype.onDepth = function () {
    var nz = parseInt(this.player.dims.z);
    var nt = parseInt(this.player.dims.t);
    var t = this.combo_time.getValue();
    var z = this.combo_depth.getValue();
    if (z>0) {
        if (t!==0)
            this.combo_time.setValue(0);
        this.changed();
    } else {
        if (t===0)
            this.combo_time.setValue(Math.ceil(nt/2));
        this.changed();
    }
},

PlayerSlice.prototype.addCommand = function (command, pars) {
    if (pars.t && pars.z) {
        command.push('slice=,,'+pars.z+','+pars.t);
        return;
    }
    if (!this.menu) return;
    var z = this.combo_depth.getValue();
    var t = this.combo_time.getValue();
    command.push('slice=,,'+(z>0?z:'')+','+(t>0?t:''));
};

//--------------------------------------------------------------------------------------
// Plug-ins - size
//--------------------------------------------------------------------------------------

function PlayerSize (player) {
    this.base = PlayerPlugin;
    this.base (player);

    this.resolutions = {
        'SD':    {w: 720, h: 480, },
        'HD720': {w: 1280, h: 720, },
        'HD':    {w: 1920, h: 1080, },
        '4K':    {w: 3840, h: 2160, },
    };
};
PlayerSize.prototype = new PlayerPlugin();

PlayerSize.prototype.init = function () {
    var p = this.player.preferences || {};
    this.def = {
        videoResolution  : p.videoResolution  || 'HD', // values: 'SD', 'HD720', 'HD', '4K'
    };
    if (!this.menu)
        this.createMenu();
};

PlayerSize.prototype.addCommand = function (command, pars) {
    var r = this.resolutions[this.combo_resolution.getValue()];
    command.push('resize='+r.w+','+r.h+',BC,MX');
};

PlayerSize.prototype.createMenu = function () {
    if (this.menu) return;
    this.menu = this.player.menu;

    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'Video',
        cls: 'heading',
    });
    this.combo_resolution = this.player.createCombo( 'Video Resolution', [
        {"value":"SD",    "text":"SD (720x480)"},
        {"value":"HD720", "text":"HD 720p (1280x720)"},
        {"value":"HD",    "text":"HD 1080p (1920x1080)"},
        {"value":"4K",    "text":"4K (3840x2160)"}
    ], this.def.videoResolution, this, this.changed, 'combo_resolution');

};

//--------------------------------------------------------------------------------------
// Plug-ins - display
//--------------------------------------------------------------------------------------

function PlayerDisplay (player) {
    this.base = PlayerPlugin;
    this.base (player);
};
PlayerDisplay.prototype = new PlayerPlugin();

PlayerDisplay.prototype.init = function () {
    var p = this.player.preferences || {};
    this.def = {
        enhancement      : p.enhancement     || 'd', // values: 'd', 'f', 't', 'e'
        enhancement_8bit : p.enhancement8bit || 'f',
        negative         : p.negative        || '',  // values: '', 'negative'
        fusion           : p.fusion          || 'm', // values: 'a', 'm'
        rotate           : p.rotate          || 0,   // values: 0, 270, 90, 180
        autoupdate       : false,
    };
    if (!this.menu)
        this.createMenu();
};

PlayerDisplay.prototype.addCommand = function (command, pars) {
    command.push ('remap=display');
    if (!this.menu) return;

    command.push ('depth=8,' + this.combo_enhancement.getValue());

    var b = this.menu.queryById('slider_brightness').getValue();
    var c = this.menu.queryById('slider_contrast').getValue();
    if (b!==0 || c!==0)
        command.push('brightnesscontrast='+b+','+c);

    var fusion='';
    for (var i=0; i<this.channel_colors.length; i++) {
        fusion += this.channel_colors[i].getRed() + ',';
        fusion += this.channel_colors[i].getGreen() + ',';
        fusion += this.channel_colors[i].getBlue() + ';';
    }
    fusion += ':'+this.combo_fusion.getValue();
    command.push('fuse='+fusion);

    var ang = this.combo_rotation.getValue();
    if (ang && ang!==''&& ang!==0)
        command.push ('rotate=' + ang);

    if (this.combo_negative.getValue()) {
        command.push(this.combo_negative.getValue());
    }
};

PlayerDisplay.prototype.createMenu = function () {
    if (this.menu) return;

    this.menu = this.player.menu;

    this.createChannelMap( );

    var enhancement = this.player.phys && parseInt(this.player.phys.pixel_depth)===8 ? this.def.enhancement_8bit : this.def.enhancement;
    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'View',
        cls: 'heading',
    });

    this.menu.add({
        xtype: 'slider',
        itemId: 'slider_brightness',
        fieldLabel: 'Brightness',
        width: 400,
        value: 0,
        increment: 1,
        minValue: -100,
        maxValue: 100,
        listeners: {
            scope: this,
            change: this.changed,
        },
    });

    this.menu.add({
        xtype: 'slider',
        itemId: 'slider_contrast',
        fieldLabel: 'Contrast',
        width: 400,
        value: 0,
        increment: 1,
        minValue: -100,
        maxValue: 100,
        zeroBasedSnapping: true,
        listeners: {
            scope: this,
            change: this.changed,
        },
    });

    this.combo_fusion = this.player.createCombo( 'Fusion', [
        {"value":"a", "text":"Average"},
        {"value":"m", "text":"Maximum"},
    ], this.def.fusion, this, this.changed);

    this.combo_enhancement = this.player.createCombo( 'Enhancement', [
        {"value":"d", "text":"Data range"},
        {"value":"f", "text":"Full range"},
        {"value":"t", "text":"Data + tolerance"},
        {"value":"e", "text":"Equalized"}
    ], enhancement, this, this.changed);

    this.combo_negative = this.player.createCombo( 'Negative', [
        {"value":"", "text":"No"},
        {"value":"negative", "text":"Negative"},
    ], this.def.negative, this, this.changed);

    this.combo_rotation = this.player.createCombo( 'Rotation', [
        {"value":0, "text":"No"},
        {"value":90, "text":"Right 90deg"},
        {"value":-90, "text":"Left 90deg"},
        {"value":180, "text":"180deg"},
    ], this.def.rotate, this, this.changed);

};

PlayerDisplay.prototype.createChannelMap = function() {
    var channel_count = parseInt(this.player.dims.ch);
    var phys = this.player.phys;

    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'Channels',
        cls: 'heading',
    });

    this.channel_colors = phys.channel_colors;
    for (var ch=0; ch<channel_count; ch++) {
        this.menu.add({
            xtype: 'colorfield',
            fieldLabel: ''+phys.channel_names[ch],
            name: 'channel_color_'+ch,
            channel: ch,
            value: this.channel_colors[ch].toString().replace('#', ''),
            listeners: {
                scope: this,
                change: function(field, value) {
                    this.channel_colors[field.channel] = Ext.draw.Color.fromString('#'+value);
                    this.changed();
                },
            },
        });
    }
};


//--------------------------------------------------------------------------------------
// Plug-ins - format
//--------------------------------------------------------------------------------------

function PlayerFormat (player) {
    this.base = PlayerPlugin;
    this.base (player);
};
PlayerFormat.prototype = new PlayerPlugin();

PlayerFormat.prototype.init = function () {
    if (this.menu) return;
    this.menu = this.player.menu;

    var z = parseInt(this.player.dims.z);
    var t = parseInt(this.player.dims.t);
    var pages = t * z;

    var fps = 30;
    if (pages < 700) fps = 15;
    if (pages < 450) fps = 12;
    if (pages < 225) fps = 6;
    //if (pages < 100) fps = 3;
    //if (pages < 50) fps = 1;

    var index = this.menu.items.findIndex( 'itemId', 'combo_resolution' );
    this.menu.insert(index+1, {
        xtype: 'numberfield',
        itemId: 'frames_per_second',
        fieldLabel: 'Frames per second',
        name: 'frames_per_second',
        value: fps,
        maxValue: 60,
        minValue: 1,
        listeners: {
            scope: this,
            change: this.changed,
        },
    });
};

PlayerFormat.prototype.addCommand = function (command, pars) {
    var fps = this.menu.queryById('frames_per_second').getValue();
    var format = pars.format || 'h264';
    if (format==='jpeg')
        command.push('format=jpeg');
    else
        command.push('format='+format+',fps,'+fps);
};

