Ext.define('Bisque.ResourceBrowser.CommandBar', {
    extend : 'Ext.toolbar.Toolbar',

    constructor : function(configOpts) {
        this.viewMgr = configOpts.browser.viewMgr;
        this.slider = new Bisque.Misc.Slider({
            hidden : this.viewMgr.cBar.slider
        });

        Ext.apply(this, {
            browser : configOpts.browser,
            taqQuery : configOpts.browser.browserParams.tagQuery,

            msgBus : configOpts.browser.msgBus,
            westPanel : configOpts.browser.westPanel,
            organizerCt : configOpts.browser.organizerCt,
            datasetCt : configOpts.browser.datasetCt,
            hidden : configOpts.browser.viewMgr.cBar.cbar,

            layout : {
                type : 'hbox',
                align : 'middle'
            },
            items : [{
                xtype : 'tbspacer',
                width : 6
            }, {
                xtype : 'textfield',
                tooltip : 'Enter a tag query here',
                itemId : 'searchBar',
                flex : 7,
                scale : 'large',
                height : 25,
                boxMinWidth : 100,
                hidden : this.viewMgr.cBar.searchBar,
                value : configOpts.tagQuery,
                listeners : {
                    specialkey : {
                        fn : function(field, e) {
                            if (e.getKey() == e.ENTER)
                                this.btnSearch();
                        },

                        scope : this
                    },
                    scope : this,
                    focus : function(c) {
                        var tip = Ext.create('Ext.tip.ToolTip', {
                            target : c.el,
                            anchor : 'top',
                            minWidth : 500,
                            width : 500,
                            autoHide : true,
                            dismissDelay : 20000,
                            shadow : true,
                            autoScroll : true,
                            loader : {
                                url : '/html/querying.html',
                                renderer : 'html',
                                autoLoad : true
                            },
                        });
                        tip.show();
                    },
                }
            }, {
                icon : bq.url('/js/ResourceBrowser/Images/search.png'),
                hidden : this.viewMgr.cBar.searchBar,
                tooltip : 'Search',
                scale : 'large',
                handler : this.btnSearch,
                scope : this
            }, {
                xtype : 'tbseparator',
                hidden : this.viewMgr.cBar.searchBar
            }, {
                itemId : 'btnThumb',
                icon : bq.url('/js/ResourceBrowser/Images/thumb.png'),
                hidden : this.viewMgr.cBar.btnLayoutThumb,
                tooltip : 'Thumbnail layout',
                toggleGroup : 'btnLayout',
                scale : 'large',
                handler : this.btnLayoutClick,
                padding : '3 0 3 0',
                scope : this
            }, {
                itemId : 'btnGrid',
                icon : bq.url('/js/ResourceBrowser/Images/grid.png'),
                hidden : this.viewMgr.cBar.btnLayoutGrid,
                tooltip : 'Grid layout',
                scale : 'large',
                toggleGroup : 'btnLayout',
                handler : this.btnLayoutClick,
                padding : '3 0 3 0',
                scope : this
            }, {
                itemId : 'btnCard',
                icon : bq.url('/js/ResourceBrowser/Images/card.png'),
                hidden : this.viewMgr.cBar.btnLayoutCard,
                tooltip : 'Card layout',
                scale : 'large',
                toggleGroup : 'btnLayout',
                handler : this.btnLayoutClick,
                padding : '3 0 3 0',
                scope : this
            }, {
                itemId : 'btnFull',
                icon : bq.url('/js/ResourceBrowser/Images/full.png'),
                hidden : this.viewMgr.cBar.btnLayoutFull,
                tooltip : 'Full layout',
                scale : 'large',
                toggleGroup : 'btnLayout',
                handler : this.btnLayoutClick,
                padding : '3 0 3 0',
                scope : this
            }, '->', {
                itemId : 'btnRefresh',
                icon : bq.url('/js/ResourceBrowser/Images/refresh.png'),
                tooltip : 'Refresh browser',
                hidden : this.viewMgr.cBar.btnRefresh,
                scale : 'large',
                handler : this.btnRefresh,
                scope : this
            }, {
                itemId : 'btnActivate',
                //icon : bq.url('/js/ResourceBrowser/Images/activate.png'),
                text: 'Edit',
                tooltip : 'Switch to editing mode',
                state : 'ACTIVATE',
                hidden : this.viewMgr.cBar.btnActivate,
                scale : 'large',
                handler : this.btnActivate,
                scope : this,
                cls: 'bq-btn-edit',
            }, {
                itemId : 'btnTS',
                icon : bq.url('/js/ResourceBrowser/Images/desc.png'),
                tooltip : 'Sort data ascending by timestamp (current: descending)',
                hidden : this.viewMgr.cBar.btnTS,
                sortState : 'DESC',
                scale : 'large',
                handler : this.btnTS,
                scope : this
            }, {
                xtype : 'tbseparator',
                hidden : this.viewMgr.cBar.btnTS
            }, {
                tooltip : 'Load more data',
                itemId : 'btnLeft',
                icon : bq.url('/js/ResourceBrowser/Images/left.png'),
                hidden : this.viewMgr.cBar.btnLeft,
                scale : 'large',
                padding : '0 1 0 0',
                handler : function(me) {
                    //me.stopAnimation();
                    //me.el.frame("#B0CEF7");
                    this.browser.resourceQueue.loadPrev(this.browser.layoutMgr.getVisibleElements('left'/*direction:left*/));
                    this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
                },
                scope : this
            }, {
                tooltip : 'Load more data',
                itemId : 'btnRight',
                icon : bq.url('/js/ResourceBrowser/Images/right.png'),
                hidden : this.viewMgr.cBar.btnRight,
                scale : 'large',
                padding : '0 0 0 1',
                handler : function(me) {
                    //me.stopAnimation();
                    //me.el.frame("#B0CEF7");
                    this.browser.resourceQueue.loadNext();
                    this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
                },

                scope : this
            }, this.slider, {
                xtype : 'tbseparator',
                hidden : this.viewMgr.cBar.btnGear
            }, {
                icon : bq.url('/js/ResourceBrowser/Images/gear.png'),
                hidden : this.viewMgr.cBar.btnGear,
                itemId : 'btnGear',
                scale : 'large',
                tooltip : 'Options',
                menu : {
                    items : [{
                        text : 'Include public resources',
                        itemId : 'btnWpublic',
                        checked : false,
                        listeners : {
                            checkchange : {
                                fn : function(chkbox, value) {
                                    var uri = {
                                        offset : 0
                                    };
                                    configOpts.browser.browserParams.wpublic = value;
                                    configOpts.browser.msgBus.fireEvent('Browser_ReloadData', uri);
                                },
                                scope : this
                            }
                        }
                    }, '-', {
                        text : 'Organize',
                        itemId : 'btnOrganize',
                        icon : bq.url('/js/ResourceBrowser/Images/organize.png'),
                        hidden : true,
                        handler : this.btnOrganizerClick,
                        scope : this
                    }, {
                        text : 'Datasets',
                        icon : bq.url('/js/ResourceBrowser/Images/datasets.png'),
                        hidden : true, //this.viewMgr.cBar.btnDataset,
                        handler : this.btnDatasetClick,
                        scope : this
                    }, {
                        text : 'Link',
                        icon : bq.url('/js/ResourceBrowser/Images/link.png'),
                        hidden : this.viewMgr.cBar.btnLink,
                        handler : function() {
                            var val = configOpts.browser.resourceQueue.uriStateToString(configOpts.browser.getURIFromState());

                            Ext.Msg.show({
                                title : 'Link to this view',
                                msg : 'Bisque URL:',
                                modal : true,
                                prompt : true,
                                width : 500,
                                buttons : Ext.MessageBox.OK,
                                icon : Ext.MessageBox.INFO,
                                value : val
                            });
                        }
                    }]
                }
            }, {
                xtype : 'tbspacer',
                flex : 0.2,
                maxWidth : 20
            }]
        });

        Bisque.ResourceBrowser.CommandBar.superclass.constructor.apply(this, arguments);

        this.manageEvents();
    },

    manageEvents : function() {
        this.msgBus.on('SearchBar_Query', function(query) {
            this.getComponent('searchBar').setValue(decodeURIComponent(query));
        }, this);

        this.mon(this, 'afterlayout', this.toggleLayoutBtn, this);

        this.slider.on('buttonClick', Ext.Function.createThrottled(function(newOffset) {
            var oldOffset = this.browser.resourceQueue.rqOffset + this.browser.resourceQueue.dbOffset.left;
            var diff = newOffset - oldOffset;

            if (diff > 0) {
                this.browser.resourceQueue.loadNext(diff);
                this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Right');
            } else if (diff < 0) {
                this.browser.resourceQueue.loadPrev(-1 * diff);
                this.browser.changeLayoutThrottled(this.browser.layoutKey, 'Left');
            }
        }, 400, this), this);

    },

    btnRefresh : function() {
        this.browser.msgBus.fireEvent('Browser_ReloadData', {});
    },

    btnActivate : function(btn) {
        if (btn.state == 'ACTIVATE') {
            btn.setIcon(bq.url('/js/ResourceBrowser/Images/select.png'));
            btn.state = 'SELECT';
            btn.setTooltip('Switch to view mode');
            btn.addCls('active');
        } else {
            btn.setIcon(bq.url('/js/ResourceBrowser/Images/activate.png'));
            btn.state = 'ACTIVATE';
            btn.setTooltip('Switch to editing mode');
            btn.removeCls('active');
        }
        this.browser.selectState = btn.state;
        this.browser.fireEvent('SelectMode_Change', btn.state);
    },

    btnTS : function(btn) {
        var tagOrder = cleanTagOrder(this.browser.browserState.tag_order) || '';

        function cleanTagOrder(tagOrder) {
            var ind = tagOrder.lastIndexOf('"@ts":desc')
            if (ind != -1)
                return tagOrder.slice(0, ind);

            ind = tagOrder.lastIndexOf('"@ts":asc');
            if (ind != -1)
                return tagOrder.slice(0, ind);

            return tagOrder;
        }


        (tagOrder.length != 0) ? ((tagOrder[tagOrder.length - 1] != ',') ? tagOrder += ',' : "") : "";

        if (btn.sortState == 'ASC') {
            btn.setIcon(bq.url('/js/ResourceBrowser/Images/desc.png'));
            btn.sortState = 'DESC';
            btn.setTooltip('Sort data ascending by timestamp (current: descending)');
            tagOrder += '"@ts":desc';
        } else {
            btn.setIcon(bq.url('/js/ResourceBrowser/Images/asc.png'));
            btn.sortState = 'ASC';
            btn.setTooltip('Sort data descending by timestamp (current: ascending)');
            tagOrder += '"@ts":asc';
        }

        this.msgBus.fireEvent('Browser_ReloadData', {
            offset : 0,
            tag_order : tagOrder
        });
    },

    btnSearch : function() {
        var uri = {
            offset : 0,
            tag_query : this.getComponent('searchBar').getValue()
        };
        this.msgBus.fireEvent('Browser_ReloadData', uri);
    },

    btnDatasetClick : function() {
        this.westPanel.removeAll(false);

        this.datasetCt = this.datasetCt || new Bisque.ResourceBrowser.DatasetManager({
            parentCt : this.westPanel,
            browser : this.browser,
            msgBus : this.msgBus
        });

        this.westPanel.setWidth(this.datasetCt.width).show().expand();
        this.westPanel.add(this.datasetCt);
        this.westPanel.doComponentLayout(null, null, true);
    },

    btnOrganizerClickOriginal : function(reload) {
        this.westPanel.setWidth(420).show().expand();
        //this.westPanel.queryById('organizer').removeAll(false); //this.westPanel.removeAll(false);
        this.organizerCt = ( reload ? undefined : this.organizerCt) || new Bisque.ResourceBrowser.Organizer({
            border: 1,
            itemId: 'organizer',
            parentCt : this.westPanel,
            dataset : this.browser.browserState['baseURL'],
            wpublic : this.browser.browserParams.wpublic,
            browser : this.browser,
            msgBus : this.msgBus
        });

        //this.westPanel.setWidth(this.organizerCt.width).show().expand();
        this.westPanel.add(this.organizerCt);
        this.westPanel.doComponentLayout(null, null, true);
    },

    btnOrganizerClickTree : function(reload) {
        this.westPanel.setWidth(420).show().expand();
        //this.westPanel.queryById('organizer').removeAll(false);
        this.organizerCt = ( reload ? undefined : this.organizerCt) || Ext.create('BQ.Organizer.Tree', {
            itemId: 'organizer',
            listeners : {
                scope : this,
                'QUERY_CHANGED' : function(uri) {
                    this.msgBus.fireEvent('Browser_ReloadData', uri);
                }
            },
            // state variables
            tagList : ['habitat', 'Plant Structure', 'Genus', 'species'],
            resourceType : '', //this.browser.browserState['baseURL'].split('/')[2],
            resourceServer : this.browser.browserState['baseURL'], //.split('/')[1],
            includePublic : this.browser.browserParams.wpublic,
        });
        this.westPanel.add(this.organizerCt);
    },

    btnOrganizerClickFiles : function(reload) {
        this.westPanel.setWidth(420).show().expand();
        //this.westPanel.queryById('files').removeAll(false);
        this.westPanel.add({
            xtype: 'bq-tree-files-panel',
            itemId: 'files',
            title: 'Files',
            listeners : {
                scope : this,
                selected : function(url) {
                    this.msgBus.fireEvent('Browser_ReloadData', {
                        baseURL : url.slice(-1)!=='/' ? url+'/value' : url+'value',
                        offset : 0,
                        tag_query : '',
                        tag_order : '',
                        wpublic : false,
                    });
                }
            },
        });
    },

    btnOrganizerClick : function(reload) {
        // dima: choose type of organizer here
        //this.btnOrganizerClickTree(reload);
        this.btnOrganizerClickOriginal(reload);
        this.btnOrganizerClickFiles(reload);
    },

    btnLayoutClick : function(item) {
        switch (item.itemId) {
            case 'btnThumb' :
                this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact);
                break;
            case 'btnCard' :
                this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Card);
                break;
            case 'btnGrid' :
                this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Grid);
                break;
            case 'btnFull' :
                this.browser.changeLayoutThrottled(Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Full);
                break;
        }
    },

    toggleLayoutBtn : function() {
        switch(this.browser.layoutKey) {
            case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Compact :
                this.getComponent('btnThumb').toggle(true, false);
                break;
            case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Card :
                this.getComponent('btnCard').toggle(true, false);
                break;
            case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Grid :
                this.getComponent('btnGrid').toggle(true, false);
                break;
            case Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Full :
                this.getComponent('btnFull').toggle(true, false);
                break;
        }
    },

    btnActivateSetState : function(state) {
        var btn = this.getComponent('btnActivate');
        btn.state = (state == 'ACTIVATE') ? 'SELECT' : 'ACTIVATE';
        this.btnActivate(btn);
    },

    btnTSSetState : function(tagOrder) {
        var sortState = (tagOrder.indexOf('"@ts":desc') != -1) ? 'DESC' : ((tagOrder.indexOf('"@ts":asc') != -1) ? 'ASC' : '');
        var btn = this.getComponent('btnTS');

        if (btn.sortState != sortState)
            if (sortState == 'DESC') {
                btn.setIcon(bq.url('/js/ResourceBrowser/Images/desc.png'));
                btn.sortState = 'DESC';
                btn.setTooltip('Sort data ascending by timestamp (current: descending)');
            } else {
                btn.setIcon(bq.url('/js/ResourceBrowser/Images/asc.png'));
                btn.sortState = 'ASC';
                btn.setTooltip('Sort data descending by timestamp (current: ascending)');
            }
    },

    btnSearchSetState : function(tagQuery) {
        this.getComponent('searchBar').setValue(decodeURIComponent(tagQuery));
    },

    setStatus : function(status) {
        if (this.slider.rendered)
            this.slider.setStatus(status);
    },

    applyPreferences : function() {
        if (this.rendered)
            this.toggleLayoutBtn();
        this.getComponent('btnGear').menu.getComponent('btnWpublic').setChecked(this.browser.browserParams.wpublic, true);
    }
});