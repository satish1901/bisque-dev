Ext.define('BQ.ShareDialog.Offline', {

    extend : 'BQ.ShareDialog',

    constructor : function(config) {
        var resource = new BQResource();

        Ext.apply(resource, {
            owner : BQApp.user.uri,
            getAuth : function(cb) {
                var resource = new BQResource();
                cb(resource);
            }
        });

        config.resource = resource;

        this.callParent([config]);
    },

    btnSave : function() {
        var modified = false;

        for (var i = 0; i < this.store.getCount(); i++) {
            var currentRecord = this.store.getAt(i);
            if (currentRecord.dirty) {
                modified = true;
                currentRecord.commit();
                this.authRecord.children[i - 1].action = (currentRecord.get('edit')) ? 'edit' : 'read';
            }
        }

        var notify = this.grid.getDockedItems('toolbar[dock="bottom"]')[0].getComponent('cbNotify').getValue();

        if (modified || this.userModified)
            for (var i = 0; i < this.resources.length; i++)
                this.resources[i].resource.getAuth(Ext.bind(this.addAuth, this, [notify], 1));

        this.close();
    },

    addAuth : function(authRecord, notify) {
        if (!notify)
            authRecord.uri = Ext.urlAppend(authRecord.uri, 'notify=false');

        for (var i = 0; i < this.authRecord.children.length; i++)
            authRecord.addchild(this.authRecord.children[i]);

        authRecord.save_(undefined, this.success, this.failure);
    },

    success : function(resource, msg) {
        BQ.ui.notification(msg || 'Operation successful.');
    },

    failure : function(msg) {
        BQ.ui.error(msg || 'Operation failed!');
    },
});

