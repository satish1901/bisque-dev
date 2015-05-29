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
    silence: false,
    resource_uniq: undefined, //if the preference has a resource set
    
    level : {
        'system'  : '/preference',
        'user'    : '/preference/user',
        //'resource': '/preference/user',
    },
    preferenceXML : {}, 
    
    // load system preferences
    constructor : function() {
        this.addEvents({
            'update_system_pref'  : true,
            'onerror_system_pref' : true,
            'update_user_pref'  : true,
            'onerror_user_pref' : true,
        });
        this.mixins.observable.constructor.call(this);
        this.load('system');
        //this.loadUser();
    },
    
    setSilence: function(bool) {
        this.silence = bool;
    },
    
    load : function(lvl, path, cb) {
        var me = this;
        var path = (!path) ? '' : '/'+path;
        var url = (lvl in me.level) ? me.level[lvl]+path: me.level['user']+'/'+lvl+path;
        if (url) {
            Ext.Ajax.request({
                method: 'GET',
                url: url,
                params: {view:'deep'},
                disableCaching: false,
                success: function(response) {
                    BQ.Preferences.preferenceXML[lvl] = response.responseXML;
                    //BQ.Preferences.systemDict = BQ.Preferences.toDict(BQ.Preferences.systemXML);
                    BQ.Preferences.fireEvent('update_'+lvl+'_pref', response.responseXML);
                    if (cb) cb(response.responseXML);
                },
                failure: function(response) {
                    if (me.silence) console.log('Warning: Failed to load '+lvl+' preference');
                    //BQ.ui.error('failed to load system preference');
                    BQ.Preferences.fireEvent('onerror_'+lvl+'_pref');
                },
                scope: me,
            });
        }
    },
    
    update: function(lvl, path, body, cb, errorcb) {
        var me = this;
        var path = (!path) ? '' : '/'+path;
        var url = (lvl in me.level) ? me.level[lvl]+path: me.level['user']+'/'+lvl+path;
        if (url) {
            Ext.Ajax.request({
                method: 'POST',
                url: url,
                params: {view:'deep'},
                disableCaching: false,
                xmlData: body,
                success: function(response) {
                    //BQ.Preferences.preferenceXML[lvl] = response.responseXML;
                    BQ.Preferences.load(lvl, '', cb) //to fetch the entire document and call update_pref
                    //BQ.Preferences.fireEvent('update_'+lvl+'_pref', response.responseXML);
                    //if (cb) cb(response.responseXML);
                },
                failure: function(response) {
                    if (me.silence) BQ.ui.error('Failed to update '+lvl+' preference.');
                    BQ.Preferences.fireEvent('onerror_'+lvl+'_pref');
                    if (errorcb) errorcb();
                },
                scope: me,
            });
        }
    },
    
    remove: function(lvl, path, cb, errorcb) {
        var me = this;
        var path = (!path) ? '' : '/'+path;
        var url = (lvl in me.level) ? me.level[lvl]+path: me.level['user']+'/'+lvl+path;
        if (url) {
            Ext.Ajax.request({
                method: 'DELETE',
                url: url,
                disableCaching: false,
                success: function(response) {
                    me.load(lvl, path, cb);
                },
                failure: function(response) {
                    if (me.silence) BQ.ui.error('Failed to delete '+lvl+' preference tag.');
                    BQ.Preferences.fireEvent('onerror_'+lvl+'_pref');
                    if (errorcb) errorcb();
                },
                scope: me,
            });
        }
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
    

    toDict: function(tagElements) {
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
        //var tagElements = BQ.util.xpath_nodes(dom, 'preference/tag');
        return conv(tagElements, pref);
    },
    
    
    /*
    * get
    *
    * @param: lvl - 
    * @param: path -
    * @param: value - 
    */
    get : function(lvl, path, defaultValue) {
        var pattern = /\s*\/\s*/;
        if (path) {
            var names = path.split(pattern);
            var xpath = 'preference';
            for (var n = 0; n<names.length; n++) {
                xpath += '/tag[@name="'+names[n]+'"]';
            }
            var nodes = BQ.util.xpath_nodes(BQ.Preferences.preferenceXML[lvl], xpath);
            return nodes.length ? this.toDict(nodes)[names[names.length-1]]: defaultValue;
        } else {
            var nodes = BQ.util.xpath_nodes(BQ.Preferences.preferenceXML[lvl], 'preference/tag');
            return nodes.length ? this.toDict(nodes): defaultValue;
        }
    },
    
    /*
    * set
    *
    * @param: lvl - 
    * @param: path - 
    * @param: value - xml string
    *
    * if no value is set to undefined or not set the value is removed from the resource document
    */
    set : function(lvl, path, value, cb, errorcb) {
        if (value===undefined) { //forces the removal 
            BQ.Preferences.remove(lvl, path, cb, errorcb);
        } else {
            BQ.Preferences.update(lvl, path, value, cb, errorcb);
        }
    },
    
    /*
     * Listens for an update and calls the other updates accordingly
     *
     *
     */
    onPreference: function() {
        
    },
});
