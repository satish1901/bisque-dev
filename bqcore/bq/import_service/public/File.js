/*******************************************************************************

  BQ.upload.File - an extension and fix for file field with multiple
    file selection

  Author: Dima Fedorov
  
  Version: 1, based on Ext 4.0.7
  
  History: 
    2012-02-10 12:08:48 - first creation
    
*******************************************************************************/

Ext.define('BQ.upload.File', {
    extend: 'Ext.form.field.File',
    alias: ['widget.filemultifield', 'widget.filemultiuploadfield'],

    /**
     * @cfg {Boolean} multiple enables multiple file selection
     */
    multiple: false,

    // private
    afterRender : function() {
        this.callParent();

        // make sure input is a multi file select
        var e = this.fileInputEl;
        if (e && e.dom) {
            e.dom.multiple = this.multiple;
            
            // fix for the error in proxying event into file input
            var h = this.getHeight()+5;
            e.dom.style.height =''+h+'px';
        }
    },  

});

