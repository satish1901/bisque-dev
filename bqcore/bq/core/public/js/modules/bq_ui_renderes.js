/*******************************************************************************

  BQ.selectors - selectors of inputs for module runs
  BQ.renderers - renderers of outputs for module runs

  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/


/*******************************************************************************
  Available selectors and renderers
*******************************************************************************/

Ext.namespace('BQ.selectors');
Ext.namespace('BQ.renderers');

BQ.selectors.resources  = { 'image'            : 'BQ.selectors.Resource', 
                            'dataset'          : 'BQ.selectors.Resource', 
                            'resource'         : 'BQ.selectors.Resource', 
                            'gobject'          : 'BQ.selectors.Gobject', };

BQ.selectors.parameters = { 'tag'              : 'BQ.selectors.String', 
                            'string'           : 'BQ.selectors.String', 
                            'number'           : 'BQ.selectors.Number', 
                            'combo'            : 'BQ.selectors.Combo',
                            'boolean'          : 'BQ.selectors.Boolean',
                            'date'             : 'BQ.selectors.Date', 
                            'image_channel'    : 'BQ.selectors.ImageChannel', 
                            'pixel_resolution' : 'BQ.selectors.PixelResolution', 
                          };

BQ.renderers.resources  = { 'image'            : 'BQ.renderers.Image', 
                            'dataset'          : 'BQ.renderers.Dataset', 
                          //'gobject'          : 'BQ.renderers.Gobject', 
                            'tag'              : 'BQ.renderers.Tag', 
                            'mex'              : 'BQ.renderers.Mex', };


/*******************************************************************************
  Baseclass for output renderers
  
  dima: name is used for unique ID, should be changed
  
  Templated configs:
    label      - 
    loadfrom   - 
    hideloaded - 
    units      - 
  
  imageresolution ?
  
*******************************************************************************/

Ext.define('BQ.renderers.Renderer', {
    alias: 'widget.renderer',    
    extend: 'Ext.container.Container',
    
    // required !!!!
    definition : undefined,
    resource : undefined,
    
    // configs
    cls: 'renderer',
    height: 10,
    border: 0,
    layout: 'auto',
    defaults: { border: 0, xtype: 'container', },

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};      
        this.callParent();
    },

});

/*******************************************************************************
  Baseclass for input selectors
  
  dima: name is used for unique ID, should be changed
  
  Templated configs:
    label      - 
    loadfrom   - 
    hideloaded - 
    units      - 
  
  imageresolution ?
  
*******************************************************************************/

Ext.define('BQ.selectors.Selector', {
    alias: 'widget.selector',    
    extend: 'Ext.container.Container',
    
    // required !!!!
    resource : undefined,
    
    // configs    
    cls: 'selector',
    height: 10,
    border: 0,
    layout: 'auto',
    
    defaults: { border: 0, xtype: 'container', },

    constructor: function(config) {
        this.addEvents({
            'changed'   : true,
        });
        this.callParent(arguments);
        return this;
    },

    validate: function() {
        if (!this.resource) {
            BQ.ui.error('Selector is not configured properly, no resource is defined!'); 
            return false;            
        }        
        
        if (!this.isValid()) {
            this.addCls('invalid');
            return false;                
        }
        
        this.removeCls('invalid');        
        return true;
    },

    // implement: you need to actually create UI for the element
    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};      
        this.callParent();
    },
    
    // implement: you need to provide a way to check the validity of the element
    isValid: function() {
        return true;
    },    

    // implement: you need to provide a way to programmatically select an element
    select: function(new_resource) {
        BQ.ui.warning('Programmatic select is not implemented in this selector');
    },

});




/*******************************************************************************
Resource templated configs:
accepted_type
example_query
prohibit_upload

Validation: enforce input image geometry, not used for datasets
ex: { z: 'stack', t:'single', fail_message: 'Only supports 3D images!' };
    fail_message - message that will be displayed if failed the check
    z or t       - specify dimension to be checked
    here the z or t value may be:
        null or undefined - means it should not be enforced
        'single' - only one plane is allowed
        'stack'  - only stack is allowed  
*******************************************************************************/

