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
      loadedPhys - event fired when image physics is loaded
      working
      done
      error
      delete     - event fired when gobject(s) is(are) deleted
      moveend    - event fired when mouse up on selected gobject
      afterPhys  - event fired after phys is loaded

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
    gobjectDeleted
    gobjectCreated

    gobjectMove      - returns shape object when manipulating a gobject, shape object has pointer to gob
    gobjectMoveStart - returns shape object when beginning a gobject manipulation, shape object has pointer to gob
    gobjectMoveEnd   - returns shape object when ending a gobject manipulation, shape object has pointer to gob

    blockforsaves  - set to true to show saving of gobjects, def: true
    showmanipulators - turns off advanced manipulators in the canvas renderer
       jrd: this should really be more advanced and allow you to customize what options you want to show on
            the renderer ie: toggle shape corners, manipulators, bounding boxes, debugging tree, etc

  Example:
    var myviewer = Ext.create('BQ.viewer.Image', {
        resource: 'http://image_url',
        user: 'user_name',
        parameters: {
            'gobjects': 'http://gobejcts_url',
            'noedit': '',
        },
    });


        var buttons = [{
            itemId: 'btnCreate',
            text: 'Create custom',
            scale: 'medium',
            iconCls: 'icon-add',
            handler: this.createComplexGobject,
            scope: this,
            tooltip: 'Create a new custom graphical annotation wrapping any primitive annotation',
        }];


*******************************************************************************/

Ext.define('BQ.editor.GraphicalSelector', {
    alias: 'widget.graphicalselector',
    extend: 'Ext.Component',
    componentCls: 'bq-editor-selector',
    //componentCls: 'editmenu',

    border: false,
    layout: 'fit',
    autoEl: {
        tag: 'div',
    },

    initComponent : function() {
        //init
        this.callParent();
        this.editprimitives = this.editprimitives || BQGObject.primitives;
    },

    onDestroy : function(){
        // clenup
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.getEl().on('click', this.onMenuToggle, this );
        // do stuff
    },

    createMenu: function() {
        if (this.menu) return;
        var buttons = [];
        for (var p in BQGObject.primitives)
            buttons.push({
                xtype: 'button',
                itemId: 'btn_'+p,
                hidden: !(p in this.editprimitives),
                cls: p,
                primitive: p,
                //text: p,
                //flex: 1,
                tooltip: BQGObject.primitives[p],
                scope: this,
                handler: this.onPrimitive,
                toggleGroup: 'Primitives',
                allowDepress: false,
            });

        buttons[0].pressed = true;
        this.primitive = buttons[0].primitive;

        var items = [{
            xtype: 'tbtext',
            cls: 'bq-gob-header',
            //itemId: 'GobsHeader',
            text: 'Selected graphical annotation:',
        }, {
            xtype: 'toolbar',
            border: false,
            cls: 'primitives',
            items: buttons,
            scale: 'large',
        }, {
            xtype: 'tbspacer',
            height: 15,
        }, {
            xtype: 'tbtext',
            cls: 'bq-gob-header',
            //itemId: 'GobsHeader',
            text: 'Semantic annotation:',
        }, {
            xtype: 'toolbar',
            border: false,
            scale: 'large',
            items: [{
                itemId: 'btnCreate',
                text: 'Add new semantic type',
                scale: 'large',
                iconCls: 'add',
                handler: this.createComplexGobject,
                scope: this,
                tooltip: 'Create a new custom graphical annotation wrapping any primitive annotation',
            }],
        }, {
            xtype: 'gobspanel',
            itemId: 'semanticTypesPanel',
            border: 0,
            flex: 10,
            listeners: {
                scope: this,
                select: this.onSemantic,
            },
        }];

        this.menu = Ext.create('Ext.tip.ToolTip', {
            target: this.getEl(),
            anchor: 'top',
            anchorToTarget: true,
            cls: 'bq-editor-menu',
            //minWidth: 460,
            width: 460,
            height: Math.round(BQApp?BQApp.getCenterComponent().getHeight()*0.98:document.height*0.98),
            anchorOffset: -5,
            autoHide: false,
            shadow: false,
            closable: true,
            layout: {
                type: 'vbox',
                align: 'stretch',
                pack: 'start',
            },
            defaults: {
                labelSeparator: '',
                labelWidth: 200,
                width: 100,
            },
            items: items,
        });

    },

    onMenuToggle : function() {
        this.createMenu();
        var m = this.menu;
        if (m.isVisible())
            m.hide();
        else
            m.show();
    },

    createComplexGobject: function () {
        Ext.MessageBox.prompt('Create new graphical type', 'Please enter a new graphical type:', this.onNewType, this);
    },

    onNewType: function (btn, mytype) {
        if (btn !== 'ok') return;
        var p = this.menu.queryById('semanticTypesPanel');
        if (p)
            p.addType(mytype);
    },

    onPrimitive: function (btn) {
        this.removeCls(this.primitive);
        this.addCls(btn.primitive);
        this.primitive = btn.primitive;
        this.onSelected();
    },

    onSemantic: function (type) {
        this.semantic = type;
        this.onSelected();
    },

    onSelected: function () {
        if (this.menu)
            this.menu.hide();
        this.fireEvent( 'selected', this.primitive, this.semantic, this );
    },

    setSelected: function(selected) {
        if (selected)
            this.addCls('selected');
        else
            this.removeCls('selected');
    },

    /*setSelected: function(selected) {
        el.disabled = disabled;
        if(disabled)
            el.dom.style.opacity = 0.25;
        else
            el.dom.style.opacity = 1.0;
    },*/

});

