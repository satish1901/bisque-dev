/*******************************************************************************

  BQ.tree.files.Panel  - blob service directory tree store panel

  This is used to navigate in the directory view and create/delete directories
  and files

  Author: Dima Fedorov
  Version: 1

  History:
    2014-09-04 13:57:30 - first creation

*******************************************************************************/


//--------------------------------------------------------------------------------------
// misc
//--------------------------------------------------------------------------------------

function getNodePath(node) {
    var path = [];
    while (node) {
        if (node.data && node.data.type !== 'link')
            path.push(node.data.name || node.data.id);
        node = node.parentNode;
    }
    path.reverse();
    var url = path.join('/');
    return url;
}

//--------------------------------------------------------------------------------------
// BQ.data.reader.Files
// XML reader that reads path records from the data store
//--------------------------------------------------------------------------------------

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

//--------------------------------------------------------------------------------------
// BQ.data.writer.Files
// XML writer that writes path records to the data store
//--------------------------------------------------------------------------------------

Ext.define('BQ.data.writer.Files', {
    extend: 'Ext.data.writer.Xml',
    alias: 'writer.bq-files',

    writeRecords: function(request, data) {
        var me = request.proxy.ownerPanel;
        var url = me.getSelected();
        if (request.action === 'create') {
            var record = request.records[0];
            //var path = getNodePath(record);
            url += '/' + record.data.name;
        }
        request.url = url;
        request.xmlData = '';
        return request;
    },
});

//--------------------------------------------------------------------------------------
// BQ.data.proxy.Files
// Proxy to perform true REST fetches from blob service
//--------------------------------------------------------------------------------------

