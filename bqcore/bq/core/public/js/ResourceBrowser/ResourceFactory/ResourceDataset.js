/* Abstract Dataset resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.ResourceBrowser.ResourceFactory.DatasetResource',
{
    extend:'Bisque.ResourceBrowser.ResourceFactory.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.DatasetResourceCompact',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.DatasetResource',
    
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
			cls:'lblModuleOwner'
		})

		var date=Ext.Date.parse(this.resource.ts, 'Y-m-d H:i:s.u');
		
		var datasetDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			padding:'8 8 8 5',
			style:'color:#444;font-size:11px'
		})

		this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.DatasetResourceList',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.DatasetResourceCompact',
    
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
			cls:'lblModuleOwner'
		})

		var date=Ext.Date.parse(this.resource.ts, 'Y-m-d H:i:s.u');
		
		var datasetDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			padding:'0 0 0 8',
			style:'color:#444;font-size:11px'
		})

		this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});


