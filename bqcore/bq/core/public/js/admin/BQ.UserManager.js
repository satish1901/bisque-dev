// a patch resource tagger to view and modify xml 
// in the admin service (needs to be replaced with the
// updated tag viewer)
Ext.define('BQ.ResourceTagger.User', {
    extend: 'Bisque.ResourceTagger',
    mainService: 'admin/user',
    border: false,
    setResource: function (resource, template) {
        this.setLoading(true);
        
        if (resource instanceof BQObject)
            this.loadResourceInfo(resource);
        else if (resource) {
            // assume it is a resource URI otherwise
            BQFactory.request({
                uri: resource,
                cb: Ext.bind(this.loadResourceInfo, this),
                errorcb: function(error) {
                    BQ.ui.error('Error fetching resource:<br>'+error.message_short, 4000);
                },
            });
        } else {
            this.setLoading(false);
        }
    },
    
    loadResourceTags: function(data, template) {
        var type = this.resource.type || this.resource.resource_type;

        // Check to see if resource was derived from a template
        if (type && type.indexOf('/data_service/') != -1 && !template && this.rootProperty != 'gobjects') {
            BQFactory.request({
                uri: this.resource.type + '?view=deep',
                cb: Ext.bind(this.initCopy, this),
                errorcb: Ext.bind(this.loadResourceTags, this, [this.resource.tags, true])
            });
            return;
        }
        
        this.setLoading(false);

        var root = {};
        root[this.rootProperty] = data;

        this.removeAll(true);
        //this.addDocked(this.getToolbar());
        this.add(this.getTagTree(root));

        this.fireEvent('onload', this, this.resource);
        this.relayEvents(this.tree, ['itemclick']);
        if (this.onLoaded) this.onLoaded();
    },
    
    updateQueryTagValues: function(tag_name) {
        //var proxy = this.store_values.getProxy();
        //proxy.url = '/data_service/'+this.resource.resource_type+'?tag_values=' + encodeURIComponent(tag_name);
        this.store_values.load();
    },
    
    importMenu: function (btn, e) {
        if (!btn.menu) {
            var menuItems = [];

            for (var i = 0; i < BQApp.resourceTypes.length; i++) {
                menuItems.push({
                    text: 'from <b>' + BQApp.resourceTypes[i].name + '</b>',
                    name: '/data_service/' + BQApp.resourceTypes[i].name,
                    handler: this.importTags,
                    scope: this
                });
            }

            btn.menu = Ext.create('Ext.menu.Menu', {
                items: menuItems
            });
        }
        btn.showMenu();
    },
    
    loadResourceInfo: function (resource) {
        this.fireEvent('beforeload', this, resource);
        this.resource = resource;
        //this.editable = false;
        if (!this.disableAuthTest)
            this.testAuth(BQApp.user, false);
        if (this.resource.tags.length > 0)
            this.loadResourceTags(this.resource.tags);
        else
            this.resource.loadTags({
                cb: callback(this, "loadResourceTags"),
                depth: 'deep&wpublic=1'
            });
    },
    
    //delete will be a removal of the node and putting the rest of the body back
    // this will be changed in the next iteration when deltas are added and hopefully
    // this custom component can be removed
    deleteTags: function () {
        var me = this;
        var selectedItems = this.tree.getSelectionModel().getSelection(), parent;
        
        // removes elements for the xml
        if (selectedItems.length) {
            this.tree.setLoading(true);
            
            for (var i = 0; i < selectedItems.length; i++) {
                //parent = (selectedItems[i].parentNode.isRoot()) ? this.resource : selectedItems[i].parentNode.raw; //this resource will always be parent
                this.resource.remove(selectedItems[i].raw); //removes child node
                
                if (selectedItems[i].parentNode.childNodes.length <= 1)
                    selectedItems[i].parentNode.data.iconCls = 'icon-tag';
                selectedItems[i].parentNode.removeChild(selectedItems[i], true);
                
            }
            
            //PUT the modified xml back into the db
            var id = this.resource.resource_uniq;
            var xmlBody = this.resource.toXML();
            Ext.Ajax.request({
                url: '/admin/user/'+id,
                method: 'PUT',
                xmlData: xmlBody,
                headers: { 'Content-Type': 'text/xml' },
                success: function(response) {
                    var xml = response.responseXML;
                    this.setProgress(false);
                    //BQ.ui.notification('Tag(s) successfully deleted');
                    //update the list
                    //this.reload()
                    this.tree.setLoading(false);
                    BQ.ui.notification(selectedItems.length + ' record(s) deleted!');
                    me.fireEvent('onDone', me, xml.documentElement)
                },
                failure: function(response) {
                    this.setProgress(false);
                    this.tree.setLoading(false);
                    BQ.ui.error('Failed to delete resource: '+id);
                    this.setResource('/admin/user/'+id) //reset resource
                    me.fireEvent('onError', me, response)
                },
                scope: this,
            });      
            
            this.tree.getSelectionModel().deselectAll();
        } else
            BQ.ui.notification('No records modified!');
    },
    
    //saveTags will put the entire body back
    // this will be changed in the next iteration when deltas are added
    saveTags: function (parent, silent) {
        var me = this;
        if (silent === undefined)
            silent = this.silent !== undefined ? this.silent : false;

        var resource = (typeof parent == BQObject) ? parent : this.resource;
        var me = this;
        if (this.store.applyModifications()) {
            this.setProgress('Saving');
            var xmlBody = resource.toXML();
            var id = resource.resource_uniq; //we want to put the entire body back for now
            Ext.Ajax.request({
                url: '/admin/user/'+id,
                method: 'PUT',
                params: {view:'deep'},
                xmlData: xmlBody,
                headers: { 'Content-Type': 'text/xml' },
                success: function(response) {
                    var xml = response.responseXML;
                    this.setProgress(false);
                    
                    BQ.ui.notification('Tag(s) successfully modified');
                    me.fireEvent('onDone', me, xml.documentElement)
                },
                failure: function(response) {
                    BQ.ui.error('Failed to modify resource: '+id);
                    this.setProgress(false);
                    //this.reload()
                    this.setResource('/admin/user/'+id)
                    me.fireEvent('onError', me, response)
                },
                scope: this,
            });
        } else
            BQ.ui.notification('No records modified!');
    },
});


