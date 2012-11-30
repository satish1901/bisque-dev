
//Ext.require(['*']);
Ext.require(['Ext.toolbar.Toolbar']);
Ext.require(['Ext.tip.QuickTip']);
Ext.require(['Ext.tip.QuickTipManager']);

//--------------------------------------------------------------------------------------
// Toolbar actions
//-------------------------------------------------------------------------------------- 

var urlAction = function(url) { 
    window.open(url); 
}; 
  
var pageAction = function(url) { 
    document.location = url; 
};   

var htmlAction = function( url, title ) {
  var c = {
      modal: true,
      //width: '60%',
      //height: '60%',
      width: BQApp?BQApp.getCenterComponent().getWidth()/1.6:document.width/1.6,
      height: BQApp?BQApp.getCenterComponent().getHeight()/1.2:document.height/1.2,
      
      buttonAlign: 'center',
      autoScroll: true,
      loader: { url: url, renderer: 'html', autoLoad: true },
      buttons: [ { text: 'Ok', handler: function () { w.close(); } }]
   };
   if (title && typeof title == 'string') c.title = title;
   
   var w = Ext.create('Ext.window.Window', c);
   w.show();           
}; 

function analysisAction(o, e) {
    //if (typeof BQApp.resource == 'undefined') {
    //    pageAction('/analysis/');
    //    return;
    //}

    var w = Math.round(Math.min(500, BQApp?BQApp.getCenterComponent().getWidth()*0.8:document.width*0.8));    
    var h = Math.round(BQApp?BQApp.getCenterComponent().getHeight()*0.99:document.height*0.99);
    
    //var resourceBrowser  = new Bisque.ResourceBrowser.Dialog({    
    var resourceBrowser  = Ext.create('Bisque.ResourceBrowser.Browser', {
        layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.IconList,
        wpublic: true,
        selType: 'SINGLE',        
        viewMode: 'ModuleBrowser',
        showOrganizer: false,
        dataset : '/module_service/',
        listeners : { 
            'Select' : function(rb, module) {
                if (BQApp.resource) 
                    pageAction('/module_service/' + module.name + '/?resource=' + BQApp.resource.uri)
                else    
                    pageAction('/module_service/' + module.name)
            },
        }
    });

    var tip = Ext.create('Ext.tip.ToolTip', {
        target: o.el,
        anchor: "right",
        width :  w,
        maxWidth: w,
        minWidth: w,
        height:  h,
        layout: 'fit',
        autoHide: false,
        shadow: true,
        items: [resourceBrowser],
                        
    }); 
    tip.show();   
}

