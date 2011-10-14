Bisque.ResourceBrowser.LayoutFactory = function(configOpts) {
	try {
		switch (configOpts.browser.layoutKey) {
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT :
				return new Bisque.ResourceBrowser.LayoutFactory.CompactLayout(configOpts);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.CARD :
				return new Bisque.ResourceBrowser.LayoutFactory.CardLayout(configOpts);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP :
				return new Bisque.ResourceBrowser.LayoutFactory.PhotoStripLayout(configOpts);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.FULL :
				return new Bisque.ResourceBrowser.LayoutFactory.FullLayout(configOpts);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.LIST :
				return new Bisque.ResourceBrowser.LayoutFactory.ListLayout(configOpts);
				break;
            case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.ICON_LIST :
                return new Bisque.ResourceBrowser.LayoutFactory.IconListLayout(configOpts);
                break;
			default :
				throw new Error('LayoutFactory: Unrecognized layout key - '
						+ configOpts.layoutKey);
		}
	} catch (error) {
		console.log(error.message);
	}
}

// Available layout enumerations
Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS = {
	"COMPACT" : 1,
	"CARD" : 2,
	"PSTRIP" : 3,
	"PSTRIP_BIG" : 3.1,
	"FULL" : 4,
	"LIST" : 5,
	"ICON_LIST" : 6
};

Bisque.ResourceBrowser.LayoutFactory.DEFAULT_LAYOUT = Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT;

/**
 * BaseLayout: Abstract base layout from which all other layouts derive
 * 
 * @param {}
 *            configOpts : Layout related options such as type, size etc.
 */
