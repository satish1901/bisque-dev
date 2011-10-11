Ext.define('Bisque.DatasetBrowser.Dialog', 
{
	extend : 'Ext.window.Window',
	
    constructor : function(config)
    {
        var bodySz=Ext.getBody().getViewSize();
        var height=parseInt((config.height.indexOf("%")==-1)?config.height:(bodySz.height*parseInt(config.height)/100));
        var width=parseInt((config.width.indexOf("%")==-1)?config.width:(bodySz.width*parseInt(config.width)/100));

        Ext.apply(this,
        {
            layout : 'fit',
            title : config.title || 'Select a dataset...',
            modal : true,
            border : false,
            height : height,
            width : width,
            items : new Bisque.DatasetBrowser.Browser(config)
        }, config);

        this.callParent([arguments]);
        this.relayEvents(this.getComponent(0), ['DatasetDestroy']);
        
        this.on('DatasetDestroy', this.destroy, this);
        this.show();
    },
});

Ext.define('Bisque.DatasetBrowser.Browser', 
{
	extend : 'Bisque.ResourceBrowser.Browser',
	
    constructor : function(config)
    {
        Ext.apply(config,
        {
			viewMode: 'DatasetBrowser',
        });

		Ext.apply(this,
		{
			selectedDataset: null,
	      	bbar :
	        {
	        	xtype: 'toolbar',
				layout:
				{
					type:'hbox',
					align:'middle',
					pack: 'center'
				},
				padding: 12,
				items:
				[
	        		{
	        			xtype:'buttongroup',
	        			items:
		       			[{
		        			text: 'Select',
		        			iconCls : 'icon-select',
		        			scale: 'medium',
		        			textAlign: 'left',
		        			width: 75,
		        			handler: this.btnSelect,
		        			scope: this
	        			}]
	        		},
	        		{
	        			xtype:'buttongroup',
	        			items:
	        			[{
		        			text: 'Cancel',
		        			iconCls : 'icon-cancel',
		        			textAlign: 'left',
		        			scale: 'medium',
		        			width: 75,
		        			handler: this.btnCancel,
		        			scope: this
	        			}]
	        		}
	        	]
	        }
		});

		this.callParent(arguments);
		this.commandBar.btnDatasetClick();
		this.manageEvents();
    },
    
    manageEvents : function()
    {
		// Listen to Dataset Change
		this.msgBus.on(
		{
			'DatasetSelected' : function(dataset)
			{
				this.selectedDataset=dataset;
				if (this.ownerCt)
					this.ownerCt.setTitle('Viewing dataset : '+dataset.name);
			},
			'DatasetUnselected' : function()
			{
        		this.selectedDataset=null;
				if (this.ownerCt)
					this.ownerCt.setTitle('Select a dataset...');
        	},
        	scope: this
        });
    },
    
    btnSelect : function()
    {
    	if (this.selectedDataset)
    	{
    		this.fireEvent('DatasetSelect', this, this.selectedDataset);
    		this.fireEvent('DatasetDestroy');
    	}
    	else
    		alert('No dataset selected!');
    },
    
    btnCancel : function()
    {
    	this.fireEvent('DatasetDestroy');
    },
});
