Ext.define('BQ.TagRenderer.Base', 
{
    
    alias               :   'BQ.TagRenderer.Base',
    inheritableStatics  :   {
                                baseClass       :   'BQ.TagRenderer',
                                template        :   {
                                                        'Type'          :   'Base',
                                                        'Default value' :   '',
                                                        'Allow blank'   :   false,
                                                        'Editable'      :   true,
                                                    },

                                /// getRenderer     :   Returns a tag renderer for a given tag type and template information
                                /// inputs -
                                /// config.tplType  :   Type of template (String, Number etc.)
                                /// config.tplInfo  :   Template information    (minValue, maxValue etc.)
                                getRenderer     :   function(config)
                                {
                                    var tplType = config.tplInfo.Type;
                                    var className = BQ.TagRenderer.Base.baseClass + '.' + tplType;
            
                                    if (Ext.ClassManager.get(className))
                                        return Ext.create(className).getRenderer(config);
                                    else
                                    {
                                        Ext.log({
                                            msg     :   Ext.String.format('TagRenderer: Unknown class: {0}, type: {1}. Initializing with default tag renderer.', className, tplType),
                                            level   :   'warn',
                                            stack   :   true
                                        });
                                        return Ext.create(BQ.TagRenderer.Base.baseClass + '.' + 'String').getRenderer(config);
                                    }
                                },
                                
                                getTemplate     :   function()
                                {
                                    var componentTemplate = Ext.clone(this.template || {});
                                    var baseTemplate = Ext.clone(Ext.ClassManager.get('BQ.TagRenderer.Base').template);
                                    return this.convertTemplate(Ext.Object.merge(baseTemplate, componentTemplate));
                                },
                                
                                convertTemplate :   function(template)
                                {
                                    if (template instanceof BQTemplate)
                                    {
                                        var templateObj = {}, template = template.tags;
                                        for (var i=0;i<template.length;i++)
                                            templateObj[template[i].name] = this.parseVariable(template[i]);  
                                        return templateObj;
                                    }
                                    else if (template instanceof Object)
                                    {
                                        var templateRes = new BQTemplate(), newTag;
                                        for (var i in template)
                                            templateRes.addtag({
                                                name    :   i,
                                                value   :   template[i].toString(),
                                                type    :   typeof template[i]
                                            });
                                        templateRes.resource_type = 'template';
                                        return templateRes;
                                    }
                                },
                                
                                parseVariable : function(tag)
                                {
                                    var value;
                                    tag.value = Ext.isEmpty(tag.value)?'':tag.value;
                                    
                                    switch (tag.type)
                                    {
                                        case 'number':
                                            value = parseFloat(tag.value);
                                            break;
                                        case 'boolean':
                                            value = Ext.isBoolean(tag.value) ? tag.value : (tag.value.toLowerCase() === "true");   
                                            break;
                                        default:
                                            value = tag.value;
                                    }
                                    
                                    return value;
                                },
                            },
});

