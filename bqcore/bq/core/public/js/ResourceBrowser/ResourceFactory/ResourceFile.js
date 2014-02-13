// Page view for a File
Ext.define('Bisque.Resource.File.Page', {
    extend : 'Bisque.Resource.Page',

    downloadOriginal : function() {
        if (this.resource.src) {
            window.open(this.resource.src);
            return;
        }
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },
});

