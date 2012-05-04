/* Abstract Image resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Image',
{
    extend:'Bisque.Resource',

    // Two functions for speed
    GetImageThumbnailRel : function(params, size, full)
    {
        //return '<img style="position:absolute;top:50%;left:50%" src="' + this.getThumbnailSrc(params) + '"/>';
        return '<img style="position:relative; top:50%; left:50%; margin-top: -'+size.height/2+'px;margin-left: -'+size.width/2+'px;"'
        +((full==undefined)?' id="'+this.resource.uri+'"':'')
        + ' src="' + this.getThumbnailSrc(params)
        + '"/>';
    },
    
    getThumbnailSrc : function(params)
    {
        return this.resource.src + this.getImageParams(params);
    },
    
    GetImageThumbnailAbs : function(params, size, full)
    {
        //return '<img src="' + this.resource.src + '?thumbnail' + params + '"/>';
        return '<img style="position:absolute; top:50%; left:50%; margin-top: -'+size.height/2+'px;margin-left: -'+size.width/2+'px;"'
        +((full==undefined)?' id="'+this.resource.uri+'"':'')
        + ' src="' + this.getThumbnailSrc(params) 
        + '"/>';
    },
    
    getImageParams : function(config)
    {
        var prefs = this.getImagePrefs('ImageParameters') || '?slice=,,{sliceZ},{sliceT}&thumbnail={width},{height}&format=jpeg';
        //var prefs = this.getImagePrefs('ImageParameters') || '?slice=,,{sliceZ},{sliceT}&depth=8,d&resize={width},{height},bc,ar&projectmax&format=jpeg';

        prefs = prefs.replace('{sliceZ}', config.sliceZ || 1);
        prefs = prefs.replace('{sliceT}', config.sliceT || 1);
        prefs = prefs.replace('{width}', config.width || 150);
        prefs = prefs.replace('{height}', config.height || 150);
        
        return prefs;
    },
    
    getImagePrefs : function(key)
    {
        if (this.browser.preferences && this.browser.preferences.Images && this.browser.preferences.Images[key])
            return this.browser.preferences.Images[key];
        return '';
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
			if (this.getData('fetched')==1)
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
            imgLoader.src = this.resource.src + this.getImageParams({
                sliceZ : sliceY,
                sliceT : sliceX,
                width : this.layoutMgr.layoutEl.imageWidth,
                height : this.layoutMgr.layoutEl.imageHeight
            });
            
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

Ext.define('Bisque.Resource.Image.Compact',
{
    extend : 'Bisque.Resource.Image',
    
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
	    		autoHide : false,
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
    		BQFactory.request({uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this, ['tags'], true)});
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
    	this.callParent(arguments);
    	
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            });
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },
    
    loadResource : function(data, type)
    {
        if (type=='image')
        {
            this.setData('image', this.GetImageThumbnailRel( 
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            },
            {
                width:data.currentTarget.width,
                height:data.currentTarget.height
            }));
        }
        else
        {
            this.resource.tags = data.tags;
            var geometry = this.resource.find_tags('geometry') || {value:'1,1,1,1,1'};
            this.resource.geometry = geometry.value.split(',');
            
            this.resource.z = parseInt(this.resource.geometry[2]);
            this.resource.t = parseInt(this.resource.geometry[3]);
            this.setData('tags', 'true');
        }

        if (this.getData('tags') && this.getData('image'))
        {
            this.setData('fetched', 1); //Loaded
    
            var renderedRef=this.getData('renderedRef')
            if (renderedRef)
                renderedRef.updateContainer();
        }
    },

    updateContainer : function()
    {
        var text = Ext.String.ellipsis(this.resource.name, 25) || '';
        this.update('<div class="textOnImage" style="width:'+this.layoutMgr.layoutEl.width+'px;">'+text+'</div>'+this.getData('image'));
        this.setLoading(false);
        
        /*this.resizer = Ext.create('Ext.resizer.Resizer', {
            target : this,
            handles : 'all',
            transparent : true
            //pinned  : true
        });*/
    },
});

Ext.define('Bisque.Resource.Image.Card',
{
    extend : 'Bisque.Resource.Image',

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
    	this.callParent(arguments);

        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            });
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type)
    {
        if (type=='image')
            this.setData('image', this.GetImageThumbnailRel( 
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight
            },
            {
                width:data.currentTarget.width,
                height:data.currentTarget.height
            }));
        else
        {
            this.resource.tags = data.tags;

            var tag, tagProp, tagArr=[], tags = this.getSummaryTags();
            
            // Show preferred tags first
            for (var i=0;i<this.resource.tags.length;i++)
            {
                tag = this.resource.tags[i];
                tagProp = new Ext.grid.property.Property({
                                                            name: tag.name,
                                                            value: tag.value
                                                        });
                (tags[tag.name])?tagArr.unshift(tagProp):tagArr.push(tagProp);
            }
            
            this.setData('tags', tagArr.slice(0, 7));
        }

        if (this.getData('tags') && this.getData('image'))
        {
            this.setData('fetched', 1);	//Loaded

            var renderedRef=this.getData('renderedRef')
            if (renderedRef	&& !renderedRef.isDestroyed)
                renderedRef.updateContainer();
        }
    },
    
    getSummaryTags : function()
    {
        if(this.browser.preferences["Summary Tags"])
            return this.browser.preferences["Summary Tags"];

        return {
            "filename" : 0,
            "attached-file" : 0,
            "image_type" : 0,
            "imagedate" : 0,
            "experimenter" : 0,
            "dataset_label" : 0,
            "species" : 0
        };
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

Ext.define('Bisque.Resource.Image.PStrip',
{
    extend:'Bisque.Resource.Image.Compact',

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

Ext.define('Bisque.Resource.Image.PStripBig',
{
    extend:'Bisque.Resource.Image',

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
			//style : 'background-color:#FFF',
		});

		this.data.image=this.GetImageThumbnailAbs(
		{
            width: this.pnlSize.width-10,
            height: this.pnlSize.width-10,
		},
		{
			width: data.currentTarget.width,
			height: data.currentTarget.height
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
				cls : 'white',
				contentEl:imgDiv
			}), resourceTagger]
		}));
            
		this.setLoading(false);
	},
    
    preAfterRender : Ext.emptyFn,
    afterRenderFn : Ext.emptyFn
});

