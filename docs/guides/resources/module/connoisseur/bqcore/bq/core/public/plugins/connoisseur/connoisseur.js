/*******************************************************************************
Author: Dmitry Fedorov
Copyright: 2017-2018 (C) Center for Bio-Image Informatics, University of California at Santa Barbara
Copyright: 2017-2018 (C) ViQi Inc

Exportable classes:
    BQ.model.Panel - renders the model resource
    BQ.model.View - renders a given sub-model of a model resource

Browser components:
    Bisque.Resource.Model.Page
    ...
    Bisque.Resource.Model.Grid

*******************************************************************************/

Ext.namespace('BQ.connoisseur.api');

//--------------------------------------------------------------------------------------
// UI integration
//--------------------------------------------------------------------------------------

Ext.onReady( function() {
    Ext.QuickTips.init();
    Ext.apply(Ext.QuickTips.getQuickTip(), {
        dismissDelay: 600000,
        showDelay: 500,
    });
});

/*Ext.onReady( function() {
    var tb = BQApp.main.getToolbar(),
        menu = tb.queryById('button_create').menu;
    if (BQ.connoisseur.api.templates.length>0)
    menu.insert(0, [{
        text: 'Create a new <b>Connoisseur model</b>',
        scope: BQ.connoisseur.api.Service,
        handler: BQ.connoisseur.api.Service.createNew,
    }]);
});*/

//--------------------------------------------------------------------------------------
// utils
//--------------------------------------------------------------------------------------

Ext.namespace('BQ.connoisseur.utils');

BQ.connoisseur.utils.toArray = function(s) {
    if (!s) return [];
    var a = s.split(','),
        i = 0;
    for (i=0; i<a.length; ++i) {
        a[i] = parseFloat(a[i]);
    }
    return a;
};

BQ.connoisseur.utils.avg = function(elements) {
    return elements.reduce(function(sum, a) { return sum + a },0)/(elements.length||1);
};

BQ.connoisseur.utils.sum = function(elements) {
    return elements.reduce(function(sum, a) { return sum + a },0);
};

BQ.connoisseur.utils.mul = function(elements, c) {
    return elements.map(function(a) { return a * c; });
};

BQ.connoisseur.utils.div = function(elements, c) {
    return elements.map(function(a) { return a / c; });
};

BQ.connoisseur.utils.diff = function(a1, a2) {
    if (typeof a1 === 'string' || a1 instanceof String)
        a1 = BQ.connoisseur.utils.toArray(a1);
    if (typeof a2 === 'string' || a2 instanceof String)
        a2 = BQ.connoisseur.utils.toArray(a2);
    var i=0,
        a=[];
    for (var i=0; i<a1.length; ++i) {
        a[i] = a1[i] - a2[i];
    }
    return a;
};

BQ.connoisseur.utils.improvement_percent = function(a1, a2, less_is_more=false, mult=0) {
    if (typeof a1 === 'string' || a1 instanceof String)
        a1 = BQ.connoisseur.utils.toArray(a1);
    if (typeof a2 === 'string' || a2 instanceof String)
        a2 = BQ.connoisseur.utils.toArray(a2);
    if (mult>0) {
        a1 = BQ.connoisseur.utils.mul(a1, 100);
        a2 = BQ.connoisseur.utils.mul(a2, 100);
    }

    var i=0,
        a=[],
        sign = a1[i] < a2[i] ? -1 : 1;
    if (less_is_more===true) {
        sign *= -1;
    }

    // if (less_is_more === false)
    //     for (var i=0; i<a1.length; ++i) { a[i] = sign * Math.max(1.0, Math.abs(a1[i] - a2[i]))*100.0/Math.max(1.0, a1[i]); }
    // else
    //     for (var i=0; i<a1.length; ++i) { a[i] = sign * Math.max(1.0, Math.abs(a1[i] - a2[i]))*100.0/Math.max(1.0, a2[i]); }

    if (less_is_more === false)
        for (var i=0; i<a1.length; ++i) { a[i] = sign * Math.abs(a1[i] - a2[i]); }
    else
        for (var i=0; i<a1.length; ++i) { a[i] = sign * Math.abs(a1[i] - a2[i]); }

    return a;
};

//--------------------------------------------------------------------------------------
// BQ.connoisseur.api.Service
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.api.Service', {
    singleton: true,
    mixins: {
        observable: 'Ext.util.Observable'
    },

    constructor: function (config) {
        this.mixins.observable.constructor.call(this, config);

        Ext.Ajax.request({
            url: '/connoisseur/',
            callback: function(opts, succsess, response) {
                if (response.status>=400 || !succsess) {
                    //BQ.ui.error(response.responseText);
                } else {
                    this.onApi(response.responseXML);
                }
            },
            scope: this,
            disableCaching: false,
        });
    },

    onApi: function(xml) {
        BQ.connoisseur.api.xml = xml;

        // parse available api entries
        BQ.connoisseur.api.templates = [];
        var tags = BQ.util.xpath_nodes(xml, '*/tag[@name="templates"]/plugin'),
            t = null;
        for (var i=0; t=tags[i]; ++i) {
            BQ.connoisseur.api.templates.push(t.getAttribute('name'));
        }

        // add to UI
        Ext.onReady( function() {
            var tb = BQApp.main.getToolbar(),
                menu = tb.queryById('button_create').menu;
            if (BQ.connoisseur.api.templates.length>0)
            menu.insert(0, [{
                text: 'Create a new <b>Connoisseur model</b>',
                scope: BQ.connoisseur.api.Service,
                handler: BQ.connoisseur.api.Service.createNew,
            }]);
        });
    },

    createNew : function() {
        var data = [], i=null, t=null;
        for (i=0; (t=BQ.connoisseur.api.templates[i]); ++i) {
            data.push([t]);
        }
        var store_templates = Ext.create('Ext.data.ArrayStore', {
            fields: ['name'],
            data: data,
        });
        var formpanel = Ext.create('Ext.form.Panel', {
            frame: false,
            bodyStyle:'padding: 15px',
            width: 500,

            /*fieldDefaults: {
                msgTarget: 'side',
                labelWidth: 75
            },*/
            defaultType: 'textfield',
            defaults: {
                anchor: '100%'
            },

            items: [{
                xtype : 'combobox',
                fieldLabel: 'Template',
                name: 'template',
                allowBlank: false,
                //value: def,
                editable: false,

                store: store_templates,
                displayField: 'name',
                valueField: 'name',
                queryMode : 'local',
            },{
                fieldLabel: 'Name',
                name: 'name',
                allowBlank: false,
            }],

        });

        var w = Ext.create('Ext.window.Window', {
            layout : 'fit',
            modal : true,
            border : false,
            title: 'Create new Connoisseur model',
            buttonAlign: 'center',
            items: formpanel,
            buttons: [{
                text: 'Cancel',
                //scope: this,
                handler: function (me) {
                    formpanel.ownerCt.hide();
                }
            }, {
                text: 'Create',
                scope: this,
                handler: function () {
                    var form = formpanel.getForm();
                    if (form.isValid()) {
                        var v = form.getValues(),
                            url = Ext.String.format('/connoisseur/create/template:{0}/name:{1}',
                                encodeURIComponent(v.template),
                                encodeURIComponent(v.name));
                        BQApp.setLoading('Creating a new model...');
                        Ext.Ajax.request({
                            url: url,
                            callback: function(opts, succsess, response) {
                                BQApp.setLoading(false);
                                if (response.status>=400 || !succsess)
                                    BQ.ui.error(response.responseText);
                                else
                                    this.onCreated(response.responseXML);
                            },
                            scope: this,
                            disableCaching: false,
                        });

                        formpanel.ownerCt.hide();
                    };
                }
            }]

        }).show();
    },

    onCreated: function(xml) {
        var uri = xml.documentElement.getAttribute('uri');
        document.location = '/client_service/view?resource='+uri;
    },

});

//--------------------------------------------------------------------------------------
// BQ.connoisseur.Model
// required parameters:
//     resource -
// events:
// working
// done
// change
//--------------------------------------------------------------------------------------

BQ.connoisseur.stages = {
    'update/classes:init': {
        command: 'update/classes:init',
        text: 'Initializing classes',
        tag: 'status.classes.init',
        id: 0,
        vis: 0,
        status: null,
        required: true,
    },
    'update/classes:filter': {
        command: 'update/classes:filter',
        text: 'Filtering classes',
        tag: 'status.classes.filter',
        id: 1,
        vis: 1,
        status: null,
        required: true,
    },
    'update/samples:init': {
        command: 'update/samples:init',
        text: 'Initializing samples',
        tag: 'status.samples.init',
        id: 2,
        vis: 2,
        status: null,
        required: true,
    },
    'update/samples:update': {
        command: 'update/samples:update',
        text: 'Updating samples',
        tag: 'status.samples.update',
        id: 3,
        vis: 2,
        status: null,
        required: false,
    },
    'update/samples:split': {
        command: 'update/samples:split',
        text: 'Splitting samples',
        tag: 'status.samples.split',
        id: 4,
        vis: 2,
        status: null,
        required: true,
    },
    'train': {
        command: 'train',
        text: 'Training',
        tag: 'status.train',
        id: 5,
        vis: 3,
        status: null,
        required: true,
    },
    'validate': {
        command: 'validate',
        text: 'Validating',
        tag: 'status.validate',
        id: 6,
        vis: 4,
        status: null,
        required: true,
    },
};

BQ.connoisseur.stages_by_tag = {
    'status.classes.init'   : BQ.connoisseur.stages['update/classes:init'],
    'status.classes.filter' : BQ.connoisseur.stages['update/classes:filter'],
    'status.samples.init'   : BQ.connoisseur.stages['update/samples:init'],
    'status.samples.update' : BQ.connoisseur.stages['update/samples:update'],
    'status.samples.split'  : BQ.connoisseur.stages['update/samples:split'],
    'status.train'          : BQ.connoisseur.stages['train'],
    'status.validate'       : BQ.connoisseur.stages['validate'],
};

BQ.connoisseur.stages_by_id = {
    0: BQ.connoisseur.stages['update/classes:init'],
    1: BQ.connoisseur.stages['update/classes:filter'],
    2: BQ.connoisseur.stages['update/samples:init'],
    3: BQ.connoisseur.stages['update/samples:update'],
    4: BQ.connoisseur.stages['update/samples:split'],
    5: BQ.connoisseur.stages['train'],
    6: BQ.connoisseur.stages['validate'],
};

BQ.connoisseur.stages_tags = [
    "status.classes.init",
    "status.classes.filter",
    "status.samples.init",
    "status.samples.update",
    "status.samples.split",
    "status.train",
    "status.validate"
];

