Ext.define('BQ.Preferences.Object', {
    tag : {},
    dictionary : {},
    status : undefined,
    exists : undefined
});

Ext.define('BQ.Preferences',
{
    singleton : true,
    queue : [],
    
    // load system preferences
    constructor : function()
    {
        this.system = Ext.create('BQ.Preferences.Object');
        this.user = Ext.create('BQ.Preferences.Object');
    
        this.loadSystem(undefined, 'INIT');
    },
    
    loadSystem : function(resource, status)
    {
        this.system.status=status;
        
        if (status=='INIT')
        {
            BQFactory.request(
            {
                uri : bq.url('/data_service/system?wpublic=1'),
                cb : Ext.bind(this.loadSystem, this, ['LOADING'], true),
            });
        }
        else if (status=='LOADING')
        {
            if (resource.children.length!=0)
                BQFactory.request(
                {
                    uri : resource.children[0].uri + '?view=deep',
                    cb : Ext.bind(this.loadSystem, this, ['LOADED'], true),
                });
            else
            {
                clog('SYSTEM object not found!\n');
                this.system.status='LOADED';
                this.system.exists=false;
            }
        }
        else if (status=='LOADED')
        {
            var tag = resource.find_tags('Preferences', false);
            
            if (tag!=null)
            {
                this.system.tag=tag;
                this.system.dictionary=tag.toNestedDict(true);
            }
            else
            {
                clog('SYSTEM preferences tag not found!\n');
                this.system.exists=false;
            }
        }
        
        this.clearQueue();
    },
    

    loadUser : function(resource, status)
    {
        this.user.status=status;

        // User is signed-in
        if (status=='INIT')
        {
            // Load the user object
            BQFactory.request(
            {
                uri : resource.uri + '?view=deep',
                cb : Ext.bind(this.loadUser, this, ['LOADED'], true)
            });
        }
        else if (status=='LOADED')
        {
            if (resource!=null)
            {
                var tag = resource.find_tags('Preferences', false);
                    
                if (tag!=null)
                {
                    this.user.tag=tag;
                    this.user.dictionary=tag.toNestedDict(true);
                }
                else
                {
                    clog('USER preferences tag not found!\n');
                    this.user.exists=true;
                }
            }
            else
            {
                clog('USER - no user found!\n');
                this.user.exists=false;
            }
        }

        this.clearQueue();
    },
    
    clearQueue : function()
    {
        if (this.system.status=='LOADED' && this.user.status=='LOADED')
            while (this.queue.length!=0)
                this.get(this.queue.pop());
    },

    /*
     * Caller object: 
     * 
     * Caller.key = Component's key e.g. "ResourceBrowser"
     * Caller.callback = Component's callback function when the preferences are loaded
     */
    get : function(caller)
    {
        if (this.system.status=='LOADED' && this.user.status=='LOADED')
            if (caller.type=='user')
                caller.callback(Ext.Object.merge(this.system.dictionary[caller.key] || {}, this.user.dictionary[caller.key] || {}));
            else    // return 'system' preferences by default 
                caller.callback(this.system.dictionary[caller.key] || {});
        else
            this.queue.push(caller);
    },
    
    reloadUser : function(user)
    {
        this.user = Ext.create('BQ.Preferences.Object');
        this.loadUser(user, 'INIT');
    },
    
    InitFromSystem : function(key)
    {
        var tag = this.stripOwnership([this.preference.systemTag.find_tags(key, false)]);
    },
    
    stripOwnership : function(tagDocument)
    {
        var treeVisitor = Ext.create('Bisque.ResourceTagger.OwnershipStripper');
        treeVisitor.visit_array(tagDocument);
        return tagDocument;
    }
})
