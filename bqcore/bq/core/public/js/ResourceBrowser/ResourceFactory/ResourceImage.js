/* Abstract Image resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Image',
{
    extend: 'Bisque.Resource',

    afterRenderFn: function () {
        this.setData('renderedRef', this);

        if (this.getData('fetched') == 1 && !this.isDestroyed)
            this.updateContainer();
    },

    OnDblClick: function () {
        this.msgBus.fireEvent('ResourceDblClick', this.resource.uri);
    },

    onMouseEnter: function (e, me) {
        if (!this.sliceLoader)
            this.sliceLoader = new Ext.util.DelayedTask(this.fetchMeta, this);
        this.sliceLoader.delay (400, this.fetchMeta, this, [e, me]);
    },

    fetchMeta: function (e, target) {
        if (this.mmData && this.mmData.needsFetchingSlices) {
            this.mmData.isFetchingSlices = true;
            this.onMouseMove (e, target);
        } else {
            Ext.Ajax.request({
                url: this.resource.src + '?meta',
                callback: function (opts, success, response) {
                    if (response.status >= 400)
                        console.log(response.responseText);
                    else
                        this.onMetaLoaded(response.responseXML, [e, target]);
                },
                scope: this,
                disableCaching: false,
            });
        }
    },

    onMetaLoaded: function (xmlDoc, args) {
        if (!xmlDoc) return;
        try {
            this.resource.t = parseInt(evaluateXPath(xmlDoc, "//tag[@name='image_num_t']/@value")[0].value);
            this.resource.z = parseInt(evaluateXPath(xmlDoc, "//tag[@name='image_num_z']/@value")[0].value);
        } catch (e) {
            this.resource.t = 1;
            this.resource.z = 1;
        }

        if (this.resource.t === 1 && this.resource.z === 1) {
            // only 1 frame available
            this.mmData = { needsFetchingSlices: false, isFetchingSlices: false };
        } else {
            var el = this.getEl();
            if (this.getData('fetched') == 1)
                this.mmData = {
                    x: el.getX() + el.getOffsetsTo(this.resource.uri)[0],
                    y: el.getY() + el.getOffsetsTo(this.resource.uri)[1],
                    needsFetchingSlices: true,
                    isFetchingSlices: true,
                    //sliceLoader  : new Ext.util.DelayedTask(this.loadThumbSlice, this),
                };
            if (args && args.length>1) 
                this.onMouseMove (args[0], args[1]);
        }
    },

    onMouseLeave: function () {
        if (this.sliceLoader)
            this.sliceLoader.cancel();
        if (this.mmData)
            this.mmData.isFetchingSlices = false;
    },


    onMouseMove: function (e, target) {
        if (!this.mmData || !this.mmData.isFetchingSlices)
            return;
            
        var sliceX = Math.max(1, Math.ceil((e.getX() - this.mmData.x) * this.resource.t / target.clientWidth));
        var sliceY = Math.max(1, Math.ceil((e.getY() - this.mmData.y) * this.resource.z / target.clientHeight));
        sliceX = Math.min(sliceX, this.resource.t);
        sliceY = Math.min(sliceY, this.resource.z);
        
        var imgLoader = new Image();
        imgLoader.style.height = this.layoutMgr.layoutEl.imageHeight;
        imgLoader.style.width = this.layoutMgr.layoutEl.imageWidth;
        
        imgLoader.onload = Ext.bind(ImgOnLoad, this);
        imgLoader.onerror = Ext.emtpyFn;
        
        imgLoader.src = this.resource.src + this.getImageParams({
            sliceZ: sliceY,
            sliceT: sliceX,
            width: this.layoutMgr.layoutEl.stdImageWidth,
            height: this.layoutMgr.layoutEl.stdImageHeight
        });

        function ImgOnLoad() {
            if (Ext.isDefined(document.images[this.resource.uri])) {
                document.images[this.resource.uri].src = imgLoader.src;
            }
        }
    },

    /* Resource operations */
    downloadOriginal: function () {
        window.open(this.resource.src);
    },
});

