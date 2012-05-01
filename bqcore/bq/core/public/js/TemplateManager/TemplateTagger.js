Ext.define('Bisque.TemplateTagger',
{
    extend : 'Bisque.ResourceTagger',
    
    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(config, 
        {
            tree        :   {
                                btnAdd      :   false,
                                btnDelete   :   false,
                                btnImport   :   true,
                                btnExport   :   true,
                            },
        });

        this.tagRenderers = Ext.ClassManager.getNamesByExpression('BQ.TagRenderer.*'), this.tagTypes={};
        for (var i=0;i<this.tagRenderers.length;i++)
            if (Ext.ClassManager.get(this.tagRenderers[i]).componentName)
                this.tagTypes[Ext.ClassManager.get(this.tagRenderers[i]).componentName]=this.tagRenderers[i];
        
        this.callParent([config]);
    },
    
    setResource : function(resource)
    {
        this.resource = resource || new BQTemplate();
        this.loadResourceTags(this.resource.tags);
    },
    
    onEdit : function(me)
    {
        if (me.field == 'value' && (me.value!=me.record.get('value')))
        {
                var tag = me.record.raw;
                var template = tag.find_children('template');
                tag.remove_resource(template.uri);
                
                //me.record.commit();
                var newTemplate = Ext.ClassManager.get(this.tagTypes[me.record.get('value')]).getTemplate();
                tag.addchild(newTemplate);
        }
            
        if (me.record.raw)
            if (this.autoSave)
            {
                this.saveTags(me.record.raw, true);
                me.record.commit();
            }
    },
    
    saveTags : Ext.emptyFn,

    updateQueryTagValues : Ext.emptyFn,
    
    cancelEdit : function(grid, eOpts)
    {
        grid.record.parentNode.removeChild(grid.record);
    },
    
    // finish editing on a new record
    finishEdit : function(me)
    {
        this.callParent(arguments);
        
        var template = Ext.ClassManager.get(this.tagTypes[me.record.data.value]).getTemplate();
        me.record.raw.addchild(template);
    },

    populateComboStore : function()
    {
       this.store_names = [];

        this.store_values = Ext.create('Ext.data.ArrayStore', {
            fields  :   [
                            'value'
                        ],
        });
        
        var tagTypes = Ext.Object.getKeys(this.tagTypes);
        Ext.Array.forEach(tagTypes, function(item, index, orgArray){
            orgArray[index] = [item];
        });
        
        this.store_values.loadData(tagTypes);
        this.defaultTagValue = this.store_values.getAt(0).get('value'); 
    },
    
    getTreeColumns : function()
    {
        return [
        {
            xtype       :   'treecolumn',
            text        :   'Field name',
            flex        :   1,
            dataIndex   :   'name',
            field       :   {
                                tabIndex    :   0,  
                                allowBlank  :   false,
                                blankText   :   'Field name is required!',
                            }
        },
        {
            text        :   'Type',
            flex        :   1,
            sortable    :   true,
            dataIndex   :   'value',
            renderer    :   Bisque.ResourceTagger.BaseRenderer,
            field       :   {
                                xtype           :   'combobox',
                                displayField    :   'value',
                                tabIndex        :   1,                
                                store           :   this.store_values,
                                editable        :   false,
                                queryMode       :   'local',
                            },
        }];
    },
});