Ext.define('BQ.connoisseur.Model', {
    mixins: {
        observable: 'Ext.util.Observable'
    },

    constructor: function (config) {
        this.mixins.observable.constructor.call(this, config);
        this.resource = config.resource;

        this.quicksaves = {};
        this.task_save = new Ext.util.DelayedTask(function() {
            this.do_save();
        }, this);
        this.task_quicksave = new Ext.util.DelayedTask(function(t) {
            this.do_quicksave(t);
        }, this);
        this.task_checkupdate = new Ext.util.DelayedTask(function() {
            this.doCheckStatus();
        }, this);

        this.task_oninit = new Ext.util.DelayedTask(function() {
            var status = this.resource.find_tags('status').value;
            if (status !== 'template' && status !== 'finished')
                this.onCheckStatus(this.resource);
        }, this);

        this.onResourceLoaded();
        this.task_oninit.delay(10);
    },

    onResourceLoaded: function() {
        this.original_classes = this.enumerateClasses("classes_data");
        this.model_classes = this.enumerateClasses("classes_model");
        this.model_classes_by_name = this.indexClasses(this.model_classes);
        this.init_stages_from_resource();
    },

    enumerateClasses : function(tag_name) {
        var parent = this.resource.find_tags(tag_name),
            t = null,
            tt = null,
            f = null
            data = [];
        if (!parent) return data;
        for (var i=0; (t=parent.tags[i]); ++i) {
            f = {
                label: t.value,
                tag: t,
            };
            for (var ii=0; (tt=t.tags[ii]); ++ii) {
                f[tt.name] = tt.value;
            }
            //if (f.samples>0)
                data[f.id] = (f);
            //data.push(f);
        }
        return data;
    },

    indexClasses : function(classes) {
        var indexed = {},
            i=0, s=null;
        for (i=0; (s=classes[i]); ++i) {
            indexed[s.label] = s;
        }
        return indexed;
    },

    updateOriginalClass: function(record) {
        if (record.data.ignored === true) {
            record.raw.ignored = true;
        } else {
            record.raw.ignored = undefined;
        }

        var parent = record.raw.tag,
            tag = parent.find_tags('ignored');
        if (tag) {
            tag.value = record.raw.ignored ? 'true' : 'false';
            tag.type = 'boolean';
            this.quicksave(tag);
        } else if (record.raw.ignored) {
            tag = parent.addtag({
                name: 'ignored',
                value: record.raw.ignored ? 'true' : 'false',
                type: 'boolean',
            });
            this.quicksave(parent);
        }
    },

    init_stages_from_resource: function() {
        var name = null,
            stage = null,
            t = null, i=0;
        for (i=0; i<BQ.connoisseur.stages_tags.length; ++i) {
            name = BQ.connoisseur.stages_tags[i];
            stage = BQ.connoisseur.stages_by_tag[name];
            t = this.get_tag(name);
            if (t)
                stage.status = t.value;
        }

        // test for old style models without status tags
        name = BQ.connoisseur.stages_tags[0];
        t = this.get_tag(name);
        if (!t) {
            if (this.original_classes.length>0 && this.model_classes.length===0) {
                BQ.connoisseur.stages_by_tag['status.classes.init'].status = 'finished';
            }

            if (this.original_classes.length>0 && this.model_classes.length>0) {
                BQ.connoisseur.stages_by_tag['status.classes.init'].status = 'finished';
                BQ.connoisseur.stages_by_tag['status.classes.filter'].status = 'finished';
            }

            // dima: needs to detect if there is validation, etc...
            if (this.original_classes.length>0 && this.model_classes.length>0 && this.model_classes[0].accuracy) {
                BQ.connoisseur.stages_by_tag['status.classes.init'].status = 'finished';
                BQ.connoisseur.stages_by_tag['status.classes.filter'].status = 'finished';
                BQ.connoisseur.stages_by_tag['status.samples.init'].status = 'finished';
                BQ.connoisseur.stages_by_tag['status.samples.split'].status = 'finished';
                BQ.connoisseur.stages_by_tag['status.train'].status = 'finished';
                BQ.connoisseur.stages_by_tag['status.validate'].status = 'finished';
            }
        }
    },

    doCheckStatus: function() {
        BQFactory.request({
            uri: this.resource.uri,
            uri_params: { view : 'full' },
            cb: callback(this, this.onCheckStatus),
            errorcb: callback(this, this.onError),
        });
    },

    onCheckStatus: function(resource) {
        var me = this,
            status = resource.find_tags('status').value;
        if (status === 'finished') {
            BQFactory.request({
                uri: this.resource.uri,
                uri_params: { view : 'deep' },
                cb: function(resource) {
                    me.resource = resource;
                    me.onResourceLoaded();
                    me.fireEvent('done', me);
                },
                errorcb: callback(this, this.onError),
            });
        } else {
            this.fireEvent('working', this, status);
            this.task_checkupdate.delay(60*1000);
        }
    },

    get_id: function() {
        return this.resource.resource_uniq;
    },

    get_name: function() {
        return this.resource.name;
    },

    set_name: function(v) {
        this.resource.name = v;
        this.save();
    },

    get_minimum_samples: function() {
        return this.resource.find_tags('minimum_samples').value;
    },

    set_minimum_samples: function(v) {
        var t = this.resource.find_tags('minimum_samples');
        t.value = v;
        this.quicksave(t);
        this.fireEvent('change', this);
    },

    get_minimum_accuracy: function() {
        return this.resource.find_tags('minimum_accuracy').value;
    },

    set_minimum_accuracy: function(v) {
        var t = this.resource.find_tags('minimum_accuracy');
        t.value = v;
        this.quicksave(t);
        this.fireEvent('change', this);
    },

    get_minimum_goodness: function() {
        return this.resource.find_tags('minimum_goodness').value;
    },

    set_minimum_goodness: function(v) {
        var t = this.resource.find_tags('minimum_goodness');
        t.value = v;
        this.quicksave(t);
        this.fireEvent('change', this);
    },

    get_dataset: function() {
        var t = this.resource.find_tags('training_set');
        if (!t) {
            t = this.resource.addtag({
                name: 'training_set',
                type: 'dataset',
            });
        }
        return t.value;
    },

    set_dataset: function(uri) {
        var t = this.resource.find_tags('training_set');
        t.value = uri;
        this.resource.stage = 'update/classes:init';
        this.save();
    },

    get_tag: function(name) {
        return this.resource.find_tags(name);
    },

    set_tag: function(name, value) {
        var t = this.resource.find_tags(name);
        t.value = value;
        //this.save();
        //this.fireEvent('change', this);
    },

    all_saved: function() {
        return Object.keys(this.quicksaves).length === 0;
    },

    quicksave: function(t) {
        this.quicksaves[t.uri] = t;
        this.task_quicksave.delay(2500, undefined, undefined, [t] );
    },

    do_quicksave: function(t) {
        for (uri in this.quicksaves) {
            this.quicksaves[uri].save_me(Ext.emptyFn, Ext.emptyFn);
            delete this.quicksaves[uri];
        }
    },

    save: function() {
        this.task_save.delay(500);
    },

    do_save: function() {
        this.fireEvent('working', this, 'Saving model');
        this.resource.save_(this.resource.uri,
            callback(this, this.onSaved),
            callback(this, this.onError)
        );
    },

    onSaved: function() {
        var url = null,
            stage = this.pop_stage();
        this.quicksaves = {};
        if (stage in BQ.connoisseur.stages) {
            this.fireEvent('working', this, BQ.connoisseur.stages[stage].text);
            url = Ext.String.format('/connoisseur/{0}/{1}', this.resource.resource_uniq, stage);
        }
        if (url) {
            Ext.Ajax.request({
                url: url,
                callback: function(opts, succsess, response) {
                    this.fireEvent('done', this);
                    // dima: we have to deal with timeouts, futures, etc...
                    if (response.status>=400 || !succsess) {
                        // re-insert stage that failed
                        this.insert_stage(stage);
                        BQ.ui.error(response.responseText);
                    } else {
                        //this.resource.stage = undefined;
                        this.onSaved();
                    }
                },
                scope: this,
                disableCaching: false,
                timeout: 12 * 60 * 60 * 1000, // 12h
            });
        } else {
            this.fireEvent('done', this);
            location.reload();
        }
    },

    onError: function() {
        this.fireEvent('done', this);
        BQ.ui.error('Error while saving the model');
    },

    // stages

    pop_stage: function() {
        var s = null;
        if (!this.resource.stage) return;
        if (this.resource.stage instanceof Array) {
            s = this.resource.stage.shift();
            if (this.resource.stage.length === 0)
                this.resource.stage = undefined;
            return s;
        }

        s = this.resource.stage;
        this.resource.stage = undefined;
        return s;
    },

    insert_stage: function(stage) {
        if (!this.resource.stage) {
            this.resource.stage = stage;
        } else if (this.resource.stage instanceof Array) {
            this.resource.stage.splice(0, 0, stage);
        } else {
            this.resource.stage = [stage, this.resource.stage];
        }
    },

    get_stage: function() {
        return this.resource.stage;
    },

    set_stage: function(stage) {
        this.resource.stage = stage;
        this.onSaved();
    },

    save_stage: function(stage) {
        this.resource.stage = stage;
        this.do_save();
    },

    get_stage_from_tag: function(i) {
        var name = BQ.connoisseur.stages_tags[i],
            t = this.get_tag(name);
        if (!t) return;
        return t.value;
    },

    get_last_stage: function() {
        var name = BQ.connoisseur.stages_tags[0],
            stage = null;
        for (var i=BQ.connoisseur.stages_tags.length-1; i>=0; --i) {
            name = BQ.connoisseur.stages_tags[i],
            stage = BQ.connoisseur.stages_by_tag[name];
            if (stage.status === 'finished')
                return stage;
        }
    },

    get_missing_stages: function() {
        var stages = [],
            name = null,
            stage = null;
        for (var i=0; i<BQ.connoisseur.stages_tags.length; ++i) {
            name = BQ.connoisseur.stages_tags[i],
            stage = BQ.connoisseur.stages_by_tag[name];
            if (stage.status !== 'finished' && stage.required)
                stages.push(stage.command);
        }

        if (stages.length<1) {
            stages.push('train');
            stages.push('validate');
        }

        return stages;
    },

    execute_stage: function(stage) {
        this.resource.stage = stage;
        if (this.all_saved() === true) {
            this.onSaved();
        } else {
            this.do_save();
        }
    },

    execute_next_stages: function() {
        var stage = this.get_stage();
        if (stage) {
            this.save_stage(stage);
            return;
        }
        stage = this.get_missing_stages();
        this.save_stage(stage);
    },

});

//--------------------------------------------------------------------------------------
// Numeric selector
// required parameters:
//     value -
//     min
//     max
//     step
//     suffix
//     tip
//--------------------------------------------------------------------------------------

Ext.define('BQ.ui.Numeric', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_ui_numeric',
    componentCls: 'bq_ui_numeric',
    layout : {
        type: 'vbox',
        align: 'stretch'
    },
    width: 150,
    height: 130,

    value: 50,
    min: 0,
    max: 99,
    step: 0.1,

    initComponent : function() {
        this.suffix = this.suffix || '';
        this.items = [{
            xtype: 'tbtext',
            itemId: 'valueText',
            cls: 'value',
            text: this.value + this.suffix,
            flex: 1,
        }, {
            xtype: 'tbtext',
            cls: 'text',
            text: this.title,
        }, {
            xtype: 'slider',
            itemId: 'slider',
            cls: 'slider',
            value: this.value,
            increment: this.step,
            minValue: this.min,
            maxValue: this.max,
            listeners: {
                scope: this,
                change: function(slider, newValue, thumb, eOpts) {
                    this.task.delay(25, undefined, undefined, [newValue]);
                },
                changecomplete( slider, newValue, thumb, eOpts ) {
                    this.task.delay(25, undefined, undefined, [newValue]);
                },
            },
        }];
        this.callParent();
        this.task = new Ext.util.DelayedTask(function(v) {
            this.changeValue(v);
        }, this);
    },

    afterRender : function() {
        this.callParent();
        if (this.tip)
            this.tip = Ext.create('Ext.tip.ToolTip', {
                target: this.el,
                trackMouse: true,
                html: this.tip,
            });
        this.mon(this.getEl(), 'mousewheel', function(e) {
            if (this.disabled) return;
            var event = e.browserEvent,
                realDelta = event.wheelDelta;
            // normalize the delta
            if (event.wheelDelta) // IE & Opera
                realDelta = event.wheelDelta / 120;
            else if (event.detail) // W3C
                realDelta = -event.detail / 3;

            this.changeValue(Math.round(this.value + this.step*realDelta));
        }, this);
    },

    changeValue: function(v) {
        v = Math.max(this.min, v);
        v = Math.min(this.max, v);
        if (self.value === v) return;
        this.value = v;
        this.queryById('valueText').setText(this.value + this.suffix);
        this.queryById('slider').setValue(this.value);
        this.fireEvent('change', v);
    },

    setDisabled: function(disabled) {
        this.disabled = disabled;
        this.queryById('slider').setDisabled(disabled);
        if (disabled)
            this.queryById('valueText').addCls('disabled');
        else
            this.queryById('valueText').removeCls('disabled');
    },

});

