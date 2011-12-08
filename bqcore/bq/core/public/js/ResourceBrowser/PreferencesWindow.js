Ext.define('Bisque.ResourceBrowser.PreferencesWindow',
{
    extend : 'Ext.window.Window',
    
    constructor : function(config)
    {
        Ext.apply(this, 
        {
            title : 'Set preferences',
            layout : 'fit',
            browser : config.browser || {}
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
        //var tag = BQ.Preferences.user.tag.find_tags(this.browser.preferenceKey, true);

        //if (tag.uri)
        {
            var tagger = Ext.create('Bisque.ResourceTagger',
            {
                resource : BQ.Preferences.user.tag,
                listeners : 
                {
                    'destroy' : function() 
                    {
                        this.browser.msgBus.fireEvent('Browser_ReloadData', "ReloadPrefs");
                    },
                    scope : this    
                }
            });
        
            this.add(tagger);
        }
    }
    
    
})