// Declare namespace for the modules in RecourseBrowser package
Ext.namespace('Bisque.ResourceBrowser');
Ext.require(['Ext.tip.*']);
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
        config = config ||
        {
        };
        config.height = config.height || '85%';
        config.width = config.width || '85%';
        config.selType = config.selType || 'MULTI';
        config.showOrganizer = ('showOrganizer' in config)? config.showOrganizer: true;

        var bodySz = Ext.getBody().getViewSize();
        var height = parseInt((config.height.toString().indexOf("%") == -1) ? config.height : (bodySz.height * parseInt(config.height) / 100));
        var width = parseInt((config.width.toString().indexOf("%") == -1) ? config.width : (bodySz.width * parseInt(config.width) / 100));

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

        this.dockedItems = [
        {
            xtype : 'toolbar',
            dock : 'bottom',
            layout :
            {
                type : 'hbox',
                align : 'middle',
                pack : 'center'
            },
            padding : 10,

            items : [
            {
                xtype : 'buttongroup',
                margin : 5,
                items : [
                {
                    text : 'Select',
                    iconCls : 'icon-select',
                    scale : 'medium',
                    width : 90,
                    handler : this.btnSelect,
                    scope : this
                }]
            },
            {
                xtype : 'buttongroup',
                margin : 5,
                items : [
                {
                    text : 'Cancel',
                    iconCls : 'icon-cancel',
                    textAlign : 'left',
                    scale : 'medium',
                    width : 90,
                    handler : this.destroy,
                    scope : this
                }]
            }]
        }];

        this.callParent([arguments]);

        // Relay all the custom ResourceBrowser events to this Window
        //this.relayEvents(this.getComponent(0), ['Select']);

        this.browser = this.getComponent(0);
        this.browser.on('Select', function(resourceBrowser, resource)
        {
            this.destroy();
        }, this);


        this.show();
    },

    btnSelect : function()
    {
        var selectedRes = this.browser.resourceQueue.selectedRes;
        var selection = Ext.Object.getValues(selectedRes);

        if (selection.length)
            if (selection.length==1)
                this.browser.fireEvent('Select', this, selection[0].resource);
            else
            {
                for (var i=0, selectRes=[]; i<selection.length; i++)
                    selectRes.push(selection[i].resource);
                this.browser.fireEvent('Select', this, selectRes);
            }
        else
            BQ.ui.message('Selection empty!', 'Please select an image or press cancel to abort.');
    },
});

// Bisque.QueryBrowser.Dialog is a query select specialization of Bisque.ResourceBrowser.Dialog
Ext.define('Bisque.QueryBrowser.Dialog', {
    extend : 'Bisque.ResourceBrowser.Dialog',

    btnSelect : function() {
        var query = this.browser.commandBar.getComponent('searchBar').getValue();
        if (query && query.length>1)
            this.browser.fireEvent('Select', this, query);
        else
            BQ.ui.message('Query is empty!', 'Please type a query or press cancel to abort.');
    },
});