Ext.define('BQ.selectors.Resource', {
    alias: 'widget.selectorresource',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.button.Button', 'Bisque.ResourceBrowser.Dialog', 'Bisque.DatasetBrowser.Dialog', 'BQ.upload.Dialog'],
    
    layout: 'auto',
    cls: 'resourcerenderer',
    height: 75,

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        var btns = [];
        var accepted_type = template.accepted_type || {};
        accepted_type[resource.type] = resource.type;

        if ('image' in accepted_type) {
            this.btn_select_image = Ext.create('Ext.button.Button', {
                text: 'Select an Image', 
                //iconCls: 'upload', 
                scale: 'large', 
                //cls: 'x-btn-default-large',
                //tooltip: 'Start the upload of all queued files',
                handler: Ext.Function.bind( this.selectImage, this ),
            });
            btns.push(this.btn_select_image);   
        }

        if ('dataset' in accepted_type || 'iterable' in template) {
            this.btn_select_dataset = Ext.create('Ext.button.Button', {
                text: 'Select a set of images', 
                //iconCls: 'upload', 
                scale: 'large', 
                //cls: 'x-btn-default-large',
                //tooltip: 'Start the upload of all queued files',
                handler: Ext.Function.bind( this.selectDataset, this ),
            });
            btns.push(this.btn_select_dataset);   
        }      
    
        if (template.example_query) {
            this.btn_select_example = Ext.create('Ext.button.Button', {
                text: 'Select an example', 
                //iconCls: 'upload', 
                scale: 'large', 
                //cls: 'x-btn-default-large',
                //tooltip: 'Start the upload of all queued files',
                handler: Ext.Function.bind( this.selectExample, this ),
            });
            btns.push(this.btn_select_example);   
        }
    
        if (!template.prohibit_upload) {
            this.btn_select_upload = Ext.create('Ext.button.Button', {
                text: 'Upload local images', 
                //iconCls: 'upload', 
                scale: 'large', 
                //cls: 'x-btn-default-large',
                //tooltip: 'Start the upload of all queued files',
                handler: Ext.Function.bind( this.selectFile, this ),
            });
            btns.push(this.btn_select_upload);   
        }              

       
        //--------------------------------------------------------------------------------------
        // items
        //-------------------------------------------------------------------------------------- 

        var i=1;
        if (btns.length>1)
        while (i<btns.length) {
            btns.splice(i, 0, {xtype: 'tbtext', text:(btns.length>2 && i>btns.length-2)?' or even ':' or ', } );
            i+=2;
        }
        
        if (template.label)
            btns.unshift( {xtype: 'label', text:template.label+':' } );

        this.items = btns;       
        this.callParent();
    },
    
    selectImage: function() {
        var rb  = new Bisque.ResourceBrowser.Dialog({
            'height' : '85%',
            'width' :  '85%',
            listeners: {  'Select': function(me, resource) { 
                           this.onselected(resource);
                    }, scope: this },
            
        });        
    },
    
    selectDataset: function(r) {
        var rb  = new Bisque.DatasetBrowser.Dialog({
            'height' : '85%',
            'width' :  '85%',
            listeners: {  'DatasetSelect': function(me, resource) { 
                           //this.onResourceSelected(resource);
                           // onResourceSelected dies and so browser is never closed
                           var i = this; var r = resource;
                           setTimeout(function() { i.onselected(r); }, 100);
                    }, scope: this },
        });        
    },
    
    selectExample: function(r) {
        
    },
    
    selectFile: function(r) {
        var uploader = Ext.create('BQ.upload.Dialog', {   
            //title: 'my upload',
            //maxFiles: 1,
            //dataset_configs: BQ.upload.DATASET_CONFIGS.PROHIBIT, 
            listeners: {  'uploaded': function(reslist) { 
                           this.onselected(reslist[0]);
                    }, scope: this },              
        });        
    },
    
    onerror: function(message) {
        BQ.ui.error('Error fethnig resource:<br>' + message); 
    },    
    
    select: function(resource) {
        // if the input resource is a reference to an image with wrapped gobjects
        if (resource instanceof BQTag) {
            this.gobs = resource.gobjects;
            BQFactory.request( { uri: resource.value, 
                                 cb: callback(this, 'onfetched'), 
                                 errorcb: callback(this, 'onerror'), 
                               });               
        } else if (typeof resource != 'string')
            this.onselected(resource);
        else
            BQFactory.request( { uri: resource, 
                                 cb: callback(this, 'onselected'), 
                                 errorcb: callback(this, 'onerror'), 
                               });         
    },    

    onfetched: function(R) {
        R.gobjects = this.gobs;
        this.onselected(R);
    },
    
    onselected: function(R) {
        this.selected_resource = R;
        this.resource.value = R.uri;
        this.resource.type = R.resource_type;
       
        // !!!!!!!!!!!!!!!!!!!!!!!!
        // dima: here I probably need to iterate over all children and run proper selectors
        // right now only one gobject selector will be available
        // !!!!!!!!!!!!!!!!!!!!!!!!!!!

        var increment = this.resource.gobjects.length<1?20:20;

        if (this.resourcePreview) {
            this.setHeight( this.getHeight() - this.resourcePreview.getHeight() - increment);    
            this.resourcePreview.destroy();
        }
        
        // show the preview thumbnail of the selected resource, 
        // if gobjects are required the image viewer will be shown, so no need for the preview
        if (!(this.selected_resource instanceof BQImage) || this.resource.gobjects.length<1) {    
            this.resourcePreview = Bisque.ResourceFactoryWrapper.getResource( {resource:R} );
        } else {
            this.resourcePreview = Ext.create('BQ.selectors.Gobject', {
                resource: this.resource.gobjects[0],
                selected_resource: this.selected_resource,
            });            
        } 
        
        // fetch image physics 
        this.phys = undefined;
        if (this.selected_resource instanceof BQImage) {
            this.phys = new BQImagePhys(this.selected_resource);
            this.phys.load(callback(this, this.onPhys));
        }
        
        this.add(this.resourcePreview);
        this.setHeight( this.getHeight() + this.resourcePreview.getHeight() + increment );

        if (!this.validate()) return;
        this.fireEvent( 'changed', this, this.selected_resource );
    },

    isValid: function() {
        var resource = this.resource;
        var template = resource.template || {};        

        if (!this.selected_resource || !this.selected_resource.uri) {
            //BQ.ui.attention('You need to select an input resource!');
            BQ.ui.tip(this.getId(), 'You need to select an input resource!', {anchor:'left',}); // dima: maybe i need to give dom object for this one, instead of this
            return false;
        }

        //if (this.selected_resource.resource_type == 'dataset' && this.resource.gobjects.length>0) {
        //    BQ.ui.error('Improper module configuration, graphical annotations cannont be required on a dataset!'); 
        //    return false;            
        //} 
        
        // check for image geometry if requested    
        // we don't have image config right in the resource for, skip this for now
        if ( this.phys && this.phys.initialized && 
             this.selected_resource.resource_type == 'image' && 'require_geometry' in template && (
             (template['require_geometry/z'] && template['require_geometry/z']=='single' && this.phys.z>1) ||
             (template['require_geometry/z'] && template['require_geometry/z']=='stack'  && this.phys.z<=1) ||
             (template['require_geometry/t'] && template['require_geometry/t']=='single' && this.phys.t>1) ||
             (template['require_geometry/t'] && template['require_geometry/t']=='stack'  && this.phys.t<=1)
        )) {
            var msg = template['require_geometry/fail_message'] || 'Image geometry check failed!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.getId(), msg); // dima: maybe i need to give dom object id for this one, instead of this        
            return false;
        }
        
        //if (this.selector_gobs) 
        //    return this.selector_gobs.validate();

        if (this.resourcePreview && this.resourcePreview.validate) 
            return this.resourcePreview.validate();
        
        return true;
    },

    onPhys: function() {
        if (this.isValid())
            this.fireEvent( 'gotPhys', this, this.phys );
    },

});

