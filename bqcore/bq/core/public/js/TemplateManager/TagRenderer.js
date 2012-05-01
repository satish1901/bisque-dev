Ext.define('BQ.TagRenderer.Base', 
{
    
    alias               :   'BQ.TagRenderer.Base',
    inheritableStatics  :   {
                                template        :   {
                                                        'Default value' :   '',
                                                        'Fail message'  :   '',
                                                        'Allow blank'   :   false,
                                                        'Editable'      :   true,
                                                        'Help text'     :   '',
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
                                    tag.value = tag.value || '';
                                    
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
                                                        'Help text'             :   'Use "String" type for fields which will contain alphabets and numerals.',
                                                        'units'                 :   'microns',                   
                                                        'minLength'             :   10,  
                                                        'maxLength'             :   100,
                                                        'RegEx'                 :   ''
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
                                                        'Help text'             :   'Use "Number" type for fields which will only contain numerals.',
                                                        'minValue'              :   0,  
                                                        'maxValue'              :   100,
                                                    }                    
                            }   
});

Ext.define('BQ.TagRenderer.Boolean',
{
    extend              :   'BQ.TagRenderer.Base',
    alias               :   'BQ.TagRenderer.Boolean',
    inheritableStatics  :   {
                                componentName   :   'Boolean',
                            }
});


Ext.define('BQ.TagRenderer.ComboBox', 
{
    extend  :   'BQ.TagRenderer.Base',
    alias   :   'BQ.TagRenderer.ComboBox',
    inheritableStatics  :   {
                                componentName   :   'ComboBox',
                                template        :   {
                                                        'Help text'             :   'Use "ComboBox" type for fields which may contain multiple choices.',
                                                        'units'                 :   'microns',
                                                        'Select'                :   '',
                                                    }                    
                            }
});

Ext.define('BQ.TagRenderer.CheckBoxGroup',
{
    extend  :   'BQ.TagRenderer.Base',
    alias   :   'BQ.TagRenderer.CheckBoxGroup',
    inheritableStatics  :   {
                                componentName   :   'CheckBoxGroup',
                                template        :   {
                                                        'Select'                :   '',
                                                    }                    
                            }
});