//--------------------------------------------------------------------------------------
// Tag visualizers - normal renderers should should have view/edit modes
//--------------------------------------------------------------------------------------

Ext.define('BQ.ui.view.tags.string', {
    extend: 'Ext.Component',
    alias: 'widget.bq_ui_view_tags_string',
    componentCls: 'bq_ui_view_tags',

    autoEl: {
        tag: 'div',
    },

    initComponent : function() {
        this.addCls(this.tag.type || this.tag.name);
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        this.update();
    },

    update: function() {
        if (!this.tag) return;
        this.getEl().dom.textContent = this.tag.name+': '+this.tag.value;
    },

});

Ext.define('BQ.ui.view.tags.copyright', {
    extend: 'BQ.ui.view.tags.string',
    alias: 'widget.bq_ui_view_tags_copyright',

    update: function() {
        if (!this.tag) return;
        this.getEl().dom.textContent = '© '+this.tag.value;
    },

});

Ext.define('BQ.ui.view.tags.description', {
    extend: 'BQ.ui.view.tags.string',
    alias: 'widget.bq_ui_view_tags_description',

    update: function() {
        if (!this.tag) return;
        this.getEl().dom.textContent = this.tag.value;
    },

});


//--------------------------------------------------------------------------------------
// Tag editors - normal renderers should should have view/edit modes
//--------------------------------------------------------------------------------------

Ext.define('BQ.ui.edit.tags.string', {
    extend: 'Ext.form.field.Text',
    alias: 'widget.bq_ui_edit_tags_string',
    componentCls: 'bq_ui_edit_tags',
});

Ext.define('BQ.ui.edit.tags.number', {
    extend: 'Ext.form.field.Number',
    alias: 'widget.bq_ui_edit_tags_number',
    componentCls: 'bq_ui_edit_tags',
    decimalPrecision: 6,
});

Ext.define('BQ.ui.edit.tags.boolean', {
    extend: 'Ext.form.field.Checkbox',
    alias: 'widget.bq_ui_edit_tags_boolean',
    componentCls: 'bq_ui_edit_tags',
    initComponent : function() {
        this.checked = this.value;
        this.callParent();
    },
});

Ext.define('BQ.ui.edit.tags.description', {
    extend: 'Ext.form.field.TextArea',
    alias: 'widget.bq_ui_edit_tags_description',
    componentCls: 'bq_ui_edit_tags',
});

//--------------------------------------------------------------------------------------
// BQ.connoisseur.view.dataset
// params:
//    model
//--------------------------------------------------------------------------------------

Ext.define('BQ.ui.view.dataset', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_ui_view_dataset',
    componentCls: 'bq_ui_view_dataset',
    layout: 'fit',

    afterRender : function() {
        this.callParent();
        var url = this.model.get_dataset();
        if (!url) {
            // add select dataset button
            this.add({
                xtype: 'button',
                text: 'Select dataset',
                scale: 'large',
                //maxWidth: 200,
                scope: this,
                handler: this.selectDataset,
            });
            return;
        }

        this.add({
            xtype: 'tbtext',
            itemId: 'datasetHeader',
            text: '<h2>Dataset</h2>',
        });

        if (!url.startsWith('/') && !url.startsWith('http')) {
            url = '/data_service/' + url;
        }
        BQFactory.request({
            uri: url,
            cb: callback(this, 'ondataset'),
            errorcb: callback(this, 'onerror'),
            uri_params: {view:'full'}
        });

        this.mon(this.getEl(), 'mouseover', function() {
            this.fireEvent('selected', this.resource);
        }, this);
    },

    ondataset: function(r) {
        this.setLoading(false);
        var h = this.queryById('datasetHeader');
        h.setText('<h2>Dataset: '+r.name+' ('+r.values.length+' images)</h2>');

        this.resource = r;
        this.fireEvent('selected', r);
    },

    selectDataset: function() {
        var browser = new Bisque.DatasetBrowser.Dialog({
            height: '85%',
            width:  '85%',
            listeners: {
                scope: this,
                DatasetSelect: function(me, resource) {
                    this.model.set_dataset(resource.uri);
                },
            },
        });
    },

});

//--------------------------------------------------------------------------------------
// BQ.connoisseur.parameters.Editor
// this component visualizes some legal model attributes and allows editing all parameters
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.parameters.Window', {
    extend: 'Ext.window.Window',
    alias: 'widget.bq_parameters_window',
    cls: 'bq_parameters_window',

    width: Math.min(800, window.innerWidth/1.6),
    height: window.innerHeight/1.1,
    modal: true,
    buttonAlign: 'right',
    plain : true,
    border: 0,
    layout: {
        type: 'vbox',
        align: 'stretch',
    },
    autoScroll: true,

    initComponent : function() {
        this.buttons = [{
            text: 'Cancel',
            cls: 'cancel',
            scope: this,
            handler: this.close,
        }, {
            text: 'Save',
            cls: 'save',
            scope: this,
            handler: this.onSave,
        }];
        this.items = [{
            xtype: 'tbtext',
            text: '<h2>Model parameters</h2>',
        }, {
            xtype: 'bq_ui_edit_tags_string',
            itemId: 'model_name',
            name: 'name',
            fieldLabel: 'Name',
            labelWidth: 200,
            allowBlank: false,
            value: this.model.get_name(),
        }];

        for (n in this.tags_visualize) {
            t = this.model.get_tag(n);
            if (t) this.items.push(this.getEditor(t));
        }

        if (this.tags_advanced) {
            this.items.push({
                xtype: 'tbtext',
                text: '<h2>Advanced</h2>',
            });
            for (n in this.tags_advanced) {
                t = this.model.get_tag(n);
                if (t) this.items.push(this.getEditor(t));
            }
        }

        this.callParent();

        this.onApi(BQ.connoisseur.api.xml);
    },

    getEditor: function(tag) {
        var xtype = 'bq_ui_edit_tags_string',
            ttype = tag.type || tag.name;
        if (ttype in BQ.ui.edit.tags) {
            xtype = 'bq_ui_edit_tags_'+ttype;
        }
        return {
            xtype: xtype,
            name: tag.name,
            fieldLabel: tag.name.replace(/_/g, ' '),
            labelWidth: 200,
            //allowBlank: false,
            value: tag.value,
            tag: tag.tag || tag,
        }
    },

    getTags: function(xml, xpath, parent) {
        var tags = [],
            xt = BQ.util.xpath_nodes(xml, xpath),
            t = null,
            tt = null, name = null, value = null, type=null;
        for (var i=0; t=xt[i]; ++i) {
            name = t.getAttribute('name');
            type = t.getAttribute('type');
            value = t.getAttribute('value');
            tt = parent.find_tags(name);
            if (tt) {
                // parameter is present in the model, use its value
                value = tt.value;
            } else {
                // parameter is not present in the model, create a tag for it
                tt = parent.addtag({
                    name:name,
                    value:value,
                    type: type
                });
            }
            tags.push({
                name: name,
                value: value,
                type: type,
                tag: tt,
            });
        }
        return tags;
    },

    createEditors: function(tags, title) {
        var t=null,
            i=null;
        this.add({
            xtype: 'tbtext',
            text: '<h2>'+title+'</h2>',
        });
        for (i=0; (t=tags[i]); ++i) {
            if (t) this.add(this.getEditor(t));
        }
    },

    onApi: function(xml) {
        var adapter_gobs = this.model.get_tag('adapter_gobjects'),
            adapter_pixs = this.model.get_tag('adapter_pixels'),
            framework = this.model.get_tag('framework'),
            tmpl_annotations = this.getTags(xml, Ext.String.format('*/tag[@name="adapters_gobjects"]/plugin[@name="{0}"]/tag', adapter_gobs.value), adapter_gobs),
            tmpl_pixels = this.getTags(xml, Ext.String.format('*/tag[@name="adapters_pixels"]/plugin[@name="{0}"]/tag', adapter_pixs.value), adapter_pixs),
            tmpl_framework = this.getTags(xml, Ext.String.format('*/tag[@name="frameworks"]/plugin[@name="{0}"]/tag', framework.value), framework);

        // dima: set proper values
        this.createEditors(tmpl_annotations, 'Annotations adapter');
        this.createEditors(tmpl_pixels, 'Pixels adapter');
        this.createEditors(tmpl_framework, 'Framework (advanced)');
    },

    onSave: function() {
        var i = null,
            item = null;

        // set the name attribute
        this.model.set_name(this.queryById('model_name').value);

        // set other tag values
        for (var i=0; (item=this.items.items[i]); ++i) {
            if (item.tag) { // && item.value) {
                item.tag.value = item.value;
            }
        }
        this.model.save();
        this.close();
    },

});


//--------------------------------------------------------------------------------------
// BQ.connoisseur.parameters.Editor
// this component visualizes some legal model attributes and allows editing all parameters
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.parameters.Editor', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_parameters_editor',
    componentCls: 'bq_parameters_editor',
    layout : {
        type: 'vbox',
        align: 'stretch'
    },
    //height: 40,

    tags_visualize: {
        "author": "author",
        "license": "license",
        "copyright": "copyright",
        "description": "description",
    },

    tags_advanced: {
        "minimum_samples_augmentation": "minimum_samples_augmentation",
        "use_background_class": "use_background_class",
    },

    initComponent : function() {
        var t = null,
            ttag = null,
            tcomp = null,
            n = null;
        this.items = [{
            xtype: 'container',
            layout: {
                type: 'vbox',
                align: 'right'
            },
            items: [{
                xtype: 'button',
                cls: 'edit_icon',
                scope: this,
                handler: this.onEdit,
                width: 35,
                height: 35,
            }],
        }];
        for (n in this.tags_visualize) {
            t = this.model.get_tag(n);
            ttag = t.type || t.name;
            tcomp = 'bq_ui_view_tags_string';
            if (ttag in BQ.ui.view.tags) {
                tcomp = 'bq_ui_view_tags_'+ttag;
            }
            this.items.push({
                xtype: tcomp,
                tag: t,
                //height: 40,
            });
        }
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
    },

    onEdit: function() {
        Ext.create('BQ.connoisseur.parameters.Window', {
            model: this.model,
            tags_visualize: this.tags_visualize,
            tags_advanced: this.tags_advanced,
        }).show();
    },

});