/*******************************************************************************
BQ.selectors.Gobject relies on BQ.selectors.Resource in that it's
not intended to be instantiated directly but only within BQ.selectors.Resource

Gobject templated configs:
accepted_type

Validation: enforce selection of graphical objects
ex: { gobject: ['point'], amount: 'many', fail_message: 'You must select some root tips!' }; 
    fail_message - message that will be displayed if failed the check
    gobject      - a vector of types of gobjects that can be collected
    amount       - constraint on the amount of objects of allowed type
    here the amount value can be:
        null or undefined - means it should not be enforced
        'single' - only one object is allowed
        'many'   - only more than one object allowed
        'oneornone' - only one or none
        number   - exact number of objects allowed        
*******************************************************************************/

Ext.define('BQ.selectors.Gobject', {
    alias: 'widget.selectorgobject',    
    extend: 'BQ.selectors.Selector',
    requires: ['BQ.viewer.Image'],
    
    cls: '',
    layout: 'fit',
    height: 500,

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        var editprimitives = (template.gobject instanceof Array)? template.gobject.join(','):template.gobject;
        var parameters = { nogobjects:'', nosave:'', alwaysedit:'', onlyedit:'', editprimitives: editprimitives, };
        if (this.selected_resource && this.selected_resource.gobjects) parameters.gobjects = this.selected_resource.gobjects;
        this.viewer = Ext.create('BQ.viewer.Image', {
            resource: this.selected_resource || resource.parent.value,
            parameters: parameters,
            listeners: { 'changed': this.onchanged, scope: this, },
        });

        this.items = [this.viewer];       
        this.callParent();
    },
    
    onchanged: function() {    
        //BQ.ui.attention('objects changed');
        if (!this.validate()) return;
        this.resource.gobjects = Ext.clone( this.viewer.getGobjects() );              
    },

    select: function(resource) {
        this.viewer.setGobjects(resource);
    },       
    
    isValid: function() {
        var resource = this.resource;
        var template = resource.template || {};               
        
        // if requested, check if gobjects are present 
        if ('require_gobjects' in template) {
            var gobs = this.viewer ? this.viewer.getGobjects() : null;
            if (!gobs || // gobs.length<=0 || 
                ( 'require_gobjects/amount' in template && template['require_gobjects/amount']=='single'    && gobs.length!=1 ) ||
                ( 'require_gobjects/amount' in template && template['require_gobjects/amount']=='many'      && gobs.length<1 ) ||
                ( 'require_gobjects/amount' in template && template['require_gobjects/amount']=='oneornone' && gobs.length>1 ) ||
                ( 'require_gobjects/amount' in template && template['require_gobjects/amount']>0 && gobs.length!=template['require_gobjects/amount'] )
            ) {
                var msg = template['require_gobjects/fail_message'] || 'Graphical annotations check failed!';
                BQ.ui.attention(msg);
                BQ.ui.tip(this.viewer.getId(), msg, {anchor:'left',});
                return;
            }  
        }         
        
        return true;
    },

});


/*******************************************************************************
BQ.selectors.ImageChannel relies on BQ.selectors.Resource and altough
it is instantiated directly it needs existing BQ.selectors.Resource to listen to
and read data from!

Image Channel templated configs:

<tag name="nuclear_channel" value="1" type="image_channel">
    <tag name="template" type="template">
        <tag name="label" value="Nuclear channel" />
        <tag name="reference" value="image_url" />
        <tag name="guess" value="nuc|Nuc|dapi|DAPI|405|dna|DNA|Cy3" />
    </tag>
</tag>
*******************************************************************************/

