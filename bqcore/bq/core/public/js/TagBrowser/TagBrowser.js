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
Ext.define('BQ.TagBrowser',
{
    extend      :   'Ext.tab.Panel',
    layout      :   'fit',
    //frame       :   true,
    plain       :   true,
    border      :   false,
    //padding     :   6,
    autoDestroy :   false,

    title       :   'Directory Browser',

    defaults    :   {
                        border      :   false,
                        header      :   false,
                        closable    :   true,
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
        
        this.config.preferences = preferences;
        this.config.tagBrowser = this;
        this.state = Ext.create('BQ.TagBrowser.State', this.config);
        this.relayEvents(this.state, ['QUERY_CHANGED']);
        
        this.refresh();
    },
    
    refresh : function()
    {
        // Remove all existing filters
        this.removeAll();
        
        // Init all filters with the tagList
        for (var i=0; i<this.state.getLength(); i++)
        {
            this.add(
            {
                xtype       :   'BQ.TagBrowser.Filter',
                state       :   this.state,
                disabled    :   true,
                data        :   {
                                    index   :   i,
                                    tag     :   this.state.tagAt(i),
                                    value   :   ''
                                },
                listeners   :   {
                                    scope   :   this,
                                    SELECT  :   this.filterSelect,
                                    CLOSE   :   this.filterClose,   
                                }
            });

            // Add the arrow next to the tabs
            if (i!=this.state.getLength()-1)            
                this.add({
                    iconCls     :   'icon-arrow',
                    closable    :   false,
                    disabled    :   true,
                    tabConfig   :   { cls : 'tab-arrow' },
                });
        }
        
        // Activate the first filter
        var filter = this.getComponent(this.mapIndex(0));
        
        if (filter)
        {
            filter.activate();
            this.state.queryChanged();
        }
        
        this.setActiveTab(this.mapIndex(0));
         
    },
    
    // Return actual filter index while ignoring indices for arrow tabs in-between
    mapIndex : function(index) {
        return 2*index;
    },
    
    filterSelect : function(filter, grid, record)
    {
        this.filterDisable(filter.getIndex()+1);

        if (filter.getIndex()+1<this.state.getLength())
        {
            this.getComponent(this.mapIndex(filter.getIndex()+1)).activate();
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
            this.setActiveTab(this.mapIndex(filter.getIndex()-1));
        
        // Raise Browser Event
        this.state.queryChanged();
    },
    
    filterDisable : function(index)
    {
        for (var i = index; i<this.state.getLength(); i++)
            this.getComponent(this.mapIndex(i)).clear();
    }
});


Ext.define('BQ.TagBrowser.Filter',
{
    extend  :   'Ext.panel.Panel',
    alias   :   'widget.BQ.TagBrowser.Filter',

    initComponent : function()
    {
        this.callParent(arguments);
        this.on('beforeclose', this.closeFilter, this);
        this.setTitle(Ext.String.capitalize(this.state.tagAt(this.data.index)));
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
            emptyText       :   'Loading...',
            listeners       :   {
                                    //'select'    :   this.OnCBSelect,
                                    scope       :   this
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
    
    selectValue : function(grid, record)
    {
        this.setValue(record.get('value'));
        this.setTitle(this.getValue());
        this.fireEvent('SELECT', this, grid, record);
    },
    
    activate : function()
    {
        this.setDisabled(false);
        this.loadValues();
        this.loadNames();
    },
    
    clear : function()
    {
        this.setDisabled(true);
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
    
    getTag : function() {
        return this.data.tag;
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
            currentIndex    :   0,
            tagList         :   this.tagList        ||  this.preferences.tagList        ||  ['Project', 'Experimenter'],
            resourceType    :   this.resourceType   ||  this.preferences.resourceType   ||  'image',
            resourceServer  :   this.resourceServer ||  this.preferences.resourceServer ||  'data_service',
            includePublic   :   this.includePublic  ||  false,
        })
    },
    
    getLength : function() {
        return this.tagList.length;
    },
    
    tagAt : function(index) {
        return this.tagList[index] || null;
    },
    
    tagOrder : function()
    {
        var tagOrder = "", tpl = '"{0}":asc,';
        
        for (var i=0; i<this.getLength(); i++)
        {
            var filter = this.tagBrowser.getComponent(this.tagBrowser.mapIndex(i));
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
            var filter = this.tagBrowser.getComponent(this.tagBrowser.mapIndex(i));
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
                    encodeURIComponent(this.tagAt(index)), this.tagQuery(), this.includePublic); 
    }
});