//--------------------------------------------------------------------------------------
// BQ.connoisseur.stages.Viewer
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.stages.Viewer', {
    extend: 'Ext.draw.Component',
    alias: 'widget.bq_ui_stages_view',
    componentCls: 'bq_ui_stages_view',

    width: 460,
    maxWidth: 460,
    height: 110,

    viewBox: 0,
    autoSize: false,
    shrinkWrap: 0,

    afterRender: function() {
        var me = this;
        this.callParent();
        this.stages = [];
        var i=0,
            r=30,
            s=30,
            t=5,
            x=20+r,
            sprite=null,
            caps=['D', 'F', 'S', 'T', 'V'],
            titles=['Select\ndataset', 'Filter\nclasses', 'Create\nsamples', 'Train', 'Validate'];

        for (i=0; i<5; ++i) {
            this.stages.push(this.surface.add({
                type: 'circle',
                //fill: '#4095ea',
                stroke: '#4095ea',
                'stroke-width': 5,
                radius: r,
                x: x,
                y: t+r,
                listeners: {
                    mouseover: {
                        element: 'el',
                        fn: function(sprite, evt, el) {
                            if (!sprite.error && me.tooltip) me.tooltip.hide();
                            if (!sprite.error) return;
                            me.tooltip = me.tooltip || Ext.create('Ext.tip.ToolTip', {
                                target: el,
                                html: sprite.error,
                            });
                            var e = evt.browserEvent;
                            me.tooltip.showAt([e.x, e.y]);
                        },
                    },
                },
            }));
            this.stages[i].show(true);
            x += r + r + s;
        }

        x=20+r;
        for (i=0; i<4; ++i) {
            sprite = this.surface.add({
                type: 'rect',
                //fill: '#4095ea',
                stroke: '#4095ea',
                'stroke-width': 5,
                x: x+r,
                y: t+r,
                width: s,
                height: 1,
            });
            sprite.show(true);
            x += r + r + s;
        }

        x=20+r;
        for (i=0; i<5; ++i) {
            sprite = this.surface.add({
                type: 'text',
                fill: '#666666',
                //stroke: '#4095ea',
                //'stroke-width': 5,
                x: x-13,
                y: t+r+2,

                text: caps[i],
                font: "45px 'Roboto', sans-serif",
            });
            sprite.show(true);
            sprite = this.surface.add({
                type: 'text',
                fill: '#666666',
                //stroke: '#4095ea',
                //'stroke-width': 5,
                x: x-20,
                y: t+r+r+15,

                text: titles[i],
                font: "14px/2 'Roboto', sans-serif",
            });
            sprite.show(true);
            x += r + r + s;
        }
    },

    update_stage: function(i, text) {
        var s = this.stages[i];
        s.error = undefined;
        if (text === 'finished') {
            s.setStyle( 'fill', '#f5f4a0' );
        } else if (!text) {
            s.setStyle( 'fill', '#ffffff' );
        } else {
            s.setStyle( 'fill', '#ee3e3e' );
            s.error = text;
        }
    },

    update_stages: function(model) {
        var name = null,
            stage = null;
        for (var i=0; i<BQ.connoisseur.stages_tags.length; ++i) {
            name = BQ.connoisseur.stages_tags[i];
            stage = BQ.connoisseur.stages_by_tag[name];
            this.update_stage(stage.vis, stage.status);
        }
    },

});


//--------------------------------------------------------------------------------------
// BQ.connoisseur.stages.Editor
//
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.stages.Editor', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_stages_editor',
    componentCls: 'bq_stages_editor',
    // layout : {
    //     type: 'vbox',
    //     align: 'stretch'
    // },
    layout: {
        type: 'vbox',
        //pack: 'center',
        align: 'center',
    },
    height: 170,

    defaults: {
        width: 300,
        maxWidth: 300,
        scale: 'large',
        hidden: true,
    },

    initComponent : function() {
        this.items = [{
            xtype: 'bq_ui_stages_view',
            itemId: 'stages_viewer',
            width: 460,
            maxWidth: 460,
            height: 110,
            hidden: false,
            model: this.model,
            listeners:{
                scope: this,
                // selected: function(resource) {
                //     this.fireEvent('selected_dataset', resource);
                // },
            },
        },{
            xtype: 'tbspacer',
            height: 15,
            hidden: false,
        }, {
            xtype: 'button',
            itemId: 'OriginalClassesInitialize',
            hidden: true,
            text: 'Initialize classes',
            scale: 'large',
            //maxWidth: 200,
            scope: this,
            handler: function() {
                this.model.execute_stage('update/classes:init');
            },
        }, {
            xtype: 'button',
            itemId: 'ModelClassesFilter',
            hidden: true,
            text: 'Filter classes',
            scale: 'large',
            //maxWidth: 200,
            scope: this,
            handler: function() {
                this.model.execute_stage('update/classes:filter');
            },
        }, {
            xtype: 'button',
            itemId: 'TrainValidateButton',
            hidden: true,
            text: 'Train & Validate',
            scale: 'large',
            //width: 200,
            //minWidth: 200,
            scope: this,
            handler: function() {
                this.model.execute_next_stages();
            },
        }, {
            xtype: 'button',
            itemId: 'ReValidateButton',
            hidden: true,
            text: 'Re-Validate',
            scale: 'large',
            //maxWidth: 200,
            scope: this,
            handler: function() {
                this.model.execute_stage('validate');
            },
        }];
        this.callParent();
        this.stages_viewer = this.queryById('stages_viewer');
    },

    afterRender: function() {
        this.callParent();

        if (this.model.get_dataset() && this.model.original_classes.length===0) {
            this.queryById('OriginalClassesInitialize').setVisible(true);
        }

        this.stages_viewer.update_stages(this.model);

        var stage = this.model.get_last_stage();
        if (!stage) return;

        if (stage.command === 'update/classes:init') {
            this.queryById('ModelClassesFilter').setVisible(true);
        }

        if (stage.id === 6) {
            this.queryById('ReValidateButton').setVisible(true);
        } else if (stage.id >= 1) {
            this.queryById('TrainValidateButton').setVisible(true);
        }

    },

    on_model_change: function() {
        this.stages_viewer.update_stages(this.model);
    },

});


//--------------------------------------------------------------------------------------
// BQ.connoisseur.classes.Plot
//
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.classes.Plot', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_classes_plot',
    componentCls: 'bq_classes_plot',
    layout: 'fit',

    initComponent : function() {
        //var me = this;
        this.items = [{
            xtype: 'chart',
            itemId: 'pie',

            flex: 1,

            title: 'Pie',
            animate: true,
            shadow: false,
            store: this.store,

            insetPadding: 30,

            // legend: {
            //     field: 'label',
            //     position: 'left',
            //     boxStrokeWidth: 0,
            //     labelFont: '12px Helvetica'
            // },
            series: [{
                type: 'pie',
                angleField: 'samples',
                insetPadding: 30,
                label: {
                    //field: 'label',
                    field: 'id_original',
                    display: 'outside',
                    //calloutLine: true,
                    padding: 60,
                },
                showInLegend: true,
                highlight: {
                    segment: {
                        margin: 20
                    }
                },
                tips: {
                    trackMouse: true,
                    cls: 'series_tip',
                    width: 400,
                    height: 100,
                    renderer: BQ.connoisseur.classes.renderer_tip,
                },
                scope: this,
                renderer: BQ.connoisseur.classes.renderer_chart,
                listeners: {
                    scope: this,
                    itemclick: function(item) {
                        var record = item.storeItem;
                        var idx = record.get('id_original') || record.get('id');
                        this.fireEvent('selected_class', idx);
                    },
                },
            }]
        }];
        this.callParent();
        this.pie = this.queryById('pie');

        this.addListener('resize', this.onResize, this);
    },

    afterRender : function() {
        this.callParent();
    },

    bindStore : function(store) {
        this.store = store;
        this.pie.bindStore(store);
    },

    on_model_change: function() {
        try {
            this.pie.redraw(false);
        } catch (e) {
        }
    },

    onResize: function(me, width, height) {
        if (width<150 || height<150) {
            this.pie.setVisible(false);
        } else {
            this.pie.setVisible(true);
        }
    },

});

//--------------------------------------------------------------------------------------
// Model viewer - renders all models present in the model resource
// required parameters:
//     resource - the model resource
//--------------------------------------------------------------------------------------

Ext.namespace('BQ.connoisseur.classes');
BQ.connoisseur.classes.goodness_idx = 0;
BQ.connoisseur.classes.goodness_array = null;

BQ.connoisseur.classes.converter_array = function(v, record) {
    return v.split(',');
};

BQ.connoisseur.classes.converter_array_int = function(v, record) {
    var vv = v.split(','),
        i = 0;
    for (i=0; i<vv.length; ++i) {
        vv[i] = parseFloat(vv[i]);
    }
    return vv;
};

BQ.connoisseur.classes.array_to_string = function(v) {
    var vv=[], i=0;
    for (i=0; i<v.length; ++i) {
        vv.push( ''+parseFloat(v[i]).toFixed(1)+'%' );
    }
    return vv.join(', ');
};

BQ.connoisseur.classes.array_to_string_percent = function(v) {
    var vv=[], i=0;
    for (i=0; i<v.length; ++i) {
        vv.push( ''+(parseFloat(v[i])*100).toFixed(1)+'%' );
    }
    return vv.join(', ');
};

BQ.connoisseur.classes.error_contributions_to_string = function(v, goodness, fp) {
    var vv=[], i=0, vvv=null;
    for (i=0; i<v.length; ++i) {
        vvv = v[i].split(';');
        if (vvv.length>3) vvv.length = 3;
        vv.push( Ext.String.format('<p>Top 3 error contributions @{0} goodness of {1} samples <li>{2}', goodness[i], fp[i], vvv.join('</li><li>')) );
    }
    return vv.join('</li></p>');
};

BQ.connoisseur.classes.renderer_tip = function(record, item) {
    var idx = record.get('id_original') || record.get('id'),
        title = '',
        a = record.get('accuracy'),
        e = record.get('error'),
        f1 = record.get('F1'),
        g = record.get('goodness'),
        ec = record.get('error_contributions'),
        discarded = record.get('discarded'),
        fp = [];

    if (record.raw.false_positive)
        fp = BQ.connoisseur.classes.converter_array_int(record.raw.false_positive);

    title += Ext.String.format('<h3>{0}: {1}</h3>', idx, record.get('label'));
    title += Ext.String.format('<p>Samples: {0}', record.get('samples'));
    if (record.raw.samples_actual) title += Ext.String.format(', (Actual: {0})', record.raw.samples_actual);
    if (record.raw.samples_training) title += Ext.String.format(', Training: {0}', record.raw.samples_training);
    if (record.raw.samples_testing) title += Ext.String.format(', Testing: {0}', record.raw.samples_testing);
    if (record.raw.samples_validation) title += Ext.String.format(', Validation: {0}', record.raw.samples_validation);
    title += '</p>';

    if (g && g.length>0 && g[0]) title += '<p>Goodness: '+BQ.connoisseur.classes.array_to_string_percent(g)+'</p>';
    if (discarded && discarded.length>0 && discarded[0]) {
        title += '<p>Discarded: ';
        var d = [], pct;
        for (i=0; i<discarded.length; ++i) {
            pct = (discarded[i]*100.0/record.raw.samples_validation).toFixed(1);
            d.push( Ext.String.format('{0}/{1} ({2}%)', discarded[i], record.raw.samples_validation, pct) );
        }
        title += d.join(', ');
        title += '</p>';
        this.setHeight(390);
    }
    if (a && a.length>0 && a[0]) title += '<p>Accuracy: '+BQ.connoisseur.classes.array_to_string(a)+'</p>';
    if (e && e.length>0 && e[0]) title += '<p>Error: '+BQ.connoisseur.classes.array_to_string(e)+'</p>';
    if (f1 && f1.length>0 && f1[0]) title += '<p>F1: '+BQ.connoisseur.classes.array_to_string_percent(f1)+'</p>';
    if (ec && ec.length>0 && ec[0]) title += BQ.connoisseur.classes.error_contributions_to_string(ec, g, fp);

    this.addCls('connoisseurio tip');
    this.setTitle(title);
    this.setWidth(500);
    //this.setHeight(390);
    this.dismissDelay = 10 * 60 * 1000; // 10m

    //me.fireEvent('selected_class', idx);
};

BQ.connoisseur.classes.renderer_chart = function (sprite, record, attributes, index, store) {
    var me = store.view || record.store.view,
        v = record.get(me.cutoff_field);

    if (v instanceof Array) {
        v = parseFloat(v[BQ.connoisseur.classes.goodness_idx])*100.0;
    }

    //if (me.extended_view) return attributes;
    if (v < me.cutoff() || record.get('ignored') === true) {
        //attributes.fill = "#ffffff";
        attributes.fill = "#cccccc";
    } else {
        attributes.fill = BQGObject.string_to_color_html(record.data.label);
        //attributes.fill = "#cccccc";
    }

    // resize the sprite in case it's
    if (!attributes.segment && isNaN(attributes.width)) {
        var w = sprite.surface.width - sprite.surface.insetPadding - sprite.x;
        attributes.width = (v/100.0)*w;
    }

    // reverse axis direction
    /*if (!attributes.segment) {
        attributes.y = sprite.surface.height - attributes.y - sprite.surface.insetPadding;
    }*/

    return attributes;
};

