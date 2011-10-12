/*******************************************************************************

  BQ.upload.Panel  - an integrated uploading tool
  BQ.upload.Dialog 
  

  Author: Dima Fedorov
  
  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/

// store support for html5 uploads into bq global class 

if (bq) {
    bq.html5uploads = (window.File && window.FileList); // && window.FileReader); // - safari does not have FileReader...
}

//Ext.require(['BQ.is.Formats']);

var annotators = {
    'application/x-zip-compressed' : 'BQ.upload.ZipAnnotator',
    'application/x-compressed'     : 'BQ.upload.ZipAnnotator',
    'application/x-gzip'           : 'BQ.upload.ZipAnnotator',
    'application/zip'              : 'BQ.upload.ZipAnnotator',
    'application/gzip'             : 'BQ.upload.ZipAnnotator',    
    'application/x-tar'            : 'BQ.upload.ZipAnnotator',
    'application/x-gtar'           : 'BQ.upload.ZipAnnotator',    
}

var mymime = {
    'zip' : 'application/zip',
    'tar' : 'application/x-tar',
    'gz'  : 'application/x-gzip',
    'tgz' : 'application/x-gzip',        
}

var view_resource = '/client_service/view?resource=';

//--------------------------------------------------------------------------------------
// trivial resource renderers - receive a resource and return a string
//-------------------------------------------------------------------------------------- 

function render_resource(r) {
    return 'Created a resource of type <b>'+r.resource_type+'</b>';
}

function render_image(r) {
    var s = '';
    s += 'Created an <b>image</b> with geometry: ';
    if (r.x) s += 'x: '+r.x+' ';
    if (r.y) s += 'y: '+r.y+' ';
    if (r.z) s += 'z: '+r.z+' ';
    if (r.t) s += 't: '+r.t+' ';
    if (r.ch) s += 'ch: '+r.ch+' ';                                                
    return s;    
}

function render_dataset(r) {
    var m = r.getMembers();
    return 'Created a <b>dataset</b> with '+ m.values.length +' images';
}

var resource_renderers = { 'image': render_image, 'dataset': render_dataset };

function render_resource(r) {
    var f = render_resource;
    if (r.resource_type in resource_renderers)
        f = resource_renderers[r.resource_type];
    return f(r);
}

//--------------------------------------------------------------------------------------
// BQ.upload.Annotator
// a base component for acquiring required annotations about a file being uploaded
// derived classes only need to provide the proper items list to create a form
// all elements of the form will be dynamically queried and added to the dictionary
// emmited in the "done" event
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.upload.Annotator', {
    extend: 'Ext.form.Panel',
    alias: 'widget.uploadannotator',
    
    frame: true,
    bodyPadding: 5,    
    border: 0,
        
    fieldDefaults: {
        labelAlign: 'right',
        labelWidth: 200,
        anchor: '100%',
    },
    
    constructor: function(config) {
        this.addEvents({
            'done' : true,
        });
        this.callParent(arguments);
        return this;
    },      

    onOk: function(e) {
        var form = this.getForm();
        if (!form.isValid()) return;

        var fields = form.getFields();
        var annotations = {};
        
        fields.each( function(){ 
            if (this.isVisible())
                annotations[ this.getName() ] = this.getValue();
        });
        
        this.fireEvent( 'done', annotations );         
    }, 
     
});

//--------------------------------------------------------------------------------------
// BQ.upload.ZipAnnotator
// a specification for requesting additional annotations about the ZIP file
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.upload.ZipAnnotator', {
    extend: 'BQ.upload.Annotator',
    alias: 'widget.uploadzipannotator',
    
    initComponent : function() {

        var types = Ext.create('Ext.data.Store', {
            fields: ['type', 'description'],
            data : [
                {"type":"zip-multi-file",  "description":"multiple unrelated images"},
                {"type":"zip-time-series", "description":"multiple files composing one time-series image"},
                {"type":"zip-z-stack",     "description":"multiple files composing one z-stack"},
                {"type":"zip-5d-image",    "description":"multiple files composing one 5-D image"},                
            ]
        });
 
        var description = 'The import of compressed file "<b>'+this.file.name+'</b>" is ambiguous, we need some additional information. '+
                          'See "help" for information about pcompressed file structure...';
        
        var resolution_question = 'It would also be very nice if you could provide pixel resolution, '+
            'although it\'s optional:';
        
        this.items = [ {
                xtype: 'label',
                html: description,
                cls: 'question',
            },{
                xtype: 'combobox',
                name: 'type',
                fieldLabel: 'My compressed file contains',
                store: types,
                allowBlank: false,
                editable: false,
                queryMode: 'local',
                displayField: 'description',
                valueField: 'type',
                listeners:{
                     scope: this,
                     select: this.onTypeSelected,
                }                
            }, {
                xtype: 'numberfield',
                name: 'number-z',
                fieldLabel: 'Number of Z slices',
                value: 1,
                minValue: 1,
                hidden: true,                
                //maxValue: 50
            }, {
                xtype: 'numberfield',
                name: 'number-t',
                fieldLabel: 'Number of T points',
                value: 1,
                minValue: 1,
                hidden: true,
                //maxValue: 50
            }, {
                xtype: 'displayfield',
                name: 'resolution-title',
                html: resolution_question,
                cls: 'question',
                hidden: true,                
            }, {
                xtype: 'numberfield',
                name: 'resolution-x',
                fieldLabel: 'Pixel resolution X in microns',
                value: 0.0,
                minValue: 0,
                hidden: true,
                //maxValue: 50
            }, {
                xtype: 'numberfield',
                name: 'resolution-y',
                fieldLabel: 'Pixel resolution Y in microns',
                value: 0.0,
                minValue: 0,
                hidden: true,
                //maxValue: 50
            }, {
                xtype: 'numberfield',
                name: 'resolution-z',
                fieldLabel: 'Pixel resolution Z in microns',
                value: 0.0,
                minValue: 0,
                hidden: true,
                //maxValue: 50
            }, {
                xtype: 'numberfield',
                name: 'resolution-t',
                fieldLabel: 'Pixel resolution T in seconds',
                value: 0.0,
                minValue: 0,
                hidden: true,
                //maxValue: 50
            }];
        
        this.buttons = [{
            text: 'Ok',
            formBind: true,
            handler: Ext.Function.bind( this.onOk, this ),
        }];    
        
        this.callParent();
    },
    
    onTypeSelected: function(combo, records) {
        var togglable_fileds = { 'number-z':null, 'number-t':null, 'resolution-title':null, 
            'resolution-x':null, 'resolution-y':null, 'resolution-z':null, 'resolution-t':null };
        
        var my_types = {
            'zip-multi-file' : {},
            'zip-time-series': {'resolution-title':null, 'resolution-x':null, 'resolution-y':null, 'resolution-t':null},
            'zip-z-stack'    : {'resolution-title':null, 'resolution-x':null, 'resolution-y':null, 'resolution-z':null},
            'zip-5d-image'   : {'number-z':null, 'number-t':null, 'resolution-title':null, 
                                'resolution-x':null, 'resolution-y':null, 'resolution-z':null, 'resolution-t':null},                        
        };
        
        // the default state is false
        var form = this.getForm();
        for (var i in togglable_fileds) {
            var e = my_types[records[0].data.type];
            var f = form.findField(i);            
            if (!f) continue;            
            
            if (i in e)
                f.setVisible(true);
            else
                f.setVisible(false);
        }
        
    },
     
});



//--------------------------------------------------------------------------------------
// BQ.ui.UploadItem
// item manages one file upload aspects, UI, progress and intentiates the actual uploader
//-------------------------------------------------------------------------------------- 

var formatFileSize = function (sz) {
    if (typeof sz !== 'number') 
        return '';
    if (sz >= 1000000000)
        return (sz / 1000000000).toFixed(2) + ' GB';
    if (sz >= 1000000)
        return (sz / 1000000).toFixed(2) + ' MB';
    return (sz / 1000).toFixed(2) + ' KB';
};

Ext.define('BQ.upload.Item', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.uploaditem',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    border: 0,
    height: 120,
    closable: true,
    cls: 'uploaditem',
    bodyStyle: 'padding: 10px',
    //autoScroll: true,
    layout: 'anchor',  
    //bodyStyle: 'margin: 15px',
    defaults: { border: 0, height_normal: 120, },
        
    constructor: function(config) {
        this.addEvents({
            'fileuploaded' : true,
            'filecanceled' : true,
            'fileerror'    : true,
        });
        this.callParent(arguments);
        return this;
    },   

    initComponent : function() {
        this.state = BQ.upload.Item.STATES.READY;

        this.progress = Ext.create('Ext.ProgressBar', {
            text:'Ready',
            //anchor: '-10',  
            animate: true,                      
        });
        
        this.fileName = Ext.create('Ext.toolbar.TextItem', {
            text: '<h4><em>Name: </em>"'+(this.file.name || this.file.fileName)+'"</h4>',
            indent: true,
        });        

        this.fileSize = Ext.create('Ext.toolbar.TextItem', {
            text: '<h4><em>Size: </em>' + formatFileSize(this.file.size || this.file.fileSize)+
                  ' <em>Type: </em>'+this.file.type+'</h4>',
            indent: true,
        });            

        /*
        this.closeButton = Ext.create('Ext.button.Button', {
            text:'Close',
            //anchor: '-50',
            scale: 'large',
            //width: 32, height: 32,
            handler: function() {
                alert('You clicked the button!')
            }                       
        });*/
        
        this.items = [ 
            //this.closeButton,
            this.fileName,
            this.fileSize,
            this.progress ];           
        
        // try to update the mime type from what browser gives
        // all browsers on different systems give all kinds of things
        // try to safeguard this issue using the extension
        var file_type = this.file.type;
        var ext = this.file.name.split('.').reverse()[0];
        if (ext in mymime)
            file_type = mymime[ext];

        this.annotator = undefined;
        if (file_type in annotators) {
            this.state = BQ.upload.Item.STATES.ANNOTATING;
            this.progress.setVisible(false);
            this.fileName.setVisible(false);
            this.fileSize.setVisible(false);
            this.annotator = Ext.create(annotators[file_type], {
                file: this.file,
                listeners: {
                    done: this.onAnnotated,
                    scope: this,
                },  
            });
            this.height = this.annotator.height;            
            this.items.push(this.annotator);             
        }
        
        this.callParent();
    },
    
    updateUi : function() {
        if (!this.progress) return;
        this.progress.updateText( BQ.upload.Item.STATE_STRINGS[this.state] );
        if (this.state<BQ.upload.Item.STATES.DONE) {
            this.progress.removeCls( 'error' );
            this.progress.removeCls( 'done' );            
        } else
        if (this.state==BQ.upload.Item.STATES.DONE) {
            this.progress.removeCls( 'error' );
            this.progress.addCls( 'done' );    
        } else
        if (this.state>BQ.upload.Item.STATES.DONE) {
            this.progress.addCls( 'error' );
            this.progress.removeCls( 'done' );
        }             
    },   

    onDestroy : function() {
        this.cancel(true);
        this.callParent();
    },   

    hasFile : function(f) {
        return (this.file.name || this.file.fileName) === (f.name || f.fileName);
    },  

    getFile : function() {
        return this.file;
    },  
   
    setFile : function(f) {
        this.file = f;
    },   

    getState : function() {
        return this.state;
    }, 
   
    upload : function() {
        if (this.state >= BQ.upload.Item.STATES.UPLOADING) return;          
        this.time_starting = new Date();
        this.state = BQ.upload.Item.STATES.UPLOADING;
        this.constructAnnotation();
        this.fup = new BQFileUpload(this.file, {
            uploadProgress: Ext.Function.bind( this.onProgress, this ),
            uploadComplete: Ext.Function.bind( this.onComplete, this ),
            uploadFailed:   Ext.Function.bind( this.onFailed, this ),
            uploadCanceled: Ext.Function.bind( this.onCanceled, this ),
            formconf: this.formconf,
            tags: this.annotations ? this.annotations.toXML(): undefined,
        });
        this.fup.upload(); 
        this.updateUi();        
    },      

    cancel : function(noui) {
        if (this.state >= BQ.upload.Item.STATES.DONE) return;  
        this.state = BQ.upload.Item.STATES.CANCELED;
        //BQ.ui.notification('Cancel'); 
        if (this.fup) {
            this.fup.cancel();
            this.fireEvent( 'filecanceled', this); 
        }
        if (noui) return;  
        this.updateUi();
    },   

    onProgress : function(e) {
        this.updateUi(); 
        var elapsed = (new Date() - this.time_starting)/1000;
        this.progress.updateProgress( e.loaded/e.total, 'Uploading at ' + formatFileSize(e.loaded/elapsed) +'/s' );
        if (e.loaded==e.total) this.time_finished_upload = new Date();           
    }, 

    onComplete : function(e) {
        this.progress.updateProgress( 1.0 );
        this.state = BQ.upload.Item.STATES.ERROR;
        this.time_finished = new Date();
        if (!this.time_finished_upload) this.time_finished_upload = this.time_finished;

        var elapsed = (this.time_finished_upload - this.time_starting)/1000;
        var speed = formatFileSize(this.file.size/elapsed)+'/s';
        var timing = ' in '+ this.time_finished.diff(this.time_starting).toString() +
                     ' at '+ speed;      
                   
        this.fileName.setText( '<h4>Uploaded <b>'+this.file.name+'</b>'+timing+'</h4>' );                
        this.fileSize.setText( '<h4>Unfortunately some error happened during upload...</h4>' );                    
                 
        // parse response
        if (e && e.target && e.target.responseXML) {
            this.resource = BQFactory.createFromXml(e.target.responseXML.firstChild.firstChild);

            if (this.resource.uri) {
                // image inserted correctly
                this.state = BQ.upload.Item.STATES.DONE;                
                var s = '<h4>Uploaded <a href="'+view_resource+encodeURIComponent(this.resource.uri)+'">'+this.file.name+'</a>'+timing+'</h4>'
                this.fileName.setText(s);

                var s = '<h4>'+ render_resource(this.resource) +'</h4>';
                this.fileSize.setText(s);
            } else {
                // some error happened
                var d = this.resource.toDict();       
                var error = Encoder.htmlEncode(d.error);
                this.fileSize.setText( '<h4>Unfortunately this error happened while processing: <b>'+error+'</b></h4>' );                  
            }
        } // if response came
        
        this.updateUi();          
        this.fireEvent( 'fileuploaded', this);        
    }, 
    
    onFailed : function(e) {
        this.state = BQ.upload.Item.STATES.ERROR;         
        this.updateUi(); 
        this.fireEvent( 'fileerror', this);         
    }, 
    
    onCanceled : function(e) {
        this.state = BQ.upload.Item.STATES.CANCELED;          
        this.updateUi();  
        this.fireEvent( 'filecanceled', this);                
    },      

    constructAnnotation: function() {
        var resource = new BQResource();
        resource.type = 'file';
        resource.uri  = this.file.name;
        resource.name = this.file.name; 

        if (this.tagger) {
            //resource.tags = this.tagger.getTagDocument();
            resource.addtags( this.tagger.getTagDocument(), true );
        }
        
        if (this.annotation_dict) {
            var d = this.annotation_dict;
            ingest = resource.addtag ({name: 'ingest'});
            for (var k in d) 
                ingest.addtag({ name: k, value: d[k] });
        }
        this.annotations = resource;
    },     

    onAnnotated : function(ann) {
        this.state = BQ.upload.Item.STATES.READY;
        this.annotator.destroy();
        this.setHeight( this.height_normal );        
        this.progress.setVisible(true);
        this.fileName.setVisible(true);
        this.fileSize.setVisible(true);
        this.annotation_dict = ann;
    },     
          
});

