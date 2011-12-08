Ext.define('Bisque.ResourceTagger',
{
    extend : 'Ext.container.Container',

    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(this,
        {
            layout : 'fit',
            padding : '0 1 0 0',
            style : 'background-color:#FFF',

            rootProperty : config.rootProperty || 'tags',
            autoSave : (config.autoSave==undefined) ? true : false,
            resource : {},
            tree : {},
            store : {},
            dirtyRecords : []
        });

        this.viewMgr = new Bisque.ResourceTagger.viewStateManager(config.viewMode);;

        // dima - datastore for the tag value combo box
        var TagValues = Ext.ModelManager.getModel('TagValues');
        if (!TagValues) {
            Ext.define('TagValues', {
                extend : 'Ext.data.Model',
                fields : [ {name: 'value', mapping: '@value' } ],
            });
        }
        this.store_values = Ext.create('Ext.data.Store', {
            model : 'TagValues', 
            autoLoad : true,
            autoSync : false,
            
            proxy: {
                noCache : false,
                type: 'ajax',
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                
                //url : '/data_service/image?tag_values=mytag',
                url: '/xml/dummy_tag_values.xml', // a dummy document just to inhibit initial complaining
                reader : {
                    type :  'xml',
                    root :  'resource',
                    record: 'tag', 
                },
            },
             
        });


        this.callParent([config]);
        this.setResource(config.resource);
    },

    setResource : function(resource)
    {
        this.setLoading(true);
        
        if (resource instanceof BQObject)
            this.loadResourceInfo(resource);
        else
            // assume it is a resource URI otherwise
            BQFactory.request(
            {
                uri : resource,
                cb : Ext.bind(this.loadResourceInfo, this)
            });
    },

    loadResourceInfo : function(resource)
    {
        this.fireEvent('beforeload', this, resource);

        this.resource = resource;
        if(this.resource.tags.length > 0)
            this.loadResourceTags(this.resource.tags);
        else
            this.resource.loadTags(
            {
                cb: callback(this, "loadResourceTags"),
                //depth: 'full'
            });
    },

    loadResourceTags : function(data)
    {
        this.setLoading(false);

        var root = {};
        root[this.rootProperty] = data;
        
        this.add(this.getTagTree(root));
        this.fireEvent('onload', this, this.resource);
    },

    getTagTree : function(data)
    {
        var rowEditor = Ext.create('Bisque.ResourceTagger.Editor',
        {
            clicksToMoveEditor : 1,
            errorSummary : false,
            listeners : 
            {
                'edit' : function(me)
                {
                    if (me.record.raw)
                        if (this.autoSave)
                        {
                            this.saveTags(me.record.raw, true);
                            me.record.commit();
                        }
                },
                scope : this
            }
        });
        
        this.tree = Ext.create('Ext.tree.Panel',
        {
            useArrows : true,
            rootVisible : false,
            border : false,
            padding : 1,
            columnLines : true,
            rowLines : true,
            lines : true,
            iconCls : 'icon-grid',
            //title : 'Resource tagger - '+'<span style="font-weight:normal">'+this.resource.uri.replace(window.location.origin,"")+'</span>',

            store : this.getTagStore(data),
            multiSelect : true,
            tbar : this.getToolbar(),
            columns : this.getTreeColumns(),

            selModel : this.getSelModel(),
            plugins : (this.viewMgr.state.editable) ? [rowEditor] : null,
            

            listeners :
            {
                'checkchange' : function(node, checked)
                {
                    (checked) ? this.fireEvent('select', this, node) : this.fireEvent('deselect', this, node);
                    this.checkTree(node, checked);
                    //Recursively check/uncheck all children of a parent node
                },
                scope :this
            }
        });

        this.store.tagTree = this.tree;

        return this.tree;
    },

    //Recursively check/uncheck all children of a parent node
    checkTree : function(node, checked)
    {
        node.set('checked', checked);

        for(var i=0;i<node.childNodes.length; i++)
            this.checkTree(node.childNodes[i], checked);
    },

    getSelModel : function()
    {
        return null;
    },

    updateQueryTagValues: function(tag_name) {
        var url = '/data_service/image?tag_values='+encodeURIComponent(tag_name);
        var proxy = this.store_values.getProxy();
        proxy.url = url;
        this.store_values.load();
    },

    getTreeColumns : function()
    {
        return [{
            xtype : 'treecolumn',
            dataIndex : 'name',
            text : this.colNameText || 'Name',
            flex : 0.8,
            sortable : true,
            field : {
                allowBlank: false,
                //fieldLabel: this.colNameText || 'Name',
                //labelAlign: 'top',    
                tabIndex: 0,            
                
                validateOnChange: false,
                blankText: 'Tag name is required!',
                msgTarget : 'none',
                
                listeners: {
                    'change': function( field, newValue, oldValue, eOpts ) {
                        this.updateQueryTagValues(newValue);
                    },
                   
                    scope: this,
                },                 
                
            }
        }, {
            text : this.colValueText || 'Value',
            dataIndex : 'value',
            flex : 1,
            sortable : true,
            field : {
                // dima: combo box instead of the normal text edit that will be populated with existing tag values
                xtype     : 'bqcombobox',
                tabIndex: 1,                
                
                store     : this.store_values,
                displayField: 'value',
                valueField: 'value',
                
                queryMode : 'local',
                //queryMode : 'remote',
                                
                minChars: 1,
                allowBlank : true,   
                editable: true,  
                forceSelection: false,           
                autoScroll: true,
                autoSelect: false,
                typeAhead : true,
                
                //matchFieldWidth: false,
                defaultListConfig : { emptyText: undefined, loadingText: "Loading...", maxHeight: 300, resizable: false, },
                
                //fieldLabel: this.colValueText || 'Value',
                //labelAlign: 'top',
            },
            
            renderer : Bisque.ResourceTagger.BaseRenderer
        }];
    },

    getTagStore : function(data)
    {
        this.store = Ext.create('Ext.data.TreeStore',
        {
            defaultRootProperty : this.rootProperty,
            root : data,

            fields : [
            {
                name : 'name',
                type : 'string',
                convert : function(value, record)
                {
                    return value || record.data.type;
                }
            },
            {
                name : 'value',
                type : 'string'
            },
            {
                name : 'type',
                type : 'string'
            },
            {
                name : 'iconCls',
                type : 'string',
                convert : Ext.bind(function(value, record)
                {
                    if(record.raw)
                        if(record.raw[this.rootProperty].length != 0)
                            return 'icon-folder';
                    return 'icon-tag';
                }, this)

            },
            {
                name : 'qtip',
                type : 'string',
                convert : function(value, record)
                {
                    return record.data.name + ' : ' + record.data.value;
                }

            }, this.getStoreFields()],

            indexOf : function(record)
            {
                return this.tagTree.getView().indexOf(record);
            },

            applyModifications : function()
            {
                var nodeHash = this.tree.nodeHash, status = false;

                if (this.getRemovedRecords().length>0)
                    return true;

                for(var node in nodeHash)
                if(nodeHash[node].dirty)
                {
                    status = true;
                        Ext.apply(nodeHash[node].raw, nodeHash[node].getChanges());
                    nodeHash[node].commit();
                }
                return status;
            },

            /* Modified function so as to not delete the root nodes */
            onNodeAdded : function(parent, node)
            {
                var proxy = this.getProxy(), reader = proxy.getReader(), data = node.raw || node.data, dataRoot, children;

                Ext.Array.remove(this.removed, node);

                if(!node.isLeaf() && !node.isLoaded())
                {
                    dataRoot = reader.getRoot(data);
                    if(dataRoot)
                    {
                        this.fillNode(node, reader.extractData(dataRoot));
                        // Do not delete the root
                        //delete data[reader.root];
                    }
                }
            }

        });

        return this.store;
    },

    getStoreFields : function()
    {
        return {};
    },

    getToolbar : function()
    {
        var tbar = [
        {
            xtype : 'buttongroup',
            hidden : (this.viewMgr.state.btnAdd && this.viewMgr.state.btnDelete),
            items : [
            {
                text : 'Add',
                hidden : this.viewMgr.state.btnAdd,
                scale : 'small',
                iconCls : 'icon-add',
                handler : this.addTags,
                scope : this
            },
            {
                text : 'Delete',
                hidden : this.viewMgr.state.btnDelete,
                scale : 'small',
                iconCls : 'icon-delete',
                handler : this.deleteTags,
                scope : this
            }]
        },
        {
            xtype : 'buttongroup',
            hidden : (this.viewMgr.state.btnImport && this.viewMgr.state.btnExport),
            items : [
            {
                text : 'Import',
                hidden : this.viewMgr.state.btnImport,
                scale : 'small',
                iconCls : 'icon-import',
                handler : this.importTags,
                scope : this
            },
            {
                text : 'Export',
                scale : 'small',
                hidden : this.viewMgr.state.btnExport,
                iconCls : 'icon-export',
                menu :
                {
                    items : [
                    {
                        text : 'as XML',
                        handler : this.exportToXml,
                        hidden : this.viewMgr.state.btnXML,
                        scope : this
                    },
                    {
                        text : 'as CSV',
                        handler : this.exportToCsv,
                        hidden : this.viewMgr.state.btnCSV,
                        scope : this
                    },
                    {
                        text : 'to Google Docs',
                        handler : this.exportToGDocs,
                        hidden : this.viewMgr.state.btnGDocs,
                        scope : this
                    }]
                }
            }]
        },
        {
            xtype : 'buttongroup',
            hidden : (this.viewMgr.state.btnSave || this.autoSave),
            items : [
            {
                text : 'Save',
                hidden : this.viewMgr.state.btnSave || this.autoSave, 
                scale : 'small',
                iconCls : 'icon-save',
                handler : this.saveTags,
                scope : this
            }]
        }];

        return tbar;
    },
    
    addTags : function()
    {
        var currentItem = this.tree.getSelectionModel().getSelection();
        var editor = this.tree.plugins[0];

        if(currentItem.length)// None selected -> add tag to parent document
            currentItem = currentItem[0];
        else
            currentItem = this.tree.getRootNode();
        
        // Adding new tag to tree
        var child = { name : '', value : '' };
        
        child[this.rootProperty] = [];
        var newNode = currentItem.appendChild(child);
        currentItem.expand();

        editor.startEdit(newNode, 0);

        editor.on('edit', function(me)
        {
            this.editing = true;
            var newTag = new BQTag();
            newTag = Ext.apply(newTag,
            {
                name : me.record.data.name,
                value : me.record.data.value,
            });
            var parent = (me.record.parentNode.isRoot()) ? this.resource : me.record.parentNode.raw;
            parent.addtag(newTag);

            if (this.autoSave)
                this.saveTags(parent, true);

            me.record.raw = newTag;
            me.record.loaded=true;
            me.record.commit();

            me.record.parentNode.data.iconCls = 'icon-folder';
            me.view.refresh();

            BQ.ui.message('Resource tagger - Add', 'New record added!');
            this.editing=false;
        }, this, {single : true});
            
        editor.on('canceledit', function(grid, eOpts) {
            if (!newNode.data.name || (newNode.data.name && newNode.data.value && newNode.name=='' && newNode.value==''))
                currentItem.removeChild(newNode);
        }, this, {single : true});            
            
            
    },

    deleteTags : function()
    {
        var selectedItems = this.tree.getSelectionModel().getSelection(), parent;

        if(selectedItems.length)
        {
            for(var i = 0; i < selectedItems.length; i++)
            {
                parent = (selectedItems[i].parentNode.isRoot()) ? this.resource : selectedItems[i].parentNode.raw;
                parent.deleteTag(selectedItems[i].raw);

                if(selectedItems[i].parentNode.childNodes.length <= 1)
                    selectedItems[i].parentNode.data.iconCls = 'icon-tag';

                selectedItems[i].parentNode.removeChild(selectedItems[i], true);
            }

            if (this.autoSave)
                this.saveTags(null, true);

            BQ.ui.message('Resource tagger - Delete', selectedItems.length + ' record(s) deleted!');
            
            this.tree.getSelectionModel().deselectAll();
        }
        else
            BQ.ui.message('Resource tagger - Delete', 'No records selected!');
    },

    saveTags : function(parent, silent)
    {
        var resource = (typeof parent == BQObject) ? parent  : this.resource;
        
        if(this.store.applyModifications())
        {
            resource.save_();
            if (!silent) BQ.ui.message('Resource tagger - Save', 'Changes were saved successfully!');
        }
        else
            BQ.ui.message('Resource tagger - Save', 'No records modified!');
    },
    
    importTags : function()
    {
        var rb = new Bisque.ResourceBrowser.Dialog(
        {
            height : '85%',
            width : '85%',
            viewMode : 'ViewerLayouts',
            listeners :
            {
                'Select' : function(me, resource)
                {
                    if(resource.tags.length > 0)
                        this.appendTags(resource.tags);
                    else
                        resource.loadTags(
                        {
                            cb : callback(this, "appendTags"),
                        });
                },

                scope : this
            },
        });
    },
    
    appendTags : function(data)
    {
        if (data.length>0)
        {
            data = this.stripURIs(data);
            this.resource.tags = this.resource.tags.concat(data);
            this.addNode(this.tree.getRootNode(), data);
        }
    },
    
    stripURIs : function(tagDocument)
    {
        var treeVisitor = Ext.create('Bisque.ResourceTagger.OwnershipStripper');
        treeVisitor.visit_array(tagDocument);
        return tagDocument;
    },
    
    updateNode : function(loaded, node, data)
    {
        if (!loaded)
            node.raw.loadTags(
            {
                cb: callback(this, "updateNode", true, node),
                depth: 'full'
            });
        else
            for(var i=0;i<data.length;i++)
                if (data[i].uri!=node.childNodes[i].raw.uri)
                    // Assuming resources come in order
                    alert('Tagger::updateNode - URIs not same!');
                else
                    this.addNode(node.childNodes[i], data[i][this.rootProperty]);
    },
    
    addNode : function(nodeInterface, children)
    {
        var newNode, i;
        
        if (!(children instanceof Array))
            children = [children];
        
        for (i=0;i<children.length;i++)
        {
            //debugger;
            newNode=Ext.ModelManager.create(children[i], this.store.model);
            Ext.data.NodeInterface.decorate(newNode);
            newNode.raw=children[i];
            nodeInterface.appendChild(newNode);

            nodeInterface.data.iconCls = 'icon-folder';
            this.tree.getView().refresh();
        }
    },

    exportToXml : function()
    {
        // append view=full ?
        window.open(this.resource.uri);
    },

    exportToCsv : function()
    {
        var url = '/stats/csv?url=';
        url += encodeURIComponent(this.resource.uri);
        url += '&xpath=%2F%2Ftag&xmap=tag-name-string&xmap1=tag-value-string&xreduce=vector';
        window.open(url);
    },

    exportToGDocs : function()
    {
        var url = '/export/to_gdocs?url=' + encodeURIComponent(this.resource.uri);
        window.open(url);
    },

});