Ext.define('BQ.connoisseur.classes.Model', {
    extend: 'Ext.data.Model',
    fields: [{
        name: 'id',
        type: 'int'
    }, {
        name: 'id_original',
        type: 'int',
        convert: function(v, record) {
            if (v==='') return record.data.id; else return v;
        }
    }, {
        name: 'label',
        type: 'string'
    }, {
        name: 'idx_label',
        type: 'string',
        convert: function(v, record) {
            return record.data.label + ' ('+ record.data.id_original + ')';
        }
    }, {
        name: 'samples',
        type: 'int'
    }, {
        name: 'ignored',
        type: 'boolean'
    }, {
        name: 'accuracy',
        type: 'float',
        convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'error',
        type: 'float',
        convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'F1',
        type: 'float',
        convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'F1X',
        type: 'int',
        convert: function(v, record) {
            var value = record.data.F1,
                v = value[BQ.connoisseur.classes.goodness_idx]*100;
            return v;
        },
    }, {
        name: 'samples_validation',
        type: 'int'
    }, {
        name: 'discarded',
        type: 'int',
        convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'goodness',
        type: 'float',
        convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'error_contributions',
        type: 'string',
        convert: BQ.connoisseur.classes.converter_array,
    }]
});

BQ.connoisseur.classes.fnc_transform = function(v) {
    if (v instanceof Array) {
        return parseFloat(v[BQ.connoisseur.classes.goodness_idx]);
    }
    return v;
};

BQ.connoisseur.classes.fnc_sort_discarded_asc = function(o1, o2) {
    var v1 = o1.data.discarded,
        t1 = o1.data.samples_validation || 1,
        v2 = o2.data.discarded,
        t2 = o2.data.samples_validation || 1;
    if (v1 instanceof Array) v1 = parseFloat(v1[BQ.connoisseur.classes.goodness_idx]);
    if (v2 instanceof Array) v2 = parseFloat(v2[BQ.connoisseur.classes.goodness_idx]);
    v1 = v1/t1;
    v2 = v2/t2;
    if (v1===v2) return 0;
    if (v1>v2) return 1;
    return -1;
};

BQ.connoisseur.classes.fnc_sort_discarded_desc = function(o1, o2) {
    var v1 = o1.data.discarded,
        t1 = o1.data.samples_validation || 1,
        v2 = o2.data.discarded,
        t2 = o2.data.samples_validation || 1;
    if (v1 instanceof Array) v1 = parseFloat(v1[BQ.connoisseur.classes.goodness_idx]);
    if (v2 instanceof Array) v2 = parseFloat(v2[BQ.connoisseur.classes.goodness_idx]);
    v1 = v1/t1;
    v2 = v2/t2;
    if (v1===v2) return 0;
    if (v1<v2) return 1;
    return -1;
};

Ext.define('BQ.connoisseur.classes.View', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_model_classes_view',
    componentCls: 'bq_model_classes_view',

    border: 0,
    plain: true,

    layout: {
        type: 'hbox',
        align: 'stretch',
    },

    cutoff: null,
    extended_view: false,

    initComponent : function() {
        var me = this;

        // store
        this.store = Ext.create('Ext.data.Store', {
            autoLoad: false,
            model: 'BQ.connoisseur.classes.Model',
            view: this,
            proxy: {
                type: 'memory',
                reader: {
                    type: 'json',
                }
            },
            sorters: [{
                property: 'samples',
                direction: 'DESC',
            }],

            listeners: {
                scope: this,
                beforesort( me, sorters, eOpts) {
                    if (sorters[0].property !== 'discarded') {
                        sorters[0].transform = BQ.connoisseur.classes.fnc_transform;
                    } else {
                        if (sorters[0].direction === "ASC")
                            sorters[0].sort = BQ.connoisseur.classes.fnc_sort_discarded_asc;
                        else
                            sorters[0].sort = BQ.connoisseur.classes.fnc_sort_discarded_desc;
                    }
                },
            },
        });

        // axes
        this.axes = [{
            type: 'Numeric',
            //position: this.extended_view ? 'left' : 'bottom',
            position: this.extended_view ? 'bottom' : 'bottom',
            fields: this.extended_view ? 'F1' : 'samples',
            label: {
                renderer: this.extended_view ? Ext.util.Format.numberRenderer('0.0') : Ext.util.Format.numberRenderer('0'),
            },
            title: this.extended_view ? 'F1' : 'Number of samples',
            grid: true,
            minimum: 0,
            maximum: this.extended_view ? 1.0 : undefined,
        }, {
            type: 'Category',
            //position: this.extended_view ? 'bottom' : 'left',
            position: this.extended_view ? 'left' : 'left',
            fields: ['idx_label'],
            title: 'Classes',
            //reverse: true,
        }];

        /*if (this.extended_view) {
            axes.push({
                type: 'Numeric',
                //position: this.extended_view ? 'right' : 'top',
                position: this.extended_view ? 'top' : 'top',
                //fields: ['F1', 'accuracy', 'error'],
                fields: ['F1'],
                label: {
                    renderer: Ext.util.Format.numberRenderer('0,0')
                },
                //title: 'F1, Accuracy, Error (%)',
                title: 'F1 (%)',
                //grid: true,
                minimum: 0
            });
        }*/

        // series
        this.series = [];
        this.series.push({
            //type: this.extended_view ? 'column' : 'bar',
            type: this.extended_view ? 'bar' : 'bar',
            xField: 'name',
            yField: this.extended_view ? 'F1' : 'samples',
            //axis: this.extended_view ? 'left' : 'bottom',
            axis: this.extended_view ? 'bottom' : 'bottom',
            highlight: true,
            stacked: false,
            tips: {
                trackMouse: true,
                cls: 'series_tip',
                width: 400,
                height: 100,
                renderer: BQ.connoisseur.classes.renderer_tip,
            },
            /*label: {
                display: 'insideEnd',
                'text-anchor': 'middle',
                field: 'samples',
                renderer: Ext.util.Format.numberRenderer('0'),
                orientation: 'vertical',
                color: '#333'
            },*/
            //scope: this,
            renderer: BQ.connoisseur.classes.renderer_chart,

            listeners: {
                scope: this,
                itemclick: function(item) {
                    var record = item.storeItem;
                    var idx = record.get('id_original') || record.get('id');
                    this.fireEvent('selected_class', idx);
                },
            },
        });

        /*if (this.extended_view) {
            this.series.push({
                //type: 'column',
                type: 'bar',
                xField: 'name',
                //yField: ['F1', 'accuracy', 'error'],
                yField: 'F1',
                //axis: 'right',
                axis: this.extended_view ? 'bottom' : 'bottom',
                highlight: false,
                style: {
                    opacity: 0.5,
                },
                stacked: false,
                groupGutter: 0,
            });
        }
        */

        // legend
        var legend = false;
        /*if (this.extended_view)
            legend = {
                position: 'bottom',
                boxStrokeWidth: 0,
            };*/

        // columns
        this.columns = {
            defaults: {
                tdCls: 'bq_row',
                cls: 'bq_row',
                width: 70,
            },
            items: [{
                text: 'ID',
                dataIndex: 'id'
            }, {
                text: 'Samples',
                dataIndex: 'samples'
            }, {
                text: 'Label',
                dataIndex: 'label',
                flex: 1,
                scope: this,
                renderer: this.rowRenderer,
            }, {
                xtype: 'actioncolumn',
                text: 'Ignore',
                width: 60,
                align : 'center',
                sortable: false,
                menuDisabled: true,
                items: [{
                    iconCls: 'icon_remove',
                    tooltip: 'Ignore this class',
                    scope: this,
                    handler: this.onIgnoreCLass,
                }]
            }],
        };
        var plugins = undefined;
        if (this.extended_view) {
            this.columns = {
                defaults: {
                    tdCls: 'bq_row',
                    cls: 'bq_row',
                    width: 70,
                },
                items: [{
                    text: 'ID',
                    dataIndex: 'id',
                }, {
                    text: 'Samples',
                    dataIndex: 'samples',
                }, {
                    text: 'Accuracy %',
                    dataIndex: 'accuracy',
                    xtype: 'numbercolumn',
                    format:'0.0',
                    renderer: this.floatRenderer,
                }, {
                    text: 'Error %',
                    dataIndex: 'error',
                    xtype: 'numbercolumn',
                    format:'0.0',
                    renderer: this.errorRenderer,
                }, {
                    text: 'F1 %',
                    dataIndex: 'F1',
                    xtype: 'numbercolumn',
                    format:'0.0',
                    renderer: this.percentRenderer,
                }, {
                    text: 'Validated',
                    dataIndex: 'samples_validation',
                }, {
                    text: 'Discarded',
                    dataIndex: 'discarded',
                    renderer: this.discardedRenderer,
                }, /*{
                    text: 'Goodness',
                    dataIndex: 'goodness',
                    renderer: this.floatRenderer,
                }, */{
                    text: 'Label',
                    dataIndex: 'label',
                    flex: 3,
                    scope: this,
                    renderer: this.rowRenderer,
                }, {
                    xtype: 'actioncolumn',
                    text: 'Ignore',
                    width: 60,
                    align : 'center',
                    sortable: false,
                    menuDisabled: true,
                    items: [{
                        iconCls: 'icon_remove',
                        tooltip: 'Ignore this class',
                        scope: this,
                        handler: this.onIgnoreCLassModel,
                    }]
                }],
            };

            /*plugins = [{
                ptype: 'rowexpander',
                rowBodyTpl : new Ext.XTemplate(
                    '<p><b>Company:</b> {company}</p>',
                    '<p><b>Change:</b> {change:this.formatChange}</p><br>',
                    '<p><b>Summary:</b> {desc}</p>',
                {
                    formatChange: function(v){
                        var color = v >= 0 ? 'green' : 'red';
                        return '<span style="color: ' + color + ';">' + Ext.util.Format.usMoney(v) + '</span>';
                    }
                })
            }];*/
        }

        // UI
        this.items = [{
            xtype: 'gridpanel',
            itemId  : 'table',
            //title: 'Table',
            flex: 5,
            autoScroll: true,
            border: 0,
            viewConfig: {
                stripeRows: true,
                forceFit: true,
                preserveScrollOnRefresh: true,
            },
            //plugins: 'bufferedrenderer',
            store: this.store,
            columns: this.columns,
            //collapsible: false,
            animCollapse: false,
            plugins: plugins,
            listeners: {
                scope: this,
                select : function(o, record, index ) {
                    var idx = record.get('id_original') || record.get('id');
                    this.fireEvent('selected_class', idx);
                },
            },
        }];
        this.callParent();
    },

    loadData: function ( classes ) {
        this.classes = classes;
        this.store.loadData( this.classes );
        this.fireEvent('loaded_data', this, this.store);
    },

    afterRender : function() {
        this.callParent();
    },

    on_model_change: function()  {
        this.queryById('table').getView().refresh();
    },

    rowRenderer: function (value, meta, record) {
        var me = this,
            v = record.get(me.cutoff_field);
        if (v instanceof Array) {
            v = v[BQ.connoisseur.classes.goodness_idx]*100;
        }
        if (v < me.cutoff() || record.get('ignored') === true) {
            meta.tdCls = 'ignored';
        }
        meta.tdAttr = Ext.String.format('data-qtip="{0}"', value);
        return value;
    },

    numberRenderer: function (value, meta, record) {
        var v = value[BQ.connoisseur.classes.goodness_idx];
        return Ext.util.Format.number(v, '0');
    },

    floatRenderer: function (value, meta, record) {
        var v = value[BQ.connoisseur.classes.goodness_idx];
        if (record.data.goodness && record.data.goodness instanceof Array) {
            var g = record.data.goodness[BQ.connoisseur.classes.goodness_idx];
            meta.tdAttr = Ext.String.format('data-qtip="@goodness {0}"', g);
        }
        return Ext.util.Format.number(v, '0.0');
    },

    percentRenderer: function (value, meta, record) {
        var v = value[BQ.connoisseur.classes.goodness_idx];
        if (record.data.goodness && record.data.goodness instanceof Array) {
            var g = record.data.goodness[BQ.connoisseur.classes.goodness_idx];
            meta.tdAttr = Ext.String.format('data-qtip="@goodness {0}"', g);
        }
        return Ext.util.Format.number(v*100, '0.0');
    },

    discardedRenderer: function (value, meta, record) {
        var v = value[BQ.connoisseur.classes.goodness_idx],
            t = record.data.samples_validation || 0,
            pct = 0;
        if (t<1)
            return Ext.util.Format.number(v, '0');
        pct = v*100.0/t;
        meta.tdAttr = Ext.String.format('data-qtip="{0}/{1}: {2}%"', v, t, Ext.util.Format.number(pct, '0.0'));
        return Ext.String.format('{0}%', Ext.util.Format.number(pct, '0.0'));
    },

    errorRenderer: function (value, meta, record) {
        var v = value[BQ.connoisseur.classes.goodness_idx],
            c = '';
        if (record.data.error_contributions && record.data.error_contributions instanceof Array) {
            c = record.data.error_contributions[BQ.connoisseur.classes.goodness_idx];
        }
        meta.tdAttr='data-qtip="' + c.replace(/;/g, '<br>') + '"';
        return Ext.util.Format.number(v, '0.0');
    },

    onIgnoreCLass: function(grid, rowIndex, colIndex) {
        if (this.model.model_classes.length>0) {
            BQ.ui.notification('Model classes have already been initialized and can not change');
            return;
        }
        this.onIgnoreCLassModel(grid, rowIndex, colIndex);
    },

    onIgnoreCLassModel: function(grid, rowIndex, colIndex) {
        var record = grid.getStore().getAt(rowIndex);
        if (record.get('ignored')===true)
            record.set('ignored', false);
        else
            record.set('ignored', true);

        this.model.updateOriginalClass(record);
    },

});

