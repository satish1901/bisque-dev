Ext.define('BQ.ResourceViewer', 
{
    extend : 'Ext.Component',

    statics : 
    {
        dispatch : function(resource) 
        {
            if (resource instanceof BQObject)
                this.initViewer(resource);
            else
                this.loadResource(resource);
        },
        
        loadResource : function(resourceURL) 
        {
            BQFactory.request({
                uri         :   resourceURL,
                uri_params  :   {view : 'deep'},
                cb          :   this.initViewer,
                errorcb     :   this.initViewer
            });
        },
        
        initViewer : function(resource) 
        {
            BQApp.resource = resource;
            
            var resourceCt = Bisque.ResourceFactoryWrapper.getResource({
                resource    :   resource,
                layoutKey   :   Bisque.ResourceBrowser.LayoutFactory.LAYOUT_KEYS.Page 
            });
            
            BQApp.setCenterComponent(resourceCt);
        }
    }
});
