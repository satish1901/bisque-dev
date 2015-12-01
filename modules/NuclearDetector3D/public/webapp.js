/*******************************************************************************

  BQ.renderers.multiroot.Image

  Author: Dima Fedorov

  Version: 1

  History:
    2015-11-25 13:57:30 - first creation

*******************************************************************************/


// overwrite standard renderer with our own
BQ.renderers.resources.image = 'BQ.renderers.nd3d.Image';

// provide our renderer
Ext.define('BQ.renderers.nd3d.Image', {
    extend: 'BQ.renderers.Image',

    afterRender : function() {
        this.callParent();
        this.queryById('bar_bottom').add({
            xtype: 'tbspacer',
            width: '30%',
        }, {
            xtype: 'slider',
            width: 200,
            value: 0,
            increment: 1,
            minValue: 0,
            maxValue: 100,
            listeners: {
                scope: this,
                change: this.doFilter,
            },
        }, {
            xtype: 'tbspacer',
            width: 20,
        }, {
            xtype:'button',
            text: 'Save',
            tooltip: 'Save filtered results into the module execution document',
            scope: this,
            handler: this.save,
        });
    },

    doFilter : function(slider, newvalue) {
        BQGObject.confidence_cutoff = newvalue;
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
                var confidence = g.gobjects[0].tags[0].value;
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

});

