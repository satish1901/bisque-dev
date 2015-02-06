function ImgOperations (viewer, name) {
    var p = viewer.parameters || {};
    this.default_enhancement      = p.enhancement     || 'd'; // values: 'd', 'f', 't', 'e'
    this.default_enhancement_8bit = p.enhancement8bit || 'f';
    this.default_negative         = p.negative        || '';  // values: '', 'negative'
    this.default_fusion           = p.fusion          || 'm'; // values: 'a', 'm'
    this.default_fusion_4plus     = p.default_fusion_4plus || 'm';
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
        var enh = this.combo_enhancement.getValue();
        this.params.enhancement = enh;
        if (enh.indexOf('hounsfield') != 0) {
            view.addParams  ('depth=8,' + this.combo_enhancement.getValue() + ',u');
        } else {
            var a = enh.split(':');
            view.addParams  ('depth=8,hounsfield,u,,'+a[1]);
        }

        /*
        var b = this.menu.queryById('slider_brightness').getValue();
        var c = this.menu.queryById('slider_contrast').getValue();
        if (b!==0 || c!==0)
            view.addParams  ('brightnesscontrast='+b+','+c);
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

    var phys = this.viewer.imagephys;
    var enhancement = phys && parseInt(phys.pixel_depth)===8 ? this.default_enhancement_8bit : this.default_enhancement;

    var fusion = phys && parseInt(phys.ch)>3 ? this.default_fusion_4plus : this.default_fusion;

    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'View',
        cls: 'heading',
    });

    /*this.menu.add({
        xtype: 'slider',
        itemId: 'slider_brightness',
        fieldLabel: 'Brightness',
        width: 400,
        value: 0,
        minValue: -100,
        maxValue: 100,
        increment: 10,
        zeroBasedSnapping: true,
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
        minValue: -100,
        maxValue: 100,
        increment: 10,
        zeroBasedSnapping: true,
        zeroBasedSnapping: true,
        listeners: {
            scope: this,
            change: this.changed,
        },
    });*/

    this.combo_fusion = this.viewer.createCombo( 'Fusion', [
        {"value":"a", "text":"Average"},
        {"value":"m", "text":"Maximum"},
    ], fusion, this, this.changed);

    var enhancement_options = [
        {"value":"d", "text":"Data range"},
        {"value":"f", "text":"Full range"},
        {"value":"t", "text":"Data + tolerance"},
        {"value":"e", "text":"Equalized"},
    ];
    if (phys.dicom && (phys.dicom.modality == 'CT' || phys.dicom.wnd_center)) {
        var prefferred = ''+phys.dicom.wnd_center+','+phys.dicom.wnd_width;
        // preferred may be lists

        dicom_options = [
            { value:"hounsfield:"+prefferred, text: "CT: Preferred ("+prefferred+")" },        
            { value:"hounsfield:40,80", text: "CT: Head Soft Tissue (40/80)" },
            { value:"hounsfield:30,110", text: "CT: Brain (30/110)" },
            { value:"hounsfield:60,300", text: "CT: Neck Soft Tissue (60/300)" },
            { value:"hounsfield:400,2000", text: "CT: Bone (400/2000)" },
            { value:"hounsfield:400,4000", text: "CT: Temporal bones (400/4000)" },
            { value:"hounsfield:350,2500", text: "CT: Bone body (350/2500)" },
            { value:"hounsfield:40,500", text: "CT: Soft Tissue (40/500)" },
            { value:"hounsfield:40,400", text: "CT: Soft Tissue, pediatric (40/400)" },
            { value:"hounsfield:400,1800", text: "CT: Mediastinum (400/1800)" },
            { value:"hounsfield:-180,2600", text: "CT: Bronchial (-180/2600)" },
            { value:"hounsfield:-350,2000", text: "CT: Lung (-350/2000)" },
            { value:"hounsfield:-700,1200", text: "CT: Lung (-700/1200)" },
            { value:"hounsfield:-20,400", text: "CT: Abdomen (-20/400)" },
            { value:"hounsfield:60,180", text: "CT: Liver (60/180)" },
            { value:"hounsfield:40,150", text: "CT: Liver without contrast (40/150)" },
            { value:"hounsfield:100,150", text: "CT: Liver with contrast (100/150)" },
            { value:"hounsfield:30,180", text: "CT: P Fossa (30/180)" },
            { value:"hounsfield:40,250", text: "CT: Cervical spine without contrast (40/250)" },
            { value:"hounsfield:40,500", text: "CT: Thoracic and Lumbar spine (40/500)" },
            { value:"hounsfield:40,60", text: "CT: Infarct (40/60)" },
            { value:"hounsfield:200,700", text: "CT: OBLIQUE MIP (200/700)" },
            { value:"hounsfield:60,650", text: "CT: MYELOGRAM W/L (60/650)" },
        ];
        enhancement = "hounsfield:"+prefferred;
        enhancement_options.push.apply(enhancement_options, dicom_options);
    }
    this.combo_enhancement = this.viewer.createCombo( 'Enhancement', enhancement_options, enhancement, this, this.changed, 300);

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
        this.menu.add({
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
        });
    }
};

ImgOperations.prototype.loadPreferences = function (p) {
    this.default_autoupdate  = 'autoUpdate'  in p ? p.autoUpdate  : this.default_autoupdate;
    this.default_negative    = 'negative'    in p ? p.negative    : this.default_negative;
    this.default_enhancement = 'enhancement' in p ? p.enhancement : this.default_enhancement;
    this.default_rotate      = 'rotate'      in p ? p.rotate      : this.default_rotate;
    this.default_fusion      = 'fusion'      in p ? p.fusion      : this.default_fusion;
    this.default_enhancement_8bit = 'enhancement-8bit' in p ? p['enhancement-8bit'] : this.default_enhancement_8bit;
    this.default_fusion_4plus = 'fusion_4plus' in p ? p['fusion_4plus'] : this.default_fusion_4plus;
};

