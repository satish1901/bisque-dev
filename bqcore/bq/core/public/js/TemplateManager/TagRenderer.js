Ext.define('BQ.TagRenderer.Base', 
{
    
    alias               :   'BQ.TagRenderer.Base',
    inheritableStatics  :   {
                                baseClass       :   'BQ.TagRenderer',
                                template        :   {
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
                                    var className = BQ.TagRenderer.Base.baseClass + '.' + config.tplType;
            
                                    if (Ext.ClassManager.get(className))
                                        return Ext.create(className).getRenderer(config);
                                    else
                                    {
                                        Ext.log({
                                            msg     :   Ext.String.format('TagRenderer: Unknown class: {0}, type: {1}. Initializing with default tag renderer.', className, config.tplType),
                                            level   :   'warn',
                                            stack   :   true
                                        });
                                        return Ext.create(BQ.TagRenderer.Base.baseClass + '.' +'String').getRenderer(config);
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
                                            value = Boolean(tag.value);
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
                                                        'minLength'             :   1,  
                                                        'maxLength'             :   200,
                                                        'RegEx'                 :   ''
                                                    }                    
                        },
                        
    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'textfield',

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
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype           :   'checkbox',
                                            boxLabel        :   ' (checked = true, unchecked = False)',
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
    extend  :   'BQ.TagRenderer.Base',
    alias   :   'BQ.TagRenderer.ComboBox',
    inheritableStatics  :   {
                                componentName   :   'ComboBox',
                                template        :   {
                                                        'Values'    :   '',
                                                    }                    
                        },
                        
    getRenderer         :   function(config)
                            {
                                var values = config.tplInfo.Values || '';
                                return  {
                                            xtype       :   'combobox',
                                            store       :   values.split(','),
                                            editable    :   false
                                        }
                            }
});

Ext.define('BQ.TagRenderer.Hyperlink',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Hyperlink',
    inheritableStatics  :   {
                                componentName   :   'Hyperlink',
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
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'BisqueResourcePicker',
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
                            },

    getRenderer         :   function(config)
                            {
                                return  {
                                            xtype       :   'textfield',
                                            vtype       :   'email'
                                        }
                            }
});


