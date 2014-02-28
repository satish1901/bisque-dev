/*******************************************************************************
  ExtJS wrapper for the Bisque image viewer
  Author: Dima Fedorov <dima@dimin.net>

  Configurations:
      resource   - url string or bqimage
      user       - url string
      parameters - viewer configuration object describied later

  Events:
      loaded     - event fired when the viewer is loaded
      changed    - event fired when the gobjects in the viewer have changed
      working
      done
      error

  Parameters:
    simpleviewer   - sets a minimal set of plug-ins and also read-only view for gobjects
    onlyedit       - only sets plug-in needed for editing of gobjects

    nogobects      - disable loading gobjects by default
    gobjects       - load gobjects from the givel URL, 'gobjects':'http://gobejcts_url' or a BQGobject or a vector of BQGObject

    noedit         - read-only view for gobjects
      alwaysedit     - instantiates editor right away and disables hiding it
      nosave         - disables saving gobjects
      editprimitives - only load edit for given primitives, 'editprimitives':'point,polyline'
                       can be one of: 'Point,Rectangle,Polyline,Polygon,Circle'

    blockforsaves  - set to true to show saving of gobjects, def: true


  Example:
    var myviewer = Ext.create('BQ.viewer.Image', {
        resource: 'http://image_url',
        user: 'user_name',
        parameters: {
            'gobjects': 'http://gobejcts_url',
            'noedit': '',
        },
    });
*******************************************************************************/

Ext.define('BQ.viewer.Movie', {
    alias: 'widget.bq_movie_viewer',
    extend: 'Ext.container.Container',
    border: 0,
    cls: 'bq-viewer-movie',

    update_delay_ms: 50,  // Update the viewer asynchronously

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

        var source = document.createElementNS (xhtmlns, 'source');
        source.setAttribute('src', this.constructMovieUrl('h264'));
        source.setAttribute('type', 'video/mp4');
        source.setAttribute('src', this.constructMovieUrl('webm'));
        source.setAttribute('type', 'video/webm;codecs="vp8, vorbis"');

        this.viewer.appendChild(source);
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

    onloaded : function() {
        this.setLoading(false);
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

    doUpdate: function () {
        this.update_needed = undefined;
        this.viewer.src = this.constructMovieUrl('webm');
        //var source = document.createElementNS (xhtmlns, 'source');
        //source.setAttribute('src', this.constructMovieUrl('h264'));
        //source.setAttribute('type', 'video/mp4');
        //source.setAttribute('src', this.constructMovieUrl('webm'));
        //source.setAttribute('type', 'video/webm;codecs="vp8, vorbis"');
    },

    needs_update: function () {
        this.requires_update = undefined;
        if (this.update_needed)
            clearTimeout(this.update_needed);
        this.update_needed = setTimeout(callback(this, this.doUpdate), this.update_delay_ms);
    },

    //----------------------------------------------------------------------
    // view menu
    //----------------------------------------------------------------------

    createCombo : function (label, items, def, scope, cb) {
        var options = Ext.create('Ext.data.Store', {
            fields: ['value', 'text'],
            data : items
        });
        var combo = this.menu.add({
            xtype: 'combobox',
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
};

PlayerSlice.prototype.addCommand = function (command, pars) {
    if (pars.t || pars.z)
        command.push('slice=,,'+pars.z+','+pars.t);
};

//--------------------------------------------------------------------------------------
// Plug-ins - size
//--------------------------------------------------------------------------------------

function PlayerSize (player) {
    this.base = PlayerPlugin;
    this.base (player);

    // do stuff
};
PlayerSize.prototype = new PlayerPlugin();

PlayerSize.prototype.init = function () {
    this.width = 1920;
    this.height = 1080;
};

PlayerSize.prototype.addCommand = function (command, pars) {
    command.push('resize='+this.width+','+this.height+',BC,MX');
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

    /*
    var r = this.menu_elements['Red'].value;
    var g = this.menu_elements['Green'].value;
    var b = this.menu_elements['Blue'].value;
    view.addParams  ('remap='+r+','+g+','+b);
    */

    var fusion='';
    for (var i=0; i<this.channel_colors.length; i++) {
        fusion += this.channel_colors[i].getRed() + ',';
        fusion += this.channel_colors[i].getGreen() + ',';
        fusion += this.channel_colors[i].getBlue() + ';';
    }
    fusion += ':'+this.combo_fusion.getValue();
    command.push('fuse='+fusion);

/*
        cb = this.menu_elements['Rotate'];
        if (cb.value != 0)
            view.addParams  ('rotate=' + cb.value);
        cb.disabled=true; // no rotation for now
        view.rotateTo( parseInt(cb.value) );
*/

    if (this.combo_negative.getValue()) {
        command.push(this.combo_negative.getValue());
    }
};

PlayerDisplay.prototype.doUpdate = function () {
    this.player.needs_update();
};

PlayerDisplay.prototype.changed = function () {
  if (!this.update_check || (this.update_check && this.update_check.checked) )
    this.player.needs_update();
};

PlayerDisplay.prototype.createMenu = function () {
    if (this.menu) return;

    this.menu = this.player.menu;

    this.createChannelMap( );

    var enhancement = this.player.phys && this.player.phys.pixel_depth===8 ? this.def.enhancement_8bit : this.def.enhancement;
    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'View',
        cls: 'heading',
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
        cc = {
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
        };
        this.menu.add(cc);
    }
};


//--------------------------------------------------------------------------------------
// Plug-ins - format
//--------------------------------------------------------------------------------------

function PlayerFormat (player) {
    this.base = PlayerPlugin;
    this.base (player);

    this.fps = 6;
};
PlayerFormat.prototype = new PlayerPlugin();

PlayerFormat.prototype.init = function () {
};

PlayerFormat.prototype.addCommand = function (command, pars) {
    var format = pars.format || 'h264';
    if (format==='jpeg')
        command.push('format=jpeg');
    else
        command.push('format='+format+',fps,'+this.fps);
};

