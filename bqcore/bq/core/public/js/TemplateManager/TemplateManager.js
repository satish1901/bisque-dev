Ext.define('BQ.TemplateManager', 
{
    statics : 
    {
        create : function(config) 
        {
            return Ext.create('BQ.TemplateManager.Creator', config);
        },
        
        initResource : function(resource, template)
        {
            // Assume the resource and the template are fully loaded)
            //template
            
            
            
        }
    }
});

Ext.define('BQ.TemplateManager.Visitor', 
{
    extend : BQVisitor,
    
    visit : function(node, args)
    {
        var a = 3;
    }
});

Ext.define('BQ.TemplateManager.Creator', 
{
    extend      :   'Ext.panel.Panel',
    border      :   false,
    layout      :   'border',
    heading     :   'Create template',
    bodyCls     :   'white',
        
    constructor : function(config)
    {
        Ext.apply(this,
        {
            centerPanel :   Ext.create('Ext.panel.Panel', {
                                region      :   'center',
                                border      :   false,
                                flex        :   7,
                                title       :   'Editing resource template - ' + config.resource.name || '',
                                layout      :   'fit',
                            }),
                            
            eastPanel   :   Ext.create('Ext.panel.Panel', {
                                region      :   'east',
                                frame       :   true,
                                flex        :   3,
                                title       :   'Properties',
                                layout      :   'fit',
                                collapsible :   true,
                                split       :   true
                            })            
        });
        
        Ext.apply(this,
        {
            items   :   [this.centerPanel, this.eastPanel],
        });
        
        this.callParent(arguments);
    },
    
    initComponent : function()
    {
        this.callParent(arguments);

        this.tagger = Ext.create('Bisque.TemplateTagger',
        {
            resource    :   this.resource,
            listeners   :   {
                                'itemclick' :   this.onFieldSelect,
                                scope       :   this
                            },
        });
        
        this.grid = Ext.create('Ext.grid.property.Grid',
        {
            source          :   {},
            listeners       :   {
                                    'edit'      :   this.onPropertyEdit,
                                    scope       :   this
                                },
            customEditors   :   {
                                    'Select'    :   {
                                                        xtype       :   'textareafield',
                                                        emptyText   :   'Enter comma separated values e.g. option1, option2'
                                                    }
                                }
        });
        
        this.centerPanel.add(this.tagger);
        this.eastPanel.add(this.grid);
    },
    
    saveTemplate : function()
    {
        BQ.TemplateManager.initResource('', this.resource);
        //this.tagger.resource.save_();
        BQ.ui.message('', 'Changes saved!');
    },
    
    onFieldSelect : function(tree, record)
    {
        this.currentField = record.raw;
        this.currentTemplate = this.currentField.find_children('template');
        this.eastPanel.setTitle('Properties - ' + this.currentField.name);
        this.grid.setSource(BQ.TagRenderer.Base.convertTemplate(this.currentTemplate));
    },
    
    onPropertyEdit : function(editor, record)
    {
        var tagName = record.record.get('name');
        var tag = this.currentTemplate.find_tags(tagName);
        
        if (tag)
            tag.value = record.value.toString();
    }
});