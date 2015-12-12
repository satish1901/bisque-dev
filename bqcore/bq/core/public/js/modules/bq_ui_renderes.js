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

Ext.namespace('BQ.selectors.resources');
Ext.namespace('BQ.selectors.parameters');
Ext.namespace('BQ.renderers.resources');

BQ.selectors.resources  = { 'image'            : 'BQ.selectors.Resource',
                            'dataset'          : 'BQ.selectors.Resource',
                            'resource'         : 'BQ.selectors.Resource',
                            'gobject'          : 'BQ.selectors.Gobject',
                            'mex'              : 'BQ.selectors.Mex',
                            'subtree'          : 'BQ.selectors.SubTree'
                          };

BQ.selectors.parameters = { 'tag'              : 'BQ.selectors.String',
                            'string'           : 'BQ.selectors.String',
                            'number'           : 'BQ.selectors.Number',
                            'combo'            : 'BQ.selectors.Combo',
                            'boolean'          : 'BQ.selectors.Boolean',
                            'date'             : 'BQ.selectors.Date',
                            'image_channel'    : 'BQ.selectors.ImageChannel',
                            'pixel_resolution' : 'BQ.selectors.PixelResolution',
                            'annotation_attr'  : 'BQ.selectors.AnnotationsAttributes',
                          };

