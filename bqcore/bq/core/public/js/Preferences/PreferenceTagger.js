Ext.define('Bisque.PreferenceTagger',
{
    extend : 'Bisque.ResourceTagger',
    
    constructor : function(config)
    {
        config = config || {};
        config.viewMode = 'PreferenceTagger';
        
        this.callParent([config]);
    },

    setResource : function(resource)
    {
        this.resource = resource || new BQResource();
        this.loadResourceTags(this.resource.tags);
        
        this.appendTags(BQ.Preferences.getMerged());
    },
    
})
