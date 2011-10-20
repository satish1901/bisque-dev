/*
 @class BQ.grid.plugin.RowEditing
 @extends Ext.grid.plugin.RowEditing
  
 This is just a error fix for original Ext.grid.plugin.RowEditing
 
 Author: Dima Fedorov 
*/
Ext.define('BQ.grid.plugin.RowEditing', {
    extend: 'Ext.grid.plugin.RowEditing',
    alias: 'bq.rowediting',

    requires: [
        'Ext.grid.RowEditor'
    ],

    cancelEdit: function() {
        var me = this;
        me.callParent();
        
        var form = me.getEditor().getForm();
        if (!form.isValid())
            me.fireEvent('canceledit', me.grid, {});
    },

});