Ext.define('Bisque.Resource.Image.Compact',
{
    extend: 'Bisque.Resource.Image',

    afterRenderFn: function (e) {
        if (!this.ttip) {
            this.mouseIn = false;
            this.ttip = Ext.create('Ext.tip.ToolTip',
            {
                target: this.id,
                anchor: "top",
                maxWidth: 600,
                width: 555,
                cls: 'LightShadow',
                dismissDelay: 0,
                //style: 'background-color:#FAFAFA;border: solid 2px #E0E0E0;',
                layout: 'hbox',
                autoHide: false,
                listeners:
                {
                    "beforeshow": function (me) { if (!this.tagsLoaded || !this.mouseIn) return false; },
                    scope: this
                }
            });
        }
        this.callParent(arguments);
    },

    onRightClick: function (e) {
        e.preventDefault();
        this.mouseIn = true;
        (!this.tagsLoaded) ? this.requestTags() : this.ttip.show();
    },

    onMouseLeave: function (e) {
        this.mouseIn = false;
        this.callParent(arguments);
    },

    requestTags: function () {
        if (!this.tagsLoaded) {
            BQFactory.request({ uri: this.resource.uri + '/tag', cb: Ext.bind(this.tagData, this, ['tags'], true) });
            BQFactory.request({ uri: this.resource.src + '?meta', cb: Ext.bind(this.tagData, this, ['meta'], true) });
        }
    },

    tagData: function (data, type) {
        this.tagsLoaded = true;
        this.resource.tags = data.tags;

        var tagArr = [], tags =
        {
        }, found = '';

        for (var i = 0; i < this.resource.tags.length; i++) {
            found = this.resource.tags[i].value;
            tags[this.resource.tags[i].name] = (found == null || found == "" ? 'None' : found);
            tagArr.push(new Ext.grid.property.Property(
            {
                name: this.resource.tags[i].name,
                value: tags[this.resource.tags[i].name]
            }));
        }

        var propsGrid = this.GetPropertyGrid({ width: 270 }, tagArr);

        if (type == 'tags')
            propsGrid.title = 'Tag data';
        else
            propsGrid.title = 'Metadata';

        this.ttip.add(propsGrid);
        this.ttip.show();
    },

    prefetch: function (layoutMgr) {
        this.callParent(arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);    //Loading

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload = Ext.bind(this.loadResource, this, ['image'], true);
            prefetchImg.onerror = Ext.bind(this.resourceError, this);
            prefetchImg.onabort = Ext.bind(this.resourceError, this);
        }
    },

    resourceError: function () {
        var errorImg = '<img style="display: block; margin-left: auto; margin-right: auto; margin-top: 60px;"'
                            + ' src="' + bq.url('/js/ResourceBrowser/Images/unavailable.png') + '"/>';
        this.setData('image', errorImg);
        this.setData('fetched', 1);
        this.update(errorImg);

        if (!this.rendered)
            this.on('afterrender', function (me) {
                me.setLoading(false);
            }, this, { single: true });
        else
            this.setLoading(false);
    },

    loadResource: function (data, type) {
        if (type == 'image') {
            this.setData('image', this.GetImageThumbnailRel(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            },
            {
                width: data.currentTarget.width,
                height: data.currentTarget.height
            },
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            }));
        }

        if (this.getData('image')) {
            this.setData('fetched', 1); //Loaded

            var renderedRef = this.getData('renderedRef');
            if (renderedRef)
                renderedRef.updateContainer();
        }
    },

    updateContainer: function () {
        var text = Ext.String.ellipsis(this.resource.name, 25) || '';
        this.update('<div class="textOnImage" style="width:' + this.layoutMgr.layoutEl.width + 'px;">' + text + '</div>' + this.getData('image'));
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Image.Card',
{
    extend: 'Bisque.Resource.Image',

    constructor: function () {
        Ext.apply(this,
        {
            layout:
            {
                type: 'vbox',
                align: 'stretch'
            }
        });

        this.callParent(arguments);
    },

    prefetch: function (layoutMgr) {
        this.callParent(arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);    //Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload = Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource: function (data, type) {
        if (type == 'image')
            this.setData('image', this.GetImageThumbnailRel(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight
            },
            {
                width: data.currentTarget.width,
                height: data.currentTarget.height
            },
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,
            }));
        else {
            this.resource.tags = data.tags;

            var tag, tagProp, tagArr = [], tags = this.getSummaryTags();

            // Show preferred tags first
            for (var i = 0; i < this.resource.tags.length; i++) {
                tag = this.resource.tags[i];
                tagProp = new Ext.grid.property.Property({
                    name: tag.name,
                    value: tag.value
                });
                (tags[tag.name]) ? tagArr.unshift(tagProp) : tagArr.push(tagProp);
            }

            this.setData('tags', tagArr.slice(0, 7));
        }

        if (this.getData('tags') && this.getData('image')) {
            this.setData('fetched', 1); //Loaded

            var renderedRef = this.getData('renderedRef')
            if (renderedRef && !renderedRef.isDestroyed)
                renderedRef.updateContainer();
        }
    },

    getSummaryTags: function () {
        if (this.browser.preferences["Summary Tags"])
            return this.browser.preferences["Summary Tags"];

        return {
            "filename": 0,
            "attached-file": 0,
            "image_type": 0,
            "imagedate": 0,
            "experimenter": 0,
            "dataset_label": 0,
            "species": 0
        };
    },

    updateContainer: function () {
        var propsGrid = this.GetPropertyGrid({/*autoHeight:true}*/ }, this.getData('tags'));
        propsGrid.determineScrollbars = Ext.emptyFn;

        var imgCt = new Ext.Component({ html: this.getData('image'), height: this.layoutMgr.layoutEl.imageHeight });
        this.add([imgCt, propsGrid]);
        this.setLoading(false);
    },

    onMouseMove: Ext.emptyFn,
});

