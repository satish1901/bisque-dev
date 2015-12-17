/*******************************************************************************
  BQ.viewer.MenuButton - base class for button-based viewer menus
  BQ.editor.GraphicalSelector - Graphical annotations menu

  Author: Dima Fedorov <dima@dimin.net>

  Configurations:
    widget : main extjs component holding the component
             needed in order to implement proper hiding
    editprimitives: primitives config from the viewer, constraints visibility
    no_semantic_types: if true hides the gobject types list

  Events:
    this.fireEvent( 'selected', this.primitive, this.semantic, this );

*******************************************************************************/

//-----------------------------------------------------------------------
// BQ.viewer.MenuButton - base class for button-based viewer menus
//-----------------------------------------------------------------------

Ext.define('BQ.viewer.MenuButton', {
    alias: 'widget.viewer_menubutton',
    extend: 'Ext.Component',
    componentCls: 'bq-viewer-button',

    border: false,
    layout: 'fit',
    autoEl: {
        tag: 'div',
    },

    afterRender : function() {
        this.callParent();
        this.onPreferences();
        this.createMenu();
        BQ.Preferences.on('update_user_pref', this.onPreferences, this);
        this.getEl().on('click', this.onMenuToggle, this );
        if (this.widget)
            this.widget.on('hide', this.onHide, this );
        else
            this.on('hide', this.onHide, this );
    },

    onHide : function() {
        if (this.menu)
            this.menu.hide();
    },

    onMenuToggle: function(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        this.createMenu();
        var m = this.menu;
        if (m.isVisible())
            m.hide();
        else
            m.show();
    },

    // methods to override

    onPreferences: function() {
        //this.auto_hide = BQ.Preferences.get('user','Viewer/gobjects_editor_auto_hide', true);
    },

    createMenu: function() {
        /*if (this.menu) return;
        this.menu = Ext.create('Ext.tip.ToolTip', {
            target: this.getEl(),
            anchor: 'left',
            anchorToTarget: true,
            anchorOffset: 4,
            cls: 'bq-editor-menu',
            width: 380,
            height: 400,
            autoHide: false,
            shadow: false,
            closable: true,
            layout: {
                type: 'vbox',
                align: 'stretch',
                pack: 'start',
            },
            items: {},
        });*/
    },

});

//-----------------------------------------------------------------------
// BQ.editor.GraphicalSelector - Graphical annotations menu
//-----------------------------------------------------------------------

Ext.define('BQ.editor.GraphicalMenu', {
    extend: 'BQ.viewer.MenuButton',
    alias: 'widget.viewer_menu_graphical',
    componentCls: 'bq-editor-selector',

    initComponent : function() {
        this.callParent();
        this.editprimitives = this.editprimitives || BQGObject.primitives;
    },

    createMenu: function() {
        if (this.menu) return;
        var buttons = [],
            el = this.getEl(),
            offset = el.getY(),
            h = 90;

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
            text: 'Graphical annotations:',
        }, {
            xtype: 'toolbar',
            border: false,
            cls: 'primitives',
            items: buttons,
            scale: 'large',
        }];

        if (this.no_semantic_types !== true) {
            items = items.concat([{
                xtype: 'tbspacer',
                height: 10,
            }, {
                xtype: 'toolbar',
                border: false,
                scale: 'large',
                items: [{
                    xtype: 'tbtext',
                    cls: 'bq-gob-header',
                    //itemId: 'GobsHeader',
                    text: 'Semantic types:',
                }, '->', {
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
            }]);
            h = Math.round(BQApp?BQApp.getCenterComponent().getHeight()-offset:document.height-offset);
        }

        this.menu = Ext.create('Ext.tip.ToolTip', {
            target: el,
            anchor: 'left',
            anchorToTarget: true,
            anchorOffset: 4,
            cls: 'bq-editor-menu',
            width: 380,
            height: h,
            autoHide: false,
            shadow: false,
            closable: true,
            layout: {
                type: 'vbox',
                align: 'stretch',
                pack: 'start',
            },
            /*defaults: {
                labelSeparator: '',
                labelWidth: 200,
                width: 100,
            },*/
            items: items,
        });

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
        if (this.menu && this.auto_hide === true)
            this.menu.hide();
        this.fireEvent( 'selected', this.primitive, this.semantic, this );
    },

    setSelected: function(selected) {
        if (selected)
            this.addCls('selected');
        else
            this.removeCls('selected');
    },

    onPreferences: function() {
        this.auto_hide = BQ.Preferences.get('user','Viewer/gobjects_editor_auto_hide', true);
    },

});

//-----------------------------------------------------------------------
// BQ.grid.GobsPanel - list view of available gobjects types
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
        BQ.Preferences.on('update_user_pref', this.onPreferences, this);
        this.onPreferences();
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
        this.onTypes();
    },

    onError : function() {
        this.setLoading(false);
        BQ.ui.error('Problem fetching available gobject types');
    },

    onTypes : function(xml) {
        xml = xml || this.xml;
        if (!xml) return;
        this.xml = xml;
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


