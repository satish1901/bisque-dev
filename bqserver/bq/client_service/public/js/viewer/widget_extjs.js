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
      working
      done
      error

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

    blockforsaves  - set to true to show saving of gobjects, def: true


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
        return this;
    },

    initComponent : function() {
        if (this.resource && typeof this.resource === 'string') {
            this.setLoading('Loading image resource');
            BQFactory.request( {uri: this.resource, uri_params: {view:'short'}, cb: callback(this, 'loadViewer') });
        }
        this.addListener( 'resize', function(me, width, height) {
            if (me.viewer) me.viewer.resize();
        });
        this.callParent();
    },

    onDestroy : function(){
        if (this.viewer)
            this.viewer.cleanup();
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.loadViewer(this.resource);
    },

    loadViewer: function(resource) {
        this.setLoading(false);
        if (!resource) return;
        if (this.loaded) return;
        this.loaded = true;
        this.resource = resource;

        this.parameters = this.parameters || {};
        this.parameters.blockforsaves = 'blockforsaves' in this.parameters ? this.parameters.blockforsaves : true;
        if (this.toolbar)
            this.parameters.toolbar = this.toolbar;
        this.parameters.gobjectschanged = callback(this, 'onchanged');
        this.parameters.onworking = callback(this, 'onworking');
        this.parameters.ondone    = callback(this, 'ondone');
        this.parameters.onerror   = callback(this, 'onerror');
        this.parameters.onselect  = callback(this, 'onselect');
        this.parameters.oneditcontrols = callback(this, this.oneditcontrols);

        var id = Ext.getVersion('core').isGreaterThan('4.2.0') ? this.getId()+'-innerCt' : this.getId();
        this.viewer = new ImgViewer(id, this.resource, this.parameters);
        this.fireEvent( 'loaded', this );
        this.viewer.resize();

        // dima: ultra ugly fix laying out toolbar on delay - NEEDS PROPER FIX!!!!
        if (this.toolbar) {
            var element = this.toolbar;
            setTimeout(function(){ element.updateLayout(); }, 1000);
        }
    },

    onchanged : function(gobs) {
        this.fireEvent( 'changed', this, gobs );
    },

    getGobjects : function() {
        if (!this.viewer) return undefined;
        return this.viewer.gobjects();
    },

    // g can be either a url, BQGobject or an array of BQGobject
    setGobjects : function(g) {
        if (!this.viewer) return;
        this.viewer.loadGObjects(g);
    },

    onworking : function(msg) {
        if (this.parameters.blockforsaves) this.setLoading(msg);
        this.fireEvent( 'working', this, msg );
    },

    ondone : function() {
        if (this.parameters.blockforsaves) this.setLoading(false);
        this.fireEvent( 'done', this );
    },

    onerror : function(error) {
        if (this.parameters.blockforsaves) this.setLoading(false);
        BQ.ui.error(error.message);
        this.fireEvent( 'error', this, error );
    },

    onselect : function(gob) {
        this.fireEvent( 'select', this, gob );
    },

    oneditcontrols : function() {
        this.fireEvent( 'edit_controls_activated', this );
    },

});

