// Page view for an image
Ext.define('Bisque.Resource.File.Page',
{
    extend : 'Bisque.Resource.Page',
    
    onResourceRender : function()
    {
        this.callParent(arguments);
        
        // add custom download option to the toolbar
        var menu = this.toolbar.getComponent("btnDownload").menu;
        menu.add([
            {
                xtype   :   'menuseparator'
            },
            {
                xtype   :   'menuitem',
                text    :   'Original file',
                handler :   function() 
                            {
                                var pathToFile = bq.url('/blob_service/' + this.resource.resource_uniq);
                                window.open(pathToFile);
                            }
            }]);
    },
});

