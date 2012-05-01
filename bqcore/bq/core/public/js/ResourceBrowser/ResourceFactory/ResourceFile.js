// Page view for an image
Ext.define('Bisque.Resource.File.Page',
{
    extend : 'Bisque.Resource.Page',
    
    onResourceRender : function()
    {
        this.callParent(arguments);
        
        this.toolbar.insert(0, {
            text : 'Download',
            iconCls : 'icon-save',
            handler : this.downloadFile,
            scope : this
        });
    },

    downloadFile : function()
    {
        var pathToFile = bq.url('/blob_service/' + this.resource.resource_uniq);
        window.open(pathToFile);
    }
});

