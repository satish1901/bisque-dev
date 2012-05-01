// Page view for a template
Ext.define('Bisque.Resource.Template1.Page',
{
    extend : 'Bisque.Resource.Page',
    
    onResourceRender : function()
    {
        this.setLoading(false);
        
        var tplMan = new BQ.TemplateManager.create({resource:this.resource});
        this.add(tplMan);
        
        this.toolbar.insert(0, 
        [{
            xtype   :   'tbspacer',
            width   :   8
        },
        {
            text    :   'Save',
            iconCls :   'icon-save',
            handler :   tplMan.saveTemplate,
            scope   :   tplMan
        },
            '-'
        ]);
    },
});
