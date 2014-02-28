function ImgOperations (viewer, name) {
    var p = viewer.parameters || {};
    this.default_enhancement      = p.enhancement     || 'd'; // values: 'd', 'f', 't', 'e'
    this.default_enhancement_8bit = p.enhancement8bit || 'f';
    this.default_negative         = p.negative        || '';  // values: '', 'negative'
    this.default_fusion           = p.fusion          || 'm'; // values: 'a', 'm'
    this.default_rotate           = p.rotate          || 0;   // values: 0, 270, 90, 180
    this.default_autoupdate       = false;

    this.base = ViewerPlugin;
    this.base (viewer, name);
}
ImgOperations.prototype = new ViewerPlugin();

ImgOperations.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
};

ImgOperations.prototype.newImage = function () {
    this.phys_inited = false;
};

ImgOperations.prototype.updateImage = function () {

};

ImgOperations.prototype.getParams = function () {
    return this.params || {};
};

ImgOperations.prototype.updateView = function (view) {
    if (!this.menu) this.createMenu();
    if (this.menu) {
        this.params = {};
        this.params.enhancement = this.combo_enhancement.getValue();
        view.addParams  ('depth=8,' + this.combo_enhancement.getValue());

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
        view.addParams  ('fuse='+fusion);

/*
        cb = this.menu_elements['Rotate'];
        if (cb.value != 0)
            view.addParams  ('rotate=' + cb.value);
        cb.disabled=true; // no rotation for now
        view.rotateTo( parseInt(cb.value) );
*/

        if (this.combo_negative.getValue()) {
            this.params.negative = this.combo_negative.getValue();
            view.addParams(this.combo_negative.getValue());
        }
    }
};

ImgOperations.prototype.doUpdate = function () {
    this.viewer.need_update();
};

ImgOperations.prototype.changed = function () {
  if (!this.update_check || (this.update_check && this.update_check.checked) )
    this.viewer.need_update();
};

ImgOperations.prototype.createMenu = function () {
    if (this.menu) return;

    this.menu = this.viewer.createViewMenu();
    var surf = this.viewer.viewer_controls_surface ? this.viewer.viewer_controls_surface : this.parent;
    surf.appendChild(this.viewer.menubutton);

    this.loadPreferences(this.viewer.preferences);



    var dim = this.viewer.imagedim;

    this.createChannelMap( );


    var enhancement = this.default_enhancement;
    var view_title = 'View';
    if (this.viewer.imagephys) {
        //view_title = 'View ['+this.viewer.imagephys.pixel_depth+'bit p/ channel]';
        if (this.viewer.imagephys.pixel_depth == 8)
            enhancement = this.default_enhancement_8bit;
    }


    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: view_title,
        cls: 'heading',
    });
    this.combo_fusion = this.viewer.createCombo( 'Fusion', [
        {"value":"a", "text":"Average"},
        {"value":"m", "text":"Maximum"},
    ], this.default_fusion, this, this.changed);

    this.combo_enhancement = this.viewer.createCombo( 'Enhancement', [
        {"value":"d", "text":"Data range"},
        {"value":"f", "text":"Full range"},
        {"value":"t", "text":"Data + tolerance"},
        {"value":"e", "text":"Equalized"}
    ], enhancement, this, this.changed);

    this.combo_negative = this.viewer.createCombo( 'Negative', [
        {"value":"", "text":"No"},
        {"value":"negative", "text":"Negative"},
    ], this.default_negative, this, this.changed);
};

ImgOperations.prototype.createChannelMap = function ( ) {
    var channel_count = parseInt(this.viewer.current_view.imagedim.ch);
    var imgphys = this.viewer.imagephys;

    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'Channels',
        cls: 'heading',
    });

    this.channel_colors = imgphys.channel_colors;
    for (var ch=0; ch<channel_count; ch++) {
        cc = {
            xtype: 'colorfield',
            fieldLabel: ''+imgphys.channel_names[ch],
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

ImgOperations.prototype.loadPreferences = function (p) {
    this.default_autoupdate  = 'autoUpdate'  in p ? p.autoUpdate  : this.default_autoupdate;
    this.default_negative    = 'negative'    in p ? p.negative    : this.default_negative;
    this.default_enhancement = 'enhancement' in p ? p.enhancement : this.default_enhancement;
    this.default_rotate      = 'rotate'      in p ? p.rotate      : this.default_rotate;
    this.default_fusion      = 'fusion'      in p ? p.fusion      : this.default_fusion;
    this.default_enhancement_8bit = 'enhancement-8bit' in p ? p['enhancement-8bit'] : this.default_enhancement_8bit;
};

