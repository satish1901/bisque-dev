Ext.define('BQ.Preferences',
{
    singleton : true,
    systemObject : undefined,
    systemLoaded : false,
    userLoaded : false,
    queue : [],
    preference :
    {
        systemTag : {},
        systemDict : {},
        userTag : {},
        userDict : {}
    },

    // load system preferences
    constructor : function()
    {
        // Load the system object
        BQFactory.request(
        {
            uri : bq.url('/data_service/system'),
            cb : Ext.bind(this.loadObject, this)
        });
    },

    loadObject : function(resource)
    {
        if(resource.children.length == 0)
            return;

        // Load the system object
        BQFactory.request(
        {
            uri : resource.children[0].uri + '?view=deep',
            cb : Ext.bind(this.objectLoaded, this, ['system'], true)
        });
    },

    objectLoaded : function(resource, type)
    {
        var obj = type+'Object', tag = type+'Tag', dict = type+'Dict';
        
        this[obj] = resource;
        this.preference[tag] = this[obj].find_tags('Preferences', false);
        if (this.preference[tag])
            this.preference[dict] = this.preference[tag].toHashTable(true);
    
        this[type+'Loaded'] = true;
        this.clearQueue();
        
    },
    
    clearQueue : function()
    {
        if (this.userLoaded && this.systemLoaded)
            while (this.queue.length!=0)
                this.get(this.queue.pop());
    },

    loadUser : function(user)
    {
        // Load the user object
        BQFactory.request(
        {
            uri : user.uri + '?view=deep',
            cb : Ext.bind(this.objectLoaded, this, ['user'], true)
        });
    },

    unloadUser : function()
    {
        Ext.apply(this.preferences, {
            userTag : {},
            userDict : {}
        });
        
        this.userLoaded = true;
        this.clearQueue();
    },

    get : function(caller)
    {
        if (this.userLoaded && this.systemLoaded)
        {
            if (Ext.Object.getSize(this.preference.userTag))
                var tag = this.preference.userTag.find_tags(caller.key, false);
            caller.callback(this.preference.userDict[caller.key] || this.preference.systemDict[caller.key], tag);
        }
        else
            this.queue.push(caller);
    },
    
    set : function(parentKey, pref, value)
    {
        if (this.userLoaded && this.systemLoaded)
        {
            var parent = this.preference.userTag.find_tags(parentKey, false);
            var tag = parent.find_tags(pref, false);
            if (tag)
            {
                tag.value=value;
                tag.save_();
            }
        }
        else
            clog('Not loaded yet!')
    }

})
