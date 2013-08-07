/*
 * BQ.TagBrowser :
 * Browser the document tag structe in a directory browser manner
 * 
 * @example : 
 * 
 * @params :
 * 
 * @defaults :
 *  
 */

Ext.Loader.setConfig({enabled: true});
Ext.Loader.setPath('Ext.ux', '../extjs/examples/ux');
Ext.require(['Ext.ux.TabReorderer']);

Ext.define('BQ.TagBrowser',
{
    extend      :   'Ext.tab.Panel',
    layout      :   'fit',
    plain       :   true,
    border      :   false,
    autoDestroy :   false,
    plugins     :   Ext.create('Ext.ux.TabReorderer'),
    title       :   'Directory Browser',

    defaults    :   {
                        border      :   false,
                        header      :   false,
                        closable    :   true,
                        reorderable :   false,
                        frame       :   true,
                        padding     :   6,
                        layout      :   {
                                            type    :   'vbox',
                                            align   :   'stretch'
                                        },
                        closeText   :   'Disable filter',
                    },
    initComponent : function()
    {
        this.callParent(arguments);
        this.readPreferences();
    },
    
    readPreferences : function(preferences)
    {
        if (!preferences)
        {
            BQ.Preferences.get({
                type        :   'user',
                key         :   'TagBrowser',
                callback    :   Ext.bind(this.readPreferences, this)
            });
            
            return;
        }
        
        this.getPlugin().on('drop', this.filterSwap, this);
        this.refresh(preferences);
    },

    // Reset all filters and reinstantiate from the original list
    refresh : function(preferences)
    {
        // Init state
        this.config.preferences = preferences;
        this.config.tagBrowser = this;
        this.state = Ext.create('BQ.TagBrowser.State', this.config);
        this.relayEvents(this.state, ['QUERY_CHANGED']);
        
        // Remove all existing filters
        this.removeAll();
        
        // Button to add new filters to the collection
        this.add(this.btnAdd());

        // Init all filters with the tagList
        for (var i=0; i<this.state.getLength(); i++)
            this.addFilter(i);
        
        // Activate the first filter
        var firstFilter = this.getComponentAt(0);
        
        if (firstFilter)
        {
            firstFilter.activate();
            this.state.queryChanged();
        }
        
        this.setActiveFilter(0);
    },
    
    addFilter : function(index)
    {
        // Add a filter to the directory browser
        this.insert(this.items.getCount()-1,
        {
            xtype       :   'BQ.TagBrowser.Filter',
            state       :   this.state,
            disabled    :   true,
            data        :   {
                                index   :   index,
                                tag     :   this.state.getTagAt(index),
                                value   :   ''
                            },
            listeners   :   {
                                scope   :   this,
                                SELECT  :   this.filterSelect,
                                CLOSE   :   this.filterClose,
                                CHANGE  :   this.filterChange,   
                            }
        });

        // Add the arrow next to the tabs
        this.insert(this.items.getCount()-1,
        {
            iconCls     :   'icon-arrow',
            reorderable :   false,
            closable    :   false,
            disabled    :   true,
            tabConfig   :   { cls : 'tab-arrow' },
        });
    },
    
    filterSelect : function(filter, grid, record)
    {
        this.filterDisable(filter.getIndex()+1);

        if (filter.getIndex()+1<this.state.getLength())
        {
            this.getComponentAt(filter.getIndex()+1).activate();
            this.setActiveTab(this.mapIndex(filter.getIndex()+1));
        }

        // Raise Browser Event
        this.state.queryChanged();
    },
    
    filterClose : function(filter)
    {
        this.filterDisable(filter.getIndex()+1);
        
        if (filter.getIndex() == 0)
        {
            filter.activate();
            this.setActiveTab(0);
        }
        else
        {
            this.setActiveTab(this.mapIndex(filter.getIndex()-1));
            
            // Remove the filter from the state
            this.state.removeTagAt(filter.getIndex());
            
            this.remove(this.getComponent(this.mapIndex(filter.getIndex())+1), false);
            this.remove(filter, false);
            
            // Recreate indices
            this.recreateIndices();
        }
        
        // Raise Browser Event
        this.state.queryChanged();
    },
    
    filterDisable : function(index)
    {
        for (var i = index; i<this.state.getLength(); i++)
            this.getComponentAt(i).clear();
    },
    
    filterChange : function(filter, combo, record)
    {
        this.filterDisable(filter.getIndex()+1);
        
        filter.clear();
        filter.activate();

        this.setActiveTab(this.mapIndex(filter.getIndex()));
        
        // Raise Browser Event
        this.state.queryChanged();
    },
    
    filterSwap : function(plugin, browser, srcTab, oldPos, newPos)
    {
        if (oldPos==newPos)
            return;
        
        // Recreate index of every filter based on new position
        this.recreateIndices();

        // Reload browser
        this.state.queryChanged();
    },
    
    recreateIndices : function()
    {
        for (var i=0, newTagList=[]; i<this.state.getLength(); i++)
        {
            var filter = this.getComponentAt(i);
            filter.setIndex(i);
            newTagList.push(filter.getTag());
        }
        
        this.state.setTagList(newTagList);
    },
    
    btnAdd : function()
    {
        this.tagCombo = Ext.create('Ext.form.field.ComboBox', {
            padding         :   '10 0 0 0',
            emptyText       :   'Select a tag...',
            store           :   Ext.create('Ext.data.ArrayStore', { fields : ['name'] }),
            queryMode       :   'local',
            displayField    :   'name',
            typeAhead       :   true,
            forceSelection  :   true,
        });
         
        this.loadData();
        
        return {
                    iconCls     :   'icon-tab-add',
                    tabConfig   :   { cls : 'tab-add' },
                    closable    :   false,
                    reorderable :   false,
                    items       :   [ this.tagCombo, {
                                        xtype   :   'button',
                                        height  :   30,
                                        text    :   'Add Filter',
                                        handler :   this.filterAdd,
                                        scope   :   this,        
                                    }]
                }
    },
    
    loadData : function(tagData)
    {
        if (!tagData)
            BQFactory.request({
                uri     :   this.state.getTagNameURI(),
                cb      :   Ext.bind(this.loadData, this),
                cache   :   false
            });
        else
        {
            var tagNames = [];
            
            for (var i=0; i<tagData.tags.length; i++)
                tagNames.push([tagData.tags[i].name || '']);
        
            this.tagCombo.getStore().loadData(tagNames);
        }
    },
    
    filterAdd : function(btn)
    {
        var value = this.tagCombo.getValue();
        
        if (Ext.isEmpty(value))
            BQ.ui.message('Add Filter', 'Please select a value from the drop down first.');
        else
        {
            var index = this.state.getLength();
            var disabled = this.getComponentAt(index-1).isDisabled();
            var record = this.getComponentAt(index-1).grid.getSelectionModel().getSelection();
            
            this.state.setTagAt(index, value);
            this.addFilter(index);
            
            if (!disabled && !Ext.isEmpty(record))
            {
                this.getComponentAt(index).activate();
                this.setActiveTab(this.mapIndex(index));
            }
        }
    },
    
    // Utility functions
    getLength : function()
    {
        // -1 due to the Add button
        // /2 due to the arrow tabs inbetween
          
        return (this.items.getCount()-1) / 2;
    },
    
    getComponentAt : function(index) {
        return this.tabBar.getComponent(this.mapIndex(index)).card;
    },
    
    setActiveFilter : function(index) {
        this.setActiveTab(this.mapIndex(index));
    },
    
    // Return actual filter index while ignoring indices for arrow tabs in-between
    mapIndex : function(index) {
        return 2*index;
    },
    
});


