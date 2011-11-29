/* Abstract Module resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.ResourceBrowser.ResourceFactory.ModuleResource',
{
    extend:'Bisque.ResourceBrowser.ResourceFactory.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ModuleResourceCompact',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.ModuleResource',
    
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
        this.addCls('compact');
		
		Bisque.ResourceBrowser.ResourceFactory.ModuleResourceCompact.superclass.constructor.apply(this, arguments);
	},

    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
	        
	        BQFactory.request({
	        	uri:this.resource.owner,
	        	cb:Ext.bind(this.loadResource, this),
	        	errorcb:Ext.emptyFn});
		}
    },
    
	loadResource : function(ownerInfo)
    {
		this.setData('owner', ownerInfo.display_name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var moduleName=new Ext.form.Label({
			text:this.resource.name,
			//padding:5,
			cls:'lblModuleName',
		})
		
		var moduleOwner=new Ext.form.Label({
			text:this.getData('owner'),
			//padding:'0 0 0 5',
			cls:'lblModuleOwner'
		})

		var moduleType=new Ext.form.Label({
			text:this.resource.type,
			padding:5,
			style:'color:#444'
		})

		this.add([moduleName, moduleOwner, moduleType]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ModuleResourceList',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.ModuleResource',
    
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
		
		Bisque.ResourceBrowser.ResourceFactory.ModuleResourceList.superclass.constructor.apply(this, arguments);
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
    		BQFactory.request({uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this)});
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
            this.setData('fetched', -1);	// -1 = Loading
	        
            BQFactory.request(
            {
                uri:this.resource.uri+'?view=deep',
                cb:Ext.bind(this.loadResourceTags, this),
                errorcb:Ext.emptyFn
            });
		}
    },
    
    loadResourceTags : function(resource)
    {
      this.setData('tags', resource.tags);

      BQFactory.request(
      {
          uri:this.resource.owner,
          cb:Ext.bind(this.loadResource, this),
          errorcb:Ext.emptyFn
      });
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
		var moduleName=new Ext.form.Label({
			text:' '+this.resource.name+' ',
			//padding:5,
			cls:'lblModuleName',
		})

		var moduleOwner=new Ext.form.Label({
			text:this.getData('owner'),
			//padding:'0 0 0 5',
			cls:'lblModuleOwner'
		})

		var moduleType=new Ext.form.Label({
			text:this.resource.type,
			padding:5,
			style:'color:#444'
		})

		this.add([moduleName, moduleOwner, moduleType]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ModuleResourceIconList',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.ModuleResourceList',

    initComponent : function() {
        this.addCls('icon-list');
        this.callParent();
    },	    
    
    afterRenderFn : function()
    {
        this.ttip=1;
        this.tagsLoaded=1;
        this.callParent(arguments);
    },
    
    updateContainer : function()
    {
        var serviceURL = BisqueServices.getURL('module_service') + this.resource.name;
        var tags = this.getData('tags'), description;
        
        for (var i=0;i<tags.length;i++)
            if (tags[i].name=="description")
                description=tags[i].value;

        var imgCt=Ext.create('Ext.container.Container', 
        {
            margin:'0 0 0 4',
            width:110,
            height:110,
            html: '<img style="position:relative;height:100%;width:100%" src="'+serviceURL+'/thumbnail"/>'
        });

        var moduleName=new Ext.form.Label({
            text:this.resource.name,
            //padding:'0 0 1 3',
            cls:'lblModuleName',
        })

        var moduleInfo=new Ext.form.Label({
            html: this.getData('owner')!=0 ? 'Owner: '+this.getData('owner'):'',
            //padding:'0 0 0 3',
            maxHeight:18,
            cls:'lblModuleOwner'
        })

        var moduleDesc=new Ext.form.Label({
            html:description,
            padding:'7 2 0 3',
            //style:'color:#555'
        })
        
        var rightCt=Ext.create('Ext.container.Container',
        {
            layout:
            {
                type:'vbox',
                align:'stretch'
            },
            margin:'2 0 0 2',
            height:120,
            flex:1,
            
            items: [moduleName, moduleInfo, moduleDesc]
        });
        
        this.add([imgCt, rightCt]);
        this.setLoading(false);
    }
});