Ext.define('BQ.admin.UserTable', {
    extend : 'Ext.grid.Panel',
    xtype: 'BQAdminUserTable',
    title: 'User List',
    userInfoPanel: null,
    border: false,

    viewConfig: {
        markDirty: false,
    },
    selModel: {  allowDeselect: true },
    columns: {
        items: [{
            dataIndex:'profile_picture',
            width: 45,
            renderer: function(value, meta, record){
                if (value) {
                    var image_url = '/'+value+'/pixels?thumbnail';
                    return '<img  src="'+image_url+'" alt=="No Image Found!" height="32" width="32"/>';
                } else {
                    return '<img  src="/images/toolbar/user.png" alt=="No Image Found!" height="32" width="32"/>';
                }
            },
        },{
            text: 'ID', dataIndex: 'resource_uniq', sortable: true, flex:1,
        },{
            text: 'User Name', dataIndex: 'name', sortable: true, flex:1,
        },{
            text: 'Email', dataIndex: 'email', sortable: true, flex:1,
        }, {
            text: 'Display Name', dataIndex: 'display_name', sortable: true, flex:1,
        }],
        defaults: {
            renderer : function (value, meta, record) {
                var value = value || '';
                return '<div style="line-height:32px; text-align:center; height:32px; overflow:hidden; text-overflow:ellipsis">'+value+'</div>';
            }
        }
    },   
    renderTo: Ext.getBody(),
    initComponent: function(config) {
        var config = config || {};
        var me = this;
        
        var tbar = new Ext.Toolbar({
            margin: false,
            border: false,
            items:[{
                xtype: 'button',
                text: 'Add',
                height: '50px',
                scale: 'large',
                tooltip: 'Add new user',
                handler: this.addUserWin,
                disabled: false,
                scope: this,
                listeners: {}, //remove default listeners
            }, {
                xtype: 'button',
                text: 'Delete',
                height: '50px',
                scale: 'large',
                tooltip: 'Delete existing user',
                handler: this.deleteUserWin,
                
                scope: this,
            },{
                xtype: 'button',
                text: 'Remove<br>All User<br>Data',
                scale: 'large',
                height: '50px',
                tooltip: 'Removes all data from selected user',
                handler: this.deleteUserImagesMessage,
                scope: this,
            },{
                xtype: 'button',
                text: 'Login<br>As',
                scale: 'large',
                height: '50px',
                tooltip: 'Login as selected user',
                handler: this.loginUserMessage,
                scope: this,
            }, {
                xtype: 'button',
                text: 'Refresh',
                height: '50px',
                scale: 'large',
                tooltip: 'Refresh information in the list',
                handler: this.reload,
                disabled: false,
                scope: this,
                listeners: {}, //remove default listeners
            }],
            defaults: {
                disabled: true,
                listeners: { //disable buttons when deselected
                    afterrender: function(el) {
                        var buttonEl = el;
                        me.on('select',
                            function(el, record) {
                                buttonEl.setDisabled(false);
                        });   
                        me.on('deselect',
                            function(el, record) {
                                buttonEl.setDisabled(true);                  
                        });
                        var store = me.getStore();
                        store.on('load',
                            function(el,record) {
                                buttonEl.setDisabled(true);
                        });
                    }
                }
            },
        });
        if (BQApp.user.name=='admin') { //the way to check for admin needs to be changed
            this.initTable();
        }
        Ext.apply(me, {
            store: me.store,
            tbar: tbar
        });
        this.callParent([config]);
    },
    
    initTable: function() {
        Ext.define('BQ.model.adminUsers', {
            extend: 'Ext.data.Model',
            fields: [{
                name: 'name' ,
                mapping: '@name', 
            },{
                name: 'resource_uniq',
                mapping: '@resource_uniq',
            },{
                name: 'email',
                mapping: "tag[@name='email']/@value",
            },{
                name: 'profile_picture',
                mapping: "tag[@name='profile_picture']/@value",
            },{
                name: 'display_name',
                mapping: "tag[@name='display_name']/@value",                
            }],
        });

        this.store = Ext.create('Ext.data.Store', {
            model: 'BQ.model.adminUsers',
            storeID: 'BQUsers',
            autoLoad: false, //dont know yet why this doesnt work
            //autoLoad: true,
            autoSync: false,
            proxy: {
                noCache: false,
                type: 'ajax',
                limitParam: undefined,
                pageParam: undefined,
                startParam: undefined,
                url: '/admin/user?view=full',
                reader: {
                    type: 'xml',
                    root: 'resource',
                    record: 'user',
                },
            },
        });
        this.store.reload();
    },
    
    addUserWin : function() {
        var me = this;
        var userForm = Ext.create('Ext.form.Panel', {
            //padding: '8px',
            padding: '20px',
            layout: 'anchor',
            border: false,
            defaultType: 'textfield',
            items: [{
                padding: '5px',
                fieldLabel: 'User name',
                name: 'username',
                allowBlank: false,
            },{
                padding: '5px',
                fieldLabel: 'Password',
                name: 'password',
                inputType: 'password',
                allowBlank: false,
                //invalidText: 
            },{
                padding: '5px',
                fieldLabel: 'Display Name',
                name: 'displayname',
                allowBlank: false,
            },{
                padding: '5px',
                fieldLabel: 'E-mail',
                name: 'email',
                allowBlank: false,
            }],
        });
        
        var win = Ext.create('Ext.window.Window', {
            border: false,
            modal : true,
            buttonAlign: 'center',
            title: 'Create New User',
            bodyStyle: 'background-color:#FFFFFF',
            layout : 'fit',
            items: userForm,
            scope: this,
            buttons: [{
                //formBind: true, //only enabled once the form is valid
                //disabled: true,
                text: 'Submit',
                handler: function() {
                    var form = userForm.getForm();
                    if (form.isValid()) {
                        var values = form.getValues()
                        me.addUser(values.username, values.password, values.displayname, values.email)
                        win.close();

                    }
                },
            },{
                text: 'Cancel',
                handler: function() {
                    win.close();
                },
            }]
        });
        win.show();
    },
    
    addUser: function(username, password, display_name, email) {
        var user = document.createElement("user");
        user.setAttribute('name',username);
        var passwordTag = document.createElement("tag");
        passwordTag.setAttribute('name','password');
        passwordTag.setAttribute('value',password);
        user.appendChild(passwordTag);
        var emailTag = document.createElement("tag");
        emailTag.setAttribute('name','email');
        emailTag.setAttribute('value',email);
        user.appendChild(emailTag);
        var display_nameTag = document.createElement("tag");
        display_nameTag.setAttribute('name','display_name');
        display_nameTag.setAttribute('value',display_name);
        user.appendChild(display_nameTag);
        
        Ext.Ajax.request({
            url: '/admin/user',
            xmlData: user.outerHTML,
            method: 'POST',
            headers: { 'Content-Type': 'text/xml' },
            success: function(response) {
                var xml = response.responseXML;
                this.reload()
            },
            failure: function(response) {
                BQ.ui.error('Failed to add new user!')
            },
            scope: this
        })
    },
    
    deleteUserWin : function() {
        var record = this.getSelectionModel().getSelection();
        if (record.length>0) {
            var resource_uniq = record[0].data.resource_uniq;
            var userName = record[0].data.name;
            var win = Ext.MessageBox.show({
                title: 'Delete User',
                msg: 'Are you sure you want to delete User: '+userName+'? (This operation can take awhile to complete)',
                buttons: Ext.MessageBox.OKCANCEL,
                fn: function(buttonResponse) {
                    if (buttonResponse === "ok") {
                        this.deleteUser(resource_uniq)
                        record.remove()
                    }
                },
                scope: this,
            });
        } else {
            var win = Ext.MessageBox.show({
                title: 'Delete User',
                msg: 'No users were selected to be deleted.',
                buttons: Ext.MessageBox.OK,
                scope: this,
            });
        }
    },
    
    deleteUser: function(uniq) {
        var me = this;
        Ext.Ajax.request({
            url: '/admin/user/'+uniq,
            method: 'DELETE',
            headers: { 'Content-Type': 'text/xml' },
            success: function(response) {
                var xml = response.responseXML;
                //update the list
                BQ.ui.notification('Resource: '+uniq+' deleted succesfully!')
                this.reload()
            },
            failure: function(response) {
                BQ.ui.error('Failed to delete resource: '+uniq)
            },
            scope: this,
        })
    },
    
    deleteUserImagesMessage: function() {
        var record = this.getSelectionModel().getSelection();
        if (record.length>0) {
            var resource_uniq = record[0].data.resource_uniq;
            var userName = record[0].data.name;
            var win = Ext.MessageBox.show({
                title: 'Delete User\'s Images',
                msg: 'Are you sure you want to delete User: '+userName+'\'s Images? (This operation can take awhile to complete)',
                buttons: Ext.MessageBox.OKCANCEL,
                fn: function(buttonResponse) {
                    if (buttonResponse === "ok") {
                        this.deleteUserImages(resource_uniq)
                        record.remove()
                    }
                },
                scope: this,
            });
        } else {
            var win = Ext.MessageBox.show({
                title: 'Delete User\'s Images ',
                msg: 'No users were selected.',
                buttons: Ext.MessageBox.OK,
                scope: this,
            });
        }       
    },
    
    deleteUserImages: function() {
         Ext.Ajax.request({
            url: '/admin/user/'+uniq+'/image',
            method: 'DELETE',
            headers: { 'Content-Type': 'text/xml' },
            success: function(response) {
                var xml = response.responseXML;
                //update the list
                BQ.ui.notification('All images were successfully deleted')
            },
            failure: function(response) {
                BQ.ui.error('Failed to delete all of users: '+uniq+' images')
            },
            scope: this,
        })        
    },
    
    loginUserMessage : function(){
        var record = this.getSelectionModel().getSelection();
        if (record.length==1) {
            var resource_uniq = record[0].data.resource_uniq;
            var userName = record[0].data.name;
            var win = Ext.MessageBox.show({
                border: false,
                title: 'Login As',
                msg: 'Are you sure you want to login as '+userName+'? (Warning: Your admin session will be closed the page will be reloaded)',
                buttons: Ext.MessageBox.OKCANCEL,
                fn: function(buttonResponse) {
                    if (buttonResponse === "ok") {
                        this.loginUser(resource_uniq)
                    }
                },
                scope: this,
            });
        } else if (record.length>1){ //in the case that multiselect is allowed
            var win = Ext.MessageBox.show({
                border: false,
                title: 'Login As',
                msg: 'Only one user can be login at a time.',
                buttons: Ext.MessageBox.OK,
                scope: this,
            });            
        } else {
            var win = Ext.MessageBox.show({
                border: false,
                title: 'Login As',
                msg: 'No user was selected to be login as.',
                buttons: Ext.MessageBox.OK,
                scope: this,
            });
        }        
    },
    
    loginUser : function(userUniq) {
         Ext.Ajax.request({
            url: '/admin/user/'+userUniq+'/login',
            method: 'GET',
            headers: { 'Content-Type': 'text/xml' },
            headers: { 'Content-Type': 'text/xml' },
            success: function(response) {
                var xml = response.responseXML;
                location = '/client_service'; //reloads with new credentials
                //update the list
            },
            failure: function(response) {
                BQ.ui.error('An issue occured when tryin to log in as '+userUniq)
            },
            scope: this,
        })        
    },
    
    reload : function() {
        if (this.userInfoPanel) {
            this.userInfoPanel.deselectUser();
        }
        this.getStore().load();
    },
});

