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
        
        //  Check if the user is logged in
        if (this.browser.preferencesTag==undefined)
        {
            BQ.ui.notification('Guests cannot save preferences! Please login first...',  3000);
            return;
        }
        
        this.callParent(arguments);
        
        this.addTagger();
        this.show();
    },
    
    addTagger : function()
    {
        var tagger = Ext.create('Bisque.ResourceTagger',
        {
            resource : this.browser.preferencesTag.uri,
        });
        
        this.add(tagger);
    }
    
    
})