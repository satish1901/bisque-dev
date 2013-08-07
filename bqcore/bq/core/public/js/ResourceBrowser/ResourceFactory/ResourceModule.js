/* Abstract Module resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Module',
{
    extend:'Bisque.Resource',

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Module.Compact',
{
    extend : 'Bisque.Resource.Module',
    
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
        var name = Ext.create('Ext.container.Container', {
            cls : 'lblHeading1',
            html : this.resource.name,
        })

        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : this.getData('owner'),
        })

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : this.resource.value,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Module.List',
{
    extend : 'Bisque.Resource.Module',
    
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
                autoHide : false,
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

Ext.define('Bisque.Resource.Module.IconList',
{
    extend : 'Bisque.Resource.Module.List',

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
            html: '<img style="position:relative;height:110px;width:110px" src="'+serviceURL+'/thumbnail"/>'
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

// Page view for a module
Ext.define('Bisque.Resource.Module.Page',
{
    extend : 'Bisque.Resource.Page',
    
/*    setDisabled : function(btn)
    {
        
    },
    
    getOperations : function(resource)
    {
        var ops = this.callParent(arguments);
        ops.push({
            itemId      :   'btnDisable',
            operation   :   this.setDisabled,
            handler     :   this.testAuth1,
            setBtnText  :   function(me)
                            {
                                var text = 'Visibility: ';
                                
                                if (this.resource.permission == 'published')
                                {
                                    text += '<span style="font-weight:bold;color: #079E0C">published</span>';
                                    me.setIconCls('icon-eye');
                                }
                                else
                                {
                                    text += 'private';
                                    me.setIconCls('icon-eye-close')
                                }
                                
                                me.setText(text);
                            },
            listeners   :   {
                                'afterrender'   :   function(me)
                                                    {
                                                        me.setBtnText.call(this, me);
                                                    },
                                scope           :   this
                
                            }
        });

        
    }*/
});
