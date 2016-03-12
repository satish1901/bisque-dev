/* Abstract Image resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Image', {
    extend : 'Bisque.Resource',

    afterRenderFn : function() {
        this.setData('renderedRef', this);

        if (this.getData('fetched') == 1 && !this.isDestroyed)
            this.updateContainer();
    },

    OnDblClick : function() {
        this.msgBus.fireEvent('ResourceDblClick', this.resource.uri);
    },

    onMouseEnter : function(e, me) {
        if (!this.sliceLoader)
            this.sliceLoader = new Ext.util.DelayedTask(this.fetchMeta, this);
        this.sliceLoader.delay(400, this.fetchMeta, this, [e, me]);
    },

    fetchMeta : function(e, target) {
        if (this.mmData && this.mmData.needsFetchingSlices) {
            this.mmData.isFetchingSlices = true;
            this.onMouseMove(e, target);
        } else {
            Ext.Ajax.request({
                url : this.resource.src + '?meta',
                callback : function(opts, success, response) {
                    if (response.status >= 400)
                        console.log(response.responseText);
                    else
                        this.onMetaLoaded(response.responseXML, [e, target]);
                },
                scope : this,
                disableCaching : false,
            });
        }
    },

    onMetaLoaded : function(xmlDoc, args) {
        if (!xmlDoc)
            return;
        try {
            this.resource.t = parseInt(BQ.util.xpath_nodes(xmlDoc, "//tag[@name='image_num_t']/@value")[0].value);
            this.resource.z = parseInt(BQ.util.xpath_nodes(xmlDoc, "//tag[@name='image_num_z']/@value")[0].value);
        } catch (e) {
            this.resource.t = 1;
            this.resource.z = 1;
        }

        if (this.resource.t === 1 && this.resource.z === 1) {
            // only 1 frame available
            this.mmData = {
                needsFetchingSlices : false,
                isFetchingSlices : false
            };
        } else {
            var el = this.getEl();
            if (el && this.getData('fetched') == 1)
                this.mmData = {
                    x : el.getX() + el.getOffsetsTo(this.resource.uri)[0],
                    y : el.getY() + el.getOffsetsTo(this.resource.uri)[1],
                    needsFetchingSlices : true,
                    isFetchingSlices : true,
                    //sliceLoader  : new Ext.util.DelayedTask(this.loadThumbSlice, this),
                };
            if (args && args.length > 1)
                this.onMouseMove(args[0], args[1]);
        }
    },

    onMouseLeave : function() {
        if (this.sliceLoader)
            this.sliceLoader.cancel();
        if (this.mmData)
            this.mmData.isFetchingSlices = false;
    },

    updateThumbnail : function(pos, o) {
        var sliceX = Math.max(1, Math.ceil((pos.x - this.mmData.x) * this.resource.t / o.w));
        var sliceY = Math.max(1, Math.ceil((pos.y - this.mmData.y) * this.resource.z / o.h));
        sliceX = Math.min(sliceX, this.resource.t);
        sliceY = Math.min(sliceY, this.resource.z);

        var imgLoader = new Image();
        imgLoader.style.height = this.layoutMgr.layoutEl.imageHeight;
        imgLoader.style.width = this.layoutMgr.layoutEl.imageWidth;

        imgLoader.onload = Ext.bind(ImgOnLoad, this);
        imgLoader.onerror = Ext.emtpyFn;

        imgLoader.src = this.resource.src + this.getImageParams({
            sliceZ : sliceY,
            sliceT : sliceX,
            width : this.layoutMgr.layoutEl.stdImageWidth,
            height : this.layoutMgr.layoutEl.stdImageHeight
        });

        function ImgOnLoad() {
            if (Ext.isDefined(document.images[this.resource.uri])) {
                document.images[this.resource.uri].src = imgLoader.src;
            }
        }
    },

    onMouseMove : function(e, target) {
        if (!this.mmData || !this.mmData.isFetchingSlices)
            return;

        if (!this.thumbnailUpdater)
            this.thumbnailUpdater = new Ext.util.DelayedTask(this.updateThumbnail, this);
        this.thumbnailUpdater.delay(10, this.updateThumbnail, this, [{x: e.getX(), y: e.getY()}, {w: target.clientWidth, h: target.clientHeight}]);
    },

    downloadOriginal : function() {
        if (this.resource.src) {
            window.open(this.resource.src);
            return;
        }
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },
});

Ext.define('Bisque.Resource.Image.Compact', {
    extend : 'Bisque.Resource.Image',

    afterRenderFn : function(e) {
        if (!this.ttip) {
            this.mouseIn = false;
            this.ttip = Ext.create('Ext.tip.ToolTip', {
                target : this.id,
                anchor : "top",
                maxWidth : 600,
                width : 555,
                cls : 'LightShadow',
                dismissDelay : 0,
                //style: 'background-color:#FAFAFA;border: solid 2px #E0E0E0;',
                layout : 'hbox',
                autoHide : false,
                listeners : {
                    "beforeshow" : function(me) {
                        if (!this.tagsLoaded || !this.mouseIn)
                            return false;
                    },
                    scope : this
                }
            });
        }
        this.callParent(arguments);
    },

    onRightClick : function(e) {
        e.preventDefault();
        this.mouseIn = true;
        (!this.tagsLoaded) ? this.requestTags() : this.ttip.show();
    },

    onMouseLeave : function(e) {
        this.mouseIn = false;
        this.callParent(arguments);
    },

    requestTags : function() {
        if (!this.tagsLoaded) {
            BQFactory.request({
                uri : this.resource.uri + '/tag',
                cb : Ext.bind(this.tagData, this, ['tags'], true)
            });
            BQFactory.request({
                uri : this.resource.src + '?meta',
                cb : Ext.bind(this.tagData, this, ['meta'], true)
            });
        }
    },

    tagData : function(data, type) {
        this.tagsLoaded = true;
        this.resource.tags = data.tags;

        var tagArr = [], tags = {
        }, found = '';

        for (var i = 0; i < this.resource.tags.length; i++) {
            found = this.resource.tags[i].value;
            tags[this.resource.tags[i].name] = (found == null || found == "" ? 'None' : found);
            tagArr.push(new Ext.grid.property.Property({
                name : this.resource.tags[i].name,
                value : tags[this.resource.tags[i].name]
            }));
        }

        var propsGrid = this.GetPropertyGrid({
            width : 270
        }, tagArr);

        if (type == 'tags')
            propsGrid.title = 'Tag data';
        else
            propsGrid.title = 'Metadata';

        this.ttip.add(propsGrid);
        this.ttip.show();
    },

    prefetch : function(layoutMgr) {
        this.callParent(arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);
            //Loading

            var prefetchImg = new Image();
            prefetchImg.onload = Ext.bind(this.loadResource, this, ['image'], true);
            prefetchImg.onerror = Ext.bind(this.resourceError, this);
            prefetchImg.onabort = Ext.bind(this.resourceError, this);
            prefetchImg.src = this.getThumbnailSrc({
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight,
            });

            if (BQ.Preferences.get('user', 'ResourceBrowser/Images/enable_annotation_status', false) === true)
                BQFactory.load(this.resource.uri + '?view='+BQ.annotations.name, callback(this, this.loadResource, 'anno_status'));
        }
    },

    resourceError : function() {
        var errorImg = '<img style="display: block; margin-left: auto; margin-right: auto; margin-top: 60px;"' + ' src="' + BQ.Server.url('/js/ResourceBrowser/Images/unavailable.png') + '"/>';
        this.setData('image', errorImg);
        this.setData('fetched', 1);
        this.update(errorImg);

        if (!this.rendered)
            this.on('afterrender', function(me) {
                me.setLoading(false);
            }, this, {
                single : true
            });
        else
            this.setLoading(false);
    },

    loadResource : function(data, type) {
        if (data === 'anno_status' && type && type.tags && type.tags.length>0) {
            this.annotation_status = type.tags[0].value;
            this.add({
                xtype: 'component',
                cls: 'status_icon '+this.annotation_status,
                autoEl: {
                    tag: 'div',
                },
            });
            return;
        }

        if (type === 'image') {
            this.setData('image', this.GetImageThumbnailRel({
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight,
            }, {
                width : data.currentTarget.width,
                height : data.currentTarget.height
            }, {
                width : this.layoutMgr.layoutEl.imageWidth,
                height : this.layoutMgr.layoutEl.imageHeight,
            }));
        }

        if (this.getData('image')) {
            this.setData('fetched', 1);
            //Loaded

            var renderedRef = this.getData('renderedRef');
            if (renderedRef)
                renderedRef.updateContainer();
        }
    },

    updateContainer : function() {
        var text = Ext.String.ellipsis(this.resource.name, 25) || '';
        this.update('<div class="textOnImage" style="width:' + this.layoutMgr.layoutEl.width + 'px;">' + text + '</div>' + this.getData('image'));
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Image.Card', {
    extend : 'Bisque.Resource.Image',

    constructor : function() {
        Ext.apply(this, {
            layout : {
                type : 'vbox',
                align : 'stretch'
            }
        });

        this.callParent(arguments);
    },

    prefetch : function(layoutMgr) {
        this.callParent(arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);
            //Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc({
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload = Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type) {
        if (type == 'image')
            this.setData('image', this.GetImageThumbnailRel({
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight
            }, {
                width : data.currentTarget.width,
                height : data.currentTarget.height
            }, {
                width : this.layoutMgr.layoutEl.imageWidth,
                height : this.layoutMgr.layoutEl.imageHeight,
            }));
        else {
            this.resource.tags = data.tags;

            var tag, tagProp, tagArr = [], tags = this.getSummaryTags();

            // Show preferred tags first
            for (var i = 0; i < this.resource.tags.length; i++) {
                tag = this.resource.tags[i];
                tagProp = new Ext.grid.property.Property({
                    name : tag.name,
                    value : tag.value
                });
                (tags[tag.name]) ? tagArr.unshift(tagProp) : tagArr.push(tagProp);
            }

            this.setData('tags', tagArr.slice(0, 7));
        }

        if (this.getData('tags') && this.getData('image')) {
            this.setData('fetched', 1);
            //Loaded

            var renderedRef = this.getData('renderedRef');
            if (renderedRef && !renderedRef.isDestroyed)
                renderedRef.updateContainer();
        }
    },

    getSummaryTags : function() {
        if (this.browser.preferences["Summary Tags"])
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

    updateContainer : function() {
        var propsGrid = this.GetPropertyGrid({/*autoHeight:true}*/ }, this.getData('tags'));
        propsGrid.determineScrollbars = Ext.emptyFn;

        var imgCt = new Ext.Component({
            html : this.getData('image'),
            height : this.layoutMgr.layoutEl.imageHeight
        });
        this.add([imgCt, propsGrid]);
        this.setLoading(false);
    },

    onMouseMove : Ext.emptyFn,
});