Ext.define('BQ.TagBrowser.Filter',
{
    extend  :   'Ext.panel.Panel',
    alias   :   'widget.BQ.TagBrowser.Filter',

    initComponent : function()
    {
        this.callParent(arguments);
        this.on('beforeclose', this.closeFilter, this);
        this.setTitle(Ext.String.capitalize(this.state.getTagAt(this.data.index)));
        
        this.addComponents();
    },
    
    addComponents : function()
    {
        this.combo = Ext.create('Ext.form.field.ComboBox',
        {
            forceSelection  :   true,
            displayField    :   'name',
            store           :   Ext.create('Ext.data.ArrayStore', { fields : ['name'] }),
            queryMode       :   'local',
            typeAhead       :   true,
            hidden          :   true,
            emptyText       :   'Loading...',
            listeners       :   {
                                    scope   :   this,
                                    select  :   this.selectTag,
                                }
        });
        
        this.grid = Ext.create('Ext.grid.Panel',
        {
            store       :   Ext.create('Ext.data.ArrayStore', { fields : ['value'] }),
            border      :   false,
            hideHeaders :   true,
            flex        :   1,
            listeners   :   {
                                scope       :   this,
                                itemclick   :   this.selectValue,
                            },
            columns     :   [{

                                text        :   'Value',
                                dataIndex   :   'value',
                                flex        :   1,
                            }],
        });
        
        this.add([this.combo, this.grid]);
    },
    
    activate : function()
    {
        this.setDisabled(false);
        this.reorderable = true;
        this.tab.reorderable = true;
        this.loadValues();
        this.loadNames();
    },
    
    clear : function()
    {
        this.setDisabled(true);
        this.tab.reorderable = false;
        this.setValue('');
        this.grid.getStore().loadData([]);
        this.setTitle(Ext.String.capitalize(this.getTag()));
    },
    
    closeFilter : function()
    {
        this.clear();
        this.fireEvent('CLOSE', this);
        return false;
    },
    
    /* Utility functions */
    
    selectTag : function(combo, record)
    {
        this.setTag(record[0].get('name'));
        this.fireEvent('CHANGE', this, combo, record);
    },
    
    selectValue : function(grid, record)
    {
        this.setValue(record.get('value'));
        this.setTitle(this.getValue());
        this.fireEvent('SELECT', this, grid, record);
    },

    getTag : function() {
        return this.data.tag;
    },
    
    setTag : function(tagName) {
        this.data.tag = tagName;
        this.state.setTagAt(this.getIndex(), tagName);
    },
    
    getValue : function() {
        return this.data.value;
    },
    
    setValue : function(value) {
        this.data.value = value;
    },
    
    getIndex : function() {
        return this.data.index;
    },
    
    setIndex : function(idx) {
        this.data.index = idx;
    },

    loadNames : function(tagData)
    {
        if (!tagData)
            BQFactory.request({
                uri     :   this.state.getTagNameURI(),
                cb      :   Ext.bind(this.loadNames, this),
                cache   :   false
            });
        else
        {
            var tagNames = [];
            
            for (var i=0; i<tagData.tags.length; i++)
                tagNames.push([tagData.tags[i].name || '']);
        
            this.combo.store.loadData(tagNames);
            this.combo.setValue(this.getTag());
            
        }
    },
    
    loadValues : function(tagData)
    {
        if (!tagData)
            BQFactory.request({
                uri     :   this.state.getTagValueURI(this.getIndex()),
                cb      :   Ext.bind(this.loadValues, this),
                cache   :   false
            });
        else
        {
            var tagValues = [];
            
            for (var i=0; i<tagData.tags.length; i++)
                tagValues.push([tagData.tags[i].value || '']);
        
            this.grid.getStore().loadData(tagValues);            
        }
    },
    
});