//--------------------------------------------------------------------------------------
// BQ.connoisseur.classes.Summary
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.classes.Summary', {
    extend: 'Ext.Component',
    alias: 'widget.bq_model_classes_summary',
    componentCls: 'bq_model_classes_summary',

    autoEl: {
        tag: 'div',
    },
    autoScroll: true,

    afterRender : function() {
        this.callParent();
        this.updateModel(this.model);
        this.on('beforeshow', this.onBeforeShow, this);
    },

    onBeforeShow: function() {
        this.doUpdate();
    },

    doUpdate: function() {
        this.updateModel(this.model);
    },

    updateModel: function(model) {
        var html = '',
            dom = this.getEl().dom,
            i=0, ii=0, s=null, a=null, has_a = false, has_e = false, has_d = false, has_f = false,
            num_samples=0,
            num_augmented=0,
            num_classes_accepted=0,
            num_trained=0,
            num_tested=0,
            num_validated=0,
            num_validated_si=0,
            accuracy = [[], [], []],
            error = [[], [], []],
            accuracy_si = [[], [], []],
            error_si = [[], [], []],
            discarded = [[], [], []],
            discarded_si = [[], [], []],
            f1 = [[], [], []],
            f1_si = [[], [], []],
            aa = 0, ae = 0,
            title = '', is_ignored=false,
            minimum_accuracy = model.get_minimum_accuracy()*100.0;
        this.model = model;
        if (this.model.model_classes.length === 0) return;

        for (i=0; (s=this.model.model_classes[i]); ++i) {
            num_samples += s.samples_actual || s.samples;
            if (s.samples_training) num_trained += s.samples_training;
            if (s.samples_testing) num_tested += s.samples_testing;
            if (s.samples_validation) num_validated += s.samples_validation;

            is_ignored = s.ignored;

            if (s.F1) {
                has_f = true;
                a = BQ.connoisseur.utils.toArray(s.F1);
                f1[0][i] = a[0]*100.0; f1[1][i] = a[1]*100.0; f1[2][i] = a[2]*100.0;
                is_ignored = s.ignored || f1[BQ.connoisseur.classes.goodness_idx][i] < minimum_accuracy;
                if (!is_ignored) {
                    f1_si[0][i] = a[0]*100.0; f1_si[1][i] = a[1]*100.0; f1_si[2][i] = a[2]*100.0;
                }
            }

            if (!is_ignored) {
                num_classes_accepted += 1;
                num_validated_si += s.samples_validation;
            }

            if (s.accuracy) {
                has_a = true;
                a = BQ.connoisseur.utils.toArray(s.accuracy);
                accuracy[0][i] = a[0]; accuracy[1][i] = a[1]; accuracy[2][i] = a[2];
                if (!is_ignored) {
                    accuracy_si[0][ii] = a[0]; accuracy_si[1][ii] = a[1]; accuracy_si[2][ii] = a[2];
                }
            }

            if (s.error) {
                has_e = true;
                a = BQ.connoisseur.utils.toArray(s.error);
                error[0][i] = a[0]; error[1][i] = a[1]; error[2][i] = a[2];
                if (!is_ignored) {
                    error_si[0][ii] = a[0]; error_si[1][ii] = a[1]; error_si[2][ii] = a[2];
                }
            }

            if (s.discarded) {
                has_d = true;
                a = BQ.connoisseur.utils.toArray(s.discarded);
                discarded[0][i] = a[0]; discarded[1][i] = a[1]; discarded[2][i] = a[2];
                if (!is_ignored) {
                    discarded_si[0][ii] = a[0]; discarded_si[1][ii] = a[1]; discarded_si[2][ii] = a[2];
                }
            }

            if (!is_ignored) ++ii;
        }
        num_augmented = num_trained+num_tested+num_validated;

        html += Ext.String.format('<h2>Classes: {0}, in model: {1}, accepted: {2}</h2>',
            this.model.original_classes.length, this.model.model_classes.length, num_classes_accepted);
        html += Ext.String.format('<h2>Samples: {0}, augmented: {1}</h2>', num_samples, num_augmented);
        html += Ext.String.format('<p>Used for training: {0}</p>', num_trained);
        html += Ext.String.format('<p>Used for testing: {0}</p>', num_tested);
        html += Ext.String.format('<p>Used for validation: {0}</p>', num_validated);

        if (has_a && has_e && has_d) {
            html += Ext.String.format('<h2>Average accuracy and error</h2>' );
            html += Ext.String.format('<p>{0}%/{1}%, discarding {2}%, @goodness 0.0</p>',
                BQ.connoisseur.utils.avg(accuracy[0]).toFixed(1),
                BQ.connoisseur.utils.avg(error[0]).toFixed(1),
                (BQ.connoisseur.utils.sum(discarded[0])*100.0/num_validated).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}%, discarding {2}%, @goodness 0.5</p>',
                BQ.connoisseur.utils.avg(accuracy[1]).toFixed(1),
                BQ.connoisseur.utils.avg(error[1]).toFixed(1),
                (BQ.connoisseur.utils.sum(discarded[1])*100.0/num_validated).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}%, discarding {2}%, @goodness 0.9</p>',
                BQ.connoisseur.utils.avg(accuracy[2]).toFixed(1),
                BQ.connoisseur.utils.avg(error[2]).toFixed(1),
                (BQ.connoisseur.utils.sum(discarded[2])*100.0/num_validated).toFixed(1) );
        } else if (has_a && has_e) {
            html += Ext.String.format('<h2>Average accuracy and error</h2>' );
            html += Ext.String.format('<p>{0}%/{1}% @goodness 0.0</p>',
                BQ.connoisseur.utils.avg(accuracy[0]).toFixed(1), BQ.connoisseur.utils.avg(error[0]).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}% @goodness 0.5</p>',
                BQ.connoisseur.utils.avg(accuracy[1]).toFixed(1), BQ.connoisseur.utils.avg(error[1]).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}% @goodness 0.9</p>',
                BQ.connoisseur.utils.avg(accuracy[2]).toFixed(1), BQ.connoisseur.utils.avg(error[2]).toFixed(1) );
        }

        if (has_a && has_e && has_d) {
            html += Ext.String.format('<h2>Average accuracy and {0}error for accepted classes</h2>', title);
            html += Ext.String.format('<p>{0}%/{1}%, discarding {2}%, @goodness 0.0</p>',
                BQ.connoisseur.utils.avg(accuracy_si[0]).toFixed(1),
                BQ.connoisseur.utils.avg(error_si[0]).toFixed(1),
                (BQ.connoisseur.utils.sum(discarded_si[0])*100.0/num_validated_si).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}%, discarding {2}%, @goodness 0.5</p>',
                BQ.connoisseur.utils.avg(accuracy_si[1]).toFixed(1),
                BQ.connoisseur.utils.avg(error_si[1]).toFixed(1),
                (BQ.connoisseur.utils.sum(discarded_si[1])*100.0/num_validated_si).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}%, discarding {2}%, @goodness 0.9</p>',
                BQ.connoisseur.utils.avg(accuracy_si[2]).toFixed(1),
                BQ.connoisseur.utils.avg(error_si[2]).toFixed(1),
                (BQ.connoisseur.utils.sum(discarded_si[2])*100.0/num_validated_si).toFixed(1) );
        } else if (has_a && has_e) {
            html += Ext.String.format('<h2>Average accuracy and {0}error for accepted classes</h2>', title);
            html += Ext.String.format('<p>{0}%/{1}% @goodness 0.0</p>',
                BQ.connoisseur.utils.avg(accuracy_si[0]).toFixed(1), BQ.connoisseur.utils.avg(error_si[0]).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}% @goodness 0.5</p>',
                BQ.connoisseur.utils.avg(accuracy_si[1]).toFixed(1), BQ.connoisseur.utils.avg(error_si[1]).toFixed(1) );
            html += Ext.String.format('<p>{0}%/{1}% @goodness 0.9</p>',
                BQ.connoisseur.utils.avg(accuracy_si[2]).toFixed(1), BQ.connoisseur.utils.avg(error_si[2]).toFixed(1) );
        }

        dom.innerHTML = html;
    },

});


//--------------------------------------------------------------------------------------
// BQ.connoisseur.classes.Comparison
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.classes.ModelComparison', {
    extend: 'Ext.data.Model',
    fields: [{
        name: 'label',
        type: 'string'
    }, {
        name: 'accuracy',
        type: 'float',
        //convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'error',
        type: 'float',
        //convert: BQ.connoisseur.classes.converter_array,
    }, {
        name: 'F1',
        type: 'float',
        //convert: BQ.connoisseur.classes.converter_array,
    }]
});

BQ.connoisseur.classes.renderer_comparison_tip = function(record, item) {
    var title = '',
        d = record.raw['a_'+item.yField],
        g = BQ.connoisseur.utils.toArray(record.raw.c1.goodness)
        f1 = BQ.connoisseur.utils.toArray(record.raw.c1[item.yField]),
        f2 = BQ.connoisseur.utils.toArray(record.raw.c2[item.yField]);

    if (item.yField === 'F1') {
        f1 = BQ.connoisseur.utils.mul(f1, 100);
        f2 = BQ.connoisseur.utils.mul(f2, 100);
    }

    title += Ext.String.format('<h3>{0}</h3>', record.get('label'));
    title += Ext.String.format('<p>{0} in this model: {1}</p>', item.yField, BQ.connoisseur.classes.array_to_string(f1));
    title += Ext.String.format('<p>{0} in comparison: {1}</p>', item.yField, BQ.connoisseur.classes.array_to_string(f2));
    title += Ext.String.format('<p>{0} improvement: {1}</p>', item.yField, BQ.connoisseur.classes.array_to_string(d));
    if (g && g.length>0)
        title += Ext.String.format('<p>@ Goodness: {0}</p>', BQ.connoisseur.classes.array_to_string_percent(g));

    this.addCls('connoisseurio tip');
    this.setTitle(title);
    this.setWidth(500);
    this.setHeight(140);
    this.dismissDelay = 10 * 60 * 1000; // 10m
};

