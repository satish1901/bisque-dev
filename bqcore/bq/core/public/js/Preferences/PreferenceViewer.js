Ext.define('BQ.Preferences.Dialog',
{
    extend : 'Ext.window.Window',
    
    constructor : function(config)
    {
        Ext.apply(this, 
        {
            title : 'Set preferences',
            modal : true,
            layout : 'fit',
            height : '70%',
            width : '70%',
        });
        
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
        this.addTagger();
        this.show();
    },
    
    addTagger : function()
    {
        this.tagger = Ext.create('Bisque.PreferenceTagger',
        {
            viewMode : 'Offline'
        });
    
        this.add(this.tagger);
    }
})