Ext.define('Bisque.ResourceBrowser.LayoutFactory.BaseLayout',
{
	extend : 'Ext.panel.Panel',

	getLayoutCSS : Ext.emptyFn,
	
	constructor : function(configOpts)
	{
		Ext.apply(this, 
		{
			browser : configOpts.browser,
			direction : configOpts.direction,
			
			key : configOpts.browser.layoutKey,
			parentCt : configOpts.browser.centerPanel,
			msgBus : configOpts.browser.msgBus,
			showGroups : configOpts.browser.showGroups,
			
			resQ : [],
			layoutEl :{},
			
			border : false,
			autoScroll : true
		});
		
		Bisque.ResourceBrowser.LayoutFactory.BaseLayout.superclass.constructor.apply(this, arguments);

		this.readCSSSettings();
		this.manageEvents();
	},
	
	manageEvents : function()
	{
		//this.on('afterrender', function(){this.animateIn(this.direction)}, this);

		if (this.browser.selType=='SINGLE')
			this.on(
			{
				'select' : function(resCt)
				{
					if (Ext.Object.getSize(this.browser.resourceQueue.selectedRes)!=0)
						this.browser.resourceQueue.selectedRes.toggleSelect(false);
					this.browser.resourceQueue.selectedRes=resCt;
					
					this.msgBus.fireEvent('ResSelectionChange', [resCt.resource.uri]);
				},
				'unselect' : function(resCt)
				{
					this.browser.resourceQueue.selectedRes={};
					this.msgBus.fireEvent('ResSelectionChange', []);
				},
				scope : this
			});
		else
			this.on(
			{
				'select' : function(resCt)
				{
					this.browser.resourceQueue.selectedRes[resCt.resource.uri]=1;
					var selRes=this.browser.resourceQueue.selectedRes;
					var keys=Ext.Object.getKeys(selRes); var selection = [];
		
					for (var i=0;i<keys.length;i++)
						selection.push(keys[i]);
					
					this.msgBus.fireEvent('ResSelectionChange', selection);
				},
				
				'unselect' : function(resCt)
				{
					delete this.browser.resourceQueue.selectedRes[resCt.resource.uri];
					var selRes=this.browser.resourceQueue.selectedRes;
					var keys=Ext.Object.getKeys(selRes); var selection = [];
		
					for (var i=0;i<keys.length;i++)
						selection.push(selRes[i]);
						
					this.msgBus.fireEvent('ResSelectionChange', selection);
				},
				
				scope : this
			});
	},
	
	readCSSSettings : function()
	{
		this.css=Ext.util.CSS.getRule('.'+this.getLayoutCSS()).style;
		
		this.layoutEl.padding=parseInt(this.css['padding']);
		this.layoutEl.margin=parseInt(this.css['margin']);
		this.layoutEl.border=parseInt(this.css['borderWidth']);
		
		this.layoutEl.width=(this.css['width'].indexOf('%')==-1)?parseInt(this.css['width']):this.css['width'];
		this.layoutEl.height=(this.css['height'].indexOf('%')==-1)?parseInt(this.css['height']):this.css['height'];

		this.layoutEl.outerWidth=this.layoutEl.width+(this.layoutEl.padding+this.layoutEl.border+2*this.layoutEl.margin);
		this.layoutEl.outerHeight=this.layoutEl.height+(this.layoutEl.padding+this.layoutEl.border+2*this.layoutEl.margin);
	},
	
	Init : function(resourceQueue, thisCt) 
	{
		this.resQ = resourceQueue;
		if (!thisCt)
			thisCt=this;
		
		var resCt=[],resCtSub=[], i=0, currentGrp;
		
		// Avoid 'if' in for loop for speed
		if (this.showGroups)
		{
			while(i<this.resQ.length)
			{
				currentGrp=this.getGroup(this.resQ[i]);
				
				while(i<this.resQ.length && (this.getGroup(this.resQ[i])==currentGrp))
				{
					this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
					this.resQ[i].addCls(this.getLayoutCSS());
					resCtSub.push(this.resQ[i]);
					this.relayEvents(this.resQ[i], ['select', 'unselect']);
					
					i++;
				}
				
				resCt.push(new Ext.form.FieldSet({
					items:resCtSub,
					cls:'fieldSet',
	            	margin:'8 0 0 8',
	            	width: (this.getParentSize().width*0.97)-15,
	            	//autoScroll:true,
        	    	padding:0,
            		title: '<b>Group </b><i>'+currentGrp+'</i>',
            		collapsible: true,
            		collapsed: false
				}));
				resCtSub=[];
			}
		}
		else
		{
			// Code for laying out resource containers in this layout container
			for (var i=0; i<this.resQ.length; i++)
			{
				this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
				this.resQ[i].addCls(this.getLayoutCSS());
				resCt.push(this.resQ[i]);
				this.relayEvents(this.resQ[i], ['select', 'unselect']);
			}
		}
		thisCt.add(resCt);
	},
	
	getParentSize : function() 
	{
		return this.browser.centerPanel.getSize();
	},
	
	getVisibleElements : function(direction)
	{
		var ctSize = this.getParentSize();
		
		var nRow = Math.floor(ctSize.height / this.layoutEl.outerHeight);
		var nCol = Math.floor(ctSize.width / this.layoutEl.outerWidth);

		if (this.showGroups)
			return this.getNoGroupedElements(this.browser.resourceQueue.getTempQ(nRow * nCol, direction));
		else
			return nRow * nCol;
	},
	
	getNoGroupedElements : function(resData) 
	{
		var currentGrp, i=0, noGrp=1, grpObj={};
		grpObj[noGrp]=0;
		
		while(i<resData.length && !this.containerFull(grpObj))
		{
			currentGrp=this.getGroup(resData[i]);
			
			while(i<resData.length && !this.containerFull(grpObj) && (this.getGroup(resData[i])==currentGrp))
			{
				grpObj[noGrp]=grpObj[noGrp]+1;
				i++;
			}
			
			if (this.containerFull(grpObj))
			{
				i--;
				break;
			}
			
			noGrp++;
			grpObj[noGrp]=0;
		}
		
		return i;
	},
	
	getGroup : function(res)
	{
		var grp='', tagHash={};
		var tagRef=res.resource.tags;
		
		for (var i=0;i<tagRef.length;i++)
			tagHash[tagRef[i].name]=tagRef[i].value;
			
		for (var k=0;k<this.showGroups.tags.length;k++)
			grp+=this.showGroups.tags[k]+':'+tagHash[this.showGroups.tags[k]]+', ';
		
		return grp.substring(0, grp.length-2);
	},
	
	containerFull : function(grpObj)
	{
		var barHeight=42;
		var ctSize = this.getParentSize();

		var bodyHeight=ctSize.height-(Ext.Object.getSize(grpObj)*barHeight);
		
		var nRow = Math.floor(bodyHeight / this.layoutEl.outerHeight);
		var nCol = Math.floor(ctSize.width / this.layoutEl.outerWidth);

		var grpRow=0;
		for (var i in grpObj)
			grpRow+=Math.ceil(grpObj[i]/nCol);

		return (grpRow>nRow);
	},
	
	/*
	animateIn : function(direction)
	{
    	var left=(direction=='Left'?-1:1)*this.ownerCt.getWidth();
    	var from=(direction=='none'?{left:0}:{left:left});

		this.animate(
		{
			from: from,
			to: {left:0},
			easing:'ease',
			duration: this.animInDuration || 0,
		});
	},
	
	Destroy : function(direction) 
	{
		if (this.rendered)
		{
	    	var left=(direction=='Left'?1:-1)*this.getWidth();
	    	
			this.animate(
			{
				to: {opacity:0, left:left},
				easing: 'easeOut',
				duration: this.animDestroyDuration || 0,
				listeners:
				{
					'afteranimate':function(){this.removeAll(true);this.destroy();},
					scope:this
				},
			});
		}
	},
	*/
});

