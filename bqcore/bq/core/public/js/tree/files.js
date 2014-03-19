
Ext.define('BQ.data.reader.Files', {
    extend: 'Ext.data.reader.Xml',
    alias : 'reader.bq-files',

    root : 'resource',
    record : '>store,>dir,>link',

    getRoot: function(data) {
        // in blob service doc the root of the document is our root
        if (Ext.DomQuery.isXml(data) && !data.parentElement) {
            return data;
        } else if (data.tagName === 'link') {
            return data;
        }
    },

    /*extractData: function(root) {
        var recordName = this.record;

        //<debug>
        if (!recordName) {
            Ext.Error.raise('Record is a required parameter');
        }
        //</debug>

        if (recordName != root.nodeName) {
            root = Ext.DomQuery.select(recordName, root);
        } else {
            root = [root];
        }
        //return this.callParent([root]);
        return this.callSuper([root]);
    },*/

});

// Proxy to perform true REST fetches from blob service
Ext.define('BQ.data.proxy.Files', {
    extend: 'Ext.data.proxy.Rest',
    alias : 'proxy.bq-files',

    noCache : false,
    appendId: false,
    limitParam : 'limit',
    pageParam: undefined,
    startParam: 'offset',

    buildUrl: function(request) {
        // extjs attempts adding ?node=NAME to all requests
        if (request.params && request.params.node) {
            delete request.params.node;
        }
        // create a URL path traversing through the parents
        var node = request.operation.node;
        var path = [];
        while (node) {
            if (node.data)
                path.push(node.data.name || node.data.id);
            node = node.parentNode;
        }
        var url = this.getUrl(request) + path.reverse().join('/');
        request.url = url;
        return url;
    },

});

Ext.define('BQ.tree.files.Panel', {
    extend: 'Ext.tree.Panel',
    alias: 'widget.bq-tree-files-panel',
    requires: ['Ext.button.Button', 'Ext.tree.*', 'Ext.data.*'],

    //pageSize: 100,          // number of records to fetch on every request
    //trailingBufferZone: 20, // Keep records buffered in memory behind scroll
    //leadingBufferZone: 20,  // Keep records buffered in memory ahead of scroll

    animate: false,
    animCollapse: false,
    deferRowRender: true,
    displayField: 'name',
    folderSort: false,
    singleExpand : false,
    viewConfig : {
        stripeRows : true,
        enableTextSelection: false,
    },
    multiSelect: false,
    lines : false,
    columnLines : true,
    rowLines : true,
    useArrows : true,
    frame : true,
    hideHeaders : true,
    border : false,
    rootVisible : false,
    disableSelection: false,
    allowDeselect: false,
    sortableColumns: false,


    /*plugins: [{
        ptype: 'bufferedrenderer'
    }],*/

    constructor : function(config) {
        this.addEvents({
            'selected' : true,
        });
        this.callParent(arguments);
    },

    initComponent : function() {
        this.url = this.url || '/blob_service/';
        this.url_selected = this.url;

        // Get store
        this.store = Ext.create('Ext.data.TreeStore', {
            defaultRootId: 'store',
            //lazyFill: true,
            proxy : {
                type : 'bq-files',
                url : this.url,
                //noCache : false,
                //appendId: false,
                //limitParam : 'limit',
                //pageParam: undefined,
                //startParam: 'offset',

                reader : {
                    type : 'bq-files',
                    root : 'resource',
                },
            },
            fields : [{
                name : 'name',
                mapping : '@name',
            }, {
                name : 'value',
                mapping : '@value',
            }, {
                name : 'type',
                convert : function(value, record) {
                    return record.raw.tagName;
                },
            }, {
                name : 'iconCls',
                type : 'string',
                convert : function(value, record) {
                    if (record.data.type === 'link')
                        return 'icon-file';
                }
            }],
        });

        this.on('select', this.onSelect, this);
        this.on('afteritemexpand', this.onAfterItemExpand, this);
        this.on('afteritemcollapse', this.onAfterItemExpand, this);

        this.dockedItems = [{
            xtype: 'tbtext',
            itemId: 'path_bar',
            text: '/',
            dock: 'top',
        }];

        this.callParent();
    },

    onSelect : function(me, record, index, eOpts) {
        var node = record;
        var path = [];
        while (node) {
            if (node.data && node.data.type !== 'link')
                path.push(node.data.name || node.data.id);
            node = node.parentNode;
        }
        path.reverse();
        var url = this.url+path.join('/');
        path.shift();
        this.queryById('path_bar').setText( '/'+path.join('/') );

        if (this.url_selected !== url) {
            this.url_selected = url;
            this.fireEvent('selected', url, this);
        }
    },

    onAfterItemExpand : function( node, index, item, eOpts ) {
        this.getSelectionModel().select(node);
    },

});

