/* Abstract Mex resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Mex', {
    extend : 'Bisque.Resource',

    afterRenderFn : function() {
        this.setData('renderedRef', this);

        if (this.getData('fetched') == 1)
            this.updateContainer();
    },

   afterRenderFn : function(me) {
        if (!this.ttip) {
            this.ttip = Ext.create('Ext.tip.ToolTip', {
                target : me.id,
                anchor : 'right',
                anchorToTarget : true,
                width : 500,

                cls : 'LightShadow',
                layout : 'fit',
                listeners : {
                    afterrender : function(me) {
                        if (!this.tagsLoaded)
                            me.setLoading('');
                    },
                    scope : this
                }
            });
        }

        this.callParent(arguments);
    },

    onMouseEnter : function() {
        if (!this.tagsLoaded) {
            Ext.Ajax.request({
                url: this.resource.uri,
                method: 'GET',
                params : {
                    view: 'start-time,end-time,inputs',
                },
                callback: function(opts, succsess, response) {
                    if (response.status>=400)
                        BQ.ui.error(response.responseText);
                    else
                        this.tagData(response.responseXML);
                },
                scope: this,
                disableCaching: false,
            });  
        }
        this.callParent(arguments);
    },

    onMouseLeave : function(e) {
        this.mouseIn = false;
        this.callParent(arguments);
    },

    tagData : function(xml) {
        var start = BQ.util.xpath_string(xml, '*/tag[@name="start-time"]/@value'),
            finish = BQ.util.xpath_string(xml, '*/tag[@name="end-time"]/@value'),
            inputs = BQ.util.xpath_nodes(xml, '*/tag[@name="inputs"]/tag'),
            ds = new Date(),
            de = new Date(),
            elapsed=null, t=null, n=null, v=null, html=null;

        ds.setISO8601(start);
        de.setISO8601(finish);
        elapsed = new DateDiff(de - ds);

        html = Ext.String.format('<h2>{0}</h2>', this.resource.name);
        html += Ext.String.format('<p>Status: {0}</p>', this.resource.value);
        html += Ext.String.format('<p>Started: {0}</p>', start);
        html += Ext.String.format('<p>Finished: {0} ({1})</p>', finish, elapsed.toString());

        // inputs
        html += '<h3>Inputs</h3>';
        for (var i=0; (t=inputs[i]); ++i) {
            n = t.getAttribute('name');
            v = t.getAttribute('value');
            if (v)
                html += Ext.String.format('<p>{0}: {1}</p>', n, v);
        }

        this.ttip.add({
            xtype: 'tbtext',
            cls: 'mex_preview',
            text: html,
        });
        
        this.ttip.setLoading(false);
        this.tagsLoaded = true;
        //this.resource.tags = data.tags;
    },    

    prefetch : function() {
        if (!this.getData('fetched')) {
            this.setData('fetched', -1);
            this.loadResource();
        }
    },

    loadResource : function(moduleInfo) {
        this.setData('module', this.resource.name);
        this.setData('fetched', 1);
        var renderedRef = this.getData('renderedRef');
        if (renderedRef)
            renderedRef.updateContainer();
    },    

});

Ext.define('Bisque.Resource.Mex.Compact', {
    extend : 'Bisque.Resource.Mex',

    layout : {
        type : 'vbox',
        align : 'stretch',
    },

    constructor : function() {
        this.callParent(arguments);
        this.addCls('compact');
    },

    updateContainer : function() {
        var date = Ext.Date.parse(this.resource.ts, BQ.Date.patterns.BisqueTimestamp);

        this.add([{
            xtype:'tbtext',
            cls : 'title',
            text : Ext.String.ellipsis(this.resource.name || 'undefined', 24),
        }, {
            xtype:'tbtext',
            cls : 'mex_status ' + this.resource.value,
            text : this.resource.value,
        }, {
            xtype:'tbtext',
            cls : 'date',
            text : Ext.Date.format(date, BQ.Date.patterns.ISO8601Long),
        }]);
        this.setLoading(false);
    },

});