Ext.define('Bisque.Resource.Image.Full',
{
    extend: 'Bisque.Resource.Image',

    constructor: function () {
        Ext.apply(this,
        {
            layout: 'fit',
        });

        this.callParent(arguments);
    },

    prefetch: function (layoutMgr) {
        this.callParent(arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);    //Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload = Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource: function (data, type) {
        if (type == 'image')
            this.setData('image', this.GetImageThumbnailRel(
            {
                width: this.layoutMgr.layoutEl.stdImageWidth,
                height: this.layoutMgr.layoutEl.stdImageHeight
            },
            {
                width: data.currentTarget.width,
                height: data.currentTarget.height
            },
            {
                width: this.layoutMgr.layoutEl.imageWidth,
                height: this.layoutMgr.layoutEl.imageHeight,

            }));
        else {
            this.resource.tags = data.tags;
            var tagArr = [], tags =
            {
            }, found = '';

            for (var i = 0; i < this.resource.tags.length; i++) {
                found = this.resource.tags[i].value;
                tags[this.resource.tags[i].name] = (found == null || found == "" ? 'None' : found);
                tagArr.push(new Ext.grid.property.Property(
                {
                    name: this.resource.tags[i].name,
                    value: tags[this.resource.tags[i].name]
                }));
            }

            this.setData('tags', tagArr);
        }

        if (this.getData('tags') && this.getData('image')) {
            this.setData('fetched', 1); //Loaded
            if (this.rendered)
                this.updateContainer();
        }
    },

    updateContainer: function () {
        this.setLoading(false);

        var propsGrid = this.GetPropertyGrid(
        {
            autoHeight: false
        }, this.getData('tags'));

        propsGrid.setAutoScroll(true);

        Ext.apply(propsGrid, {
            region: 'center',
            padding: 5,
            //style: 'background-color:#FAFAFA'

        });

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.dom.align = "center";
        imgDiv.update(this.getData('image'));

        this.add(new Ext.Panel(
        {
            layout: 'border',
            border: false,
            items: [new Ext.Container(
            {
                region: 'west',
                layout:
                {
                    type: 'hbox',
                    pack: 'center',
                    align: 'center'
                },
                region: 'west',
                width: this.layoutMgr.layoutEl.imageHeight,
                //style: 'background-color:#FAFAFA',
                contentEl: imgDiv
            }), propsGrid]
        }));
    },

    onMouseMove: Ext.emptyFn,
    onMouseEnter: Ext.emptyFn
});


Ext.define('Bisque.Resource.Image.Grid',
{
    extend: 'Bisque.Resource.Image',

    prefetch: function (layoutMgr) {
        this.callParent(arguments);
        var prefetchImg = new Image();

        prefetchImg.src = this.getThumbnailSrc(
        {
            width: this.layoutMgr.layoutEl.stdImageWidth,
            height: this.layoutMgr.layoutEl.stdImageHeight,
        });
    },

    getFields: function (cb) {
        var fields = this.callParent();

        fields[0] = '<div class="gridCellIcon" >' + this.GetImageThumbnailRel(
        {
            width: 280,
            height: 280
        },
        {
            width: 280,
            height: 280
        },
        {
            width: 40,
            height: 40,
        }) + '</div>';

        fields[6].height = 48;

        return fields;
    },
});


//-----------------------------------------------------------------------
// Page view for an image
//-----------------------------------------------------------------------