Ext.define('Bisque.GObjectTagger',
{
    extend : 'Bisque.ResourceTagger',

    constructor : function(config)
    {
        config.rootProperty = 'gobjects';
        config.colNameText = 'GObject';
        config.colValueText = 'Vertices';

        this.callParent(arguments);
    },

    loadResourceInfo : function(resource)
    {
        this.fireEvent('beforeload', this, resource);
        
        this.resource = resource;
        this.resource.loadGObjects(
        {
            cb: callback(this, "loadResourceTags"),
            //depth: 'full'
        });
    },

    getStoreFields : function()
    {
        return {
            name : 'checked',
            type : 'bool',
            defaultValue : true
        }
    },
    
    getToolbar : function()
    {
        var toolbar = this.callParent(arguments);
        
        var buttons =  
        [{
            xtype : 'buttongroup',
            items : [{
                text : 'Uncheck All',
                scale : 'small',
                iconCls : 'icon-uncheck',
                handler : this.toggleCheck,
                scope : this,
                checked : true
            }]
        }];
        
        return buttons.concat(toolbar);
    },
    
    toggleCheck : function(button)
    {
        button.checked = !button.checked;
        var rootNode = this.tree.getRootNode(), eventName=(button.checked)?'Select':'Deselect';
        
        if (button.checked)
        {
            button.setText('Uncheck All')
            button.setIconCls('icon-uncheck')
        }
        else
        {
            button.setText('Check All')
            button.setIconCls('icon-check')
        }
        
        for (var i=0;i<rootNode.childNodes.length;i++)
            this.fireEvent(eventName, this, rootNode.childNodes[i]);

        this.checkTree(rootNode, button.checked);
    },
    
    appendFromMex : function(resQ)
    {
        for (var i=0;i<resQ.length;i++)
            resQ[i].resource.loadGObjects({cb: Ext.bind(this.appendGObjects, this, [resQ[i].resource], true)});
    },
    
    appendGObjects : function(data, mex)
    {
        if (data.length>0)
        {
            this.addNode(this.tree.getRootNode(), {name:data[0].name, value:Ext.Date.format(Ext.Date.parse(mex.ts, 'Y-m-d H:i:s.u'), "F j, Y g:i:s a"), gobjects:data});
            this.fireEvent('onappend', this, data);
        }
    },

    exportToXml : Ext.emptyFn,
    exportToGDocs : Ext.emptyFn,

    exportToCsv : function()
    {
        var gobject, selection = this.tree.getChecked();
        this.noFiles = 0, this.csvData = '';
        
        function countGObjects(node, i)
        {
            if (node.raw)
                this.noFiles++;
        }
        
        selection.forEach(Ext.bind(countGObjects, this));
        
        for (var i=0;i<selection.length;i++)
        {
            gobject = selection[i].raw;

            if (gobject)
            {
                Ext.Ajax.request({
                    url : gobject.uri+'?view=deep&format=csv',
                    success : Ext.bind(this.saveCSV, this),
                    disableCaching : false 
                });
            }
        }
    },
    
    saveCSV : function(data)
    {
        this.csvData += '\n'+data.responseText;
        this.noFiles--;
        
        if (!this.noFiles)
            location.href = "data:text/csv," + encodeURIComponent(this.csvData);
    }
});

