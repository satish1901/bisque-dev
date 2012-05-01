Ext.define('Bisque.Resource.User.Grid',
{
    extend : 'Bisque.Resource.Grid',
    
    getFields : function(displayName)
    {
        var tag = this.resource.find_tags('display_name', false);
        this.displayName = (tag) ? tag.value : ''; 
        this.resource.display_name = this.displayName;
        var fields = this.callParent();
        fields[1] = this.displayName;
            
        return fields;
    }
})