//-----------------------------------------------------------------------
// BQ.grid.GobsPanel
//-----------------------------------------------------------------------

function getType(v, record) {
    var r = BQ.util.xpath_string(record.raw, '@type') || record.raw.nodeName;
    return r;
}

Ext.define('BQ.grid.GobsPanel', {
    alias: 'widget.gobspanel',
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],
    layout: 'fit',

    types_ignore: {},

    initComponent : function() {
        /*
        Ext.define('Gobs', {
            extend : 'Ext.data.Model',
            fields : [
                { name: 'Type', convert: getType },
                //{ name: 'Name', mapping: '@name' },
                { name: 'Custom', mapping: '@type' },
            ],

            proxy : {
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                type: 'ajax',
                url : '/data_service/image/?gob_types=true&wpublic=false',
                reader : {
                    type :  'xml',
                    root :  '/',
                    record: '/*:not(value or vertex or template)',
                }
            },

        });
        */
        this.typesstore = Ext.create('Ext.data.Store', {
            fields : [
                { name: 'Type' },
                { name: 'Custom' },
            ],
            sorters: [{
                property: 'Type',
                direction: 'ASC',
                transform: function(v) { return v.toLowerCase(); },
            }]
        });

        this.items = [{
            xtype: 'gridpanel',
            itemId: 'gob_types_panel',
            header: false,
            hideHeaders: true,
            allowDeselect: true,
            /*store: {
                model : 'Gobs',
                autoLoad : true,
                autoSync : false,
            },*/
            store: this.typesstore,
            border: 0,
            columns: [{
                text: "Type",
                flex: 1,
                dataIndex: 'Type',
                sortable: true,
            }],
            viewConfig: {
                stripeRows: true,
                forceFit: true,
                getRowClass: function(record, rowIndex, rowParams, store){
                    if (record.data.Custom != '')
                        return 'bq-row-gob-custom';
                },
            },
            listeners: {
                scope: this,
                //select: this.onselected,
                selectionchange: this.onchanged,
            }
        }];

        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.setLoading('Fetching types of graphical annotations');
        var me = this;
        BQ.Preferences.on('update_user_pref', function(el, resourcePrefXML){
            me.onPreferences(); //update preferences
        });
        this.onPreferences();
    },

    onPreferences: function() {
        this.preferences = {};
        this.preferences.hide_gobjects_creation = BQ.Preferences.get('user','Viewer/hide_gobjects_creation','');
        this.preferences = Ext.apply(this.preferences, this.parameters || {});
        if (this.preferences.hide_gobjects_creation) {
            var l = this.preferences.hide_gobjects_creation.split(',');
            var n=null;
            for (var i=0; n=l[i]; ++i)
                this.types_ignore[n] = n;
        }

        Ext.Ajax.request({
            url: '/data_service/image/?gob_types=true&wpublic=false',
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
        BQ.ui.error('Problem fetching available gobject types');
    },

    onTypes : function(xml) {
        this.setLoading(false);
        this.types = [];
        //this.types_index = {};

        // add primitives
        /*for (var g in BQGObject.primitives) {
            if (!(g in this.types_ignore)){
                var ix = this.types.push({
                    Type   : g,
                    Custom : '',
                });
            }
            //this.formats_index[name] = this.formats[ix-1];
        } // for primitives
        */

        var gobs = BQ.util.xpath_nodes(xml, '//gobject');
        var g=undefined;
        for (var i=0; g=gobs[i]; ++i) {
            var t = g.getAttribute('type');
            if (!(t in this.types_ignore)){
                var ix = this.types.push({
                    Type   : t,
                    Custom : t,
                });
            }
            //this.formats_index[name] = this.formats[ix-1];
        } // for types

        this.typesstore.loadData(this.types);
    },

    addType: function(newType) {
        var ix = this.types.push({
            Type   : newType,
            Custom : newType,
        });
        this.typesstore.loadData(this.types);

        // select added type
        var grid = this.queryById('gob_types_panel'),
            id = this.typesstore.find('Type', newType);
        grid.getSelectionModel().select(id);
    },

    onselected: function(model, record, index, eOpts) {
        this.fireEvent('select', record.data.Type);
    },

    onchanged: function(me, selected, eOpts) {
        if (selected.length == 0)
            this.fireEvent('select', null);
        else
            this.fireEvent('select', selected[0].data.Type);
    },

    deselect: function() {
        var grid = this.queryById('gob_types_panel');
        if (grid) grid.getSelectionModel().deselectAll();
    },
});