Ext.define('Bisque.ResourceTagger.Editor',
{
    extend : 'BQ.grid.plugin.RowEditing',

    completeEdit : function()
    {
        this.callParent(arguments);
        this.finishEdit();
    },
    
    cancelEdit : function()
    {
        this.callParent(arguments);
        this.finishEdit();
    },

    finishEdit : function()
    {
        if(this.context)
            this.context.grid.getSelectionModel().deselect(this.context.record);
    }

});

Ext.define('Bisque.ResourceTagger.OwnershipStripper', 
{
    extend : BQVisitor,
    
    visit : function(node, args)
    {
        Ext.apply(node, 
        {
            uri : undefined,
            ts : undefined,
            owner : undefined,
            perm : undefined,
            index : undefined 
        });
    }
});

Ext.define('Bisque.ResourceTagger.viewStateManager',
{
    //	ResourceTagger view-state
    state : 
    {
        btnAdd : true,
        btnDelete : true,
        
        btnToggleCheck : true,
        
        btnImport : true,
        btnExport : true,
        btnXML : true,
        btnCSV : true,
        btnGDocs : true,
    
        btnSave : true,
        editable : true,
    },

    constructor : function(mode)
    {
        function setHidden(obj, bool)
        {
            var result={};
            
            for (i in obj)
                result[i]=bool;
            
            return result;
        }
        
        if (!BQApp.user)
            mode = 'ReadOnly';
        
        switch(mode)
        {
            case 'ViewerOnly':
            {
                // all the buttons are hidden
                this.state = setHidden(this.state, true);
                this.state.editable = false;
                break;
            }
            case 'ReadOnly':
            {
                this.state.btnExport = false;
                this.state.btnXML = false;
                this.state.btnCSV = false;
                this.state.btnGDocs = false;
                break;
            }
            case 'Offline':
            {
                this.state.btnAdd = false;
                this.state.btnDelete = false;
                this.state.btnImport = false;
                break;
            }
            case 'GObjectTagger':
            {
                // all the buttons are hidden except export
                this.state = setHidden(this.state, true);
                this.state.editable = false;
                
                this.state.btnExport = false;
                this.state.btnCSV = false;
                //this.state.btnGDocs = false;
                //this.state.btnXML = false;
                
                break;
            }
            default:
            {
                // default case: all buttons are visible (hidden='false')
                this.state = setHidden(this.state, false);
                this.state.editable = true;
            }
        }
        
    }
});