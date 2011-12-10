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
            else if (BQ.Preferences.user.exists==true)
            {
                BQ.ui.notification('User preferences not found!',  3000);
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
            /*listeners : 
            {
                'destroy' : function() 
                {
                    this.browser.msgBus.fireEvent('Browser_ReloadData', "ReloadPrefs");
                },
                scope : this    
            }*/
        });
    
        this.add(this.tagger);
    }
})





//--------------------------------------------------------------------------------------
// BQ.Preferences.Dialog
// instantiates preferences in a modal window
//-------------------------------------------------------------------------------------- 

