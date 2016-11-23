
Ext.define('BQ.setting.Dialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.bqsettingsdialog',
    border: 0,
    title: 'Settings',
    layout: 'fit',
    modal : true,
    width : '85%',
    height : '85%',
    buttonAlign: 'center',
    bodyCls: 'bq_settings_dialog',

    constructor : function(config) {
        config = config || {};
        Ext.apply(this, {
            items  : [{
                xtype: 'bq_settings_panel',
                itemId: 'bq_settings_panel',
                border: 0,
                activeTab: config.activeTab,
            }]
        }, config);

        this.callParent(arguments);
        this.show();
    },
});

Ext.define('BQ.setting.Panel', {
    extend : 'Ext.tab.Panel',
    alias: 'widget.bq_settings_panel',
    //layout : 'fit',
    //height : '85%',
    //width : '85%',
    //modal : true,
    border: false,
    plain: true,
    componentCls: 'bq_settings_panel',

    tools_none:  [], //a none user has no settings
    tools_user:  ['settings_module_manager', 'settings_module_developer', 'setting_preference'],
    tools_admin: ['settings_user_manager', 'settings_cache_manager', 'settings_system', 'settings_log_viewer'],

    defaults: {
        border: false,
    },

    initComponent: function() {
        var me = this;
        this.items = [{
            title: 'User Manager',
            layout: 'fit',
            items: [Ext.create('BQ.admin.UserManager')],
            itemId: 'settings_user_manager',
            hidden: true,
        },{
            title: 'Cache Manager',
            padding: '8px',
            border: false,
            itemId: 'settings_cache_manager',
            hidden: true,
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
            border: false,
            itemId: 'settings_module_manager',
            hidden: true,
            items: Ext.create('BQ.module.ModuleManagerMain'),
        },{
            title: 'Module Developer',
            layout: 'fit',
            border: false,
            itemId: 'settings_module_developer',
            hidden: true,
            items: Ext.create('BQ.module.ModuleDeveloperPage'),
        }, {
            title: 'Preferences',
            layout: 'fit',
            border: false,
            itemId: 'setting_preference',
            hidden: true,
            items: Ext.create('BQ.preference.PreferencePage',{
                activeTab: 1,
            }),
        }, {
            title: 'System',
            layout: 'fit',
            itemId: 'settings_system',
            hidden: true,
            disabled: true,
            //items: Ext.create('BQ.admin.SystemManager'),
        }, {
            xtype: 'bq_loggers_manager',
            title: 'Loggers',
            itemId: 'loggers_manager',
        }, {
            title: 'Log Viewer',
            layout: 'fit',
            itemId: 'settings_log_viewer',
            hidden: true,
            disabled: true,
        }, {
            xtype: 'bq_notifications_manager',
            title: 'Notifications',
            itemId: 'notifications_manager',
        }];

        this.on('beforerender', this.setVisibility);
        this.callParent();
    },

    setVisibility : function() {
        // hide no user menus
        for (var i=0; (p=this.tools_none[i]); i++)
            this.setSettingTabVisibility(p, false);
        if (BQApp.user) {
            // show user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.setSettingTabVisibility(p, true);

            // show admin menus
            if (BQApp.user.is_admin() ) //needs to change
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.setSettingTabVisibility(p, true);
        }
    },

    setSettingTabVisibility: function(id, v) {
        var m = this.queryById(id);
        if (m) m.tab.setVisible(v);

    },
});
