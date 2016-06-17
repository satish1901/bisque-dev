/*******************************************************************************

  BQ.share.Panel  - sharing component to add shared users to the resource
  BQ.share.Dialog - window wrapper for the sharing panel

  Author: Dima Fedorov <dima@dimin.net>

  Parameters:
      resource - the BQResource object for the resource of interest

------------------------------------------------------------------------------

  Version: 1

  History:
    2014-05-02 13:57:30 - first creation

*******************************************************************************/

//--------------------------------------------------------------------------------------
// BQ.share.Dialog
// Events:
//    changedShare
//--------------------------------------------------------------------------------------

Ext.define('BQ.share.Dialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.bqsharedialog',
    border: 0,
    layout: 'fit',
    modal : true,
    width : '70%',
    height : '85%',
    //minHeight: 350,
    //maxWidth: 900,
    buttonAlign: 'center',
    autoScroll: true,
    bodyCls: 'bq-share-dialog',

    constructor : function(config) {
        config = config || {};
        Ext.apply(this, {
            title  : 'Sharing - ' + (config.resource ? config.resource.name : ''),
            buttons: [{
                text: 'Done',
                scale: 'large',
                scope: this,
                handler: this.close
            }],
            items  : [{
                xtype: 'bqsharepanel',
                itemId: 'sharepanel',
                border: 0,
                resource: config.resource
            }]
        }, config);

        this.callParent(arguments);
        this.show();
    },

    afterRender : function() {
        this.callParent();

        this.on('beforeclose', this.onBeforeClose, this);

        // this is used for capturing window closing and promting the user if upload is in progress
        Ext.EventManager.addListener(window, 'beforeunload', this.onPageClose, this, {
            normalized:false //we need this for firefox
        });
    },

    onBeforeClose: function(el) {
        if (this.queryById('sharepanel').isChanged())
            this.fireEvent( 'changedShare' );
        Ext.EventManager.removeListener(window, 'beforeunload', this.onPageClose, this);
        return true; // enable closing
    },

    onPageClose : function(e) {
        if (this.queryById('sharepanel').isChanged()) {
            var message = 'Some shares have not yet been saved, by closing the page you will discard all changes!';
            if (e) e.returnValue = message;
            if (window.event) window.event.returnValue = message;
            return message;
        }
    },


});

//--------------------------------------------------------------------------------------
// BQ.share.Panel
// Events:
//    changePermission
//--------------------------------------------------------------------------------------

function getName(v, record) {
    return BQ.util.xpath_string(record.raw, 'tag[@name="display_name"]/@value');
}

function getFull(v, record) {
    var username = BQ.util.xpath_string(record.raw, '@name');
    var email = BQ.util.xpath_string(record.raw, '@value');
    var name = BQ.util.xpath_string(record.raw, 'tag[@name="display_name"]/@value');
    return Ext.util.Format.format('{0} - {1} - {2}', username, name, email);
}

Ext.define('BQ.model.Auth', {
    extend : 'Ext.data.Model',
    fields : [ {name: 'user', mapping: "@user" },
               {name: 'email', mapping: '@email' },
               {name: 'action', mapping: '@action' },
             ],
    /*associations: [{
        type: 'hasOne',
        model: 'BQ.model.Users',
        name: 'username',
        instanceName: 'username',
        //associationKey: 'username',
        primaryKey: 'uri',
        foreignKey: 'user',
        getterName: 'getUserName',
    }],*/

});

Ext.define('BQ.model.Users', {
    extend : 'Ext.data.Model',
    fields : [ {name: 'username', mapping: '@name' },
               {name: 'name', convert: getName },
               {name: 'email', mapping: '@value' },
               {name: 'uri', mapping: '@uri' },
               {name: 'full', convert: getFull },
             ],
    //belongsTo: 'BQ.model.Auth',
    proxy : {
        limitParam : undefined,
        pageParam: undefined,
        startParam: undefined,
        noCache: false,
        type: 'ajax',
        url : '/data_service/user?view=full&tag_order="@ts":desc&wpublic=true',
        reader : {
            type :  'xml',
            root :  'resource',
            record: 'user',
        },
    },
});

