/* Abstract Mex resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.ResourceBrowser.ResourceFactory.MexResource',
{
    extend:'Bisque.ResourceBrowser.ResourceFactory.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.MexResourceCompact',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.MexResource',
    
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
		
		Bisque.ResourceBrowser.ResourceFactory.MexResourceCompact.superclass.constructor.apply(this, arguments);
	},
	
    afterRenderFn : function(me)
    {
    	if (!this.ttip)
    	{
	    	this.ttip=Ext.create('Ext.tip.ToolTip', 
	    	{
	    		target: me.id,
	    		width:278,
	    		cls:'LightShadow',
	    		style:'background-color:#FAFAFA;border: solid 3px #E0E0E0;',
	    		layout:'hbox',
	    		listeners : 
	    		{
	    			"afterrender" : function(me){if (!this.tagsLoaded) me.setLoading({msg:''})},
	    			scope : this
	    		}
	    	});
    	}
    	
    	this.callParent(arguments);
    },
    
    onMouseEnter : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tags', cb: Ext.bind(this.tagData, this)});
    	}
    	this.callParent(arguments);
    },
    
	tagData : function(data)
	{
		this.tagsLoaded=true;
		this.resource.tags=data.tags;
		
		var tagArr=[], tags =
		{
		}, found='';

		for (var i = 0; i < this.resource.tags.length; i++)
		{
			found = this.resource.tags[i].value;
			tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
			tagArr.push(new Ext.grid.property.Property(
			{
				name: this.resource.tags[i].name,
				value: tags[this.resource.tags[i].name]
			}));
		}
        
        var propsGrid=this.GetPropertyGrid({width:270}, tagArr);
        
        this.ttip.add(propsGrid);
		this.ttip.setLoading(false);
	},

    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

			/*if (this.resource.module.indexOf(window.location.host)!=-1)	// Load module names if running on
			{
				BQFactory.request(
				{
					uri:this.resource.module,
					cb:Ext.bind(this.loadResource, this),
					errorcb:Ext.emptyFn
				});
			}
			else*/
				this.loadResource({name:'Module.NoName'});
		}
    },
    
	loadResource : function(moduleInfo)
    {
		this.setData('module', moduleInfo.name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var mexName=new Ext.form.Label({
			text:this.getData('module'),
			padding:5,
			cls:'lblModuleName',
		})

		var mexStatus=new Ext.form.Label({
			text:this.resource.status,
			padding:'0 0 0 5',
			cls:'lblModuleOwner'
		})

		var date=Ext.Date.parse(this.resource.ts, 'Y-m-d H:i:s.u');
		
		var mexDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			padding:5,
			style:'color:#444'
		})

		this.add([mexName, mexStatus, mexDate]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.MexResourceList',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.MexResource',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'hbox',
            	align:'middle'	
            }
        });
		
		this.callParent(arguments);
	},

    afterRenderFn : function(me)
    {
    	if (!this.ttip)
    	{
	    	this.ttip=Ext.create('Ext.tip.ToolTip', 
	    	{
	    		target: me.id,
	    		width:278,
	    		cls:'LightShadow',
	    		style:'background-color:#FAFAFA;border: solid 3px #E0E0E0;',
	    		layout:'hbox',
	    		listeners : 
	    		{
	    			"afterrender" : function(me){if (!this.tagsLoaded) me.setLoading({msg:''})},
	    			scope : this
	    		}
	    	});
    	}
    	
    	this.callParent(arguments);

    },
    
    onMouseEnter : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tags', cb: Ext.bind(this.tagData, this)});
    	}
    	this.callParent(arguments);
    },
    
	tagData : function(data)
	{
		this.tagsLoaded=true;
		this.resource.tags=data.tags;
		
		var tagArr=[], tags = {}, found='';

		for (var i = 0; i < this.resource.tags.length; i++)
		{
			found = this.resource.tags[i].value;
			tags[this.resource.tags[i].name] = (found==null||found==""?'None':found);
			tagArr.push(new Ext.grid.property.Property(
			{
				name: this.resource.tags[i].name,
				value: tags[this.resource.tags[i].name]
			}));
		}
        
        var propsGrid=this.GetPropertyGrid({width:270}, tagArr);
        
        this.ttip.add(propsGrid);
		this.ttip.setLoading(false);
	},
    
    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
			
			if (this.resource.module && this.resource.module.indexOf(window.location.host)!=-1)	// HACK: Load module names if running on the same host
			{
				BQFactory.request(
				{
					uri:this.resource.module,
					cb:Ext.bind(this.loadResource, this),
					errorcb:Ext.emptyFn
				});
			}
			else
			{
			    // HACK to hide session "mex". Come up with better strategy in future
                if (this.resource.status=='SESSION')
                    this.setVisible(false);
                else
                    this.loadResource({name:'Module.NoName'});
                
			}
		}
    },

	loadResource : function(moduleInfo)
    {
		this.setData('module', moduleInfo.name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var mexName=new Ext.form.Label({
			text:' '+this.getData('module')+' ',
			padding:'0 8 0 8',
			cls:'lblModuleName',
		})

		var mexStatus=new Ext.form.Label({
			text:this.resource.status,
			padding:'0 0 0 4',
			cls:'lblModuleOwner'
		})

		var date=Ext.Date.parse(this.resource.ts, 'Y-m-d H:i:s.u');
		
		var mexDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			padding:'0 0 0 8',
			style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
		})

		this.add([mexName, mexStatus, mexDate]);
        this.setLoading(false);
    },
});

