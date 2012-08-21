/*******************************************************************************

  BQ.selectors - selectors of inputs for module runs
  
  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/

/*******************************************************************************
Resource templated configs:

*******************************************************************************/

Ext.define('BQ.data.reader.Bisque', {
    extend: 'Ext.data.reader.Xml',
    alternateClassName: 'BQ.data.BisqueReader',
    alias : 'reader.bisque',
    
    //root :  'resource',
    //record: 'image',
    root :  '/',
    record: '/*:not(value or vertex or template)',    

    constructor: function(config) {
        this.callParent(arguments);
        BQFactory.request({ uri: this.url+'?view=count', 
                            cb: callback(this, 'onTotal'), });        
        return this;
    },
    
    onTotal: function(r) {
        if (r.tags.length<1) return;
        if (r.tags[0].name != 'count') return;
        this.total_count = r.tags[0].value;
    },

    readRecords: function(doc) {
        var r = this.callParent([doc]);
        r.total = this.total_count || 10;
        return r;
    },
    
}); 

Ext.define('Resources', {
    extend : 'Ext.data.Model',
    fields : [ {name: 'Name', mapping: '@name' },
               {name: 'Value', mapping: '@value' },
               {name: 'Type', mapping: '@type' },
               //{name: 'Metadata', convert: getMetadata },                       
             ],
});


/*
function xpath(node, expression) {
    var xpe = new XPathEvaluator();
    var nsResolver = xpe.createNSResolver(node.ownerDocument == null ? node.documentElement : node.ownerDocument.documentElement);    
    var result = xpe.evaluate( expression, node, nsResolver, XPathResult.STRING_TYPE, null );     
    return result.stringValue;
}

function getReading(v, record) {
    var expression = "tag[@value='reading']/@value";    
    var r = xpath(record.raw, expression);
    return r=='reading'?'yes':'';
}

function getSource(v, record) {
    var r = xpath(record.raw.parentNode, '@name');
    var v = xpath(record.raw.parentNode, '@version');
    return r.replace(/DIMIN|CODEC/gi, '') + ' ' + v;
}
*/

Ext.define('BQ.grid.Panel', {
    alias: 'bq.gridpanel',    
    extend: 'Ext.panel.Panel',
    requires: ['Ext.button.Button', 'Ext.tree.*', 'Ext.data.*'],
    
    layout: 'fit',
    height: 300,

    pageSize: 100,          // number of records to fetch on every request
    trailingBufferZone: 20, // Keep records buffered in memory behind scroll
    leadingBufferZone: 20,  // Keep records buffered in memory ahead of scroll

    initComponent : function() {
    
        var url = this.url || '/data_service/image';
        this.reader = Ext.create('BQ.data.reader.Bisque', {
            url: url,
        });
    
        this.store = new Ext.data.Store( {
            model : 'Resources', 
            autoLoad : true,
            //autoSync : false,
            remoteSort: true,
            buffered: true,
            pageSize: this.pageSize,
            
            proxy : { 
                type: 'rest',
                url : this.reader.url+'?view=full',
                appendId: true,
                limitParam : 'limit',
                pageParam: undefined,
                startParam: 'offset',
                noCache: false,
                reader : this.reader,
            },             
            
        }); 
        
        this.grid = Ext.create('Ext.grid.Panel', {
            store: this.store,
            loadMask: true,
            border: 0,
            //verticalScrollerType: 'paginggridscroller',
            //invalidateScrollerOnRefresh: false,
            disableSelection: false,
            //autoLoad: true, 
            columns: [
                {text: "Name",  flex: 2, dataIndex: 'Name',  sortable: true},
                {text: "Value", flex: 2, dataIndex: 'Value', sortable: true},
                {text: "Type",  flex: 1, dataIndex: 'Type',  sortable: true},
                //{text: "Reading", width: 60, dataIndex: 'Reading', sortable: true},
                //{text: "Writing", width: 60, dataIndex: 'Writing', sortable: true},
                //{text: "Metadata", width: 100, dataIndex: 'Metadata', sortable: true},                
                //{text: "Extensions", flex: 1, dataIndex: 'Extensions', sortable: true},
                //{text: "Source", width: 100, dataIndex: 'Source', sortable: true},                
            ],
            viewConfig: {
                stripeRows: true,
                forceFit: true                
            },    
            verticalScroller: {
                trailingBufferZone: this.trailingBufferZone,  // Keep records buffered in memory behind scroll
                leadingBufferZone: this.leadingBufferZone,   // Keep records buffered in memory ahead of scroll
            },                    
        });           
        this.items = [this.grid];
        this.callParent();
    },


});
