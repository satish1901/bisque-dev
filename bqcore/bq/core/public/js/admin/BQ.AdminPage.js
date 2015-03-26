Ext.define('BQ.admin.MainPage', {
    extend : 'Ext.window.Window',
    requires: [
        'BQ.admin.UserManager', 
        'BQ.admin.ModuleManager',
    ],
    //xtype: 'BQAdminViewer',
    title : 'Admin Page',
    layout : 'fit',
    height : '85%',
    width : '85%',
    modal : true,
    border: false,
    
    initComponent: function(config) {
        var config = config || {};
        var me = this;
        
        var items = [{
            region: 'center',
            xtype: 'tabpanel',
            items: [{
                title: 'User Manager',
                layout: 'fit',
                items: [Ext.create('BQ.admin.UserManager')],
            },{
                title: 'Cache Manager',
                padding: '8px',
                items: [{
                    xtype: 'container',
                    padding: '8px',
                    html : '<h2>Cache Manager</h2><p>Select to clear all the cache for all the users.</p>',
                },{
                    text: 'Clear Cache',
                    xtype: 'button',
                    padding: '8px',
                    style: {left:'20px'},
                    handler: function() {this.clearCache();},
                    clearCache: function() {
                         Ext.Ajax.request({
                            url: '/admin/cache',
                            method: 'DELETE',
                            headers: { 'Content-Type': 'text/xml' },
                            success: function(response) {
                                var xml = response.responseXML;
                                BQ.ui.notification('Cache cleared!');
                            },
                            failure: function(response) {
                                BQ.ui.error('Cache failed to be cleared!')
                            },
                            scope: this,
                        });
                    },
                }],
            },{
                title: 'Module Manager',
                layout: 'fit',
                //disabled: true,
                items: Ext.create('BQ.admin.ModuleManagerMain'),
            }, {
                title: 'Log Viewer',
                disabled: true,
            }, {
                title: 'System Configuration',
                disabled: true,
            }]
        }];
        
        Ext.apply(me, {
            items: items,
        });
        this.callParent([config]);
    }
});




