// Page view for an image
Ext.define('Bisque.Resource.File.Page',
{
    extend : 'Bisque.Resource.Page',
    
    updateContainer : function() 
    {
        this.callParent(arguments);
        
        var tagger = this.getComponent('resourceTagger');
        var toolbar = tagger.tree.getDockedItems('toolbar')[0];
        
        toolbar.add({
            xtype : 'buttongroup',
            items : [
            {
                text : 'Download',
                scale : 'small',
                iconCls : 'icon-save',
                handler : this.downloadFile,
                scope : this
            }]
        });
    },
    
    downloadFile : function()
    {
        var pathToFile = bq.url('/blob_service/' + this.resource.resource_uniq);
        window.open(pathToFile);
    }
});