Ext.define('BQ.connoisseur.classes.Comparison', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_model_classes_comparison',
    componentCls: 'bq_model_classes_comparison',

    layout: {
        type: 'vbox',
        align: 'stretch',
    },

    initComponent : function() {
        this.comparison = [];

        this.store = Ext.create('Ext.data.Store', {
            autoLoad: false,
            model: 'BQ.connoisseur.classes.ModelComparison',
            proxy: {
                type: 'memory',
                reader: {
                    type: 'json',
                }
            },
            sorters: [{
                property: 'label',
                direction: 'ASC',
            }],
        });

        // axes
        this.axes = [{
            type: 'Numeric',
            position: 'bottom',
            fields: ['F1', 'accuracy', 'error'],
            label: {
                renderer: Ext.util.Format.numberRenderer('0.0'),
            },
            title: 'Improvement %',
            grid: true,
            minimum: -100,
            maximum: 100,
        }, {
            type: 'Category',
            position: 'left',
            fields: ['label'],
            title: 'Classes',
        }];


        // series
        this.series = [{
            type: 'bar',
            xField: 'name',
            yField: ['F1', 'accuracy', 'error'],
            axis: 'bottom',
            highlight: true,
            stacked: false,
            tips: {
                trackMouse: true,
                cls: 'series_tip',
                width: 400,
                height: 100,
                renderer: BQ.connoisseur.classes.renderer_comparison_tip,
            },
            //renderer: BQ.connoisseur.classes.renderer_comparison_chart,
        }];

        this.items = [{
            xtype: 'container',
            height: 50,
            padding: '10 0 0 0',
            layout: {
                type: 'hbox',
                pack: 'center',
                align: 'middle',
            },
            items: [{
                xtype: 'button',
                itemId: 'SelectModel',
                text: 'Select model for comparison',
                scale: 'large',
                //maxWidth: 200,
                scope: this,
                handler: this.doLoadComparison,
            }],
        }, {
            xtype: 'chart',
            itemId: 'plot',
            flex: 1,
            insetPadding: 20,
            animate: true,
            shadow: false,
                legend: {
                    position: 'bottom',
                    boxStrokeWidth: 0,
                    padding: 0,
                },
            store: this.store,
            axes: this.axes,
            series: this.series,
        }];
        this.callParent();
        this.plot = this.queryById('plot');
    },

    afterRender : function() {
        this.callParent();
        //this.updateModel(this.model);
    },

    doLoadComparison : function() {
        var browser = new Bisque.ResourceBrowser.Dialog({
            height: '85%',
            width: '85%',
            selType: 'SINGLE',
            dataset: '/data_service/connoisseur',
            query_resource_type: 'connoisseur',
            listeners: {
                scope: this,
                Select: function(me, resource) {
                    this.onLoadComparison(resource);
                },
            },
        });
    },

    onLoadComparison : function(resource) {
        if (resource.tags.length < 1) {
            this.setLoading('Loading model...');
            BQFactory.request({
                uri: resource.uri,
                uri_params: { view : 'deep' },
                cb: callback(this, this.onLoadComparison),
                errorcb: callback(this, this.onError),
            });
            return;
        }

        this.setLoading(false);
        this.model2 = Ext.create('BQ.connoisseur.Model', {
            resource: resource,
            listeners:{
                scope: this,

                working: function(model, text) {
                    this.setLoading(text);
                },

                done: function(model) {
                    this.setLoading(false);
                },

                //change: function(model) {
                //    this.queryById('editor').on_model_change();
                //},
            },
        });

        var i=0, s=null, s2=null, A=null, E=null, F=null;
        this.comparison = [];
        if (this.model.model_classes.length === 0) return;
        for (i=0; (s=this.model.model_classes[i]); ++i) {
            if (s.ignored) continue;
            if (!(s.label in this.model2.model_classes_by_name)) continue;
            s2 = this.model2.model_classes_by_name[s.label];

            A = BQ.connoisseur.utils.improvement_percent(s.accuracy, s2.accuracy);
            E = BQ.connoisseur.utils.improvement_percent(s.error, s2.error, true);
            F = BQ.connoisseur.utils.improvement_percent(s.F1, s2.F1, false, 100);
            this.comparison.push({
                label: s.label,
                accuracy: A[BQ.connoisseur.classes.goodness_idx],
                error: E[BQ.connoisseur.classes.goodness_idx],
                F1: F[BQ.connoisseur.classes.goodness_idx],

                a_accuracy: A,
                a_error: E,
                a_F1: F,
                c1: s,
                c2: s2,
            });
        }
        this.doPlot();
    },

    onError: function() {
        this.setLoading(false);
        BQ.ui.error('Error while loading the model');
    },

    redraw: function() {
        if (!this.plot || !this.comparison || this.at_goodness === BQ.connoisseur.classes.goodness_idx) return;
        //this.plot.redraw(false);

        var i=0, s=null;
        for (i=0; (s=this.comparison[i]); ++i) {
            s.accuracy = s.a_accuracy[BQ.connoisseur.classes.goodness_idx];
            s.error = s.a_error[BQ.connoisseur.classes.goodness_idx];
            s.F1 = s.a_F1[BQ.connoisseur.classes.goodness_idx];
        }
        this.at_goodness = BQ.connoisseur.classes.goodness_idx;
        this.store.loadData( this.comparison );
    },

    doPlot: function() {
        this.store.loadData( this.comparison );
    },

});


//--------------------------------------------------------------------------------------
// BQ.connoisseur.classes.Tabs
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.classes.Tabs', {
    extend: 'Ext.tab.Panel',
    alias: 'widget.bq_model_classes_tabs',
    componentCls: 'bq_model_classes_tabs',

    tabPosition: 'top',
    activeTab : 0,
    border : false,
    bodyBorder : 0,
    plain : true,

    initComponent : function() {
        var me = this;
        this.items = [{
            xtype: 'bq_model_classes_view',
            itemId: 'OriginalClassesView',
            title: 'Available classes',
            model: this.model,
            cutoff_field: 'samples',
            cutoff: function() {
                return me.model.get_minimum_samples();
            },
            extended_view: false,
            listeners:{
                scope: this,
                selected_class: function(original_class_id) {
                    this.fireEvent('selected_class', original_class_id);
                },
                loaded_data: function(classes_view) {
                    this.on_loaded_original(classes_view);
                },
            },
        }];

        if (this.model.model_classes.length>0) {
            this.items.push({
                xtype: 'bq_model_classes_view',
                itemId: 'ModelClassesView',
                title: 'Model performance',
                model: this.model,
                cutoff_field: 'F1',
                cutoff: function() {
                    return me.model.get_minimum_accuracy()*100;
                },
                extended_view: true,
                listeners:{
                    scope: this,
                    selected_class : function(original_class_id) {
                        this.fireEvent('selected_class', original_class_id);
                    },
                    loaded_data: function(classes_view) {
                        this.on_loaded_model(classes_view);
                    },
                },
            });
        }

        this.callParent();
        this.grid_classes = this.queryById('OriginalClassesView');
        this.grid_model = this.queryById('ModelClassesView');
    },

    afterRender: function() {
        this.callParent();

        if (this.model.original_classes.length>0) {
            this.setVisible(true);
            this.grid_classes.loadData( this.model.original_classes );
        }

        if (this.model.model_classes.length>0) {
            this.setVisible(true);
            this.grid_model.loadData( this.model.model_classes );
        }
    },

    getStore: function() {
        var cnt = this.getActiveTab();
        return cnt.store;
    },

    on_loaded_original: function(classes_view) {
        if (this.plot_classes) return;

        this.plot_classes = this.insert(1, {
            xtype: 'chart',
            itemId: 'OriginalChart',
            title: 'Classes plot',
            insetPadding: 40,
            //animate: false,
            animate: true,
            shadow: false,
            legend: false,
            view: this.grid_classes,
            store: classes_view.store,
            axes: classes_view.axes,
            series: classes_view.series,
            listeners:{
                scope: this,
                selected_class: function(original_class_id) {
                    this.fireEvent('selected_class', original_class_id);
                },
            },
        });
    },

    on_loaded_model: function(classes_view) {
        if (this.plot_model) return;
        var me = classes_view;
        this.plot_model = this.add({
            xtype: 'chart',
            itemId: 'ModelChart',
            title: 'Performance plot',
            insetPadding: 40,
            //animate: false,
            animate: true,
            shadow: false,
            legend: false,
            view: this.grid_model,
            store: classes_view.store,
            axes: classes_view.axes,
            series: classes_view.series,
            cutoff_field: classes_view.cutoff_field,
            listeners:{
                scope: this,
                selected_class: function(original_class_id) {
                    this.fireEvent('selected_class', original_class_id);
                },
            },
        });

        this.summary = this.add({
            xtype: 'bq_model_classes_summary',
            itemId: 'ModelSummary',
            title: 'Summary',
            model: this.model,

            view: this.grid_model, // mimic other grids
            store: classes_view.store, // mimic other grids
        });

        this.comparison = this.add({
            xtype: 'bq_model_classes_comparison',
            itemId: 'ModelComparison',
            title: 'Comparison',
            model: this.model,

            view: this.grid_model, // mimic other grids
            store: classes_view.store, // mimic other grids
        });

    },

    on_model_change: function() {
        this.grid_classes.on_model_change();
        if (this.plot_classes) {
            try {
                this.plot_classes.redraw(false);
            } catch (e) {
            }
        }
        if (this.grid_model)
            this.grid_model.on_model_change();
        if (this.plot_model) {
            try {
                this.plot_model.redraw(false);
            } catch (e) {
            }
        }
        if (this.summary)
            this.summary.doUpdate();
        if (this.comparison)
            this.comparison.redraw();
    },

});

