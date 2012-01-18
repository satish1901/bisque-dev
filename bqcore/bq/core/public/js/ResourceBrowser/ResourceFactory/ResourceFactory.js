Ext.define('Bisque.ResourceFactory', {

    statics : {

        baseClass : 'Bisque.Resource',

        getResource : function(config) {
            var layoutKey = Ext.Object.getKey(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS, config.layoutKey);
            // resource naming convention : baseClass.resourceType.layoutKey
            var className = Bisque.ResourceFactory.baseClass + '.' + Ext.String.capitalize(config.resource.resource_type.toLowerCase()) + '.' + layoutKey;
            
            if (Ext.ClassManager.get(className))
                return Ext.create(className, config);
            else
            {
                Ext.log({
                    msg     :   Ext.String.format('Unknown class: {0}, type: {1}, layoutKey: {2}. Initializing with base resource class.', className, config.resource.resource_type, layoutKey),
                    level   :   'warn',
                    stack   :   true
                });
                return Ext.create(Bisque.ResourceFactory.baseClass+'.'+layoutKey, config);
            }
        }
    }
})

Bisque.ResourceFactoryDeprecated = function(config)
{
    var resType = (config.resource.xmltag=="resource")?config.resource.type:config.resource.xmltag; 
    
    switch (resType)
    {
        case 'mex':
            switch (config.layoutKey)
            {
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.CARD :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP_BIG :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.FULL :
                    return new Bisque.ResourceBrowser.ResourceFactory.MexResourceCompact(config);
                    break;
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.LIST :
                    return new Bisque.ResourceBrowser.ResourceFactory.MexResourceList(config);
                    break;
                default :
                    throw new Error('ResourceFactory: Unrecognized resource layout key - '
                    + config.layoutKey);
            }
            break;
        case 'module':
            switch (config.layoutKey)
            {
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.CARD :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP_BIG :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.FULL :
                    return new Bisque.ResourceBrowser.ResourceFactory.ModuleResourceCompact(config);
                    break;
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.LIST :
                    return new Bisque.ResourceBrowser.ResourceFactory.ModuleResourceList(config);
                    break;
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.ICON_LIST :
                    return new Bisque.ResourceBrowser.ResourceFactory.ModuleResourceIconList(config);
                    break;
                default :
                    throw new Error('ResourceFactory: Unrecognized resource layout key - '
                    + config.layoutKey);
            }
            break;
        case 'dataset':
            switch (config.layoutKey)
            {
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.COMPACT :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.CARD :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.PSTRIP_BIG :
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.FULL :
                    return new Bisque.ResourceBrowser.ResourceFactory.DatasetResourceCompact(config);
                    break;
                case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.LIST :
                    return new Bisque.ResourceBrowser.ResourceFactory.DatasetResourceList(config);
                    break;
                default :
                    throw new Error('ResourceFactory: Unrecognized resource layout key - '
                    + config.layoutKey);
            }
            break;
        default :
            return new Bisque.ResourceBrowser.ResourceFactory.Resource(config);
            
            //throw new Error('ResourceFactory: Unknown resource type: ' + config.resource.type);
    }
};


// Returns standalone resources 
Ext.define('Bisque.ResourceFactoryWrapper',
{
    statics : 
    {
        getResource : function(config)
        {
    		config.resourceManager = Ext.create('Ext.Component', 
    		{
    			store : {},
    			
    			storeMyData : function(uri, tag, value)
    			{
    				this.store[tag]=value;
    			},
    			
    			getMyData : function(uri, tag)
    			{
                    if (this.store[tag])
                        return this.store[tag];
    				return 0;
    			}
    		});
    		
    		Ext.apply(config,
    		{
    			layoutKey : config.layoutKey || Bisque.ResourceBrowser.LayoutFactory.DEFAULT_LAYOUT,
    			msgBus : config.msgBus || config.resourceManager,
    			resQ : config.resQ || config.resourceManager,
    			browser : config.browser || {},
    		});
    			
    		var resource = Bisque.ResourceFactory.getResource(config);
    		var layoutCls = Bisque.ResourceBrowser.LayoutFactory.getClass(config.layoutKey);
    		var css = Ext.ClassManager.get(layoutCls).readCSS();
    
    		resource.prefetch(css);
    		resource.setSize({width:css.layoutEl.width, height:css.layoutEl.height})
    		resource.addCls(css.layoutCSS);
    		
    		return resource;
        }
    }
});

/**
 * BaseLayout: Abstract base resource, extends Ext.Container, parent of all other
 * resource types
 *
 * @param {}
 *            config : Includes {resource, layoutKey}. Resource: Passed resource
 *            object, layoutKey : layout key according to which the resource
 *            object will be formatted
 */