Ext.define('BQ.share.Panel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.bqsharepanel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip', 'Ext.selection.CellModel' ],
    cls: 'bq-share-panel',
    layout: {
        type: 'vbox',
        align: 'stretch'
    },

    initComponent : function() {

        if (this.resource)
            this.url = this.resource.uri+'/auth';

        //this.setLoading('Fetching users...');
        this.store_users = Ext.create('Ext.data.Store', {
            model : 'BQ.model.Users',
            autoLoad : false,
            autoSync : false,
            listeners : {
                scope: this,
                load: this.onUsersStoreLoaded,
            },
        });

        var storetype = this.resource ? 'BQ.share.Store' : 'Ext.data.Store';
        this.store = Ext.create(storetype, {
            model : 'BQ.model.Auth',
            autoLoad : false,
            autoSync : this.resource ? true : false,
            proxy : {
                type: 'ajax',
                url : this.url,
                actionMethods: {
                    create : 'PUT',
                    read   : 'GET',
                    update : 'POST',
                    destroy: 'PUT'
                },
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                noCache: false,
                reader : {
                    type :  'xml',
                    root :  'resource',
                    record: 'auth',
                },
                writer : {
                    type :  'bqauthxml',
                    root :  'resource',
                    record: 'auth',
                    resource: this.resource,
                    writeAllFields : true,
                    writeRecordId: false,
                },
            },
            listeners : {
                scope: this,
                load: this.onStoreLoaded,
                datachanged: this.onStoreChange,
            },
        });

        //--------------------------------------------------------------------------------------
        // items
        //--------------------------------------------------------------------------------------
        this.cellEditing = new Ext.grid.plugin.CellEditing({
            clicksToEdit: 1
        });
        var me = this;
        var grid_panel = {
            xtype: 'gridpanel',
            itemId  : 'main_grid',
            autoScroll: true,
            flex: 2,
            store: this.store,
            plugins: [this.cellEditing],
            //border: 0,
            columns: [{
                text: 'User',
                flex: 1,
                dataIndex: 'user',
                sortable: true,
                renderer: function(value, meta, record, row, col, store, view) {
                    if (me.users_xml)
                        return BQ.util.xpath_string(me.users_xml, '//user[@uri="'+value+'"]/@name');
                    // can't read directly from the store used for combobox due to filtering applied by it
                    //me.store_users.clearFilter(true);
                    //var r = me.store_users.findRecord( 'uri', value );
                    //if (r && r.data)
                    //    return r.data.username;
                    return '';
                },
            }, {
                text: 'Name',
                flex: 2,
                dataIndex: 'user',
                sortable: true,
                renderer: function(value) {
                    if (me.users_xml)
                        return BQ.util.xpath_string(me.users_xml, '//user[@uri="'+value+'"]/tag[@name="display_name"]/@value');
                    // can't read directly from the store used for combobox due to filtering applied by it
                    //me.store_users.clearFilter(true);
                    //var r = me.store_users.findRecord( 'uri', value );
                    //if (r && r.data)
                    //    return r.data.name;
                    return '';
                },
            }, {
                text: 'E-Mail',
                flex: 2,
                dataIndex: 'email',
                sortable: true,
                renderer: function(value, meta, record) {
                    if (value!=='') return value;
                    if (me.users_xml)
                        return BQ.util.xpath_string(me.users_xml, '//user[@uri="'+record.data.user+'"]/@value');
                    // can't read directly from the store used for combobox due to filtering applied by it
                    //me.store_users.clearFilter(true);
                    //var r = me.store_users.findRecord( 'uri', record.data.user );
                    //if (r && r.data)
                    //    return r.data.email;
                    return '';
                },
            }, {
                text: 'Permission',
                flex: 2,
                dataIndex: 'action',
                sortable: true,
                editor: new Ext.form.field.ComboBox({
                    triggerAction: 'all',
                    editable: false,
                    store: [
                        ['read','read'],
                        ['edit','edit']
                    ]
                })
            }, {
                xtype: 'actioncolumn',
                width: 30,
                sortable: false,
                menuDisabled: true,
                items: [{
                    icon : BQ.Server.url('/export/images/delete.png'),
                    tooltip: 'Delete share',
                    scope: this,
                    handler: this.onRemoveShare,
                }]
            }],
            viewConfig: {
                stripeRows: true,
                forceFit: true
            },
        };

        var new_share_cnt = {
            xtype: 'container',
            border: 0,
            layout: 'hbox',
            cls: 'bq-share-bar',
            //defaults: { scale: 'large'  },
            items: [{
                xtype: 'combobox',
                itemId: 'user_combo',
                cls: 'bq-user-picker',
                flex: 3,
                heigth: 30,
                //fieldLabel: 'Add new shares by user name or any e-mail',
                store: this.store_users,
                queryMode: 'local',
                displayField: 'full',
                valueField: 'email',
                anyMatch: true,
                autoSelect: false,
                hideTrigger: true,
                minChars: 2,
                listConfig: {

                },
                listeners : {
                    scope: this,
                    change: function(field) {
                        var v = field.getValue();
                        var p = field.getPicker();
                        var h = p && p.isVisible() ? p.getHeight() : 0;
                        if (!v || v.length<2 || h<5)
                            field.collapse();
                    },
                    select: this.onAddShare,
                    specialkey: function(field, e) {
                        if (e.getKey() === e.ENTER && !field.isExpanded) {
                            this.onAddShare();
                        }
                    },
                },
            }, {
                xtype: 'button',
                text: 'Add share',
                iconCls: 'icon-add',
                scale: 'medium',
                scope: this,
                handler: this.onAddShare,
            }, {
                xtype: 'tbfill',
            }, {
                xtype: 'checkbox',
                itemId  : 'notify_check',
                boxLabel: 'Notify users about new shares',
                //boxLabelAlign: 'before',
                //iconCls: 'icon-add',
                checked: true,
                scope: this,
                handler: this.onNotifyUsers,
            }],
        };

        var visibility_cnt = {
            xtype: 'container',
            border: 0,
            layout: 'hbox',
            cls: 'bq-visibility-bar',
            iconCls: 'bq-icon-visibility',
            items: [{
                xtype: 'container',
                html: this.resource ? '<h3>This resource is:</h3>' : '<h3>Set all resources to:</h3>',
            },{
                xtype: this.resource ? 'bqresourcepermissions' : 'bqmultipermissions',
                itemId : 'btn_permission',
                scale: 'large',
                resource: this.resource,
                permission: this.permission,
                prefix: '',
                listeners : {
                    changePermission: this.onChangePermission,
                    scope: this,
                },
            }, {
                xtype: 'container',
                flex: 1,
                html: '<p><b>Private</b> resources are only accessible by the owner and shared users.</p><p><b>Published</b> resources are visible to everybody but are only modifiable by owners and shared users.</p>',
            }],
        };

        this.items = [{
            xtype: 'container',
            html: '<h2>Share with public:</h2>',
        }, visibility_cnt, {
            xtype: 'container',
            html: '<h2>Share with collaborators:</h2>',
        }, {
            xtype: 'container',
            html: '<p>Add new shares by <b>user name</b> or by any <b>e-mail</b>, if the e-mail is not registered with the system a new user will be created and notified.</p>',
        }, new_share_cnt, grid_panel ];
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.setLoading('Fetching users...');
        this.store_users.load();
    },

    onUsersStoreLoaded: function( store, records, successful, eOpts) {
        this.setLoading(false);
        this.users_xml = this.store_users.proxy.reader.rawData;
        if (this.resource)
            this.store.load();
    },

    onStoreLoaded: function( store, records, successful, eOpts) {
        this.changed = undefined;
    },

    onNotifyUsers: function(box) {
        var notify = box.getValue();
        var url = this.url;
        if (!notify)
            url = Ext.urlAppend(url, 'notify=false');
        this.store.getProxy().url = url;
    },

    onAddShare: function() {
        var email = this.queryById('user_combo').getValue();
        if (!email) {
            BQ.ui.notification('User must have an e-mail for sharing...');
            return;
        }
        if (!(/\S+@\S+\.\S+/.test(email))) {
            BQ.ui.notification('The e-mail seems malformed...');
            return;
        }

        var r = this.store.findRecord( 'email', email );
        if (r && r.data) {
            BQ.ui.notification('You are already sharing with this user...');
            return;
        }

        var user = '';
        r = this.store_users.findRecord( 'email', email );
        if (r && r.data)
            user = r.data.uri;

        var self_user = BQSession.current_session && BQSession.current_session.user ? BQSession.current_session.user.uri : '';
        if (user === self_user) {
            BQ.ui.notification('You are trying to share with yourself, skipping...');
            return;
        }

        // Create a model instance
        var recs = this.store.add({
            user: user,
            email: email,
            action: 'read',
        });
        recs[0].setDirty();
        this.queryById('main_grid').view.refresh();

        // clear combo box when successfully added share
        this.queryById('user_combo').setValue('');
    },

    onRemoveShare: function(grid, rowIndex) {
        this.store.removeAt(rowIndex);
    },

    // this one deletes selected share
    onDeleteShare: function(){
        var selection = this.getView().getSelectionModel().getSelection()[0];
        if (selection) {
            this.store.remove(selection);
        }
    },

    onChangePermission: function(perm, btn) {
        this.fireEvent( 'changePermission', perm, this );
    },

    onStoreChange: function() {
        this.changed = true;
    },

    isChanged: function() {
        return this.changed === true;
    },

});

