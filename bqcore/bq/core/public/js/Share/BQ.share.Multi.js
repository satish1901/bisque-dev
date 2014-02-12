/*******************************************************************************

  BQ.share.MultiDialog - window wrapper for the sharing of multiple resources

  Author: Dima Fedorov <dima@dimin.net>

  Parameters:
      resources - vector of the BQResource objects

------------------------------------------------------------------------------

  Version: 1

  History:
    2014-05-02 13:57:30 - first creation

*******************************************************************************/

//--------------------------------------------------------------------------------------
// BQ.share.Dialog
//--------------------------------------------------------------------------------------

Ext.define('BQ.share.MultiDialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.bqsharemultidialog',
    border: 0,
    layout: {
        type: 'vbox',
        align: 'stretch'
    },
    modal : true,
    border : false,
    width : '70%',
    height : '85%',
    //minHeight: 350,
    //maxWidth: 900,
    buttonAlign: 'center',
    autoScroll: true,
    bodyCls: 'bq-share-dialog',

    constructor : function(config) {
        config = config || {};
        Ext.apply(this, {
            title: 'Add shares to selected '+config.resources.length+' resources',
            permission: config.permission === 'private' ? 'published' : 'private',
            buttons: [{
                xtype: 'progressbar',
                itemId: 'progressbar',
                animate: false,
                flex: 2,
            }, {
                itemId: 'btn_add_shares',
                text: 'Add shares to selected '+config.resources.length+' resources',
                scale: 'large',
                cls: 'bq-btn-highlight',
                scope: this,
                handler: this.onAddShares,
            }, {
                text: 'Close',
                scale: 'large',
                scope: this,
                handler: this.onFinish,
            }],
            items  : [{
                xtype: 'bqsharepanel',
                itemId: 'sharepanel',
                border: 0,
                flex: 2,
                //resource: config.resource,
                permission: config.permission === 'private' ? 'published' : 'private',
                listeners : {
                    changePermission: this.onChangePermission,
                    scope: this,
                },
            }],
        }, config);

        this.callParent(arguments);
        this.show();
    },

    onFinish: function() {
        this.close();
    },

    onDone: function() {
        //this.close();
    },

    onOk: function(pos) {
        this.onUpdated();
        if (pos+1>=this.resources.length)
            return;

        var me = this;
        setTimeout( function() { me.addShares(pos+1); }, 1);
    },

    onError: function(error) {
        this.onUpdated();
        BQ.ui.warning('Error while adding shares!');
    },

    onUpdated: function() {
        this.updating--;
        if (this.updating<=0) {
            this.queryById('btn_add_shares').setLoading(false);
            this.queryById('btn_add_shares').setDisabled(false);
            this.queryById('progressbar').reset();
            this.queryById('progressbar').updateProgress( 0, 'Done', false );
            this.xml = undefined;
            this.records = undefined;
            return;
        }
    },

    addAuth : function(auth, notify, pos) {
        auth.children.push.apply(auth.children, this.records);

        var url = notify?undefined:Ext.urlAppend(auth.uri, 'notify=false');
        auth.save_(url, Ext.bind(this.onOk, this, [pos]), this.onError);
    },

    addShares: function(pos) {
        var total = this.resources.length;
        if (pos>=total)
            return;

        var resource = this.resources[pos].resource;
        var pr = pos/total;
        this.queryById('progressbar').updateProgress( pr, 'Adding shares to '+resource.name+' ('+(pos+1)+'/'+total+ ')' );

        var notify = this.queryById('notify_check').getValue();
        resource.getAuth(Ext.bind(this.addAuth, this, [notify, pos], 1));
    },

    onAddShares: function() {
        // change shares for all images
        var store = this.queryById('sharepanel').store;
        var data = store.data;
        this.xml = store.proxy.writer.writeRecords({}, data.items);

        this.records = [];
        for (var i=0; i<store.getCount(); i++) {
            var rec = store.getAt(i);
            if (rec.dirty) {
                var user = rec.data.user;
                var email = rec.data.email;
                var action = rec.data.action;
                this.records.push(new BQAuth (user, email, action));
                rec.commit();
            }
        }
        if (this.records.length>0) {
            this.queryById('btn_add_shares').setDisabled(true);
            this.queryById('btn_add_shares').setLoading('');
            this.updating = this.resources.length;
            this.addShares(0);
        }
    },

    onChangePermission: function(perm, btn) {
        // change permission for all images
    },

});

//--------------------------------------------------------------------------------------
// BQ.button.ResourceVisibility
// button that shows and changes resource visibility
// Parameters: resource
//--------------------------------------------------------------------------------------

Ext.define('BQ.button.MultiPermissions', {
    extend: 'BQ.button.ResourcePermissions',
    alias: 'widget.bqmultipermissions',

    toggleVisibility: function() {
        this.permission = this.permission === 'private' ? 'published' : 'private';
        this.fireEvent( 'changePermission', this.permission, this );
    },
});

