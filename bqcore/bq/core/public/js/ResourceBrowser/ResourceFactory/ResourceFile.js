// Page view for an image
Ext.define('Bisque.Resource.File.Page',
{
    extend : 'Bisque.Resource.Page',
    
    downloadOriginal : function()
    {
        var pathToFile = bq.url('/blob_service/' + this.resource.resource_uniq);
        window.open(pathToFile);
    }
});

