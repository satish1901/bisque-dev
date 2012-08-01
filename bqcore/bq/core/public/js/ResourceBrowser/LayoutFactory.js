Ext.define('Bisque.ResourceBrowser.LayoutFactory', {

    statics : {

        baseClass : 'Bisque.ResourceBrowser.Layout',

        getClass : function(layout) {
            var layoutKey = Ext.Object.getKey(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS, layout);
            var className = Bisque.ResourceBrowser.LayoutFactory.baseClass + '.' + layoutKey;
            
            return className;
        },
        
        getLayout : function(config) {
            var className = this.getClass(config.browser.layoutKey);
            
            if (Ext.ClassManager.get(className))
                return Ext.create(className, config);
            else
            {
                Ext.log({
                    msg     :   Ext.String.format('Unknown layout: {0}', className),
                    level   :   'warn',
                    stack   :   true
                });
                return Ext.create(Bisque.ResourceBrowser.Layout+'.Base', config);
            }
        }
    }
})


// Available layout enumerations
Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS = {
	"Compact"    :   1,
	"Card"       :   2,
	"PStrip"     :   3,
	"PStripBig"  :   3.1,
	"Full"       :   4,
	"List"       :   5,
	"IconList"   :   6,
	'Page'       :   7,
	'Grid'       :   8,

    // for backwards compatibility
    "COMPACT"    :   1,
    "CARD"       :   2,
};

Bisque.ResourceBrowser.LayoutFactory.DEFAULT_LAYOUT = Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact;

/**
 * BaseLayout: Abstract base layout from which all other layouts derive
 * 
 * @param {}
 *            configOpts : Layout related options such as type, size etc.
 */