Ext.define('BQ.data.proxy.Files', {
    extend: 'Ext.data.proxy.Rest',
    alias : 'proxy.bq-files',

    batchActions: false,
    noCache : false,
    appendId: false,
    limitParam : 'limit',
    pageParam: undefined,
    startParam: 'offset',

    actionMethods: {
        create : 'POST', // 'PUT'
        read   : 'GET',
        update : 'POST',
        destroy: 'DELETE'
    },

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

//--------------------------------------------------------------------------------------
// BQ.tree.files.Panel
// events:
//    selected -
//--------------------------------------------------------------------------------------

Ext.namespace('BQ.tree.files');
BQ.tree.files.icons = {
   store: 'icon-store',
   dir: 'icon-folder',
   link: 'icon-file',
};

Ext.define('BQ.tree.files.Panel', {
    extend: 'Ext.tree.Panel',
    alias: 'widget.bq-tree-files-panel',
    requires: ['Ext.button.Button', 'Ext.tree.*', 'Ext.data.*'],

    path: undefined, // initial path

    cls: 'files',
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
    defaults: {
        border : false,
    },


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

        this.dockedItems = [{
            xtype: 'toolbar',
            itemId: 'tool_bar',
            dock: 'top',
            defaults: {
                scale: 'medium',
            },
            items: [{
                itemId: 'btnCreateFolder',
                text: 'Create',
                //scale: 'medium',
                iconCls: 'icon-add-folder',
                handler: this.createFolder,
                scope: this,
                tooltip: 'Create a new folder',
            },{
                itemId: 'btnDeleteSelected',
                text: 'Delete',
                //scale: 'medium',
                iconCls: 'icon-trash',
                handler: this.deleteSelected,
                scope: this,
                tooltip: 'Delete selected',
            }],
        }, {
            xtype:'bq-picker-path',
            itemId: 'path_bar',
            dock: 'top',
            height: 35,
            //prefix: 'Upload to: ',
            path: '/',
            listeners: {
                scope: this,
                //browse: this.browsePath,
                changed: function(el, path) {
                    this.setPath(path);
                },
            },
        }];

        this.store = Ext.create('Ext.data.TreeStore', {
            defaultRootId: 'store',
            //autoLoad: false,
            autoSync: true,
            //lazyFill: true,
            proxy : {
                type : 'bq-files',
                url : this.url,
                ownerPanel: this,
                //noCache : false,
                //appendId: false,
                //limitParam : 'limit',
                //pageParam: undefined,
                //startParam: 'offset',

                reader : {
                    type : 'bq-files',
                    root : 'resource',
                },
                writer : {
                    type : 'bq-files',
                },
            },
            fields : [{
                name : 'name',
                mapping : '@resource_unid',
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
                    if (record.data && record.data.type && record.data.type in BQ.tree.files.icons)
                        return BQ.tree.files.icons[record.data.type];
                }
            }],
            listeners: {
                scope: this,
                load: function () {
                    if (this.initialized) return;
                    this.initialized = true;
                    if (this.path)
                        this.setPath(this.path);
                },
            },
        });

        this.on('select', this.onSelect, this);
        this.on('afteritemexpand', this.onAfterItemExpand, this);
        this.on('afteritemcollapse', this.onAfterItemExpand, this);

        this.callParent();
    },

    /*afterRender : function() {
        this.store.load();
        this.store.autoLoad = true;
        this.callParent();
    },*/

    setActive : function() {
        var url = this.url_selected === this.url ? this.url + 'store' : this.url_selected;
        this.fireEvent('selected', url, this);
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
        this.queryById('path_bar').setPath( '/'+path.join('/') );

        if (this.url_selected !== url) {
            this.url_selected = url;
            this.fireEvent('selected', url, this);
        }
        record.expand();
    },

    getSelected : function() {
        return this.url_selected;
    },

    getSelectedAsResource : function() {
        var sel = this.getSelectionModel().getSelection();
        if (sel.length<1) return;
        var node = sel[0];
        if (!node) return;
        var r = BQFactory.parseBQDocument(node.raw);
        return r;
    },

    onAfterItemExpand : function( node, index, item, eOpts ) {
        this.getSelectionModel().select(node);
    },

    onPath: function(node, p) {
        if (!node) return;
        p.shift();

        if (p.length<=0) {
            this.getSelectionModel().select(node);
            return;
        }

        var name = p[0];
        node = node.findChildBy(
            function(n) {
                if (n.data.name === name) return true;
            },
            this,
            true
        );
        if (node)
            node.expand(false, function(nodes) {
                if (!nodes || nodes.length<1) return;
                this.onPath(nodes[0].parentNode, p);
            }, this);
    },

    setPath: function(path) {
        path = path.replace('/blob_service/store', '');
        var p = path === '/' ? [''] : path.split('/');
        this.onPath(this.getRootNode(), p);
    },

    onError: function(r) {
        BQ.ui.error('Error: '+r.statusText );
    },

    createFolder: function() {
        //Ext.Msg.prompt('Create folder', 'Please enter new folder\' name:', function(btn, text) {
        BQ.MessageBox.prompt('Create folder', 'Please enter new folder\' name:', function(btn, text) {
            var me = this;
            if (btn !== 'ok') return;

            var selection = me.getSelectionModel().getSelection();
            var parent = undefined;
            if (selection.length>0)
                parent = selection[0];
            else
                parent = me.getRootNode();

            var node = parent.appendChild({
                name : text,
                //value : '',
                type : 'dir',
            });
            me.getSelectionModel().select(node);
        }, this, undefined, undefined, function(v) {
            //| ; , ! @ # $ ( ) / \ " ' ` ~ { } [ ] = + & ^ <space> <tab>
            var regex = /[\n\f\r\t\v\0\*\?\|;,!@#$\(\)\\\/\"\'\`\~\{\}\[\]=+&\^]|^\s+/gi;
            if (regex.test(v))
                return 'Invalid characters are present';
            else
                return true;
        });
    },

    deleteSelected: function() {
        var me = this;
        var url = this.url_selected;
        Ext.Msg.confirm('Deletion', 'Are you sure to delete?', function(btn) {
            if (btn !== 'yes') return;

            var selection = me.getSelectionModel().getSelection();
            if (selection) {
                var node = selection[0];
                var parent = node.parentNode;
                node.remove();
                me.getSelectionModel().select(parent);
            }
        });
    },

});

