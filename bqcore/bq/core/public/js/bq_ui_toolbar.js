
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
      width: '60%',
      height: '60%',
      buttonAlign: 'center',
      autoScroll: true,
      loader: { url: url, renderer: 'html', autoLoad: true },
      buttons: [ { text: 'Ok', handler: function () { w.close(); } }]
   };
   if (title && typeof title == 'string') c.title = title;
   
   var w = Ext.create('Ext.Window', c);
   w.show();           
}; 


function analysisAction(o, e) {
    //if (typeof BQApp.resource == 'undefined') {
    //    pageAction('/analysis/');
    //    return;
    //}

    var w = Math.min(500, BQApp.main.getComponent('centerEl').body.dom.offsetWidth * 0.8);    
    var h = BQApp.main.getComponent('centerEl').body.dom.offsetHeight * 0.8;
    
    //var resourceBrowser  = new Bisque.ResourceBrowser.Dialog({    
    var resourceBrowser  = new Bisque.ResourceBrowser.Browser({
        layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.IconList,
        wpublic: true,
        selType: 'SINGLE',        
        viewMode: 'ModuleBrowser',
        //width :  w,
        //height : '85%',
        width : '100%',
        height : '100%',
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
    defaults: { scale: 'large', },
    cls: 'toolbar_main',
    
    tools_none: [ 'menu_user_signin', 'menu_user_register'],    
    tools_user: ['menu_user_name', 'menu_user_profile', 'menu_user_signout', ],
    tools_admin: ['menu_user_admin_separator', 'menu_user_admin', 'menu_user_admin_prefs', ],    
    
    config: {
        title: 'Bisque demo',    
        toolbar_opts: { 'browse':true, 'upload':true, 'download':true, 'services':true, 'query':true },
        image_query_text: 'Find images using tags',
    },

    constructor: function(config) {
        config = config || {};
        Ext.apply(config, {}, {images_base_url: bq.url('/images/toolbar/') });
        if (bq.title) config.title = bq.title;
        this.initConfig(config);
        return this.callParent(arguments);        
    },    
   
    initComponent : function() {
        Ext.QuickTips.init();
        Ext.tip.QuickTipManager.init();
        var toolbar = this;        
       
        //--------------------------------------------------------------------------------------
        // Toolbar menus
        //--------------------------------------------------------------------------------------   

        //this.menu_services = Ext.create('Ext.menu.Menu');
        this.menu_services = [];
        this.menu_services.push( {text: 'Analysis', handler: analysisAction } );
        //this.menu_services.push( {text: 'Dataset operations', handler: Ext.Function.pass(pageAction, '/dataset_service/') } );        
        this.menu_services.push( '-' );
        this.menu_services.push( {text: 'Import', handler: Ext.Function.pass(pageAction, '/import/')} );
        this.menu_services.push( {text: 'Export', handler: Ext.Function.pass(pageAction, '/export/')} );
        this.menu_services.push( '-' );
        this.menu_services.push( {text: 'Statistics', handler: Ext.Function.pass(pageAction, '/stats/')} );        
                       
        
        // Sign in | Register
        this.menu_user = Ext.create('Ext.menu.Menu');
        this.menu_user.add( {xtype:'tbtext', itemId: 'menu_user_name', text: 'Sign in', indent: true, hidden: true, cls: 'menu-heading', } );
        
        
        this.menu_user.add( {text: 'Profile', itemId: 'menu_user_profile', hidden: true, 
                                handler: Ext.Function.pass(pageAction, bq.url('/registration/edit_user'))} );
        
        this.menu_user.add( { xtype:'menuseparator', itemId: 'menu_user_admin_separator', hidden: true } );
        this.menu_user.add( {text: 'Website admin', itemId: 'menu_user_admin', hidden: true, 
                                handler: Ext.Function.pass(pageAction, bq.url('/admin'))} );        
        
        this.menu_user.add( { text: 'User preferences', itemId: 'menu_user_prefs', 
                              handler: this.userPrefs, scope: this } );    

        this.menu_user.add( { text: 'System preferences', itemId: 'menu_user_admin_prefs', hidden:true, 
                              handler: this.systemPrefs, scope: this } );    

        this.menu_user.add( {text: 'Register new user', itemId: 'menu_user_register', 
                                handler: Ext.Function.pass(pageAction, bq.url('/registration'))} );
        
        this.menu_user.add( '-' );           
        this.menu_user.add( {text: 'Sign out', itemId: 'menu_user_signout', hidden: true, 
                                handler: Ext.Function.pass(pageAction, bq.url('/auth_service/logout_handler'))} );
                                 
        this.menu_user.add( {text: 'Sign in', itemId: 'menu_user_signin', 
                                handler: Ext.Function.pass(pageAction, bq.url('/auth_service/login?came_from='+encodeURIComponent(window.location)))} );
                         
    
        
        var menu_help = [];
        menu_help.push( { xtype:'tbtext', html: '<img src="'+this.images_base_url+'bisque_logo_white_170.png" style="width: 96px; height: 77px; margin: 10px; margin-left: 30px;" />', indent: true } );
        menu_help.push( {text: 'About Bisque', 
                            handler: Ext.Function.pass(htmlAction, [bq.url('/client_service/public/about/about.html'), 'About Bisque'] ) } );    
        menu_help.push( {text: 'Privacy policy', 
                            handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/privacypolicy.html')) } );
        menu_help.push( {text: 'Terms of use', 
                            handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/termsofuse.html') )} );    
        menu_help.push( {text: 'License', 
                            handler: Ext.Function.pass(htmlAction, bq.url('/client_service/public/about/license.html') )} );  

        menu_help.push( '-' );  
        menu_help.push( {text: 'Usage statistics', 
                            handler: Ext.Function.pass(pageAction, bq.url('/usage/') )} );  
        
        menu_help.push( '-' );                
        menu_help.push( {text: 'Online Help', 
                            handler: Ext.Function.pass(urlAction, bq.url('/client_service/help'))} );
      
        menu_help.push( {text: 'Bisque project website', 
                         handler: Ext.Function.pass(urlAction, 'http://www.bioimage.ucsb.edu/downloads/Bisque%20Database') } );   
                             
        menu_help.push( '-' ); 
        menu_help.push( {xtype:'tbtext', text: 'Problems with Bisque?', indent: true, cls: 'menu-heading', } );
        menu_help.push( {text: 'Developers website', 
                         handler: Ext.Function.pass(urlAction, 'http://biodev.ece.ucsb.edu/projects/bisquik')} );
        menu_help.push( {text: 'Submit a bug or suggestion', 
                         handler: Ext.Function.pass(urlAction, 'http://biodev.ece.ucsb.edu/projects/bisquik/newticket')} );
        menu_help.push( {text: 'Send us e-mail', 
                         handler: Ext.Function.pass(urlAction, 'mailto:bisque-dev@biodev.ece.ucsb.edu')} );                                        
        
        
        //--------------------------------------------------------------------------------------
        // Toolbar items
        //-------------------------------------------------------------------------------------- 
        if (!this.items) this.items = [];

        this.items.push({ xtype:'tbtext', html: '<img src="'+this.images_base_url+'bisque_logo_100px.png" style="width: 58px; height: 38px; margin-right: 5px; margin-left: 5px;" />' });
        this.items.push({ xtype:'tbtext', html: '<h3><a href="/">'+this.title+'</a></h3>' });
        this.items.push({ xtype: 'tbspacer', width: 40 });        
        
        this.items.push({ menu: this.menu_services, icon: this.images_base_url+'services.png', text: 'Services', tooltip: '' });
        this.items.push('-');        
        this.items.push({ text: 'Upload', icon: this.images_base_url+'upload.png',
                 handler: Ext.Function.pass(pageAction, bq.url('/import/upload')),
                 tooltip: '' });            
        this.items.push('-');
        this.items.push({ text: 'Download', icon: this.images_base_url+'download.png', 
                 handler: Ext.Function.pass(pageAction, '/export/'),
                 tooltip: '' });
        this.items.push('-');            


        var browse_vis = (this.toolbar_opts && this.toolbar_opts.browse===false) ? false : true;
        this.items.push({itemId: 'menu_images', 
                         xtype:'splitbutton', 
                         text: 'Images', 
                         icon: this.images_base_url+'browse.png', 
                         hidden: !browse_vis, 
                         tooltip: 'Browse images',
                         //menu: [{text: 'Menu Button 1'}], 
                         handler: function(c) { 
                              var q = '';
                              var m = toolbar.child('#menu_query');
                              if (m && m.value != toolbar.image_query_text) { q = '?tag_query='+escape(m.value); }
                              document.location = bq.url('/client_service/browser'+q); 
                         },
              });
        this.items.push({itemId: 'menu_resources', 
                         text: 'Resources', 
                         icon: this.images_base_url+'browse.png', 
                         hidden: browse_vis, 
                         tooltip: 'Browse resources',
              });

               
        this.items.push({ xtype: 'tbspacer', width: 10, hidden: !browse_vis });    
        this.items.push({itemId: 'menu_query', xtype:'textfield', flex: 2, name: 'search', value: this.image_query_text, hidden: !browse_vis,
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
               });

            
        this.items.push('->');
        this.items.push({ itemId: 'menu_user', menu: this.menu_user, icon: this.images_base_url+'user.png', text: 'Sign in', tooltip: 'Edit your user account' });
        this.items.push('-');            
        this.items.push({ menu: menu_help, icon: this.images_base_url+'help.png', tooltip: 'All information about Bisque'  }); 
        
        this.callParent();
        
        
        // update user menu based on application events
        Ext.util.Observable.observe(BQ.Application);        
        BQ.Application.on('gotuser', function(u) { 
            this.child('#menu_user').setText( u.display_name );
            this.menu_user.child('#menu_user_name').setText( u.display_name+' - '+u.email_address );
            
            // hide no user menus
            for (var i=0; (p=this.tools_none[i]); i++)
                this.menu_user.child('#'+p).setVisible(false);

            // show user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.menu_user.child('#'+p).setVisible(true);            

            // show user menus
            if (u.user_name == 'admin')
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.menu_user.child('#'+p).setVisible(true);  
        }, this);

        BQ.Application.on('signedin', function() { 
            //clog('signed in !!!!!');           
        });  
                 
        BQ.Application.on('signedout', function() { 
            // show no user menus
            for (var i=0; (p=this.tools_none[i]); i++)
                this.menu_user.child('#'+p).setVisible(true);

            // hide user menus
            for (var i=0; (p=this.tools_user[i]); i++)
                this.menu_user.child('#'+p).setVisible(false);            

            // hide user menus
            for (var i=0; (p=this.tools_admin[i]); i++)
                this.menu_user.child('#'+p).setVisible(false);              
        }, this);  
        
        this.fetchResourceTypes();        
    },

    // private
    onDestroy : function() {
        this.callParent();
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
        var menu = Ext.create('Ext.menu.Menu');
        var r=null;
        for (var i=0; (r=resource.children[i]); i++) {
            var name = r.name;
            var uri = r.uri;            
            menu.add( {text: name, handler: Ext.Function.pass(pageAction, '/client_service/browser?resource='+uri)} );
        }
        menu.add( '-' );
        menu.add( {text: 'Create a new resource', 
                   handler: function() {this.createResource(resource);},
                   scope: this, });
        
        
        this.child('#menu_images').menu = menu;
        this.child('#menu_resources').menu = menu;        
    }, 
   
    createResource : function(resource) {
        var ignore = { 'mex':null, 'user':null, 'image':null, 'module':null, 'service':null, 'system':null, };        
        var mydata = [];
        var r=null;
        for (var i=0; (r=resource.children[i]); i++)
            if (!(r.name in ignore))
                mydata.push( [r.name] );       
        
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
                
                invalidText: 'This type is not allowed for creation!',
                validator: function(value) { return !(value in ignore) },
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
                        
                        // dima: temporary hack to fix the dataset memebers tag problem
                        if (v.type == 'dataset')
                             resource.addtag ({name: 'members'});
                        
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
   
});

