Ext.define('BQ.Organizer.Tree',
{
    extend      :   'Ext.tree.Panel',
    
    title       :   'Organizer',
    viewConfig  :   { stripeRows : true, expanderSelector : '.x-grid-cell-inner' /* Private */ },
    lines       :   true,
    columnLines :   true,
    rowLines    :   true,
    useArrows   :   true,
    singleExpand:   true,
    frame       :   true,
    hideHeaders :   true,
    border      :   false,
    rootVisible :   false,
    
    constructor : function(config)
    {
        var urlStateMgr = Ext.create('BQ.Organizer.URLState', {
            resourceServer  :   config.resourceServer   ||  'data_service',
            resourceType    :   config.resourceType     ||  'image',
            includePublic   :   config.includePublic    ||  false,
        });
        
        this.tabPanel = Ext.create('Ext.tab.Panel', {
            dock    :   'top',
            plain   :   true,
            padding :   '0 0 2 0',
            border  :   false,
        });
        
        this.dockedItems = this.tabPanel;        
        this.store = this.getTreeStore(urlStateMgr);
        this.columns = this.getColumns();
        this.callParent(arguments);
        this.store.organizerTree = this;
    },
    
    getTreeStore : function(urlStateMgr)
    {
        this.store = Ext.create('Ext.data.TreeStore',
        {
            root        :   { hasAttribute : Ext.emptyFn },
            listeners   :   {
                                'load' : function(me, parentNode, childNodes)
                                {
                                    if (!parentNode.isRoot())
                                        if (parentNode.get('depth') % 2 == 0)
                                            for (var i=0; i<childNodes.length; i++)
                                                if (childNodes[i].get('name') in parentNode.get('tagLineage'))
                                                    parentNode.removeChild(childNodes[i]);
                                },
                                'beforeexpand' : function(node)
                                {
                                    if (!node.isRoot())
                                    {
                                        var view = this.organizerTree.getView(), keys = urlStateMgr.getKeys(node); 
                                        view.focusRow(view.indexOf(node));
                                        
                                        this.organizerTree.tabPanel.removeAll();
                                        for (var i=keys.length-1; i>=0; i--)
                                            this.organizerTree.tabPanel.add({title : ellipsis(keys[i], 8, "..")});
                                        this.organizerTree.tabPanel.setActiveTab(keys.length-1);
                                        
                                        if (node.get('depth') % 2 == 1)
                                            this.getProxy().url = urlStateMgr.getTagValues(node);
                                        else
                                        {
                                            this.getProxy().url = urlStateMgr.getTagNames(node);
                                            var iter = node.parentNode, tagLineage = {};
                                            
                                            if (Ext.isEmpty(node.get('tagLineage')))
                                            {
                                                while(!iter.isRoot())
                                                {
                                                    if (iter.get('depth') % 2 == 1)
                                                        tagLineage[iter.get('name')] = 1;
                                                    iter = iter.parentNode;
                                                }
                                                
                                                node.set('tagLineage', tagLineage);
                                            }
                                        }
                                        
                                        this.organizerTree.fireEvent('QUERY_CHANGED', urlStateMgr.getBrowserURI(node, keys));
                                    }
                                },
                            },
            proxy       :   { 
                                type        :   'ajax',
                                url         :   urlStateMgr.getTagNames(),
                                noCache     :   false,
                                reader      :   {
                                                    type    :   'xml',
                                                    root    :   'resource',
                                                    record  :   'tag'
                                                }
                            },
            fields      :   [{
                                name    :   'name',
                                mapping :   '@name',
                                convert :   function(value, record)
                                {
                                    return record.get('value') || value;
                                },
                            },
                            {
                                name    :   'value',
                                mapping :   '@value'
                            },
                            {
                                name    :   'tagLineage',
                            },
                            {
                                name    :   'iconCls',
                                type    :   'string',
                                convert :   function(value, record)
                                {
                                    if (record.raw.hasAttribute('value'))
                                        return 'icon-file';
                                    return value;
                                }
                            }],
        });

        return this.store;
    },

    getColumns  :   function()
    {
        return  [{
                    width       :   10,
                },
                {
                    xtype       :   'treecolumn',
                    dataIndex   :   'name',
                    flex        :   1,
                }];
    },
});

Ext.define('BQ.Organizer.URLState',
{
    extend  :   'Ext.util.Observable',

    urlTemplates    :   {
                            tagNames    :   '/{0}/{1}?tag_names=1&tag_query={2}&wpublic={3}',
                            tagValues   :   '/{0}/{1}?tag_values={2}&tag_query={3}&wpublic={4}',
                        },
    
    constructor : function(config)
    {
        this.callParent(arguments);
        
        Ext.apply(this,
        {
            resourceType    :   this.resourceType   ||  this.preferences.resourceType   ||  'image',
            resourceServer  :   this.resourceServer ||  this.preferences.resourceServer ||  'data_service',
            includePublic   :   this.includePublic  ||  false,
        });
    },
    
    getKeys : function(node)
    {
        var keys = [];
        
        while(!node.isRoot())
        {
            keys.push(node.get('name'));
            node = node.parentNode;
        }
        
        return keys;
    },
    
    tagQuery : function(node, tkeys)
    {
        if (!Ext.isDefined(node))
            return '';
            
        var keys = tkeys || this.getKeys(node), tagQuery = "", tpl = '"{0}":"{1}" AND ';
        
        for (var i=keys.length-1; i>=keys.length%2; i=i-2)
            tagQuery = tagQuery + Ext.String.format(tpl, encodeURIComponent(keys[i]), encodeURIComponent(keys[i-1]));

        return tagQuery.substring(0, tagQuery.length - 5);
    },
    
    tagOrder : function(node, tkeys)
    {
        var keys = tkeys || this.getKeys(node), tagOrder = "", tpl = '"{0}":asc,';
            
        for (var i=keys.length-1; i>=0; i=i-2)
            tagOrder = tagOrder + Ext.String.format(tpl, encodeURIComponent(keys[i]));
            
        return tagOrder.substring(0, tagOrder.length - 1);
    },
    
    getTagNames : function(node)
    {
        return Ext.String.format(this.urlTemplates.tagNames, this.resourceServer, this.resourceType, this.tagQuery(node), this.includePublic);
    },
    
    getTagValues : function(node)
    {
        return Ext.String.format(this.urlTemplates.tagValues, this.resourceServer, this.resourceType, node.get('name'), this.tagQuery(node), this.includePublic);
    },
    
    getBrowserURI : function(node, keys)
    {
        var uri =
        {
            baseURL     :   Ext.String.format('/{0}/{1}', this.resourceServer, this.resourceType),
            offset      :   0,
            tag_query   :   this.tagQuery(node, keys) || '',
            tag_order   :   this.tagOrder(node, keys) || '',
            wpublic     :   this.includePublic
        };
        
        return uri;
    }
})