BQ.upload.Item.STATES = {
    'ANNOTATING': 0,
    'READY'     : 1,
    'UPLOADING' : 2,
    'DONE'      : 3,
    'CANCELED'  : 4,
    'ERROR'     : 5,        
};

BQ.upload.Item.STATE_STRINGS = {
    0: 'Needs annotations',
    1: 'Ready',
    2: 'Uploading',
    3: 'Done',
    4: 'Canceled',
    5: 'Error',
};

//--------------------------------------------------------------------------------------
// BQ.upload.Panel
// upload manages items and all other UI aspects like drag and drop
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.upload.Panel', {
    alias: 'widget.upload',    
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    border: 0,
    autoScroll: true,
    layout: 'fit',            

    defaults: { 
        border: 0, 
        heading: 'File upload',
        maxFiles: 0, // use 1 for single file
        maxFileSize: 0, // maximum file size in bytes, 0 no limit
        //allowedFileTypes: undefined, // currently not supported, ex: { mime: ['image/tiff', 'image/jpeg'], exts: ['pptx', 'zip'] }
        //limitConcurrentUploads: undefined, // currently not supported, use 1 for sequential uploads
    },

    constructor: function(config) {
        this.addEvents({
            'fileuploaded'   : true,
            'filesuploaded'  : true,
            'datasetcreated' : true,            
            'filecanceled'   : true,
            'filescanceled'  : true,
            'fileadded'      : true,
            'fileerror'      : true,            
        });
        this.callParent(arguments);
        return this;
    },

    initComponent : function() {
        
        // header toolbar's elements

        this.fileChooser = Ext.create('Ext.form.field.File', {
            buttonOnly: true, 
            handler: this.chooseFiles,
            buttonConfig: { scale: 'large', iconCls: 'browse', text: 'Choose files', tooltip: 'Select several local files to upload', },
            listeners: {
                    change: this.chooseFiles,
                    scope: this,
            }            
        });        
        
        // footer's toolbar elements

        this.progress = Ext.create('Ext.ProgressBar', {
            text:'Uploading',
            flex: 1,
            height: 30,
            style: 'margin-left: 30px; margin-right: 30px;',
            animate: true,
            value: 0,
        });
        this.progress.setVisible(false);
        
        this.btn_upload = Ext.create('Ext.button.Button', {
            text: 'Upload', 
            disabled: true,
            iconCls: 'upload', 
            scale: 'large', 
            cls: 'x-btn-default-large',
            tooltip: 'Start the upload of all queued files',
            handler: Ext.Function.bind( this.upload, this ),
        });
        this.btn_cancel = Ext.create('Ext.button.Button', {
            text: 'Cancel', 
            disabled: true,            
            iconCls: 'cancel', 
            scale: 'large', 
            cls: 'x-btn-default-large',            
            tooltip: 'Cancel all queued and uploading files',            
            handler: Ext.Function.bind( this.cancel, this ),
        });
        this.btn_dataset = Ext.create('Ext.button.Button', {
            text: 'Create a dataset', 
            //iconCls: 'cancel', 
            scale: 'large', 
            enableToggle: true,
            pressed: false,
            cls: 'x-btn-default-large', 
            tooltip: 'Wrap all uploaded images into a dataset, if selected all images will be added into a dataset after upload',   
            
            handler: function(){ 
                if (this.pressed)
                    BQ.ui.notification('All images will be wraped in a dataset', 1000);
                else 
                    BQ.ui.notification('Dataset will not be created', 1000);                    
            },
        });

        // main elements

        this.formatsPanel = Ext.create('BQ.is.Formats', {
            border: 0, 
            title: 'Supported image formats', 
            bodyStyle: 'padding: 0px',
        });

        this.helpPanel = Ext.create('Ext.panel.Panel', {
            border: 0, 
            title: 'Help on compressed files', 
            bodyStyle: 'padding: 10px',
            loader: { url: '/import_service/public/help.html', renderer: 'html', autoLoad: true },
        });

        this.taggerPanel = Ext.create('Bisque.ResourceTaggerOffline', { });
        this.taggerPrent = Ext.create('Ext.panel.Panel', {
            border: 0, 
            title: 'Textual annotations', 
            layout: 'fit',   
            items: [this.taggerPanel],         
        });
        
        this.tabPanel = Ext.create('Ext.panel.Panel', {
            border: 0, 
            region:'east',                
            collapsible: true,
            width: 350,
            cls: 'tabs',            
            layout: 'accordion',
            items: [ this.formatsPanel, this.helpPanel, this.taggerPrent ],            
        }); 


        this.uploadPanel = Ext.create('Ext.container.Container', {
            border: 0, 
            region:'center',                
            autoScroll: true,
            cls: 'upload',
            //bodyStyle: 'padding:10px', 
            //defaults: { bodyStyle: 'margin: 15px' },            
        });      


        //--------------------------------------------------------------------------------------
        // toolbars
        //-------------------------------------------------------------------------------------- 

        this.dockedItems = [{
            xtype: 'toolbar',
            dock: 'top',
            defaults: { scale: 'large',  },
            allowBlank: false,
            cls: 'tools', 
            items: [ { xtype:'tbtext', html: '<h1>'+this.heading+':</h1>', },
                     this.fileChooser, {
                         text: 'Annotate', 
                         iconCls: 'annotate', 
                         cls: 'x-btn-default-large', 
                         tooltip: 'Show annotation tagger',            
                         handler: function() { this.taggerPrent.expand(); },
                         scope: this,
                     },{
                         text: 'Formats', 
                         iconCls: 'formats', 
                         cls: 'x-btn-default-large', 
                         tooltip: 'Show supported formats',            
                         handler: function() { this.formatsPanel.expand(); },
                         scope: this,
                     },{
                         text: 'Help', 
                         iconCls: 'help', 
                         cls: 'x-btn-default-large', 
                         tooltip: 'Show help page about file uploading',            
                         handler: function() { this.helpPanel.expand(); },
                         scope: this,
                     },
                   ]
        },{
            xtype: 'toolbar',
            dock: 'bottom',
            //ui: 'footer',
            cls: 'footer',   
            defaults: { scale: 'large', cls: 'x-btn-default-large', },  
            items: [ this.btn_dataset, this.btn_upload, this.btn_cancel, this.progress, ]            
        }];    
       
        //--------------------------------------------------------------------------------------
        // items
        //-------------------------------------------------------------------------------------- 
        this.items = [{
            xtype: 'panel',
            border: 0,
            layout: 'border',
            defaults: { split: true, },
            items: [ 
                this.uploadPanel,
                this.tabPanel,
            ],                
        }];        
        
        this.callParent();
    },
   
    afterRender : function() {
        this.callParent();

        // make sure input is a multi file select
        var e = this.fileChooser.fileInputEl;
        if (e && e.dom)
            e.dom.multiple = true;
        
        // accept file drag and drop
        var el = this.getEl();
        if (el) {
            el.on( 'dragover', this.onDragOver, this );
            el.on( 'dragleave', this.onDragLeave, this );
            el.on( 'drop', this.onDrop, this );
        }
    },   

    onDestroy : function() {
        this.cancel();
        this.callParent();        
    },   
   
    chooseFiles : function(field, value, opts) {
        var files = field.fileInputEl.dom.files;
        for (var i=0, f; f=files[i]; i++)
            this.addFile(f);
    },   

    checkFile : function(f) {
        // first check if the file is already included       
        var found = false;
        for (var i=0; i<this.uploadPanel.items.getCount(); i++) {
            var item = this.uploadPanel.items.getAt(i);
            if (item && item.hasFile)
                found = item.hasFile(f);
            if (found) break;
        }
        return found;
    },   

    addFile : function(f) {
        // first check if the file is already included       
        if (this.checkFile(f)) {
            BQ.ui.notification('File already in the upload queue: '+f.name);
            return;
        }
        
        if (this.maxFileSize && this.maxFileSize>0 && this.maxFileSize > f.size) {
            BQ.ui.notification('File is too large: '+f.name);
            return;
        }        
        
        if (this.maxFiles && this.maxFiles>0 && this.maxFiles >= this.uploadPanel.items.getCount()) {
            BQ.ui.notification('Maximum size of file queue reached...');
            return;
        }        
        
        //allowedFileTypes: undefined, // currently not supported, ex: { mime: ['image/tiff', 'image/jpeg'], exts: ['pptx', 'zip'] }                
         
        var fp = Ext.create('BQ.upload.Item', {
            file: f, 
            formconf: this.formconf,
            tagger: this.taggerPanel,
            listeners: {
                    fileuploaded: this.onFileUploaded,
                    filecanceled: this.onFileCanceled,
                    fileerror: this.onFileError,
                    scope: this,
            },     
        });        
        this.uploadPanel.add(fp);
        
        this.btn_upload.setDisabled(false);
        this.btn_cancel.setDisabled(false);        
        this.fireEvent( 'fileadded', fp);         
    },   
   
    upload : function() {
        this.all_done = false;        
        this.files_uploaded = 0;
        this.progress.setVisible(true);
        this.progress.updateProgress(0);
        this.uploadPanel.items.each( function() { if (this.upload) this.upload(); } );
    },     

    cancel : function() {
        this.uploadPanel.items.each( function() { if (this.cancel) this.cancel(); } );
        this.testDone(true);        
        /*   
        for (var i=0; i<this.uploadPanel.items.getCount(); i++) {
            var item = this.uploadPanel.items.getAt(i);
            if (item && item.cancel)
                item.cancel();
        }*/
        this.fireEvent( 'filescanceled', this); 
    },     

    blockPropagation: function (e) {
        if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
        else e.cancelBubble = true;                 // IE    
        if (e.preventDefault) e.preventDefault();   // prevent image dragging
        else e.returnValue=false;    
    },

    onDragOver : function(e) {
        e = e ? e : window.event;
        this.blockPropagation(e);
        this.uploadPanel.addCls( 'dragging' );
    },     

    onDragLeave : function(e) {
        e = e ? e : window.event;
        this.blockPropagation(e);
        this.uploadPanel.removeCls( 'dragging' );
    },

    onDrop : function(e) {
        e = e ? e : window.event;
        this.blockPropagation(e);
        this.uploadPanel.removeCls( 'dragging' );        
        if (!e || !e.browserEvent || !e.browserEvent.dataTransfer || !e.browserEvent.dataTransfer.files) return;
        var files = e.browserEvent.dataTransfer.files;
        for (var i=0, f; f=files[i]; i++)
            this.addFile(f);
    },

    testDone : function(nomessage) {
        var total = this.uploadPanel.items.getCount();
        this.progress.updateProgress( this.files_uploaded/total );
        
        var e = this.uploadPanel.items.findBy( function(){ return (this.getState && this.getState()<BQ.upload.Item.STATES.DONE); } );
        if (!e && this.files_uploaded==total && !this.all_done) {
            this.all_done = true;
            if (!nomessage) BQ.ui.notification('All files uploaded!');
            this.progress.setVisible(false);                    
            this.btn_upload.setDisabled(true);
            this.btn_cancel.setDisabled(true); 
            if (this.btn_dataset.pressed) this.wrapDataset();
            this.fireEvent( 'filesuploaded', this);   
        } else {
            this.btn_upload.setDisabled(false);
            this.btn_cancel.setDisabled(false);
        }
    },
    
    onFileUploaded : function(fu) {
        this.files_uploaded++;        
        this.fireEvent( 'fileuploaded', fu);
        this.testDone();
    },
    
    onFileCanceled : function(fu) {
        this.files_uploaded++;        
        this.fireEvent( 'filecanceled', fu);        
        this.testDone();
    },
    
    onFileError : function(fu) {
        this.files_uploaded++;        
        this.fireEvent( 'fileerror', fu);        
        this.testDone();
    },        

    wrapDataset : function() {
        var members = [];
        this.uploadPanel.items.each( function() { 
            if (this.resource && this.resource.uri && this.resource.resource_type=='image') {
                members.push( new Value( "object", this.resource.uri ) );
            }
        });
        
        var dataset = new BQDataset();
        dataset.name = 'Uploaded on '+(new Date()).toISOString();
        dataset.setMembers( members );
        dataset.save_('/data_service/datasets/', callback(this, 'onCreatedDataset'));        
    },   
    
    onCreatedDataset : function(dataset) {
        BQ.ui.notification('Dataset created with the name: "'+dataset.name+'"', 10000);
        this.fireEvent( 'datasetcreated', dataset);
    },        
       
});

//--------------------------------------------------------------------------------------
// BQ.upload.Dialog
// Instantiates upload panel in a modal window
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.upload.Dialog', {
	extend : 'Ext.window.Window',
	
    constructor : function(config) {
        config = config || {};
        config.height = config.height || '85%';
        config.width = config.width || '85%';
        
        /*
        var bodySz=Ext.getBody().getViewSize();
        var width = config.width;        
        var height=parseInt((config.height.indexOf("%")==-1)?config.height:(bodySz.height*parseInt(config.height)/100));
        var width = config.width;
        if (typeof config.width === 'string')
            width=parseInt((config.width.indexOf("%")==-1)?config.width:(bodySz.width*parseInt(config.width)/100));
        */

        Ext.apply(this, {
            layout : 'fit',
            title : 'Image upload',
            modal : true,
            border : false,
            //height : height,
            //width : width,
            items : new Bisque.ResourceBrowser.Browser(config),
        }, config);

        this.callParent([arguments]);

        // Relay all the custom ResourceBrowser events to this Window
        //this.relayEvents(this.getComponent(0), ['Select']);
        
        //this.getComponent(0).on('Select', function(resourceBrowser, resource) {
        //    this.destroy();
        //}, this);
        
        this.show();
    }
});