//--------------------------------------------------------------------------------------
// BQ.button.ResourceVisibility
// button that shows and changes resource visibility
// Parameters: resource
//--------------------------------------------------------------------------------------

Ext.define('BQ.button.ResourcePermissions', {
    extend: 'Ext.button.Button',
    alias: 'widget.bqresourcepermissions',
    cls: 'bq-button-visibility',
    iconCls: 'bq-icon-visibility',
    minWidth: 120,
    permission: 'private',
    prefix: 'Visibility: ',

    constructor: function(config) {
        this.addEvents({
            'changePermission' : true,
        });
        this.callParent(arguments);
        return this;
    },

    initComponent : function() {
        this.handler = this.toggleVisibility;
        this.scope = this;
        this.callParent();
        if (this.resource)
            this.permission = this.resource.permission;
    },

    afterRender : function() {
        this.callParent();
        this.setVisibility();
    },

    onSuccess: function(resource) {
        this.setLoading(false);
        this.permission = resource.permission;
        this.resource.permission = this.permission; // update currently loaded resource
        this.setVisibility();
        this.fireEvent( 'changePermission', this.permission, this );
    },

    onError: function() {
        this.setLoading(false);
        BQ.ui.warning('Could not change permission!');
    },

    toggleVisibility: function() {
        this.setLoading('');
        this.updatePermission(this.resource, this.resource.permission === 'private' ? 'published' : 'private');
    },

    updatePermission: function(res, perm) {
        var resource = BQFactory.makeShortCopy(res);
        resource.permission = perm;
        resource.save_(undefined,
                       callback(this, this.onSuccess),
                       callback(this, this.onError),
                       'post');
    },

    setVisibility : function() {
        var me = this;
        if (me.permission === 'published') {
            me.setText(this.prefix+'published');
            me.addCls('published');
        } else {
            me.setText(this.prefix+'private');
            me.removeCls('published');
        }
    },
});

