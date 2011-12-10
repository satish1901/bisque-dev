
Ext.define('Bisque.Module.AbstractModule',
{
    //extend: 'Ext.container.Container',
    extend: BQWebApp,
    
    constructor : function()
    {
        Ext.apply(this, 
        {
            style: 'background:#7A7',
            module_url : '/module_service/CellProfiler',
            label_run : "Analyze Images"
        })
        
        this.callParent(arguments);
    },
})
