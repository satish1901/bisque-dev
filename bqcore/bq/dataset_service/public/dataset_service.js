/*******************************************************************************

  BQ.dataset.Service  - 

  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/

//--------------------------------------------------------------------------------------
// BQ.dataset.Service
// 
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.dataset.Service', {
    alias: 'widget.datasetservice',    
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    border: 0,
    autoScroll: true,
    layout: 'fit',     
    heading: 'Dataset service',
    defaults: { border: 0, },

    constructor: function(config) {
        //this.addEvents({
        //    'fileerror'      : true,
        //});
        this.callParent(arguments);
        return this;
    },

    initComponent : function() {

        this.browser = Ext.create('Bisque.ResourceBrowser.Browser', {
            region:'west',                
            collapsible: false,
            width: 350,
            
            layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.LIST,
            title: 'Datasets',
            tagOrder: '"@ts":desc',          
            dataset: '/data_service/dataset',
            selType: 'SINGLE',          
            wpublic: false,
            viewMode: 'ViewerOnly',
            listeners: { 'Select': function(me, resource) { 
                          //window.open(bq.url('/client_service/view?resource='+resource.uri)); 
                       }, 
                       scope: this },    
        });        

        this.preview = Ext.create('Bisque.ResourceBrowser.Browser', {
            region:'north', 
            flex: 1,
            
            title : 'Dataset content preview',
            tagOrder: '"@ts":desc',          
            selType: 'SINGLE',          
            wpublic: false,
            viewMode: 'ViewerLayouts',
            listeners: { 'Select': function(me, resource) { 
                          //window.open(bq.url('/client_service/view?resource='+resource.uri)); 
                       }, 
                       scope: this },         
        }); 

        this.operationPanel = Ext.create('Ext.panel.Panel', {
            flex: 1,
            title : 'Operations',            
            border: 0,
            region:'center',
            layout: 'accordion',                            
            defaults: { border: 0, },            
        }); 

        // header toolbar's elements
        this.btn_modify = Ext.create('Ext.button.Button', {
            text: 'Modify', 
            disabled: false,
            //iconCls: 'upload', 
            scale: 'large', 
            cls: 'x-btn-default-large',
            tooltip: 'Start the upload of all queued files',
            handler: Ext.Function.bind( this.upload, this ),
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
            items: [ this.btn_modify, ]            
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
    },

});