Ext.define('BQ.selectors.ImageChannel', {
    alias: 'widget.selectorchannel',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Number', 'Ext.data.Store', 'Ext.form.field.ComboBox'],

    height: 30,
    layout: 'hbox',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        var reference = this.module.inputs_index[template.reference];
        if (reference && reference.renderer) {
            this.reference = reference.renderer;
            this.reference.on( 'changed', function(sel, res) { this.onNewResource(sel, res); }, this );
            this.reference.on( 'gotPhys', function(sel, phys) { this.onPhys(sel, phys); }, this );            
        }
        
        this.items = [];        

        // create numeric channel selector
        var label = template.label?template.label:undefined;
        this.numfield = Ext.create('Ext.form.field.Number', {
            //flex: 1,
            cls: 'number',
            name: resource.name,
            labelWidth: 200,
            labelAlign: 'right',
            fieldLabel: label,
            value: resource.value!=undefined?parseInt(resource.value):undefined,
            minValue: 1,
            maxValue: 100,
            allowDecimals: false,
            step: 1,
            
            listeners: {
                change: function(field, value) {
                    this.resource.value = String(value);
                }, scope: this,
            },
            
        });
        this.items.push(this.numfield);
       
        // create combo box selector
        this.store = Ext.create('Ext.data.Store', {
            fields: ['name', 'channel'],
        });
        
        this.combo = Ext.create('Ext.form.field.ComboBox', {       
            itemId: 'combobox',
            //flex: 1,
            name: resource.name+'_combo',
            labelWidth: 200,
            labelAlign: 'right',
            hidden: true,
            
            fieldLabel: label,
            //value: resource.value,
            multiSelect: false,
            store: this.store,
            queryMode: 'local',
            displayField: 'name',
            valueField: 'channel', 
            
            forceSelection : true,  
            editable : false, 

            listeners: {
                select: function(field, value) {
                    this.resource.value = field.getValue();
                }, scope: this,
            },
            
        });       
        this.items.push(this.combo);        
        
        this.callParent();
    },

    onNewResource : function(sel, res) {
        var resource = this.resource;
        var template = resource.template || {};
        this.numfield.setVisible(true);
        this.combo.setVisible(false);
        
        if (res instanceof BQDataset) {
            var msg = 'You have selected a dataset, this module will only work correctly if all images have the same channel structure!';
            BQ.ui.tip(this.numfield.getId(), msg, {anchor:'left', timeout: 30000, });
        }
    },

    onPhys : function(sel, phys) {
        var resource = this.resource;
        var template = resource.template || {};
        var guess = template.guess || '';
                
        // create channel combo
        var selected = 1;
        var a = [];
        var i=undefined;
        for (var p=0; (i=phys.channel_names[p]); p++) {
            i = String(i);
            a.push({ 'name': ''+(p+1)+': '+i, 'channel': p+1, });  
            if (i.match(guess))
                selected = p+1; 
        }
        this.store.removeAll(true);                      
        this.store.add(a);
        this.combo.setValue(selected);

        this.numfield.setVisible(false);
        this.combo.setVisible(true);
      
    },

    select: function(value) {
        this.numfield.setValue( value );
        this.combo.setValue( value );        
    }, 

    isValid: function() {
        if (!this.resource.value) {
            var template = resource.template || {};
            var msg = template.fail_message || 'You need to select an option!';
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;               
        }        
        return true;
    },

});

/*******************************************************************************
BQ.selectors.PixelResolution relies on BQ.selectors.Resource and altough
it is instantiated directly it needs existing BQ.selectors.Resource to listen to
and read data from!

Pixel Resolution templated configs:

<tag name="pixel_resolution" type="pixel_resolution">
    <value>0</value>
    <value>0</value>
    <value>0</value>             
    <value>0</value>               
    <tag name="template" type="template">
        <tag name="label" value="Voxel resolution" />
        <tag name="reference" value="image_url" />
        <tag name="units" value="microns" />        
    </tag>
</tag>
*******************************************************************************/

Ext.define('BQ.selectors.PixelResolution', {
    alias: 'widget.selectorresolution',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Number'],

    height: 30,
    layout: 'hbox',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        var reference = this.module.inputs_index[template.reference];
        if (reference && reference.renderer) {
            this.reference = reference.renderer;
            this.reference.on( 'changed', function(sel, res) { this.onNewResource(sel, res); }, this );
            this.reference.on( 'gotPhys', function(sel, phys) { this.onPhys(sel, phys); }, this );            
        }

        Ext.tip.QuickTipManager.init();
        
        if (!resource.values) 
            resource.values = []; 
        if (resource.values.length<4)
            resource.values.length = 4;
        // dima, here i need to instantiate Value objects

        this.items = [];        
        var label = template.label?template.label:undefined;  
        var labels = [label+' X', 'Y', 'Z', 'T'];      

        // create resolution pickers        
        this.field_res = [];
        for (var i=0; i<4; i++) {

            this.field_res[i] = Ext.create('Ext.form.field.Number', {
                //flex: 1,
                cls: 'number',
                name: resource.name+String(i),
                value_index: i,
                
                labelAlign: 'right',
                width: i==0?270:80,
                labelWidth: i==0?200:10,
                fieldLabel: labels[i],
                
                value: parseFloat(resource.values[i].value),
                minValue: 0,
                maxValue: 33,
                allowDecimals: true,
                decimalPrecision: 4,
                step: 0.01,
                
                listeners: {
                    change: function(field, value) {
                        resource.values[field.value_index].value = String(value);
                    }, scope: this,
                },
            });
            
            if (template.description)
            Ext.tip.QuickTipManager.register({
                target: this.field_res[i],
                //title: 'My Tooltip',
                text: template.description,
                width: 200,
                dismissDelay: 10000, // Hide after 10 seconds hover
            });            
            
            this.items.push(this.field_res[i]);
        }
        
        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', });        
        
        this.callParent();
    },

    onNewResource : function(sel, res) {
        var resource = this.resource;
        var template = resource.template || {};
        
        var p=null;
        for (var i=0; (p=this.field_res[i]); i++) { 
            p.setVisible(true);
            // probably should not force the reset of resolution here,
            //resource.values[i].value = 0.0;
            //p.setValue(0.0);            
        }
        
        if (res instanceof BQDataset) {
            var msg = 'You have selected a dataset, this module will only work correctly if all images have the same pixel resolution!';
            BQ.ui.tip(this.getId(), msg, {anchor:'left', timeout: 30000, });
        }
    },

    onPhys : function(sel, phys) {
        var resource = this.resource;
        var template = resource.template || {};

        for (var i=0; i<4; i++)
            this.field_res[i].setValue( phys.pixel_size[i] );
        
        if (phys.t>1)
            this.field_res[3].setVisible(true);
        else {
            this.field_res[3].setVisible(false);            
            resource.values[3].value = 1.0;
        }
    },

    select: function(value) {
        //this.numfield.setValue( value );
    }, 

    isValid: function() {
        var resource = this.resource;
        if (!resource.values || 
            resource.values[0].value<=0 || resource.values[1].value<=0 || resource.values[2].value<=0 || resource.values[3].value<=0) {
            var template = resource.template || {};
            var msg = template.fail_message || 'You need to select an option!';
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;               
        }        
        return true;
    },

});




