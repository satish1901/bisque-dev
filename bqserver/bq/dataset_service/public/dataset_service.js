/*******************************************************************************

  BQ.dataset.Service  - 

  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/

Ext.define('BQ.dataset.Service', {
    alias: 'widget.datasetservice',    
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip', 'BQ.dataset.Panel'],

    border: 0,
    autoScroll: true,
    layout: 'fit',     
    heading: 'Dataset service',
    defaults: { border: 0, },

    initComponent : function() {
        
        this.browser = Ext.create('Bisque.ResourceBrowser.Browser', {
            region:'west',                
            collapsible: false,
            width: 350,
            
            layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.List,
            title: 'Datasets',
            tagOrder: '"@ts":desc',          
            dataset: '/data_service/dataset',
            selType: 'SINGLE',          
            wpublic: false,
            viewMode: 'ViewerOnly',
            listeners: { 'Select': function(me, resource) { 
                          this.operationPanel.setDataset(resource);
                          this.preview.setTitle('Preview for "'+resource.name+'"');
                          this.preview.loadData({baseURL:resource});
                         }, 
                       scope: this },    
        });        

        this.preview = Ext.create('Bisque.ResourceBrowser.Browser', {
            //region:'north',
            region:'west', 
            width: 500,
            flex: 1,
            //border: 1,
            dataset: 'None',
            
            title : 'Dataset preview',
            tagOrder: '"@ts":desc',          
            selType: 'SINGLE',          
            wpublic: false,
            viewMode: 'ViewerLayouts',
            listeners: { 'Select': function(me, resource) { 
                          window.open(bq.url('/client_service/view?resource='+resource.uri)); 
                       }, 
                       scope: this },         
        }); 

        this.operationPanel = Ext.create('BQ.dataset.Panel', {
            flex: 1,
            border: 1,
            region:'center',
            listeners: { 'done': this.onDone, 'error': this.onError, scope: this },               
        }); 


        //--------------------------------------------------------------------------------------
        // toolbars
        //-------------------------------------------------------------------------------------- 

        this.dockedItems = [{
            xtype: 'toolbar',
            dock: 'top',
            defaults: { scale: 'large'  },
            allowBlank: false,
            cls: 'tools', 
            layout: {
                overflowHandler: 'Menu'
            },            
            items: [{ xtype:'tbtext', html: '<h1>'+this.heading+'</h1>', }],
        },{
            xtype: 'toolbar',
            dock: 'bottom',
            //ui: 'footer',
            cls: 'footer',   
            defaults: { scale: 'large', cls: 'x-btn-default-large', },  
            //items: [ this.btn_modify, ]            
        }];    
       
        //--------------------------------------------------------------------------------------
        // items
        //-------------------------------------------------------------------------------------- 
        this.items = [{
            xtype: 'panel',
            layout: 'border',
            defaults: { split: true, border: 0, },
            items: [ 
                this.browser, {
                    xtype: 'panel',
                    region:'center',
                    flex: 1,
                    layout: 'border',
                    defaults: { split: true, border: 0, },
                    items: [ 
                        this.preview,
                        this.operationPanel,
                    ],
                },
            ],
        }];        
        
        this.callParent();
        this.doComponentLayout(null, null, true); // some rendering bug in showing options
    },

    onDone: function(panel) {
        BQ.ui.notification('Done<br><br>'+panel.getStatus());        
    },    

    onError: function(panel) {
        BQ.ui.error('Error<br><br>'+panel.getStatus());
    },  

});

