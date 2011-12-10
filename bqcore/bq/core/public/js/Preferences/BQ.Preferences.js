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
                uri : bq.url('/data_service/system?wpublic=1&view=deep'),
                cb : Ext.bind(this.loadSystem, this, ['LOADED'], true),
            });
        }
        else if (status=='LOADED')
        {
            resource = resource.children[0];
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
    

    // bq_ui_application raises event loadUser 
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
                    clog('USER preferences tag not found! Initializing from system\n');
                    
                    alert('User preferences not found.. Aborting');
                    return
                    
                    var newTag = new BQTag();
                    newTag = Ext.apply(newTag,
                    {
                        name : 'Preferences',
                        permission : 'published'
                    });
                    resource.addtag(newTag);
                    resource.save_();

                    // Reload the user object
                    BQFactory.request(
                    {
                        uri : resource.uri + '?view=deep',
                        cb : Ext.bind(this.loadUser, this, ['LOADED'], true)
                    });
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
    
    getMerged : function()
    {
        var mergedPrefs = Ext.Object.merge(this.system.dictionary, this.user.dictionary);

        var prefs = new BQObject();
        prefs.name = 'Preferences';
        prefs.fromNestedDict(mergedPrefs);

        return prefs.tags;
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