//--------------------------------------------------------------------------------------
// Model Editor - renders all models present in the model resource
// required parameters:
//     resource - the model resource
//     selected_class : function(original_class_id) {
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.Editor', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_model_editor',
    componentCls: 'bq_model_editor_main',
    layout: 'fit',

    initComponent : function() {
        var me = this;

        var model_descriptors = [{
            xtype: 'tbtext',
            cls: 'title',
            text: '<h1><span class="bold">Connoisseur | </span>'+this.model.get_name()+'</h1>',
        }, {
            xtype: 'bq_parameters_editor',
            itemId: 'parameters',
            height: 180,
            model: this.model,
        }, {
            xtype: 'bq_ui_view_dataset',
            height: 55,
            model: this.model,
            listeners:{
                scope: this,
                selected: function(resource) {
                    this.fireEvent('selected_dataset', resource);
                },
            },
        }, {
            xtype: 'container',
            itemId: 'ModelClassesFilters',
            hidden: true,
            height: 140,
            layout: {
                type: 'hbox',
                pack: 'center',
                align: 'middle',
            },
            items: [{
                xtype: 'bq_ui_numeric',
                itemId: 'selector_samples',
                title: 'Number of samples',
                value: this.model.get_minimum_samples(),
                min: 10,
                max: 500,
                step: 1,
                tip: 'Select a minimum number of samples required for a class to be selected for training',
                listeners: {
                    scope: this,
                    change: function(newValue) {
                        this.model.set_minimum_samples(newValue);
                    },
                },
            }, {
                xtype: 'bq_ui_numeric',
                itemId: 'selector_accuracy',
                title: 'Class accuracy',
                value: this.model.get_minimum_accuracy()*100,
                suffix: '%',
                min: 0,
                max: 99,
                step: 1,
                tip: 'Select a minimum accuracy required for a class to be used in classification',
                listeners: {
                    scope: this,
                    change: function(newValue) {
                        this.model.set_minimum_accuracy(newValue/100.0);
                    },
                },
            }, {
                xtype: 'bq_ui_numeric',
                itemId: 'selector_goodness',
                title: 'Sample goodness',
                value: this.model.get_minimum_goodness()*100,
                suffix: '%',
                min: 0,
                max: 99,
                step: 1,
                tip: 'Select a minimum goodness value required for a sample to be used in classification',
                listeners: {
                    scope: this,
                    change: function(newValue) {
                        this.model.set_minimum_goodness(newValue/100.0);
                        this.update_goodness_idx(newValue);
                    },
                },
            }],
        }, {
            xtype: 'bq_stages_editor',
            itemId: 'stages_editor',
            model: this.model,
            listeners:{
                scope: this,
                // selected: function(resource) {
                //     this.fireEvent('selected_dataset', resource);
                // },
            },
        }];

        this.items = [{
            xtype: 'container',
            layout : 'border',
            items: [{
                xtype: 'container',
                componentCls: 'bq_model_editor',
                itemId: 'model_editor',

                region : 'west',
                width: 500,
                collapsible : false,
                split : true,

                autoScroll: true,
                layout: {
                    type: 'vbox',
                    //pack: 'center',
                    align: 'stretch',
                },
                items: model_descriptors,
            }, {
                xtype: 'bq_model_classes_tabs',
                itemId: 'model_classes_tabs',

                region : 'center',
                collapsible : false,
                split : true,
                flex: 2,
                hidden: true,

                model: this.model,

                listeners:{
                    scope: this,
                    selected_class: function(original_class_id) {
                        this.fireEvent('selected_class', original_class_id);
                    },
                    tabchange: function(tabs, newCard, oldCard) {
                        newCard.store.view = newCard.view || newCard;
                        if (this.pie) {
                            //this.pie.bindStore(tabs.getStore());
                            this.pie.bindStore(newCard.store);
                        }
                    },
                },
            }],
        }];

        this.callParent();

        this.tabs = this.queryById('model_classes_tabs');
        this.editor = this.queryById('model_editor');
        this.pie = this.editor.add({
            xtype: 'bq_classes_plot',
            flex: 3,
            model: this.model,
            store: this.tabs.getStore(),
            listeners:{
                scope: this,
                selected_class: function(original_class_id) {
                    this.fireEvent('selected_class', original_class_id);
                },
            },
        });
        this.selector_samples = this.queryById('selector_samples');
        this.stages_editor = this.queryById('stages_editor');
    },

    afterRender: function() {
        this.callParent();

        if (this.model.original_classes.length>0) {
            this.queryById('ModelClassesFilters').setVisible(true);
        }

        if (this.model.model_classes.length>0) {
            this.update_goodness_idx(this.model.get_minimum_goodness()*100);
            this.selector_samples.setDisabled(true);
        } else {

        }

        if (this.model.original_classes.length>0 && this.model.model_classes.length===0) {
            //this.queryById('TrainValidateButton').setVisible(true);
        }

    },

    on_model_change: function() {
        this.tabs.on_model_change(this.model);
        this.pie.on_model_change(this.model);
        this.stages_editor.on_model_change(this.model);

    },

    update_goodness_idx: function(newValue) {
        if (!this.model.model_classes[0] || !this.model.model_classes[0].goodness || typeof this.model.model_classes[0].goodness === "number") {
            return;
        }

        if (!BQ.connoisseur.classes.goodness_array) {
            BQ.connoisseur.classes.goodness_array = this.model.model_classes[0].goodness.split(',');
            for (var i=0; i<BQ.connoisseur.classes.goodness_array.length; ++i)
                BQ.connoisseur.classes.goodness_array[i] = parseFloat(BQ.connoisseur.classes.goodness_array[i])*100;
        }
        var idx = 0,
            val = Number.MAX_VALUE,
            dist = BQ.connoisseur.classes.goodness_array.slice(0);

        for (var i=0; i<dist.length; ++i) {
            dist[i] =  Math.abs(dist[i] - newValue);
            if (dist[i]<val) {
                val = dist[i];
                idx = i;
            }
        }

        BQ.connoisseur.classes.goodness_idx = idx;
    },
});

//--------------------------------------------------------------------------------------
// Model viewer - renders all models present in the model resource
// required parameters:
//     resource - the model resource
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.class.Preview', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_model_class_preview',
    componentCls: 'bq_model_class_preview',
    layout : {
        type: 'fit',
        align: 'stretch'
    },

    initComponent : function() {
        var me = this;

        this.items = [{
            xtype: 'component',
            itemId: 'thumbnails',
            autoScroll: true,
            flex: 10,
            autoEl: {
                tag: 'div',
                cls: 'thumbnails',
            },
        }, {
            xtype: 'tbtext',
            itemId: 'title',
            cls: 'title',
            //text: '<h2><span class="bold">Preview</span></h2>',
        }];
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        // document.addEventListener('touchmove', function (e) { e.preventDefault(); }, isPassive() ? {
        //     capture: false,
        //     passive: false
        // } : false);

        var me = this,
            thmb = this.queryById('thumbnails');

        this.myScroll = new IScroll(thmb.getEl().dom, {
            bindToWrapper: true,
            mouseWheel: true,
            scrollbars: true,
            resizeScrollbars: true,
            shrinkScrollbars: false,
            //fadeScrollbars: false,
            interactiveScrollbars: true,
            //shrinkScrollbars: 'scale',
            //fadeScrollbars: true,
            mouseWheelAnimationDuration: 20,
            keyBindings: {
                pageUp: 33,
                pageDown: 34,
                end: 35,
                home: 36,
                left: 37,
                up: 38,
                right: 39,
                down: 40
            },

            scrollX: false,
            //scrollX: 1, // use 1 to fit elements into available space
            scrollY: true,

            useInfinity: true,
            elementsCount: 0,
            cacheSize: 100000,
            cacheStep: 1000,

            contentCreateFunc: function () {
                var el = document.createElement('div');
                el.classList.add('tile');
                return {
                    dom: el,
                };
            },
            contentUpdateFunc: function (el, data) {
                if (!data) return;
                if (el._idx_data === data.idx) return;
                el._idx_data = data.idx;
                el.dom.innerHTML = data.name;
                el.dom.style.backgroundImage = "url('"+data.image+"')";
            },
        });
    },

    onclass: function(original_class_id) {
        this.original_class_id = original_class_id;
        var me = this,
            cls = this.model.original_classes[original_class_id],
            class_samples = cls.samples,
            class_name = cls.label,
            title = this.queryById('title'),
            model_id = this.model.get_id();

        title.setText('<h2>'+class_name+'</h2>');

        this.myScroll.reload({
            //elementsCount: class_samples,
            elementsCount: 10,

            dataRequestFunc: function (start, count, buffer) {
                for (var i=start, n=start+count; i<n; ++i) {
                    buffer[i] = {
                        idx : i,
                        name: '' + (i+1),
                        image: '/connoisseur/'+model_id+'/class:'+original_class_id+'/sample:'+(i),
                    };
                }
                //me.updateView(); // only needed if fetch is async
            },
        });
    },

    ondataset: function(resource) {
        var me = this,
            class_name = 'Dataset: '+resource.name,
            class_samples = resource.values.length,
            title = this.queryById('title'),
            values = resource.values;

        title.setText('<h2>'+class_name+'</h2>');

        this.myScroll.reload({
            elementsCount: class_samples,

            dataRequestFunc: function (start, count, buffer) {
                for (var i=start, n=start+count; i<n; ++i) {
                    buffer[i] = {
                        idx : i,
                        //name: '',
                        name: '' + (i+1),
                        image: values[i].value.replace('/data_service/', '/image_service/') + '?thumbnail=280,280',
                    };
                }
                //me.updateView(); // only needed if fetch is async
            },
        });
    },

});


//--------------------------------------------------------------------------------------
// Model viewer - renders all models present in the model resource
// required parameters:
//     resource - the model resource
//--------------------------------------------------------------------------------------

Ext.define('BQ.connoisseur.Panel', {
    extend: 'Ext.container.Container',
    alias: 'widget.bq_model_panel',
    componentCls: 'bq_model_panel',
    layout : 'border',

    initComponent : function() {
        this.model = Ext.create('BQ.connoisseur.Model', {
            resource: this.resource,
            listeners:{
                scope: this,

                working: function(model, text) {
                    this.setLoading(text);
                },

                done: function(model) {
                    this.setLoading(false);
                },

                change: function(model) {
                    //this.setLoading(false);
                    this.queryById('editor').on_model_change();
                },
            },
        });

        var me = this;
        this.items = [{
            xtype: 'bq_model_class_preview',
            itemId: 'preview',
            region : 'east',
            border : false,
            collapsible : true,
            split : false,
            width : 250,
            image_size: 220,
            model: this.model,
        }, {
            xtype: 'bq_model_editor',
            itemId: 'editor',
            flex: 2,
            region : 'center',
            border: 0,
            model: this.model,
            class_name: '',
            listeners:{
                scope: this,
                selected_class: function(original_class_id) {
                    this.queryById('preview').onclass(original_class_id);
                },
                selected_dataset: function(resource) {
                    this.queryById('preview').ondataset(resource);
                },
            },
        }];
        this.callParent();
    },

    afterRender : function() {
        this.callParent();
        //this.queryById('preview').onclass(0);

        // add contextual video
        //BQApp.setActiveHelpVideo('//www.youtube.com/embed/wRzzEV3-48A');

        // add contextual analysis query
        //BQApp.setAnalysisQuery(encodeURIComponent('(accepted_type:"{1}" or "{1}":::)'.replace(/\{1\}/g, 'heatmap')));
    },

});

//--------------------------------------------------------------------------------------
// Resource renderer
//--------------------------------------------------------------------------------------

Ext.define('Bisque.Resource.Connoisseur.Page', {
    extend : 'Bisque.Resource.Page',

    initComponent : function() {
        this.addCls('connoisseurio');
        this.callParent();
    },

    downloadOriginal : function() {
        if (this.resource.src) {
            window.open(this.resource.src);
            return;
        }
        var exporter = Ext.create('BQ.Export.Panel');
        exporter.downloadResource(this.resource, 'none');
    },

    onResourceRender : function() {
        this.add({
            xtype: 'bq_model_panel',
            flex: 2,
            region : 'center',
            border: 0,
            resource: this.resource,
        });
        this.toolbar.hide();

        // create a new menu
        var tb = BQApp.getToolbar();
        var btn = tb.add({
            xtype: 'button',
            itemId: 'menu_contextual',
            menu: {
                xtype: 'menu',
                //cls: 'toolbar-menu',
                plain: true,
                defaults: {
                    scope: this,
                    scale: 'large',
                },
                items: [{
                    xtype: 'bqresourcepermissions',
                    itemId : 'btn_permission',
                    resource: this.resource,
                }, {
                    itemId: 'btnShare',
                    text: 'Share',
                    iconCls: 'icon-group',
                    operation: this.shareResource,
                    handler: this.testAuth1
                }, {
                    itemId: 'btnDelete',
                    text: 'Delete',
                    iconCls: 'icon-delete',
                    handler: this.deleteResource,
                }],
            },
            iconCls: 'icon_menu_contextual',
            //tooltip: 'All information about Bisque',
        });

    },
});

Ext.define('Bisque.Resource.Connoisseur.Compact', {
    extend : 'Bisque.Resource.Compact',
    initComponent : function() {
        this.addCls(['resicon', 'connoisseur']);
        this.callParent();
    },

});

Ext.define('Bisque.Resource.Connoisseur.Card', {
    extend : 'Bisque.Resource.Card',
    initComponent : function() {
        this.addCls('connoisseur');
        this.callParent();
    },
});

Ext.define('Bisque.Resource.Connoisseur.Full', {
    extend : 'Bisque.Resource.Full',
    initComponent : function() {
        this.addCls('connoisseur');
        this.callParent();
    },
});

Ext.define('Bisque.Resource.Connoisseur.Grid', {
    extend : 'Bisque.Resource.Grid',

    initComponent : function() {
        this.addCls(['resicon', 'connoisseur']);
        this.callParent();
    },

    getFields : function(cb) {
        var fields = this.callParent();
        fields[0] = '<div class="resicon gridIcon connoisseur" />';
        return fields;
    },
});