Ext.define('Bisque.Resource.Image.Full', {
    extend : 'Bisque.Resource.Image',

    constructor : function() {
        Ext.apply(this, {
            layout : 'fit',
        });

        this.callParent(arguments);
    },

    prefetch : function(layoutMgr) {
        this.callParent(arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);
            //Loading

            BQFactory.load(this.resource.uri + '/tag', Ext.bind(this.loadResource, this, ['tags'], true));

            var prefetchImg = new Image();
            prefetchImg.src = this.getThumbnailSrc({
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight,
            });
            prefetchImg.onload = Ext.bind(this.loadResource, this, ['image'], true);
        }
    },

    loadResource : function(data, type) {
        if (type == 'image')
            this.setData('image', this.GetImageThumbnailRel({
                width : this.layoutMgr.layoutEl.stdImageWidth,
                height : this.layoutMgr.layoutEl.stdImageHeight
            }, {
                width : data.currentTarget.width,
                height : data.currentTarget.height
            }, {
                width : this.layoutMgr.layoutEl.imageWidth,
                height : this.layoutMgr.layoutEl.imageHeight,

            }));
        else {
            this.resource.tags = data.tags;
            var tagArr = [], tags = {
            }, found = '';

            for (var i = 0; i < this.resource.tags.length; i++) {
                found = this.resource.tags[i].value;
                tags[this.resource.tags[i].name] = (found == null || found == "" ? 'None' : found);
                tagArr.push(new Ext.grid.property.Property({
                    name : this.resource.tags[i].name,
                    value : tags[this.resource.tags[i].name]
                }));
            }

            this.setData('tags', tagArr);
        }

        if (this.getData('tags') && this.getData('image')) {
            this.setData('fetched', 1);
            //Loaded
            if (this.rendered)
                this.updateContainer();
        }
    },

    updateContainer : function() {
        this.setLoading(false);

        var propsGrid = this.GetPropertyGrid({
            autoHeight : false
        }, this.getData('tags'));

        propsGrid.setAutoScroll(true);

        Ext.apply(propsGrid, {
            region : 'center',
            padding : 5,
            //style: 'background-color:#FAFAFA'

        });

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.dom.align = "center";
        imgDiv.update(this.getData('image'));

        this.add(new Ext.Panel({
            layout : 'border',
            border : false,
            items : [new Ext.Container({
                region : 'west',
                layout : {
                    type : 'hbox',
                    pack : 'center',
                    align : 'center'
                },
                region : 'west',
                width : this.layoutMgr.layoutEl.imageHeight,
                //style: 'background-color:#FAFAFA',
                contentEl : imgDiv
            }), propsGrid]
        }));
    },

    onMouseMove : Ext.emptyFn,
    onMouseEnter : Ext.emptyFn
});

