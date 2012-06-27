Bisque.ResourceBrowser.DatasetManager = Ext.extend(Ext.Panel,
{
    constructor : function(configOpts)
    {
        Ext.apply(this,
        {
            selectedDS : null,
            selectedRes : null,
            msgBus : configOpts.msgBus,
            parentCt : configOpts.parentCt,
            browser : configOpts.browser,

            title : 'Datasets',
            itemId: 'datasetCt',
            width : 300,
            autoScroll : true,

            tools : [
            {
                type : 'left',
                text : 'Collapse dataset panel',
                tooltip : 'Collapse dataset panel',
                handler : function()
                {
                    this.parentCt.hideCollapseTool = false;
                    this.parentCt.collapse();
                },

                scope:this
            }],

            tbar : new Ext.Toolbar(
            {
                items : [
                {
                    xtype : 'tbspacer',
                    width : 6
                },
                {
                    text : 'Add Dataset',
                    icon : '/js/ResourceBrowser/Images/add.png',
                    hidden : true,
                    scale : 'medium',
                    iconAlign : 'left',
                    handler : Ext.bind(this.promptDatasetName, this, [false])
                },
                {
                    text : 'Delete Dataset',
                    icon : '/js/ResourceBrowser/Images/delete.png',
                    scale : 'medium',
                    hidden : true,
                    iconAlign : 'left',
                    handler : this.deleteDataset,
                    scope : this
                }]
            })
        });

        this.callParent(arguments);
        this.ManageEvents();

        this.LoadDSList(false);
    },

    LoadDSList : function(loaded, list)
    {
        if (!loaded)
            BQFactory.load('/data_service/dataset/?view=short', callback(this, 'LoadDSList', true));
        else
        {
            for (i = 0; i < list.children.length; i++)
                this.addDataset(list.children[i]);
        }
    },

    addDataset : function(dataset)
    {
        var dsTbar = new Bisque.ResourceBrowser.DatasetManager.DatasetTbar(
        {
            dataset : dataset
        })
        this.add(dsTbar);
        this.relayEvents(dsTbar, ['datasetLoad']);
    },

    deleteDataset : function()
    {
        if (this.selectedDS)
        {
            this.selectedDS.deleteDS();
            this.selectedDS = null;
            var uri =
            {
                offset : 0,
                baseURL : '/data_service/image'
            };

            this.msgBus.fireEvent('Browser_ReloadData', uri);
        }
    },

    promptDatasetName : function(loaded, btn, name)
    {
        Ext.MessageBox.prompt('Create new dataset', 'Dataset name:', this.createDataset, this);
    },

    createDataset : function(btn, name)
    {
        if (btn == 'ok')
        {
            var dataset = new BQDataset();
            dataset.name = name;
            dataset.save_(undefined, callback(this, 'addDataset'));
        }
    },

    ManageEvents : function()
    {
        this.on('datasetLoad', function(opts)
        {
            if (this.selectedDS)
                this.selectedDS.removeCls('DS-Tbar-HLite');
            if (this.selectedDS==opts.ct)
            {
                this.selectedDS = null;
                var uri =
                {
                    offset : 0,
                    baseURL : '/data_service/image'
                };

                document.title='Dataset: Images';
	            this.msgBus.fireEvent('DatasetUnselected');
                this.msgBus.fireEvent('Browser_ReloadData', uri);
            }
            else
            {
                this.selectedDS = opts.ct;
                document.title='Dataset: '+this.selectedDS.dataset.name;
                this.selectedDS.addClass('DS-Tbar-HLite');

	            this.msgBus.fireEvent('DatasetSelected', this.selectedDS.dataset);

                opts.ct.dataset.getMembers(callback(this,'ChangeDataset'));
            }
        }, this);

        this.msgBus.on('ResSelectionChange', function(selection)
        {
            this.selectedRes = selection;
        }, this);

    },

    ChangeDataset : function(data)
    {
        if (data.length!=0)
        {
            var uri =
            {
                offset : 0,
                baseURL : data.uri+'/value'
            };

            this.msgBus.fireEvent('Browser_ReloadData', uri);
        }
    }
});

Bisque.ResourceBrowser.DatasetManager.DatasetTbar = Ext.extend(Ext.Toolbar,
{
    constructor : function(configOpts)
    {
        Ext.apply(this,
        {
            layout:'hbox',
            height: 44,
            layoutConfig:
            {
                align:'middle'
            },
            dataset : configOpts.dataset,
            menuClicked : false,
            cls : 'DS-Tbar',
            items :
            [
            {
                xtype : 'tbspacer',
                width : 6
            },
            {
                text : Ext.String.ellipsis(configOpts.dataset.name, 35),
                overCls :'',
                pressedCls:'',
                handler : this.datasetLoad,
                scope : this
            },
            {
                text : ' ', 
                scale : 'medium',
                overCls :'',
                pressedCls:'',
                flex:1,
                handler : this.datasetLoad,
                scope : this
            },
            {
                text : 'Options',
                icon : '/js/ResourceBrowser/Images/menu.png',
                scale : 'medium',
                hidden : true,
                iconAlign : 'left',
                handler : this.showMenu,
                scope : this
            }
            ],
            contextMenu : new Ext.menu.Menu(
            {
                items : [
                {
                    text : 'Add selection to dataset',
                    handler : this.addRes,
                    scope : this
                },
                {
                    text : 'Add query result to dataset',
                    handler : this.addResFromQuery,
                    scope : this
                }, '-',
                {
                    text : 'Remove selection from dataset'
                }]
            })
        });

        this.callParent(arguments);
    },

    showMenu : function(btn)
    {
        this.contextMenu.showBy(btn.getEl());
    },

    addRes : function()
    {
        if (this.ownerCt.selectedRes)
        {
            var members = [];
            for (var i = 0; i < this.ownerCt.selectedRes.length; i++) {
                members.push(new Value('object', this.ownerCt.selectedRes[i]));
            }
            this.dataset.appendMembers(members, callback(this, function()
            {
                this.dataset.save_(undefined, callback(this, 'datasetLoad'));
            }));
        }
    },
    
    addResFromQuery : function()
    {
    	var resQ=this.ownerCt.browser.resourceQueue;
		var members = [];
        for (var i = 0; i < resQ.length; i++) {
			members.push(new Value('object', resQ[i].resource.uri));
		}
        
		this.dataset.appendMembers(members, callback(this, function()
		{
			this.dataset.save_(undefined, callback(this, 'datasetLoad'));
		}));
    },

    datasetLoad : function()
    {
        this.fireEvent('datasetLoad',
        {
            ct : this
        });
    },

    deleteDS : function()
    {
        this.dataset.delete_();
        this.removeAll(true);
        this.destroy();
    }
});