BQ.renderers.resources  = { 'image'            : 'BQ.renderers.Image',
                            'file'             : 'BQ.renderers.File',
                            'dataset'          : 'BQ.renderers.Dataset',
                          //'gobject'          : 'BQ.renderers.Gobject',
                            'tag'              : 'BQ.renderers.Tag',
                            'mex'              : 'BQ.renderers.Mex',
                            'browser'          : 'BQ.renderers.Browser',
                            'table'            : 'BQ.renderers.Table',
                          };


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
    defaults: { border: 0, xtype: 'container' },

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

    defaults: { /*border: 0,*/ xtype: 'container', },

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
    custom_resources: {'resource':null, 'image':null, 'dataset':null, 'query':null},
    btn_select: {},

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

        if ('query' in accepted_type) {
            this.btn_select_query = Ext.create('Ext.button.Button', {
                text: 'Query for a set of images',
                //iconCls: 'upload',
                scale: 'large',
                //cls: 'x-btn-default-large',
                //tooltip: 'Start the upload of all queued files',
                handler: Ext.Function.bind( this.selectQuery, this ),
            });
            btns.push(this.btn_select_query);
        }

        // now create pickers for any other requested resource type
        for (res in accepted_type) {
            if (res in this.custom_resources) continue;
            this.btn_select[res] = this.createSelectorButton(res, template);
            btns.push(this.btn_select[res]);
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
        var browser  = new Bisque.ResourceBrowser.Dialog({
            height      :   '85%',
            width       :   '85%',
            selType     :   'SINGLE',
            listeners   :   {'Select': function(me, resource) {
                                   //this.onselected(resource);
                                   var i = this; var r = resource;
                                   setTimeout(function() { i.onselected(r); }, 100);
                            }, scope: this },

        });
    },

    selectExample: function() {
        var template = this.resource.template || {};
        var browser  = new Bisque.ResourceBrowser.Dialog({
            height   : '85%',
            width    : '85%',
            selType  : 'SINGLE',
            viewMode : 'ViewerOnly',
            tagQuery : template.example_query,
            wpublic  : 'true',
            listeners: {  'Select': function(me, resource) {
                           //this.onselected(resource);
                           var i = this; var r = resource;
                           setTimeout(function() { i.onselected(r); }, 100);
                    }, scope: this },
        });
    },

    selectDataset: function() {
        var browser  = new Bisque.DatasetBrowser.Dialog({
            'height' : '85%',
            'width' :  '85%',
            listeners: {  'DatasetSelect': function(me, resource) {
                           //this.onselected(resource);
                           var i = this; var r = resource;
                           setTimeout(function() { i.onselected(r); }, 100);
                    }, scope: this },
        });
    },

    selectQuery: function() {
        var browser  = new Bisque.QueryBrowser.Dialog({
            'height' : '85%',
            'width' :  '85%',
            dataset   : '/data_service/image',
            query_resource_type: 'image',
            listeners: {'Select': function(me, tag_query) {
                        //this.onselected(resource);
                        var i = this;
                        this.tag_query = tag_query // passing the tag_query to createQueryViewer
                        var r = '/data_service/image?tag_query='+tag_query;
                        if (me.browser.browserParams.wpublic) {
                            r += '&wpublic=true'; //adds with public to query
                        }
                        setTimeout(function() {
                            BQFactory.request( { uri: r,
                                 cb: callback(i, 'onselectedquery'),
                                 errorcb: callback(i, 'onerror'),
                            });
                            }, 100);
                        }, scope: this },
        });
    },


    selectFile: function() {
        var uploader = Ext.create('BQ.upload.Dialog', {
            //title: 'my upload',
            //maxFiles: 1,
            //dataset_configs: BQ.upload.DATASET_CONFIGS.PROHIBIT,
            listeners: {
                scope: this,
                uploaded: function(reslist) {
                    //this.onselected(reslist[0]);
                    var i = this; var r = reslist[0];
                    setTimeout(function() { i.onselected(r); }, 100);
                }
            },
        });
    },

    createSelectorButton: function(res_type, template) {
        return Ext.create('Ext.button.Button', {
            text: 'Select '+res_type,
            scale: 'large',
            scope: this,
            handler: function() {
                var browser  = Ext.create('Bisque.ResourceBrowser.Dialog', {
                    'height' : '85%',
                    'width' :  '85%',
                    dataset: BQ.Server.url('/data_service/'+res_type),
                    tagQuery: template.query,
                    listeners: {
                        'Select': function(me, resource) { this.onselected(resource); },
                        scope: this
                    },
                });
            },
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
            this.resourcePreview = Bisque.ResourceFactoryWrapper.getResource({
                resource: R,
                listeners: {
                    'select': function(T) {
                        window.open('/client_service/view?resource='+T.resource.uri);
                    },
                    scope: this,
                },
            });

        } else {
            this.resourcePreview = Ext.create('BQ.selectors.Gobject', {
                resource: this.resource.gobjects[0],
                selected_resource: this.selected_resource,
                parent_renderer: this,
            });
        }

        // fetch image physics
        this.phys = undefined;
        if (this.selected_resource instanceof BQImage) {
            this.onImage(this.selected_resource);
        } else if (this.selected_resource instanceof BQDataset) {
            var me = this;

            this.selected_resource.getMembers(function (dataset) {
                // Sometime values are loaded instances (image) and sometimes not!
                var uri = dataset.members[0].uri || dataset.values[0].value;
                BQFactory.request ({ uri : uri,
                                     cb: callback(me, 'onImage'),
                                     errorcb: callback(me, 'onerror'),
                                   }); });


            // BQFactory.request({
            //     uri: this.selected_resource.getMembers().values[0].value,
            //     cb: callback(this, 'onImage'),
            //     errorcb: callback(this, 'onerror'),
            // });
        }

        this.add(this.resourcePreview);
        this.setHeight( this.getHeight() + this.resourcePreview.getHeight() + increment );

        this.fireEvent( 'changed', this, this.selected_resource );
        if (!this.validate()) return;
    },

    /*
     *
     *  Query View (since there are no query templates a list
     *     of items queried are displayed
     *
     */
    onselectedquery: function(R){
        this.selected_resource = R;
        this.resource.value = R.uri;
        this.resource.type = R.resource_type;

        var increment = this.resource.gobjects.length<1?20:20;

        if (this.resourcePreview) {
            this.setHeight( this.getHeight() - this.resourcePreview.getHeight() - increment);
            this.resourcePreview.destroy();
        }

        this.resourcePreview = this.createQueryViewer(R);

        this.add(this.resourcePreview);
        this.setHeight( this.getHeight() + this.resourcePreview.getHeight() + increment );

        this.fireEvent( 'changed', this, this.selected_resource );
        if (!this.validate()) return;
    },

    //create a view for the query
    //  The veiw is just a list of tags and values used to query
    createQueryViewer: function(R) {

        Ext.regModel('QueryModel', {
            fields: [
                {type: 'string', name: 'Tag'},
                {type: 'string', name: 'Name'},
                    ]
            });

        var querytags = [];
        d_query=this.tag_query.replace(/"/g, ""); //removing '"'
        d_query=d_query.split(' AND ');
        for(i=0;i<d_query.length;i++){
            s_query=d_query[i].split(':');
            querytags.push([s_query[0],s_query[1]]);
        }
        // The data store holding the states
        var store = Ext.create('Ext.data.Store', {
            model: 'QueryModel',
            data: querytags
        });

        var queryView = Ext.create('Ext.grid.Panel', {
            store: store,
            autoScroll: true,
            width: 'auto',
            height: 125,
            stateful: true,
            title: 'Query',
            stateId: 'stateGrid',
            enableColumnHide:false,
            forceFit: true,
            margin: "10 0 0 0",
            columns: [
                {
                    text     : 'Tags',
                    width    : '30%',
                    //width    : 175,
                    sortable : true,
                    dataIndex: 'Tag'
                },
                {
                    text     : 'Names',
                    width    : '70%',
                    //width    : 175,
                    sortable : true,
                    dataIndex: 'Name'
                },
            ],
            viewConfig: {
                stripeRows: true,
                //enableTextSelection: true
            }
        });
        delete this.tag_query  // no longer need tag_query
        return queryView
    },

    onImage: function(image) {
        this.phys = new BQImagePhys(image);
        this.phys.load(callback(this, this.onPhys));
    },

    onPhys: function() {
        this.fireEvent( 'gotPhys', this, this.phys );
        this.validate();
    },

    isValid: function() {
        var resource = this.resource;
        var template = resource.template || {};

        if (template.allow_blank && (!this.selected_resource || !this.selected_resource.uri)) {
            return true;
        } else if (!this.selected_resource || !this.selected_resource.uri) {
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

        if (this.resourcePreview && this.resourcePreview.validate)
            return this.resourcePreview.validate();

        return true;
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
        var parameters = {
            nogobjects: '',
            nosave: '',
            alwaysedit: '',
            onlyedit: '',
            editprimitives: editprimitives,
            no_semantic_types: true,
        };
        if (this.selected_resource && this.selected_resource.gobjects) parameters.gobjects = this.selected_resource.gobjects;
        this.viewer = Ext.create('BQ.viewer.Image', {
            resource: this.selected_resource || resource.parent.value,
            parameters: parameters,
            listeners: {
                scope: this,
                changed: this.onchanged,
            },
        });

        this.items = [this.viewer];
        this.callParent();
    },

    onchanged: function() {
        //BQ.ui.attention('objects changed');
        var rend = this.parent_renderer || this;
        if (!rend.validate()) return;
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
            var amount = null;
            if ('require_gobjects/amount' in template) amount = template['require_gobjects/amount'];

            if (gobs && amount && amount=='single'    && gobs.length==1) return true;
            if (gobs && amount && amount=='many'      && gobs.length>=1) return true;
            if (gobs && amount && amount=='oneornone' && gobs.length<=1) return true;
            if (gobs && amount && typeof(amount)=='number' && amount>0 && gobs.length==amount) return true;

            if (gobs && amount && typeof(amount)=='string') {
                var ops = { '>':undefined, '<':undefined, '>=':undefined, '<=':undefined, '==':undefined, };
                var m = amount.match(/([<>=]+)|(\d+)/g);
                if (m && m.length==2 && m[0] in ops && !(isNaN(parseFloat(m[1]))))
                    if (eval('gobs.length '+m[0]+m[1])) return true;
            }

            // all tests have failed
            var msg = template['require_gobjects/fail_message'] || 'Graphical annotations check failed!';
            //BQ.ui.attention(msg);
            BQ.ui.tip(this.viewer.getId(), msg, {anchor:'left',});
            return false;
        }
        //this.resource.gobjects = Ext.clone( this.viewer.getGobjects() );
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
        <tag name="allowNone" value="false" type="boolean" />
    </tag>
</tag>
*******************************************************************************/

Ext.define('BQ.selectors.ImageChannel', {
    alias: 'widget.selectorchannel',
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.form.field.Number', 'Ext.data.Store', 'Ext.form.field.ComboBox', 'Ext.tip.*'],

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
            minValue: template.allowNone?0:1,
            maxValue: 1000,
            allowDecimals: false,
            step: 1,

            listeners: {
                scope: this,
                change: function(field, value) {
                    this.resource.value = String(value);
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
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
                scope: this,
                select: function(field, value) {
                    this.resource.value = field.getValue();
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
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

        if (!(res instanceof BQImage)) {
            var msg = 'You have selected a group resource, this module will only work correctly if all images have the same channel structure!';
            BQ.ui.tip(this.numfield.getId(), msg, {anchor:'left', timeout: 30000, color: 'blue', });
        }
    },

    setValue : function(v) {
        this.numfield.setValue(v);
        this.combo.setValue(v);
    },

    onPhys : function(sel, phys) {
        var resource = this.resource;
        var template = resource.template || {};
        var guess = template.guess;

        // create channel combo
        var selected = 1;
        var a = [];
        if (template.allowNone) {
            a.push({ 'name': 'None', 'channel': 0, });
            selected = 0;
        }

        var i=undefined;
        for (var p=0; (i=phys.channel_names[p]); p++) {
            i = String(i);
            a.push({ 'name': ''+(p+1)+': '+i, 'channel': p+1, });
            if (guess && i.match(guess))
                selected = p+1;
        }
        this.store.removeAll(true);
        this.store.add(a);
        this.setValue(this.selected_value || selected);
        this.selected_value = undefined;

        this.numfield.setVisible(false);
        this.combo.setVisible(true);
    },

    select: function(resource) {
        var value = parseInt(resource.value);
        this.selected_value = value;
        this.setValue( value );
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

                value: resource.values[i] ? parseFloat(resource.values[i].value) : 0.0,
                minValue: 0,
                //maxValue: 33,
                allowDecimals: true,
                decimalPrecision: 4,
                step: 0.01,

                listeners: {
                    scope: this,
                    change: function(field, value) {
                        resource.values[field.value_index] = new BQValue ('number', value, field.value_index);
                    },
                    afterrender : function(o) {
                        o.tip = Ext.create('Ext.tip.ToolTip', {
                            target : o.getEl().getAttribute("id"),
                            html : template.description,
                        });
                    },
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
            this.items.push({
                xtype: 'tbtext',
                itemId: 'units'+i,
                //html:'<label>'+template.units+'</label>',
                cls: 'units',
            });
        }

        //if (template.units)
        //    this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', });

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

        this.reference = res;
        if (res instanceof BQDataset) {
            var msg = 'In a dataset run, use 0 to pull embedded resolution or all images should have the same pixel resolution!';
            BQ.ui.tip(this.getId(), msg, { anchor:'left', timeout: 30000, color: 'blue', });
        }
    },

    onPhys : function(sel, phys) {
        var resource = this.resource;
        var template = resource.template || {};

        if (this.selected_value)
            this.selected_value = undefined;
        else
        for (var i=0; i<4; i++) {
            this.field_res[i].setValue( phys.pixel_size[i] );
            this.queryById('units'+i).setText(phys.pixel_units[i]);
        }

        if (phys.t>1) {
            this.field_res[3].setVisible(true);
            this.queryById('units3').setVisible(true);
        } else {
            this.field_res[3].setVisible(false);
            this.queryById('units3').setVisible(false);
            resource.values[3] = new BQValue ('number', 1.0, 3);
        }
    },

    select: function(resource) {
        var value = resource.value==undefined?resource.values:resource.value;
        this.selected_value = value;
        if (value instanceof Array)
            for (var i=0; i<value.length; i++)
                this.field_res[i].setValue( value[i].value );
        else
            this.field_res[0].setValue( value );
    },

    isValid: function() {
        var resource = this.resource;
        var reference = this.reference;

        if (reference instanceof BQDataset) {
            return true;
        }

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
BQ.selectors.AnnotationsAttributes relies on BQ.selectors.Resource and altough
it is instantiated directly it needs existing BQ.selectors.Resource to listen to
and read data from!

templated configs:

<tag name="gob_types" value="" type="annotation_attr">
    <tag name="template" type="template">
        <tag name="label" value="Graphical types" />
        <tag name="allowBlank" value="false" type="boolean" />

        <tag name="reference_dataset" value="dataset_url" />
        <tag name="reference_type" value="annotation_type" />
        <tag name="reference_attribute" value="annotation_attribute" />

        <tag name="element" value="gobject" />
        <tag name="attribute" value="type" />
        <tag name="dataset" value="/data_service/" />
    </tag>
</tag>
*******************************************************************************/

Ext.define('BQ.selectors.AnnotationsAttributes', {
    alias: 'widget.selectorannotationattr',
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.data.Store', 'Ext.form.field.ComboBox', 'Ext.tip.*'],

    height: 30,
    layout: 'hbox',

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};
        this.element = template.element;
        this.attribute = template.attribute;
        this.dataset = template.dataset;
        this.editable = template.editable || false;

        var reference_dataset = this.module.inputs_index[template.reference_dataset];
        if (reference_dataset && reference_dataset.renderer) {
            this.reference_dataset = reference_dataset.renderer;
            this.reference_dataset.on( 'changed', this.onNewResource, this );
        }

        var reference_element = this.module.inputs_index[template.reference_type];
        if (reference_element && reference_element.renderer) {
            this.reference_element = reference_element.renderer;
            this.reference_element.on( 'changed', this.onNewType, this );
        }

        var reference_attribute = this.module.inputs_index[template.reference_attribute];
        if (reference_attribute && reference_attribute.renderer) {
            this.reference_attribute = reference_attribute.renderer;
            this.reference_attribute.on( 'changed', this.onNewAttribute, this );
        }

        this.items = [];

        // create combo box selector
        this.store = Ext.create('Ext.data.Store', {
            fields: ['Value', 'Element'],
        });

        this.combo = Ext.create('Ext.form.field.ComboBox', {
            itemId: 'combobox',
            //flex: 1,
            name: resource.name+'_combo',
            labelWidth: 200,
            labelAlign: 'right',
            width: '100%',

            fieldLabel: template.label,
            //value: resource.value,
            multiSelect: false,
            store: this.store,
            queryMode: 'local',
            displayField: 'Value',
            valueField: 'Value',

            forceSelection : !this.editable,
            editable : this.editable,

            listeners: {
                scope: this,
                select: function(field, value) {
                    this.resource.value = field.getValue();
                },
                change: function(field, value) {
                    this.resource.value = field.getValue();
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
            },

        });
        this.items.push(this.combo);

        this.callParent();
        this.reload();
    },

    onNewResource : function(el, res) {
        if (res instanceof BQDataset)
            this.dataset = res.uri + '/value';
        else
            this.dataset = res.uri;
        this.reload();
    },

    onNewType : function(el, sel) {
        this.element = sel;
        this.reload();
    },

    onNewAttribute : function(el, sel) {
        this.attribute = sel;
        this.reload();
    },

    setValue : function(v) {
        this.combo.setValue(v);
    },

    reload : function() {
        this.setLoading('Fetching attributes...');
        //  /data_service/00-ecpvN7bnv9cD5KtKkKwLpT/value?extract=tag[name],gobject[type]
        var url = this.dataset + '?extract='+this.element+'['+this.attribute+']';
        Ext.Ajax.request({
            url: url,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    this.onError();
                else
                    this.onTypes(response.responseXML);
            },
            scope: this,
            disableCaching: false,
        });
    },

    onError : function() {
        this.setLoading(false);
        BQ.ui.error('Problem fetching attributes');
    },

    onTypes : function(xml) {
        this.setLoading(false);
        var types = [],
            gobs = BQ.util.xpath_nodes(xml, '//'+this.element),
            g=undefined;
        for (var i=0; g=gobs[i]; ++i) {
            types.push({
                Element: g.tag,
                Value : g.getAttribute(this.attribute),
            });
        } // for types

        this.store.loadData(types);
        if (!this.editable) {
            this.setValue(undefined);
        }
    },

    select: function(resource) {
        this.setValue( resource.value );
    },

    isValid: function() {
        if (!this.resource.value) {
            var template = this.resource.template || {},
                msg = template.fail_message || 'You need to select an option!';
            if (template.allowBlank) return true;
            BQ.ui.tip(this.getId(), msg, {anchor:'left',});
            return false;
        }
        return true;
    },

});


/*******************************************************************************
Resource templated configs:
query
*******************************************************************************/

Ext.define('BQ.selectors.Mex', {
    alias: 'widget.selectormex',
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.button.Button', 'Bisque.ResourceBrowser.Dialog', 'Bisque.DatasetBrowser.Dialog'],

    layout: 'auto',
    cls: 'resourcerenderer',
    height: 75,

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};

        this.items = [];
        this.items.push( {xtype: 'label', text:template.label+':' } );
        this.items.push( Ext.create('Ext.button.Button', {
            text: 'Select a module execution (MEX)',
            //iconCls: 'upload',
            scale: 'large',
            //cls: 'x-btn-default-large',
            tooltip: template.description,
            handler: Ext.Function.bind( this.selectMex, this ),
        }));

        this.callParent();
    },

    selectMex: function() {
        var resource = this.resource;
        var template = resource.template || {};
        var browser  = Ext.create('Bisque.ResourceBrowser.Dialog', {
            'height' : '85%',
            'width' :  '85%',
            dataset: BQ.Server.url('/data_service/mex'),
            tagQuery: template.query,
            listeners: {
                'Select': function(me, resource) { this.onselected(resource); },
                scope: this
            },

        });
    },

    onerror: function(message) {
        this.setLoading(false);
        BQ.ui.error('Error fethnig resource:<br>' + message);
    },

    select: function(resource) {
        // if the input resource is a reference to an image with wrapped gobjects
        if (resource instanceof BQTag) {
            BQFactory.request({
                uri: resource.value,
                cb: callback(this, 'onselected'),
                errorcb: callback(this, 'onerror'),
                uri_params: { view:'deep' },
            });
        } else if (typeof resource != 'string') {
            this.onselected(resource);
        } else {
            BQFactory.request({
                uri: resource,
                cb: callback(this, 'onselected'),
                errorcb: callback(this, 'onerror'),
                uri_params: { view:'deep' },
            });
        }
    },

    onselected: function(R) {
        this.selected_resource = R;
        this.resource.value = R.uri;
        this.resource.type = R.resource_type;
        var increment = 20;

        if (this.resourcePreview) {
            this.setHeight( this.getHeight() - this.resourcePreview.getHeight() - increment);
            this.resourcePreview.destroy();
        }
        this.resourcePreview = Bisque.ResourceFactoryWrapper.getResource( {resource:R} );
        this.add(this.resourcePreview);
        this.setHeight( this.getHeight() + this.resourcePreview.getHeight() + increment );

        this.fireEvent( 'changed', this, this.selected_resource );
        if (!this.validate()) return;

        var template = this.resource.template || {};
        var mymex = this.selected_resource;
        if (template.query_selected_resource && mymex.inputs_index) {
            this.onFullMex(mymex);
        } else if (template.query_selected_resource && !mymex.inputs_index) {
            this.setLoading('Fetching full Module Execution document');
            BQFactory.request({
                uri: mymex.uri,
                cb: callback(this, 'onFullMex'),
                errorcb: callback(this, 'onerror'),
                uri_params: { view:'deep' },
            });
        }
    },

    onFullMex: function(mex) {
        var template = this.resource.template || {};

        //dima: if iterated mex, find first submex, we need  xpath here !!!!!!!!!!!!
        if (mex.iterables && mex.iterables[template.query_selected_resource]) {
            var o=null;
            for (var i=0; (o=mex.children[i]); i++)
                if (o instanceof BQMex) {
                    mex = o;
                    break;
                }
        }

        var uri = mex.dict['inputs/'+template.query_selected_resource];
        BQFactory.request({
            uri: uri,
            cb: callback(this, 'onImage'),
            errorcb: callback(this, 'onerror'),
        });
    },

    onImage: function(image) {
        this.setLoading(false);
        this.phys = new BQImagePhys(image);
        this.phys.load(callback(this, this.onPhys));
    },

    onPhys: function() {
        this.fireEvent( 'gotPhys', this, this.phys );
    },

    isValid: function() {
        var resource = this.resource;
        var template = resource.template || {};

        if (!this.selected_resource || !this.selected_resource.uri) {
            //BQ.ui.attention('You need to select an input resource!');
            BQ.ui.tip(this.getId(), 'You need to select an input resource!', {anchor:'left',});
            return false;
        }

        return true;
    },

});

/*******************************************************************************
Resource templated configs:

*******************************************************************************/

Ext.define('BQ.selectors.SubTree', {
    alias: 'widget.selectorsubtree',
    extend: 'BQ.selectors.Selector',
    requires: ['Ext.button.Button', 'Ext.tree.*', 'Ext.data.*'],

    layout: 'auto',
    cls: 'resourcerenderer',
    //height: 75,
    height: 400,

    initComponent : function() {
        var resource = this.resource;
        var template = resource.template || {};

        this.items = [];
        this.items.push( {xtype: 'label', text:template.label+':' } );
        /*
        this.items.push( Ext.create('Ext.button.Button', {
            text: 'Select a module execution (MEX)',
            //iconCls: 'upload',
            scale: 'large',
            //cls: 'x-btn-default-large',
            //tooltip: 'Start the upload of all queued files',
            handler: Ext.Function.bind( this.selectSub, this ),
        }));
        */


        var grid = Ext.create('BQ.grid.Panel', {
            border: 1,
            url: BQ.Server.url('/data_service/image'),
        });
        this.items.push(grid);


        this.callParent();
    },

    selectSub: function() {
        var resource = this.resource;
        var template = resource.template || {};
        var browser  = Ext.create('Bisque.ResourceBrowser.Dialog', {
            'height' : '85%',
            'width'  : '85%',
            dataset  : template.path,
            tagQuery : template.query,
            listeners: {  'Select': function(me, resource) {
                           this.onselected(resource);
                    }, scope: this },

        });
    },

    onerror: function(message) {
        BQ.ui.error('Error fethnig resource:<br>' + message);
    },

    select: function(resource) {
        // if the input resource is a reference to an image with wrapped gobjects
        if (resource instanceof BQTag) {
            BQFactory.request( { uri: resource.value,
                                 cb: callback(this, 'onselected'),
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

    onselected: function(R) {
        //this.selected_resource = R;
        //this.resource.value = R.uri;
        //this.resource.type = R.resource_type;
        var increment = 20;

        if (this.resourcePreview) {
            this.setHeight( this.getHeight() - this.resourcePreview.getHeight() - increment);
            this.resourcePreview.destroy();
        }




        this.resourcePreview = Bisque.ResourceFactoryWrapper.getResource( {resource:R} );










        this.add(this.resourcePreview);
        this.setHeight( this.getHeight() + this.resourcePreview.getHeight() + increment );
        //this.fireEvent( 'changed', this, this.selected_resource );
        if (!this.validate()) return;
    },

    isValid: function() {
        var resource = this.resource;
        var template = resource.template || {};

        if (!this.selected_resource || !this.selected_resource.uri) {
            //BQ.ui.attention('You need to select an input resource!');
            BQ.ui.tip(this.getId(), 'You need to select an input resource!', {anchor:'left',});
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
        var sliderStep = template.stepSlider || ((template.allowDecimals && (!('setep' in template) || template.step>=1))?0.01:1.0);

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
                scope: this,
                change: function(field, value) {
                    if (!this.multivalue) {
                        this.resource.value = value;
                        if (this.numfield && this.numfield.getValue()!=value) this.numfield.setValue(value);
                        if (this.numlabel) this.numlabel.setText(value);
                    } else {
                        var vals = field.getValues();
                        for (var i=0; (v=this.resource.values[i]); i++)
                            v.value = vals[i];
                    }
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
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
                scope: this,
                change: function(field, value) {
                    this.resource.value = String(value);
                    if (this.slider && this.slider.getValue(0)!=value) this.slider.setValue(0, value);
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
            },

        });

        if (!this.multivalue && template.hideNumberPicker)
            this.numlabel = Ext.create('Ext.form.Label', { cls: 'numberlabel', width: 32, });

        if (this.numfield) this.items.push(this.numfield);
        if (this.slider) this.items.push(this.slider);
        if (this.numlabel) this.items.push(this.numlabel);
        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', flex: 2, });

        this.callParent();
    },

    select: function(resource) {
        var value = resource.value==undefined?resource.values:resource.value;
        if (this.slider) {
            if (value instanceof Array)
                for (var i=0; i<value.length; i++)
                    this.slider.setValue( i, value[i].value );
            else
                this.slider.setValue( 0, value );
        } else {
            this.numfield.setValue( value );
        }
    },

    isValid: function() {
        var valid = true;
        if (!this.multivalue && (this.resource.value===undefined || this.resource.value===null)) valid = false;
        if (this.multivalue)
            for (var i=0; (v=this.resource.values[i]); i++)
                valid = valid && v.value!==undefined && v.value!==null;

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
                scope: this,
                change: function(field, value) {
                    //value = parseInt(value, 10);
                    //field.setValue(value + value % 2);
                    this.resource.value = String(value);
                    this.value = String(value);
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
            },

        }];

        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', });

        this.callParent();
    },

    select: function(resource) {
        this.child('#textfield').setValue( resource.value );
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
                scope: this,
                select: function(field, value) {
                    this.resource.value = field.getValue();
                    this.value = this.resource.value;
                    this.fireEvent( 'changed', this, this.value );
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
            },

        });

        if (template.units)
            this.items.push({ xtype: 'container', html:'<label>'+template.units+'</label>', cls: 'units', });

        this.callParent();
    },

    select: function(resource) {
        this.resource.value = resource.value;
        this.child('#combobox').setValue( resource.value );
    },

    isValid: function() {
        var template = this.resource.template || {};

        if (Ext.isEmpty(this.resource.value) || this.resource.value==template.fail_value) {
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
            checked : resource.value,

            listeners: {
                scope: this,
                select: function(field, value) {
                    this.resource.value = field.getValue();
                    this.value = this.resource.value;
                },
                afterrender : function(o) {
                    o.tip = Ext.create('Ext.tip.ToolTip', {
                        target : o.getEl().getAttribute("id"),
                        html : template.description,
                    });
                },
            },

        });

        this.callParent();
    },

    select: function(resource) {
        this.child('#checkbox').setValue( resource.value );
    },

    isValid: function() {
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
                listeners: {
                    scope: this,
                    select: this.onselect,
                    afterrender : function(o) {
                        o.tip = Ext.create('Ext.tip.ToolTip', {
                            target : o.getEl().getAttribute("id"),
                            html : template.description,
                        });
                    },
                },

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
                listeners: {
                    scope: this,
                    select: this.onselect,
                    afterrender : function(o) {
                        o.tip = Ext.create('Ext.tip.ToolTip', {
                            target : o.getEl().getAttribute("id"),
                            html : template.description,
                        });
                    },
                },

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
        'export_package': 'createMenuExportPackage',
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
                var title = template[name+'/label']?template[name+'/label']:'Plot';
                if (title instanceof Array) title = title.join(', ');
                var titles = template[name+'/title'];
                if (!(titles instanceof Array)) titles = [titles];
                this.plotter = Ext.create('BQ.stats.Dialog', {
                    url     : this.res_uri_for_tools,
                    xpath   : template[name+'/xpath'],
                    xmap    : template[name+'/xmap'],
                    xreduce : template[name+'/xreduce'],
                    title   : title,
                    opts    : { args: {numbins: template[name+'/args/numbins']}, titles: titles, },
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
                var url = BQ.Server.url('/stats/csv?url=' + this.res_uri_for_tools);
                if (this.root) url = this.root + url;
                url += createStatsArgs('xpath', template, name);
                url += createStatsArgs('xmap', template, name);
                url += createStatsArgs('xreduce', template, name);
                url += createStatsArgs('title', template, name);
                if (template[name+'/filename'])
                    url += '&filename='+template[name+'/filename'];
                else if (this.res_for_tools)
                    url += '&filename='+this.res_for_tools.name+'.csv';
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
                window.open(this.res_uri_for_tools + '?view=deep,clean');
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
                window.open(BQ.Server.url('/export/to_gdocs?url='+this.res_uri_for_tools));
            },
        });
    },

    createMenuExportPackage : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if (!('export_package' in template) || template['export_package']==false) return;
        menu.add({
            text: 'complete document as a GZip package',
            scope: this,
            handler: function() {
                window.open(BQ.Server.url('/export/stream?compression=gzip&urls='+this.res_uri_for_tools + '?view=deep'));
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

    height: 600,
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

        // find image host root to use to form stats requests
        this.root = this.resource.uri.replace(/\/data_service\/.*$/i, '');
        this.gobjects = resource.gobjects;

        // create tools menus
        var tool_items = [];
        if (this.gobjects.length>0) {
            this.res_for_tools = this.resource;
            this.res_uri_for_tools = this.gobjects[0].uri;
            var gobs = this.definition.gobjects[0];
            this.template_for_tools = (gobs?gobs.template:{}) || {};
            tool_items = this.createTools();
        }
        Array.prototype.push.apply(tool_items, [{
            xtype: 'tbspacer',
            width: '30%',
        }, {
            itemId: 'button_view',
            xtype:'button',
            text: 'View: 2D',
            iconCls: 'view2d',
            needsAuth: false,
            tooltip: 'Change the view for the current image',
            scope: this,
            menu: {
                defaults: {
                    scope: this,
                },
                items: [{
                    xtype  : 'menuitem',
                    itemId : 'menu_view_2d',
                    text   : '2D',
                    iconCls: 'view2d',
                    handler: this.show2D,
                    tooltip: 'View current image in 2D tiled viewer',
                },{
                    xtype  : 'menuitem',
                    itemId : 'menu_view_3d',
                    text   : '3D',
                    disabled: true,
                    iconCls: 'view3d',
                    tooltip: 'View current image in 3D volume renderer',
                    handler: this.show3D,
                }, {
                    xtype  : 'menuitem',
                    itemId : 'menu_view_movie',
                    text   : 'movie',
                    disabled: true,
                    iconCls: 'movie',
                    tooltip: 'View current image as a movie',
                    handler: this.showMovie,
                }]
            },
        }]);

        this.items = [{
            xtype: 'label',
            html: template.label ? template.label : resource.name,
        }, {
            xtype: 'toolbar',
            itemId: 'bar_top',
            items: tool_items,
            hidden: tool_items.length==0,
            defaults: {
                scale: 'medium',
            },
        }, {
            xtype: 'container',
            itemId: 'main_container',
            flex: 2,
            layout: 'fit',
        }, {
            xtype: 'toolbar',
            itemId: 'bar_bottom',
            defaults: {
                scale: 'medium',
            },
            //items: [{
            //    xtype: 'button',
            //}],
            hidden: false,
        }];

        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        var resource = this.resource;
        this.queryById('main_container').add({
            xtype: 'imageviewer',
            itemId: 'main_view_2d',
            resource: resource.resource_type==='image' ? resource : resource.value, // reference or resource
            parameters: {
                simpleview: '',
                gobjects: this.gobjects,
                /*recolor: {
                    tag: 'confidence',
                    tag_bounds: [0, 100],
                    gradient: ['#000066', '#FFFF00'],
                },*/
            },
            listeners: {
                scope: this,
                loadedPhys: this.onPhysLoaded,
            },
        });

        this.toolbar = this.queryById('bar_top');
        this.viewerContainer = this.queryById('main_view_2d');
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
                var player = Ext.create('BQ.viewer.Movie.Dialog', {
                    resource: resource_uri,
                    gobjects: this.gobjects[0].uri,
                    //phys: this.viewerContainer.viewer.imagephys,
                    //preferences: this.viewerContainer.preferences
                });
            },
        });
    },

    createExportCsv : function(menu, name, template) {
        if (!this.res_uri_for_tools) return;
        menu.add({
            text: template[name+'/label']?template[name+'/label']:'as CSV',
            scope: this,
            handler: function() {
                var url = BQ.Server.url('/stats/csv?url=' + this.res_uri_for_tools);
                if (this.root) url = this.root + url;
                url += createStatsArgs('xpath', template, name);
                url += createStatsArgs('xmap', template, name);
                url += createStatsArgs('xreduce', template, name);
                url += createStatsArgs('title', template, name);
                if (template[name+'/filename'])
                    url += '&filename='+template[name+'/filename'];
                else if (this.res_for_tools)
                    url += '&filename='+this.viewerContainer.viewer.image.name+'.csv';
                window.open(url);
            },
        });
    },

    onPhysLoaded : function(viewer, phys, dims) {
        this.viewerContainer.viewer.setGobTolerance({ z: 3.0, t: 1.0 });
        if (dims.t>1 || dims.z>1)
            this.queryById('menu_view_movie').setDisabled( false );
        if (dims.t>1 || dims.z>1)
            this.queryById('menu_view_3d').setDisabled( false );

        if (!BQ.util.isWebGlAvailable()) {
            var button3D = this.queryById('menu_view_3d');
            button3D.setText('3D (WebGl not available)');
            button3D.setTooltip('Enable WebGl to access viewer.');
            button3D.setDisabled( true );
        }
    },

    show2D : function() {
        var btn = this.queryById('button_view');
        btn.setText('View: 2D');
        btn.setIconCls('view2d');

        var image2d = this.queryById('main_view_2d');
        if (image2d && image2d.isVisible()) return;

        var movie = this.queryById('main_view_movie');
        if (movie) {
            movie.setVisible(false);
            movie.destroy();
        }

        var image3d = this.queryById('main_view_3d');
        if (image3d) {
            image3d.setVisible(false);
            image3d.destroy();
        }

        image2d.setVisible(true);
    },

    showMovie : function() {
        var btn = this.queryById('button_view');
        btn.setText('View: Movie');
        btn.setIconCls('movie');

        var movie = this.queryById('main_view_movie');
        if (movie && movie.isVisible()) return;

        var image2d = this.queryById('main_view_2d');
        if (image2d) {
            image2d.setVisible(false);
            //image2d.destroy(); // do not destroy to really fast return
        }

        var image3d = this.queryById('main_view_3d');
        if (image3d) {
            image3d.setVisible(false);
            image3d.destroy();
        }

        var cnt = this.queryById('main_container');
        cnt.add({
            xtype: 'bq_movie_viewer',
            itemId: 'main_view_movie',
            resource: this.viewerContainer.viewer.image, // reference or resource
            toolbar: this.toolbar,
            phys: this.viewerContainer.viewer.imagephys,
            preferences: this.viewerContainer.viewer.preferences,
        });

    },

    show3D : function() {
        var me = this;
        var btn = this.queryById('button_view');
        btn.setText('View: 3D');
        btn.setIconCls('view3d');

        var image3d = this.queryById('main_view_3d');
        if (image3d && image3d.isVisible()) return;

        var image2d = this.queryById('main_view_2d');
        if (image2d) {
            image2d.setVisible(false);
            //image2d.destroy(); // do not destroy to really fast return
        }

        var movie = this.queryById('main_view_movie');
        if (movie) {
            movie.setVisible(false);
            movie.destroy();
        }

        this.queryById('main_container').add({
            //region : 'center',
            xtype: 'bq_volume_panel',
            itemId: 'main_view_3d',
            resource: this.viewerContainer.viewer.image,
            toolbar: this.toolbar,
            phys: this.viewerContainer.viewer.imagephys,
            preferences: this.viewerContainer.viewer.preferences,
            listeners: {
                glcontextlost: function(event){
                    var msgText = " ";
                    var link = " mailto:me@example.com"
                        + "?cc=myCCaddress@example.com"
                        + "&subject=" + escape("This is my subject")
                        + "&body=" + msgText + "";

                    BQ.ui.error("Hmmm... WebGL seems to hit a snag: <BR/> " +
                                "error: " + event.statusMessage +
                                "<BR/>Do you want to report this problem?" +
                                "<a href = " + link + "> send mail </a>");

                    var image3d = me.queryById('main_view_3d');
                    var toolMenu = image3d.toolMenu;
                    toolMenu.destroy();
                    image3d.destroy();
                    //this should destroy the 3D viewer
                    me.show2D();
                },

            }
        });
    },

    reRenderGobs : function() {
        var image3d = this.queryById('main_view_3d');
        if (image3d && image3d.isVisible()) {
            image3d.updateGobs();
        } else {
            this.viewerContainer.rerender();
        }
    },

});


/*******************************************************************************
File templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.File', {
    alias: 'widget.rendererfile',
    extend: 'BQ.renderers.Renderer',
    //requires: ['Bisque.ResourceBrowser.Browser'],

    height: 80,
    layout: {
        type: 'vbox',
        pack  : 'start',
    },
    defaults: { border: null, },

    initComponent : function() {
        var definition = this.definition;
        var template = definition.template || {};
        var resource = this.resource;
        if (!definition || !resource) return;
        template.label = template.label || 'Output file';

        if (resource.resource_type == 'tag' && resource.type == 'file') {
            BQFactory.request( { uri: resource.value,
                                 cb:  callback(this, 'onFile'), });
        }

        this.items = [];
        this.items.push( {xtype: 'label', html: template.label, } );
        this.callParent();
    },

    onFile : function(r) {
        this.file = r;
        this.add({
            xtype: 'button',
            text: 'Download "<b>'+this.file.name+'</b>"',
            iconCls: 'download',
            scale: 'large',
            //cls: 'x-btn-default-large',
            //tooltip: 'Download',
            handler: Ext.Function.bind( this.download, this ),
        });
    },

    download : function() {
        window.open(this.file.src);
    },

});

/*******************************************************************************
Dataset templated configs:

events:
    selected
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
            BQFactory.request({
                uri: resource,
                cb:  callback(this, 'initBrowser'),
                uri_params: {view:'deep'},
            });
        } else if (resource.resource_type == 'tag' && resource.type == 'dataset') {
            BQFactory.request({
                uri: resource.value,
                cb:  callback(this, 'initBrowser'),
                uri_params: {view:'deep'},
            });
        } else {
            this.initBrowser(resource);
        }
    },

    initBrowser: function(resource) {
        //resource: resource.resource_type=='image'?resource:resource.value, // reference or resource
        this.browser = Ext.create('Bisque.ResourceBrowser.Browser', {
            //dataset: resource,
            dataset: resource.uri+'/value',
            selType: 'SINGLE',
            flex: 1,
            cls: 'bordered',
            viewMode : 'ViewerOnly',
            listeners: {
                scope: this,
                Select: function(me, resource) {
                    this.fireEvent('selected', resource);
                },
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

    height: 80,
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
        template.label = template.label || 'Summary of this analysis';

        this.items = [];
        this.items.push( {xtype: 'label', html: template.label, } );

        if (template.mode == 'browser') {
            // in this mode we browse a MEX and show its sub-MEXs
            this.browser = Ext.create('Bisque.ResourceBrowser.Browser', {
                dataset: resource.value + '?view=full',
                selType: 'SINGLE',
                flex: 1,
                cls: 'bordered',
                //viewMode : 'ViewerOnly',
                viewMode : 'ViewerLayouts',
                //layout:
                listeners: {
                    'Select': function(me, resource) {
                        this.fireEvent( 'selected', resource);
                    },
                    scope: this
                },
            });
            this.setHeight(450);
            this.items.push(this.browser);
        } else {
            // this is a default mode where we show export menus
            // create tools menus
            var tool_items = [];
            this.res_for_tools = {name: resource.resource_type+'.csv', };
            this.res_uri_for_tools = resource.value;
            this.template_for_tools = template;
            tool_items = this.createTools();

            if (tool_items.length>0)
                this.items.push( {xtype: 'toolbar', items: tool_items, defaults: { scale: 'medium' }, } );
        }
        this.callParent();
    },

});

/*******************************************************************************
Mex templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.Browser', {
    alias: 'widget.rendererbrowser',
    extend: 'BQ.renderers.Renderer',
    requires: ['Bisque.ResourceBrowser.Browser'],

    height: 400,
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

        this.browser = Ext.create('Bisque.ResourceBrowser.Browser', {
            dataset: template.path,
            selType: 'SINGLE',
            viewMode : 'ViewerOnly',
            tagQuery : resource.value,
            wpublic  : 'true',
            flex: 1,
            cls: 'bordered',
            listeners: { 'Select': function(me, resource) {
                           window.open(BQ.Server.url('/client_service/view?resource='+resource.uri));
                           },
                        scope: this
            },
        });
        this.items.push(this.browser);
        this.callParent();
    },

});


/*******************************************************************************
Table templated configs:

*******************************************************************************/

Ext.define('BQ.renderers.Table', {
    alias: 'widget.renderertable',
    extend: 'BQ.renderers.Renderer',

    height: 400,
    layout: {
        type: 'vbox',
        align : 'stretch',
        pack  : 'start',
    },
    defaults: { border: null, },

    initComponent : function() {
        var definition = this.definition;
        var template = definition.template || {};
        var resource = this.resource;
        if (!definition || !resource) return;
        template.label = template.label || 'Table file';

        if (resource.resource_type == 'tag' && resource.type == 'table') {
            BQFactory.request( { uri: resource.value,
                                 cb:  callback(this, 'onFile'), });
        }

        this.items = [];
        this.items.push( {xtype: 'label', html: template.label, } );
        this.callParent();
    },

    onFile : function(r) {
        this.resource = r;
        this.add({
            xtype: 'toolbar',
            height: 50,
            border: 0,
            items: [{
                xtype: 'button',
                text: 'Download "<b>'+this.resource.name+'</b>"',
                iconCls: 'download',
                scale: 'large',
                //cls: 'x-btn-default-large',
                //tooltip: 'Download',
                handler: Ext.Function.bind( this.download, this ),
            }],
        }, {
            xtype: 'tbspacer',
            height: 10,
        }, {
            xtype: 'bq_table_panel',
            flex: 2,
            border: 0,
            resource: this.resource,
        });

    },

    download : function() {
        window.open(this.resource.src);
    },

});

