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
                }, config);

                resource = copyTags.call(this, template, resource);

                if (config.noSave)
                    cb(resource, template);
                else
                    //resource.save_('/data_service/' + resource.resource_type + '?view=deep',
                    resource.save_('/data_service/resource?view=deep',
                      cb,
                      function(e) {
                          BQ.ui.error('An error occured while trying to create a resource from template: <br>' + e.message_short);
                    });
            }

            function copyTags(template, resource)
            {
                var parser = document.createElement('a');

                for(var i = 0; i < template.tags.length; i++)
                {
                    var tag = template.tags[i];
                    parser.href = tag.uri;
                    copyTags.call(this, tag, resource.addtag({name:tag.name, value:tag.template["defaultValue"] || '', type: parser.pathname}));
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

        window.onbeforeunload = Ext.bind(this.checkUnsavedChanges, this);
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

        this.grid = Ext.create('Ext.grid.property.Grid', {
            source: {},
            listeners: {
                'edit': this.onPropertyEdit,
                scope: this
            },
            customEditors: {
                'select': {
                    xtype: 'textareafield',
                    emptyText: 'Enter comma separated display values e.g. Alabama, Alaska'
                },
                'passedValues': {
                    xtype: 'textareafield',
                    emptyText: 'Enter comma separated passed values e.g. AL, AK (defaults to display values)'
                },
                'resourceType': {
                    xtype: 'combo',
                    /* // dima: BQApp.resourceTypes can't be used due to race condition
                    store: Ext.create('Ext.data.Store', {
                        fields  :   ['name', 'uri'],
                        data    :   BQApp.resourceTypes,
                    }), */
                    store: {
                        //fields  :   ['name', 'uri'],
                        //data    :   BQApp.resourceTypes,
                        fields : [
                            { name: 'name', mapping: '@name' },
                            { name: 'uri', mapping: '@uri' },
                        ],
                        proxy : {
                            limitParam : undefined,
                            pageParam: undefined,
                            startParam: undefined,
                            noCache: false,
                            type: 'ajax',
                            url : '/data_service/',
                            reader : {
                                type :  'xml',
                                root :  '/',
                                record: '/*:not(value or vertex or template)',
                            }
                        },
                        autoLoad : true,
                        autoSync : false,
                    },
                    queryMode   :   'local',
                    displayField:   'name',
                    editable    :   false
                },
                'help' : {
                    xtype    : 'hyperreference',
                    viewMode : 'widget',
                },
            },
        });

        this.centerPanel.add(this.tagger);
        this.eastPanel.add(this.grid);
    },

    checkUnsavedChanges : function()
    {
        if (this.resource.dirty)
        {
            this.tplToolbar.getComponent('tbTplSave').getEl().highlight('FF9500', {duration:250, iterations:6});
            return "You have unsaved changes which will be lost.";
        }
    },

    saveTemplate : function()
    {
        function success(resource)
        {
            BQ.ui.notification('Changes saved!', 2000);
            this.tagger.setResource(resource);
        }

        this.resource.dirty = false;
        this.resource.uri = this.resource.uri + '?view=deep';
        this.resource.save_(undefined, Ext.bind(success, this), Ext.pass(BQ.ui.error, ['Save failed!']));
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

Ext.define('BQ.form.field.HyperReference', {
    extend: 'Ext.form.field.Display',
    alias: 'widget.hyperreference',

    setValue : function(value) {
        this.callParent(arguments);
        if (value)
            htmlAction(BQ.Server.url(value), 'Help');
    },
});