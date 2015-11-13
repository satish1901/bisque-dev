/*******************************************************************************
Author: Dmitry Fedorov
Copyright: 2015 (C) Center for Bio-Image Informatics, University of California at Santa Barbara
*******************************************************************************/

Ext.namespace('BQ.data');
BQ.data.pageSize = 500;

Ext.require([
    'Ext.grid.*',
    'Ext.data.*',
    'Ext.util.*',
    'Ext.grid.plugin.BufferedRenderer'
]);

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
        // temporary columns and store needed to init empty gridpanel without errors
        this.columns = [
            { text: '',  dataIndex: 'name' },
        ];
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
                }]
            }, {
                xtype: 'gridpanel',
                itemId  : 'table',
                autoScroll: true,
                flex: 2,
                region : 'center',
                border: 0,
                viewConfig: {
                    stripeRows: true,
                    //forceFit: true
                },
                plugins: 'bufferedrenderer',
                store: this.store,
                columns: this.columns,
            }],
        });
        //this.toolbar.doLayout();

        // load table info to configure columns and the store
        this.setLoading(true);
        Ext.Ajax.request({
            url: '/table/' + this.resource.resource_uniq + '/info/format:json',
            callback: function(opts, succsess, response) {
                if (response.status>=400 || !succsess)
                    BQ.ui.error(response.responseText);
                else
                    this.onTableInfo(response.responseText);
            },
            scope: this,
            disableCaching: false,
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
        var json = Ext.JSON.decode(txt),
            h = null;

        this.info = json;
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
                //flex: 1,
                dataIndex: i, // need to use numbers for reading from json array
                //sortable: true,
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

    onTableContents: function(txt) {
        var json = Ext.JSON.decode(txt);
        this.setLoading(false);
        this.table = json;
        //this.ontableLoaded(this.table);
    },

    onLoad: function(cb, url, r) {
        this.setLoading(false);
        if (r && r.target && r.target.responseText) {
            cb(r.target.responseText);
        } else {
            BQ.ui.error('Could not fetch '+url);
        }
    },

    onError: function(r) {
        this.setLoading(false);
        var m = r.target ? r.target.responseText : undefined;
        if (!m && r.target.status === 0) {
            m = 'Request failed probably due to Access-Control-Allow-Origin protection in your browser';
        } else if (!m && r.target.status>0) {
            m = 'Request failed';
        }
        BQ.ui.error(m);
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
