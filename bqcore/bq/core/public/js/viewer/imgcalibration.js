Ext.define('BQ.Calibration.StackCount', {
    extend: 'Ext.form.NumberField',
    dimension: 'z',
    minValue: 0,
    margins: '10px',
    originalMetaDoc: undefined,
    initComponent: function(config) {
        var me = this;
        var config = config || {};
        Ext.apply(me, {
            fieldLabel: this.dimension.toUpperCase()+' Count',
            dimsXpath: '//tag[@name="image_num_'+this.dimension.toLowerCase()+'"]',
        });
        this.callParent([config]);
    },
    setValues: function(xmlDoc) {
        var value = xmlDoc.evaluate(this.dimsXpath+'/@value', xmlDoc, null, XPathResult.NUMBER_TYPE, null).numberValue;
        this.originalMetaDoc = xmlDoc; //save document
        if (value) { //set value
            this.setValue(value);
        } else { //set zero
            this.setValue(0);
        }
    },
    fromXmlNode: function(imageMeta) {
        //check to see if tag exists
        if (this.value==0) {
            var oldValue = this.originalMetaDoc.evaluate(this.dimsXpath+'/@value', this.originalMetaDoc, null, XPathResult.NUMBER_TYPE, null).numberValue;
            if (oldValue!=this.value) {
                if (imageMeta) { //if no image meta make new node
                    var uri = imageMeta.evaluate(this.dimsXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
                    if (uri) { //assign to old value
                        return '<tag name="image_num_'+this.dimension.toLowerCase()+'" type="number" value="'+this.value+'" uri="'+uri+'"/>';
                    } else { // create a new one
                        return '<tag name="image_num_'+this.dimension.toLowerCase()+'" type="number" value="'+this.value+'"/>';
                    }
                } else { // create a new one
                    return '<tag name="image_num_'+this.dimension.toLowerCase()+'" type="number" value="'+this.value+'"/>';
                }
            }
        } /*else { //delete resource if exists
            var uri = imageMeta.evaluate(this.dimsXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
            if (uri) {
                delete_queue.push(uri);
                
                Ext.Ajax.request({
                    method: 'DELETE',
                    headers: { 'Content-Type': 'text/xml' },
                    url: uri,
                    success: function(response) {
                        BQ.ui.notification('Removed image_num_'+this.dimension.toLowerCase());
                    },
                    failure: function(response) {
                        BQ.ui.error('Failed to delete Image Meta Tag!');
                    },
                    scope: this,
                });
                                
            }
        }*/
        return '';
    }
});

Ext.define('BQ.Calibration.ChannelOrder', {
    extend: 'Ext.form.Text',
    fieldLabel: 'Dimension Order',
    originalMetaDoc: undefined,
    initComponent: function(config) {
        var me = this;
        var config = config || {};
        Ext.apply(me, {
            dimsXpath: '//tag[@name="dimension"]',
        }); 
        this.callParent([config]);
    },
    setValues: function(xmlDoc) {
        var value = xmlDoc.evaluate(this.dimsXpath+'/@value', xmlDoc, null, XPathResult.STRING_TYPE, null).stringValue;
        this.originalMetaDoc = xmlDoc; //save document
        if (value) { //set value
            this.setValue(value);
        } else { //set default
            this.setValue('');
        }
    },
    fromXmlNode: function(imageMeta) {
        //check to see if tag exists
        if (this.value) {
            var oldValue = this.originalMetaDoc.evaluate(this.dimsXpath+'/@value', this.originalMetaDoc, null, XPathResult.NUMBER_TYPE, null).numberValue;
            if (oldValue!=this.value) {
                if (imageMeta) { //if no image meta make new node
                    var uri = imageMeta.evaluate(this.dimsXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
                    if (uri) { //assign to old value
                        return '<tag name="dimension" value="'+this.value+'" uri="'+uri+'"/>';
                    } else { // create a new one
                        return '<tag name="dimension" value="'+this.value+'"/>';
                    }
                } else { // create a new one
                    return '<tag name="dimension" value="'+this.value+'"/>';
                }
            }
        }
        return ''; 
    }
    
})

Ext.define('BQ.Calibration.PixelResolution', {
    extend: 'Ext.form.Panel',
    dimension: 'x',
    width: '100%',
    border: false,
    layout: {
        type: 'hbox',
        //pack: 'center',
    },
    initComponent: function(config) {
        var me = this;
        var config = config || {};
        var items = [];
        items.push({
            text: 'Pixel Resolution '+this.dimension,
            xtype: 'label',
            margins: '5px',
        });
        items.push({
            name: 'pixel_resolution_'+this.dimension,
            xtype: 'numberfield',
            decimalPrecision : 6,
            margins: '5px',
        });        
        items.push({
            name: 'pixel_resolution_unit_'+this.dimension,
            xtype:'combobox',
            store: Object.keys(BQ.api.Phys.units),
            margins: '5px',
        });
        Ext.apply(me, {
            //fieldLabel: this.dimension.toUpperCase()+'-Stack Count',
            resolutionXpath: '//tag[@name="pixel_resolution_'+this.dimension+'"]',
            unitsXpath: '//tag[@name="pixel_resolution_unit_'+this.dimension+'"]',
            bodyStyle: 'margin: "center"',
            items: items,
        }); 
        this.callParent([config]);
    },
    setValues: function(xmlDoc) {
        this.originalMetaDoc = xmlDoc; //save document
        var resolutionValue = xmlDoc.evaluate(this.resolutionXpath+'/@value', xmlDoc, null, XPathResult.NUMBER_TYPE, null).numberValue;
        if (resolutionValue) {
            var resolutionForm = this.getForm().findField('pixel_resolution_'+this.dimension.toLowerCase());
            resolutionForm.setValue(resolutionValue);
        }
        var unitValue = xmlDoc.evaluate(this.unitsXpath+'/@value', xmlDoc, null, XPathResult.STRING_TYPE, null).stringValue;
        if (unitValue) {
            var unitForm = this.getForm().findField('pixel_resolution_unit_'+this.dimension.toLowerCase());
            unitForm.setValue(unitValue);
        }
    },
    fromXmlNode: function(imageMeta) {
        //check to see if tag exists
        var xmlNode = '';
        var unitForm = this.getForm().findField('pixel_resolution_'+this.dimension);
        var value = unitForm.getValue();
        if (value) {
            var oldValue = this.originalMetaDoc.evaluate(this.resolutionXpath+'/@value', this.originalMetaDoc, null, XPathResult.NUMBER_TYPE, null).numberValue;
            if (oldValue!=value) {
                if (imageMeta) { //if no image meta make new node
                    var uri = imageMeta.evaluate(this.resolutionXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
                    if (uri) { //assign to old value
                        xmlNode += '<tag name="pixel_resolution_'+this.dimension.toLowerCase()+'" type="number" value="'+value+'" uri="'+uri+'"/>';
                    } else { // create a new one
                        xmlNode +=  '<tag name="pixel_resolution_'+this.dimension.toLowerCase()+'" type="number" value="'+value+'"/>';
                    }
                } else { // create a new one
                    xmlNode +=  '<tag name="pixel_resolution_'+this.dimension.toLowerCase()+'" type="number" value="'+value+'"/>';
                }
            }
        }
        var unitForm = this.getForm().findField('pixel_resolution_unit_'+this.dimension);
        var value = unitForm.getValue();
        if (value) {
            var oldValue = this.originalMetaDoc.evaluate(this.unitsXpath+'/@value', this.originalMetaDoc, null, XPathResult.STRING_TYPE, null).stringValue;
            if (oldValue!=value) {
                if (imageMeta) { //if no image meta make new node
                    var uri = imageMeta.evaluate(this.unitsXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
                    if (uri) { //assign to old value
                        xmlNode += '<tag name="pixel_resolution_unit_'+this.dimension.toLowerCase()+'" value="'+value+'" uri="'+uri+'"/>';
                    } else { // create a new one
                        xmlNode +=  '<tag name="pixel_resolution_unit_'+this.dimension.toLowerCase()+'" value="'+value+'"/>';
                    }
                } else { // create a new one
                    xmlNode +=  '<tag name="pixel_resolution_unit_'+this.dimension.toLowerCase()+'" value="'+value+'"/>';
                }
            }
        }
        return xmlNode; 
    }
});

Ext.define('BQ.Calibration.ChannelPanel', {
    extend: 'Ext.form.Panel',
    layout: 'hbox',
    width: '100%',
    channel: 0,
    autoSize: true,
    border: false,
    name: '',
    color: '#000000', //default color
    initComponent: function(config) {
        var me = this;
        var config = config || {};
        var items = [];
        items.push({ //channel number
            text: this.channel,
            xtype: 'label',
            labelAlign: 'right', 
            margins: '8px',
            flex: 1,
            style: {
                textAlign: 'center',
            }
            //width: '20%',
        });
        items.push({ //channel name editor
            value: this.name,
            id: 'channel_'+me.channel+'_name',
            xtype: 'textfield',
            margins: '8px',
            //width: '40%',
            flex: 3,
            listeners: {
                scope: this,
                change: function(field, value) {
                    me.name = value;
                },
            },
        });
        items.push({
            xtype:'panel',
            //width:'100%',
            height: '100%',
            flex: 5,
            margin: '0 5 5 0',
            border:false,
            items:[{
                //width: '20%',
                //margins: '10px',
                id: 'channel_color_'+me.channel,
                xtype: 'colorfield',
                value: this.color.toString().replace('#', ''),
                
                listeners: {
                    scope: this,
                    change: function(field, value) {
                        me.color = '#'+value;
                    },
                },
            }],
        });
        Ext.apply(me, {
            items: items,
        });
        this.callParent([config]);
    },
    
    setValues: function(xmlDoc) {
        this.originalMetaDoc = xmlDoc; //save document
        if (this.channel != undefined){
            var nameXpath = '//tag[@name="channel_'+this.channel+'_name"]/@value';
            var nameValue = xmlDoc.evaluate(nameXpath, xmlDoc, null, XPathResult.STRING_TYPE, null).stringValue;
            if (nameValue != undefined) { //add name if name found
                this.name = nameValue;
                var channel_name = this.queryById('channel_'+this.channel+'_name')
                channel_name.setValue(this.name)
            }
            var colorXpath = '//tag[@name="channel_color_'+this.channel+'"]/@value';
            var colorValue = xmlDoc.evaluate(colorXpath, xmlDoc, null, XPathResult.STRING_TYPE, null).stringValue;
            if (colorValue) { //add color if color found
                //convert to hex
                var colors = colorValue.match(/(\d*),(\d*),(\d*)/); //return the value only	
                if (colors) {
                    var r = parseInt(colors[1]);
                    var g = parseInt(colors[2]);
                    var b = parseInt(colors[3]);
                    var c = Ext.draw.Color.create(r, g, b);
                }
                
                //set the color
                this.color = c.toString();
                color = this.color.replace('#', '');
                var colorPicker = this.queryById('channel_color_'+this.channel); //color picker is the 3 item, change to look up
                if (colorPicker)
                    colorPicker.onColorSelected(null, color);
            }
        }
        
    },
    
    fromXmlNode: function(imageMeta) {
        var xmlNode = '';
        if (this.name) {
            var nameXpath = '//tag[@name="channel_'+this.channel+'_name"]';
            var oldValue = this.originalMetaDoc.evaluate(nameXpath+'/@value', this.originalMetaDoc, null, XPathResult.STRING_TYPE, null).stringValue;
            if (oldValue!=this.name) {
                if (imageMeta) { //if no image meta make new node
                    var uri = imageMeta.evaluate(nameXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
                    if (uri) { //assign to old value
                        xmlNode += '<tag name="channel_'+this.channel+'_name" value="'+this.name+'" uri="'+uri+'"/>';
                    } else { // create a new one
                        xmlNode +=  '<tag name="channel_'+this.channel+'_name" value="'+this.name+'"/>';
                    }
                } else { // create a new one
                    xmlNode +=  '<tag name="channel_'+this.channel+'_name" value="'+this.name+'"/>';
                }
            }
        }
        if (this.color) {
            var color = Ext.draw.Color.fromString(this.color);
            var color = color.r+','+color.g+','+color.b;
            var colorXpath = '//tag[@name="channel_color_'+this.channel+'"]';
            var oldValue = this.originalMetaDoc.evaluate(colorXpath+'/@value', this.originalMetaDoc, null, XPathResult.STRING_TYPE, null).stringValue;
            if (oldValue!=color) {
                if (imageMeta) { //if no image meta make new node
                    var uri = imageMeta.evaluate(colorXpath+'/@uri', imageMeta, null, XPathResult.STRING_TYPE, null).stringValue;
                    if (uri) { //assign to old value
                        xmlNode += '<tag name="channel_color_'+this.channel+'" value="'+color+'" uri="'+uri+'"/>';
                    } else { // create a new one
                        xmlNode +=  '<tag name="channel_color_'+this.channel+'" value="'+color+'"/>';
                    }
                } else { // create a new one
                    xmlNode +=  '<tag name="channel_color_'+this.channel+'" value="'+color+'"/>';
                }
            }
        }
        return xmlNode
    },
});

Ext.define('BQ.Calibration.ChannelOrganizer', {
    extend: 'Ext.panel.Panel',
    layout: 'vbox',
    channelNum: 0,
    border: false,
    chStore: [],
    autoScroll: true,
    height: '200px',
    width: '80%',
    margin: '10px',
    
    initComponent: function(config) {
        var me = this;
        var config = config || {};
        var items = [];  
        Ext.apply(me, {
            items: items,
        }); 
        this.callParent([config]);
    },
    
    setValues: function(xmlDoc) { //resets the entire panel
        this.originalMetaDoc = xmlDoc; //save document
        this.chStore = []; //resets chStore
        var i;
        while(i = this.items.first()){ //clear old panel
            this.remove(i, true);
        }
        
        this.add({ //title
            width: '100%',
            xtype: 'panel',
            layout: 'hbox',
            border: false,
            items: [{
                xtype: 'label',
                text: 'Number',
                flex: 1,
                style: {
                    textAlign: 'center',
                    fontWeight: 'bold',
                }
            }, {
                xtype: 'label',
                text: 'Name',
                flex: 3,
                style: {
                    textAlign: 'center',
                    fontWeight: 'bold',
                }
            }, {
                xtype: 'label',
                text: 'Color',
                flex: 5,
                style: {
                    textAlign: 'center',
                    fontWeight: 'bold',
                }
            }]
        });
        
        for (var c=0; c<this.channelNum; c++) {
            var channelPanel = Ext.create('BQ.Calibration.ChannelPanel', {
                channel: c.toString(),
            });
            this.add(channelPanel)
            channelPanel.setValues(xmlDoc) 
            this.chStore.push(channelPanel)
        }
        this.doLayout();
    },
    
    fromXmlNode: function(imageMeta) {
        var xmlNode = '';
        for (var c=0; c<this.chStore.length; c++) {
            xmlNode += this.chStore[c].fromXmlNode(imageMeta)
        }
        return xmlNode;        
    },
    
    setChannelNum: function(value, xmlDoc) {
        this.channelNum = value;
        this.setValues(xmlDoc);
    },
});



Ext.define('BQ.viewer.Calibration', {
    extend: 'Ext.window.Window',
    layout: 'hbox',
    title: 'Image Meta Editor',
    bodyStyle: 'background-color:#FFFFFF',
    image_resource: '', //data_service url (ex. '/data_service/($id)')
    //viewer: {}, //required
    buttonAlign: 'center',
    initComponent: function(config) {
        var config = config || {};
        var items = [];
        var me = this;
        
        fbar = [{
            scale: 'large',
            xtype: 'button',
            margin: '0 8 0 8',
            text: 'Apply New MetaData Values',
            handler: me.getImageMetaTag.bind(me, me.updateImageMeta),
        }, {
            scale: 'large',
            margin: '0 8 0 8',
            xtype: 'button',
            text: 'Reset to Default MetaData Values',
            handler: function() {
                //request for image meta
                Ext.Ajax.request({
                    method: 'GET',
                    disableCaching: false,
                    headers: { 'Content-Type': 'text/xml' },
                    url: me.image_resource+'/pixels',
                    params: {meta:''},
                    success: function(response) {
                        var xml = response.responseXML;
                        this.setFormValues(xml);
                    },
                    failure: function(response) {
                        BQ.ui.error('Image Meta failed to be servered for this resource from image service!');
                    },
                    scope: me,
                });      
            },
        }, {
            scale: 'large',
            margin: '0 8 0 8',
            xtype: 'button',
            text: 'Remove All Edited MetaData',
            handler: me.getImageMetaTag.bind(me, me.deleteImageMeta),
        }],        
        
        this.imageMetaForm = Ext.create('Ext.form.Panel', {
            height : '100%',
            width : '50%',
            margin: '10px',
            border: false,
            autoScroll: true,
            formComponents: {},
            items: [],
            layout: {
                //align: 'center',
                type: 'vbox',
                //align: 'stretch',
            },
            defaults: {
                margins: '5 0 5 0',
                type: 'combobox',
            },
            scope: this,
        });

        //request for image meta
        Ext.Ajax.request({
            method: 'GET',
            disableCaching: false,
            headers: { 'Content-Type': 'text/xml' },
            url: this.image_resource+'/pixels',
            params: {meta:''},
            success: function(response) {
                var xml = response.responseXML;
                this.constructImageMetaForm(xml);
            },
            failure: function(response) {
                BQ.ui.error('Image Meta failed to be servered for this resource from image service!');
            },
            scope: this,
        });        
        
        //set the scales of the lines and return the pixel scaling factor
        this.imageCalibForm = Ext.create('Ext.form.Panel', {
            //flex: 2,
            height:'100%',
            width : '50%',
            margin: '10px',
            formComponents: {},
            items: [],
            layout: {
                //align: 'center',
                type: 'vbox',
                //align: 'stretch',
            },
            bodyStyle: {
                borderColor: '#FFFFFF'
            },
            padding: 0,
            border: 0,
            //margin: '10px',
            defaults: {
                margins: '5px',
            },
        });
        
        items.push(this.imageMetaForm);
        items.push(this.imageCalibForm);
        
        Ext.apply(me, {
            fbar: fbar,
            items: items,
        }); 
        this.callParent([config]);
        this.constructImageCalibrationForm()
    },
    
    constructImageCalibrationForm: function() {
        var me = this;
        
        this.imageCalibForm.add({
            xtype: 'box',
            html: '<h2>Image Resolution Calibration</h2><p>A fast an easy way to calibrate pixel resolution when you do not have values.</p>',
            width: '100%',
            cls: 'imgmetaeditor',
            padding: '0px',
            margins:'0px',
        });
        
        this.imageCalibForm.formComponents['reference_length'] = Ext.createWidget('numberfield',{
            fieldLabel: 'Reference Length',
            //xtype: 'numberfield',
            decimalPrecision : 6,
            margin: '10px',
            minValue: 0,           
            listeners: {
                change : function() {
                    me.updateReferenceLength()
                }
            },
        });
        
        this.imageCalibForm.add({
            border: false,
            layout: {
                align: 'middle',
                type: 'hbox',
                //pack: 'justify'
                //pack: 'center',
            },            
            width: '100%',
            padding: '0px',
            margins:'0px',
            items: [
                this.imageCalibForm.formComponents['reference_length'],
                {
                    xtype: 'box',
                    html: '<p> Set the reference length and to a known object length in the image.</p>',
                    //width: '100%',
                    flex: 1,
                    cls: 'imgmetaeditor',
                },
            ],
        });
        
        this.imageCalibForm.add({
            xtype: 'box',
            html: '<p>Select the gobject line in the image viewer and draw a line spanning that distance on the image. Many lines can be added and the estimated pixel resolution will be the average of the provided lines. Select Calibrate Values when a close Estimated Pixel Resolution has been reached. The values will be transfered to the x and y resolution entries.</p>',
            width: '100%',
            cls: 'imgmetaeditor',
            padding: 0,
            margins:'0px',
        });  
        
        this.imageCalibForm.formComponents['est_px_res'] = Ext.createWidget('textfield',{
            fieldLabel: 'Estimated Pixel Resolution',
            margin: '0 70 0 10',
            id: 'est_px_res',
            readOnly: true,
        });
        
        this.imageCalibForm.formComponents['set_px_rex'] = Ext.createWidget('button',{
            //scale: 'large',
            margin: '0 0 0 70',
            text: 'Calibrate Values',
            scale: 'large',
            handler: function() {
                var value =  me.imageCalibForm.formComponents['est_px_res'].getValue()
                if (value) {
                    var xform = me.imageMetaForm.formComponents['pixel_resolution_x'].getForm().findField('pixel_resolution_x'); 
                    var yform = me.imageMetaForm.formComponents['pixel_resolution_y'].getForm().findField('pixel_resolution_y');
                    xform.setValue(value);
                    yform.setValue(value);
                } else {
                    BQ.ui.notification('No Value to Update.');
                }
                
            },
        });
        
        this.imageCalibForm.formComponents['imgViewer'] = this.imageCalibForm.add(
            Ext.create('BQ.viewer.Image',{
                width:'100%',
                flex: 1,
                resource: me.image_resource,               
                parameters: {
                    onlyedit: true,
                    nosave: true,
                    editprimitives: 'Line',
                },
                listeners: {
                    'changed': function() {
                        me.updateReferenceLength()
                    }
                },
            })
        );
        
        this.imageCalibForm.add({
            border: false,
            layout: {
                align: 'middle',
                type: 'hbox',
                //pack: 'justify'
                //pack: 'center',
            },            
            width: '100%',
            items: [
                this.imageCalibForm.formComponents['est_px_res'],
                this.imageCalibForm.formComponents['set_px_rex'],
                //this.imageCalibForm.formComponents['reset_gobs'],
            ],
        })
    },
    
    constructImageMetaForm: function(imMetaXML) {
        //add components
        var me = this;
        
        this.imageMetaForm.add({
            xtype: 'box',
            html: '<h2>Image Meta</h2><p>Welcome to the image meta data editor. Edit the fields that need to be corrected and update the meta data by selecting Apply New MetaData Values. If a field is left empty or 0 the original meta data will be applied</p>',
            width: '100%',
            cls: 'imgmetaeditor',
            padding: '0px',
            margins:'0px',
        });        
        
        
        //stack count panel
        this.imageMetaForm.formComponents['image_num_z'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.StackCount',{
                dimension: 'z',
            })
        );
        
        this.imageMetaForm.formComponents['image_num_t'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.StackCount',{
                dimension: 't',
            })
        );
        
        this.imageMetaForm.formComponents['image_num_c'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.StackCount',{
                dimension: 'c',
            })
        );
        
        /*
        this.imageMetaForm.formComponents['dimension'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.ChannelOrder')
        );
        */
        
        //dimensions panel
        this.imageMetaForm.formComponents['pixel_resolution_x'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.PixelResolution',{
                dimension: 'x',
            })
        );
        
        this.imageMetaForm.formComponents['pixel_resolution_y'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.PixelResolution',{
                dimension: 'y',
            })
        );
        
        this.imageMetaForm.formComponents['pixel_resolution_z'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.PixelResolution',{
                dimension: 'z',
            })
        );
        
        this.imageMetaForm.formComponents['pixel_resolution_t'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.PixelResolution',{
                dimension: 't',
            })
        );
        
        //channel panel
        this.imageMetaForm.add({
            xtype: 'box',
            html: '<h2>Channel Meta</h2><p>The amount of channels is effected by the channel count.</p>',
            width: '100%',
            cls: 'imgmetaeditor',
            padding: '0px',
            margins:'0px',
        });              
        
        
        this.imageMetaForm.formComponents['channels'] = this.imageMetaForm.add(
            Ext.create('BQ.Calibration.ChannelOrganizer')
        );
        
        //adding listeners to components
        this.imageMetaForm.formComponents['image_num_c'].on('change', function() {
            //var image_num_c_value = me.value;
            //set back to default
            me.imageMetaForm.formComponents['channels'].setChannelNum(this.value, imMetaXML)
        });
        
        //populate values
        this.setFormValues(imMetaXML);
    },

    updateReferenceLength: function() {
        var gobjects = this.imageCalibForm.formComponents['imgViewer'].getGobjects();
        var estimated = this.imageCalibForm.formComponents['reference_length'].getValue();
        if (estimated && gobjects.length>0) {
            var lengths = [];
            for (var g=0; g<gobjects.length; g++) {
                //distance of gobjcts times scalar
                var x1 = gobjects[g].vertices[0].x;
                var x2 = gobjects[g].vertices[1].x;
                
                var y1 = gobjects[g].vertices[0].y;
                var y2 = gobjects[g].vertices[1].y;
                lengths.push(Math.sqrt(Math.pow(x1-x2,2)+Math.pow(y1-y2,2)));
            }
            var avg_lengths = 0;
            for (var i=0; i<lengths.length; i++) {
                 avg_lengths += lengths[i];
            }
            avg_lengths = avg_lengths/lengths.length
            //average all the distances together
            this.imageCalibForm.formComponents['est_px_res'].setValue(estimated/avg_lengths);
        } else {
            this.imageCalibForm.formComponents['est_px_res'].setValue();
        }        
    },
    
    setFormValues: function(imMetaXML) {
        if (this.imageMetaForm.formComponents) {
            for (var k in this.imageMetaForm.formComponents) {
                this.imageMetaForm.formComponents[k].setValues(imMetaXML);
            }
        }
    },
    
    //POST all values back to data_service
    getImageMetaTag: function(cb) {
        var me = this;
        //request for image meta
        Ext.Ajax.request({
            method: 'GET',
            disableCaching :false,
            headers: { 'Content-Type': 'text/xml' },
            url: this.image_resource+'/tag?name=image_meta&view=full',
            params: {view:'full'},
            success: function(response) {
                var xml = response.responseXML;
                cb.apply(this,[xml]);
            },
            failure: function(response) {
                BQ.ui.error('Image Meta failed to be servered for this resource!');
            },
            scope: this,
        });     
        
    },
    
    updateImageMeta: function(imMetaXML) {
        //image meta check for multi tiff to put the correct tags
    
        //from xml document to post
        var uri = imMetaXML.evaluate('//tag[@name="image_meta"]/@uri', imMetaXML, null, XPathResult.STRING_TYPE, null).stringValue;
        if (uri) {
            var imMetaTag = '<tag name="image_meta" type="image_meta" uri="'+uri+'">';
        } else { //image meta query has nothing in it
            imMetaXML = '';
            var imMetaTag = '<tag name="image_meta" type="image_meta">';
 
        }
        
        //var delete_queue = [];
        
        var xmlBody = '';
        if (this.imageMetaForm.formComponents) {
            for (var k in this.imageMetaForm.formComponents) {
                xmlBody += this.imageMetaForm.formComponents[k].fromXmlNode(imMetaXML) || ''; //if nothing is return add empty string
            }
        }

        if (xmlBody.length<1) {
            BQ.ui.notification('Nothing updated.');
            return
        }        
        var imMetaTag = imMetaTag+xmlBody+'</tag>';
        //post to image meta
        /*
        //wait for all deletes
        for (var d=0; d<delete_queue; d++) {
            Ext.Ajax.request({
                method: 'DELETE',
                disableCaching: false,
                headers: {'Content-Type': 'text/xml'},
                url: delete_queue[d],
                success: function(response) {
                    BQ.ui.notification('Removed: '+delete_queue[d]);
                },
                failure: function(response) {
                    BQ.ui.error('Failed to delete Image Meta Tag!');
                },
            });
        }
        */
        Ext.Ajax.request({
            method: 'POST',
            disableCaching: false,
            headers: {'Content-Type': 'text/xml'},
            url: this.image_resource,
            xmlData: imMetaTag,
            success: function(response) {
                this.cleanImageCache();
            },
            failure: function(response) {
                BQ.ui.error('Failed to update Image Meta Tag!');
            },
            scope: this,
        }); 
        
    },
    
    deleteImageMeta: function(imMetaXML) {
        var uri = imMetaXML.evaluate('//tag[@name="image_meta"]/@uri', imMetaXML, null, XPathResult.STRING_TYPE, null).stringValue;
        if (uri) {
            Ext.Ajax.request({
                method: 'DELETE',
                disableCaching: false,
                headers: { 'Content-Type': 'text/xml' },
                url: uri,
                success: function(response) {
                    this.cleanImageCache();
                },
                failure: function(response) {
                    BQ.ui.error('Failed to delete Image Meta Tag!');
                },
                scope: this,
            });               
        } else {
            BQ.ui.notification('No image meta found.');
            return
        }
    },
    
    cleanImageCache: function() {
        Ext.Ajax.request({
            method: 'POST',
            disableCaching: false,
            headers: { 'Content-Type': 'text/xml' },
            url: this.image_resource+'/pixels?cleancache=true',
            success: function(response) {
                Ext.MessageBox.show({
                    title: 'Updated Image Meta Data',
                    msg: 'Updating image meta data was successful! Clean browser cache and then click ok to reload the page.',
                    buttons: Ext.MessageBox.OK,
                    scope: this,
                    fn: function() {
                        location.reload(true);
                    },
                });
            },
            failure: function(response) {
                BQ.ui.error('Image cache has failed to clear!');
            },
            scope: this,
        });
     
    }
    
});