Ext.define('Bisque.Resource.Image.Grid', {
    extend : 'Bisque.Resource.Image',

    prefetch : function(layoutMgr) {
        this.callParent(arguments);
        var prefetchImg = new Image();

        prefetchImg.src = this.getThumbnailSrc({
            width : this.layoutMgr.layoutEl.stdImageWidth,
            height : this.layoutMgr.layoutEl.stdImageHeight,
        });
    },

    getFields : function(cb) {
        var fields = this.callParent();

        fields[0] = '<div class="gridCellIcon" >' + this.GetImageThumbnailRel({
            width : this.layoutMgr ? this.layoutMgr.layoutEl.stdImageWidth : 280,
            height : this.layoutMgr ? this.layoutMgr.layoutEl.stdImageHeight : 280,
        }, {
            width : this.layoutMgr ? this.layoutMgr.layoutEl.stdImageWidth : 280,
            height : this.layoutMgr ? this.layoutMgr.layoutEl.stdImageHeight : 280,
        }, {
            width : 40,
            height : 40,
        }) + '</div>';

        fields[6].height = 48;

        return fields;
    },
});

//-----------------------------------------------------------------------
// Page view for an image
//-----------------------------------------------------------------------

Ext.define('Bisque.Resource.Image.Page', {
    extend : 'Bisque.Resource.Page',

    onResourceRender : function() {
    	BQApp.setActiveHelpVideo('//www.youtube.com/embed/0odEMDQ1xqo?list=PLAaP7tKanFcyR5cjJsPTCa0CDmWp9unds');
        this.setLoading(true);
        this.root = '';
        if (this.resource && this.resource.uri)
            this.root = this.resource.uri.replace(/\/data_service\/.*$/i, '');

        this.viewerContainer = Ext.create('BQ.viewer.Image', {
            region : 'center',
            itemId: 'main_view_2d',
            resource : this.resource,
            toolbar : this.toolbar,
            main : this,
            parameters : {
                hide_create_gobs_menu: true,
                hide_file_name_osd: true,
                blockforsaves: false,
                main: this,
                render_plugins: ['color', 'corners', 'bbox'],
                //gobjectDeleted :
            },
            listeners : {

                create: Ext.bind(function(scope,gob) {
                    this.gobjectTagger.appendGObject(gob);
                    //jrd: we don't need to select after creation
                    //var node = this.gobjectTagger.findNodeByGob(gob);
                    //this.gobjectTagger.tree.getSelectionModel().select(node);
                }, this),

                delete: Ext.bind(function(scope, gob) {
                    this.gobjectTagger.deleteGObject(gob);
                }, this),

                loaded: function(vc) {
                    var editor = vc.viewer.editor;
                    this.gobjectTagger.on('createGob', editor.onCreateGob, editor);

                },
                changed : function(me, gobjects) {
                    this.gobjectTagger.tree.getView().refresh();
                },
                select : function(viewer, gob) {
                    var nodes = [];
                    var me = this;

                    gob.forEach(function(e,i,a){
                        var node = me.gobjectTagger.findNodeByGob(e.gob);
                        nodes.push(node);
                        if (!node) {
                            console.log('No node found!');
                            return;
                        }
                        // dima: here expand to expose the selected node
                        var parent = node;
                        for (var i=0; i<node.getDepth()-1; i++)
                            parent = parent.parentNode;
                        me.gobjectTagger.tree.expandNode( parent, true );
                    })
                    if(nodes.length === 1)
                        this.gobjectTagger.tree.getSelectionModel().select(nodes[0]);
                    else
                        this.gobjectTagger.tree.getSelectionModel().select(nodes);
                },
                edit_controls_activated : function(viewer) {
                    this.gobjectTagger.deselectGobCreation();
                },
                position_selected: function(pt, viewer) {
                    var map = this.queryById('map');
                    if (map && map.isVisible()) {
                        map.positionMarker(pt);
                    }
                },
                hover: function(panel, gob, e){

                    var panel = this.queryById('main_view_2d');

                    var size = 0;
                    tagData  = function(gob) {
                        //this.tagsLoaded = true;
                        //this.resource.tags = data.tags;
                        var val = gob.value ? 'value: ' + gob.value : '';
                        var tagArr = [], tags = {
                        }, found = '';
                        while(gob.parent){
                            if(!gob.type)
                                tagArr.push(gob.name);
                            else
                            tagArr.push(gob.type);
                            gob = gob.parent;
                            size += 1;
                        }
                        var spaces = '';
                        for(var i = 0; i < tagArr.length; i++){
                            found += (spaces + '-' + tagArr[tagArr.length - 1 -i] + '<br>');
                            spaces += '&nbsp &nbsp'
                        }

                        return found + val;
                    }


                    var hoverMenu = Ext.create('Ext.tip.ToolTip', {
			            target : panel.getEl(),
			            anchor : 'top',
			            anchorToTarget : true,
			            maxWidth : 200,
                        header : false,
                        html: tagData(gob),

			           /*
                        layout : {
				            type : 'fit',
                            //align: 'stretch',
			            },*/
		            });
                    //hoverMenu.setHeight(40*size);
                    hoverMenu.show();
                    hoverMenu.setX(e.clientX+15);
                    hoverMenu.setY(e.clientY-10);
                    //var tagger = this.hoverMenu.queryById('hover-tagger');
                    //tagger.setResource(gob);

                    //if(this.hoverMenu.getEl()){
                    //
                    //}

                    //console.log(panel.hoverMenu);
                },
                modechange: function(viewer, type) {
                    if (!type)
                        this.gobjectTagger.deselectAll();
                },

                loadedPhys: this.onImagePhys,
                working : this.onworking,
                done    : this.ondone,
                error   : this.onerror,
                scope   : this,
            }
        });

        this.gobjectTagger = Ext.create('Bisque.GObjectTagger', {
            resource : this.resource,
            mexBrowser : mexBrowser,
            title : 'Graphical',
            viewMode : 'GObjectTagger',
            full_load_on_creation: true, // gobtagger is referred from other places that are loaded immediately
            listeners : {
                onappend: function(me, gobjects) {
                    this.viewerContainer.viewer.show_additional_gobjects(gobjects);
                },

                select : function(me, record, index, eOpts) {
                    if (!(record.raw instanceof BQObject) && !record.raw.loaded) return;
                    var gobject = (record.raw instanceof BQGObject) ? record.raw : record.raw.gobjects[0];
                    this.viewerContainer.viewer.highlight_gobject(gobject, true);

                    var image3d = this.queryById('main_view_3d');
                    if(image3d){
                        image3d.highlight_gobject(gobject);
                    }

                    this.viewerContainer.viewer.set_parent_gobject(gobject);
                },

                deselect : function(me, record, index, eOpts) {
                    if (!(record.raw instanceof BQObject) && !record.raw.loaded) return;
                    var gobject = (record.raw instanceof BQGObject) ? record.raw : record.raw.gobjects[0];

                    var image3d = this.queryById('main_view_3d');
                    if(image3d){
                        image3d.unhighlight_gobject(gobject);
                    }

                    this.viewerContainer.viewer.highlight_gobject(gobject, false);
                    this.viewerContainer.viewer.set_parent_gobject(undefined);
                },

                checked : function(me, record, index) {
                    if (!(record.raw instanceof BQObject) && !record.raw.loaded) return;
                    var gobject = (record.raw instanceof BQGObject) ? record.raw : record.raw.gobjects;
                    this.viewerContainer.viewer.showGObjects(gobject);
                },

                unchecked : function(me, record, index) {
                    if (!(record.raw instanceof BQObject) && !record.raw.loaded) return;
                    var gobject = (record.raw instanceof BQGObject) ? record.raw : record.raw.gobjects;
                    this.viewerContainer.viewer.hideGObjects(gobject);
                },

                gob_projection : function(me, projection) {
                    this.viewerContainer.viewer.setGobProjection(projection);
                },

                gob_tolerance : function(me) {
                    var tolerance = this.viewerContainer.viewer.getGobTolerance();
                    Ext.create('BQ.window.Prompt', {
                        title: 'Gobject visible plane tolerance',
                        minWidth: 300,
                        minHeight: 200,
                        scope: this,
                        fields: [{
                            xtype: 'tbtext',
                            text: '<h3>Please enter new tolerance (in planes):</h3>',
                        }, {
                            xtype: 'numberfield',
                            itemId: 'tolerance_z',
                            name: 'tolerance_z',
                            fieldLabel: 'Z',
                            value: tolerance.z,
                            maxValue: 1000000,
                            minValue: 0,
                            step: 0.5,
                        }, {
                            xtype: 'numberfield',
                            itemId: 'tolerance_t',
                            name: 'tolerance_t',
                            fieldLabel: 'T',
                            value: tolerance.t,
                            maxValue: 1000000,
                            minValue: 0,
                            step: 0.5,
                        }],
                        func: function(fields) {
                            var v = {z: 1.0, t: 1.0},
                                num_z = fields.queryById('tolerance_z'),
                                num_t = fields.queryById('tolerance_t');
                            v.z = num_z.value;
                            v.t = num_t.value;
                            return v;
                        },
                        callback: function(btn, tolerance) {
                            if (btn !== 'ok') {
                                return;
                            }
                            this.viewerContainer.viewer.setGobTolerance(tolerance);
                        },
                    }).show();

                },

                delete_gobjects : function(gobs) {
                    this.viewerContainer.viewer.delete_gobjects(gobs);
                },

                color_gobjects : function(gobs, color) {
                    var image3d = this.queryById('main_view_3d');
                    for (var i=0; i<gobs.length; i++){
                        if(image3d){
                            image3d.color_gobjects(gobs[i], color);
                        }
                        this.viewerContainer.viewer.editor.color_gobject(gobs[i], color);

                    }
                },

                create_gobject : function(gob) {
                    var uri = '';
                    if (!gob.parent) {
                        this.viewerContainer.viewer.image.addgobjects(gob);
                        uri = gob.parent.uri + '/gobject';
                    } else {
                        uri = gob.parent.uri;
                    }
                    gob.save_reload( uri, this.ondone, this.onerror );
                },
                scope: this,
            }
        });

        var mexBrowser = Ext.create('Bisque.ResourceBrowser.Browser', {
            'layout' : 5,
            'title' : 'Analysis',
            'viewMode' : 'MexBrowser',
            'dataset' : this.root + '/data_service/mex',
            'tagQuery' : '"' + this.resource.uri + '"',
            'wpublic' : true,
            showOrganizer : false,
            mexLoaded : false,
            listeners : {
                'browserLoad' : function(me, resQ){ e
                    me.mexLoaded = true;
                },
                'Select' : function(me, resource) {
                    window.open(BQ.Server.url('/module_service/' + resource.name + '/?mex=' + resource.uri));
                },
                'browserLoad' : function(mb, resQ) {
                    for (var i=resQ.length-1; i>=0; i--)
                        this.gobjectTagger.appendMex(resQ[i].resource);
                },
                scope : this
            },
        });

        var resourceTagger = {
            xtype: 'bq-tagger',
            resource : this.resource,
            title : 'Annotations',
        };

        var embeddedTagger = {
            xtype: 'bq-tagger',
            resource : this.resource.src + '?meta',
            title : 'Embedded',
            viewMode : 'ReadOnly',
            disableAuthTest : true
        };

        var map = {
            xtype : 'bqmap',
            itemId: 'map',
            title : 'Map',
            zoomLevel : 16,
            gmapType : 'map',
            autoShow : true,
            resource : this.resource,
        };

        var graph = {
            xtype : 'bq_graphviewer_panel',
            itemId: 'graph',
            title : 'Provenance',
            resource: this.resource,
            listeners:{
                'context' : function(res, div, graph) {
                    var node = graph.g.node(res);
                    window.open(BQ.Server.url(node.card.getUrl(res)));
                },
            },
            resource : this.resource,
        };

        var resTab = {
            xtype: 'tabpanel',
            itemId: 'tabs',
            title : 'Metadata',
            deferredRender: true,
            region : 'east',
            activeTab : 0,
            border : false,
            bodyBorder : 0,
            collapsible : true,
            split : true,
            width : 400,
            plain : true,
            //items : [resourceTagger, this.gobjectTagger, embeddedTagger, mexBrowser, graph, map]
            items : [resourceTagger, this.gobjectTagger, embeddedTagger, mexBrowser, map]
        };

        this.add({
            xtype : 'container',
            itemId: 'viewer_container',
            layout : 'border',
            items : [resTab, {
                xtype: 'container',
                itemId: 'main_container',
                region : 'center',
                layout: 'fit',
                items : [this.viewerContainer]
            }]
        });

        //var download = this.toolbar.queryById('btnDownload');
        var download = BQApp.getToolbar().queryById('button_download');
        if (download) {
            //download.menu.add([{
            download.menu.insert(3, [{
                itemId: 'download_as_ometiff',
                text: 'as OME-TIFF',
                scope: this,
                handler: this.download_ometiff,
            }, {
                itemId: 'download_as_omebigtiff',
                text: 'as OME-BigTIFF',
                scope: this,
                handler: this.download_omebigtiff,
            }]);
        };

        var export_btn = this.toolbar.queryById('menu_viewer_external');
        if (export_btn) {
            export_btn.menu.insert(1, [{
                xtype  : 'menuitem',
                itemId : 'menu_viewer_embed_code',
                text   : 'Get embed code',
                scope  : this,
                handler: this.getEmbedCode,
            }]);
        };

        this.toolbar.insert(5, [{
            itemId: 'button_view',
            xtype:'button',
            text: 'View: 2D',
            iconCls: 'view2d',
            needsAuth: false,
            tooltip: 'Change the view for the current image',
            scope: this,
            menu: {
                defaults: {
                    scope: this,
                },
                items: [{
                    xtype  : 'menuitem',
                    itemId : 'menu_view_2d',
                    text   : '2D',
                    iconCls: 'view2d',
                    handler: this.show2D,
                    tooltip: 'View current image in 2D tiled viewer',
                }, {
                    xtype  : 'menuitem',
                    itemId : 'menu_view_3d',
                    text   : '3D',
                    disabled: true,
                    iconCls: 'view3d',
                    tooltip: 'View current image in 3D volume renderer',
                    handler: this.show3D,
                }, {
                    xtype  : 'menuitem',
                    itemId : 'menu_view_movie',
                    text   : 'movie',
                    disabled: true,
                    iconCls: 'movie',
                    tooltip: 'View current image as a movie',
                    handler: this.showMovie,
                }]
            },
        }, '-']);

        this.toolbar.doLayout();

        this.setLoading(false);
    },

    downloadOriginal : function() {
        if (this.resource.src) {
            window.open(this.resource.src);
            return;
        }
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },

    download_ometiff : function() {
        if (!this.resource.resource_uniq) return;
        var url = '/image_service/image/' + this.resource.resource_uniq + '?format=ome-tiff';
        window.open(url);
    },

    download_omebigtiff : function() {
        if (!this.resource.resource_uniq) return;
        var url = '/image_service/image/' + this.resource.resource_uniq + '?format=ome-bigtiff';
        window.open(url);
    },

    onworking : function(msg) {
        //this.setLoading(msg);

        if (this.gobjectTagger) this.gobjectTagger.setLoading(msg);
        if (this.viewerContainer) {
            this.viewerContainer.setButtonLoading(true);
        };

    },

    ondone : function() {
        //this.setLoading(false);
        if (this.gobjectTagger) this.gobjectTagger.setLoading(false);
        if (this.viewerContainer){
            this.viewerContainer.setButtonLoading(false);
        };

    },

    onerror : function(error) {
        if (this.gobjectTagger) this.gobjectTagger.setLoading(false);
        BQ.ui.error(error.message_short);
    },

    onImagePhys : function(viewer, phys, dims) {

        this.dims = dims;
        if (dims.t>1 || dims.z>1)
            this.toolbar.queryById('menu_view_movie').setDisabled( false );
        if (dims.t>1 || dims.z>1)
            this.toolbar.queryById('menu_view_3d').setDisabled( false );

        if (dims.x>10000 && dims.y>10000) {
            this.toolbar.queryById('menu_view_movie').setDisabled( true );
            this.toolbar.queryById('menu_view_3d').setDisabled( true );
        }

        if (dims.x>15000 && dims.y>15000) {
            BQApp.getToolbar().queryById('download_as_ometiff').setDisabled( true );
            BQApp.getToolbar().queryById('download_as_omebigtiff').setDisabled( true );
        }

        if (!BQ.util.isWebGlAvailable()) {//if webgl isn't available then we'll disable the command.
            var button3D = this.toolbar.queryById('menu_view_3d');
            button3D.setText('3D (WebGl not available)');
            button3D.setTooltip('Enable WebGl to access viewer.');
            button3D.setDisabled( true );
        }

    },

    show2D : function() {
        var btn = this.queryById('button_view');
        btn.setText('View: 2D');
        btn.setIconCls('view2d');

        var image2d = this.queryById('main_view_2d');
        if (image2d && image2d.isVisible()) return;

        var movie = this.queryById('main_view_movie');
        if (movie) {
            movie.setVisible(false);
            movie.destroy();
        }

        var image3d = this.queryById('main_view_3d');
        if (image3d) {
            image3d.setVisible(false);
            image3d.destroy();
        }

        image2d.setVisible(true);
    },

    showMovie : function() {
        var btn = this.queryById('button_view');
        btn.setText('View: Movie');
        btn.setIconCls('movie');

        var movie = this.queryById('main_view_movie');
        if (movie && movie.isVisible()) return;

        var image2d = this.queryById('main_view_2d');
        if (image2d) {
            image2d.setVisible(false);
            //image2d.destroy(); // do not destroy to really fast return
        }

        var image3d = this.queryById('main_view_3d');
        if (image3d) {
            image3d.setVisible(false);
            image3d.destroy();
        }

        var cnt = this.queryById('main_container');
        cnt.add({
            //region : 'center',
            xtype: 'bq_movie_viewer',
            itemId: 'main_view_movie',
            resource: this.resource,
            toolbar: this.toolbar,
            phys: this.viewerContainer.viewer.imagephys,
            preferences: this.viewerContainer.viewer.preferences,
        });
        var movie = cnt.queryById('main_view_movie');
        //var download = this.toolbar.queryById('btnDownload');
        var download = BQApp.getToolbar().queryById('button_download');
        var qt = download.menu.queryById('download_movie_qt');
        if (!qt) {
            download.menu.add([{
                xtype: 'menuseparator',
            }, {
                itemId: 'download_movie_h264',
                text: 'Movie as MPEG4 H264',
                handler: function() { movie.export('h264'); },
            }, {
                itemId: 'download_movie_qt',
                text: 'Movie as Apple QuickTime (MOV)',
                handler: function() { movie.export('quicktime'); },
            }, {
                itemId: 'download_movie_webm',
                text: 'Google WebM',
                handler: function() { movie.export('webm'); },
            }, {
                itemId: 'download_movie_avi',
                text: 'Microsoft AVI (MPEG4)',
                handler: function() { movie.export('avi'); },
            }, {
                itemId: 'download_movie_wmv',
                text: 'Windows Media Video',
                handler: function() { movie.export('wmv'); },
            }, {
                itemId: 'download_movie_flv',
                text: 'Adobe Flash Video',
                handler: function() { movie.export('flv'); },
            }]);

        }
    },

    show3D : function() {
        var me = this;
        if(!BQ.util.isWebGlAvailable()) return;

        //try{
            var btn = this.queryById('button_view');
            btn.setText('View: 3D');
            btn.setIconCls('view3d');

            var image3d = this.queryById('main_view_3d');
            if (image3d && image3d.isVisible()) return;

            var image2d = this.queryById('main_view_2d');
            if (image2d) {
                image2d.setVisible(false);
                //image2d.destroy(); // do not destroy to really fast return
            }

            var movie = this.queryById('main_view_movie');
            if (movie) {
                movie.setVisible(false);
                movie.destroy();
            }

            var cnt = this.queryById('main_container');

            cnt.add({
                //region : 'center',
                xtype: 'bq_volume_panel',
                itemId: 'main_view_3d',
                resource: this.resource,
                toolbar: this.toolbar,
                phys: this.viewerContainer.viewer.imagephys,
                preferences: this.viewerContainer.viewer.preferences,
                listeners: {
                    select_gobject : function(viewer, gob) {
                        var node = me.gobjectTagger.findNodeByGob(gob);
                        if (!node) {
                            console.log('No node found!');
                            return;
                        }
                        // dima: here expand to expose the selected node
                        var parent = node;
                        for (var i=0; i<node.getDepth()-1; i++)
                            parent = parent.parentNode;
                        me.gobjectTagger.tree.expandNode( parent, true );
                        me.gobjectTagger.tree.getSelectionModel().select(node);
                    },

                    glcontextlost: function(event){
                        var msgText = " ";
                        var link = " mailto:me@example.com"
                            + "?cc=myCCaddress@example.com"
                            + "&subject=" + escape("This is my subject")
                            + "&body=" + msgText + "";

                        BQ.ui.error("Hmmm... WebGL seems to hit a snag: <BR/> " +
                                    "error: " + event.statusMessage +
                                    "<BR/>Do you want to report this problem?" +
                                    "<a href = " + link + "> send mail </a>");

                        var image3d = me.queryById('main_view_3d');
                        var toolMenu = image3d.toolMenu;
                        toolMenu.destroy();
                        image3d.destroy();
                        //this should destroy the 3D viewer
                        me.show2D();
                    },

                }
            });
    //}
    /*
        catch(err){
            BQ.ui.error("This is strange, the volume renderer failed to load. <BR/>" +
                        "The reported error is: <BR/> " +
                        err.message);
            me.show2D();
        }
    */
    },

    getEmbedCode : function() {
        var movie = this.queryById('main_view_movie'),
            image3d = this.queryById('main_view_3d'),
            host = location.origin,
            url = this.resource.uri,
            view = '2d',
            embed = '<iframe width="854" height="510" src="{0}/client_service/embedded?view={1}&resource={2}" frameborder="0" allowfullscreen></iframe>';
        if (image3d) {
            view = '3d';
        } else if (movie) {
            view = 'movie';
        }
        embed = Ext.String.format(embed, host, view, url);
        Ext.Msg.prompt('Embed code', 'Embed code:', null, this, false, embed);
    },

});
