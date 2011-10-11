Ext.define('Bisque.ResourceBrowser.viewStateManager',
{
	//	ResourceBrowser view-state 
	cBar : 
	{
		cbar : false,
		
		searchBar : false,
		
		btnTS : false,
		
		btnLayoutThumb : false,
		btnLayoutCard : false,
		btnLayoutPStrip : false,
		btnLayoutFull : false,

		btnLayoutLeft : false,
		btnLayoutRight : false,
		
		btnGear : false,
		btnOrganizer : false,
		btnDataset : false,
		btnLink : false,
	},
	
	constructor : function(mode)
	{
		switch(mode)
		{
			case 'MexBrowser':
			case 'ViewerOnly':
			case 'DatasetBrowser':
			{
				this.cBar.searchBar=true;
				
				this.cBar.btnLayoutThumb=true;
				this.cBar.btnLayoutCard=true;
				this.cBar.btnLayoutPStrip=true;
				this.cBar.btnLayoutFull=true;
				
				this.cBar.btnGear=true;
				break;
			}
			case 'ViewerLayouts':
			{
                this.cBar.searchBar=true;
                this.cBar.btnGear=true;
			    break;
			}
			case 'ModuleBrowser':
			{
                this.cBar.cbar=true;
                break;
			}
		}
		
		return this;
	}
})
