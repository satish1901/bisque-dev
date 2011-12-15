
Ext.define('Bisque.ResourceBrowser.CommandBar',
{
	extend : 'Ext.toolbar.Toolbar',

	constructor : function(configOpts)
	{
		this.slider = new Bisque.Misc.Slider();

		this.viewMgr = configOpts.browser.viewMgr;

		Ext.apply(this,
		{
			browser : configOpts.browser,
			taqQuery : configOpts.browser.browserParams.tagQuery,
			
			msgBus : configOpts.browser.msgBus,
			westPanel : configOpts.browser.westPanel,
			organizerCt : configOpts.browser.organizerCt,
			datasetCt : configOpts.browser.datasetCt,
			hidden : configOpts.browser.viewMgr.cBar.cbar,
			
			layout :
			{
				type:'hbox',
				align:'middle'
			},
			items :
			[
				{
					xtype : 'tbspacer',
					width : 6
				},
				{
					xtype : 'textfield',
					tooltip : 'Enter a tag query here',
					itemId : 'searchBar',
					flex:7,
					scale:'large',
					height:25,
					boxMinWidth : 100,
					hidden : this.viewMgr.cBar.searchBar,
					value : configOpts.tagQuery,
					listeners :
					{
						specialkey :
						{
							fn : function(field, e)
							{
								if (e.getKey() == e.ENTER)
									this.btnSearch()
							},
	
							scope : this
						}
					}
				},
				{
					icon : bq.url('/js/ResourceBrowser/Images/search.png'),
					hidden : this.viewMgr.cBar.searchBar,
					tooltip : 'Search',
					scale : 'large',
					handler : this.btnSearch,
					scope : this
				},
				{
					xtype : 'tbseparator',
					hidden : this.viewMgr.cBar.searchBar
				},
				{
					itemId : 'btnThumb',
					icon : bq.url('/js/ResourceBrowser/Images/thumb.png'),
					hidden : this.viewMgr.cBar.btnLayoutThumb,
					tooltip : 'Thumbnail layout',
					toggleGroup : 'btnLayout',
					scale : 'large',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},
				{
					itemId : 'btnCard',
					icon : bq.url('/js/ResourceBrowser/Images/card.png'),
					hidden : this.viewMgr.cBar.btnLayoutCard,
					tooltip : 'Card layout',
					scale : 'large',
					toggleGroup : 'btnLayout',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},
				{
					itemId : 'btnPStrip',
					icon : bq.url('/js/ResourceBrowser/Images/pstrip.png'),
					hidden : this.viewMgr.cBar.btnLayoutPStrip,
					tooltip : 'Photo strip layout',
					scale : 'large',
					toggleGroup : 'btnLayout',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},
				{
					itemId : 'btnFull',
					icon : bq.url('/js/ResourceBrowser/Images/full.png'),
					hidden : this.viewMgr.cBar.btnLayoutFull,
					tooltip : 'Full layout',
					scale : 'large',
					toggleGroup : 'btnLayout',
					handler : this.btnLayoutClick,
					padding : '3 0 3 0',
					scope : this
				},'->',
				{
					itemId : 'btnTS',
					icon : bq.url('/js/ResourceBrowser/Images/desc.png'),
					tooltip : 'Sort data ascending by timestamp (current: descending)',
					hidden : this.viewMgr.cBar.btnTS,
					sortState : 'DESC',
					scale : 'large',
					handler : this.btnTS,
					scope : this
				},
				'-',
				{
					tooltip : 'Load more data',
					itemId : 'btnLeft',
					icon : bq.url('/js/ResourceBrowser/Images/left.png'),
					hidden : this.viewMgr.cBar.btnLeft,
					scale : 'large',
					padding : '5 1 5 5',
					handler : function(me)
					{
						me.stopAnimation();
						me.el.frame("#B0CEF7");
						this.browser.resourceQueue.loadPrev(this.browser.layoutMgr.getVisibleElements('left'/*direction:left*/));
						this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
					},
					scope : this
				},
				{
					tooltip : 'Load more data',
					itemId :  'btnRight',
					icon : bq.url('/js/ResourceBrowser/Images/right.png'),
					hidden : this.viewMgr.cBar.btnRight,
					scale : 'large',
					padding : '5 5 5 1',
					handler : function(me)
					{
						me.stopAnimation();
						me.el.frame("#B0CEF7");
						this.browser.resourceQueue.loadNext();
						this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
					},
	
					scope : this
				},
					
				this.slider,
				
				{
					xtype : 'tbseparator',
					hidden : this.viewMgr.cBar.btnGear
				},
				{
					icon : bq.url('/js/ResourceBrowser/Images/gear.png'),
					hidden : this.viewMgr.cBar.btnGear,
					itemId : 'btnGear',
					scale : 'large',
					tooltip : 'Options',
					menu :
					{
						items : 
						[{
							text : 'Include public resources',
							itemId : 'btnWpublic',
							checked : false,
					 		listeners:
					 		{
							 	checkchange:
						 		{
						 			fn : function(chkbox, value)
				 					{
				 						var uri={offset:0};
						 				configOpts.browser.browserParams.wpublic = value;
						 				configOpts.browser.msgBus.fireEvent('Browser_ReloadData', uri);
						 			},
						 			scope : this
					 			}
					 		}
				 		},'-',
						{
							text : 'Organize',
                            itemId : 'btnOrganize',
							icon : bq.url('/js/ResourceBrowser/Images/organize.png'),
							hidden : this.viewMgr.cBar.btnOrganizer,
				 			handler : this.btnOrganizerClick,
				 			scope : this
				 		},
				 		{
				 			text : 'Datasets',
				 			icon : bq.url('/js/ResourceBrowser/Images/datasets.png'),
							hidden : this.viewMgr.cBar.btnDataset,
				 			handler : this.btnDatasetClick,
				 			scope : this
				 		},
						{
							text : 'Link',
							icon : bq.url('/js/ResourceBrowser/Images/link.png'),
							hidden : this.viewMgr.cBar.btnLink,
							handler : function()
							{
				 				var val = configOpts.browser.resourceQueue.uriStateToString(configOpts.browser.getURIFromState());
				 				
				 				Ext.Msg.show
				 				({
				 					title : 'Link to this view',
				 					msg : 'Bisque URL:',
				 					modal : true,
				 					prompt : true,
				 					width : 500,
				 					buttons : Ext.MessageBox.OK,
				 					icon : Ext.MessageBox.INFO,
				 					value : val
				 				});
				 			}
				 		}]
					}
				},
				{
					xtype : 'tbspacer',
					flex : 0.2,
					maxWidth : 20
				}
			]
		});

		Bisque.ResourceBrowser.CommandBar.superclass.constructor.apply(this, arguments);
		
		this.manageEvents();
	},
	
	manageEvents : function()
	{
		this.msgBus.on('SearchBar_Query', function(query)
		{
			this.getComponent('searchBar').setValue(decodeURIComponent(query));
		}, this);
		
		this.mon(this, 'afterlayout', this.toggleLayoutBtn, this);
		
        this.slider.on('buttonClick', Ext.Function.createThrottled(function(newOffset)
        {
            var oldOffset = this.browser.resourceQueue.rqOffset + this.browser.resourceQueue.dbOffset.left;
            var diff = newOffset - oldOffset;

            if(diff > 0)
            {
                this.browser.resourceQueue.loadNext(diff);
                this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
            }
            else if(diff < 0)
            {
                this.browser.resourceQueue.loadPrev(-1 * diff);
                this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
            }
        }, 400, this), this);

	},

	btnTS : function(btn)
	{
        var tagOrder = cleanTagOrder(this.browser.browserState.tag_order) || '';
        
		function cleanTagOrder(tagOrder)
		{
			var ind=tagOrder.lastIndexOf('"@ts":desc')
			if (ind!=-1)
				return tagOrder.slice(0, ind);

			ind=tagOrder.lastIndexOf('"@ts":asc')
			if (ind!=-1)
				return tagOrder.slice(0, ind);
			
			return tagOrder;
		}
		
		(tagOrder.length!=0)?((tagOrder[tagOrder.length-1]!=',')?tagOrder+=',':""):"";
		
		if (btn.sortState=='ASC')
		{
			btn.setIcon(bq.url('/js/ResourceBrowser/Images/desc.png'));
			btn.sortState='DESC';
			btn.setTooltip('Sort data ascending by timestamp (current: descending)');
			tagOrder+='"@ts":desc';
		}
		else
		{
			btn.setIcon(bq.url('/js/ResourceBrowser/Images/asc.png'));
			btn.sortState='ASC';
			btn.setTooltip('Sort data descending by timestamp (current: ascending)');
			tagOrder+='"@ts":asc';
		}
		
        this.msgBus.fireEvent('Browser_ReloadData',
        {
            offset:0,
            tag_order:tagOrder
        });
	},

	btnSearch : function()
	{
		var uri =
		{
			offset : 0,
			tag_query : this.getComponent('searchBar').getValue()
		};
		this.msgBus.fireEvent('Browser_ReloadData', uri);
	},

	btnDatasetClick : function()
	{
		this.westPanel.removeAll(false);
		
        this.datasetCt = this.datasetCt || new Bisque.ResourceBrowser.DatasetManager(
        {
            parentCt : this.westPanel,
            browser : this.browser,
            msgBus : this.msgBus
        });
        
        this.westPanel.setWidth(this.datasetCt.width).show().expand();
        this.westPanel.add(this.datasetCt);
        this.westPanel.doComponentLayout(null, null, true);
	},

	btnOrganizerClick : function()
	{
        this.westPanel.removeAll(false);
        
        this.organizerCt = this.organizerCt || new Bisque.ResourceBrowser.Organizer(
        {
            parentCt : this.westPanel,
            dataset : this.browser.browserState['baseURL'],
            wpublic : this.browser.browserParams.wpublic,
            browser : this.browser,
            msgBus : this.msgBus
        });
        
        this.westPanel.setWidth(this.organizerCt.width).show().expand();
        this.westPanel.add(this.organizerCt);
        this.westPanel.doComponentLayout(null, null, true);
	},

	btnLayoutClick : function(item)
	{
		switch (item.itemId)
		{
			case 'btnThumb' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT);
				break;
			case 'btnCard' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.CARD);
				break;
			case 'btnPStrip' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP);
				break;
			case 'btnFull' :
				this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.FULL);
				break;
		}
	},
	
	toggleLayoutBtn : function()
	{
		switch(this.browser.layoutKey)
		{
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT :
				this.getComponent('btnThumb').toggle(true, false);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.CARD :
				this.getComponent('btnCard').toggle(true, false);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP :
				this.getComponent('btnPStrip').toggle(true, false);
				break;
			case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.FULL :
				this.getComponent('btnFull').toggle(true, false);
				break;
		}
	},
	
	btnTSSetState : function(tagOrder)
	{
        var sortState=(tagOrder.indexOf('"@ts":desc')!=-1)?'DESC':((tagOrder.indexOf('"@ts":asc')!=-1)?'ASC':'');
        var btn=this.getComponent('btnTS');

        if (btn.sortState!=sortState)
            if (sortState=='DESC')
            {
                btn.setIcon(bq.url('/js/ResourceBrowser/Images/desc.png'));
                btn.sortState='DESC';
                btn.setTooltip('Sort data ascending by timestamp (current: descending)');
            }
            else
            {
                btn.setIcon(bq.url('/js/ResourceBrowser/Images/asc.png'));
                btn.sortState='ASC';
                btn.setTooltip('Sort data descending by timestamp (current: ascending)');
            }
	},
	
	btnSearchSetState : function(tagQuery)
	{
	    this.getComponent('searchBar').setValue(decodeURIComponent(tagQuery));
	},
	
	setStatus : function(status)
	{
		if (this.slider.rendered)
			this.slider.setStatus(status);	
	},
	
	applyPreferences : function()
	{
	    if (this.rendered)
            this.toggleLayoutBtn();
        this.getComponent('btnGear').menu.getComponent('btnWpublic').setChecked(this.browser.browserParams.wpublic, true);
	}
})