/* Abstract Dataset resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Dataset', {
    extend : 'Bisque.Resource',
    operationBarClass: 'Bisque.ResourceBrowser.OperationBar.dataset',

    initComponent : function() {
        this.addCls('dataset');
        this.callParent();
    },

    afterRenderFn : function() {
        this.setData('renderedRef', this);

        if (this.getData('fetched') == 1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Dataset.Compact', {
    extend : 'Bisque.Resource.Dataset',

    constructor : function() {
        Ext.apply(this, {
            layout : {
                type : 'vbox',
                align : 'stretch'
            }
        });
        this.callParent(arguments);
        this.addCls('compact');
    },

    prefetch : function(layoutMgr) {
        this.callParent(arguments);
        if (!this.getData('fetched')) {
            this.setData('fetched', -1);
            // -1 = Loading
            this.fetchMembers(this.resource);
        }
    },

    fetchMembers : function(memberTag) {
        BQFactory.request({
            uri : memberTag.uri + '/value?limit=4',
            cb : Ext.bind(this.loadResource, this),
            errorcb : Ext.emptyFn
        });
    },

    loadResource : function(resource) {
        var imgs = '<div style = "margin-left:4px; margin-top:-1px; width:152px;height:152px">';
        var thumbnail, margin;

        for (var i = 0; i < resource.children.length && i < 4; i++) {
            switch (resource.children[i].resource_type) {
                case 'image': {
                    //thumbnail = resource.children[i].src + '?slice=,,1,1&thumbnail=280,280';
                    thumbnail = resource.children[i].src + this.getImageParams({
                        width : this.layoutMgr.layoutEl.stdImageWidth, //280,
                        height : this.layoutMgr.layoutEl.stdImageHeight, //280,
                    });
                    break;
                }
                case 'dataset': {
                    thumbnail = bq.url('../export_service/public/images/folder-large.png');
                    break;
                }
                default :
                    thumbnail = bq.url('../export_service/public/images/file-large.png');
            }

            margin = (i == 1 ? 'margin:0px 0px 0px 2px;' : (i == 2 ? 'margin:2px 2px 0px 0px;' : ''));
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src=' + thumbnail + ' />';
        }

        imgs += '</div>';

        this.setData('fetched', 1);
        // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef = this.getData('renderedRef');
        if (renderedRef)
            renderedRef.updateContainer();
    },

    updateContainer : function() {
        var date = new Date();
        date.setISO(this.resource.ts);

        this.update('<div class="labelOnImage" style="width:160px;">' + this.resource.name + '<br><span class="smallLabelOnImage">' + Ext.Date.format(date, "m/d/Y") + '</span></div>' + this.getData('previewDiv'));
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Dataset.Card', {
    extend : 'Bisque.Resource.Dataset.Compact',

    fetchMembers : function(memberTag) {
        BQFactory.request({
            uri : memberTag.uri + '/value?limit=12',
            cb : Ext.bind(this.loadResource, this),
            errorcb : Ext.emptyFn
        });
    },

    loadResource : function(resource) {
        var imgs = '<div style = "margin:0px 0px 0px 12px;width:258px;height:310px">';
        var thumbnail, margin;

        for (var i = 0; i < resource.children.length && i < 12; i++) {
            switch (resource.children[i].resource_type) {
                case 'image': {
                    thumbnail = resource.children[i].src + this.getImageParams({
                        width : this.layoutMgr.layoutEl.stdImageWidth, //280,
                        height : this.layoutMgr.layoutEl.stdImageHeight, //280,
                    });
                    break;
                }
                case 'dataset': {
                    thumbnail = bq.url('../export_service/public/images/folder-large.png');
                    break;
                }
                default :
                    thumbnail = bq.url('../export_service/public/images/file-large.png');
            }

            margin = 'margin:0px 3px 2px 0px;';
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src=' + thumbnail + ' />';
        }

        imgs += '</div>';

        this.setData('fetched', 1);
        // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef = this.getData('renderedRef');
        if (renderedRef)
            renderedRef.updateContainer();
    },

    updateContainer : function() {
        var date = new Date();
        date.setISO(this.resource.ts);

        this.update('<div class="labelOnImage" style="width:260px;">' + this.resource.name + '<br><span class="smallLabelOnImage">' + Ext.Date.format(date, "m/d/Y") + '</span></div>' + this.getData('previewDiv'));
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Dataset.Full', {
    extend : 'Bisque.Resource.Dataset.Compact',

    constructor : function() {
        this.callParent(arguments);

        Ext.apply(this, {
            layout : 'fit',
        });
    },

    fetchMembers : function(memberTag) {
        BQFactory.request({
            uri : memberTag.uri + '/value?limit=12',
            cb : Ext.bind(this.loadResource, this),
            errorcb : Ext.emptyFn
        });
    },

    loadResource : function(resource) {
        var imgs = '<div style = "margin:0px 0px 0px 12px;width:99%;">';
        var thumbnail, margin;

        for (var i = 0; i < resource.children.length; i++) {
            switch (resource.children[i].resource_type) {
                case 'image': {
                    thumbnail = resource.children[i].src + this.getImageParams({
                        width : this.layoutMgr.layoutEl.stdImageWidth, //280,
                        height : this.layoutMgr.layoutEl.stdImageHeight, //280,
                    });
                    break;
                }
                case 'dataset': {
                    thumbnail = bq.url('../export_service/public/images/folder-large.png');
                    break;
                }
                default :
                    thumbnail = bq.url('../export_service/public/images/file-large.png');
            }

            margin = 'margin:0px 3px 2px 0px;';
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src=' + thumbnail + ' />';
        }

        imgs += '</div>';

        this.setData('fetched', 1);
        // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef = this.getData('renderedRef');
        if (renderedRef)
            renderedRef.updateContainer();
    },

    updateContainer : function() {
        var date = new Date();
        date.setISO(this.resource.ts);

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.update('<div class="labelOnImage" style="width:99%;">' + this.resource.name + '<br><span class="smallLabelOnImage">' + Ext.Date.format(date, "m/d/Y") + '</span></div>' + this.getData('previewDiv'));

        this.add(Ext.create('Ext.panel.Panel', {
            border : 0,
            autoScroll : true,
            contentEl : imgDiv,
        }));

        this.setLoading(false);

    },
});

Ext.define('Bisque.Resource.Dataset.List', {
    extend : 'Bisque.Resource.Dataset.Compact',

    constructor : function() {
        this.callParent(arguments);

        Ext.apply(this, {
            layout : {
                type : 'hbox',
                align : 'middle'
            }
        });
        this.addCls('list');
    },

    updateContainer : function() {
        var datasetName = new Ext.form.Label({
            text : ' ' + this.resource.name + ' ',
            padding : '0 8 0 8',
            cls : 'lblModuleName',
        });

        var datasetOwner = new Ext.form.Label({
            text : this.getData('owner'),
            padding : '0 0 0 4',
            cls : 'lblModuleOwner',
        });

        var date = new Date();
        date.setISO(this.resource.ts);

        var datasetDate = new Ext.form.Label({
            text : Ext.Date.format(date, "F j, Y g:i:s a"),
            cls : 'lblModuleDate',
            flex : 1,
            //padding:'0 0 0 8',
            //style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
        });

        this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});

// Page view for a dataset
Ext.define('Bisque.Resource.Dataset.Page', {
    extend : 'Bisque.Resource',

    constructor : function() {
        Ext.apply(this, {
            layout : 'fit',
        });

        this.callParent(arguments);
    },

    updateContainer : function() {
        this.setLoading(false);

        var renderer = Ext.create('BQ.renderers.dataset', {
            resource : this.resource,
            loadmap : true,
        });

        this.add(renderer);
    }
});


//-----------------------------------------------------------------------------
// Operation bar for dataset
//-----------------------------------------------------------------------------

Ext.define('Bisque.ResourceBrowser.OperationBar.dataset', {
    extend : 'Bisque.ResourceBrowser.OperationBar',

    initComponent : function() {
        this.items = [{
            xtype: 'button',
            icon : bq.url('/js/ResourceBrowser/Images/down.png'),
            tooltip : 'Available operations for this resource.',
            handler : this.menuHandler,
            scope : this
        }, {
            xtype: 'button',
            itemId : 'btn_delete_full',
            text: 'Delete',
            //icon : bq.url('/js/ResourceBrowser/Images/close.gif'),
            tooltip : 'Delete this dataset and its elements',
            handler : this.deleteDataset,
            scope : this,
        }, {
            xtype: 'button',
            itemId : 'btn_delete',
            icon : bq.url('/js/ResourceBrowser/Images/close.gif'),
            tooltip : 'Delete this dataset, keep elements',
            handler : this.deleteResource,
            scope : this,
        }];
        this.dataset_service = Ext.create('BQ.dataset.Service', {
            listeners: {
                //'running': this.onDatasetRunning,
                //'success': this.onDatasetSuccess,
                'error': this.onDatasetError,
                scope: this,
            },
        });
        this.callParent();
    },

    onDatasetError: function() {
        BQ.ui.error('Error while deleteing dataset');
    },

    deleteDataset : function(me, e) {
        e.stopPropagation();
        var list = Ext.Object.getSize(this.browser.resourceQueue.selectedRes);

        if (list > 1) {
            this.fireEvent( 'removed', this.browser.resourceQueue.selectedRes );
            var members = [];

            for (var res in this.browser.resourceQueue.selectedRes) {
                this.browser.resourceQueue.selectedRes[res].setLoading({
                    msg : 'Deleting...'
                });
                members.push(this.browser.resourceQueue.selectedRes[res]);
            }

            for (var i=0; i<members.length; i++)
                this.dataset_service.run_delete(members[i].resource.uri);

            this.browser.msgBus.fireEvent('Browser_ReloadData', {});
        } else {
            var selected = {};
            selected[this.resourceCt.resource.uri] = this.resourceCt.resource;
            this.fireEvent( 'removed', selected );

            this.resourceCt.setLoading({
                msg : 'Deleting...'
            });
            this.dataset_service.run_delete(this.resourceCt.resource.uri);
            this.browser.msgBus.fireEvent('Browser_ReloadData', {});
        }
    },

});