/*******************************************************************************
Number templated configs:
            minValue: template.minValue?template.minValue:undefined,
            maxValue: template.maxValue?template.maxValue:undefined,
            allowDecimals: template.allowDecimals?template.allowDecimals:true,
            decimalPrecision: template.decimalPrecision?template.decimalPrecision:2,
            step: template.step?template.step:1,
            hideNumberPicker
            showSlider
*******************************************************************************/

Ext.define('BQ.selectors.Number', {
    alias: 'widget.selectornumber',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Number'],

    height: 30,    
    layout: 'hbox',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        this.items = [];

        var label = template.label?template.label:undefined;
        
        var values = [resource.value];           
        if (resource.values && resource.values.length>0) {
            values = []; 
            var v=undefined;
            for (var i=0; (v=resource.values[i]); i++)
                values.push(v.value);
            delete resource.value;
        }
        if (values.length>1) this.multivalue = true;
        // slider needs max and min!
        if (!('minValue' in template) || !('maxValue' in template)) template.showSlider = false;
        // configure slider for floating point values
        var defaultDecimalPrecision = template.allowDecimals?2:0;
        var sliderStep = (template.allowDecimals && (!('setep' in template) || template.step>=1))?0.01:1.0;
        
        if (this.multivalue || template.showSlider != false)
        this.slider = Ext.create('Ext.slider.Multi', {        
            flex: 3,
            name: resource.name+'-slider',
            
            labelAlign: 'right',
            labelWidth: (this.multivalue || template.hideNumberPicker)?200:undefined,
            fieldLabel: (this.multivalue || template.hideNumberPicker)?label:undefined,

            values: values,
            minValue: template.minValue,
            maxValue: template.maxValue,
            decimalPrecision: template.decimalPrecision?template.decimalPrecision:template.allowDecimals,
            increment: sliderStep,

            listeners: {
                change: function(field, value) {
                    if (!this.multivalue) {
                        this.resource.value = value;
                        if (this.numfield && this.numfield.getValue()!=value) this.numfield.setValue(value);    
                    } else {
                        var vals = field.getValues(); 
                        for (var i=0; (v=this.resource.values[i]); i++)
                            v.value = vals[i];                                               
                    }
                }, scope: this,
            },
            
        });          
        
        if (!this.multivalue && template.hideNumberPicker != true)
        this.numfield = Ext.create('Ext.form.field.Number', {
            //flex: 1,
            cls: 'number',
            name: resource.name,
            labelWidth: 200,
            labelAlign: 'right',
            fieldLabel: label,
            
            value: resource.value!=undefined?parseFloat(resource.value):undefined,
            
            minValue: template.minValue!=undefined?template.minValue:undefined,
            maxValue: template.maxValue!=undefined?template.maxValue:undefined,
            allowDecimals: template.allowDecimals!=undefined?template.allowDecimals:true,
            decimalPrecision: template.decimalPrecision!=undefined?template.decimalPrecision:2,
            step: template.step!=undefined?template.step:1,
            
            listeners: {
                change: function(field, value) {
                    this.resource.value = String(value);
                }, scope: this,
            },
            
        });

        if (this.numfield) this.items.push(this.numfield);
        if (this.slider) this.items.push(this.slider);
        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', flex: 1, });        
            
        this.callParent();
    },

    select: function(value) {
        if (this.slider) {
            if (value instanceof Array)
                for (var i=0; i<value.length; i++)
                    this.slider.setValue( i, value[i] );
            else
                this.slider.setValue( 0, value ); 
        } else {
            this.numfield.setValue( value ); 
        }
    },     

    isValid: function() {
        var valid = true;
        if (!this.multivalue && !this.resource.value) valid = false;
        if (this.multivalue)
            for (var i=0; (v=this.resource.values[i]); i++)
                valid = valid && v.value;
            
        if (!valid) {
            var template = this.resource.template || {};
            var msg = template.fail_message || 'A numeric value needs to be selected!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;            
        }
        return true;
    },

});


/*******************************************************************************
String templated configs:

            minLength: template.minLength?template.minLength:undefined,
            maxLength: template.maxLength?template.maxLength:undefined,
            allowBlank: template.allowBlank?template.allowBlank:true,
            regex: template.regex?template.regex:undefined,
*******************************************************************************/

