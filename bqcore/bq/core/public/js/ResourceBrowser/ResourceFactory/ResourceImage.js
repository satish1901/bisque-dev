/* Abstract Image resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.ResourceBrowser.ResourceFactory.ImageResource',
{
    extend:'Bisque.ResourceBrowser.ResourceFactory.Resource',

    // Two functions for speed
    GetImageThumbnailRel : function(params, size, full)
    {
        //return '<img src="' + this.resource.src + '?thumbnail' + params + '"/>';
        return '<img style="position:relative; top:50%; left:50%; margin-top: -'+size.height/2+'px;margin-left: -'+size.width/2+'px;"'
        +((full==undefined)?' id="'+this.resource.uri+'"':'')
        + ' src="' + this.resource.src + '?' +  this.browser.preferences.Images.ImageParameters +'&thumbnail' + params
        + '"/>';
    },
    
    GetImageThumbnailAbs : function(params, size, full)
    {
        //return '';
        //return '<img src="' + this.resource.src + '?thumbnail' + params + '"/>';

        return '<img style="position:absolute; top:50%; left:50%; margin-top: -'+size.height/2+'px;margin-left: -'+size.width/2+'px;"'
        +((full==undefined)?' id="'+this.resource.uri+'"':'')
        + ' src="' + this.resource.src + '?' +  this.browser.preferences.Images.ImageParameters +'&thumbnail' + params
        + '"/>';
    },

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1 && !this.isDestroyed)
            this.updateContainer();
    },

    OnDblClick : function()
    {
        this.msgBus.fireEvent('ResourceDblClick', this.resource.uri);
    },

    onMouseEnter : function(e, me)
    {
		// only 1 frame available
		if (this.resource.t==1 && this.resource.z==1)
			this.mmData={isLoadingImage:true};
		else
		{			
			var el = this.getEl();
			this.mmData =
			{
				x : el.getX() + el.getOffsetsTo(this.resource.uri)[0],
				y : el.getY() + el.getOffsetsTo(this.resource.uri)[1],
				isLoadingImage : false
			};
		}
    },

    onMouseLeave : function()
    {
        if (this.mmData)
            this.mmData.isLoadingImage = true;
    },

    onMouseMove : function(e, target)
    {
        if (this.mmData && !this.mmData.isLoadingImage)
        {
            this.mmData.isLoadingImage = true;

            var sliceX = Math.ceil((e.getX() - this.mmData.x) * this.resource.t / target.clientWidth);
            var sliceY = Math.ceil((e.getY() - this.mmData.y) * this.resource.z / target.clientHeight);

            if (sliceX > this.resource.t)
                sliceX = this.resource.t
            if (sliceY > this.resource.z)
                sliceY = this.resource.z

            var imgLoader = new Image();
            imgLoader.src = this.resource.src + '?slice=,,' + sliceY + ',' + sliceX + '&' +  this.browser.preferences.ImageParameters +'&thumbnail='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight;

            function ImgOnLoad()
            {
                if (Ext.isDefined(document.images[this.resource.uri]))
                {
                    document.images[this.resource.uri].src = imgLoader.src;
                    this.mmData.isLoadingImage = false;
                }
            }

            imgLoader.onload = Ext.bind(ImgOnLoad, this);
        }
    },
    
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ImageResourceCompact',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.ImageResource',
    
  	afterRenderFn : function(e)
  	{
		if (!this.ttip)
    	{
    		this.mouseIn=false;
	    	this.ttip=Ext.create('Ext.tip.ToolTip', 
	    	{
	    		target: this.id,
	    		anchor: "top",
	    		maxWidth: 600,
	    		width: 555,
	    		cls: 'LightShadow',
	    		dismissDelay: 0,
	    		style: 'background-color:#FAFAFA;border: solid 2px #E0E0E0;',
	    		layout: 'hbox',
	    		
	    		listeners : 
	    		{
	    			"beforeshow" : function(me){if (!this.tagsLoaded || !this.mouseIn) return false;},
	    			scope : this
	    		}
	    	});

    	}
    	this.callParent(arguments);
  	},
  	
  	onRightClick : function(e)
  	{
  		e.preventDefault();
  		this.mouseIn=true;
		(!this.tagsLoaded)?this.requestTags():this.ttip.show();
  	},
  	
  	onMouseLeave : function(e)
  	{
  		this.mouseIn=false;
  		this.callParent(arguments);
  	},
  	
    requestTags : function()
    {
    	if (!this.tagsLoaded)
    	{
    		BQFactory.request({uri: this.resource.uri + '/tags', cb: Ext.bind(this.tagData, this, ['tags'], true)});
    		BQFactory.request({uri: this.resource.src + '?meta', cb: Ext.bind(this.tagData, this, ['meta'], true)});
    	}
    },
    
	tagData : function(data, type)
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
        
        if (type=='tags')
        	propsGrid.title='Tag data';
        else
        	propsGrid.title='Metadata';
        
        this.ttip.add(propsGrid);
		this.ttip.show();
	},
	    
    prefetch : function(layoutMgr)
    {
    	Bisque.ResourceBrowser.ResourceFactory.ImageResourceCompact.superclass.prefetch(layoutMgr);
    	
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            var prefetchImg = new Image();
            prefetchImg.src = this.resource.src + '?thumbnail='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight;
            prefetchImg.onload=Ext.bind(this.loadResource, this);
        }
    },
    
    loadResource : function(img)
    {
        this.setData('image', this.GetImageThumbnailRel.call(this, '='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight,
        {
            width:img.currentTarget.width,
            height:img.currentTarget.height
        }));
        this.setData('fetched', 1);	//Loaded

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },

    updateContainer : function()
    {
    	var text="ch:"+this.resource.ch+" x:"+this.resource.x+" y:"+this.resource.y+" z:"+this.resource.z+" t:"+this.resource.t;
        this.update('<div class="textOnImage" style="width:'+this.layoutMgr.layoutEl.width+'px;">'+text+'</div>'+this.getData('image'));
        
        this.setLoading(false);
    },
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ImageResourceCard',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.ImageResource',

	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
                type : 'vbox',
                align : 'stretch'
            }
        });
		
		this.callParent(arguments);
	},
	
    prefetch : function(layoutMgr)
    {
    	Bisque.ResourceBrowser.ResourceFactory.ImageResourceCard.superclass.prefetch(layoutMgr);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            BQFactory.load(this.resource.uri + '/tags', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.resource.src + '?thumbnail='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight;
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type)
    {
        if (type=='image')
            this.setData('image', this.GetImageThumbnailRel.call(this, '='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight,
            {
                width:data.currentTarget.width,
                height:data.currentTarget.height
            }));
        else
        {
            this.resource.tags = data.tags;

            // Assuming we know which tags to fetch
            var tagArr=[], tags =
            {
                "filename" : 0,
                "attached-file" : 0,
                "image_type" : 0,
                "imagedate" : 0,
                "experimenter" : 0,
                "dataset_label" : 0,
                "species" : 0
            };

            for (var tagID in tags)
            {
                var tag = this.resource.find_tags(tagID, false, '');
                tags[tagID] = (tag == null || tag.value == "" ? 'None' : tag.value);
                tagArr.push(new Ext.grid.property.Property(
                {
                    name: tagID,
                    value: tags[tagID]
                }));
            }

            this.setData('tags', tagArr);
        }

        if (this.getData('tags') && this.getData('image'))
        {
            this.setData('fetched', 1);	//Loaded

            var renderedRef=this.getData('renderedRef')
            if (renderedRef	&& !renderedRef.isDestroyed)
                renderedRef.updateContainer();
        }
    },

    updateContainer : function()
    {
        var propsGrid=this.GetPropertyGrid({/*autoHeight:true}*/}, this.getData('tags'));
        propsGrid.determineScrollbars=Ext.emptyFn;
        
        var imgCt=new Ext.Component({html:this.getData('image'), height:this.layoutMgr.layoutEl.imageHeight});
        this.add([imgCt, propsGrid]);
        this.setLoading(false);
    },
    
	onMouseMove : Ext.emptyFn,
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ImageResourcePStrip',
{
    extend:'Bisque.ResourceBrowser.ResourceFactory.ImageResourceCompact',

    onClick : function()
    {
        this.msgBus.fireEvent('PStripResourceClick', this.resource, this.layoutMgr);
    },
    
    afterRenderFn : function()
    {
    	this.ttip=1;
    	this.callParent(arguments);
    },
    
    requestTags : Ext.emptyFn,
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ImageResourcePStripBig',
{
    extend:'Bisque.ResourceBrowser.ResourceFactory.ImageResource',

    constructor : function(config)
    {
        this.callParent(arguments);
        Ext.apply(this,
        {
            layout:
            {
                type:'fit'
            },
            overCls:'',
            data: {},
        });

		this.setSize(config.bigPanel.getSize());
        this.pnlSize=config.bigPanel.getSize();
        this.pnlSize.width=Math.floor(0.35*this.pnlSize.width);

        var prefetchImg = new Image();
        prefetchImg.src = this.resource.src + '?thumbnail='+(this.pnlSize.width-10).toString()+','+(this.pnlSize.height-10).toString();
        prefetchImg.onload=Ext.bind(this.loadResource, this);
    },

    loadResource : function(data, type)
    {
		var resourceTagger = new Bisque.ResourceTagger(
		{
			region : 'center',
			resource : this.resource.uri,
			style : 'background-color:#FFF',
		});

		this.data.image=this.GetImageThumbnailAbs.call(this, '='+(this.pnlSize.width-10).toString()+','+(this.pnlSize.width-10).toString(),
		{
			width:data.currentTarget.width,
			height:data.currentTarget.height
		}, true);
            
		var imgDiv = new Ext.get(document.createElement('div'));
		imgDiv.update(this.data.image);

		this.add(new Ext.Panel(
		{
			layout:'border',
			border:false,
			items:[new Ext.Container(
			{
				region:'west',
				layout:
				{
					type:'vbox',
					align:'top'
				},
				width:'55%',
				style:'background-color:#FFF',
				contentEl:imgDiv
			}), resourceTagger]
		}));
            
		this.setLoading(false);
	},
    
    preAfterRender : this.setLoadingMask,
    afterRenderFn : Ext.emptyFn
});

