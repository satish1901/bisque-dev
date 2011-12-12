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
        this.tree.expandAll();
    },
    
    saveTags : function(tag, silent)
    {
        if(this.store.applyModifications())
        {
            var parents = this.getTagParents(tag);
            this.saveUserPrefs(tag, parents); 
            if (!silent) BQ.ui.message('Resource tagger - Save', 'Changes were saved successfully!');
        }
        else
            BQ.ui.message('Resource tagger - Save', 'No records modified!');
    },
    
    saveUserPrefs : function(changedTag, parents)
    {
        var root = BQ.Preferences.user.object;

        // Recursively find if the saved tag exist in user preferences or not
        // if not then add it otherwise continue with the search        
        for (var i=parents.length;i>=1;i--)
        {
            var current = parents[i-1];
            var tag = root.find_tags(current.name, false);
            
            root = (!tag)?root.addtag({name:current.name, value:current.value}):tag;
        }
        
        // if the user-changed tag exists already, modify the existing one
        if (root.uri)
        {
            root.name = changedTag.name;
            root.value = changedTag.value || '';
        }

        BQ.Preferences.user.tag.save_();
    },
    
    getTagParents : function(tag)
    {
        var parents = [];
        
        while (tag.parent)
        {
            parents.push(tag);
            tag = tag.parent;
        }
        
        parents.push(tag);
        
        return parents
    }
    
})