Ext.define('Bisque.ResourceBrowser.Layout.Base',
{
	extend : 'Ext.panel.Panel',
	
	inheritableStatics : 
	{
	    layoutCSS : null,
        readCSS : function()
        {
            var me = {};
            
            me.layoutCSS = this.layoutCSS;
            me.layoutEl = {
                width   :   null,
                height  :   null
            };
            
            if (me.layoutCSS)
            {
                me.css=Ext.util.CSS.getRule('.'+me.layoutCSS).style;
                
                me.layoutEl.padding=parseInt(me.css['padding']);
                me.layoutEl.margin=parseInt(me.css['margin']);
                me.layoutEl.border=parseInt(me.css['borderWidth']);
                
                me.layoutEl.width=(me.css['width'].indexOf('%')==-1)?parseInt(me.css['width']):me.css['width'];
                me.layoutEl.height=(me.css['height'].indexOf('%')==-1)?parseInt(me.css['height']):me.css['height'];
        
                me.layoutEl.outerWidth=me.layoutEl.width+(me.layoutEl.padding+me.layoutEl.border+2*me.layoutEl.margin);
                me.layoutEl.outerHeight=me.layoutEl.height+(me.layoutEl.padding+me.layoutEl.border+2*me.layoutEl.margin);
            }
            
            return me;
        }
	},
	
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
			//bodyStyle : 'background: #AFA',
			
			resQ : [],
			layoutEl :{},
			border : false,
			autoScroll : true
		});
		
		this.callParent(arguments);
		
        Ext.apply(this, Ext.ClassManager.getClass(this).readCSS());
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
					this.browser.resourceQueue.selectedRes[resCt.resource.uri]=resCt.resource;
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
	
	Init : function(resourceQueue, thisCt) 
	{
		this.resQ = resourceQueue;
		if (!thisCt)
			thisCt=this;
		
		var resCt=[],resCtSub=[], i=0, currentGrp;
		
		// if no results were obtained for a given query, show a default no-results message
		if (this.resQ.length==0)
		{
            this.noResults();
            return;
		}
		
		// Avoid 'if' in for loop for speed
		if (this.showGroups)
		{
			while(i<this.resQ.length)
			{
				currentGrp=this.getGroup(this.resQ[i]);
				
				while(i<this.resQ.length && (this.getGroup(this.resQ[i])==currentGrp))
				{
					this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
					this.resQ[i].addCls(this.layoutCSS);
					resCtSub.push(this.resQ[i]);
					this.relayEvents(this.resQ[i], ['select', 'unselect']);
					
					i++;
				}
				
				resCt.push(new Ext.form.FieldSet({
					items:resCtSub,
					cls:'fieldSet',
	            	margin:'8 0 0 8',
	            	width: (this.getParentSize().width-30),
	            	//autoScroll:true,
        	    	padding:0,
            		title: '<b>Group </b><i>'+Ext.String.ellipsis(currentGrp, 80)+'</i>',
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
				this.resQ[i].addCls(this.layoutCSS);
				
				if (this.browser.resourceQueue.selectedRes[this.resQ[i].resource.uri])
				    this.resQ[i].cls = 'resource-view-selected';
				
				resCt.push(this.resQ[i]);
				this.relayEvents(this.resQ[i], ['select', 'unselect']);
			}
		}
		thisCt.add(resCt);
	},

    noResults : function()
    {
        this.imgNoResults = Ext.create('Ext.Img', 
        {
            width   :   300,
            margin  :   0,
            padding :   0,
            src     :   bq.url('/js/ResourceBrowser/Images/no-results.png'),
        });
        
        var ct = Ext.create('Ext.panel.Panel', 
        {
            border      :   false,
            layout      :   {
                                type : 'vbox',
                                pack : 'center',
                                align: 'center'
                            },
        });
        
        ct.addListener('afterlayout', function(me) {
            me.add(this.imgNoResults)
        }, this, {single:true});

        this.layout = 'fit';
        this.add(ct);     // "add" calls doLayout internally so 'fit' will be applied
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
		var grp='', tagHash={}, value;
		var tagRef=res.resource.tags;
		var value;
		
		for (var i=0;i<tagRef.length;i++)
			tagHash[tagRef[i].name]=tagRef[i].value;
			
		for (var k=0;k<this.showGroups.tags.length;k++)
		{
		    value = tagHash[this.showGroups.tags[k]];
            grp+=this.showGroups.tags[k]+(value?':'+value:'')+', ';
		}
		
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
Ext.define('Bisque.ResourceBrowser.Layout.Compact',
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',	

    inheritableStatics : {
        layoutCSS : 'ImageCompact'
    },

	constructor : function()
	{
		this.callParent(arguments);
		this.layoutEl.imageWidth=150;
		this.layoutEl.imageHeight=150;
	}
});

// Card Layout: Shows resources as cards (thumbnail + tag/value pairs)
Ext.define('Bisque.ResourceBrowser.Layout.Card',
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',

    inheritableStatics : {
        layoutCSS : 'ImageCard'
    },

	constructor : function()
	{
		this.callParent(arguments);
		this.layoutEl.imageWidth=140;
		this.layoutEl.imageHeight=115;
	}
});


// PhotoStrip Layout: Shows resources in a photostrip
Ext.define('Bisque.ResourceBrowser.Layout.PStrip', 
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',
	
    inheritableStatics : {
        layoutCSS : 'ImagePStripSmall'
    },

	constructor : function() 
	{
		Ext.apply(this, {layout:{type:'vbox', align:'stretch'}});
		this.callParent(arguments);

		this.layoutEl.imageWidth=150;
		this.layoutEl.imageHeight=150;
		
		this.setSize(this.getParentSize());
	},

	Init : function(resourceQueue) 
	{
		this.resQ = resourceQueue;

        // if no results were obtained for a given query, show a default no-results message
        if (this.resQ.length==0)
        {
            this.noResults();
            return;
        }
		
		this.proxyPnl = Ext.create('Ext.panel.Panel', {border:false, flex:1, autoScroll:true, layout:{type:'hbox', align:'middle',  pack:'center'}});
		var psPnl = Ext.create('Ext.panel.Panel', {border:false});
		
		// Code for laying out resource containers in this layout container
		for (var i=0; i<this.resQ.length; i++)
		{
			this.resQ[i].setSize({width:this.layoutEl.width, height:this.layoutEl.height});
			this.resQ[i].addCls(this.layoutCSS);
			psPnl.add(this.resQ[i]);
			this.relayEvents(this.resQ[i], ['select', 'unselect']);
		}
		
		this.add([this.proxyPnl, psPnl]);

		if (this.resQ.length)	// Register eventHandler only if resourceQueue is not null
			this.on('afterlayout', function(){this.CreateBigResource(this.resQ[0].resource, this)}, this);
		this.msgBus.on('PStripResourceClick', this.CreateBigResource);
	},
	
	getVisibleElements : function() 
	{
		var ctSize = this.getParentSize();
		var nCol = Math.floor(ctSize.width / this.layoutEl.outerWidth);
		return nCol;
	},
	
	// Private member
	CreateBigResource : function(resource, layoutMgr) 
	{
		var res = Bisque.ResourceFactory.getResource(
		    {
    			resource  :  resource,
    			browser   :  layoutMgr.browser,
    			layoutKey :  Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PStripBig,
    			msgBus    :  layoutMgr.msgBus,
    			bigPanel  :  layoutMgr.proxyPnl 
    		});
		
		layoutMgr.proxyPnl.add(0, res);
		layoutMgr.proxyPnl.animate(
		{
			from: {opacity:0},
			to: {opacity:1},
			easing:'easeIn',
			duration: 180,
		});
		
		if (layoutMgr.proxyPnl.items.length>1)
			layoutMgr.proxyPnl.getComponent(layoutMgr.proxyPnl.items.length-1).destroy();
	},
});

// Full Layout: Shows all the tags assosiated with a resource
Ext.define('Bisque.ResourceBrowser.Layout.Full',
{
	extend : 'Bisque.ResourceBrowser.Layout.Base',

    inheritableStatics : {
        layoutCSS : 'ImageFull'
    },

	constructor : function()
	{
		this.callParent(arguments);

		this.layoutEl.imageHeight=275;
		this.layoutEl.imageWidth=280;
	},
	
	getVisibleElements : function() 
	{
		return 10;
	}
});

// List Layout: Lists the basic information about each resource
Ext.define('Bisque.ResourceBrowser.Layout.List',
{
	extend : 'Bisque.ResourceBrowser.Layout.Full',

    inheritableStatics : {
        layoutCSS : 'ResourceList'
    },

	getVisibleElements : function() 
	{
		return 35;
	}
});

// IconList Layout: Lists the basic information about each resource along with an icon
Ext.define('Bisque.ResourceBrowser.Layout.IconList',
{
    extend : 'Bisque.ResourceBrowser.Layout.List',

    inheritableStatics : {
        layoutCSS : 'ResourceIconList'
    },
    
    constructor : function()
    {
        this.callParent(arguments);

        this.layoutEl.iconHeight=110;
        this.layoutEl.iconWidth=110;
    },
    
    getVisibleElements : function() 
    {
        return 3500;
    }
});

Ext.define('Bisque.ResourceBrowser.Layout.Page',
{
    extend : 'Bisque.ResourceBrowser.Layout.Base',  

    inheritableStatics : {
        layoutCSS : null
    },
});

// Grid layout: Shows resources in a grid
Ext.define('Bisque.ResourceBrowser.Layout.Grid', 
{
    extend : 'Bisque.ResourceBrowser.Layout.Base',
    
    inheritableStatics : {
        layoutCSS : null
    },

    constructor : function() 
    {
        Ext.apply(this, {layout:'fit'});
        this.callParent(arguments);
    },

    Init : function(resourceQueue) 
    {
        this.layoutConfig = this.browser.layoutConfig || {};
        this.add(this.getResourceGrid());
        
        var resource, list=[];
        for (var i=0;i<resourceQueue.length;i++)
            list.push(resourceQueue[i].getFields());
        
        this.resourceStore.loadData(list);
    },
    
    getVisibleElements : function(direction) 
    {
        var ctHeight = this.getParentSize().height-22; // height of grid header = 22px 
        var noEl = Math.floor(ctHeight/21)+1; 
        var tempQ = this.browser.resourceQueue.getTempQ(noEl, direction);
        var elHeight, currentHeight = 0;

        for (var i=0;i<tempQ.length;i++)
        {
            elHeight = tempQ[i].getFields()[6].height;
            if (currentHeight + elHeight > ctHeight)
                break;
            else
                currentHeight += elHeight;
        }
        
        return i;
    },
    
    getResourceGrid : function()
    {
        this.resourceGrid = Ext.create('Ext.grid.Panel', {
            store       :   this.getResourceStore(),
            border      :   0,
            multiSelect :   true,
            listeners : 
            {
                scope: this,
                'itemclick' : function(view, record, item, index)
                {
                    var resource = record.get('raw');
                    this.browser.msgBus.fireEvent('ResourceSingleClick', resource.resource);
                    this.fireEvent('select', resource);
                },
                'itemdblclick' : function(view, record, item, index)
                {
                    var resource = record.get('raw');
                    this.browser.msgBus.fireEvent('ResourceDblClick', resource.resource);
                }
            },
            plugins : new Ext.ux.DataTip({tpl:'<div>{name}:{value}</div>'}),
            
            columns : 
            {
                items : [
                {
                    //maxWidth: 70,
                    //hidden:true,
                    dataIndex: 'icon',
                    menuDisabled : true,
                    sortable : false,
                    align : 'center',
                    maxWidth : this.layoutConfig.colIconWidth || 70,
                    minWidth : 1,
                },
                {
                    text: this.layoutConfig.colNameText || 'Name',
                    dataIndex: 'name',
                    align: 'left',
                    flex : 0.4 
                },
                {
                    text: this.layoutConfig.colValueText || 'Value',
                    dataIndex: 'value',
                    flex : 0.6
                },
                {
                    text: 'Type',
                    dataIndex: 'type',
                    hidden : true,
                },
                {
                    text : this.layoutConfig.colDateText || 'Date created',
                    dataIndex: 'ts',
                    flex : 0.4 
                }],
                defaults : 
                {
                    tdCls: 'align',
                    align: 'center',
                    sortable : true,
                    flex : 0.4
                }
            }
        });
        
        return this.resourceGrid;
    },
    
    getResourceStore : function()
    {
        this.resourceStore = Ext.create('Ext.data.ArrayStore', {
            fields:  ['icon', 'name', 'value', 'type', {name: 'ts', convert: 
            function(value)
            {
                var created = new Date(value), today = new Date();
                var days = Math.round((today-created)/(1000*60*60*24));
                var pattern = (days) ? "n/j/Y" : "g:i A";   

                return Ext.Date.format(created, pattern);
            }}, 'raw']});
        
        return this.resourceStore;
    }
});