Ext.define('Bisque.ResourceBrowser.ResourceFactory.ImageResourceFull',
{
    extend : 'Bisque.ResourceBrowser.ResourceFactory.ImageResource',

	constructor : function()
	{
        Ext.apply(this,
        {
            layout:'fit',
        });
		
		Bisque.ResourceBrowser.ResourceFactory.ImageResourceFull.superclass.constructor.apply(this, arguments);
	},

    prefetch : function(layoutMgr)
    {
    	Bisque.ResourceBrowser.ResourceFactory.ImageResourceFull.superclass.prefetch(layoutMgr);
    	
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            BQFactory.load(this.resource.uri + '/tags', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.resource.src + '?thumbnail='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight;
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type)
    {
        if (type=='image')
            this.setData('image', this.GetImageThumbnailAbs.call(this, '='+this.layoutMgr.layoutEl.imageWidth+','+this.layoutMgr.layoutEl.imageHeight,
            {
                width:data.currentTarget.width,
                height:data.currentTarget.height
            }, true));
        else
        {
            this.resource.tags = data.tags;
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

            this.setData('tags', tagArr);
        }

        if (this.getData('tags') && this.getData('image'))
        {
            this.setData('fetched', 1);	//Loaded
            if (this.rendered)
                this.updateContainer();
        }
    },

    updateContainer : function()
    {
        this.setLoading(false);
        var propsGrid=this.GetPropertyGrid(
        {
            autoHeight:false
        }, this.getData('tags'));
        propsGrid.setAutoScroll(true);
        propsGrid.region='center';
        propsGrid.padding=5;
        propsGrid.style='background-color:#FAFAFA';

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.dom.align = "center";
        imgDiv.update(this.getData('image'));

        this.add(new Ext.Panel(
        {
            layout:'border',
            border:false,
            items:[new Ext.Container(
            {
                region:'west',
                layout:
                {
                    type:'hbox',
                    pack:'center',
                    align:'center'
                },
                region : 'west',
                padding:5,
                width:this.layoutMgr.layoutEl.imageHeight+10,
                style:'background-color:#FAFAFA',
                contentEl:imgDiv
            }), propsGrid]
        }));
    },

    onMouseMove : Ext.emptyFn,
    preMouseEnter : Ext.emptyFn,
    preMouseLeave : Ext.emptyFn,
    onMouseEnter : Ext.emptyFn
});