Ext.define('BQ.selectors.String', {
    alias: 'widget.selectorstring',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Text'],

    height: 30,    
    layout: 'fit',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        this.items = [{
            xtype: 'textfield',
            itemId: 'textfield',
            flex: 1,
            name: resource.name,
            labelWidth: 200,
            labelAlign: 'right',
            
            fieldLabel: template.label?template.label:'',
            value: resource.value?resource.value:'',
            
            minLength: template.minLength!=undefined?template.minLength:undefined,
            maxLength: template.maxLength!=undefined?template.maxLength:undefined,
            allowBlank: template.allowBlank!=undefined?template.allowBlank:true,
            regex: template.regex?template.regex:undefined,

            listeners: {
                change: function(field, value) {
                    //value = parseInt(value, 10);
                    //field.setValue(value + value % 2);
                    this.resource.value = String(value);
                    this.value = String(value);
                }, scope: this,
            },
            
        }];
        
        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', });
        
        this.callParent();
    },

    select: function(value) {
        this.child('#textfield').setValue( value );
    }, 

    isValid: function() {
        if (!this.resource.value) {
            var template = this.resource.template || {};
            var msg = template.fail_message || 'A string is needed!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;            
        }        
        return true;
    },

});


/*
Combo templated configs:

    select - combo element
    editable
*/
Ext.define('BQ.selectors.Combo', {
    alias: 'widget.selectorcombo',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.data.Store', 'Ext.form.field.ComboBox'],

    height: 30,
    layout: 'hbox',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};

        var a = [];
        var i=undefined;
        for (var p=0; (i=template.select[p]); p++)
            a.push({'select': i});           
        
        var selects = Ext.create('Ext.data.Store', {
            fields: ['select'],
            data: a,
        });
        
        this.items = [];            
        this.items.push({
            xtype: 'combobox',
            itemId: 'combobox',
            //flex: 1,
            name: resource.name,
            labelWidth: 200,
            labelAlign: 'right',
            
            fieldLabel: template.label?template.label:'',
            value: resource.value,
            multiSelect: false,
            store: selects,
            queryMode: 'local',
            displayField: 'select',
            valueField: 'select', 
            
            forceSelection : (template.editable!=undefined)?!template.editable:false,  
            editable : (template.editable!=undefined)?template.editable:true, 

            listeners: {
                select: function(field, value) {
                    this.resource.value = field.getValue();
                    this.value = this.resource.value;
                }, scope: this,
            },
            
        });
        
        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', });
        
        this.callParent();
    },

    select: function(value) {
        this.child('#combobox').setValue( value );
    }, 

    isValid: function() {
        if (!this.resource.value) {
            var template = resource.template || {};
            var msg = template.fail_message || 'You need to select an option!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;               
        }        
        return true;
    },

});

/*
Boolean templated configs:

*/
Ext.define('BQ.selectors.Boolean', {
    alias: 'widget.selectorboolean',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Checkbox'],
    
    height: 30,
    layout: 'hbox',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        
        this.items = [];            
        this.items.push({
            xtype: 'checkbox',
            itemId: 'checkbox',
            //flex: 1,
            name: resource.name,
            labelWidth: 200,
            labelAlign: 'right',
            
            fieldLabel: template.label?template.label:'',
            value: resource.value,

            listeners: {
                select: function(field, value) {
                    this.resource.value = field.getValue();
                    this.value = this.resource.value;
                }, scope: this,
            },
            
        });
        
        this.callParent();
    },

    select: function(value) {
        this.child('#checkbox').setValue( value );
    }, 

    isValid: function() {
        if (!this.resource.value) {
            var template = resource.template || {};
            var msg = template.fail_message || 'You need to make a selection!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;             
        }        
        return true;
    },

});

/*
value is a string in ISO standard
Date templated configs:
nodate
notime
*/
Ext.define('BQ.selectors.Date', {
    alias: 'widget.selectordate',    
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Date', 'Ext.form.field.Time'],
    
    height: 30,
    layout: {type: 'hbox', pack: 'start', },

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        
        //Ext.form.field.Time
        
        this.items = []; 
        if (!template.nodate) {    
            this.selector_date = Ext.create('Ext.form.field.Date', {    
                //xtype: 'datefield',
                //flex: 1,
                name: resource.name,
                labelWidth: 200,
                labelAlign: 'right',
                fieldLabel: template.label?template.label:'',
                
                format: 'Y-m-d',
                value: resource.value!=undefined?resource.value:new Date(),
                listeners: { select: this.onselect, scope: this, },
                
            });
            this.items.push(this.selector_date);
        }

        if (!template.notime) {  
            this.selector_time = Ext.create('Ext.form.field.Time', {         
            //this.items.push({
                //xtype: 'timefield',
                //flex: 1,
                name: resource.name,
                labelWidth: 6,
                fieldLabel: ' ',
                labelSeparator: '',            
                
                format: 'H:i:s',
                value: resource.value!=undefined?resource.value:new Date(),
                listeners: { select: this.onselect, scope: this, },
                
            });  
            this.items.push(this.selector_time); 
        }
        
        this.callParent();
    },

    /*
    select: function(value) {
        this.child('#checkbox').setValue( value );
    },
    */ 

    onselect: function() {
        this.resource.value = this.selector_date.getRawValue() +' ' + this.selector_time.getRawValue();
    },

    isValid: function() {
        if (!this.resource.value) {
            var template = this.resource.template || {};
            var msg = template.fail_message || 'You need to select a time!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;            
        }        
        return true;
    },

});



/*******************************************************************************
  Output renderers - dima: name is used for unique ID, should be changed
  
  image (gobjects)
  dataset (images(gobjects))
  tag (tag)
  
  Templated configs:
    label      - 
    ?? units      - 
  
*******************************************************************************/



