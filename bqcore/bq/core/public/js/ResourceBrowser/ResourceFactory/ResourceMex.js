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
        
        if (tagArr.length>0 && this.ttip)
            this.ttip.add(propsGrid);
        if (this.ttip)            
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

        var date = new Date();
        date.setISO(this.resource.ts);
        
        var type = Ext.create('Ext.container.Container', {
            cls : 'lblHeading2',
            html : Ext.Date.format(date, "m-d-Y g:i:s a"),
        })

        var value = Ext.create('Ext.container.Container', {
            cls : 'lblContent',
            html : this.resource.value,
        })

        this.add([name, type, value]);
        this.setLoading(false);
    },
});


Ext.define('Bisque.Resource.Mex.Card',
{
    extend : 'Bisque.Resource.Card',
    
    prefetch : function(layoutMgr)
    {
        this.superclass.superclass.prefetch.apply(this, arguments);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);    //Loading
            BQFactory.load(this.resource.uri + '/tag?view=deep', Ext.bind(this.loadResource, this));
        }
    },

    loadResource : function(data)
    {
        this.resource.tags = data.tags;
        var tagProp, tagArr=[], tagsFlat = this.resource.toDict(true);

        // Show preferred tags first
        for (var tag in tagsFlat)
        {
            tagProp = new Ext.grid.property.Property({
                                                        name: tag,
                                                        value: tagsFlat[tag]
                                                    });
            tagArr.push(tagProp);
            //(tag.indexOf('inputs')!=-1 || tag.indexOf('outputs')!=-1)?tagArr.unshift(tagProp):tagArr.push(tagProp);
        }
        
        tagArr.unshift(new Ext.grid.property.Property({name: 'Status', value: this.resource.value}));
        tagArr.unshift(new Ext.grid.property.Property({name: 'Module', value: this.resource.name}));

        this.setData('tags', tagArr);
        this.setData('fetched', 1); //Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
});


Ext.define('Bisque.Resource.Mex.Full',
{
    extend : 'Bisque.Resource.Full',
    
    loadResource : function(data)
    {
        this.resource.tags = data.tags;
        var tagProp, tagArr=[], tagsFlat = this.resource.toDict(true);

        // Show preferred tags first
        for (var tag in tagsFlat)
        {
            tagProp = new Ext.grid.property.Property({
                                                        name: tag,
                                                        value: tagsFlat[tag]
                                                    });
            tagArr.push(tagProp);
        }
        
        tagArr.unshift(new Ext.grid.property.Property({name: 'Status', value: this.resource.value}));
        tagArr.unshift(new Ext.grid.property.Property({name: 'Module', value: this.resource.name}));
        
        this.setData('tags', tagArr);
        this.setData('fetched', 1); //Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
})

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
            this.ttip = Ext.create('Ext.tip.ToolTip', {
                target      :   me.id,
                width       :   278,
                cls         :   'LightShadow',
                layout      :   'hbox',
                style       :   {
                                    'background-color'  :   '#FAFAFA',
                                    'border'            :   'solid 3px #E0E0E0'
                                },
                listeners   :   {
                                    'afterrender'   :   function(me)
                                    {
                                        if (!this.tagsLoaded)
                                            me.setLoading({msg:''})
                                    },
                                    scope   :   this
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

		var date=new Date();
		date.setISO(this.resource.ts);
		
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

Ext.define('Bisque.Resource.Mex.Grid',
{
    extend : 'Bisque.Resource.Mex',
    
    getFields : function(cb)
    {
        var status = this.resource.status || 'unknown', resource = this.resource;
        var color = (status=='FINISHED') ? '#1C1' : (status=='FAILED') ? '#E11' : '#22F';
       
        return ['', resource.name || '', '<div style="color:'+color+'">'+Ext.String.capitalize(status.toLowerCase())+'</div>' || '', resource.resource_type, resource.ts, this, {height:21}];
    }
});

// Page view for a mex
/*Ext.define('Bisque.Resource.Mex.Page',
{
    extend : 'Bisque.Resource.Page',
    
    constructor : function(config)
    {
        window.location = bq.url('/module_service/'+config.resource.name+'/?mex='+config.resource.uri);
    }
});*/

        

