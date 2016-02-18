/*******************************************************************************
Author: Dmitry Fedorov
Copyright: 2015 (C) Center for Bio-Image Informatics, University of California at Santa Barbara

Exportable classes:
    BQ.table.Panel - renders the table resource
    BQ.table.View - renders a given sub-table of a table resource

Browser components:
    Bisque.Resource.Table.Page
    ...
    Bisque.Resource.Table.Grid

*******************************************************************************/

Ext.namespace('BQ.data');
Ext.namespace('BQ.table');
BQ.data.pageSize = 500;

Ext.require([
    'Ext.grid.*',
    'Ext.data.*',
    'Ext.util.*',
    'Ext.grid.plugin.BufferedRenderer'
]);

//--------------------------------------------------------------------------------------
// Table json proxy
//--------------------------------------------------------------------------------------

Ext.define('BQ.data.proxy.Table', {
    extend: 'Ext.data.proxy.Ajax',
    alternateClassName: 'BQ.data.TableProxy',
    alias : 'proxy.bq-table',

    noCache : false,
    batchActions: false,

    pageParam: undefined,
    startParam: undefined,
    limitParam: undefined,

    actionMethods: {
        create : 'POST',
        read   : 'GET',
        update : 'PUT',
        destroy: 'DELETE'
    },

    buildUrl: function(request) {
        var me        = this,
            operation = request.operation,
            records   = operation.records || [],
            record    = records[0],
            format    = me.format,
            url       = me.getUrl(request),
            id        = record ? record.getId() : operation.id;

        if (operation.limit>1) {
            url += '/'+operation.start+';'+(operation.start+operation.limit-1);
        } else if (operation.limit==1) {
            url += '/'+operation.start;
        }
        url += '/format:json';
        request.url = url;
        return me.callParent(arguments);
    },

});

//--------------------------------------------------------------------------------------
// Table json reader
//--------------------------------------------------------------------------------------

Ext.define('BQ.data.reader.Table', {
    extend: 'Ext.data.reader.Json',
    alternateClassName: 'BQ.data.TableReader',
    alias : 'reader.bq-table',

    pageSize: BQ.data.pageSize,

    readRecords: function(data) {
        var me = this;
        if (data.table && data.table.length >= me.pageSize) {
            data.total = data.table.length + me.pageSize;
            data.total += data.offset || 0;
        } else if (data.table) {
            data.total = data.table.length;
            data.total += data.offset || 0;
        }
        return me.callParent([data]);
    },
});

//--------------------------------------------------------------------------------------
// Table grid view - renders actual grid content for one given table
// required parameters:
//     resource - the table resource
//     path - sub table path
//--------------------------------------------------------------------------------------

BQ.table.encodeURIpath = function(p) {
    p = encodeURIComponent(p).replace('%2F', '/');
    if (p[0] == '/') return p; else return '/'+p;
}

Ext.define('BQ.table.View', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_table_view',
    cls: 'bq_table_view',
    layout: 'fit',

    initComponent : function() {
        // temporary columns and store needed to init empty gridpanel without errors
        this.store = Ext.create('Ext.data.Store', {
            fields:['name'],
            data:{ 'items': [{ 'name': '' }, ]},
            proxy: {
                type: 'memory',
                reader: {
                    type: 'json',
                    root: 'items'
                }
            }
        });

        // create view components: grid and tagger
        this.items = [{
            xtype: 'gridpanel',
            itemId  : 'table',
            autoScroll: true,
            border: 0,
            viewConfig: {
                stripeRows: true,
                forceFit: true,
            },
            plugins: 'bufferedrenderer',
            store: this.store,
            columns: [
                { text: '',  dataIndex: 'name' },
            ],
        }];

        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        if (this.info) {
            this.onTableInfo();
            return;
        }

        // load table info to configure columns and the store
        //this.setLoading('Fetching table info...');
        Ext.Ajax.request({
            url: '/table/' + this.resource.resource_uniq + BQ.table.encodeURIpath(this.path)+ '/info/format:json',
            callback: function(opts, succsess, response) {
                if (response.status>=400 || !succsess)
                    BQ.ui.error(response.responseText);
                else
                    this.onTableInfo(response.responseText);
            },
            disableCaching: false,
            scope: this,
            listeners: {
                scope: this,
                beforerequest   : function() { this.setLoading('Loading table...'); },
                requestcomplete : function() { this.setLoading(false); },
                requestexception: function() { this.setLoading(false); },
            },
        });
    },

    onTableInfo: function(txt) {
        //this.setLoading(false);
        var json = this.info,
            h = null;
        if (!this.info && txt) {
            json = Ext.JSON.decode(txt);
        }
        this.fields = [];
        this.columns = [];
        for (var i=0; i<json.headers.length; ++i) {
            var h = json.headers[i],
                t = json.types[i],
                tt = 'string';

            if (t.indexOf('int')>=0)
                tt = 'int';
            else if (t.indexOf('float')>=0)
                tt = 'float';

            this.fields.push({
                name: i, // need to use numbers for reading from json array
                type: tt,
                useNull: true,
            });

            this.columns.push({
                text: h,
                flex: 1,
                dataIndex: i, // need to use numbers for reading from json array
                //sortable: true,
                autoSizeColumn : true,
            });
        }

        this.store = Ext.create('Ext.data.Store', {
            autoLoad: true,
            autoSync: true,
            fields: this.fields,

            buffered: true,
            leadingBufferZone: 100, // 300
            pageSize: BQ.data.pageSize,

            proxy: {
                //type: 'rest',
                type: 'bq-table',
                url: '/table/' + this.resource.resource_uniq, // + '/format:json',
                //noCache : false,
                //pageParam: undefined,
                //startParam: undefined,
                //limitParam: undefined,
                reader: {
                    type: 'bq-table', // 'json',
                    root: 'table'
                },
                //writer: {
                //    type: 'json'
                //}
            },
        });
        var table = this.queryById('table');
        table.reconfigure(this.store, this.columns);
    },

});


