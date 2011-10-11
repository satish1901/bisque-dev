
Ext.require([
    'Ext.data.*',
    'Ext.grid.*'
]);

/*
<codec index="0" name="JPEG">
    <tag name="support" value="reading"/>
    <tag name="support" value="writing"/>
    <tag name="support" value="reading metadata"/>
    <tag name="extensions" value="jpg|jpeg|jpe|jif|jfif"/>
</codec>
*/

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

function getWriting(v, record) {
    var expression = "tag[@value='writing']/@value";    
    var r = xpath(record.raw, expression);
    return r=='writing'?'yes':'';
}

function getMetadata(v, record) {
    var expression = "tag[@value='reading metadata']/@value";    
    var r = xpath(record.raw, expression);
    return r=='reading metadata'?'yes':'';
}

function getExtensions(v, record) {
    var expression = "tag[@name='extensions']/@value";    
    var r = xpath(record.raw, expression);
    return r.replace(/\|/gi, ', ');
}

function getSource(v, record) {
    var r = xpath(record.raw.parentNode, '@name');
    var v = xpath(record.raw.parentNode, '@version');
    return r.replace(/DIMIN|CODEC/gi, '') + ' ' + v;
}

Ext.define('BQ.is.Formats', {
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],
    layout: 'fit', 

    initComponent : function() {
       
        Ext.define('Formats', {
            extend : 'Ext.data.Model',
            fields : [ {name: 'Name', mapping: '@name' },
                       {name: 'Reading', convert: getReading },
                       {name: 'Writing', convert: getWriting },
                       {name: 'Metadata', convert: getMetadata },                       
                       {name: 'Extensions', convert: getExtensions },
                       {name: 'Source', convert: getSource },],
                       
            proxy : { 
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                type: 'ajax',
                url : '/image_service/formats',
                reader : {
                    type :  'xml',
                    root :  'response',
                    record: 'codec', 
                }
            },                       
            
        });
    
        this.store = new Ext.data.Store( {
            model : 'Formats', 
            autoLoad : true,
            autoSync : false,
        });       
        
        var grid = Ext.create('Ext.grid.Panel', {
            store: this.store,
            border: 0,
            columns: [
                {text: "Name", flex: 2, dataIndex: 'Name', sortable: true},
                {text: "Reading", width: 60, dataIndex: 'Reading', sortable: true},
                {text: "Writing", width: 60, dataIndex: 'Writing', sortable: true},
                //{text: "Metadata", width: 100, dataIndex: 'Metadata', sortable: true},                
                {text: "Extensions", flex: 1, dataIndex: 'Extensions', sortable: true},
                {text: "Source", width: 100, dataIndex: 'Source', sortable: true},                
            ],
            viewConfig: {
                stripeRows: true,
                forceFit: true                
            },        
        });        
       
       
        //--------------------------------------------------------------------------------------
        // items
        //-------------------------------------------------------------------------------------- 
        this.items = this.items || [];
        this.items.push(grid);
        
        this.callParent();
       
    },
   
});


