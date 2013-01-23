Ext.define('BQ.ResourceViewer', {
    statics : {
        dispatch : function(resource) {
            if (resource instanceof BQObject)
                this.initViewer(resource);
            else
                this.loadResource(resource);
        },
        
        loadResource : function(resourceURL) {
            BQApp.setLoading('Fetching resource...');
            BQFactory.request({
                uri         :   resourceURL,
                uri_params  :   {view : 'deep'},
                cb          :   this.initViewer,
                errorcb     :   this.onError
            });
        },
        
        initViewer : function(resource) {
            BQApp.setLoading(false);
            BQApp.resource = resource;
            var resourceCt = Bisque.ResourceFactoryWrapper.getResource({
                resource    :   resource,
                layoutKey   :   Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Page 
            });
            BQApp.setCenterComponent(resourceCt);
        },

        onError: function(error) {
            BQApp.setLoading(false);
            BQ.ui.error('Error fetching resource: <br>' + error.message);
            this.initViewer();         
        },
    }
});