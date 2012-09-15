Ext.define('Bisque.ResourceTagger',
{
    extend : 'Ext.panel.Panel',

    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(this,
        {
            layout : 'fit',
            padding : '0 1 0 0',
            style : 'background-color:#FFF',
            border : false,

            rootProperty : config.rootProperty || 'tags',
            autoSave : (config.autoSave==undefined) ? true : false,
            resource : {},
            editable : true,
            tree : config.tree || {
                btnAdd : true,
                btnDelete : true,
                btnImport : true,
                //btnExport : true,
            },
            store : {},
            dirtyRecords : []
        });

        this.viewMgr = new Bisque.ResourceTagger.viewStateManager(config.viewMode);;
        this.populateComboStore();
        
        this.callParent([config]);
        this.setResource(config.resource);
    },
    
    populateComboStore : function()
    {
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

        // dima - datastore for the tag name combo box
        var TagNames = Ext.ModelManager.getModel('TagNames');
        if (!TagNames) {
            Ext.define('TagNames', {
                extend : 'Ext.data.Model',
                fields : [ {name: 'name', mapping: '@name' } ],
            });
        }
        this.store_names = Ext.create('Ext.data.Store', {
            model : 'TagNames', 
            autoLoad : true,
            autoSync : false,
            
            proxy: {
                noCache : false,
                type: 'ajax',
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                
                url : '/data_service/image/?tag_names=1',
                reader : {
                    type :  'xml',
                    root :  'resource',
                    record: 'tag', 
                },
            },
        });
    },

    setResource : function(resource, template)
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
        this.editable = false;
        this.testAuth(BQApp.user, false);
        
        if(this.resource.tags.length > 0)
            this.loadResourceTags(this.resource.tags);
        else
            this.resource.loadTags(
            {
                cb: callback(this, "loadResourceTags"),
                depth: 'deep&wpublic=1'
            });
    },

    reload : function() {
         this.setResource( this.resource.uri );
    },

    loadResourceTags : function(data, template)
    {
        var type = this.resource.type || this.resource.resource_type;

        // Check to see if resource was derived from a template
        if (type.indexOf('data_service/template')!=-1 && !template)
        {
            BQFactory.request({
                uri :   this.resource.type+'?view=deep',
                cb  :   Ext.bind(this.initCopy, this)
            });
            
            return;
        }

        this.setLoading(false);

        var root = {};
        root[this.rootProperty] = data;
        
        this.removeAll(true);
        this.add(this.getTagTree(root));
        this.fireEvent('onload', this, this.resource);
        this.relayEvents(this.tree, ['itemclick']);
    },

    initCopy : function(template)
    {
        var resource = this.copyTemplate(template, this.resource);
        this.resource = resource;
        this.loadResourceTags(this.resource.tags, template);
    },
        
    copyTemplate : function(template, resource)
    {
        for(var i = 0; i < resource.tags.length; i++)
        {
            var matchingTag = template.find_tags(resource.tags[i].name);
            if (matchingTag)
            {
                matchingTag = (matchingTag instanceof Array)?matchingTag[0]:matchingTag;
                resource.tags[i].template = matchingTag.template;
                this.copyTemplate(matchingTag, resource.tags[i]);
            }
        }
        
        return resource;
    },

    getTagTree : function(data)
    {
        this.rowEditor = Ext.create('Bisque.ResourceTagger.Editor',
        {
            clicksToMoveEditor  :   1,
            tagger              :   this,
            errorSummary        :   false,

            listeners           :   {
                                        'edit'          :   this.finishEdit,
                                        'cancelEdit'    :   this.cancelEdit,
                                        scope           :   this
                                    },
            
            beforeEdit          :   function(editor)
                                    {
                                        var isEmpty = function(obj)
                                        {
                                            return Object.keys(obj).length === 0;
                                        }                                        
                                        
                                        if (this.tagger.editable && !isEmpty(editor.record.raw.template) && this.tagger.resource.resource_type!='template')
                                        {
                                            if (editor.record.raw.template.Editable)
                                            {
                                                try {
                                                    this.tagger.tree.columns[1].setEditor(BQ.TagRenderer.Base.getRenderer({tplType:editor.record.get('type'), tplInfo:editor.record.raw.template}));
                                                }
                                                catch(error)
                                                {
                                                    alert(error);
                                                }
                                                return true;
                                            }
                                            else
                                                return false;
                                        }

                                        return this.tagger.editable;
                                    }
        });
        
        this.tree = Ext.create('Ext.tree.Panel',
        {
            useArrows : true,
            rootVisible : false,
            border : false,
            columnLines : true,
            rowLines : true,
            lines : true,
            iconCls : 'icon-grid',
            animate : this.animate,
            header : false,

            store : this.getTagStore(data),
            multiSelect : true,
            tbar : this.getToolbar(),
            columns : this.getTreeColumns(),

            selModel : this.getSelModel(),
            plugins : (this.viewMgr.state.editable) ? [this.rowEditor] : null,
            
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
    
    toggleTree : function(node)
    {
        node.set('checked', !node.get('checked'));

        for(var i=0;i<node.childNodes.length; i++)
            this.toggleTree(node.childNodes[i]);
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
                // dima: combo box instead of the normal text edit that will be populated with existing tag names
                xtype     : 'bqcombobox',
                tabIndex: 0,  
                
                store     : this.store_names,
                displayField: 'name',
                valueField: 'name',
                queryMode : 'local',
                                
                allowBlank: false,
                //fieldLabel: this.colNameText || 'Name',
                //labelAlign: 'top',    

                validateOnChange: false,
                blankText: 'Tag name is required!',
                msgTarget : 'none',
                
                listeners: {
                    'change': {
                        fn: function( field, newValue, oldValue, eOpts ) {
                                this.updateQueryTagValues(newValue);
                            },
                        buffer: 250,
                    },
                   
                    scope: this,
                },                 
                
            }
        }, {
            text        :   this.colValueText || 'Value',
            itemId      :   'colValue',
            dataIndex   :   'value',
            flex        :   1,
            sortable    :   true,
            editor      :   {
                                allowBlank: false
                            },
            renderer    :   Bisque.ResourceTagger.BaseRenderer
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
                convert : function(value, record) {
                    // dima: show type and name for gobjects
                    if (record.raw instanceof BQGObject) {
                        var txt = [];
                        if (record.raw.type && record.raw.type != 'gobject') txt.push(record.raw.type);
                        if (record.raw.name) txt.push(record.raw.name); 
                        if (txt.length>0) return txt.join(': ');
                    }
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
                convert : this.getTooltip
            }, this.getStoreFields()],

            indexOf : function(record)
            {
                return this.tagTree.getView().indexOf(record);
            },

            applyModifications : function()
            {
                var nodeHash = this.tree.nodeHash, status = false;

                for(var node in nodeHash)
                    if(nodeHash[node].dirty)
                    {
                        status = true;
                        Ext.apply(nodeHash[node].raw, {'name': nodeHash[node].get('name'), 'value': nodeHash[node].get('value')});
                        nodeHash[node].commit();
                    }

                if (this.getRemovedRecords().length>0)
                    return true;

                return status;
            },

            /* Modified function so as to not delete the root nodes */
            onNodeAdded : function(parent, node)
            {
                var me = this,
                    proxy = me.getProxy(),
                    reader = proxy.getReader(),
                    data = node.raw || node[node.persistenceProperty],
                    dataRoot;
        
                Ext.Array.remove(me.removed, node);
        
                if (!node.isLeaf()) {
                    dataRoot = reader.getRoot(data);
                    if (dataRoot) {
                        me.fillNode(node, reader.extractData(dataRoot));
                        //delete data[reader.root];
                    }
                }
        
                if (me.autoSync && !me.autoSyncSuspended && (node.phantom || node.dirty)) {
                    me.sync();
                }                
            }
        });

        return this.store;
    },
    
    getTooltip : function(value, record)
    {
        if (record.raw instanceof BQGObject)
        {
            var txt = [];
            if (record.raw.type && record.raw.type != 'gobject') txt.push(record.raw.type);
            if (record.raw.name) txt.push(record.raw.name);                        
            if (txt.length>0) return txt.join(' : ');
        }    
        
        return record.data.name + ' : ' + record.data.value;
    },

    getStoreFields : function()
    {
        return {name : 'dummy', type : 'string'};
    },

    getToolbar : function()
    {
        var tbar = [
        {
            xtype : 'buttongroup',
            itemId : 'grpAddDelete',
            hidden : (this.viewMgr.state.btnAdd && this.viewMgr.state.btnDelete),
            items : [
            {
                itemId : 'btnAdd', 
                text : 'Add',
                hidden : this.viewMgr.state.btnAdd,
                scale : 'small',
                iconCls : 'icon-add',
                handler : this.addTags,
                disabled : this.tree.btnAdd,
                scope : this
            },
            {
                itemId : 'btnDelete', 
                text : 'Delete',
                hidden : this.viewMgr.state.btnDelete,
                scale : 'small',
                iconCls : 'icon-delete',
                handler : this.deleteTags,
                disabled : this.tree.btnDelete,
                scope : this
            }]
        },
        {
            xtype : 'buttongroup',
            itemId : 'grpImportExport',
            hidden : (this.viewMgr.state.btnImport && this.viewMgr.state.btnExport),
            items : [
            {
                itemId : 'btnImport', 
                text : 'Import',
                hidden : this.viewMgr.state.btnImport,
                scale : 'small',
                iconCls : 'icon-import',
                handler : this.importMenu,
                disabled : this.tree.btnImport,
                scope : this
            },
            {
                text : 'Export',
                scale : 'small',
                hidden : this.viewMgr.state.btnExport,
                disabled : this.tree.btnExport,
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
                        hidden : true,//this.viewMgr.state.btnGDocs,
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
        var child = { name : this.defaultTagName || '', value : this.defaultTagValue || '' };
        child[this.rootProperty] = [];

        var newNode = currentItem.appendChild(child);
        this.newNode = newNode;
        currentItem.expand();
        editor.startEdit(newNode, 0);
    },
    
    cancelEdit : function (grid, eOpts)
    {
        if (eOpts.record && eOpts.record.dirty)
        {
            eOpts.record.parentNode.removeChild(eOpts.record);
        }
    },    
    
    finishEdit : function(_editor, me)
    {
        if (me.record.raw instanceof BQObject)
        {
            if (this.autoSave)
            {
                this.saveTags(me.record.raw, true);
                me.record.data.qtip = this.getTooltip('', me.record);
                me.record.commit();
            }

            return;
        }
        
        this.editing = true;
        var newTag = new BQTag();
        newTag = Ext.apply(newTag,
        {
            name : me.record.data.name,
            value : me.record.data.value,
        });
        var parent = (me.record.parentNode.isRoot()) ? this.resource : me.record.parentNode.raw;
        parent.addtag(newTag);

        if (this.isValidURL(newTag.value))
        {
            newTag.type = 'link';
            me.record.data.type = 'link';
        }
            
        if (this.autoSave)
            this.saveTags(parent, true);

        me.record.raw = newTag;
        me.record.loaded = true;
        me.record.data.qtip = this.getTooltip('', me.record);
        me.record.commit();

        me.record.parentNode.data.iconCls = 'icon-folder';
        me.view.refresh();

        this.editing = false;
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
            if (!silent) BQ.ui.message('', 'Changes were saved successfully!');
        }
        else
            BQ.ui.message('', 'No records modified!');
    },
    
    importMenu : function(btn, e)
    {
        if (!btn.menu)
        {
            var menuItems = [];
            
            for (var i=0; i<BQApp.resourceTypes.length; i++)
            {
                menuItems.push({
                    text    :   'from <b>'+BQApp.resourceTypes[i].name+'</b>',
                    name    :   '/data_service/'+BQApp.resourceTypes[i].name,
                    handler :   this.importTags,
                    scope   :   this
                })
            }
            
            btn.menu = Ext.create('Ext.menu.Menu', {
                items   :   menuItems
            });
        }
        
        btn.showMenu();
    },
    
    importTags : function(menuItem)
    {
        var rb = new Bisque.ResourceBrowser.Dialog(
        {
            height      :   '85%',
            width       :   '85%',
            dataset     :   menuItem.name,
            viewMode    :   'ViewerLayouts',
            selType     :   'SINGLE',
            listeners   :
            {
                'Select' : function(me, resource)
                {
                    if (resource instanceof BQTemplate)
                        BQ.TemplateManager.createResource({name: '', noSave:true}, Ext.bind(this.onResourceCreated, this), resource.uri+'?view=deep');
                    else
                    {
                        if(resource.tags.length > 0)
                            this.appendTags(resource.tags);
                        else
                            resource.loadTags(
                            {
                                cb : callback(this, "appendTags"),
                            });
                    }
                },

                scope : this
            },
        });
    },
    
    onResourceCreated : function(resource, template)
    {
        this.resource.type = resource.type;
        this.appendTags(resource.tags);
        
        var resource = this.copyTemplate(template, this.resource);
        this.resource = resource;
    },
    
    appendTags : function(data)
    {
        this.tree.setLoading(true);
        
        if (data.length>0)
        {
            data = this.stripURIs(data);
            this.resource.tags = this.resource.tags.concat(data);
            this.addNode(this.tree.getRootNode(), data);
            
            if (this.autoSave)
                this.saveTags(null, true);
        }

        this.tree.setLoading(false);
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
    
    testAuth : function(user, loaded, permission)
    {
        if (user)
        {
            if (!loaded)
                this.resource.testAuth(user.uri, Ext.bind(this.testAuth, this, [user, true], 0));            
            else
            {
                if (permission)
                {
                    // user is authorized to edit tags
                    this.tree.btnAdd = false;
                    this.tree.btnDelete = false;
                    this.tree.btnImport = false;
        
                    this.editable = true;
                    
                    if (this.tree instanceof Ext.Component)
                    {
                        var tbar = this.tree.getDockedItems('toolbar')[0];
                        
                        tbar.getComponent('grpAddDelete').getComponent('btnAdd').setDisabled(false);
                        tbar.getComponent('grpAddDelete').getComponent('btnDelete').setDisabled(false);
                        tbar.getComponent('grpImportExport').getComponent('btnImport').setDisabled(false);
                    }
                }
            }
        }
        else if (user===undefined)
        {
            // User autentication hasn't been done yet
            BQApp.on('gotuser', Ext.bind(this.testAuth, this, [false], 1));
        }
    },
    
    isValidURL : function(url)
    {
        var pattern = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/
        return pattern.test(url);        
    },

    exportToXml : function()
    {
        var url = '/export/initStream?urls='
        url += encodeURIComponent(this.resource.uri+'?view=deep');
        url += '&filename='+(this.resource.name || 'document');
        
        window.open(url);
    },

    exportToCsv : function()
    {
        var url = '/stats/csv?url=';
        url += encodeURIComponent(this.resource.uri);
        url += '&xpath=%2F%2Ftag&xmap=tag-name-string&xmap1=tag-value-string&xreduce=vector';
        url += '&title=Name&title1=Value';
        url += '&filename='+(this.resource.name || 'document') + '.csv';
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
    extend  :   'Bisque.ResourceTagger',
    animate :   false,

    constructor : function(config)
    {
        config.rootProperty = 'gobjects';
        config.colNameText = 'GObject';
        config.colValueText = 'Vertices';
        config.tree = {btnExport : true};

        this.callParent(arguments);
    },

    loadResourceInfo : function(resource)
    {
        this.fireEvent('beforeload', this, resource);
        
        this.resource = resource;
        this.resource.loadGObjects(
        {
            cb: callback(this, "loadResourceTags"),
            depth: 'deep&wpublic=1'
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
                xtype: 'splitbutton',
                arrowAlign: 'right',
                text : 'Toggle selection',
                scale : 'small',
                iconCls : 'icon-uncheck',
                handler : this.toggleCheckTree,
                checked : true,
                scope : this,
                menu:
                {
                    items: [{
                        check: true,
                        text: 'Check all',
                        handler: this.toggleCheck,
                        scope: this,
                    }, {
                        check: false,
                        text: 'Uncheck all',
                        handler: this.toggleCheck,
                        scope: this,
                    }]
                }
            }]
        }];
        
        return buttons.concat(toolbar);
    },
    
    toggleCheckTree : function(button)
    {
        var rootNode = this.tree.getRootNode(), eventName;
        button.checked = !button.checked;

        if (button.checked)
            button.setIconCls('icon-uncheck')
        else
            button.setIconCls('icon-check')

        for (var i=0;i<rootNode.childNodes.length;i++)
        {
            eventName=(!rootNode.childNodes[i].get('checked'))?'Select':'Deselect';
            this.fireEvent(eventName, this, rootNode.childNodes[i]);
        }

        this.toggleTree(rootNode);
    },
    
    toggleCheck : function(button)
    {
        button.checked = button.check;
        var rootNode = this.tree.getRootNode(), eventName=(button.checked)?'Select':'Deselect';
        
        for (var i=0;i<rootNode.childNodes.length;i++)
            this.fireEvent(eventName, this, rootNode.childNodes[i]);

        this.checkTree(rootNode, button.checked);
    },
    
    appendFromMex : function(resQo) {
        // dima: deep copy the resq array, otherwise messes up with analysis
        var resQ = [];
        for (var i=0; i<resQo.length; i++)
            resQ[i] = resQo[i];
        
        // Only look for gobjects in tags which have value = image_url 
        for (var i=0;i<resQ.length;i++)
        {
            // the mex may have sub mexs
            if (resQ[i].resource.children && resQ[i].resource.children.length>0) {
                for (var k=0; k<resQ[i].resource.children.length; k++)
                    if (resQ[i].resource instanceof BQMex) {
                        var rr = Ext.create('Bisque.Resource.Mex', { resource : resQ[i].resource.children[k], });
                        resQ.push(rr);
                    }
                continue;
            }
                
            var outputsTag = resQ[i].resource.find_tags('outputs');
            
            if (outputsTag)
                this.appendGObjects(this.findGObjects(outputsTag, this.resource.uri), resQ[i].resource);
            else
                resQ[i].resource.loadGObjects({cb: Ext.bind(this.appendGObjects, this, [resQ[i].resource], true)});    
        }
    },
    
    findGObjects : function(resource, imageURI)
    {
        if (resource.value && resource.value == imageURI)
            return resource.gobjects;
            
        var gobjects = null;
        var t = null;
        for (var i=0; (t=resource.tags[i]) && !gobjects; i++)
            gobjects = this.findGObjects(t, imageURI); 

        return gobjects;
    },
    
    deleteGObject : function(index)
    {
        var root = this.tree.getRootNode();
        var g = root.getChildAt(index);
        root.removeChild(g, true);
        this.tree.getView().refresh();
    },
    
    appendGObjects : function(data, mex)
    {
        if (data && data.length>0)
        {
            if (mex)
            {
                var date = new Date();
                date.setISO(mex.ts);
                
                this.addNode(this.tree.getRootNode(), {name:data[0].name, value:Ext.Date.format(date, "F j, Y g:i:s a"), gobjects:data});
                this.fireEvent('onappend', this, data);
            }
            else
            {
                this.addNode(this.tree.getRootNode(), data);
                //this.fireEvent('onappend', this, data);
            }
        }
    },

    exportToXml : function()
    {
        //var gobject=this.tree.getRootNode(), selection = this.tree.getChecked();
        //debugger
        //this.exportTo('xml');
    },
    
    //exportToGDocs : Ext.emptyFn,

    exportToCsv : function()
    {
        //this.exportTo('csv');
    },
    
    exportTo : function(format)
    {
        format = format || 'csv';
        
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
                    url : gobject.uri+'?view=deep&format='+format,
                    success : Ext.bind(this.saveCSV, this, [format], true),
                    disableCaching : false 
                });
            }
        }
    },
    
    saveCSV : function(data, params, format)
    {
        this.csvData += '\n'+data.responseText;
        this.noFiles--;
        
        if (!this.noFiles)
            location.href = "data:text/attachment," + encodeURIComponent(this.csvData);
    },
    
    updateViewState : function(state)
    {
        
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
        if (this.context)
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
        
        switch(mode)
        {
            case 'ViewerOnly':
            {
                // all the buttons are hidden
                this.state = setHidden(this.state, true);
                this.state.editable = false;
                break;
            }
            case 'PreferenceTagger':
            {
                break;
            }
            case 'ReadOnly':
            {
                this.state.btnExport = false;
                this.state.btnXML = false;
                this.state.btnCSV = false;
                this.state.btnGDocs = false;
                this.state.editable = false;
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
                this.state.btnGDocs = false;
                this.state.btnXML = false;
                
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