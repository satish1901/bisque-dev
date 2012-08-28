// Needs to be rewritten for better generics as and when the specs become clear
Ext.define('Bisque.ResourceBrowser.Organizer',
{
    extend : 'Ext.panel.Panel',
    defaults: { border: 0, },
    constructor : function()
    {
        Ext.apply(this,
        {
            parentCt    : arguments[0].parentCt,
            dataset     : arguments[0].dataset,
            wpublic     : arguments[0].wpublic,
            msgBus      : arguments[0].msgBus,
            uri         : arguments[0].browser.uri,
            tag_order   : arguments[0].browser.uri.tag_order || '',
            tag_query   : arguments[0].browser.uri.tag_query || '',

            title       : 'Organizer',
            width       : 305,
            itemId      : 'organizerCt',
            layout      : 'accordion',
            border      : false,
            tbar        :   {
                                items : [
                                {
                                    iconCls : 'icon-add',
                                    text : 'Add',
                                    tooltip : 'Add new filter',
                                    handler : this.AddFilter,
                                    scope : this
                                },
                                {
                                    iconCls : 'icon-refresh',
                                    text : 'Reset',
                                    tooltip : 'Reset all filters',
                                    handler : this.resetFilters,
                                    scope : this
                                }]
                            },

            existingTags : new Array(),
            items : [],
            tools : [
            {
                type : 'left',
                title : 'Collapse organizer panel',
                tooltip : 'Collapse organizer panel',
                handler : function()
                {
                    this.parentCt.hideCollapseTool = false;
                    this.parentCt.collapse();
                },
                scope : this
            }]
        });

        this.callParent(arguments);
        
        this.on('afterrender', function()
        {
            this.initFilters(this.uri);
            this.ManageEvents();
        }, this, {single : true});
    },
    
    initFilters : function(uri)
    {
        this.tag_order = uri.tag_order || '';
        this.tag_query = uri.tag_query || '';
        
        this.tag_order = this.tag_order.replace(/"/g,'').split(',');
        this.tag_query = this.parseTagQuery(this.tag_query.replace(/"/g,''));

        var filterCount=0;
        
        for(var i=0;i<this.tag_order.length;i++)
        {
            if (this.tag_order[i].indexOf('@ts')!=-1)   // Ignore time-stamp from tag_order
                continue;
                
            filterCount++;
            
            var pair = this.tag_order[i].split(':');
            var filterCt = new Bisque.ResourceBrowser.Organizer.TagFilterCt({parent: this, tag_order: pair, tag_query: this.tag_query[pair[0]] || ''});
            this.add(filterCt);
    
            filterCt.addEvents('onFilterDragDrop');
            this.relayEvents(filterCt, ['onFilterDragDrop']);
            //filterCt.expand(true);
        }
        
        if (filterCount==0) // Add a blank filter if no tag_query was used to initialize the Organizer
            this.AddFilter();
    },
    
    parseTagQuery : function(tag_query)
    {
        var obj={}, arr, pair, pairs, query = tag_query.split(' AND ');
        
        
        for (var i=0;i<query.length;i++)
        {
            pairs = query[i].split(' OR ');
            arr=[];
            for (var j=0;j<pairs.length;j++)
            {
                pair = pairs[j].split(':');
                arr.push(pair[1]);
            }
            obj[pair[0]] = arr || '';
        }
        
        return obj;
    },

    AddFilter : function()
    {
        var filterCt = new Bisque.ResourceBrowser.Organizer.TagFilterCt(
        {
            parent : this
        });
        this.add(filterCt);

        filterCt.addEvents('onFilterDragDrop');
        this.relayEvents(filterCt, ['onFilterDragDrop']);
        filterCt.expand(true);
    },

    ManageEvents : function()
    {
        this.msgBus.on('Organizer_OnCBSelect', function(args)
        {
            this.CBSelect(args);
            this.ReloadBrowserData();
        }, this);

        this.msgBus.on('Organizer_OnGridSelect', function()
        {
            this.GridSelect();
            this.ReloadBrowserData();
        }, this);

        this.on('onFilterDragDrop', this.ReorderFilters, this);
    },

    ReorderFilters : function(opts)
    {
        var keySource = this.items.keys.indexOf(opts.source), keySink = this.items.keys.indexOf(opts.sink);
        var sourceEl = Ext.fly(opts.source);
        var sinkEl = this.getComponent(keySink).el;

        // If source item (the one being dragged) was below the sink item
        if(this.items.indexOf(keySink) < this.items.indexOf(keySource))
        {
            sourceEl.insertBefore(sinkEl);
            this.items.insert(keySource, this.items.removeAt(keySink));
        }
        else
        {
            sourceEl.insertAfter(sinkEl);
            this.items.insert(keySource + 1, this.items.removeAt(keySink));
        }
        this.ReloadBrowserData();
    },

    CBSelect : function(child)
    {
        this.PopulateGrid(false, child);

        // Add previously selected tag to other child filter containers
        this.AddNewTag(child.oldTag, child.getId());

        // Remove selected tags from other child filter containers
        this.existingTags.push(child.tag);
        this.RemoveExistingTags(child.tag, child.getId());
    },

    GridSelect : function()
    {
        // Repopulate all other grids based on new tag_query
        for(var i = 0; i < this.items.length; i++)
        {
            if(!(this.getComponent(i).value.length > 0))
                this.PopulateGrid(false, this.getComponent(i));
            else
                continue;
        }
    },

    ReloadBrowserData : function()
    {
        var uri =
        {
            offset : 0,
            tag_query : this.GetTagQuery(),
            tag_order : this.GetTagOrder()
        };
        this.msgBus.fireEvent('Browser_ReloadData', uri);
        this.msgBus.fireEvent('SearchBar_Query', this.GetTagQuery());
    },

    PopulateGrid : function(loaded, child, resourceData)
    {
        if(!loaded)
        {
            child.grid.setLoading({msg:''});
            var query = this.GetTagQuery();
            var uri = Ext.String.urlAppend(this.dataset, '{0}=' + child.tag + '&wpublic=' + this.browser.browserParams.wpublic + (query.length?'&tag_query='+query:''));
            var uri = Ext.String.format(uri, (child.tagType=='tag'?'tag_values':'gob_names'));
            
            BQFactory.load(uri, callback(this, 'PopulateGrid', true, child));
        }
        else
        {
            child.grid.setLoading(false);
            // Populate child filter's grid
            var tagArr = [];
            var data=(child.tagType=='tag'?resourceData.tags:resourceData.gobjects);
            
            for(var i = 0; i < data.length; i++)
                tagArr.push(new Ext.grid.property.Property(
                {
                    name : i + 1,
                    value : (child.tagType=='tag'?data[i].value:data[i].name)
                }));

            child.grid.store.loadData(tagArr);
            
            // Initialize the grid with tag_query if provided
            var index, selector = child.grid.getSelectionModel();
            for (var i=0;i<child.tag_query.length;i++)
            {
                index = child.grid.store.findExact('value', child.tag_query[i]);
                selector.select(child.grid.store.getAt(index), true);
                child.OnGridSelect();
            }
        }
    },

    AddNewTag : function(tag, skipCt)
    {
        if(this.existingTags.indexOf(tag) >= 0)
        {
            this.existingTags.splice(this.existingTags.indexOf(tag), 1);
            for(var i = 0; i < this.items.length; i++)
                if(this.getComponent(i).getId() != skipCt)
                {
                    this.getComponent(i).tagCombo.store.loadData([tag], true);
                    this.getComponent(i).SortComboBox('ASC');
                }
        }
    },

    RemoveExistingTags : function(tag, skipCt)
    {
        // Remove currently selected filter tag from all other combo boxes
        for(var i = 0; i < this.items.length; i++)
        {
            if(this.getComponent(i).getId() != skipCt)
            {
                var cb = this.getComponent(i).tagCombo;
                cb.store.remove(cb.findRecord(cb.displayField, tag));
            }
        }
    },

    GetTagOrder : function()
    {
        var tagOrder = "";
        for(var i = 0; i < this.items.length; i++)
        {
            if(this.getComponent(i).tag != "" && this.getComponent(i).tagType=='tag') 
                tagOrder = tagOrder + '"' + encodeURIComponent(this.getComponent(i).tag) + '":' + (this.getComponent(i).sortOrder == "" ? 'asc' : this.getComponent(i).sortOrder) + ",";
            else
                continue;
        }
        return tagOrder.substring(0, tagOrder.length - 1);
    },

    GetTagQuery : function()
    {
        var tagQuery = "";
        for(var i = 0; i < this.items.length; i++)
        {
            var pair = this.getComponent(i).GetTagValuePair()
            if(pair != "")
                tagQuery += pair + " AND ";
        }
        return tagQuery.substring(0, tagQuery.length - 5);
    },

    resetFilters : function()
    {
        while(this.items.length != 0)
            this.getComponent(0).destroy();
    }
});



/**
 * @class Bisque.ResourceBrowser.Organizer.TagFilterCt : Generates tag filters
 *        based on existing tag queries
 * @extends Ext.Panel
 */
Ext.define('Bisque.ResourceBrowser.Organizer.TagFilterCt',
{
    extend : 'Ext.panel.Panel',
    cls: 'organizer-filter',
    constructor : function()
    {
        Ext.apply(this,
        {
            layout :
            {
                type : 'vbox',
                align : 'stretch'
            },
            parent : arguments[0].parent,
            tag_order : arguments[0].tag_order || '',
            tag_query : arguments[0].tag_query || '',
            tag : "",
            oldTag : "",
            sortOrder : "",
            value : new Array(),
            tagCombo : [],
            grid : [],
            
            //bodyStyle : 'background : #D9E7F8',
            titleCollapse : true,
            collapsible : true,
            hideCollapseTool : true,
            frame : true,
            border : false,
            tools : [
            {
                type : 'up',
                tooltip : 'Sort ascending',
                handler : function()
                {
                    this.sortOrder = 'asc';
                    this.SetTitle();
                    this.ownerCt.ReloadBrowserData();
                },

                scope : this
            },
            {
                type : 'down',
                tooltip : 'Sort descending',
                handler : function()
                {
                    this.sortOrder = 'desc';
                    this.SetTitle();
                    this.ownerCt.ReloadBrowserData();
                },

                scope : this
            },
            {
                type : 'close',
                tooltip : 'Close this filter',
                handler : this.destroy,
                scope : this
            }]
        });

        this.callParent(arguments);

        this.on('afterrender', function(thisCt)
        {
            var ds = new Ext.dd.DragSource(thisCt.id,
            {
                dragData : thisCt.id
            });
            ds.setHandleElId(thisCt.header.id);
            var dt = new Ext.dd.DropTarget(thisCt.id,
            {
                filterCt : this,
                notifyDrop : function(source, e, data)
                {
                    this.filterCt.fireEvent('onFilterDragDrop',
                    {
                        source : data,
                        sink : this.id
                    });
                }
            });
        }, this);

        this.GenerateComponents();
        this.GetTagList(false);
    },

    SetTitle : function()
    {
        var tag = this.tag || '';
        tag += this.sortOrder ? ':'+this.sortOrder : '';
        tag += this.value.length!=0 ? ':'+this.value : '';
        
        this.setTitle('<span class="TagStyle">' + tag + '</span>');
    },

    SortComboBox : function(dir)
    {
        this.tagCombo.store.sort(this.tagCombo.displayField, dir);
    },

    GetTagList : function(loaded, type, tagData)
    {
        if(!loaded)
        {
            var query = this.parent.GetTagQuery();
            
            var uri = Ext.String.urlAppend(this.parent.dataset,  
                        '{0}=1&wpublic=' 
                      + this.parent.browser.browserParams.wpublic
                      + (query.length?'&tag_query='+query:'')); 
            
            BQFactory.load(Ext.String.format(uri, 'tag_names'), Ext.bind(this.GetTagList, this, [true, 'tag'], 0));
            BQFactory.load(Ext.String.format(uri, 'gob_types'), Ext.bind(this.GetTagList, this, [true, 'gobject'], 0));
        }
        else if (type=='tag')
        {
            var tagArr = [];
            for( i = 0; i < tagData.tags.length; i++)
                tagArr.push(
                {
                    "name" : (tagData.tags[i].name) ? tagData.tags[i].name.toString() : '',
                    "value": 'tag'
                });
            this.tagArr = tagArr;
            this.tagArrLoaded = true;
        }
        else if (type=='gobject')
        {
            var gobArr = [];
            for( i = 0; i < tagData.gobjects.length; i++){
                var name = tagData.gobjects[i].type || '';
                gobArr.push(
                {
                    "name" : name.toString(),
                    "value": 'gobject'
                });
            }
            this.gobArr = gobArr;
            this.gobArrLoaded = true;
        }
        if (this.tagArrLoaded && this.gobArrLoaded)
        {
            this.tagCombo.store.loadData(this.tagArr.concat(this.gobArr), false);
            this.tagCombo.setLoading(false);

            // Remove already selected tags from the just added filter
            // container
            for(var i = 0; i < this.parent.existingTags.length; i++)
                this.tagCombo.store.remove(this.tagCombo.findRecord(this.tagCombo.displayField, this.parent.existingTags[i]));

            // Initialize the filter if provided with tag_order/tag_query
            if (this.tag_order.length)
            {
                this.tagCombo.select(this.tag_order[0]);
                this.tagCombo.fireEvent('Select', this.tagCombo, true);
            }

            this.SortComboBox('ASC');
        }
    },

    GenerateComponents : function()
    {
        this.tagCombo = Ext.create('Ext.form.field.ComboBox',
        {
            editable : false,
            forceSelection : true,
            displayField : 'name',
            store : Ext.create('Ext.data.Store',
            {
                model   : 'Ext.grid.property.Property',
                sorters :   [{
                                property: 'value',
                                direction: 'DESC'
                            }, {
                                property: 'name',
                                direction: 'ASC'
                            }],           
            }),
            listConfig  :   {
                                getInnerTpl : function()
                                {
                                    return ['<tpl if="value==&quot;gobject&quot;">' +
                                                '<div>' +
                                                    '<p class="alignLeft">{name}</p>' + 
                                                    '<p class="alignRightGobject">gobject</p>' +
                                                    '<div style="clear: both;"></div>' +
                                                '</div>' +
                                            '<tpl else>' +
                                                '<div>' +
                                                    '<p class="alignLeft">{name}</p>' + 
                                                    '<p class="alignRightTag">tag</p>' +
                                                    '<div style="clear: both;"></div>' +
                                                '</div>' +
                                            '</tpl>'];
                                }
                            },
            emptyText : 'Select a tag...',
            queryMode : 'local',
            listeners :
            {
                'select' : this.OnCBSelect,
                scope : this
            }
        });

        this.grid = Ext.create('Ext.grid.Panel',
        {
            store : Ext.create('Ext.data.Store',
            {
                model : 'Ext.grid.property.Property'
            }),
            hideHeaders : true,
            multiSelect : true,
            flex : 1,
            border : 0,

            viewConfig :
            {
                emptyText : 'No data to display',
                forceFit : true,
                scrollOffset : 2
            },

            plugins : new Ext.ux.DataTip(
            {
                tpl : '<div>{value}</div>'
            }),

            listeners :
            {
                'cellclick' : this.OnGridSelect,
                scope : this
            },

            columns : [
            {
                text : 'Tag',
                dataIndex : 'name',
                hidden: true
            },
            {
                text : 'Value',
                flex : 1,
                dataIndex : 'value'
            }]
        });

        this.add([this.tagCombo, this.grid]);
        
    },

    GetSelection : function()
    {
        var selection = this.grid.getSelectionModel().getSelection();

        var dataToSend = new Array();
        for(var i = 0; i < selection.length; i++)
        dataToSend.push(selection[i].data.value);

        return dataToSend;
    },

    GetTagValuePair : function()
    {
        if  (this.tagType=='gobject')
        {
            if (this.value.length>0)
            {
                var str = "";
                for(var i = 0; i < this.value.length; i++)
                    str += '"' + encodeURIComponent(this.tag) + '"::"' + encodeURIComponent(this.value[i]) + '": OR ';
                return str.substring(0, str.length - 4);
            }
            else if (this.tag!="")
                return '"'+encodeURIComponent(this.tag)+'":::';
            else
                return "";
        }
        else
        {
            if(this.value.length > 0)
            {
                var str = "";
                for(var i = 0; i < this.value.length; i++)
                    str += '"' + encodeURIComponent(this.tag) + '":"' + encodeURIComponent(this.value[i]) + '" OR ';
                return str.substring(0, str.length - 4);
            }
            else
                return "";
        }
    },

    Reinitialize : function()
    {
        this.removeAll(true);

        this.ownerCt.AddNewTag(this.tag, this.getId());
        this.tag = "";
        this.oldTag = "";
        this.value = [];

        this.SetTitle();
        this.GenerateComponents();
        this.GetTagList(false);

        this.ownerCt.ReloadBrowserData();
    },

    destroy : function()
    {
        if(this.ownerCt)
            this.ownerCt.AddNewTag(this.tag, this.getId());
        this.removeAll(true);

        this.tag = "";
        this.oldTag = "";
        this.value = [];

        if(this.ownerCt)
            this.ownerCt.ReloadBrowserData();

        this.callParent(arguments);
    },

    /* Event handlers */
    OnCBSelect : function(combo, silent)
    {
        if(this.tag != combo.getRawValue())
        {
            this.oldTag = this.tag;
            this.tag = combo.getRawValue();
            this.tagType = combo.lastSelection[0].data.value;
            this.value = [];
            this.SetTitle();

            if (silent)
                this.parent.msgBus.fireEvent('Organizer_OnCBSelect', this);
        }
    },

    OnGridSelect : function()
    {
        this.value = this.GetSelection();
        this.SetTitle();
        this.parent.msgBus.fireEvent('Organizer_OnGridSelect');
    }
});