//--------------------------------------------------------------------------------------
// Table viewer - renders all tables present in the table resource
// required parameters:
//     resource - the table resource
//--------------------------------------------------------------------------------------

Ext.define('BQ.table.Panel', {
    extend: 'Ext.tab.Panel',
    alias: 'widget.bq_table_panel',
    cls: 'bq_table_panel',
    deferredRender: true,
    activeTab : 0,
    plain : true,

    initComponent : function() {
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        // load table info to configure columns and the store
        //this.setLoading('Fetching table info...');
        Ext.Ajax.request({
            url: '/table/' + this.resource.resource_uniq + '/info/format:json',
            callback: function(opts, succsess, response) {
                if (response.status>=400 || !succsess)
                    BQ.ui.error(response.responseText);
                else
                    this.onTableInfo(response.responseText);
            },
            disableCaching: false,
            scope: this,
            listeners: {
                scope: this,
                beforerequest   : function() { this.setLoading('Loading table...'); },
                requestcomplete : function() { this.setLoading(false); },
                requestexception: function() { this.setLoading(false); },
            },
        });
    },

    onTableInfo: function(txt) {
        this.setLoading(false);
        var json = Ext.JSON.decode(txt);
        this.tables = json.tables;
        if (this.tables && this.tables.length>1) {
            var p=undefined,
                i=undefined;
            for (i=0; (p=this.tables[i]); ++i) {
                this.add({
                    xtype: 'bq_table_view',
                    border: 0,
                    resource: this.resource,
                    path: p,
                    title: p,
                });
            }
        } else {
            this.add({
                xtype: 'bq_table_view',
                border: 0,
                resource: this.resource,
                path: p,
                info: json,
            });
            this.getTabBar().hide();
        }
    },

});

//--------------------------------------------------------------------------------------
// Resource renderer
//--------------------------------------------------------------------------------------

Ext.define('Bisque.Resource.Table.Page', {
    extend : 'Bisque.Resource.Page',

    initComponent : function() {
        this.addCls('tableio');
        this.callParent();
    },

    downloadOriginal : function() {
        if (this.resource.src) {
            window.open(this.resource.src);
            return;
        }
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },

    onResourceRender : function() {
        // create view components: grid and tagger
        this.add({
            xtype : 'container',
            itemId: 'main_container',
            layout : 'border',
            items : [{
                xtype: 'tabpanel',
                itemId: 'tabs',
                title : 'Metadata',
                deferredRender: true,
                region : 'east',
                activeTab : 0,
                border : false,
                bodyBorder : 0,
                collapsible : true,
                split : true,
                width : 400,
                plain : true,
                items : [{
                    xtype: 'bq-tagger',
                    resource : this.resource,
                    title : 'Annotations',
                }, {
		            xtype : 'bq_graphviewer_panel',
		            itemId: 'graph',
		            title : 'Provenance',
		            resource: this.resource,
		            listeners:{
		                'context' : function(res, div, graph) {
		                    var node = graph.g.node(res);
		                    if(node.card.cardType=='mex'){
		                        window.open(BQ.Server.url('/module_service/MetaData' + '/?mex=/data_service/' + res));

		                    }
		                    if(node.card.cardType=='image' || node.card.cardType=='table'){
		                        window.open(BQ.Server.url('/client_service/view?resource=/data_service/' + res));

		                    }
		                },
		            },
		            resource : this.resource,
		        }]
            }, {
                xtype: 'bq_table_panel',
                flex: 2,
                region : 'center',
                border: 0,
                resource: this.resource,
                //path: '',
            }],
        });
        //this.toolbar.doLayout();
    },
});

Ext.define('Bisque.Resource.Table.Compact', {
    extend : 'Bisque.Resource.Compact',
    initComponent : function() {
        this.addCls(['resicon', 'table']);
        this.callParent();
    },

});

Ext.define('Bisque.Resource.Table.Card', {
    extend : 'Bisque.Resource.Card',
    initComponent : function() {
        this.addCls('table');
        this.callParent();
    },
});

Ext.define('Bisque.Resource.Table.Full', {
    extend : 'Bisque.Resource.Full',
    initComponent : function() {
        this.addCls('table');
        this.callParent();
    },
});

Ext.define('Bisque.Resource.Table.Grid', {
    extend : 'Bisque.Resource.Grid',

    initComponent : function() {
        this.addCls(['resicon', 'table']);
        this.callParent();
    },

    getFields : function(cb) {
        var fields = this.callParent();
        fields[0] = '<div class="resicon gridIcon table" />';
        return fields;
    },
});
