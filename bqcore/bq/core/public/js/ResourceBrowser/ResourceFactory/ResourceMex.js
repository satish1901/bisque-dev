/* Abstract Mex resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Mex',
{
    extend:'Bisque.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Mex.Compact',
{
    extend : 'Bisque.Resource.Mex',
    
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
		this.addCls('compact');		
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
        
        if (tagArr.length>0)
            this.ttip.add(propsGrid);
		this.ttip.setLoading(false);
	},

    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
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
        var name = Ext.create('Ext.container.Container', {
            cls : 'lblHeading1',
            html : Ext.String.ellipsis(this.resource.name || 'undefined', 24),
        })

        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : Ext.Date.format(new Date(this.resource.ts), "m-d-Y g:i:s a"),
        })

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : this.resource.value,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Mex.List',
{
    extend : 'Bisque.Resource.Mex',
    
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
		this.addCls('list');			
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
                //autoHide : false,
	    		listeners : 
	    		{
	    			"afterrender" : function(me){if (!this.tagsLoaded) me.setLoading({msg:''})},
	    			scope : this
	    		}
	    	});
    	}
        // HACK to hide session "mex". Come up with better strategy in future
        //if (this.resource.status=='SESSION')
        //    this.setVisible(false);

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
    
    onMouseLeave : function(e)
    {
        this.mouseIn=false;
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
        
        if (tagArr.length>0)
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
                this.loadResource({name:'Module.NoName'});
			}
		}
    },

	loadResource : function(moduleInfo)
    {
		this.setData('module', this.resource.name);
		this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
		var mexName=new Ext.form.Label({
			text:' '+Ext.String.ellipsis(this.resource.name, 22)+' ',
			padding:'0 8 0 8',
			cls:'lblModuleName',
		})

		var mexStatus=new Ext.form.Label({
			text:this.resource.status,
			padding:'0 0 0 4',
			cls: this.resource.status=='FINISHED'?'lblModuleOwnerFin':(this.resource.status=='FAILED'?'lblModuleOwnerFail':'lblModuleOwner')
		})

		var date=new Date(this.resource.ts);
		
		var mexDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			padding:'0 0 0 8',
			//style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
			cls: 'lblModuleDate',
			flex: 1,			
		})

		this.add([mexName, mexStatus, mexDate]);
        this.setLoading(false);
    },
});
