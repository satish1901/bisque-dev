Ext.define('Bisque.DatasetBrowser.Dialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.bq-dataset-dialog',
    modal : true,
    border : false,
    width : '85%',
    height : '85%',
    layout: 'fit',
    buttonAlign: 'center',

    constructor : function(config) {
        Ext.apply(this, {
            title : config.title || 'Select a dataset...',
            items : [{
                xtype: 'bq-dataset-browser',
                itemId: 'browser-dataset',
            }],
            buttons: [{
                text: 'Select',
                iconCls : 'icon-select',
                scale: 'large',
                scope: this,
                width: 100,
                handler: this.onDone,
            }, {
                text: 'Close',
                iconCls : 'icon-cancel',
                scale: 'large',
                scope: this,
                width: 100,
                handler: this.close,
            }],
        }, config);

        this.callParent([arguments]);
        this.show();
    },

    onDone: function() {
        var browser = this.queryById('browser-dataset');
        if (browser.selected_dataset) {
            this.fireEvent( 'DatasetSelect', this, browser.selected_dataset );
            this.close();
        }
    },

});

Ext.define('Bisque.DatasetBrowser.Browser', {
    extend : 'Ext.panel.Panel',
    alias: 'widget.bq-dataset-browser',
    layout: 'border',

    constructor : function(config) {
        Ext.apply(this, {
            items : [{
                xtype: 'bq-resource-browser',
                itemId: 'browser-dataset',
                region: 'west',
                split: true,
                title: 'Dataset browser',
                flex: 3,
                'dataset' : '/data_service/dataset',
                selType: 'SINGLE',
                showOrganizer : false,
                listeners : {
                    'Select' : this.onSelect,
                    scope : this
                },
            }, {
                xtype: 'bq-resource-browser',
                itemId  : 'browser-preview',
                region: 'center',
                showOrganizer : false,
                'dataset' : 'None',
                layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact,
                viewMode: 'ViewerOnly',
                title: 'Dataset preview',
                flex: 1,
            }],
        }, config);

        this.callParent([arguments]);
    },

    onSelect: function(me, resource) {
        this.selected_dataset = resource;
        var preview = this.queryById('browser-preview');
        preview.loadData({
            baseURL: resource.uri + '/value',
            offset: 0,
            tag_order: '"@ts":desc',
            tag_query: '',
        });
        this.fireEvent('Select', this, this.selected_dataset);
    },

});
