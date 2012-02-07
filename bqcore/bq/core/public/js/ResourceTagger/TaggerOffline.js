Ext.define('Bisque.ResourceTaggerOffline',
{
    extend : 'Bisque.ResourceTagger',
    
    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(config, 
        {
            viewMode    :   'Offline',
            tree        :   {
                                btnAdd : false,
                                btnDelete : false,
                                btnImport : false
                            }
        });
        
        this.callParent([config]);
    },
    
    setResource : function(resource)
    {
        this.resource = resource || new BQResource();
        this.loadResourceTags(this.resource.tags);
    },
    
    saveTags : function() {
        this.store.applyModifications();
    },
    
    getTagDocument : function() {
        return (this.resource && this.resource.tags) ? this.resource.tags : [];
    },
});