Ext.define('Bisque.Resource.Image.Page', {
    extend: 'Bisque.Resource.Page',

    onResourceRender: function () {
        this.setLoading(true);
        this.root = '';
        if (this.resource && this.resource.uri)
            this.root = this.resource.uri.replace(/\/data_service\/.*$/i, '');

        var resourceTagger = Ext.create('Bisque.ResourceTagger', {
            resource: this.resource,
            title: 'Annotations',
        });

        var embeddedTagger = Ext.create('Bisque.ResourceTagger', {
            resource: this.resource.src + '?meta',
            title: 'Embedded',
            viewMode: 'ReadOnly',
            disableAuthTest: true
        });

        var mexBrowser = new Bisque.ResourceBrowser.Browser({
            'layout': 5,
            'title': 'Analysis',
            'viewMode': 'MexBrowser',
            'dataset': this.root + '/data_service/mex',
            'tagQuery': '"' + this.resource.uri + '"',
            'wpublic': true,
            showOrganizer: false,
            mexLoaded: false,
            listeners: {
                'browserLoad': function (me, resQ) {
                    me.mexLoaded = true;
                },
                'Select': function (me, resource) {
                    window.open(bq.url('/module_service/' + resource.name + '/?mex=' + resource.uri));
                },
                scope: this
            },
        });

        var resTab = Ext.create('Ext.tab.Panel', {
            title: 'Metadata',
            region: 'east',
            activeTab: 0,
            border: false,
            bodyBorder: 0,
            collapsible: true,
            split: true,
            width: 400,
            plain: true,
            //bodyStyle: 'background-color:#F00',
            items: [resourceTagger, embeddedTagger, mexBrowser]
        });

        var viewerContainer = Ext.create('BQ.viewer.Image', {
            region: 'center',
            resource: this.resource,
            toolbar: this.toolbar,
            parameters: {
                gobjectCreated: Ext.bind(function (gob) {
                    this.gobjectTagger.appendGObjects([gob]);
                }, this),

                gobjectDeleted: Ext.bind(function (gi) {
                    this.gobjectTagger.deleteGObject(gi);
                }, this),
            },
            listeners: {
                'changed': function (me, gobjects) {
                    this.gobjectTagger.tree.getView().refresh();
                },
                scope: this
            }
        });

        this.add({
            xtype: 'container',
            layout: 'border',
            items: [viewerContainer, resTab]
        });

        this.gobjectTagger = new Bisque.GObjectTagger({
            resource: this.resource,
            imgViewer: viewerContainer.viewer,
            mexBrowser: mexBrowser,
            title: 'Graphical',
            viewMode: 'GObjectTagger',
            readFromMex: function (resQ) {
                function changeFormat(mex) {
                    this.appendFromMex([{ resource: mex }]);
                }

                for (var i = 0; i < resQ.length; i++)
                    BQFactory.request({
                        uri: resQ[i].resource.uri + '?view=deep',
                        cb: Ext.bind(changeFormat, this)
                    });
            },

            listeners: {
                'beforeload': function (me, resource) {
                    me.imgViewer.start_wait({
                        op: 'gobjects',
                        message: 'Fetching gobjects'
                    });
                },
                
                'onload': function (me, resource) {
                    me.imgViewer.loadGObjects(resource.gobjects, false);

                    if (me.mexBrowser.mexLoaded)
                        me.readFromMex(me.mexBrowser.resourceQueue);
                    else
                        me.mexBrowser.on('browserLoad', function (mb, resQ) {
                            me.readFromMex(resQ);
                        }, me);

                },
                
                'onappend': function (me, gobjects) {
                    me.imgViewer.gobjectsLoaded(true, gobjects);
                },

                'select': function (me, record, index) {
                    var gobject = (record.raw instanceof BQGObject) ? record.raw : record.raw.gobjects;
                    me.imgViewer.showGObjects(gobject);
                },

                'deselect': function (me, record, index) {
                    var gobject = (record.raw instanceof BQGObject) ? record.raw : record.raw.gobjects;
                    me.imgViewer.hideGObjects(gobject);
                }
            }
        });
        resTab.add(this.gobjectTagger);

        resTab.add({
            xtype: 'bqmap',
            title: 'Map',
            zoomLevel: 16,
            gmapType: 'map',
            autoShow: true,
            resource: this.resource,            
        });

        this.setLoading(false);
    },

    downloadOriginal: function () {
        window.open(this.resource.src);
    }
});