Ext.define('Bisque.Resource',
{
    extend:'Ext.container.Container',

    constructor : function(config)
    {
        Ext.apply(this,
        {
            resource : config.resource,
            browser : config.browser,
            layoutKey : config.layoutKey,
            msgBus : config.msgBus,
            resQ : config.resQ,

            border : false,
            cls : 'LightShadow',
            overCls : 'resource-view-over',
			style: 'float:left;'
        });
        
        this.callParent(arguments);
        this.manageEvents();
    },
    
    setLoadingMask : function()
    {
        if (this.getData('fetched')!=1)
            this.setLoading({msg:''});
    },

    GetPropertyGrid : function(configOpts, source)
    {
        var propsGrid=Ext.create('Ext.grid.Panel',
        {
            autoHeight : configOpts.autoHeight,
            style : "text-overflow:ellipsis;"+configOpts.style,
            width : configOpts.width,
            store : Ext.create('Ext.data.Store',
            {
                model: 'Ext.grid.property.Property',
                data: source
            }),
            border : false,
            padding : 1,
            multiSelect: true,
            plugins : new Ext.ux.DataTip(
            {
                tpl : '<div>{value}</div>'
            }),

            columns:
            [{
                text: 'Tag',
                flex: 0.8,
                dataIndex: 'name'
            },
            {
                text: 'Value',
                flex: 1,
                dataIndex: 'value'
            }]
        });

        return propsGrid
    },

    getData : function(tag) 
    {
        if (this.resQ)
            return this.resQ.getMyData(this.resource.uri, tag);
    },
    setData : function(tag, value) {this.resQ.storeMyData(this.resource.uri, tag, value)},
    // Resource functions 
    prefetch : function(layoutMgr)	//Code to prefetch resource data
    {
    	this.layoutMgr=layoutMgr;
    },
    loadResource : Ext.emptyFn,	//Callback fn when data is loaded 

    //Render a default resource view into container when resource data is loaded
    //(can be overridden for a customized view of the resource)
    updateContainer : function()
    {
        // default data shown
        var name = Ext.create('Ext.container.Container', {
            cls : 'lblHeading1',
            html : this.resource.name,
        })

        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : this.resource.resource_type,
        })

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : this.resource.value,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
    
    afterRenderFn : function()
    {
        this.updateContainer();
    },

    manageEvents : function()
    {
    	this.on('afterrender', Ext.Function.createInterceptor(this.afterRenderFn, this.preAfterRender, this));
    },
    
    preAfterRender : function()
    {
		this.setLoadingMask();	// Put a mask on the resource container while loading
		var el=this.getEl();

		el.on('mouseenter', Ext.Function.createSequence(this.preMouseEnter, this.onMouseEnter, this), this);
		el.on('mousemove', this.onMouseMove, this);
		el.on('mouseleave', Ext.Function.createSequence(this.preMouseLeave, this.onMouseLeave, this), this);
		el.on('click', Ext.Function.createSequence(this.preClick, this.onClick, this), this);
		el.on('contextmenu', this.onRightClick, this);
		el.on('dblclick', Ext.Function.createSequence(this.preDblClick, this.onDblClick, this), this);
		
		if (this.browser.gestureMgr)
			this.browser.gestureMgr.addListener(
			[
				{
					dom: el.dom,
					eventName: 'doubletap',
					listener: Ext.bind(Ext.Function.createSequence(this.preDblClick, this.onDblClick, this), this), 
					//options: {holdThreshold:500}
				},
				{
					dom: el.dom,
					eventName: 'singletap',
					listener: Ext.bind(Ext.Function.createSequence(this.preClick, this.onClick, this), this), 
				}
			]);
    },

    preClick : function()
    {
        this.msgBus.fireEvent('ResourceSingleClick', this.resource);
    	
    	if (this.el.hasCls('resource-view-selected'))
    	{
    		this.toggleSelect(false);
    		this.fireEvent('unselect', this);
    	}
    	else
    	{
    		this.toggleSelect(true);
    		this.fireEvent('select', this);
    	}
    },
    
    toggleSelect : function(state)
    {
    	if (state)
    		this.addCls('resource-view-selected')
    	else
    	{
    		this.removeCls('resource-view-selected');
			this.addCls('LightShadow');
    	}
    },
    
    preDblClick : function()
    {
		this.msgBus.fireEvent('ResourceDblClick', this.resource);
    },

    preMouseEnter : function()
    {
    	this.removeCls('LightShadow');
    },
    preMouseLeave : function()
    {
		if (!this.el.hasCls('resource-view-selected'))
			this.addCls('LightShadow');
    },

    onMouseEnter : Ext.emptyFn,
    onMouseMove : Ext.emptyFn,
    onMouseLeave : Ext.emptyFn,
    onDblClick : Ext.emptyFn,
    onClick : Ext.emptyFn,
    onRightClick : Ext.emptyFn
});

Ext.define('Bisque.Resource.Compact', {
    extend:'Bisque.Resource'
});

Ext.define('Bisque.Resource.Card', {
    extend:'Bisque.Resource'
});

Ext.define('Bisque.Resource.PStrip', {
    extend:'Bisque.Resource'
});

Ext.define('Bisque.Resource.PStripBig', {
    extend:'Bisque.Resource',
});

Ext.define('Bisque.Resource.Full', {
    extend:'Bisque.Resource'
});

Ext.define('Bisque.Resource.List', {
    extend:'Bisque.Resource'
});

// Default page view is a full page ResourceTagger
Ext.define('Bisque.Resource.Page', 
{
    extend:'Bisque.Resource',
    
    updateContainer : function() 
    {
        var name = this.resource.name || this.resource.uri;
        var type = this.resource.type || this.resource.resource_type;
        var title = "Editing " + type + ' : ' + name;
        
        var resourceTagger = new Bisque.ResourceTagger(
        {
            title : title,
            resource : this.resource,
            split : true
        });
        
        this.add(resourceTagger);
        this.setLoading(false);
    }
});