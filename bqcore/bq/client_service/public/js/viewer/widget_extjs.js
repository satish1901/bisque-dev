/*******************************************************************************
  ExtJS wrapper for the Bisque image viewer
  Author: Dima Fedorov <dima@dimin.net>
  
  Configurations:
      resource   - url string or bqimage
      user       - url string
      parameters - viewer configuration object describied later
  
  Events:
      loaded     - event fired when the viewer is loaded
      changed    - event fired when the gobjects in the viewer have changed
        
  Parameters:
    simpleviewer   - sets a minimal set of plug-ins and also read-only view for gobjects
    onlyedit       - only sets plug-in needed for editing of gobjects 

    nogobects      - disable loading gobjects by default
    gobjects       - load gobjects from the givel URL, 'gobjects':'http://gobejcts_url' or a BQGobject or a vector of BQGObject

    noedit         - read-only view for gobjects
	  alwaysedit     - instantiates editor right away and disables hiding it
	  nosave         - disables saving gobjects
	  editprimitives - only load edit for given primitives, 'editprimitives':'point,polyline'
	                   can be one of: 'Point,Rectangle,Polyline,Polygon,Circle'  

  Example:
    var myviewer = Ext.create('BQ.viewer.Image', {
        resource: 'http://image_url',
        user: 'user_name',
        parameters: {
            'gobjects': 'http://gobejcts_url', 
            'noedit': '',
        },
    });     
*******************************************************************************/

Ext.define('BQ.viewer.Image', {
    alias: 'widget.imageviewer',    
    extend: 'Ext.container.Container',
    requires: ['ImgViewer'],
    
    border: 0,
    cls: 'bq-image-viewer',

    constructor: function(config) {
        this.addEvents({
            'loaded': true,
            'changed': true,            
        });
        this.callParent(arguments);
        this.parameters = {};
        return this;
    },

    initComponent : function() {
        this.bq_user = new BQUser();
        if (this.resource && typeof this.resource === 'string') {
            this.setLoading('Loading image resource');
            BQFactory.request( {uri: this.resource, uri_params: {view:'short'}, cb: callback(this, 'loadViewer') }); 
        } 
 
        this.addListener( 'resize', function(me, width, height) {
            if (me.viewer) me.viewer.resize();   
        });
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.loadViewer(this.resource);
    },

    loadViewer: function(resource) {
        if (!resource) return;        
        this.setLoading(false);
        if (this.loaded) return;
        this.loaded = true;

        //if (!this.user || typeof this.user != 'string')
        //    this.user = BQSession.current_session.user?BQSession.current_session.user.uri:null;
        this.user = null;
        
        this.parameters.gobjectschanged = callback(this, 'onchanged');
        this.viewer = new ImgViewer(this.getId(), resource, this.user, this.parameters);   
        this.fireEvent( 'loaded', this ); 
        this.viewer.resize();     
    },

    onchanged : function(gobs) {
        this.fireEvent( 'changed', this );
    },

    getGobjects : function() {
        if (!this.viewer) return undefined;
        return this.viewer.gobjects();
    },

});