// ResourceBrowser in a Ext.Panel container
Ext.define('Bisque.ResourceBrowser.Browser',
{
    extend : 'Ext.panel.Panel',

    constructor : function(config)
    {
        //Prefetch the loading spinner
        var imgSpinner = new Image();
        imgSpinner.src = bq.url('/js/ResourceBrowser/Images/loading.gif');

        this.westPanel = new Ext.panel.Panel(
        {
            region : 'west',
            split : true,
            layout : 'fit',
            cls: 'organizer',
            frame : true,
            header : false,
            hidden : true,
            collapsible: true,
            hideCollapseTool : true,
            listeners : {
                'beforecollapse' : function(me)
                {
                    me.setTitle(me.getComponent(0).title);
                },
            }
        });

        this.centerPanel = new Ext.Panel(
        {
            region : 'center',
            border : false,
            layout : 'fit',
        });
        config = config || {};

        Ext.apply(this,
        {
            browserParams : config,
            layoutKey : parseInt(config.layout),
            viewMgr : Ext.create('Bisque.ResourceBrowser.viewStateManager', config.viewMode),
            organizerCt : null,
            datasetCt : null,
            layoutMgr : null,
            browserState : {},
            resourceQueue : [],
            msgBus : new Bisque.Misc.MessageBus(),
            gestureMgr : null,
            showGroups : false,
            preferenceKey : 'ResourceBrowser',
            
            //bodyCls : 'background-transparent',
            bodyCls : 'browser-main',
            // Panel related config
            border : false,
            title : config.title || '',
            layout : 'border',
            items : [this.westPanel, this.centerPanel],
            listeners : config.listeners || {},
        }, config);

        this.commandBar = new Bisque.ResourceBrowser.CommandBar(
        {
            browser : this
        });
        this.tbar = this.commandBar;

        this.callParent([arguments]);

        this.loadPreferences();

        if(Ext.supports.Touch)
            this.gestureMgr = new Bisque.Misc.GestureManager();
    },

    loadPreferences : function(preferences, tag)
    {
        if(preferences == undefined)
            BQ.Preferences.get(
            {
                type : 'user',
                key : this.preferenceKey,
                callback : Ext.bind(this.loadPreferences, this)
            });
        else
        // preferences loaded
        {
            this.preferences = preferences;
            this.applyPreferences();

            // defaults (should be loaded from system preferences)
            Ext.apply(this.browserParams,
            {
                layout : this.browserParams.layout || 1,
                dataset : this.browserParams.dataset || '/data_service/image/',
                offset : this.browserParams.offset || 0,
                tagQuery : this.browserParams.tagQuery || '',
                tagOrder : this.browserParams.tagOrder || '"@ts":desc',
                wpublic : (this.browserParams.wpublic == 'true' ? true : false),
                selType : (this.browserParams.selType || 'SINGLE').toUpperCase()
            });

            this.browserState['offset'] = this.browserParams.offset;
            this.layoutKey = this.layoutKey || this.browserParams.layout;
            //this.showOrganizer = true;
            //if ('showOrganizer' in this.browserParams) 
            this.showOrganizer = this.browserParams.showOrganizer || false;
            this.selectState = this.browserParams.selectState || 'ACTIVATE';
            this.commandBar.applyPreferences();

            if (this.browserParams.dataset!="None")
            {
                this.loadData(
                {
                    baseURL : this.browserParams.dataset,
                    offset : this.browserParams.offset,
                    tag_query : this.browserParams.tagQuery,
                    tag_order : this.browserParams.tagOrder
                });
                
                var btnOrganize = this.commandBar.getComponent("btnGear").menu.getComponent("btnOrganize");
                this.showOrganizer?btnOrganize.handler.call(this.commandBar):'';
            }
        }
    },

    applyPreferences : function()
    {
        var browserPref = this.preferences.Browser;

        // Browser preferences
        if(browserPref != undefined && !this.browserParams.viewMode)
        {
            this.browserParams.tagQuery = this.browserParams.tagQuery || browserPref["Tag Query"];
            this.layoutKey = parseInt(this.browserParams.layout || Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS[browserPref["Layout"]]);
            this.browserParams.wpublic = (browserPref["Include Public Resources"] == undefined) ? this.browserParams.wpublic : browserPref["Include Public Resources"];
        }
    },

    loadData : function(uri)
    {
        this.loading = true;
        this.on('afterlayout', function(me){
            me.centerPanel.setLoading(me.loading);
        });
        
        this.centerPanel.setLoading(
        {
            msg : ''
        });
        uri = uri || null;

        if (uri)
        {
            if(uri.tag_query == undefined)
                uri.tag_query = this.browserState.tag_query || '';
            if(uri.tag_order == undefined)
                uri.tag_order = this.browserState.tag_order || '';
            if(uri.offset == undefined)
                uri.offset = this.browserState.offset;

            if(!uri.baseURL)
                uri.baseURL = this.browserState.baseURL;

            uri.wpublic = this.browserParams.wpublic

            function checkTS(tagOrder)
            {
                if (tagOrder.indexOf('@ts')==-1)
                {
                    var ts = this.commandBar.getComponent("btnTS").sortState;
                    tagOrder += (tagOrder) ? ',' : '';
                    tagOrder += (ts=='ASC') ? '"@ts":asc' : '"@ts":desc';
                }
                
                return tagOrder;
            }
            
            uri.tag_order = checkTS.call(this, uri.tag_order);

            this.setBrowserState(uri);
        }
        else
            var uri = this.getURIFromState();

        if(uri.tag_order)
        {
            var tagValuePair = uri.tag_order.split(','), tags = [], values = [], nextPair;

            function unquote(string)
            {
                return (string.length < 2) ? string : string.substring(1, string.length - 1);
            }

            for(var i = 0; i < tagValuePair.length; i++)
            {
                nextPair = tagValuePair[i].split(':');

                if(unquote(nextPair[0]) != "@ts")
                {
                    tags.push(unquote(nextPair[0]));
                    values.push(nextPair[1].toUpperCase());
                }
            }

            uri.view = tags.join(',');
            if(tags.length >= 1)
                this.showGroups =
                {
                    tags : tags,
                    order : values
                };
        }
        else
            //this.showGroups is used in LayoutFactory to group resources based on tag order
            this.showGroups = false;

        function loadQueue(membersTag)
        {
            if (membersTag)
                this.uri.baseURL = membersTag.uri + '/value'; 
                this.browserState['baseURL'] = this.uri.baseURL;                
                
            for(var param in this.uri)
                if(this.uri[param].length == 0)
                    delete this.uri[param];
    
            this.resourceQueue = new Bisque.ResourceBrowser.ResourceQueue(
            {
                callBack : callback(this, 'dataLoaded'),
                browser : this,
                uri : this.uri
            });
        }

        this.uri = uri;
        // if baseURL is typeof BQResource (BQDataset etc.) then load its members
        if (uri.baseURL instanceof BQDataset)
            uri.baseURL.getMembers(Ext.bind(loadQueue, this));
        else
            loadQueue.call(this);
    },

    dataLoaded : function()
    {
        function doLayout()
        {
            this.ChangeLayout(this.layoutKey);

            if(!this.eventsManaged)
                this.ManageEvents();
        }

        this.fireEvent('browserLoad', this, this.resourceQueue);

        if(this.rendered)
            doLayout.call(this);
        else
            this.on('afterlayout', Ext.bind(doLayout, this),
            {
                single : true
            });
    },

    ChangeLayout : function(newLayoutKey, direction)
    {
        //console.time("Browser - ChangeLayout");
        this.loading = false;
        this.centerPanel.setLoading(this.loading);

        direction = direction || 'none';

        if(this.layoutMgr)
            this.layoutMgr.destroy();

        this.layoutKey = newLayoutKey == -1 ? this.layoutKey : newLayoutKey;

        this.layoutMgr = Bisque.ResourceBrowser.LayoutFactory.getLayout(
        {
            browser : this,
            direction : direction
        });

        this.resourceQueue.changeLayout(
        {
            key : this.layoutKey,
            layoutMgr : this.layoutMgr
        });

        this.layoutMgr.Init(this.resourceQueue.getMainQ(this.layoutMgr.getVisibleElements(direction), this.layoutMgr));
        this.centerPanel.add(this.layoutMgr);

        this.updateTbarItemStatus();

        //console.timeEnd("Browser - ChangeLayout");
    },

    /* Custom ResourceBrowser event management */
    ManageEvents : function()
    {
        this.eventsManaged = true;
        this.addEvents('Select');
        this.changeLayoutThrottled = Ext.Function.createThrottled(this.ChangeLayout, 400, this);
        this.centerPanel.on('resize', Ext.bind(this.ChangeLayout, this, [-1]));
        
        this.centerPanel.getEl().on('mousewheel', function(e)
        {
            if (this.layoutMgr.key!=Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Full)
            {
                if(e.getWheelDelta()>0)
                {
                    var btnLeft = this.commandBar.getComponent("btnLeft");
                    if(!btnLeft.disabled)
                        btnLeft.handler.call(btnLeft.scope, btnLeft);
                }
                else
                {
                    var btnRight = this.commandBar.getComponent("btnRight");
                    if(!btnRight.disabled)
                        btnRight.handler.call(btnRight.scope, btnRight);
                }
            }
        }, this);

        Ext.create('Ext.util.KeyMap',
        {
            target  :   Ext.getDoc(),
            binding :   [{
                            key                 :   "aA",
                            ctrl                :   true,
                            handler             :   function(key, e)
                                                    {
                                                        this.layoutMgr.toggleSelectAll();
                                                    },
                            defaultEventAction  :   'stopEvent',
                            scope               :   this
                        }]
        });

        this.msgBus.mon(this.msgBus,
        {
            'ResourceDblClick' : function(resource)
            {
                if(this.browserParams.selType == 'MULTI' && this.selectState == 'ACTIVATE')
                    this.fireEvent('Select', this, resource);
            },

            'ResourceSingleClick' : function(resource)
            {
                if(this.browserParams.selType == 'SINGLE' && this.selectState == 'ACTIVATE')
                    this.fireEvent('Select', this, resource);
            },

            'Browser_ReloadData' : function(uri)
            {
                //var btnOrganize = this.commandBar.getComponent("btnGear").menu.getComponent("btnOrganize");
                //this.showOrganizer?btnOrganize.handler.call(this.commandBar, true):'';

                if(uri == "")
                {
                    this.resourceQueue = new Bisque.ResourceBrowser.ResourceQueue(
                    {
                        callBack : callback(this, 'ChangeLayout', this.layoutKey),
                        browser : this,
                        uri : ""
                    });
                }
                else if(uri == 'ReloadPrefs')
                {
                    var user = BQSession.current_session.user;

                    if(user)
                    {
                        BQ.Preferences.reloadUser(user);
                        this.browserParams =
                        {
                        };
                        this.loadPreferences();
                    }
                }
                else
                    this.loadData(uri);
            },

            scope : this
        });

        // HTML5 Gestures (iPad/iPhone/Android etc.)
        if(this.gestureMgr)
            this.gestureMgr.addListener(
            {
                dom : this.centerPanel.getEl().dom,
                eventName : 'swipe',
                listener : Ext.bind(function(e, params)
                {
                    if(params.direction == "left")
                    {
                        var btnRight = this.commandBar.getComponent("btnRight");
                        if(!btnRight.disabled)
                            btnRight.handler.call(btnRight.scope, btnRight);
                    }
                    else
                    {
                        var btnLeft = this.commandBar.getComponent("btnLeft");
                        if(!btnLeft.disabled)
                            btnLeft.handler.call(btnLeft.scope, btnLeft);
                    }
                }, this),

                options :
                {
                    swipeThreshold : 100
                }
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
        var btnRight = this.commandBar.getComponent("btnRight"), btnLeft = this.commandBar.getComponent("btnLeft");
        var st = this.resourceQueue.getStatus();

        this.commandBar.setStatus(st);

        btnLeft.setDisabled(st.left || st.loading.left);
        btnRight.setDisabled(st.right || st.loading.right);
        
        this.commandBar.slider.slider.setDisabled(btnLeft.disabled && btnRight.disabled);
        this.commandBar.btnTSSetState(this.browserState.tag_order.toLowerCase());
        this.commandBar.btnSearchSetState(this.browserState.tag_query);
        this.commandBar.btnActivateSetState(this.selectState);
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

        for(var param in uri)
        if(uri[param].length == 0)
            delete uri[param];

        return uri;
    },
    
    findRecord : function(uri)
    {
        return this.resourceQueue.find(uri);
    }
});
