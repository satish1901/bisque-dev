Ext.define('BQ.Organizer.Tree', {
    extend : 'Ext.tree.Panel',

    title : 'Organizer',
    viewConfig : {
        stripeRows : true,
        expanderSelector : '.x-grid-cell-inner' /* Private */
    },
    lines : true,
    columnLines : true,
    rowLines : true,
    useArrows : true,
    singleExpand : true,
    frame : true,
    hideHeaders : true,
    border : false,
    rootVisible : false,

    constructor : function(config) {
        this.urlStateMgr = Ext.create('BQ.Organizer.URLState', {
            resourceServer : config.resourceServer || 'data_service',
            resourceType : config.resourceType || 'image',
            includePublic : config.includePublic || false,
        });

        this.tabPanel = Ext.create('Ext.tab.Panel', {
            dock : 'top',
            plain : true,
            padding : '0 0 2 0',
            border : false,
        });

        this.dockedItems = this.tabPanel;
        this.store = this.getTreeStore(this.urlStateMgr);
        this.columns = this.getColumns();
        this.callParent(arguments);
        this.store.organizerTree = this;
    },

    getTreeStore : function(urlStateMgr) {
        this.store = Ext.create('Ext.data.TreeStore', {
            root : {
                hasAttribute : Ext.emptyFn
            },
            listeners : {
                'load' : function(me, parentNode, childNodes) {
                    if (!parentNode.isRoot())
                        if (parentNode.get('depth') % 2 == 0)
                            for (var i = 0; i < childNodes.length; i++)
                                if (childNodes[i].get('name') in parentNode.get('tagLineage'))
                                    parentNode.removeChild(childNodes[i]);
                },

                'beforeexpand' : Ext.bind(this.onExpand, this),
                'collapse' : Ext.bind(this.onCollapse, this),

            },
            proxy : {
                type : 'ajax',
                url : urlStateMgr.getTagNames(),
                noCache : false,
                reader : {
                    type : 'xml',
                    root : 'resource',
                    record : 'tag'
                }
            },
            fields : [{
                name : 'name',
                mapping : '@name',
                convert : function(value, record) {
                    return record.get('value') || value;
                },
            }, {
                name : 'value',
                mapping : '@value'
            }, {
                name : 'tagLineage',
            }, {
                name : 'iconCls',
                type : 'string',
                convert : function(value, record) {
                    if (record.raw.hasAttribute('value'))
                        return 'icon-file';
                    return value;
                }
            }],
        });

        return this.store;
    },

    onExpand : function(node) {
        if (!node.isRoot()) {
            var view = this.getView(), nodeList = this.urlStateMgr.getKeys(node);
            keys = nodeList.keys;
            nodes = nodeList.nodes;
            view.focusRow(view.indexOf(node));

            this.tabPanel.removeAll();
            for (var i = keys.length - 1; i >= 0; i--)
                this.tabPanel.add(this.getDirButton(keys[i], nodes[i]));
            this.tabPanel.setActiveTab(keys.length - 1);

            if (node.get('depth') % 2 == 1)
                this.store.getProxy().url = this.urlStateMgr.getTagValues(node);
            else {
                this.store.getProxy().url = this.urlStateMgr.getTagNames(node);
                var iter = node.parentNode, tagLineage = {};

                if (Ext.isEmpty(node.get('tagLineage'))) {
                    while (!iter.isRoot()) {
                        if (iter.get('depth') % 2 == 1)
                            tagLineage[iter.get('name')] = 1;
                        iter = iter.parentNode;
                    }

                    node.set('tagLineage', tagLineage);
                }
            }
            this.fireEvent('QUERY_CHANGED', this.urlStateMgr.getBrowserURI(node, keys));
        }
    },

    onCollapse : function(node) {
        if (!this.flagCollapse) {
            this.onExpand(node.parentNode);
            this.flagCollapse = true;
            node.collapseChildren();
            this.flagCollapse = false;
        } else
            node.collapseChildren();

        if (node.parentNode.isRoot())
            this.tabPanel.removeAll();
    },

    getDirButton : function(name, node) {
        return {
            closable : true,
            node : node,
            title : ellipsis(name, 8, ".."),
            listeners : {
                'beforeclose' : function(me) {
                    me.node.collapse();
                },
            },
        };
    },

    getColumns : function() {
        return [{
            width : 10,
        }, {
            xtype : 'treecolumn',
            dataIndex : 'name',
            flex : 1,
        }];
    },
});

Ext.define('BQ.Organizer.URLState', {
    extend : 'Ext.util.Observable',

    urlTemplates : {
        tagNames : '{0}?tag_names=1&tag_query={1}&wpublic={2}',
        tagValues : '{0}?tag_values={1}&tag_query={2}&wpublic={3}',
    },

    constructor : function(config) {
        this.callParent(arguments);

        Ext.apply(this, {
            resourceType : this.resourceType || this.preferences.resourceType || 'image',
            resourceServer : this.resourceServer || this.preferences.resourceServer || 'data_service',
            includePublic : this.includePublic || false,
        });
    },

    getKeys : function(node) {
        var keys = [], nodes = [];

        while (!node.isRoot()) {
            keys.push(node.get('name'));
            nodes.push(node);
            node = node.parentNode;
        }

        return {
            keys : keys,
            nodes : nodes
        };
    },

    tagQuery : function(node, tkeys) {
        if (!Ext.isDefined(node))
            return '';

        var keys = tkeys || this.getKeys(node).keys, tagQuery = "", tpl = '"{0}":"{1}" AND ';

        for (var i = keys.length - 1; i >= keys.length % 2; i = i - 2)
            tagQuery = tagQuery + Ext.String.format(tpl, encodeURIComponent(keys[i]), encodeURIComponent(keys[i - 1]));

        return tagQuery.substring(0, tagQuery.length - 5);
    },

    tagOrder : function(node, tkeys) {
        var keys = tkeys || this.getKeys(node).keys, tagOrder = "", tpl = '"{0}":asc,';

        for (var i = keys.length - 1; i >= 0; i = i - 2)
            tagOrder = tagOrder + Ext.String.format(tpl, encodeURIComponent(keys[i]));

        return tagOrder.substring(0, tagOrder.length - 1);
    },

    getTagNames : function(node) {
        return Ext.String.format(this.urlTemplates.tagNames, this.resourceServer, this.tagQuery(node), this.includePublic);
    },

    getTagValues : function(node) {
        return Ext.String.format(this.urlTemplates.tagValues, this.resourceServer, node.get('name'), this.tagQuery(node), this.includePublic);
    },

    getBrowserURI : function(node, keys) {
        var uri = {
            baseURL : this.resourceServer, //Ext.String.format('/{0}/{1}', this.resourceServer, this.resourceType),
            offset : 0,
            tag_query : this.tagQuery(node, keys) || '',
            tag_order : this.tagOrder(node, keys) || '',
            wpublic : this.includePublic
        };

        return uri;
    }
});
