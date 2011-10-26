///////////////////////////////////////////////////////
// master viewer for different types of resources

Ext.Loader.setConfig(
{
    enabled : true
});
Ext.Loader.setPath('Ext.ux', '/extjs/examples/ux');
Ext.require(['Ext.window.*', 'Ext.ux.GMapPanel']);

function ResourceDispatch(user_url, imagediv, tagdiv)
{
    this.user_url = user_url;
    this.imagediv = imagediv;
    this.tagdiv = tagdiv;
}

ResourceDispatch.prototype.dispatch = function(resource) {
    if (!resource || resource == '') return;
    resource = decodeURIComponent(resource);
    
    if(resource.match(/\/data_service\/images\/\d+$/)) {
        BQFactory.load(resource, callback(this, 'dispatch_image'));
    }
    else
    if(resource.match(/\/data_service\/dataset/)) {
        BQApp.main.getComponent('centerEl').setLoading(true);
        BQFactory.request( {uri: resource, uri_params: {view:'deep'}, cb: callback(this, 'dispatch_dataset') }); 
    }
    else
    if(resource.match(/\/image_service\//)) {
        window.location = resource;
    }
    else {
        //var bq = new BQObject(resource);
        BQFactory.load(resource, callback(this, 'dispatch_other'));
    }
};

ResourceDispatch.prototype.dispatch_image = function(bqimage)
{
    BQApp.resource = bqimage;

    var resourceTagger = Ext.create('Bisque.ResourceTagger', 
    {
        resource : bqimage,
        title : 'Tagger',
    });

    var embeddedTagger = Ext.create('Bisque.ResourceTagger', {
        resource : bqimage.src + '?meta',
        title : 'Embedded',
        viewMode : 'ViewerOnly',
    });

    var mexBrowser = new Bisque.ResourceBrowser.Browser(
    {
        'layout' : 5,
        'title' : 'Execution Results',
        'viewMode' : 'MexBrowser',
        'dataset' : '/data_service/mex',
        'tagQuery' : Ext.String.format('"{0}":"{1}"', 'image_url', ( bqimage instanceof BQObject) ? bqimage.uri : bqimage),
        'wpublic' : true,

        mexLoaded : false,

        listeners :
        {
            'browserLoad' : function(me, resQ)
            {
                me.mexLoaded = true;
            },
            'Select' : function(me, resource)
            {
                me.setLoading(true);
                var nw = window.open('', "_blank");
                BQFactory.request(
                {
                    uri : resource.module,
                    cb : function(r)
                    {
                        me.setLoading(false);
                        //window.open(bq.url('/module_service/' + r.name + '/?mex=' + resource.uri), "", "menubar=yes,location=yes,resizable=yes,scrollbars=yes,status=yes");
                        nw.location = bq.url('/module_service/' + r.name + '/?mex=' + resource.uri);
                    }

                });
            }, scope:this

        }
    });

    var resTab = Ext.create('Ext.tab.Panel',
    {
        title : 'Metadata',

        region : 'east',
        activeTab : 0,
        border : false,
        bodyBorder : 0,
        collapsible : true,
        split : true,
        width : 480,
        plain : true,
        bodyStyle : 'background-color:#F00',
        items : [resourceTagger, embeddedTagger, mexBrowser]
    });
    
    var imageCt = new Ext.container.Container(
    {
        region : 'center',
        padding : 2,
        style : 'background-color:#FFF',

        listeners :
        {
            'resize' : function(me, width, height)
            {
                if(me.IV)
                    //me.IV.resize( {height : height} );
                    me.IV.resize();
            }

        }
    });

    BQApp.main.getComponent('centerEl').add(
    {
        xtype : 'container',
        layout : 'border',
        items : [imageCt, resTab]
    });

    imageCt.IV = new ImgViewer(imageCt.getId(), bqimage, this.user_url);
    //imageCt.doComponentLayout(null, null, true);

    var gobjectTagger = new Bisque.GObjectTagger(
    {
        resource : bqimage,
        imgViewer : imageCt.IV,
        mexBrowser : mexBrowser,
        title : 'GObjects',
        viewMode : 'ViewerOnly',
        listeners :
        {
            'beforeload' : function(me, resource)
            {
                me.imgViewer.start_wait(
                {
                    op : 'gobjects',
                    message : 'Fetching gobjects'
                });
            },
            'onload' : function(me, resource)
            {
                me.imgViewer.loadGObjects(resource.gobjects, false);

                if(me.mexBrowser.mexLoaded)
                    me.appendFromMex(me.mexBrowser.resourceQueue);
                else
                    me.mexBrowser.on('browserLoad', function(mb, resQ)
                    {
                        me.appendFromMex(resQ);
                    }, me);

            },
            'onappend' : function(me, gobjects)
            {
                me.imgViewer.gobjectsLoaded(true, gobjects);
            },

            'select' : function(me, record, index)
            {
                var gobject = (record.raw instanceof BQGObject)?record.raw:record.raw.gobjects;
                me.imgViewer.showGObjects(gobject);
            },

            'deselect' : function(me, record, index)
            {
                var gobject = (record.raw instanceof BQGObject)?record.raw:record.raw.gobjects;
                me.imgViewer.hideGObjects(gobject);
            }
        }
    });
    resTab.add(gobjectTagger);
   
    var map = Ext.create('BQ.gmap.GMapPanel3',  {
        title: 'Map',
        url: bqimage.src+'?meta',
        zoomLevel: 16,
        gmapType: 'map',
        autoShow: true,
    });
    resTab.add(map);
};

ResourceDispatch.prototype.dispatch_dataset = function(resource) {
    BQApp.resource = resource;
    BQApp.main.getComponent('centerEl').setLoading(false);
    var resourcesBrowser = new Bisque.ResourceBrowser.Browser({
        dataset: resource.getMembers().uri+'/values',
        height: '100%',   
        selType: 'SINGLE',
        //viewMode : 'ViewerOnly',
        listeners : { 'Select': function(me, resource) { 
                      window.open(bq.url('/client_service/view?resource='+resource.uri)); 
                    }, 
                   scope: this },
    });  

    BQApp.main.getComponent('centerEl').add({
        xtype : 'container',
        layout : 'fit',
        items : [resourcesBrowser]
    });

    
};


ResourceDispatch.prototype.dispatch_other = function(resource)
{
    BQApp.resource = resource;

    var resourceTagger = new Bisque.ResourceTagger(
    {
        region : 'north',
        resource : resource,
        split : true
    });

    var resourceCt = new Ext.container.Container(
    {
        region : 'center',
        height : 480,
        split : true,
        padding : 2,
        style : 'background-color:#FFF',
        id : 'resourceCt',
    });

    BQApp.main.getComponent('centerEl').add(
    {
        xtype : 'container',
        layout : 'border',
        items : [resourceTagger, resourceCt]
    });

    var rv = new ResourceViewer('resourceCt', resource, this.user_url);
};

function ResourceViewer(resourcediv, resource, user)
{
    this.target = getObj(resourcediv);
    this.resourceuri = resource;
    // Toplevel Image URI
    this.user = user;

    this.menudiv = document.createElementNS(xhtmlns, "div");
    this.menudiv.setAttributeNS(null, "id", "tagmenu");
    this.menudiv.className = "buttonbar";
    this.target.appendChild(this.menudiv);
    this.groups =
    {
    };
    this.target.appendChild(this.menudiv);
    this.titlediv = document.createElementNS(xhtmlns, "div");
    this.target.appendChild(this.titlediv);

    if( resource instanceof BQObject)
        this.newResource(resource);
    else
        this.load(resource);
}

ResourceViewer.prototype.load = function(uri)
{
    this.resourceuri = uri;
    var tv = this;
    BQFactory.load(this.resourceuri, callback(tv, 'newResource'));
}

ResourceViewer.prototype.newResource = function(bq)
{
    this.resource = bq;

    var nm = document.createElementNS(xhtmlns, 'b');
    this.titlediv.appendChild(nm);

    //var name = bq.attributes['name'] || bq.attributes['uri'];
    var name = bq.name || bq.uri;
    var type = bq.type || bq.xmltag;
    var title = "Editing " + type + ' ' + name;

    nm.textContent = title;
}