Ext.define('Bisque.Resource.Mex.Card', {
    extend : 'Bisque.Resource.Card',

    prefetch : function(layoutMgr) {
        this.superclass.superclass.prefetch.apply(this, arguments);

        if (!this.getData('fetched')) {
            this.setData('fetched', -1);
            //Loading
            BQFactory.load(this.resource.uri + '/tag?view=deep', Ext.bind(this.loadResource, this));
        }
    },

    loadResource : function(data) {
        this.resource.tags = data.tags;
        var tagProp, tagArr = [], tagsFlat = this.resource.toDict(true);

        // Show preferred tags first
        for (var tag in tagsFlat) {
            tagProp = new Ext.grid.property.Property({
                name : tag,
                value : tagsFlat[tag]
            });
            tagArr.push(tagProp);
            //(tag.indexOf('inputs')!=-1 || tag.indexOf('outputs')!=-1)?tagArr.unshift(tagProp):tagArr.push(tagProp);
        }

        tagArr.unshift(new Ext.grid.property.Property({
            name : 'Status',
            value : this.resource.value
        }));
        tagArr.unshift(new Ext.grid.property.Property({
            name : 'Module',
            value : this.resource.name
        }));

        this.setData('tags', tagArr);
        this.setData('fetched', 1);
        //Loaded

        var renderedRef = this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
});

Ext.define('Bisque.Resource.Mex.Full', {
    extend : 'Bisque.Resource.Full',

    loadResource : function(data) {
        this.resource.tags = data.tags;
        var tagProp, tagArr = [], tagsFlat = this.resource.toDict(true);

        // Show preferred tags first
        for (var tag in tagsFlat) {
            tagProp = new Ext.grid.property.Property({
                name : tag,
                value : tagsFlat[tag]
            });
            tagArr.push(tagProp);
        }

        tagArr.unshift(new Ext.grid.property.Property({
            name : 'Status',
            value : this.resource.value
        }));
        tagArr.unshift(new Ext.grid.property.Property({
            name : 'Module',
            value : this.resource.name
        }));

        this.setData('tags', tagArr);
        this.setData('fetched', 1);
        //Loaded

        var renderedRef = this.getData('renderedRef')
        if (renderedRef && !renderedRef.isDestroyed)
            renderedRef.updateContainer();
    },
});

Ext.define('Bisque.Resource.Mex.List', {
    extend : 'Bisque.Resource.Mex',

    layout: {
        type: 'hbox',
        align: 'middle',
    },

    constructor : function() {
        this.callParent(arguments);
        this.addCls('list');
    },

    updateContainer : function() {
        var date = Ext.Date.parse(this.resource.ts, BQ.Date.patterns.BisqueTimestamp);
        this.add([{
            xtype:'tbtext',
            text : this.resource.name,
            cls : 'title',
            flex : 1,
        }, {
            xtype:'tbtext',
            cls : 'mex_status ' + this.resource.value,
            text : this.resource.status,
            //cls : this.resource.status == 'FINISHED' ? 'lblModuleOwnerFin' : (this.resource.status == 'FAILED' ? 'lblModuleOwnerFail' : 'lblModuleOwner')
        }, {
            xtype:'tbtext',
            text : Ext.Date.format(date, BQ.Date.patterns.ISO8601Long),
            cls : 'lblModuleDate',
        }]);

        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Mex.Grid', {
    extend : 'Bisque.Resource.Mex',

    getFields : function(cb) {
        var status = this.resource.status || 'unknown', resource = this.resource;
        var color = (status == 'FINISHED') ? '#1C1' : (status == 'FAILED') ? '#E11' : '#22F';

        return ['', resource.name || '', '<div style="color:' + color + '">' + Ext.String.capitalize(status.toLowerCase()) + '</div>' || '', resource.resource_type, resource.ts, this, {
            height : 21
        }];
    }
});

// Page view for a mex
/*Ext.define('Bisque.Resource.Mex.Page',
 {
 extend : 'Bisque.Resource.Page',

 constructor : function(config)
 {
 window.location = BQ.Server.url('/module_service/'+config.resource.name+'/?mex='+config.resource.uri);
 }
 });*/

