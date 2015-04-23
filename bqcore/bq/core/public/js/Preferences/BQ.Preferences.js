Ext.define('BQ.Preferences', {
    mixins: {
        observable: 'Ext.util.Observable',
    },
    singleton : true,
    preference_system_uri: '/preference',
    preference_user_uri: '/preference/user',
    systemXML: undefined,
    userXML: undefined,
    resourceXML: undefined,
    systemDict: undefined,
    userDict: undefined,
    resourceDict: undefined,
    resource_uniq: undefined, //if the preference has a resource set
    
    // load system preferences
    constructor : function() {

        this.addEvents({
            'updatesystempref': true,
            'updateuserpref': true,
            'updateresourcepref': true,
        })
        this.mixins.observable.constructor.call(this);
        this.loadSystem();
        this.loadUser();
    },
    
    loadSystem : function(cb) {
        var me = this;
        Ext.Ajax.request({
            method: 'GET',
            url: '/preference',
            params: {view:'deep'},
            disableCaching: false,
            success: function(response) {
                BQ.Preferences.systemXML = response.responseXML;
                BQ.Preferences.systemDict = BQ.Preferences.toDict(BQ.Preferences.systemXML);
                BQ.Preferences.fireEvent('updatesystempref', BQ.Preferences, BQ.Preferences.systemDict, BQ.Preferences.systemXML);
                if (cb) cb(BQ.Preferences.systemDict, BQ.Preferences.systemXML);
            },
            failure: function(response) {
                BQ.ui.error('failed to load system preference')
            },
            scope: me,
        })
    },

    // bq_ui_application raises event loadUser
    loadUser : function(cb) {
        var me = this;
        Ext.Ajax.request({
            method: 'GET',
            url: '/preference/user',
            params: {view:'deep'},
            disableCaching: false,
            success: function(response) {
                BQ.Preferences.userXML = response.responseXML;
                BQ.Preferences.userDict = BQ.Preferences.toDict(BQ.Preferences.userXML);
                BQ.Preferences.fireEvent('updateuserpref', BQ.Preferences, BQ.Preferences.userDict, BQ.Preferences.userXML);
                if (cb) cb(BQ.Preferences.userDict, BQ.Preferences.userXML);
            },
            failure: function(response) {
                BQ.ui.error('failed to load user preference')
            },
            scope: me,
        });
    },
    
    loadResource: function(uniq, cb) {
        var me = this;
        BQ.Preferences.resource_uniq = uniq;
        Ext.Ajax.request({
            method: 'GET',
            url: '/preference/user/'+uniq,
            params: {view:'deep'},
            disableCaching: false,
            success: function(response) {
                BQ.Preferences.resourceXML = response.responseXML;
                BQ.Preferences.resourceDict = BQ.Preferences.toDict(BQ.Preferences.resourceXML);
                BQ.Preferences.fireEvent('updateresourcepref', BQ.Preferences, BQ.Preferences.userDict, BQ.Preferences.userXML);
                if (cb) cb(BQ.Preferences.resourceDict, BQ.Preferences.resourceXML);              
            },
            failure: function(response) {
                BQ.ui.error('failed to load user preference')
            },
            scope: me,
        });
    },
    
    updateSystem: function(body, cb) {
        var me = this;
        Ext.Ajax.request({
            method: 'PUT',
            url: '/preference',
            params: {view:'deep'},
            disableCaching: false,
            xmlData: body,
            success: function(response) {
                BQ.Preferences.systemXML = response.responseXML;
                BQ.Preferences.systemDict = BQ.Preferences.toDict(me.systemXML);
                BQ.Preferences.fireEvent('updatesystempref', BQ.Preferences, BQ.Preferences.systemDict, BQ.Preferences.systemXML);
                
                //reload lower levels
                BQ.Preferences.loadUser();
                if (BQ.Preferences.resource_uniq) {
                    BQ.Preferences.loadResource(BQ.Preferences.resource_uniq);
                }
                
                if (cb) cb(BQ.Preferences.systemDict, BQ.Preferences.systemXML);
            },
            failure: function(response) {
                BQ.ui.error('failed to update system preference')
            },
            scope: me,
        });        
    },
    
    updateUser: function(body, cb) {
        var me = this;
        Ext.Ajax.request({
            method: 'PUT',
            url: '/preference/user',
            params: {view:'deep'},
            disableCaching: false,
            xmlData: body,
            success: function(response) {
                BQ.Preferences.userXML = response.responseXML;
                BQ.Preferences.userDict = BQ.Preferences.toDict(BQ.Preferences.userXML);
                BQ.Preferences.fireEvent('updateuserpref', BQ.Preferences, BQ.Preferences.userDict, BQ.Preferences.userXML);
                
                //reload lower level
                if (BQ.Preferences.resource_uniq) {
                    BQ.Preferences.loadResource(BQ.Preferences.resource_uniq);
                }
                
                if (cb) cb(BQ.Preferences.userDict, BQ.Preferences.userXML);
                //me.fireEvent('updateUser', me, me.userDict);
                //me.fireEvent('updateResource', me, me.userDict);
            },
            failure: function(response) {
                BQ.ui.error('failed to load user preference')
            },
            scope: me,
        });
    },
    
    updateResource: function(body, cb) {
        var me = this;
        if (BQ.Preferences.resource_uniq) {
            Ext.Ajax.request({
                method: 'PUT',
                url: '/preference/user/'+BQ.Preferences.resource_uniq,
                params: {view:'deep'},
                disableCaching: false,
                xmlData: body,
                success: function(response) {
                    BQ.Preferences.resourceXML = response.responseXML;
                    BQ.Preferences.resourceDict = BQ.Preferences.toDict(BQ.Preferences.resourceXML);
                    BQ.Preferences.fireEvent('updateresourcepref', BQ.Preferences, BQ.Preferences.userDict, BQ.Preferences.userXML);
                    if (cb) cb(BQ.Preferences.userDict, BQ.Preferences.userXML);
                    //me.fireEvent('updateResource', me, me.resourceDict);
                },
                failure: function(response) {
                    BQ.ui.error('failed to load resource preference');
                },
                scope: me,
            });
        } else {
            BQ.ui.error('No resource set to preferences, Update failed')
        }
    },
    
    
    resetUserTag : function(path) {
        var me = this;
        Ext.Ajax.request({
            method: 'DELETE',
            url: me.preference_user_uri+'/'+uniq+'/'+path,
            disableCaching: false,
            success: function(response) {
                //me.resourceXML = response.responseXML;
                me.loadUser(cb);
            },
            failure: function(response) {
                BQ.ui.error('failed to delete user preference tag');
            },
            scope: me,
        });
    },
    
    
    resetResourceTag : function(uniq, path, cb) {
        var me = this;
        path = path?path:'';
        Ext.Ajax.request({
            method: 'DELETE',
            url: me.preference_user_uri+'/'+uniq+'/'+path,
            disableCaching: false,
            success: function(response) {
                //me.resourceXML = response.responseXML;
                me.loadResource(uniq, cb);
            },
            failure: function(response) {
                BQ.ui.error('failed to delete resource preference tag');
            },
            scope: me,
        });
    },
    
    resetResource: function(resource_uniq) {
        this.resource_uniq = resource_uniq
    },
    
    toDict: function(dom) {
        var pref = {}
        function conv(dom,node) {
            for (var d=0; d<dom.children.length; d++) {
                if (dom.children[d].tagName == 'tag') {
                    if (dom.children[d].getAttribute('value')===null && dom.children[d].children.length<1) {
                        node[dom.children[d].getAttribute('name')] = '';
                    } else if (dom.children[   d].getAttribute('value')===null) { //had no value
                        node[dom.children[d].getAttribute('name')] = {};
                        conv(dom.children[d], node[dom.children[d].getAttribute('name')]);
                    } else if (dom.children[d].getAttribute('value')===undefined) {
                        node[dom.children[d].getAttribute('name')] = '';
                    } else {
                        node[dom.children[d].getAttribute('name')] = dom.children[d].getAttribute('value');
                    }
                }
            }
            return node
        }
        if (dom.children[0].tagName == 'preference')
            return conv(dom.children[0], pref)
        else
            return pref
    },
    
    /*
     * Caller object:
     *
     * Caller.key = Component's key e.g. "ResourceBrowser"
     * Caller.type = 'user' or 'system' or 'resource'
     * Caller.callback = Component's callback function when the preferences are loaded
     */
    get : function(caller) {
        var me = this;
        caller.type = caller.type || 'user';
        
        var resource = {
            'system':this.systemDict,
            'user':this.userDict,
            'resource':this.resourceDict,
        };
        
        if (resource[caller.type]) {
            if (caller.callback) {
                setTimeout(function(){
                    if (resource[caller.type][caller.key]) {
                        caller.callback(resource[caller.type][caller.key])
                    } else {
                        caller.callback({})
                    }
                }, 1);
            } else {
                return resource[caller.type][caller.key]||{}
            }
        }
    },
    
/*
 * Listens for an update and calls the other updates accordingly
 *
 *
 */
    onPreference: function() {
        
    }
});