/*******************************************************************************
Tag templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.Tag', {
    alias: 'widget.renderertag',    
    extend: 'BQ.renderers.Renderer',
    requires: ['Bisque.ResourceTagger'],

    height: 250,    
    layout: {
        type: 'vbox',
        align : 'stretch',
        pack  : 'start',
    },

    initComponent : function() {
        var definition = this.definition;
        var template = definition.template || {};
        var resource = this.resource;
        if (!definition || !resource) return;                
        
        this.tagger = Ext.create('Bisque.ResourceTagger', {
            resource: resource.type?resource.value:resource, // reference or resource
            flex: 1,
            cls: 'tagger',
            //title : template.label?template.label:resource.name,
            viewMode : 'ReadOnly',
        });        
       
        this.items = [];
        this.items.push( {xtype: 'label', html:(template.label?template.label:resource.name),  } );        
        this.items.push(this.tagger);
        
        this.callParent();
    },

});


/*******************************************************************************
 Abstract class for renderer with Tools - export and plot

*******************************************************************************/
function createArgs(command, values) {
    if (typeof(values)=='string') return '&'+command+'='+escape(values);
    var s='';
    for (var i=0; i<values.length; i++)
        s += '&'+command+(i==0?'':i)+'='+escape(values[i]);
    return s;    
}

function createStatsArgs(command, template, name) {
    var c = template[name+'/'+command];
    if (!c) return '';
    return createArgs(command, c);
}

Ext.define('BQ.renderers.RendererWithTools', {
    extend: 'BQ.renderers.Renderer',

/*
    tools: {
        'plot'          : 'createMenuPlot',
        'export-csv'    : 'createMenuExportCsv',
        'export-xml'    : 'createMenuExportXml',
        'export-excel'  : 'createMenuExportExcel',
        'export-gdocs'  : 'createMenuExportGdocs',
        'preview-movie' : 'createMenuPreviewMovie',   
    },
*/
    toolsPlot: {
        'plot'          : 'createMenuPlot',
    },
    toolsPreview: {
        'preview_movie' : 'createMenuPreviewMovie',   
    },
    toolsExport: {
        'export_csv'    : 'createMenuExportCsv',
        'export_xml'    : 'createMenuExportXml',
        'export_excel'  : 'createMenuExportExcel',
        'export_gdocs'  : 'createMenuExportGdocs',
    },

    createTools : function() {
        // create tools menus
        var plotMenu = Ext.create('Ext.menu.Menu');
        for (var i in this.toolsPlot)
            if (this.toolsPlot[i] in this)
                this[this.toolsPlot[i]](plotMenu);

        var previewMenu = Ext.create('Ext.menu.Menu');
        for (var i in this.toolsPreview)
            if (this.toolsPreview[i] in this)        
                this[this.toolsPreview[i]](previewMenu);

        var exportMenu = Ext.create('Ext.menu.Menu');                
        for (var i in this.toolsExport)
            if (this.toolsExport[i] in this)          
                this[this.toolsExport[i]](exportMenu);     

        var tool_items = [];                
        if (plotMenu.items.getCount()>0)    tool_items.push( { text : 'Plot',    menu: plotMenu, } );
        if (previewMenu.items.getCount()>0) tool_items.push( { text : 'Preview', menu: previewMenu, } );
        if (exportMenu.items.getCount()>0)  tool_items.push( { text : 'Export',  menu: exportMenu, } ); 
        return tool_items;
    },

    createPlot : function(menu, name, template) {
        if (!this.res_uri_for_tools) return;
        menu.add({
            text: template[name+'/label']?template[name+'/label']:'Plot',
            scope: this,
            handler: function() {
                var title = template[name+'/title'];
                if (title instanceof Array) title = title.join(', ');
                var titles = template[name+'/title'];
                if (!(titles instanceof Array)) titles = [titles];
                var opts = { args: {numbins: template[name+'/args/numbins']}, titles: titles, };
                this.plotter = Ext.create('BQ.stats.Dialog', {
                    url     : this.res_uri_for_tools,
                    xpath   : template[name+'/xpath'],
                    xmap    : template[name+'/xmap'],
                    xreduce : template[name+'/xreduce'],
                    title   : title,
                    opts    : opts,
                    root    : this.root,
                });
            },
        });          
    },

    createMenuPlot : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if ('plot' in template && template['plot']==false) return;
        
        var name = 'plot';
        for (var i=0; i<20; i++) {
            if (i>0) name = 'plot' + i;
            if (!(name in template)) break;        
            this.createPlot(menu, name, template);
        }
            
    }, 

    createExportCsv : function(menu, name, template) {
        if (!this.res_uri_for_tools) return;        
        menu.add({
            text: template[name+'/label']?template[name+'/label']:'as CSV',
            scope: this,
            handler: function() {
                var url = '/stats/csv?url=' + this.res_uri_for_tools;
                if (this.root) url = this.root + url;
                url += createStatsArgs('xpath', template, name);
                url += createStatsArgs('xmap', template, name);
                url += createStatsArgs('xreduce', template, name);                                        
                window.open(url);                
            },
        });         
    },

    createMenuExportCsv : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if ('export_csv' in template && template['export_csv']==false) return;
        
        var name = 'export_csv';
        for (var i=0; i<20; i++) {
            if (i>0) name = 'export_csv' + i;
            if (!(name in template)) break;            
            this.createExportCsv(menu, name, template);
        }
    }, 

    createMenuExportXml : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if ('export_xml' in template && template['export_xml']==false) return; 
        menu.add({
            text: 'complete document as XML',
            scope: this,
            handler: function() {
                window.open(this.res_uri_for_tools + '?view=deep');
            },
        }); 
    }, 

    createMenuExportExcel : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if ('export_excel' in template && template['export_excel']==false) return; 
        menu.add({
            text: 'complete document as CSV',
            scope: this,
            handler: function() {
                window.open(this.res_uri_for_tools + '?view=deep&format=csv');
            },
        });      
    }, 

    createMenuExportGdocs : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if ('export_gdocs' in template && template['export_gdocs']==false) return; 
        menu.add({
            text: 'complete document to Google Docs',
            scope: this,
            handler: function() {
                window.open('/export/to_gdocs?url='+this.res_uri_for_tools);
            },
        });        
    }, 


});




