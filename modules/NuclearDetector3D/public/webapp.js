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
        // filter gobjects first
        //this.gobjects.save();
    },

});

