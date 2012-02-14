//  Img Viewer plugin for dealing with image permssions and deletion
//


function ImgShare(viewer, name) {
    this.base = ViewerPlugin;
    this.base(viewer, name);
    this.bt_share = this.viewer.addCommand('Share', callback(this, 'readShare'));

}
ImgShare.prototype = new ViewerPlugin();

ImgShare.prototype.update_state = function () {
    var perm = this.viewer.image.perm;
    this.bt_public.innerHTML = (perm == 0) ? 'Public' : 'Private';
}
ImgShare.prototype.newImage = function () {
    var show = this.viewer.user_uri && (this.viewer.image.owner == this.viewer.user_uri);
    this.bt_share.style.display = show ? "" : "none";
}

ImgShare.prototype.editShare = function (resource) {

    var auth_uri = resource.uri;

    if (!this.w ) {
        var me = this;
        Ext.define('User', {
            extend : 'Ext.data.Model',
            fields : [ {name: 'id', mapping: '@uri' },
                       {name: 'name', mapping: '@name' },
                       {name: 'email', mapping: '@value' },]
            
        });
    
        me.ds = new Ext.data.Store( {
            model : 'User', 
            autoLoad : true,
            autoSync : false,
            proxy : { 
                limitParam : undefined,
                pageParam: undefined,
                startParam: undefined,
                type: 'ajax',
                url : '/data_service/user?wpublic=1',
                reader : {
                    type :'xml',
                    root : 'resource',
                    record:'user', 
                }
            },
        listeners: {
            load: function(records, options) {
                clog ('loaded ' + records + ' records');
            }
        },
        });

        function entry(i, auth, newauth) {
            var email = auth.email;
            var canedit = (auth.action == "edit");


            var items = [{ xtype: 'radiogroup',
                           //layout : 'hbox',
                           //fieldLabel: 'Permission',
                           defaults : { xtype: 'radio', name :'permission' },
                           allowBlank : false,
                           width: 100,
                           items: [{
                               boxLabel: 'Edit',
                               //name: 'share' + i,
                               inputValue: 'Edit',
                               checked: canedit,
                               flex:1,

                           }, {
                               boxLabel: 'Read',
                               //name: 'share' + i,
                               inputValue: 'Read',
                               flex:1,
                               checked: !canedit,
                           }, ],
                           listeners: {
                               change: function (field, nv, ov) {
                                   var radio = field.getValue()
                                   //var checked = field.getChecked();
                                   auth.action = (radio.permission == "Edit") ? "edit" : "read";
                               }
                           },
                         }, 
                         { xtype: "button",
                           //fieldLabel: '',
                           //labelSeparator: ' ',
                           text: 'Remove',
                           handler: function () {
                               resource.children.removeItems([auth]);
                               //var form = form.getCmp('AuthPanel');
                               form.remove("auth" + i);
                           },
                         }];

            if (newauth) {
                items.unshift ( { 
                    xtype: 'combo',
                    //store : store,
                    store : me.ds,
                    queryMode : 'local',
                    //triggerAction: 'all', 
                    displayField: 'name',
                    valueField : 'email',
                    fieldLabel: 'Email',
                    allowBlank : false,
                    listeners: {
                        change: {
                            fn: function (field, nv, ov) {
                                auth.email = nv;
                            }
                        },
                    }
                });
            } else {
                items.unshift ( { 
                    xtype: 'displayfield',
                    fieldLabel: 'Email',
                    name: 'email' + i,
                    vtype: 'email',
                    value: email,
                    anchor : '-20',
                });
            }

            var field = {
                //xtype: 'compositefield',
                xtype: 'fieldcontainer',
                //labelWidth: 80,
                bodyStyle: 'padding: 5px',
                labelWidth: 100,
                //width: 600,
                //autoHeight : true,
                layout : 'hbox',
                defaults : { anchor : '0',  },
                itemId: "auth" + i,
                items:  items
            }
            return field;
        }



        // Create the sharing form and window 
        var form = Ext.create('Ext.form.FormPanel', {
            //id: 'AuthPanel',
            //baseCls: 'x-plain',
            labelWidth: 55,
            url: '',
            dynamic: true,
            defaultType: 'textfield',
            layout: 'anchor',
            defaults: {
                anchor : '100%'
            },
            tbar: [{
                text: 'Add Share',
                handler: function () {
                    var a = new BQAuth();
                    resource.addchild(a);
                    form.add([ entry(form.items.getCount(), a, true) ]);
                    //form.doLayout();
                }
            }],
        });


        // Create the items list of known shares 
        for (var i = 0; i < resource.children.length; i++) {
            form.add(entry(i, resource.children[i]));
        }
        

        this.w = Ext.create('Ext.Window', {
            title: 'Edit Sharing',
            modal: true,
            //collapsible: true,
            //maximizable: true,
            width: 600,
            height: 400,
            minWidth: 600,
            minHeight: 400,
            //autoCreate:True,
            layout: 'fit',
            plain: true,
            bodyStyle: 'padding:5px;',
            buttonAlign: 'center',
            items: form,
            buttons: [{
                text: 'Save',
                scope: this,
                handler: function () {
                    resource.save_();
                    this.w.hide();
                }
            }, {
                text: 'Cancel',
                scope: this,
                handler: function (me) {
                    this.w.hide();
                }
            }]
        });
    }
    this.w.show();
}

ImgShare.prototype.readShare = function () {
    var uri = this.viewer.imageuri;

    BQFactory.load(uri + "/auth/", callback(this, 'editShare'))
}



ImgShare.prototype.toggleShare = function () {
    var uri = this.viewer.imageuri;
    var src = this.viewer.imagesrc;
    var perm = this.viewer.image.perm;
    perm = (perm == 0) ? 1 : 0;

    // Dataserver 
    var xmldata = '<request>';
    xmldata += '<image uri="' + uri + '" perm="' + perm + '" />';
    xmldata += '</request>';
    makeRequest(uri, callback(this, 'checkPerm'), null, "post", xmldata);

    // Imageserver
    var xmldata = '<request>';
    xmldata += '<image src="' + src + '" perm="' + perm + '" />';
    xmldata += '</request>';

    var imgsrv_req = src.replace(/\d+$/, "update_image_permission");
    makeRequest(imgsrv_req, null, null, "post", xmldata);

    this.viewer.image.perm = perm;
}
ImgShare.prototype.checkPerm = function (ignore, response) {
    this.update_state()
}
ImgShare.prototype.deleteImage = function () {
    var ok = window.confirm("Really Delete image");
    var uri = this.viewer.imageuri;
    if (ok) {
        this.viewer.image.delete_(callback(this, 'close_viewer'));
    }
    window.close();
}

ImgShare.prototype.close_viewer = function () {
    //history.back();
    window.close();
}
