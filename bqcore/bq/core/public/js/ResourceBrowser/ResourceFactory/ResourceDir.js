
// Dir

Ext.define('Bisque.Resource.Dir.Compact', {
    extend : 'Bisque.Resource.Compact',
    //cls: 'folder', //dima: unfortunately overwritten somewhere later
    initComponent : function() {
        this.addCls('folder');
        this.callParent();
    },
});

Ext.define('Bisque.Resource.Dir.Card', {
    extend : 'Bisque.Resource.Dir.Compact',
});

Ext.define('Bisque.Resource.Dir.Full', {
    extend : 'Bisque.Resource.Dir.Compact',
});

Ext.define('Bisque.Resource.Dir.Grid', {
    extend : 'Bisque.Resource.Grid',
    //cls: 'folder', //dima: unfortunately overwritten somewhere later
    initComponent : function() {
        this.addCls('folder');
        this.callParent();
    },

    getFields : function(cb) {
        var fields = this.callParent();
        fields[0] = '<div class="gridDirIcon" />';
        return fields;
    },
});

// Store

Ext.define('Bisque.Resource.Store.Compact', {
    extend : 'Bisque.Resource.Compact',
    //cls: 'folder', //dima: unfortunately overwritten somewhere later
    initComponent : function() {
        this.addCls('store');
        this.callParent();
    },
});

Ext.define('Bisque.Resource.Store.Card', {
    extend : 'Bisque.Resource.Store.Compact',
});

Ext.define('Bisque.Resource.Store.Full', {
    extend : 'Bisque.Resource.Store.Compact',
});

Ext.define('Bisque.Resource.Store.Grid', {
    extend : 'Bisque.Resource.Grid',
    //cls: 'folder', //dima: unfortunately overwritten somewhere later
    initComponent : function() {
        this.addCls('store');
        this.callParent();
    },

    getFields : function(cb) {
        var fields = this.callParent();
        fields[0] = '<div class="gridStoreIcon" />';
        return fields;
    },
});