// Compact Layout: Shows resources as thumbnails
Ext.define('Bisque.ResourceBrowser.LayoutFactory.CompactLayout',
{
	extend : 'Bisque.ResourceBrowser.LayoutFactory.BaseLayout',	
	constructor : function()
	{
		Bisque.ResourceBrowser.LayoutFactory.CompactLayout.superclass.constructor.call(this, arguments[0]);
		this.layoutEl.imageWidth=150;
		this.layoutEl.imageHeight=150;
	},
	
	getLayoutCSS : function()
	{
		return 'ImageCompact';
	}
});

// Card Layout: Shows resources as cards (thumbnail + tag/value pairs)
Ext.define('Bisque.ResourceBrowser.LayoutFactory.CardLayout',
{
	extend : 'Bisque.ResourceBrowser.LayoutFactory.BaseLayout',
	constructor : function()
	{
		Bisque.ResourceBrowser.LayoutFactory.CardLayout.superclass.constructor.call(this, arguments[0]);
		this.layoutEl.imageWidth=140;
		this.layoutEl.imageHeight=115;
	},
	
	getLayoutCSS : function()
	{
		return 'ImageCard';
	}
});


// PhotoStrip Layout: Shows resources in a photostrip
Ext.define('Bisque.ResourceBrowser.LayoutFactory.PhotoStripLayout', 
{
	extend : 'Bisque.ResourceBrowser.LayoutFactory.BaseLayout',
	
	constructor : function() 
	{
		Ext.apply(this, {layout:{type:'vbox', align:'stretch'}});
		Bisque.ResourceBrowser.LayoutFactory.PhotoStripLayout.superclass.constructor.call(this, arguments[0]);

		this.layoutEl.imageWidth=150;
		this.layoutEl.imageHeight=150;
		
		this.setSize(this.getParentSize());
	},

	Init : function(resourceQueue) 
	{
		this.resQ = resourceQueue;
		
		this.proxyPnl = new Ext.Panel({border:false, flex:1, autoScroll:true, layout:{type:'hbox', align:'middle',  pack:'center'}});
		var psPnl = new Ext.Panel({border:false});
		
		// Code for laying out resource containers in this layout container
		for (var i=0; i<this.resQ.length; i++)
		{
			this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
			this.resQ[i].addCls(this.getLayoutCSS());
			psPnl.add(this.resQ[i]);
			this.relayEvents(this.resQ[i], ['select', 'unselect']);
		}
		
		this.add([this.proxyPnl, psPnl]);

		if (this.resQ.length)	// Register eventHandler only if resourceQueue is not null
			this.on('afterrender', function(){this.CreateBigResource(this.resQ[0].resource, this)}, this);
		this.msgBus.on('PStripResourceClick', this.CreateBigResource);
	},
	
	getVisibleElements : function() 
	{
		var ctSize = this.getParentSize();
		var nCol = Math.floor(ctSize.width / this.layoutEl.outerWidth);
		return nCol;
	},
	
	getLayoutCSS : function()
	{
		return 'ImagePStripSmall';
	},

	// Private member
	CreateBigResource : function(resource, layoutMgr) 
	{
		var res = Bisque.ResourceBrowser.ResourceFactory({
			resource : resource,
			browser : layoutMgr.browser,
			layoutKey : Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP_BIG,
			msgBus : layoutMgr.msgBus,
			bigPanel : layoutMgr.proxyPnl 
		});
		
		layoutMgr.proxyPnl.add(0, res);
		layoutMgr.proxyPnl.animate(
		{
			from: {opacity:0},
			to: {opacity:1},
			easing:'easeIn',
			duration: 180,
		});
		
		res.setLoading({msg:''});
		
		if (layoutMgr.proxyPnl.items.length>1)
			layoutMgr.proxyPnl.getComponent(layoutMgr.proxyPnl.items.length-1).destroy();
	},
});

