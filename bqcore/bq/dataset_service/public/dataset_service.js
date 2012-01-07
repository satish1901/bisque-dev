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
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip', 'BQ.dataset.Operations'],

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
            //border: 1,
            
            layout: Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.LIST,
            title: 'Datasets',
            tagOrder: '"@ts":desc',          
            dataset: '/data_service/dataset',
            selType: 'SINGLE',          
            wpublic: false,
            viewMode: 'ViewerOnly',
            listeners: { 'Select': function(me, resource) { 
                          this.btn_modify.setDisabled(false);
                          this.dataset = resource;
                          this.preview.setTitle('Dataset preview for "'+resource.name+'"');
                          this.preview.loadData({baseURL:resource});
                          if (this.selected_operation) 
                              this.onChanged(this.selected_operation);                          
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

        this.operations = {};
        var op_items = [];
        for (i in BQ.dataset.Operations) {
            var o = Ext.create(BQ.dataset.Operations[i], {
                listeners: { 'changed': this.onChanged,
                             scope: this },       
            });
            this.operations[i] = o;
            op_items.push(o);
        }
        this.operationPanel = Ext.create('Ext.panel.Panel', {
            flex: 1,
            title : 'Operations',            
            border: 1,
            region:'center',
            layout: 'accordion',                            
            defaults: { border: 0, }, 
            items: op_items,           
        }); 

        
        // header toolbar's elements
        this.btn_modify = Ext.create('Ext.button.Button', {
            text: 'Modify', 
            disabled: true,
            //iconCls: 'upload', 
            scale: 'large', 
            //tooltip: 'Start the upload of all queued files',
            handler: Ext.Function.bind( this.run, this ),
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
        this.doComponentLayout(null, null, true); // some rendering bug in showing options
    },
   
    onChanged: function(o) {
        this.selected_operation = o;
        var txt = o.getStatus();
        txt += this.dataset ? ' in dataset "<b>'+this.dataset.name+'</b>"':'';
        this.btn_modify.setText( txt );
    },    

    run: function(o) {
        //this.btn_modify.setText( txt ); 
        if (this.selected_operation && this.dataset) {
            this.btn_modify.setDisabled(true);
            var d = this.selected_operation.getArguments();
            var operation = this.selected_operation.getName();
            d.duri = this.dataset.uri;
            var l = [];
            for (var i in d)
                l.push( i+'='+d[i] );
            var uri = '/dataset_service/' + operation + '?' + l.join('&');            
            BQFactory.request ({uri : uri, 
                                cb : callback(this, 'onDone'),
                                errorcb: callback(this, 'onError'),
                                cache : false});           
        }
    },    

    onDone: function(response) {
        this.btn_modify.setDisabled(false);
        BQ.ui.notification('done');        
    },    

    onError: function(response) {
        this.btn_modify.setDisabled(false);
        BQ.ui.error('error');
    },  

});