Ext.define('BQ.admin.UserInfo', {
    extend: 'Ext.panel.Panel',
    title: 'User View',
    //layout : 'fit',
    layout: 'card',
    border: false,
    initComponent: function(config) {
        items = [];
        var me = this;
        
        this.tagger = Ext.create('BQ.ResourceTagger.User', {
            layout : 'fit',
            editable: true,
            disableAuthTest: true,
            tree: {
                btnAdd: false, //enable add button
                btnDelete: false, //enable delete button
            },
            //hidden: true,
            //viewMode: 'ReadOnly',
            resource: '',
            //flex: 1,
        });
        
        this.userManagerWelcomePage = Ext.createWidget('box',{
            border: false,
            padding: '10px',
            layout: 'fit',
            tpl: [
                '<h2>Welcome to the Administrator\'s User Manager</h2>',
                '<p>This page allows for an admin to create, delete, modify and manage users in the system with normal bisque credentials. If the user is registered to bisque with another system like cas or google this page will not be able to modify those users with the current iteration. Below is some information on how this page can be used to manage users.</p>',
                '<p><b>Create User:</b> Select the add button at the top of the User List and a form will pop up. Enter the neccessary user information.</p>',
                '<p><b>Delete User:</b> Select a user and then select the Delete at the top of the User List</p>',
                '<p><b>Modify User:</b> Select a user and tags for the user will appear in the User View. Modify the tags you want to modify. <i>Note: The email, password and display name tags cannot be delete.</i></p>',
                '<p><b>Login As User:</b> Select a user and press the Login As button at the top of the User List. This will log in the currect user as the selected user and return to the front page.</p>',
            ],
            data: {},
        });
        var items = [
            this.userManagerWelcomePage,
            this.tagger,
        ];
        Ext.apply(me, {
            items: items,
        });
        this.callParent([config]);
    },
    
    selectUser: function(resource_uri) {
        this.layout.setActiveItem(this.tagger);
        this.tagger.setResource(resource_uri+'?view=deep');
        
    },
    deselectUser: function() {
        this.layout.setActiveItem(this.userManagerWelcomePage);
        //this.tagger.setResource('');
    },
});


