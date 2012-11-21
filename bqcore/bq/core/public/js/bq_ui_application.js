/////////////////////////////////////////
// Bisque service and access 

Ext.require(['Ext.util.Observable']);
Ext.require(['Ext.container.Viewport']);

Ext.define('BQ', {
    extend: 'Ext.util.Observable',

    root: '/',
    baseCSSPrefix: 'bq-',

    constructor: function(config) {
        if (typeof(bq) == "undefined")
            bq = {};
        /*
        config = config || {};
        Ext.apply(config, {root: '/'}, bq);
        this.initConfig(config);
        */
        return this.callParent(arguments);        
    },   

    url : function (base, params) {
        if (this.root && this.root != "/")
            return this.root + base;
        return base;
    },
});

// instantiate a global variable, it might get owerwritten later 
bq = Ext.create('BQ');


//--------------------------------------------------------------------------------------
// BQ.Application
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.Application', {
    extend: 'Ext.util.Observable',

    constructor: function(config) {
        this.addEvents({
            "signedin" : true,
            "signedout" : true,
            "gotuser" : true,
            "nouser" : true,                           
        });
        config = config || {};
        this.callParent();

        config.config = config.config || {};                
        this.onReady();        
        this.main = Ext.create('BQ.Application.Window', config.config);
        
        BQSession.initialize_timeout('', { 
            onsignedin: callback(this, this.onSignedIn), 
            onsignedout: callback(this, this.onSignedOut),
            ongotuser: callback(this, this.onGotUser),
            onnouser: callback(this, this.onNoUser),            
        });
        
        return this;
    },
    
    onReady : function()
    {
        // Load user information for all users.
        BQFactory.request({
            uri :   bq.url('/data_service/user?view=deep&wpublic=true'),
            cb  :   Ext.bind(userInfoLoaded, this)
        });
        
        function userInfoLoaded(data)
        {
            this.userList = {};
            
            for (var i=0; i<data.children.length;i++)
                this.userList[data.children[i].uri] = data.children[i];
        }
    },
    
    onSignedIn: function() {
        this.session = BQSession.current_session;
        this.fireEvent( 'signedin', BQSession.current_session);
    },
    
    onSignedOut: function() {
        this.session = undefined;
        this.fireEvent( 'signedout');
        alert("Your session has  timed out");
        window.location = this.url( "/auth_service/logout" );
    },
    
    onGotUser: function() {
        this.user = BQSession.current_session.user;
        this.fireEvent( 'gotuser', BQSession.current_session.user);
        BQ.Preferences.loadUser(BQSession.current_session.user, 'INIT');
    }, 

    onNoUser: function() {
        this.user = null;
        this.fireEvent( 'nouser');
        BQ.Preferences.loadUser(null, 'LOADED');
    }, 

    hasUser: function() {
        return (this.session && this.user);
    },

    getCenterComponent: function() {
        if (this.main)
            return this.main.getCenterComponent();
    },

    setCenterComponent: function(c) {
        if (!this.main) return;
        this.main.setCenterComponent(c);  
    },

    setLoading: function(load, targetEl) {
        if (!this.main) return;
        var w = this.getCenterComponent() || this.main;
        w.setLoading(load, targetEl);
    },

});

//--------------------------------------------------------------------------------------
// BQ.Application.Window
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.Application.Window', {
    extend: 'Ext.container.Viewport',
    requires: ['Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],
   
    id : 'appwindow',
    layout : 'border',
    border : false,
    
    /*
    constructor: function(config) {
        this.initConfig(config);
        return this.callParent(arguments);        
    },
    */    

    initComponent : function() {
        Ext.tip.QuickTipManager.init();
        
        var content = document.getElementById('content');
        if (content && content.children.length<1) {
          document.body.removeChild(content);
          content = undefined;
        }
        
        this.toolbar = Ext.create('BQ.Application.Toolbar', { toolbar_opts: bq.toolbar_opts });
        this.items = [
                this.toolbar, { 
                    region : 'center',
                    id: 'centerEl',
                    layout: 'fit',
                    flex: 3,
                    border : false,
                    header : false,
                    contentEl : content,
                    autoScroll: true,
                }, { 
                    id: 'help',
                    region : 'east',
                    collapsible: true,
                    split: true,
                    layout: 'fit',
                    hidden: true,
                    cls: 'help',
                    width: 320,
                    //flex: 1,
                    border : false,
                }, ];
        
        this.callParent();
    },

    // private
    onDestroy : function(){
        this.callParent();
    },
    
    removeWindowContent: function() {
        var c = this.getComponent('centerEl');
        c.removeAll();
        c.update(''); 
    },

    getCenterComponent: function() {
        return this.getComponent('centerEl');  
    },   

    setCenterComponent: function(c) {
        this.removeWindowContent(); 
        this.getComponent('centerEl').add(c);  
    },    
    
    getHelpComponent: function() {
        return this.getComponent('help');  
    },       
    
});

BQ.Application.Window.prototype.test = function () {
  alert('test');
}

Ext.define('BisqueServices', {
    singleton : true,
    
    constructor : function()
    {
        BQFactory.request(
        {
            uri : '/services',
            cb : Ext.bind(this.servicesLoaded, this)
        });
    },
    
    servicesLoaded : function(list)
    {
        this.services=[];
        
        for (var i=0;i<list.tags.length;i++)
            this.services[list.tags[i].type.toLowerCase()]=list.tags[i];
    },
    
    getURL : function(serviceName)
    {
        var service = this.services[serviceName];
        return (service)?service.value:'';
    }
})

//--------------------------------------------------------------------------------------
// BisqueService
//-------------------------------------------------------------------------------------- 

BisqueService = function (urllist) {
    this.urls = urllist;
    if (this.urls.length) 
        this.url = this.urls[0];
}

BisqueService.prototype.make_url  = function (path, params) {
    var url = this.url;
    if (path) 
        url = url + '/' + path;
    if (params) 
        url = url + '?' +  encodeParameters (params );
    return url;
}
BisqueService.prototype.xmlrequest  = function (path, params, cb, body) {
    var method = null;
    var url = this.make_url (path, params);
    if (body) 
        method = 'post';
    xmlrequest (url, cb, method, body);
}
BisqueService.prototype.request  = function (path, params, cb, body) {
    var method = null;
    var url = this.make_url (path, params);
    if (body) 
        method = 'post';
    BQFactory.request ({ uri:url, callback:cb, method:method, body:body});
}

Bisque = function () {
    this.services = {};
}

Bisque.prototype.init = function () {
    BQFactory.load ("/services", callback (this, 'on_init'));
}
Bisque.prototype.on_init = function (resource) {
    // Each each tag type to 
    var tags = resource.tags;
    for (var i=0; i<tags.length; i++) {
        var ty = tags[i].type;
        var uri = tags[i].value; 
        Bisque[ty] = new BisqueService (uri);
    }
}

Bisque.onReady  = function (f) {
    Ext.onReady (f);
}
Bisque.init_services = function (services) {
    for (var ty in services) {
        Bisque[ty] = new  BisqueService (services[ty]);
    }
}

