Ext.define('BQ.TemplateManager', 
{
    statics : 
    {
        create : function(config) 
        {
            return Ext.create('BQ.TemplateManager.Creator', config);
        },
        
        // Create a blank resource from a template
        createResource : function(config, cb, template)
        {
            if (!(template instanceof BQTemplate))
            {
                BQFactory.request({
                    uri     :   template,
                    cb      :   Ext.pass(BQ.TemplateManager.createResource, [config, cb]),
                    cache   :   false,
                });
            }
            else
            {
                // Parse template URL #http://www.joezimjs.com/javascript/the-lazy-mans-url-parsing/
                var parser = document.createElement('a');
                parser.href = template.uri;
                
                // Assume the template is fully loaded
                var resource = new BQResource();
                
                Ext.apply(resource, {
                    resource_type   :   template.name,
                    type            :   parser.pathname,
                }, config)
                
                resource = copyTags.call(this, template, resource);
                resource.save_('/data_service/' + resource.resource_type + '?view=deep', cb, function(msg) {BQ.ui.error('An error occured while trying to create a resource from template: ' + msg)});
            }

            function copyTags(template, resource)
            {
                for(var i = 0; i < template.tags.length; i++)
                {
                    var tag = template.tags[i]; 
                    copyTags.call(this, tag, resource.addtag({name:tag.name, value:tag.template["Default value"] || '', type: tag.value}));
                }
                return resource;
            }
        },
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
            resource        :   this.resource,
            listeners       :   {
                                    'itemclick' :   this.onFieldSelect,
                                    scope       :   this
                                },
        });
        
        this.grid = Ext.create('Ext.grid.property.Grid',
        {
            source          :   {},
            listeners       :   {
                                    'edit'          :   this.onPropertyEdit,
                                    scope           :   this
                                },
            customEditors   :   {
                                    'Values'        :   {
                                                            xtype       :   'textareafield',
                                                            emptyText   :   'Enter comma separated values e.g. option1, option2'
                                                        },
                                    'Resource type' :   {
                                                            xtype       :   'combo',
                                                            store       :   Ext.create('Ext.data.Store', {
                                                                                fields  :   ['name', 'uri'],
                                                                                data    :   BQApp.resourceTypes,   
                                                                            }),
                                                            queryMode   :   'local',       
                                                            displayField:   'name',
                                                            editable    :   false
                                                        }
                                }
        });
        
        this.centerPanel.add(this.tagger);
        this.eastPanel.add(this.grid);
    },
    
    saveTemplate : function()
    {
        this.resource.save_(undefined, Ext.pass(BQ.ui.notification, ['Changes saved!', 2000]), Ext.pass(BQ.ui.error, ['Save failed!']));
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