//--------------------------------------------------------------------------------------
// Main Bisque toolbar menu
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.Application.Toolbar', {
    extend: 'Ext.toolbar.Toolbar',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    // default toolbar config
    region: 'north', 
    border: false,             
    layout: { overflowHandler: 'Menu',  },
    defaults: { scale: 'large',  },
    cls: 'toolbar-main',
    preferences : {},
    
    title: 'Bisque demo', 
    toolbar_opts: { 'browse':true, 'upload':true, 'download':true, 'services':true, 'query':true },   
    image_query_text: 'Find images using tags',

    tools_big_screen: [ 'button_upload', 'button_download' ],  
    
    tools_none: [ 'menu_user_signin', 'menu_user_register', 'menu_user_register_sep','menu_user_recover' ],    
    tools_user: ['menu_user_name', 'menu_user_profile', 'menu_user_signout', 'menu_user_prefs', 
                 'menu_user_signout_sep', 'menu_resource_template', 'menu_resource_create', ],
    tools_admin: ['menu_user_admin_separator', 'menu_user_admin', 'menu_user_admin_prefs', ],    
    
    initComponent : function() {
        this.images_base_url = this.images_base_url || bq.url('/images/toolbar/');
        this.title = bq.title || this.title;        
        
        Ext.QuickTips.init();
        Ext.tip.QuickTipManager.init();
        var toolbar = this;        
       
        BQ.Preferences.get({
            key : 'Toolbar',
            callback : Ext.bind(this.onPreferences, this),
        });
       
        //--------------------------------------------------------------------------------------
        // Services menu
        //--------------------------------------------------------------------------------------   

        this.menu_services = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{
                text: 'Analysis', 
                handler: analysisAction, 
            }, '-', {
                text: 'Import', 
                iconCls: 'icon-import',
                handler: Ext.Function.pass(pageAction, '/import/'),
            }, {
                text: 'Export', 
                iconCls: 'icon-export',            
                handler: Ext.Function.pass(pageAction, '/export/'),
            }, '-', {
                text: 'Statistics', 
                handler: Ext.Function.pass(pageAction, '/stats/'),
            }],       
        };                       

        //--------------------------------------------------------------------------------------
        // User menu
        //--------------------------------------------------------------------------------------   
        
        // Sign in menu item
        var signin = { 
            itemId: 'menu_user_signin', 
            plain: true,
            xtype: 'form',
            id: 'login_form',
            layout: 'form', // uncomment for extjs 4.1
            cls: 'loginmenu',
            standardSubmit: true,
            border: false,
            bodyBorder: false,            
            url: '/auth_service/login_check',
            width: 350,
            fieldDefaults: {
                msgTarget: 'side',
                border: 0,
            },
            items: [{
                xtype: 'hiddenfield',
                name: 'came_from',
                value: document.location,
                allowBlank: true,
            }, {
                xtype: 'textfield',
                fieldLabel: 'User name',
                name: 'login',
                //id: 'loginusername',
                inputId: 'loginusername',
                allowBlank: false,  
                
                fieldSubTpl: [ // note: {id} here is really {inputId}, but {cmpId} is available
                    '<input id="{id}" type="{type}" {inputAttrTpl}',
                        ' size="1"', // allows inputs to fully respect CSS widths across all browsers
                        '<tpl if="name"> name="{name}"</tpl>',
                        '<tpl if="value"> value="{[Ext.util.Format.htmlEncode(values.value)]}"</tpl>',
                        '<tpl if="placeholder"> placeholder="{placeholder}"</tpl>',
                        '<tpl if="maxLength !== undefined"> maxlength="{maxLength}"</tpl>',
                        '<tpl if="readOnly"> readonly="readonly"</tpl>',
                        '<tpl if="disabled"> disabled="disabled"</tpl>',
                        '<tpl if="tabIdx"> tabIndex="{tabIdx}"</tpl>',
                        '<tpl if="fieldStyle"> style="{fieldStyle}"</tpl>',
                    ' class="{fieldCls} {typeCls} {editableCls}" autocomplete="on" autofocus="true" />',
                    {
                        disableFormats: true,
                    }
                ],                                                       
                            
                listeners: {
                    specialkey: function(field, e){
                        if (e.getKey() == e.ENTER) {
                            var form = field.up('form').getForm();
                            form.submit();
                        }
                    }
                },                                                                                                               
            }],
    
            buttons: [{
                xtype: 'button',
                text: 'Sign in',
                formBind: true, //only enabled once the form is valid
                disabled: true, // uncomment for extjs 4.1
                handler: function() {
                    var form = this.up('form').getForm();
                    if (form.isValid())
                        form.submit();
                }
            }],
            
            autoEl: {
                tag: 'form',
            },
            
            listeners: {
                render: function() {
                    this.el.set({ autocomplete: 'on' });
                },
            },                                    
        };      
        
        this.menu_user = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{
                plain: true,
                cls: 'toolbar-menu',
            }, {
                xtype:'tbtext', 
                itemId: 'menu_user_name', 
                text: 'Sign in', 
                indent: true, 
                hidden: true, 
                cls: 'menu-heading', 
            }, {
                text: 'Profile', 
                itemId: 'menu_user_profile', 
                hidden: true, 
                handler: Ext.Function.pass(pageAction, bq.url('/registration/edit_user')),
            }, { 
                xtype:'menuseparator', 
                itemId: 'menu_user_admin_separator', 
                hidden: true, 
            }, {
                text: 'Website admin', 
                itemId: 'menu_user_admin', 
                hidden: true, 
                handler: Ext.Function.pass(pageAction, bq.url('/admin')), 
            }, { 
                text: 'User preferences', 
                itemId: 'menu_user_prefs', 
                handler: this.userPrefs, 
                scope: this, 
                hidden: true, 
            }, { 
                text: 'System preferences', 
                itemId: 'menu_user_admin_prefs', 
                hidden:true, 
                handler: this.systemPrefs, 
                scope: this, 
            }, {
                xtype: 'menuseparator', 
                itemId: 'menu_user_signout_sep', 
                hidden: true, 
            }, {
                text: 'Sign out', 
                itemId: 'menu_user_signout', 
                hidden: true, 
                handler: Ext.Function.pass(pageAction, bq.url('/auth_service/logout_handler')), 
            }, signin, {
                xtype: 'menuseparator', 
                itemId: 'menu_user_register_sep', 
            }, {
                text: 'Register new user', 
                itemId: 'menu_user_register', 
                handler: Ext.Function.pass(pageAction, bq.url(this.preferences.registration || '/registration')), 
            }, {
                text: 'Recover Password', 
                itemId: 'menu_user_recover', 
                handler: Ext.Function.pass(pageAction, bq.url(this.preferences.registration || '/registration/lost_password')), 
            }],
        };

        //--------------------------------------------------------------------------------------
        // Help menu
        //--------------------------------------------------------------------------------------
        var menu_help = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{ 
                xtype:'tbtext', 
                text: '<img src="'+this.images_base_url+'bisque_logo_white_170.png" style="width: 96px; height: 77px; margin: 10px; margin-left: 30px;" />', 
                indent: true, 
            }, {
                text: 'About Bisque', 
                //handler: Ext.Function.pass(htmlAction, [bq.url('/client_service/public/about/about.html'), 'About Bisque'] ), 
                handler: Ext.Function.pass(htmlAction, [bq.url('/client_service/about'), 'About Bisque'] ), 
            }, {
                text: 'Privacy policy', 
                handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/privacypolicy.html')), 
            }, {
                text: 'Terms of use', 
                handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/termsofuse.html') ),
            }, {
                text: 'License', 
                handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/license.html') ),
            }, '-', {
                text: 'Usage statistics', 
                handler: Ext.Function.pass(pageAction, bq.url('/usage/') ),
            }, '-', {
                text: 'Online Help', 
                handler: Ext.Function.pass(urlAction, bq.url('/client_service/help')),
            }, {
                text: 'Bisque project website', 
                handler: Ext.Function.pass(urlAction, 'http://www.bioimage.ucsb.edu/downloads/Bisque%20Database'), 
            }, '-', {
                xtype:'tbtext', text: 'Problems with Bisque?', 
                indent: true, 
                cls: 'menu-heading', 
            }, {
                text: 'Developers website', 
                handler: Ext.Function.pass(urlAction, 'http://biodev.ece.ucsb.edu/projects/bisquik'),
            }, {
                text: 'Submit a bug or suggestion', 
                handler: Ext.Function.pass(urlAction, 'http://biodev.ece.ucsb.edu/projects/bisquik/newticket'),
            }, {
                text: 'Send us e-mail', 
                handler: Ext.Function.pass(urlAction, 'mailto:bisque-dev@biodev.ece.ucsb.edu,bisque-bioimage@googlegroups.com'),
            }],
        };                                        
        
        
        //--------------------------------------------------------------------------------------
        // Toolbar items
        //-------------------------------------------------------------------------------------- 
        var browse_vis = (this.toolbar_opts && this.toolbar_opts.browse===false) ? false : true;        
        this.items = [{ 
                xtype:'tbtext', 
                text: '<img src="'+this.images_base_url+'bisque_logo_100px.png" style="width: 58px; height: 38px; margin-right: 5px; margin-left: 5px;" />',
            }, { 
                xtype:'tbtext', 
                itemId: 'menu_title', 
                text: '<h3><a href="/">'+this.title+'</a></h3>', 
            }, { 
                xtype: 'tbspacer', 
                width: 40, 
            }, {
                xtype : 'button',
                itemId: 'button_services', 
                menu  : this.menu_services,
                iconCls : 'icon-services', 
                text  : 'Services', 
            }, { 
                text: 'Upload', 
                itemId: 'button_upload', 
                iconCls : 'icon-import',
                handler: Ext.Function.pass(pageAction, bq.url('/import/upload')),
                tooltip: '', 
            }, { 
                text: 'Download', 
                itemId: 'button_download', 
                iconCls : 'icon-export', 
                handler: Ext.Function.pass(pageAction, '/export/'),
                tooltip: '', 
            }, {
                itemId: 'menu_images', 
                xtype:'splitbutton', 
                text: 'Images', 
                iconCls : 'icon-browse', 
                hidden: !browse_vis, 
                tooltip: 'Browse images',
                //menu: [{text: 'Menu Button 1'}], 
                handler: function(c) { 
                    var q = '';
                    var m = toolbar.queryById('menu_query');
                    if (m && m.value != toolbar.image_query_text) { q = '?tag_query='+escape(m.value); }
                    document.location = bq.url('/client_service/browser'+q); 
                },
            }, {
                itemId: 'menu_resources', 
                text: 'Resources', 
                iconCls : 'icon-browse', 
                hidden: browse_vis, 
                tooltip: 'Browse resources',
            }, { 
                xtype: 'tbspacer', 
                width: 10, 
                hidden: !browse_vis,
            }, {
                itemId: 'menu_query', 
                xtype:'textfield', 
                flex: 2, 
                name: 'search', 
                value: this.image_query_text, 
                hidden: !browse_vis,
                minWidth: 60,
                tooltip: 'Query for images used Bisque expression',  
                enableKeyEvents: true,
                listeners: {
                    focus: function(c){ if (c.value == toolbar.image_query_text) c.setValue(''); },
                    specialkey: function(f, e) { 
                        if (e.getKey()==e.ENTER && f.value!='' && f.value != toolbar.image_query_text) {
                            document.location = bq.url('/client_service/browser?tag_query='+escape(f.value)); 
                        }                         
                    },
                }
            }, '->', { 
                itemId: 'menu_user', 
                menu: this.menu_user, 
                iconCls: 'icon-user', 
                text: 'Sign in', 
                tooltip: 'Edit your user account', 
                plain: true,
            }, { 
                menu: menu_help, 
                iconCls: 'icon-help', 
                tooltip: 'All information about Bisque',
            }, 
        ];

        //--------------------------------------------------------------------------------------
        // final touches
        //--------------------------------------------------------------------------------------         
        this.addListener( 'resize', this.onResized, this);        
        this.callParent();

        // update user menu based on application events
        Ext.util.Observable.observe(BQ.Application);        
        BQ.Application.on('gotuser', function(u) { 
            this.queryById('menu_user').setText( u.display_name );
            this.queryById('menu_user_name').setText( u.display_name+' - '+u.email_address );
            
            // hide no user menus
            for (var i=0; (p=this.tools_none[i]); i++)
                this.queryById(p).setVisible(false);

            // show user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.queryById(p).setVisible(true);            

            // show admin menus
            if (u.user_name == 'admin')
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.queryById(p).setVisible(true);  

        }, this);

        BQ.Application.on('signedin', function() { 
            //clog('signed in !!!!!');           
        });  
                 
        BQ.Application.on('signedout', function() { 
            // show no user menus
            for (var i=0; (p=this.tools_none[i]); i++)
                this.queryById(p).setVisible(true);

            // hide user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.queryById(p).setVisible(false);            

            // hide user menus
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.queryById(p).setVisible(false);    
                         
        }, this);  
        
        this.fetchResourceTypes();        
    },

    onResized: function() {
        //tools_big_screen: [ 'button_upload', 'button_download' ], 
        var w = this.getWidth();
        //var w = document.width;
        if (w<1024) {
            for (var i=0; id=this.tools_big_screen[i]; ++i)
               this.queryById(id).setVisible(false);
        } else {
            for (var i=0; id=this.tools_big_screen[i]; ++i)
               this.queryById(id).setVisible(true);          
        }
    },

    userPrefs : function() {
        var preferences = Ext.create('BQ.Preferences.Dialog');
    },

    systemPrefs : function() {
        var preferences = Ext.create('BQ.Preferences.Dialog', {prefType:'system'});
    },

    fetchResourceTypes : function() {
        BQFactory.request ({uri : '/data_service/', 
                            cb : callback(this, 'onResourceTypes'),
                            cache : false});             
    }, 

    onResourceTypes : function(resource) {
        var menu = {
            xtype: 'menu',
            cls: 'toolbar-menu',
            plain: true,
            items: [{
                text: 'dataset', 
                handler: Ext.Function.pass(pageAction, '/client_service/browser?resource=/data_service/dataset'),
            }],
        };

        BQApp.resourceTypes = [];
        var r=null;
        for (var i=0; (r=resource.children[i]); i++) {
            BQApp.resourceTypes.push({name:r.name, uri:r.uri});
            if (r.name == 'dataset') continue;
            var name = r.name;
            var uri = r.uri;            
            menu.items.push({
                text: name, 
                handler: Ext.Function.pass(pageAction, '/client_service/browser?resource='+uri),
            });
        }
        
        menu.items.push('-');
        menu.items.push({
            text    : 'Create a new resource', 
            itemId  : 'menu_resource_create', 
            handler : function() {this.createResource(resource);},
            scope   : this, 
            hidden  : !BQApp.hasUser(),
        });
        menu.items.push({
            itemId  : 'menu_resource_template', 
            text    : 'Create resource from template', 
            handler : function() {this.createResourceFromTemplate()},
            scope   : this, 
            hidden  : !BQApp.hasUser()
        });

        menu = Ext.create('Ext.menu.Menu', menu);
        this.queryById('menu_images').menu = menu;
        this.queryById('menu_resources').menu = menu;        
    },
    
    createResourceFromTemplate  :   function(template)
    {
        if (!template)
        {
            BQFactory.request({
                uri     :   '/data_service/template/',
                cb      :   Ext.bind(this.createResourceFromTemplate, this),
                errorcb :   function(error){BQ.ui.error('createResourceFromTemplate: Error occured while fetching list of available templates.'+error.message, 4000)}
                }
            )
            
            return;
        }
        
        var store = Ext.create('Ext.data.Store', {
            fields  :   ['name', 'uri'],
            data    :   template.children
        });
        
        var formPanel = Ext.create('Ext.form.Panel',
        {
            frame           :   true,
            width           :   350,
            defaultType     :   'textfield',
            bodyStyle       :   {
                                    padding         :   '10px'
                                },
            fieldDefaults   :   {
                                    msgTarget       :   'side',
                                    labelWidth      :   100
                                },
            defaults        :   {
                                    anchor          : '100%',
                                    allowBlank      :   false,
                                },
            items           :   [{
                                    xtype           :   'combobox',
                                    name            :   'template',
                                    fieldLabel      :   'Select template',
                                    store           :   store,
                                    displayField    :   'name',
                                    valueField      :   'uri',
                                    editable        :   false
                                }, {
                                    fieldLabel      :   'Name',
                                    name            :   'name'
                                }]
        });
        
           
        var display = Ext.create('Ext.window.Window',
        {
            items       :   formPanel,
            modal       :   true,
            border      :   false,
            title       :   'Create resource from template',
            buttonAlign :   'center',
            buttons     :   [
                                {
                                    text    :   'Create',
                                    scope   :   this,
                                    margin  :   3,
                                    handler :   function(btn)
                                    {
                                        var form = formPanel.getForm();
                                        
                                        if (form.isValid())
                                        {
                                            var input = form.getValues();
                                            BQ.TemplateManager.createResource({name: input.name}, this.onResourceCreated, input.template+'?view=deep');
                                        }
                                    }
                                },
                                {
                                    text    :   'Cancel',
                                    scope   :   this,
                                    margin  :   3,
                                    handler :   function()
                                    {
                                        display.destroy();
                                    }
                                },
                            ]
        }).show();
        
    },
   
    createResource : function(resource) {
        var ignore = { 'mex':null, 'user':null, 'image':null, 'module':null, 'service':null, 'system':null, 'file':null, 'dataset':null, };        
        var mydata = [['dataset']];
        var r=null;
        for (var i=0; (r=resource.children[i]); i++)
            if (!(r.name in ignore))
                mydata.push( [r.name] );   
        delete ignore.dataset;
        
        store_types = Ext.create('Ext.data.ArrayStore', {
            fields: [ {name: 'name',}, ],        
            data: mydata,
        });                
        
        var formpanel = Ext.create('Ext.form.Panel', {
            //url:'save-form.php',
            frame:true,
            bodyStyle:'padding:5px 5px 0',
            width: 350,
            fieldDefaults: {
                msgTarget: 'side',
                labelWidth: 75
            },
            defaultType: 'textfield',
            defaults: {
                anchor: '100%'
            },
    
            items: [{
                xtype : 'combobox',
                fieldLabel: 'Type',
                name: 'type',
                allowBlank: false,
                
                store     : store_types,
                displayField: 'name',
                valueField: 'name',
                queryMode : 'local',
                
                //invalidText: 'This type is not allowed for creation!',
                validator: function(value) { 
                    if (value in ignore) return 'This type is not allowed for creation!';
                    if (/[^\w]/.test(value)) return 'Resource type may only contain word characters: letters, digits, dash and underscore';
                    return true;
                },
            },{
                fieldLabel: 'Name',
                name: 'name',
                allowBlank: false,                
            }],
    
        });
        
        var w = Ext.create('Ext.window.Window', {
            layout : 'fit',
            modal : true,
            border : false,
            title: 'Create new resource',
            buttonAlign: 'center',
            items: formpanel,
            buttons: [{
                text: 'Save',
                scope: this,
                handler: function () {
                    var form = formpanel.getForm();
                    if (form.isValid()) {
                        var v = form.getValues()
                        var resource = BQFactory.make(v.type, undefined, v.name);
                        resource.save_('/data_service/'+v.type, 
                                       callback(this, this.onResourceCreated), 
                                       callback(this, this.onResourceError));
                        formpanel.ownerCt.hide();                    
                    };                    
                }
            }, {
                text: 'Cancel',
                //scope: this,
                handler: function (me) {
                    formpanel.ownerCt.hide();
                }
            }]            
            
        }).show();
    },    

    onResourceCreated: function(resource) {
        document.location = '/client_service/view?resource='+resource.uri;
    },

    onResourceError: function(message) {
        BQ.ui.error('Error creating resource: <br>'+message);
    },
   
    onPreferences: function(pref) {
        this.preferences = pref;  
        
        if (this.preferences.registration === 'disabled')
            this.queryById('menu_user_register').setVisible(false);        
        
        this.queryById('menu_user_register').setHandler( 
            Ext.Function.pass(pageAction, bq.url(this.preferences.registration || '/registration')), 
            this 
        );

        if (this.preferences.title)
            this.queryById('menu_title').setText( '<h3><a href="/">'+this.preferences.title+'</a></h3>' );
        
    },
   
});