Ext.define('BQ.TagBrowser.State',
{
    extend  :   'Ext.util.Observable',
    
    constructor : function(config)
    {
        this.callParent(arguments);
        
        Ext.apply(this,
        {
            tagList         :   this.tagList        ||  this.preferences.tagList        ||  ['Project', 'Experimenter'],
            resourceType    :   this.resourceType   ||  this.preferences.resourceType   ||  'image',
            resourceServer  :   this.resourceServer ||  this.preferences.resourceServer ||  'data_service',
            includePublic   :   this.includePublic  ||  false,
        })
    },
    
    setTagList : function(tagList) {
        this.tagList = tagList;
    },
    
    getLength : function() {
        return this.tagList.length;
    },
    
    getTagAt : function(index) {
        return this.tagList[index] || null;
    },

    setTagAt : function(index, tagName) {
        this.tagList[index] = tagName;
    },
    
    removeTagAt : function(index) {
        this.tagList.splice(index, 1);
    },
    
    tagOrder : function()
    {
        var tagOrder = "", tpl = '"{0}":asc,';
        
        for (var i=0; i<this.getLength(); i++)
        {
            var filter = this.tagBrowser.getComponentAt(i);
            if (!filter.isDisabled())
                tagOrder = tagOrder + Ext.String.format(tpl, encodeURIComponent(filter.getTag()));
        }
            
        return tagOrder.substring(0, tagOrder.length - 1);
    },
    
    tagQuery : function()
    {
        var tagQuery = "", tpl = '"{0}":"{1}" AND ';
        
        for (var i=0; i<this.getLength(); i++)
        {
            var filter = this.tagBrowser.getComponentAt(i);
            if (!filter.isDisabled())
                tagQuery = tagQuery + Ext.String.format(tpl, encodeURIComponent(filter.getTag()), encodeURIComponent(filter.getValue()));
        }
            
        return tagQuery.substring(0, tagQuery.length - 4);
    },
    
    queryChanged : function()
    {
        var uri =
        {
            baseURL     :   Ext.String.format('/{0}/{1}', this.resourceServer, this.resourceType),
            offset      :   0,
            tag_query   :   this.tagQuery() || '',
            tag_order   :   this.tagOrder() || '',
            wpublic     :   this.includePublic
        };
        
        this.fireEvent('QUERY_CHANGED', uri);
    },
    
    getTagNameURI : function()
    {
        var queryTpl = '/{0}/{1}?tag_names=1&wpublic={3}';
        return Ext.String.format(queryTpl, this.resourceServer, this.resourceType, this.includePublic); 
    },
    
    getTagValueURI : function(index)
    {
        var queryTpl = '/{0}/{1}?tag_values={2}&tag_query={3}&wpublic={4}';
        
        return Ext.String.format(queryTpl, this.resourceServer, this.resourceType,
                    encodeURIComponent(this.tagBrowser.getComponentAt(index).getTag()), this.tagQuery(), this.includePublic); 
    }
});