Ext.define('BQ.TagRenderer.String',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.String',
    inheritableStatics  :   {
                                componentName   :   'String',
                                template        :   {
                                                        'Type'                  :   'String',
                                                        'minLength'             :   1,  
                                                        'maxLength'             :   200,
                                                        'RegEx'                 :   ''
                                                    }                    
                        },
                        
    getRenderer         :   function(config)
                            {
                                var valueStore = config.valueStore;
                                
                                if (!valueStore)
                                {
                                    if (!Ext.ModelManager.getModel('TagValues'))
                                    {
                                        Ext.define('TagValues',
                                        {
                                            extend  :   'Ext.data.Model',
                                            fields  :   [ {name: 'value', mapping: '@value' } ],
                                        });
                                    }
            
                                    var valueStore = Ext.create('Ext.data.Store',
                                    {
                                        model       :   'TagValues', 
                                        autoLoad    :   true,
                                        autoSync    :   false,

                                        proxy       :   {
                                                            noCache     :   false,
                                                            type        :   'ajax',
                                                            limitParam  :   undefined,
                                                            pageParam   :   undefined,
                                                            startParam  :   undefined,
                                                            url         :   '/xml/dummy_tag_values.xml',
                                                            reader      :   {
                                                                                type    :   'xml',
                                                                                root    :   'resource',
                                                                                record  :   'tag', 
                                                                            },
                                                        },
                                    });
                                }
                                    
                                return  {
                                            xtype       :   'combobox',
                                            store       :   valueStore,
                                            
                                            displayField:   'value',
                                            valueField  :   'value',
                                            queryMode   :   'local',
                                            typeAhead   :   true,

                                            minLength   :   config.tplInfo.minLength || BQ.TagRenderer.String.template.minLength,
                                            maxLength   :   config.tplInfo.maxLength || BQ.TagRenderer.String.template.maxLength,
                                            regex       :   RegExp(config.tplInfo.RegEx || ''),
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Number', 
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Number',
    inheritableStatics  :   {
                                componentName   :   'Number',
                                template        :   {
                                                        'Type'                  :   'Number',
                                                        'minValue'              :   0,  
                                                        'maxValue'              :   100,
                                                        'allowDecimals'         :   true,
                                                        'decimalPrecision'      :   2,
                                                    }                    
                            },
                               
    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype               :   'numberfield',
                                            
                                            minValue            :   config.tplInfo.minValue || BQ.TagRenderer.Number.template.minValue,
                                            maxValue            :   config.tplInfo.maxValue || BQ.TagRenderer.Number.template.maxValue,
                                            allowDecimals       :   config.tplInfo.allowDecimals || BQ.TagRenderer.Number.template.allowDecimals,
                                            decimalPrecision    :   config.tplInfo.decimalPrecision || BQ.TagRenderer.Number.template.decimalPrecision,
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Boolean',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Boolean',
    inheritableStatics  :   {
                                componentName   :   'Boolean',
                                template        :   {
                                                        'Type'  :   'Boolean'
                                                    }
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype           :   'checkbox',
                                            boxLabel        :   ' (checked = True, unchecked = False)',
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Date',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Date',
    inheritableStatics  :   {
                                componentName   :   'Date',
                                template        :   {
                                                        'Type'      :   'Date',
                                                        'format'    :   'm/d/Y',
                                                    }                    
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'datefield',
                                            format      :   config.tplInfo.format || BQ.TagRenderer.Date.template.format,
                                            getValue    :   function()
                                            {
                                                return this.getRawValue();
                                            }
                                        }
                            }
});

Ext.define('BQ.TagRenderer.ComboBox',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.ComboBox',
    inheritableStatics  :   {
                                componentName   :   'ComboBox',
                                template        :   {
                                                        'Type'              :   'ComboBox',
                                                        'Display values'    :   '',
                                                        'Passed values'     :   ''
                                                    }                    
                        },
                        
    getRenderer         :   function(config)
                            {
                                var values = config.tplInfo['Display values'] || '', passedValues = '';
                                values = values.split(',');
                                
                                if (config.tplInfo['Passed values'])
                                    passedValues = config.tplInfo['Passed values'].split(',');
                                else
                                    passedValues = values;

                                // prepare data to be compatible with store
                                for (var i=0, data=[]; i<values.length; i++)
                                    data.push({'name':values[i], 'value':passedValues[i]});  
                                
                                var store = Ext.create('Ext.data.Store',
                                {
                                    fields  :   ['name', 'value'],
                                    data    :   data
                                });
                                
                                return  {
                                            xtype           :   'combobox',
                                            store           :   store,
                                            displayField    :   'name',
                                            valueField      :   'value',
                                            editable        :   false,
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Hyperlink',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Hyperlink',
    inheritableStatics  :   {
                                componentName   :   'Hyperlink',
                                template        :   {
                                                        'Type'  :   'Hyperlink'
                                                    }
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'textfield',
                                            vtype       :   'url'
                                        }
                            }
});

Ext.define('BQ.TagRenderer.BisqueResource',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.BisqueResource',
    inheritableStatics  :   {
                                componentName   :   'BisqueResource',
                                template        :   {
                                                        'Type'          :   'BisqueResource',
                                                        'Resource type' :   'image',
                                                    }                    
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'BisqueResourcePicker',
                                            dataset     :   config.tplInfo['Resource type'] || BQ.TagRenderer.BisqueResource.template['Resource type'],
                                            editable    :   false,
                                        }
                            }
});

Ext.define('Bisque.Resource.Picker',
{
    extend      :   'Ext.form.field.Picker',
    xtype       :   'BisqueResourcePicker',
    triggerCls  :   Ext.baseCSSPrefix + 'form-date-trigger',
    
    createPicker: function()
    {
        var rb = new Bisque.ResourceBrowser.Dialog(
        {
            height      :   '85%',
            width       :   '85%',
            viewMode    :   'ViewerLayouts',
            selType     :   'SINGLE',
            dataset     :   '/data_service/' + this.dataset,
            listeners   :
            {
                'Select' : function(me, resource)
                {
                    this.setValue(resource.uri);
                },

                scope : this
            },
        });
    },
});


Ext.define('BQ.TagRenderer.Email',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Email',
    inheritableStatics  :   {
                                componentName   :   'Email',
                                template        :   {
                                                        'Type'  :   'Email'
                                                    }
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'textfield',
                                            vtype       :   'email'
                                        }
                            }
});


