Ext.define('Bisque.ResourceTaggerOffline',
{
    extend : 'Bisque.ResourceTagger',
    
    constructor : function(config)
    {
        config = config || {};
        config.viewMode = 'Offline';
        
        this.callParent([config]);
    },
    
    setResource : function(resource)
    {
        this.resource = resource || new BQResource();  
        this.loadResourceTags(this.resource.tags);
    },
    
    saveTags : Ext.emptyFn,
    
    getTagDocument : function() {
        return this.resource && this.resource.tags ? this.resource.tags : [];
    },
});


