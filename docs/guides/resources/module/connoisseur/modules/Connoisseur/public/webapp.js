/*******************************************************************************

  BQ.renderers.connoisseur.Image

  Author: Dima Fedorov

  Version: 1

  History:
    2015-11-25 13:57:30 - first creation

*******************************************************************************/

/*
// BQPoint override
function BQPoint(ty, uri){
    BQObject.call(this, uri);
    this.type = 'point';
    this.uri=null;
    this.name = null;
    this.vertices = [];
    this.resource_type = "gobject";
    this.default_alpha = 1.0;
};
BQPoint.prototype = new BQGObject();

BQPoint.prototype.initializeXml = function (node) {
    BQGObject.prototype.initializeXml.call(this, node);

    var t = BQ.util.xpath_node(node, 'tag[@name="confidence"]');
    if (t)
        this.confidence = parseFloat(t.getAttribute('value'));
};

// BQPolygon override
function BQPolygon(ty, uri){
    BQObject.call(this, uri);
    this.type = 'polygon';
    this.uri=null;
    this.name = null;
    this.vertices = [];
    this.resource_type = "gobject";
    this.default_alpha = 0.5;
};
BQPolygon.prototype = new BQPoint();
*/

// overwrite standard renderer with our own
Ext.onReady( function() {
    BQ.renderers.resources.image = 'BQ.renderers.connoisseur.Image';

    //BQFactory.objects.point = BQPoint;
    //BQFactory.ctormap.point = BQPoint;
    //BQFactory.objects.polygon = BQPolygon;
    //BQFactory.ctormap.polygon = BQPolygon;
}); // Ext.onReady


// provide our renderer
Ext.define('BQ.renderers.connoisseur.Image', {
    extend: 'BQ.renderers.Image',

    afterRender : function() {
        this.coloring_modes = Ext.create('Ext.data.Store', {
            fields: ['name', 'tag'],
            data : [
                {'name': 'Class', 'tag': ''},
                {'name': 'Confidence', 'tag': 'confidence'},
                {'name': 'Class accuracy', 'tag': 'accuracy'},
                {'name': 'Sample goodness', 'tag': 'goodness'}
            ]
        });

        this.callParent();
        this.queryById('bar_bottom').add({
            xtype: 'combobox',
            fieldLabel: 'Colored by ',
            store: this.coloring_modes,
            queryMode: 'local',
            displayField: 'name',
            valueField: 'tag',
            allowBlank: false,
            editable: false,
            labelAlign: 'right',
            value: 'Class',
            listeners: {
                scope: this,
                change: this.recolor,
            },
        }, /*{
            xtype: 'button',
            itemId: 'button_coloring',
            text: 'Colored by class',
            enableToggle: true,
            pressed: true,
            scope: this,
            handler: this.recolor,
        },*/ {
            xtype: 'tbspacer',
            width: 10,
        },/* {
            xtype: 'colorfield',
            itemId: 'color1',
            cls: 'simplepicker',
            labelWidth: 0,
            name: 'color1',
            value: '0000ff',
            listeners: {
                scope: this,
                change: this.onNewGradient,
            },
        }, {
            xtype: 'colorfield',
            itemId: 'color2',
            cls: 'simplepicker',
            labelWidth: 0,
            name: 'color2',
            value: 'ffff00',
            listeners: {
                scope: this,
                change: this.onNewGradient,
            },
        }, {
            xtype: 'tbspacer',
            width: 10,
        }, */{
            xtype: 'slider',
            width: 250,
            value: 0,
            animate: false,
            increment: 1,
            minValue: 0,
            maxValue: 99,
            fieldLabel: 'Filter by confidence',
            listeners: {
                scope: this,
                change: this.onFilter,
            },
        }, {
            xtype: 'tbspacer',
            width: 20,
        }, {
            xtype:'button',
            text: 'Save filtered',
            tooltip: 'Save filtered results into the module execution document',
            scope: this,
            handler: this.save,
        }, {
            xtype: 'tbspacer',
            flex: 1,
        });

        /*
        var me = this;
        BQPoint.prototype.getColor = function (r,g,b,a) {
            if (BQGObject.coloring_mode === 'class' && this.color && this.confidence > BQGObject.confidence_cutoff) {
                return Kinetic.Util._hexToRgb('#' + this.color);
            } else if (typeof(this.confidence) !== 'undefined') {
                if (this.confidence < BQGObject.confidence_cutoff)
                    return {r: 255, g: 0, b: 0, a: 0};
                var cc = Math.max(0, Math.min(100, Math.round(this.confidence)));
                var c = BQGObject.color_gradient[cc];
                return {r: c.r, g: c.g, b: c.b, a: this.default_alpha};
            }
            return {r: r, g: g, b: b, a: a};
        };
        BQPolygon.prototype.getColor = BQPoint.prototype.getColor;
        */
    },

    onFilter : function(slider, newvalue) {
        BQGObject.confidence_cutoff = newvalue;
        var me = this;
        clearTimeout(this.updatetimer);
        this.updatetimer = setTimeout(function(){ me.reRenderGobs(); }, 50);
    },

    doFilter : function() {
        // request re-rendering of gobjects
        this.reRenderGobs();
    },

    save : function() {
        var me = this,
            points = this.gobjects[0];
        this.setLoading('Filtering...');
        // filter gobjects first
        points.gobjects = points.gobjects.filter(function(g){
            try {
                var confidence = g.gobjects[0].getConfidence();
                if (confidence<BQGObject.confidence_cutoff) return false;
            } catch (e) {
                return true;
            }
            return true;
        });

        this.setLoading('Saving...');
        points.save_(
            undefined,
            function() {
                me.setLoading(false);
            },
            function() {
                me.setLoading(false);
                BQ.ui.error('Problem saving filtered points');
            }
        );
    },

    recolor: function(combo, newValue, oldValue) {
        if (newValue === '' || newValue === 'Class') {
            BQGObject.coloring_mode = 'class';
        } else {
            BQGObject.coloring_mode = 'confidence';
            BQGObject.confidence_tag = newValue;
            BQGObject.confidence_mult = BQGObject.confidence_tag !== 'goodness' ? 1.0 : 100.0;
        }
        this.reRenderGobs();
    },

    onNewGradient: function() {
        var c1 = this.queryById('color1').getColor(),
            c2 = this.queryById('color2').getColor();
        bq_create_gradient(c1.r,c1.g,c1.b,1.0, c2.r,c2.g,c2.b,1.0);
        this.reRenderGobs();
    }

});

