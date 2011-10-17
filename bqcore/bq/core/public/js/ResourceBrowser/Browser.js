// Declare namespace for the modules in RecourseBrowser package
Ext.namespace('Bisque.ResourceBrowser');
Ext.require([
	'Ext.tip.*'
]);
Ext.tip.QuickTipManager.init();

/**
 * Browser: Main ResourceBrowser class which acts as an interface between
 * ResourceBrowser and other Bisque components
 *
 * @param {}
 *            browserParams : Initial config parameters such as URI, Offset etc.
 */

// ResourceBrowser in a Ext.Window container
Ext.define('Bisque.ResourceBrowser.Dialog', 
{
	extend : 'Ext.window.Window',
	
    constructor : function(config)
    {
        config = config || {};
        config.height = config.height || '85%';
        config.width = config.width || '85%';
        
        var bodySz=Ext.getBody().getViewSize();
        var height=parseInt((config.height.indexOf("%")==-1)?config.height:(bodySz.height*parseInt(config.height)/100));
        var width = config.width;
        if (typeof config.width === 'string')
            width=parseInt((config.width.indexOf("%")==-1)?config.width:(bodySz.width*parseInt(config.width)/100));

        Ext.apply(this,
        {
            layout : 'fit',
            title : 'Resource Browser',
            modal : true,
            border : false,
            height : height,
            width : width,
            items : new Bisque.ResourceBrowser.Browser(config),
        }, config);

        this.callParent([arguments]);

        // Relay all the custom ResourceBrowser events to this Window
        //this.relayEvents(this.getComponent(0), ['Select']);
        
        this.getComponent(0).on('Select', function(resourceBrowser, resource)
        {
            this.destroy();
        }, this);
        
        this.show();
    }
});