Ext.define('BQ.admin.UserManager', {
    extend: 'Ext.container.Container',
    layout: 'border',
    border: false,
    //renderTo: Ext.getBody(),
    initComponent: function(config) {
        var config = config || {};
        items = [];
        var me = this;
        
        this.userInfo = Ext.create('BQ.admin.UserInfo',{
            width: '35%',
            plain : true,
            hidden : false,
            collapsible : true,
            region: 'east',
            split: true,
            resource: '',
            minimizable: true,
        });
        
        this.userTable = Ext.create('BQ.admin.UserTable', {
            split: true,
            region: 'center',
            autoScroll: true,
            plain : true,
            userInfoPanel: this.userInfo,
        });
        
        this.userTable.on('select',
            function(el, record) {
                var resource_uniq = record.get('resource_uniq');
                me.userInfo.selectUser('/admin/user/'+resource_uniq);
        });
        
        this.userTable.on('deselect',
            function(el, record) {
                me.userInfo.deselectUser();
        });
        
        this.userInfo.tagger.on('onDone', 
            function(el, xmlResponse) {
                var userName = xmlResponse.attributes['name'].value;
                var record = me.userTable.store.findRecord('name', userName);
                var email = xmlResponse.querySelector('tag[name="email"]');
                record.set('email', email ? email.attributes['value'].value: '');
                var resource_uniq = xmlResponse.attributes['resource_uniq'];
                record.set('resource_uniq', resource_uniq ? resource_uniq.value: '');
                var profile_picture = xmlResponse.querySelector('tag[name="profile_picture"]');
                record.set('profile_picture', profile_picture ?  profile_picture.attributes['value'].value : '');
                var display_name = xmlResponse.querySelector('tag[name="display_name"]');
                record.set('display_name', display_name ?  display_name.attributes['value'].value : '');                
        });
        
        items.push(this.userTable);
        items.push(this.userInfo);
        
        Ext.apply(me, {
            items: items,
        }); 
        this.callParent([config]);
        
    },
});