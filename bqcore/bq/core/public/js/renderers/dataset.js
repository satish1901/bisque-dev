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
            title : 'Tags',
        });
    
        this.operations = Ext.create('BQ.dataset.Panel', {
            title : 'Operations',     
            dataset : this.resource,       
            listeners: { 'done': this.onDone, 'error': this.onError, scope: this },               
        }); 
    
        this.tabber = Ext.create('Ext.tab.Panel', {
            region : 'east',
            activeTab : 0,
            border : false,
            bodyBorder : 0,
            collapsible : true,
            split : true,
            width : 400,
            plain : true,

            items : [this.tagger, this.operations]
        });

        this.preview = Ext.create('Bisque.ResourceBrowser.Browser', {
            region:'center', 
            flex: 1,
            dataset: this.resource?this.resource:'None',
            
            title : this.resource.name?'Preview for "'+this.resource.name+'"':'Preview',
            tagOrder: '"@ts":desc',          
            selType: 'SINGLE',          
            //wpublic: false,
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
            dock: 'top',
            defaults: { scale: 'medium'  },
            allowBlank: false,
            //cls: 'tools', 
            layout: {
                overflowHandler: 'Menu'
            },            
            items: [{ text: ' ', },
                    /*{ text: 'Share', //icon: this.images_base_url+'upload.png',
                        //handler: Ext.Function.pass(pageAction, bq.url('/import/upload')),
                        tooltip: '' }, 
                    { text: 'Delete', //icon: this.images_base_url+'upload.png',
                        //handler: Ext.Function.pass(pageAction, bq.url('/import/upload')),
                        tooltip: '' },*/
                    '->', 
                    { xtype:'tbtext', html: 'Dataset: <b>'+this.resource.name+'</b>', cls: 'heading', }
                  ],
        }];    
        
        
        this.items = [this.preview, this.tabber];        
        this.callParent();
    },
 
    onDone: function(panel) {
        BQ.ui.notification('Done<br><br>'+panel.getStatus());        
    },    

    onError: function(panel) {
        BQ.ui.error('Error<br><br>'+panel.getStatus());
    },  
    
});

