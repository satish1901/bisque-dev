Ext.Loader.setConfig({
    enabled: true
});
Ext.Loader.setPath('Ext.ux', bq.url('/extjs/examples/ux'));

Ext.require([
    'Ext.ux.CheckColumn'
]);

Ext.define('BQ.ShareDialog', {
    
    extend : 'Ext.window.Window',

    constructor : function(config)
    {
        config          =   config || {};
        config.height   =   config.height || '65%';
        config.width    =   config.width || '65%';

        var bodySz      =   Ext.getBody().getViewSize();
        var height      =   parseInt((config.height.toString().indexOf("%") == -1) ? config.height : (bodySz.height * parseInt(config.height) / 100));
        var width       =   parseInt((config.width.toString().indexOf("%") == -1) ? config.width : (bodySz.width * parseInt(config.width) / 100));

        this.eastPanel  =   Ext.create('Ext.panel.Panel', {
            layout      :   {
                                type    :   'vbox',
                                align   :   'stretch'
                            },
            flex        :   4,
            title       :   'Add user',   
            region      :   'east',
            margin      :   '3 3 3 0',
            collapsible :   true,
            frame       :   true,
            split       :   true
        });
        
        this.centerPanel = Ext.create('Ext.panel.Panel', {
            region      :   'center',
            border      :   false,
            flex        :   6,
            margin      :   '3 1 3 3',
            layout      :   'fit',
        });

        Ext.apply(this,
        {
            title       :   'Sharing settings - ' + config.resource.name,
            modal       :   true,
            height      :   height,
            bodyStyle   :   'border:0px',
            width       :   width,
            layout      :   'border',
            bodyCls     :   'white',
            items       :   [this.centerPanel, this.eastPanel],
            bbar :
            {
                xtype   :   'toolbar',
                style   :   {
                                background  :   '#FFF',
                                border      :   0
                            },
                layout:
                {
                    type:'hbox',
                    align:'middle',
                    pack: 'center'
                },
                defaults    :   {
                                    cls         :   'x-btn-default-medium',
                                    scale       :   'medium',
                                    style       :   'border-color:#D1D1D1',   
                                    width       :   85,
                                    margin      :   1,
                                    textAlign   :   'left',
                                    scope       :   this,
                                },
                padding :   '6 6 9 6',
                items   :
                [
                    {
                            text    :   'Save',
                            iconCls :   'icon-select24',
                            handler :   this.btnSave,
                            scope   :   this,
                    },
                    {
                            text    :   'Cancel',
                            iconCls :   'icon-cancel24',
                            handler :   this.btnCancel,
                    }
                ]
            }
                        
        }, config);
        
        this.callParent(arguments);
        
        this.addComponents();
        this.show();
    },
    
    btnSave : function()
    {
        var modified = false;

        for (var i=0;i<this.store.getCount();i++)
        {
            var currentRecord = this.store.getAt(i);
            if (currentRecord.dirty)
            {
                modified = true;
                currentRecord.commit();
                this.authRecord.children[i-1].action = (currentRecord.get('edit')) ? 'edit' : 'read';
            }
        }

        if (modified || this.userModified)
        {
            this.authRecord.save_();
            BQ.ui.notification('Sharing settings saved!', 2500);
        }
            
        this.close();
    },

    btnCancel : function()
    {
        this.close();
    },
     
    userSelected : function(resourceBrowser, user)
    {
        this.addUser({
            user    :   user.uri,
            email   :   user.email,
            action  :   'read'
        });
    },
    
    addEmail : function()
    {
        this.addUser({
            email   :   this.txtEmail.getValue(),
            action  :   'read'
        });
        
        this.clearForm();
    },
    
    clearForm : function()
    {
        this.txtEmail.setValue('');
        this.txtEmail.focus();
    },
    
    addUser : function(record)
    {
        this.userModified = true;
        
        var authRecord = new BQAuth();
        Ext.apply(authRecord, record);
        this.authRecord.addchild(authRecord);
        
        this.reloadPermissions(this.authRecord);
    },
    
    reloadPermissions : function(authRecord)
    {
        if (!authRecord)
        {
            this.resource.getAuth(Ext.bind(this.reloadPermissions, this));
            return;
        }
        
        this.authRecord = authRecord;
        authRecord = this.authRecord.children;
                    
        var record = [];
        var owner = this.browser.findRecord(this.resource.owner), user;
        record.push([owner.display_name, owner.email, 'owner']);
        
        for (var i=0; i<authRecord.length; i++)
        {
            if (authRecord[i].user)
            {
                user = this.browser.findRecord(authRecord[i].user);
                record.push([user.display_name, user.email, authRecord[i].action]);
            }
            else
                record.push(['', authRecord[i].email, authRecord[i].action]);
        }
        
        this.store.loadData(record);
    },
    
    addComponents : function()
    {
        
        this.browser = Ext.create('Bisque.ResourceBrowser.Browser',
        {
            layout          :   Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Grid,
            layoutConfig    :   {
                                    colIconWidth    :   8,
                                    colValueText    :   'Email'
                                },
            flex            :   1,
            frame           :   true,
            region          :   'east',
            viewMode        :   'ViewSearch',
            wpublic         :   'true',
            dataset         :   '/data_service/user?view=full',
            listeners       :   {
                                    scope           :   this,
                                    'Select'        :   this.userSelected,
                                    'browserLoad'   :   Ext.Function.pass(this.reloadPermissions, [undefined], this) 
                                }
        });
        
        var label = Ext.create('Ext.form.Label',
        {
            html    :   '<b>- or -</b>',
            margin  :   3,
            style   :   'color:#04408C;text-align:center'
        });
        
        this.form = Ext.create('Ext.form.Panel',
        {
            frame           :   true,
            height          :   110,
            title           :   'Invite a guest',
    
            fieldDefaults   :   {
                                    labelAlign: 'left',
                                    labelWidth: 90,
                                    anchor: '100%'
                                },
    
            items           :   [{
                                    xtype       :   'textfield',
                                    name        :   'email',
                                    fieldLabel  :   'Email address',
                                    vtype       :   'email',
                                    margin      :   '10 5 5 5'
                                }],
            buttonAlign     :   'center',
            buttons         :   {
                                    defaults    :   {
                                                        scope   :   this,
                                                        padding :   5
                                                    },
                                    items       :   [{
                                                        text    :   'Add guest',
                                                        handler :   this.addEmail
                                                    },
                                                    {
                                                        text    :   'Clear',
                                                        handler :   this.clearForm
                                                    }                                                    ]
                                }
        });
        
        this.txtEmail = this.form.getComponent(0);
        
        this.grid = Ext.create('Ext.grid.Panel',
        {
            store   :   this.getStore(),
            frame   :   true,
            border  :   false,
            
            columns :   {
                            defaults : {
                                minWidth : 1
                            },
                            items : [
                            {
                                text: 'Name',
                                flex: 0.4,
                                sortable: false,
                                dataIndex: 'name',
                            },
                            {
                                text: 'Email address',
                                flex: 0.5,
                                sortable: false,
                                align: 'center',
                                dataIndex: 'value'
                            }, 
                            {
                                text    :   'Permissions',
                                defaults:   {
                                                align       :   'center',
                                                sortable    :   false,
                                                minWidth    :   25
                                            },
                                columns :   [{
                                                xtype       :   'checkcolumn',
                                                text        :   'View',
                                                dataIndex   :   'view',
                                                allowBlank  :   false
                                            },
                                            {
                                                xtype       :   'checkcolumn',
                                                text        :   'Edit',
                                                dataIndex   :   'edit',
                                            }],
                                flex: 0.3,
                                sortable: false,
                                align: 'center',
                            }, 
                            {
                                xtype: 'actioncolumn',
                                itemId: 'colAction',
                                maxWidth: 80,
                                menuDisabled : true,
                                sortable : false,
                                align: 'center',
                                items: [
                                {
                                    icon : bq.url('../export_service/public/images/delete.png'),
                                    align : 'center',
                                    tooltip: 'Remove',
                                    handler: function(grid, rowIndex, colIndex)
                                    {
                                        // Cannot remove owner record
                                        if (rowIndex == 0)
                                        {
                                            BQ.ui.error('Cannot delete owner record!', 3000);
                                            return;
                                        }
                                        
                                        this.userModified = true;
                                        this.authRecord.children.splice(rowIndex-1, 1);
                                        grid.store.removeAt(rowIndex);
                                    },
                                    scope : this
                                }]
                            }],
                        }
        });
        
        this.centerPanel.add(this.grid);
        this.eastPanel.add([this.browser, label, this.form]);
    },
    
    getStore : function()
    {
        this.store = Ext.create('Ext.data.ArrayStore', {
            fields: 
            [
                'name',
                'value',
                'permission',
                {
                    name : 'view',
                    type : 'bool',
                    convert : function(value, record){
                        return true;
                    }
                },
                {
                    name : 'edit',
                    type : 'bool',
                    convert : function(value, record){
                        if (value == undefined)
                            value = (record.data.permission=='edit' || record.data.permission=='owner') ? true : false
                        if (value == true)
                            record.set('view', true);
                        if (record.data.permission=='owner')
                            value = true;

                        return value;
                    }
                },
            ],
        });
        
        return this.store;
    }
});
