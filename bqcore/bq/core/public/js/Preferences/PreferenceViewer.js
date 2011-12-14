Ext.define('BQ.Preferences.Dialog',
{
    extend : 'Ext.window.Window',
    
    constructor : function(config)
    {
        config = config || {};
        
        Ext.apply(this, 
        {
            title : 'Set preferences',
            modal : true,
            layout : 'fit',
            height : '70%',
            width : '70%',
            prefType : config.prefType || 'user'
        });
        
        if (config.prefType=='user')
            if (BQ.Preferences.user.status=='LOADED')
            {
                if (BQ.Preferences.user.exists==false)
                {
                    BQ.ui.notification('Guests cannot save preferences! Please login first...',  3000);
                    return;
                }
            }
            else
            {
                BQ.ui.notification('Initializing. Please wait...',  2000);
                return;
            }
                
        this.callParent(arguments);
        this.addTagger(this.prefType);
        this.show();
    },
    
    addTagger : function(prefType)
    {
        this.tagger = Ext.create('Bisque.PreferenceTagger',
        {
            viewMode : 'Offline',
            prefType : prefType
        });
    
        this.add(this.tagger);
    }
})
