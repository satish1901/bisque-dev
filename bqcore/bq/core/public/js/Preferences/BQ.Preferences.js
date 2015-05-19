/* 
 *  BQ.Preference
 *
 *  
 *
 */
Ext.define('BQ.Preferences', {
    mixins: {
        observable: 'Ext.util.Observable',
    },
    singleton : true,
    preference_system_uri: '/preference',
    preference_user_uri: '/preference/user',
    systemXML: undefined,
    userXML: undefined,
    resourceXML: {},
    systemDict: undefined,
    userDict: undefined,
    resourceDict: {},
    resource_uniq: undefined, //if the preference has a resource set
    
    // load system preferences
    constructor : function() {
        this.addEvents({
            'update_system_pref'  : true,
            'onerror_system_pref' : true,
            'update_user_pref'  : true,
            'onerror_user_pref' : true,
        });
        this.mixins.observable.constructor.call(this);
        this.loadSystem();
        //this.loadUser();
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
                BQ.Preferences.fireEvent('update_system_pref', BQ.Preferences, BQ.Preferences.systemDict, BQ.Preferences.systemXML);
                if (cb) cb(BQ.Preferences.systemDict, BQ.Preferences.systemXML);
            },
            failure: function(response) {
                console.log('Warning: Failed to load system preference');
                //BQ.ui.error('failed to load system preference');
                BQ.Preferences.fireEvent('onerror_system_pref');
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
                BQ.Preferences.fireEvent('update_user_pref', BQ.Preferences, BQ.Preferences.userDict, BQ.Preferences.userXML);
                if (cb) cb(BQ.Preferences.userDict, BQ.Preferences.userXML);
            },
            failure: function(response) {
                console.log('Warning: Failed to load user preference');
                //BQ.ui.error('failed to load user preference');
                BQ.Preferences.fireEvent('onerror_user_pref');
            },
            scope: me,
        });
    },
    
    loadResource: function(uniq, cb) {
        var me = this;
        if (!BQ.Preferences.resourceXML[uniq] || !BQ.Preferences.resourceDict[uniq]) {
            BQ.Preferences.resourceXML[uniq] = {};
            BQ.Preferences.resourceDict[uniq] = {};
            var events = {}
            events['update_'+uniq+'_pref'] = true;
            events['onerror_'+uniq+'_pref'] = true;
            me.addEvents(events);
        }
        Ext.Ajax.request({
            method: 'GET',
            url: '/preference/user/'+uniq,
            params: {view:'deep'},
            disableCaching: false,
            success: function(response) {
                BQ.Preferences.resourceXML[uniq] = response.responseXML;
                BQ.Preferences.resourceDict[uniq] = BQ.Preferences.toDict(BQ.Preferences.resourceXML[uniq]);
                BQ.Preferences.fireEvent('update_'+uniq+'_pref', BQ.Preferences, BQ.Preferences.resourceDict[uniq], BQ.Preferences.resourceXML[uniq]);
                if (cb) cb(BQ.Preferences.resourceDict[uniq], BQ.Preferences.resourceXML[uniq]);
            },
            failure: function(response) {
                console.log('Warning: Failed to load resource:'+uniq+' preference!')
                //BQ.ui.error('Failed to load resource:'+uniq+' preference!');
                BQ.Preferences.fireEvent('onerror_'+uniq+'_pref');
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
                BQ.Preferences.fireEvent('onerror_system_pref', BQ.Preferences, BQ.Preferences.systemDict, BQ.Preferences.systemXML);
                
                //reload lower levels
                BQ.Preferences.loadUser();
                if (BQ.Preferences.resource_uniq) {
                    BQ.Preferences.loadResource(BQ.Preferences.resource_uniq);
                }
                
                if (cb) cb(BQ.Preferences.systemDict, BQ.Preferences.systemXML);
            },
            failure: function(response) {
                //console.log('Warning: Failed to update system preference');
                BQ.ui.error('Failed to update system preference.');
                BQ.Preferences.fireEvent('onerror_system_pref');
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
                BQ.Preferences.fireEvent('update_user_pref', BQ.Preferences, BQ.Preferences.userDict, BQ.Preferences.userXML);
                
                //reload lower level
                if (BQ.Preferences.resource_uniq) {
                    BQ.Preferences.loadResource(BQ.Preferences.resource_uniq);
                }
                
                if (cb) cb(BQ.Preferences.userDict, BQ.Preferences.userXML);
                //me.fireEvent('updateUser', me, me.userDict);
                //me.fireEvent('updateResource', me, me.userDict);
            },
            failure: function(response) {
                //console.log('Warning: Failed to update user preference');
                BQ.ui.error('Failed to load user preference.')
            },
            scope: me,
        });
    },
    
    updateResource: function(uniq, body, cb) {
        var me = this;
        if (BQ.Preferences.resourceXML[uniq]) {
            Ext.Ajax.request({
                method: 'PUT',
                url: '/preference/user/'+uniq,
                params: {view:'deep'},
                disableCaching: false,
                xmlData: body,
                success: function(response) {
                    BQ.Preferences.resourceXML[uniq] = response.responseXML;
                    BQ.Preferences.resourceDict[uniq] = BQ.Preferences.toDict(BQ.Preferences.resourceXML[uniq]);
                    BQ.Preferences.fireEvent('update_'+uniq+'_pref', BQ.Preferences, BQ.Preferences.resourceDict[uniq], BQ.Preferences.resourceXML[uniq]);
                    if (cb) cb(BQ.Preferences.resourceDict[uniq], BQ.Preferences.resourceXML[uniq]);
                },
                failure: function(response) {
                    //console.log('Warning: Failed to update resource preference.');
                    BQ.ui.error('Failed to update resource preference');
                },
                scope: me,
            });
        } else {
            //console.log('Warning: No resource set to preferences, Update failed.');
            BQ.ui.error('No resource set to preferences, Update failed.')
        }
    },
    
    resetSystemTag : function(path, cb) {
        var me = this;
        Ext.Ajax.request({
            method: 'DELETE',
            url: me.preference_user_uri+'/'+path,
            disableCaching: false,
            success: function(response) {
                me.loadSystem(cb);
            },
            failure: function(response) {
                BQ.ui.error('Failed to delete system preference tag.');
            },
            scope: me,
        });
    },
    
    resetUserTag : function(path, cb) {
        var me = this;
        Ext.Ajax.request({
            method: 'DELETE',
            url: me.preference_user_uri+'/'+uniq+'/'+path,
            disableCaching: false,
            success: function(response) {
                me.loadUser(cb);
            },
            failure: function(response) {
                BQ.ui.error('Failed to delete user preference tag.');
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
                me.loadResource(uniq, cb); //reset the element
            },
            failure: function(response) {
                BQ.ui.error('Failed to delete resource preference tag.');
            },
            scope: me,
        });
    },
    
    
    parseValueType: function parseValueType(v, t) { //taken from bqapi
        try {
            if (t && typeof v === 'string' && t == 'number')
                return parseFloat(v);
            else if (t && t == 'boolean')
                return (v=='true') ? true : false;
        } catch(err) {
            return v;
        }
        return v;
    },

    toDict: function(dom) {
        var pref = {};
        
        function conv(tagList, node) {
            for (var t=0; t<tagList.length; t++) {
                var childList = BQ.util.xpath_nodes(tagList[t], 'tag');
                var name = tagList[t].getAttribute('name');
                if (childList.length>0) { //parent node
                    node[name] = {};
                    conv(childList, node[name]);
                } else { //child node
                    var value = tagList[t].getAttribute('value');
                    var type = tagList[t].getAttribute('type'); //cast if type is boolean or number                    
                    node[name] = parseValueType(value, type);
                }
            }
            return node;
        };
        
        //check if its a preference document
        var tagElements = BQ.util.xpath_nodes(dom, 'preference/tag');
        return conv(tagElements, pref);
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
