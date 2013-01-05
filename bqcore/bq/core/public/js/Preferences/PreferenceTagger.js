Ext.define('Bisque.PreferenceTagger',
{
    extend : 'Bisque.ResourceTagger',
    
    //autoSave : true,
    
    constructor : function(config)
    {
        config      =   config || {};
        
        config.viewMode =   'PreferenceTagger';
        config.autoSave =   true,
        config.tree     =   config.tree || {
                                btnAdd : false,
                                btnDelete : false,
                            },
        
        this.callParent([config]);
    },

    setResource : function(resource)
    {
        if (this.prefType=='user')
        {
            this.resource = resource || new BQResource();
            this.loadResourceTags(this.resource.tags);
            
            this.appendTags(BQ.Preferences.getMerged());
        }
        else
        {
            this.resource = BQ.Preferences.system.tag;
            this.loadResourceTags(this.resource.tags);
        }

        this.tree.expandAll();
    },
    
    saveTags : function(tag, silent, child)
    {
        if (tag)
            if(this.store.applyModifications())
            {
                if (this.prefType=='user')
                {
                    if (child) tag = child;
                    var parents = this.getTagParents(tag);
                    this.savePrefs(tag, parents); 
                    if (!silent) BQ.ui.message('Save', 'Changes were saved successfully!');
                }
                else
                {
                    this.resource.doc = this.resource;
                    this.resource.save_();
                }
            }
            else
                BQ.ui.message('Save', 'No records modified!');
    },
    
    savePrefs : function(changedTag, parents)
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
    
    deleteTags : function()
    {
        var selectedItems = this.tree.getSelectionModel().getSelection(), parent;
        var root = BQ.Preferences.user.tag;
        
        BQ.Preferences.user.object.tags[0].delete_();

        var cb = Ext.bind(function(){
            this.tree.setLoading(false);
        }, this);
        
        if(selectedItems.length)
        {
            this.tree.setLoading(true);
            
            for(var i = 0; i < selectedItems.length; i++)
            {
                var tag = root.findTags({
                    attr    :   'name',
                    value   :   selectedItems[i].get('name'),
                    deep    :   true
                });
                
                if (!Ext.isEmpty(tag))
                    for (var j=0; j<tag.length; j++)
                        if (tag[j].value == selectedItems[i].get('value'))
                        {
                            parent = (selectedItems[i].parentNode.isRoot()) ? root : tag[j].parent;
                            parent.deleteTag(tag[j], cb, cb);

                            if(selectedItems[i].parentNode.childNodes.length <= 1)
                                selectedItems[i].parentNode.data.iconCls = 'icon-tag';
            
                            selectedItems[i].parentNode.removeChild(selectedItems[i], true);

                            break;
                        }
            }

            this.tree.setLoading(false);

            BQ.ui.message('Resource tagger - Delete', selectedItems.length + ' record(s) deleted!');
            this.tree.getSelectionModel().deselectAll();
        }
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
