/*******************************************************************************

  BQ.renderers.dataset  - 

  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/

Ext.define('BQ.renderers.dataset', {
    alias: 'widget.renderersdataset',    
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip', 'BQ.dataset.Panel'],

    border: 0,
    autoScroll: true,
    layout : 'border',   
    heading: 'Dataset',
    defaults: { border: 0, },

    initComponent : function() {
    
        this.tagger = Ext.create('Bisque.ResourceTagger', {
            resource : this.resource,
            title : 'Annotations',
        });
    
        this.operations = Ext.create('BQ.dataset.Panel', {
            title : 'Operations',     
            dataset : this.resource,       
            listeners: { 'done': this.onDone, 'error': this.onError, scope: this },               
        });
        
        this.mexs = new Bisque.ResourceBrowser.Browser({
            'layout' : 5,
            'title' : 'Analysis',
            'viewMode' : 'MexBrowser',
            'dataset' : '/data_service/mex',
            'tagQuery' : '"'+this.resource.uri+'"&view=deep',
            'wpublic' : true,
            mexLoaded : false,
            listeners : {
                'browserLoad' : function(me, resQ) {
                    me.mexLoaded = true;
                },
                'Select' : function(me, resource) {
                    window.open(bq.url('/module_service/'+resource.name+'/?mex='+resource.uri));
                },
                scope:this
            },
        });         
    
        this.tabber = Ext.create('Ext.tab.Panel', {
            region : 'east',
            activeTab : 0,
            border : false,
            bodyBorder : 0,
            collapsible : true,
            split : true,
            flex: 1,
            plain : true,
            title : 'Annotate and modify',
            //collapsed: true,

            items : [this.tagger, this.mexs, this.operations]
        });

        this.preview = Ext.create('Bisque.ResourceBrowser.Browser', {
            region:'center', 
            flex: 3,
            dataset: this.resource?this.resource:'None',
            
            title : this.resource.name?'Preview for "'+this.resource.name+'"':'Preview',
            tagOrder: '"@ts":desc',          
            //selType: 'SINGLE',          
            //wpublic: false,
            showOrganizer : true,
            viewMode: 'ViewerLayouts',
            listeners: { 'Select': function(me, resource) { 
                          window.open(bq.url('/client_service/view?resource='+resource.uri)); 
                       }, 
                       scope: this },         
        }); 

        //--------------------------------------------------------------------------------------
        // toolbars
        //--------------------------------------------------------------------------------------

        this.dockedItems = [{
            xtype: 'toolbar',
            itemId: 'toolbar',
            dock: 'top',
            defaults: { scale: 'medium',  },
            allowBlank: false,
            //cls: 'tools', 
            layout: {
                overflowHandler: 'Menu'
            },            
            items: [{ itemId: 'menu_images', xtype:'splitbutton', text: 'Add images', iconCls: 'icon_plus',
                      scope: this, tooltip: 'Add resources into the dataset', //cls: 'x-btn-default-medium', 
                      handler: function() { this.browseResources('image'); }, },
                    { itemId: 'menu_delete_selected', text: 'Remove selected', tooltip: 'Remove selected resource from the dataset, keeps the resource untouched',
                      scope: this, iconCls: 'icon_minus', //cls: 'x-btn-default-medium',
                      handler: this.removeSelectedResources, },                        
                    { itemId: 'menu_delete', text: 'Delete', //icon: this.images_base_url+'upload.png',
                        handler: this.remove, scope: this, iconCls: 'icon_x', 
                        tooltip: 'Delete current dataset, keeps all the elements untouched' },
                    '->', 
                    //{ xtype:'tbtext', html: 'Dataset: <b>'+this.resource.name+'</b>', cls: 'heading', }
                    
                    { itemId: 'menu_rename', 
                      text: 'Dataset: <b>'+this.resource.name+'</b>', cls: 'heading',
                      scope: this, tooltip: 'Rename the dataset', //cls: 'x-btn-default-medium', 
                      handler: this.askRename, },
                  ],
        }];    
        
        
        this.items = [this.preview, this.tabber];        
        this.callParent();

        this.fetchResourceTypes();
        if (!BQSession.current_session)
            BQFactory.request( {uri: '/auth_service/session', cb: callback(this, 'onsession') }); 
        else
            this.onsession(BQSession.current_session);            
    },
 
    onsession: function (session) {
        this.user_uri = session && session.user_uri?session.user_uri:null;
        if (this.user_uri) return;
        var tb = this.child('#toolbar');
        tb.child('#menu_images').setDisabled(true);   
        tb.child('#menu_delete_selected').setDisabled(true);
        tb.child('#menu_delete').setDisabled(true);                
    },
 
    onDone: function(panel) {
        BQ.ui.notification('Done<br><br>'+panel.getStatus());        
    },    

    onError: function(panel) {
        BQ.ui.error('Error<br><br>'+panel.getStatus());
    },  

    browseResources: function(resource_type) {
        if (!this.checkAllowWrites(true)) return;        
        var resourceDialog = Ext.create('Bisque.ResourceBrowser.Dialog', {
            'height'  : '85%',
            'width'   :  '85%',
            //wpublic   : 'true',
            dataset   : '/data_service/'+resource_type,
            listeners : {
                'Select' : this.addResources,
                scope: this
            },
        });    
    }, 
    
    fetchResourceTypes : function() {
        BQFactory.request ({uri : '/data_service/', 
                            cb : callback(this, 'onResourceTypes'),
                            cache : false});             
    }, 

    onResourceTypes : function(resource) {
        var ignore = { 'user':null, 'module':null, 'service':null, 'system':null, }; 
        var menu = Ext.create('Ext.menu.Menu');
        var r=null;
        for (var i=0; (r=resource.children[i]); i++) {
            if (r.name in ignore) continue;
            this.addResourceTypeMenu(menu, r.name);
        }
        this.child('#toolbar').child('#menu_images').menu = menu;
    },     

    addResourceTypeMenu : function(menu, name) {
        menu.add( {text: 'Add '+name, 
                   handler: function() { this.browseResources(name); },
                   scope: this,
                  } );
    },     
    
    changedOk : function() {
        this.setLoading(false);
        // reload the browser
        var uri = { offset: 0, };
        this.preview.msgBus.fireEvent('Browser_ReloadData', uri);
        this.child('#toolbar').child('#menu_rename').setText('Dataset: <b>'+this.resource.name+'</b>'); 
        this.preview.setTitle(this.resource.name?'Preview for "'+this.resource.name+'"':'Preview');    
    },     

    changedError : function(message) {
        this.setLoading(false);
        BQ.ui.error('Error creating resource: <br>'+message);
    },  

    checkAllowWrites : function(warn) {
        var session = BQSession.current_session;
        this.user_uri = session && session.user_uri?session.user_uri:null;
        // dima: this is an incomplete solution, will return true for every logged-in user, even without write ACL!
        if (warn && !this.user_uri)
            BQ.ui.warning('You don\'t have enough access to modify this resource!');
        return this.user_uri;      
    }, 

    addResources : function(browser, sel) {
        if (!this.checkAllowWrites(true)) return;        
        this.setLoading('Appending resources');
        if (!(sel instanceof Array)) {
            sel = [sel];
        }

        var members = [];
        var r = null;
        for (var i=0; (r=sel[i]); i++) {
            var v = new Value('object', r.uri );
            members.push(v);
        }
        // append elements to current values
        members = this.resource.getMembers().values.concat(members);
        this.resource.setMembers(members);
        this.resource.save_(undefined, 
                            callback(this, 'changedOk'),
                            callback(this, 'changedError'));
    },    

    removeSelectedResources : function() {
        if (!this.checkAllowWrites(true)) return;        
        var d = this.preview.resourceQueue.selectedRes;
        var l = Ext.Object.getKeys(d);
        var members = this.resource.getMembers().values;
        if (!members || l.length<1) return;
        
        this.setLoading('Removing selected resources');
        var uri = null;
        var m = null;        
        for (var i=0; (uri=l[i]); i++) {
            for (var j=0; (m=members[j]); j++) {
                if (m.value == uri) {
                   members.splice(j, 1);
                   break;
                }
            }
        }
        
        // dima: this does not work  backend error!!!!!!!!!!!!!
        this.resource.setMembers(members);
        this.resource.save_(undefined, 
                            callback(this, 'changedOk'),
                            callback(this, 'changedError'));
    },  
    
    remove: function() {   
        if (!this.checkAllowWrites(true)) return;
        this.resource.delete_();
        var myMask = new Ext.LoadMask(BQApp.getCenterComponent(), {
            msg: 'Dataset removed...',
            msgCls: 'final', 
        });
        myMask.show();
    },

    askRename: function() {   
        Ext.Msg.prompt('Dataset name', 'Please enter a new name:', function(btn, text){
            if (btn == 'ok'){
                this.rename(text);
            }
        }, this, false, this.resource.name);
    },

    rename: function(name) {   
        if (!this.checkAllowWrites(true)) return;
        this.setLoading('Renaming...');        
        this.resource.name = name;
        this.resource.save_(undefined, 
                            callback(this, 'changedOk'),
                            callback(this, 'changedError'));
    },
    
});

