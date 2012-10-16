// Page view for a File
Ext.define('Bisque.Resource.File.Page',
{
    extend : 'Bisque.Resource.Page',
    
    downloadOriginal : function() {
        window.open(this.resource.src);
    }
});

