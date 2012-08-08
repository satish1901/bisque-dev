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
                return Ext.create(Bisque.ResourceFactory.baseClass + '.' + layoutKey, config);
            }
        }
    }
})

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
    
    // getFields : returns an array of data used in the grid view
    getFields : function()
    {
        var resource = this.resource;
        return ['', resource.name || '', resource.value || '', resource.resource_type, resource.ts, this, {height:21}]
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
        if (!this.el) return; // dima: not sure what this is but it may not exist
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
    	{
            this.removeCls('LightShadow');
            this.addCls('resource-view-selected')
        }
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
    extend   :'Ext.panel.Panel',
    defaults : { border: false, },
    layout   : 'fit',
        
    constructor : function(config)
    {
        var name = config.resource.name || '';
        var type = config.resource.resource_type || config.resource.type;

        Ext.apply(this,
        {
            //layout  :   'fit',
            border  :   false,
            
            tbar    :   Ext.create('Ext.toolbar.Toolbar', 
                        {
                            defaults    :   {
                                                scale       :   'medium',
                                                scope       :   this,
                                                needsAuth   :   true,
                                            },
                            items       :   this.getOperations(config.resource).concat([
                                                '-', '->',
                                                {
                                                    itemId  :   'btnRename',
                                                    text    :   type + ': <b>' + name + '</b>',
                                                    handler :   this.promptName,
                                                    scope   :   this,
                                                    cls     :   'heading',
                                                }
                                             ])
                        }),
        }, config);
        
        this.callParent(arguments);
        this.toolbar = this.getDockedComponent(0);
        this.testAuth(BQApp.user, false);
        this.addListener('afterlayout', this.onResourceRender, this, {single:true});
    },

    onResourceRender : function() 
    {
        this.setLoading(true);

        var resourceTagger = new Bisque.ResourceTagger(
        {
            itemId      :   'resourceTagger',
            title       :   'Annotations',
            resource    :   this.resource,
            split       :   true,
        });

        this.add(resourceTagger);
        this.setLoading(false);
    },
    
    testAuth : function(user, loaded, permission)
    {
        function disableOperations()
        {
            // user is not authorized
            var tbar = this.getDockedItems('toolbar')[0];
            for (var i=0;i<tbar.items.getCount();i++)
            {
                var cmp = tbar.items.getAt(i);
                if (cmp.needsAuth)
                    cmp.setDisabled(true);
            }
        }

        if (user)
        {
            if (!loaded)
                this.resource.testAuth(user.uri, Ext.bind(this.testAuth, this, [user, true], 0));            
            else
                if (!permission)
                    disableOperations.call(this);
        }
        else if (user===undefined)
            // User autentication hasn't been done yet
            BQApp.on('gotuser', Ext.bind(this.testAuth, this, [false], 1));
        else if (user == null)
            disableOperations.call(this)
    },
    
    getOperations : function(resource)
    {
        var items=[];

        items.push({
            xtype       :   'button',
            text        :   'Download',
            itemId      :   'btnDownload',
            iconCls     :   'icon-download-small',
            needsAuth   :   false,
            compression :   'tar',
            menu        :   {
                                defaults    :   {
                                                    group       :   'downloadGroup',
                                                    groupCls    :   Ext.baseCSSClass + 'menu-group-icon',
                                                    scope       :   this,
                                                    handler     :   this.downloadResource,
                                                    operation   :   this.downloadResource,
                                                },
                                items       :   [{
                                                    xtype       :   'menuitem',
                                                    compression :   'none',
                                                    text        :   'Original file'
                                                }, {
                                                    xtype       :   'menuseparator'
                                                }, {
                                                    compression :   'tar',
                                                    text        :   'as TARball',
                                                },{
                                                    compression :   'gzip',
                                                    text        :   'as GZip archive',
                                                },{
                                                    compression :   'bz2',
                                                    text        :   'as BZip2 archive',
                                                },{
                                                    compression :   'zip',
                                                    text        :   'as (PK)Zip archive',
                                                },]
                            }
        },
        {
            itemId      :   'btnShare',
            text        :   'Share',
            iconCls     :   'icon-group',
            operation   :   this.shareResource,
            handler     :   this.testAuth1
        },
        {
            itemId      :   'btnDelete',
            text        :   'Delete',
            iconCls     :   'icon-delete',
            operation   :   this.deleteResource,
            handler     :   this.testAuth1
        },
        {
            itemId      :   'btnPerm',
            operation   :   this.changePrivacy,
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
        
        return items;
    },
    
    testAuth1 : function(btn, loaded, permission)
    {
        if (loaded!=true)
        {
            var user = BQSession.current_session.user_uri;
            this.resource.testAuth(user, Ext.bind(this.testAuth1, this, [btn, true], 0));            
        }
        else
        {
            if (permission)
                btn.operation.call(this, btn);
            else
                BQ.ui.attention('You do not have permission to perform this action!');
        }
    },
    
    /* Resource operations */

    shareResource : function()
    {
        var shareDialog = Ext.create('BQ.ShareDialog', {
            resource    :   this.resource
        });
    },

    deleteResource : function()
    {
        function success()
        {
            this.setLoading(false);
            
            Ext.MessageBox.show({
                title   :   'Success',
                msg     :   'Resource deleted successfully! You will be redirected to your BISQUE homepage.',
                buttons :   Ext.MessageBox.OK,
                icon    :   Ext.MessageBox.INFO,
                fn      :   function(){window.location = bq.url('/')}
            });
        }
        
        function deleteRes(response)
        {
            if (response == 'yes')
            {
                this.setLoading({msg:'Deleting...'});
                this.resource.delete_(Ext.bind(success, this), Ext.Function.pass(this.failure, ['Delete operation failed!']));
            }
        }
        
        Ext.MessageBox.confirm('Confirm operation', 'Are you sure you want to delete ' + this.resource.name + '?', Ext.bind(deleteRes, this));
    },
    
    renameResource : function(btn, name, authRecord)
    {
        function success(msg)
        {
            BQ.ui.notification(msg);
            var type = this.resource.resource_type || this.resource.type;
            this.toolbar.getComponent('btnRename').setText(type + ': <b>' + (this.resource.name || '') + '</b>');
        }
        
        if (btn == 'ok' && this.resource.name != name) {
            var type = this.resource.resource_type || this.resource.type;
            var successMsg = type + ' <b>' + this.resource.name + '</b> renamed to <b>' + name + '</b>.';
            this.resource.name = name;
            this.resource.save_(undefined, success.call(this, successMsg), Ext.bind(this.failure, this));
        }
    },
    
    downloadResource : function(btn)
    {
        if (btn.compression == 'none')
            this.downloadOriginal();
        else
        {
            var exporter = Ext.create('BQ.Export.Panel');
            exporter.downloadResource(this.resource, btn.compression);
        }
    },
    
    downloadOriginal : function()
    {
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },
    
    changePrivacy : function(btn)
    {
        function loaded(resource)
        {
            resource.permission = (this.resource.permission=='private')?'published':'private';
            resource.append(Ext.bind(success, this), Ext.bind(this.failure, this));
        }
        
        function success(resource)
        {
            // can also broadcast 'reload' event on the resource, once apps start listening to it.
            this.resource.permission = resource.permission;
            var btnPerm = this.toolbar.getComponent('btnPerm');
            btnPerm.setBtnText.call(this, btnPerm);
        };
        
        BQFactory.request({
            uri :   this.resource.uri + '?view=short',
            cb  :   Ext.bind(loaded, this) 
        });
    },
       
    promptName : function(btn)
    {
        Ext.MessageBox.prompt('Rename "' + this.resource.name+'"', 'Please, enter new name:', this.renameResource, this, false, this.resource.name);
    },

    success : function(resource, msg)
    {
        BQ.ui.notification(msg || 'Operation successful.');
    },
    
    failure : function(msg)
    {
        BQ.ui.error(msg || 'Operation failed!');
    },
    
    prefetch : Ext.emptyFn
});

Ext.define('Bisque.Resource.Grid', {
    extend:'Bisque.Resource',
});