//--------------------------------------------------------------------------------------
// BQ.auth.writer.Xml
// XML writer that writes records in the Bisque Auth format
//--------------------------------------------------------------------------------------

Ext.define('BQ.auth.writer.Xml', {
    extend: 'Ext.data.writer.Xml',
    alternateClassName: 'BQ.auth.XmlWriter',

    alias: 'writer.bqauthxml',

    documentRoot: 'resource',
    defaultDocumentRoot: 'resource',
    record: 'auth',
    ignoreKeys: {'id':undefined},

    writeRecords: function(request, data) {
        var me = this,
            xml = [],
            i = 0,
            len = data.length,
            root = me.documentRoot,
            record = me.record,
            needsRoot = data.length !== 1,
            item,
            key;

        // may not exist
        xml.push(me.header || '');

        if (!root && needsRoot) {
            root = me.defaultDocumentRoot;
        }

        if (root) {
            if (this.resource)
                xml.push('<', root, ' uri="', this.resource.uri, '/auth">');
            else
                xml.push('<', root, '>');
        }

        if (request.action !== "destroy") // destroy will only be fired when the list is empty
        for (i=0; i<len; ++i) {
            item = data[i];
            xml.push('<', record);
            for (key in item) {
                if (item.hasOwnProperty(key) && !(key in this.ignoreKeys)) {
                    xml.push(' ', key, '="', item[key], '"');
                }
            }
            xml.push('/>');
        }

        if (root) {
            xml.push('</', root, '>');
        }

        request.xmlData = xml.join('');
        return request;
    }
});

//--------------------------------------------------------------------------------------
// BQ.share.Store
// store that writes all of its data records disconsidering dirty bit at any change to store content,
// all records go out as a NEW record
//--------------------------------------------------------------------------------------

Ext.define('BQ.share.Store', {
    extend: 'Ext.data.Store',
    alias: 'store.bqsharestore',

    getNewRecords: function() {
        return this.data.items;
    },

    getUpdatedRecords: function() {
        return [];
    },

    getModifiedRecords : function(){
        return [];
    },

    getRemovedRecords: function() {
        // we have to set the removed list to fire the request with an empty document if everything is removed
        if (this.data.items.length>0)
            return [];
        return this.removed;
    },

});