// ResourceBrowser in a Ext.Panel container
Ext.define('Bisque.ResourceBrowser.Browser', 
{
	extend : 'Ext.panel.Panel',
	
    constructor : function(config)
    {
        //Prefetch the loading spinner
        var imgSpinner = new Image();
        imgSpinner.src=bq.url('/js/ResourceBrowser/Images/loading.gif');
        
        this.westPanel = new Ext.Panel(
        {
            region:'west',
            split:true,
            layout:'fit',
            border:false,
            hidden:true,
        });
        
        this.centerPanel = new Ext.Panel(
        {
            region:'center',
            border:false,
            layout:'hbox',
        });

		config = config || {};
        
		Ext.apply(config,
        {
        	layout	: config.layout || 1,
			dataset	: config.dataset || '/data_service/images/',
			offset	: config.offset || 0,
			tagQuery : config.tagQuery || '',
			tagOrder : config.tagOrder || '',
			wpublic : (config.wpublic=='true'?true:false),
			selType : (config.selType || 'MULTI').toUpperCase()
        });

        Ext.apply(this,
        {
            browserParams : config,
            layoutKey : parseInt(config.layout),
            viewMgr : new Bisque.ResourceBrowser.viewStateManager(config.viewMode),
            organizerCt : null,
            datasetCt : null,
            layoutMgr : null,
            browserState : {},
            resourceQueue : [],
            msgBus : new Bisque.Misc.MessageBus(),
            gestureMgr : null,
            showGroups : false,
            preferenceKey : 'ResourceBrowser',

            // Panel related config
            border : false,
            title : config.title || '',
            layout : 'border',
            items : [this.westPanel, this.centerPanel],
            listeners : config.listeners || {}, 
        }, config);

        this.loadPreferences();
        
        this.browserState['offset'] = config.offset;
        this.commandBar = new Bisque.ResourceBrowser.CommandBar({browser:this});
        this.tbar = this.commandBar;

		if (Ext.supports.Touch)
			this.gestureMgr=new Bisque.Misc.GestureManager();

        this.callParent([arguments]);
	},

    loadPreferences : function(preferences, tag)
    {
        if (preferences==undefined)
            BQ.Preferences.get({key:this.preferenceKey, callback: Ext.bind(this.loadPreferences, this)});
        else
        {            
            this.preferences = preferences;
            this.preferencesTag = tag;
            
            this.applyPreferences();

            this.LoadData(
            {
                baseURL: this.browserParams.dataset,
                offset: this.browserParams.offset,
                tag_query: this.browserParams.tagQuery,
                tag_order: this.browserParams.tagOrder
            });
        }
    },
    
    applyPreferences : function()
    {
        var browserPref = this.preferences.Browser;
        
        this.browserParams.tagQuery = this.browserParams.tagQuery || browserPref["Tag Query"]; 
        this.layoutKey = parseInt(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS[browserPref["Layout"]] || this.browserParams.layout);
        this.browserParams.wpublic = (this.browserParams.wpublic==undefined) ? browserPref["Include Public Resources"] : this.browserParams.wpublic; 
        // Browser preferences
        
    },

    LoadData : function(uri)
    {
        this.centerPanel.setLoading({msg:''});
        
        uri = uri || null;
        
        if (uri)
        {
            if (uri.tag_query == undefined)
                uri.tag_query = this.browserState.tag_query || '';
            if (uri.tag_order == undefined)
                uri.tag_order = this.browserState.tag_order || '';

            if (!uri.baseURL)
                uri.baseURL = this.browserState.baseURL;

            uri.wpublic = this.browserParams.wpublic

            this.setBrowserState(uri);
        }
        else
            var uri = this.getURIFromState();

        for (var param in uri)
            if (uri[param].length == 0)
                delete uri[param];

		if (uri.tag_order)
		{
			var tagValuePair=uri.tag_order.split(','), tags=[], values=[], nextPair;

			function unquote(string)
			{
				return (string.length<2)?string:string.substring(1, string.length-1);
			}
			
			for (var i=0;i<tagValuePair.length;i++)
			{
				nextPair=tagValuePair[i].split(':');
				
				if (unquote(nextPair[0])!="@ts")
				{
					tags.push(unquote(nextPair[0]));
					values.push(nextPair[1].toUpperCase());
				}
			}
			
			uri.view=tags.join(',');
			if (tags.length>=1)
				this.showGroups={tags:tags, order:values};
		}
		else
            //this.showGroups is used in LayoutFactory to group resources based on tag order
			this.showGroups=false;

        this.uri = uri;
        this.resourceQueue = new Bisque.ResourceBrowser.ResourceQueue(
        {
            callBack : callback(this, 'dataLoaded'),
            browser : this,
            uri : this.uri
        });

    },
    
    dataLoaded : function()
    {
        function doLayout()
        {
            this.ChangeLayout(this.layoutKey);
        }

        this.fireEvent('browserLoad', this, this.resourceQueue);

        if (this.rendered)
        {
            doLayout.call(this);
            this.ManageEvents();
        }
        else
            this.on('afterlayout', Ext.Function.createSequence(Ext.bind(doLayout, this), this.ManageEvents, this), {single:true});
    },

    ChangeLayout : function(newLayoutKey, direction)
    {
		console.time("Browser - ChangeLayout");

    	direction=direction||'none';
    	this.centerPanel.setLoading(false);

        if (this.layoutMgr)
            this.layoutMgr.destroy();

        this.layoutKey = newLayoutKey==-1?this.layoutKey:newLayoutKey;
        
        this.layoutMgr = Bisque.ResourceBrowser.LayoutFactory({browser:this, direction:direction});

        this.resourceQueue.changeLayout(
        {
            key:this.layoutKey,
            layoutMgr:this.layoutMgr
        });
        
        this.layoutMgr.Init(this.resourceQueue.getMainQ(this.layoutMgr.getVisibleElements(direction), this.layoutMgr));
        this.centerPanel.add(this.layoutMgr);
        
        this.updateTbarItemStatus();

		console.timeEnd("Browser - ChangeLayout");
    },

    /* Custom ResourceBrowser event management */
    ManageEvents : function()
    {
        this.addEvents('Select');
        this.changeLayoutThrottled = Ext.Function.createThrottled(this.ChangeLayout, 400, this);
        this.centerPanel.on('resize', Ext.bind(this.ChangeLayout, this, [-1]));
        
        this.msgBus.mon(this.msgBus, 
        {
        	'ResourceDblClick' : function(resource)
        	{
        		if (this.selType=='MULTI')
					this.fireEvent('Select', this, resource);
        	},
        	'ResourceSingleClick' : function(resource)
        	{
        		if (this.selType=='SINGLE')
					this.fireEvent('Select', this, resource);
        	},
			'Browser_ReloadData' : function(uri)
       		{
       			if (uri=="")
       			{
			        this.resourceQueue = new Bisque.ResourceBrowser.ResourceQueue(
			        {
			            callBack : callback(this, 'ChangeLayout', this.layoutKey),
			            browser : this,
			            uri : ""
			        });
       			}
       			else
           			this.LoadData(uri);
       		},
			scope  : this
		});

		// HTML5 Gestures (iPad/iPhone/Android etc.)
		if (this.gestureMgr)
			this.gestureMgr.addListener(
			{
				dom: this.centerPanel.getEl().dom,
				eventName: 'swipe',
				listener: Ext.bind(function(e, params)
				{
					if (params.direction=="left")
					{
						var btnRight=this.commandBar.getComponent("btnRight");
						if (!btnRight.disabled)
							btnRight.handler.call(btnRight.scope, btnRight);
					}
					else
					{
						var btnLeft=this.commandBar.getComponent("btnLeft");
						if (!btnLeft.disabled)
							btnLeft.handler.call(btnLeft.scope, btnLeft);
					}
				}, this),
				options: {swipeThreshold:100}
			});
    },

    setBrowserState : function(uri)
    {
        this.browserState['baseURL'] = uri.baseURL;
        this.browserState['tag_query'] = uri.tag_query;
        this.browserState['wpublic'] = this.browserParams.wpublic;
        this.browserState['layout'] = this.layoutKey;
        this.browserState['tag_order'] = uri.tag_order;
    },

    updateTbarItemStatus : function()
    {
        var btnRight=this.commandBar.getComponent("btnRight"), btnLeft=this.commandBar.getComponent("btnLeft");
        var st=this.resourceQueue.getStatus();

        this.commandBar.setStatus(st);

       	btnLeft.setDisabled(st.left || st.loading.left);
        btnRight.setDisabled(st.right || st.loading.right);
        
        this.commandBar.btnTSSetState(this.browserState.tag_order.toLowerCase());
        this.commandBar.btnSearchSetState(this.browserState.tag_query);
    },

    getURIFromState : function()
    {
        var uri =
        {
            baseURL : this.browserState.baseURL,
            offset : this.browserState.offset,
            tag_query : this.browserState.tag_query || '',
            tag_order : this.browserState.tag_order || '',
            wpublic : this.browserParams.wpublic
        };

        for (var param in uri)
            if (uri[param].length == 0)
                delete uri[param];

        return uri;
    },
});