/*******************************************************************************
Image templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.Image', {
    alias: 'widget.rendererimage',    
    extend: 'BQ.renderers.RendererWithTools',
    requires: ['BQ.viewer.Image'],
    
    height: 500,
    layout: {
        type: 'vbox',
        align : 'stretch',
        pack  : 'start',
    },    

    initComponent : function() {
        var definition = this.definition;
        var template = definition.template || {};
        var resource = this.resource;
        if (!definition || !resource) return;
        
        this.gobjects = resource.gobjects;
        var parameters = { simpleview: '', gobjects: this.gobjects, };
        this.viewer = Ext.create('BQ.viewer.Image', {
            resource: resource.resource_type=='image'?resource:resource.value, // reference or resource
            flex: 1,
            parameters: parameters,
            //listeners: { 'changed': this.onchanged, scope: this, },
        });

        // create tools menus
        var tool_items = [];
        if (this.gobjects.length>0) {
            this.res_uri_for_tools = this.gobjects[0].uri;
            var gobs = this.definition.gobjects[0];
            this.template_for_tools = (gobs?gobs.template:{}) || {};
            tool_items = this.createTools();
        }

        this.items = [];
        this.items.push( {xtype: 'label', html:(template.label?template.label:resource.name), } );        
        if (tool_items.length>0) this.items.push( {xtype: 'toolbar', items: tool_items, defaults: { scale: 'medium' }, } );               
        this.items.push(this.viewer);        

        // find image host root to use to form stats requests 
        this.root = this.resource.uri.replace(/\/data_service\/.*$/i, '');  
               
        this.callParent();
    },

    createMenuPreviewMovie : function(menu) {
        var gobs = this.definition.gobjects[0];
        var template = (gobs?gobs.template:{}) || {};
        if ('preview_movie' in template && template['preview_movie']==false) return;
        var resource_uri = this.resource.resource_type=='image'?this.resource.uri:this.resource.value;
        menu.add({
            text: 'Overlay annotations on a movie',
            scope: this,
            handler: function() {
                window.open('/client_service/movieplayer?resource='+resource_uri+'&gobjects='+this.gobjects[0].uri);
            },
        }); 
    }, 


});


/*******************************************************************************
Dataset templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.Dataset', {
    alias: 'widget.rendererdataset',    
    extend: 'BQ.renderers.Renderer',
    requires: ['Bisque.ResourceBrowser.Browser'],
    
    height: 300,
    layout: {
        type: 'vbox',
        align : 'stretch',
        pack  : 'start',
    },    

    constructor: function(config) {
        this.addEvents({
            'selected' : true,
        });
        this.callParent(arguments);
        return this;
    },

    initComponent : function() {
        var definition = this.definition;
        var template = definition ? definition.template||{} : {};
        var resource = this.resource;
        
        var heading = this.title?this.title:(template.label?template.label:resource.name); 

        this.items = [];
        this.items.push( {xtype: 'label', html: heading, } );        
        //this.items.push(this.browser);        
        this.callParent();
        if (typeof resource == 'string') {
            BQFactory.request( { uri: resource, 
                                 cb:  callback(this, 'initBrowser'), 
                                 uri_params: {view:'deep'}, });
        } else if (resource.resource_type == 'tag' && resource.type == 'dataset') {
            BQFactory.request( { uri: resource.value, 
                                 cb:  callback(this, 'initBrowser'), 
                                 uri_params: {view:'deep'}, });
        } else {
            this.initBrowser(resource);
        }        
    },
    
    initBrowser: function(resource) {
        //resource: resource.resource_type=='image'?resource:resource.value, // reference or resource
        this.browser = Ext.create('Bisque.ResourceBrowser.Browser', {
            //dataset: resource,
            dataset: resource.getMembers().uri+'/value',
            selType: 'SINGLE',
            height: '100%',
            cls: 'bordered',
            viewMode : 'ViewerOnly',
            listeners: { 'Select': function(me, resource) { 
                           this.fireEvent( 'selected', resource); 
                           }, 
                        scope: this 
            },
        }); 
        this.add(this.browser);              
    },

});

/*******************************************************************************
Mex templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.Mex', {
    alias: 'widget.renderermex',    
    extend: 'BQ.renderers.RendererWithTools',
    
    height: 50,
    layout: {
        type: 'vbox',
        align : 'stretch',
        pack  : 'start',
    },    

    initComponent : function() {
        var definition = this.definition;
        var template = definition.template || {};
        var resource = this.resource;
        if (!definition || !resource) return;
        
        // create tools menus
        var tool_items = [];
        this.res_uri_for_tools = resource.value; // dima: resource.value ???
        this.template_for_tools = template;
        tool_items = this.createTools();

        this.items = [];
        this.items.push( {xtype: 'label', html:(template.label?template.label:resource.name), } );        
        if (tool_items.length>0) 
            this.items.push( {xtype: 'toolbar', items: tool_items, defaults: { scale: 'medium' }, } );               
               
        this.callParent();
    },

});
