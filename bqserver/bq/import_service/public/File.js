/*******************************************************************************

  BQ.upload.File - an extension and fix for file field with multiple
    file selection

  Author: Dima Fedorov

  Version: 1, based on Ext 4.0.7

  History:
    2012-02-10 12:08:48 - first creation

*******************************************************************************/

function isInputDirSupported() {
    var tmpInput = document.createElement('input');
    return ('webkitdirectory' in tmpInput
        || 'mozdirectory' in tmpInput
        || 'odirectory' in tmpInput
        || 'msdirectory' in tmpInput
        || 'directory' in tmpInput);
}

Ext.define('BQ.upload.File', {
    extend: 'Ext.form.field.File',
    alias: ['widget.filemultifield', 'widget.filemultiuploadfield'],
    cls: 'bq-upload-file',
    /**
     * @cfg {Boolean} multiple enables multiple file selection
     */
    multiple: false,
    directory: false,

    // private
    afterRender : function() {
        this.callParent();

        // make sure input is a multi file select
        var e = this.fileInputEl;
        if (e && e.dom) {
            e.dom.multiple = this.multiple;
            e.dom.webkitdirectory = this.directory; // allow selecting directories on webkit
            e.dom.nwdirectory = this.directory; // allow selecting directories on node-webkit
            e.dom.mozdirectory = this.directory;
            e.dom.odirectory = this.directory;
            e.dom.msdirectory = this.directory;
            e.dom.directory = this.directory;

            // fix for the error in proxying event into file input
            e.dom.style.width = this.getWidth()+'px';
            e.dom.style.height = this.getHeight()+'px';
        }
    },

});