Ext.define('Bisque.Resource.Image.Full',
{
    extend : 'Bisque.Resource.Image',

	constructor : function()
	{
        Ext.apply(this,
        {
            layout:'fit',
        });
		
		this.callParent(arguments);
	},

    prefetch : function(layoutMgr)
    {
    	this.callParent(arguments);
    	
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);	//Loading
            
            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            });
            prefetchImg.onload=Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type)
    {
        if (type=='image')
            this.setData('image', this.GetImageThumbnailAbs(
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight
            },
            {
                width: data.currentTarget.width,
                height: data.currentTarget.height
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
            layout: 'border',
            border: false,
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


Ext.define('Bisque.Resource.Image.Grid',
{
    extend : 'Bisque.Resource.Image',
    
    // convert ArrayStore to JsonStore?
    getFields : function()
    {
        var fields = this.callParent();
        fields[0] = '<img style="height:40px;width:40px;" src='+this.resource.src+'?thumbnail=75,75&format=jpeg />';
        fields[6].height = 48;
        return fields;
    },
});



// Page view for an image
Ext.define('Bisque.Resource.Image.Page',
{
    extend : 'Bisque.Resource.Page',
    
    onResourceRender : function()
    {
        this.setLoading(true);
        this.root = '';
        if (this.resource && this.resource.uri)
            this.root = this.resource.uri.replace(/\/data_service\/.*$/i, '');  
        
        var resourceTagger = Ext.create('Bisque.ResourceTagger', 
        {
            resource : this.resource,
            title : 'Annotations',
        });
    
        var embeddedTagger = Ext.create('Bisque.ResourceTagger', {
            resource : this.resource.src + '?meta',
            title : 'Embedded',
            viewMode : 'ReadOnly',
        });
    
        var mexBrowser = new Bisque.ResourceBrowser.Browser(
        {
            'layout' : 5,
            'title' : 'Analysis',
            'viewMode' : 'MexBrowser',
            'dataset' : this.root+'/data_service/mex',
            'tagQuery' : '"'+this.resource.uri+'"&view=deep',
            'wpublic' : true,
    
            mexLoaded : false,
    
            listeners :
            {
                'browserLoad' : function(me, resQ) {
                    me.mexLoaded = true;
                },
                'Select' : function(me, resource) {
                    window.open(bq.url('/module_service/'+resource.name+'/?mex='+resource.uri));
                },
                scope:this
            },
        });
        
        var resTab = Ext.create('Ext.tab.Panel',
        {
            title : 'Metadata',
    
            region : 'east',
            activeTab : 0,
            border : false,
            bodyBorder : 0,
            collapsible : true,
            split : true,
            width : 400,
            plain : true,
            bodyStyle : 'background-color:#F00',
            items : [resourceTagger, embeddedTagger, mexBrowser]
        });

        var viewerContainer = Ext.create('BQ.viewer.Image', {
            region : 'center',
            resource: this.resource,
        });
    
        this.add({
            xtype : 'container',
            layout : 'border',
            items : [viewerContainer, resTab]
        });
    
        var gobjectTagger = new Bisque.GObjectTagger(
        {
            resource : this.resource,
            imgViewer : viewerContainer.viewer,
            mexBrowser : mexBrowser,
            title : 'Graphical',
            viewMode : 'GObjectTagger',
            listeners :
            {
                'beforeload' : function(me, resource)
                {
                    me.imgViewer.start_wait(
                    {
                        op : 'gobjects',
                        message : 'Fetching gobjects'
                    });
                },
                'onload' : function(me, resource)
                {
                    me.imgViewer.loadGObjects(resource.gobjects, false);
    
                    if(me.mexBrowser.mexLoaded)
                        me.appendFromMex(me.mexBrowser.resourceQueue);
                    else
                        me.mexBrowser.on('browserLoad', function(mb, resQ)
                        {
                            me.appendFromMex(resQ);
                        }, me);
    
                },
                'onappend' : function(me, gobjects)
                {
                    me.imgViewer.gobjectsLoaded(true, gobjects);
                },
    
                'select' : function(me, record, index)
                {
                    var gobject = (record.raw instanceof BQGObject)?record.raw:record.raw.gobjects;
                    me.imgViewer.showGObjects(gobject);
                },
    
                'deselect' : function(me, record, index)
                {
                    var gobject = (record.raw instanceof BQGObject)?record.raw:record.raw.gobjects;
                    me.imgViewer.hideGObjects(gobject);
                }
            }
        });
        resTab.add(gobjectTagger);

        var map = Ext.create('BQ.gmap.GMapPanel3',  {
            title: 'Map',
            url: this.resource.src+'?meta',
            zoomLevel: 16,
            gmapType: 'map',
            autoShow: true,
        });
        resTab.add(map);
        
        // add custom download option to the toolbar
        var menu = this.toolbar.getComponent("btnDownload").menu;
        menu.add([{
            xtype   :   'menuseparator'
        }, {
            xtype   :   'menuitem',
            text    :   'Original image',
            handler :   function() 
                        {
                            window.open(this.resource.src);
                        }
        }]);

        this.setLoading(false);
    }
});