// Full Layout: Shows all the tags assosiated with a resource
Ext.define('Bisque.ResourceBrowser.LayoutFactory.FullLayout',
{
	extend : 'Bisque.ResourceBrowser.LayoutFactory.BaseLayout',

	constructor : function()
	{
		Bisque.ResourceBrowser.LayoutFactory.FullLayout.superclass.constructor.call(this, arguments[0]);
		this.layoutEl.imageHeight=275;
		this.layoutEl.imageWidth=280;
		
		var size=this.getParentSize();
		this.setSize({height:size.height, width:size.width+31});
	},
	
	Init : function(resourceQueue) 
	{
		var proxyPnl=new Ext.panel.Panel({border:false, autoScroll:true});

		Bisque.ResourceBrowser.LayoutFactory.FullLayout.superclass.Init.call(this, arguments[0], proxyPnl);
		
		this.add(proxyPnl);
	},
	
	getParentSize : function() 
	{
		var size = this.browser.centerPanel.getSize();
		size.width=size.width-31;
		
		return size;
	},
	
	getLayoutCSS : function()
	{
		return 'ImageFull';
	},

	getVisibleElements : function() 
	{
		return 10;
	}
});

// List Layout: Lists the basic information about each resource
Ext.define('Bisque.ResourceBrowser.LayoutFactory.ListLayout',
{
	extend : 'Bisque.ResourceBrowser.LayoutFactory.BaseLayout',

	constructor : function()
	{
		Bisque.ResourceBrowser.LayoutFactory.FullLayout.superclass.constructor.call(this, arguments[0]);
		//this.layoutEl.iconHeight=72;
		//this.layoutEl.iconWidth=72;
		
		var size=this.getParentSize();
		this.setSize({height:size.height, width:size.width});
	},
	
	Init : function(resourceQueue) 
	{
		var proxyPnl=new Ext.panel.Panel({border:false, autoScroll:true});

		Bisque.ResourceBrowser.LayoutFactory.FullLayout.superclass.Init.call(this, arguments[0], proxyPnl);
		
		this.add(proxyPnl);
	},
	
	getLayoutCSS : function()
	{
		return 'ResourceList';
	},

	getVisibleElements : function() 
	{
		return 35;
	}
});

// IconList Layout: Lists the basic information about each resource along with an icon
Ext.define('Bisque.ResourceBrowser.LayoutFactory.IconListLayout',
{
    extend : 'Bisque.ResourceBrowser.LayoutFactory.ListLayout',

    constructor : function()
    {
        this.callParent(arguments);

        this.layoutEl.iconHeight=110;
        this.layoutEl.iconWidth=110;
    },
    
    getLayoutCSS : function()
    {
        return 'ResourceIconList';
    },
    
    getVisibleElements : function() 
    {
        return 3500;
    }
});

