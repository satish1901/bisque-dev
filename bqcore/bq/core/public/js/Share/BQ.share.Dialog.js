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
//--------------------------------------------------------------------------------------

Ext.define('BQ.share.Dialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.bqsharedialog',
    border: 0,
    layout: 'fit',
    modal : true,
    border : false,
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
                scope: this,
                handler: this.close,
            }],
            items  : [{
                xtype: 'bqsharepanel',
                border: 0,
                resource: config.resource,
            }],
        }, config);

        this.callParent(arguments);
        this.show();
    },
});

//--------------------------------------------------------------------------------------
// BQ.share.Panel
//--------------------------------------------------------------------------------------

function xpath(node, expression) {
    var xpe = new XPathEvaluator();
    var nsResolver = xpe.createNSResolver(node.ownerDocument == null ? node.documentElement : node.ownerDocument.documentElement);
    var result = xpe.evaluate( expression, node, nsResolver, XPathResult.STRING_TYPE, null );
    return result.stringValue;
}

function getName(v, record) {
    return xpath(record.raw, 'tag[@name="display_name"]/@value');
}

function getFull(v, record) {
    var username = xpath(record.raw, '@name');
    var email = xpath(record.raw, '@value');
    var name = xpath(record.raw, 'tag[@name="display_name"]/@value');
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
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip', 'Ext.selection.CellModel', ],
    cls: 'bq-share-panel',
    layout: {
        type: 'vbox',
        align: 'stretch'
    },

    initComponent : function() {

        this.url = this.resource.uri+'/auth';

        this.store_users = Ext.create('Ext.data.Store', {
            model : 'BQ.model.Users',
            autoLoad : true,
            autoSync : false,
            listeners : {
                'load': this.onUsersStoreLoaded,
                scope: this,
            },
        });

        this.store = Ext.create('BQ.share.Store', {
            model : 'BQ.model.Auth',
            autoLoad : false,
            autoSync : true,
            proxy : {
                actionMethods: {
                    create : 'PUT',
                    read   : 'GET',
                    update : 'POST',
                    destroy: 'POST'
                },
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                noCache: false,
                type: 'ajax',
                url : this.url,
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
                        return xpath(me.users_xml, '//user[@uri="'+value+'"]/@name');

                    //me.store_users.clearFilter(true);
                    var r = me.store_users.findRecord( 'uri', value );
                    if (r && r.data)
                        return r.data.username;
                    return '';
                },
            }, {
                text: 'Name',
                flex: 2,
                dataIndex: 'user',
                sortable: true,
                renderer: function(value) {
                    if (me.users_xml)
                        return xpath(me.users_xml, '//user[@uri="'+value+'"]/tag[@name="display_name"]/@value');

                    //me.store_users.clearFilter(true);
                    var r = me.store_users.findRecord( 'uri', value );
                    if (r && r.data)
                        return r.data.name;
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
                        return xpath(me.users_xml, '//user[@uri="'+record.data.user+'"]/@value');

                    //me.store_users.clearFilter(true);
                    var r = me.store_users.findRecord( 'uri', record.data.user );
                    if (r && r.data)
                        return r.data.email;
                    return '';
                },
            }, {
                text: 'Permission',
                flex: 2,
                dataIndex: 'action',
                sortable: true,
                editor: new Ext.form.field.ComboBox({
                    typeAhead: true,
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
                    icon : bq.url('../export_service/public/images/delete.png'),
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
                flex: 2,
                //fieldLabel: 'Add new shares by user name or any e-mail',
                store: this.store_users,
                queryMode: 'local',
                displayField: 'full',
                valueField: 'email',
                anyMatch: true,
            }, {
                xtype: 'button',
                text: 'Add share',
                iconCls: 'icon-add',
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
                html: '<h3>This resource is:</h3>',
            },{
                xtype: 'bqresourcepermissions',
                itemId : 'btnPerm',
                scale: 'large',
                resource: this.resource,
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

    onUsersStoreLoaded: function( store, records, successful, eOpts) {
        this.users_xml = this.store_users.proxy.reader.rawData;
        this.store.load();
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
        var user = '';

        var r = this.store.findRecord( 'email', email );
        if (r && r.data) {
            BQ.ui.notification('You are already sharing with this user...');
            return;
        }

        r = this.store_users.findRecord( 'email', email );
        if (r && r.data)
            user = r.data.uri;

        // Create a model instance
        this.store.add({
            user: user,
            email: email,
            action: 'read',
        });z
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

    initComponent : function() {
        this.handler = this.toggleVisibility,
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.setVisibility();
    },

    onOk: function(resource) {
        this.setLoading(false);
        this.resource.permission = resource.permission;
        this.setVisibility();
    },

    onError: function() {
        this.setLoading(false);
        BQ.ui.warning('Could not change permission!');
    },

    toggleVisibility: function() {
        this.setLoading('');
        var resource = BQFactory.makeShortCopy(this.resource);
        resource.permission = this.resource.permission === 'private' ? 'published' : 'private';
        resource.save_(undefined,
                       callback(this, this.onOk),
                       callback(this, this.onError));
    },

    setVisibility : function() {
        var me = this;
        if (me.resource.permission === 'published') {
            me.setText('published');
            me.addCls('published');
        } else {
            me.setText('private');
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

        for (; i < len; ++i) {
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
        return [];
    },

});
