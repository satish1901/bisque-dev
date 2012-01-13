/* Abstract Dataset resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Dataset',
{
    extend:'Bisque.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Dataset.Compact',
{
    extend : 'Bisque.Resource.Dataset',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'vbox',
            	align:'stretch'	
            }
        });
		this.callParent(arguments);
        this.addCls('compact');				
	},
    
    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	// -1 = Loading

	        BQFactory.request(
	        {
	        	uri:this.resource.owner,
	        	cb:Ext.bind(this.loadResource, this),
	        	errorcb:Ext.emptyFn
	        });
		}
    },
    
	loadResource : function(ownerInfo)
    {
		this.setData('owner', ownerInfo.display_name);
		this.setData('fetched', 1);	// 1 = Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var datasetName=new Ext.form.Label({
			text:' '+this.resource.name+' ',
			padding:'8 8 8 5',
			cls:'lblModuleName',
		})
		
		var datasetOwner=new Ext.form.Label({
			text:this.getData('owner'),
			padding:5,
			cls:'lblModuleOwner',
		})

		var date=Ext.Date.parse(this.resource.ts, 'Y-m-d H:i:s.u');
		
		var datasetDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			//padding:'8 8 8 5',
			//style:'color:#444;font-size:11px'
			flex: 1,				
			cls: 'lblModuleDate',			
		})

		this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Dataset.List',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
   	constructor : function()
	{
		this.callParent(arguments);
		
        Ext.apply(this,
        {
            layout:
            {
            	type:'hbox',
            	align:'middle'	
            }
        });
        this.addCls('list');        
	},
	
    updateContainer : function()
    {
		var datasetName=new Ext.form.Label({
			text:' '+this.resource.name+' ',
			padding:'0 8 0 8',
			cls:'lblModuleName',
		})
		
		var datasetOwner=new Ext.form.Label({
			text:this.getData('owner'),
			padding:'0 0 0 4',
			cls:'lblModuleOwner',
		})

		var date=Ext.Date.parse(this.resource.ts, 'Y-m-d H:i:s.u');
		
		var datasetDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			cls: 'lblModuleDate',	
			flex: 1,		
			//padding:'0 0 0 8',
            //style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
		})

		this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});

// Page view for a dataset
Ext.define('Bisque.Resource.Dataset.Page',
{
    extend : 'Bisque.Resource',
    
    constructor : function()
    {
        Ext.apply(this, {
            layout:'fit',
        });
        
        this.callParent(arguments);
    },
    
    updateContainer : function()
    {
        this.setLoading(false);
    
        var renderer = Ext.create('BQ.renderers.dataset', {
            resource: this.resource,
        });
        
        this.add(renderer);
    }
});
