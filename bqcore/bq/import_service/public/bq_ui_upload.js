/*******************************************************************************

  BQ.upload.Panel  - an integrated uploading tool allowing many file uploads
  BQ.upload.Dialog - uploader in the modal window

  Author: Dima Fedorov

------------------------------------------------------------------------------
  BQ.upload.Dialog:
------------------------------------------------------------------------------
  
  Sends multi-part form with a file and associated tags in XML format
  form parts should be something like this: file and file_tags

    The tag XML document is in the following form:
    <resource>
        <tag name='any tag' value='any value' />
        <tag name='another' value='new value' />
    </resource>


    The document can also contain special tag for prosessing and additional info:
    <resource>
        <tag name='any tag' value='any value' />
        <tag name='ingest'>
            
            Permission setting for imported image as: 'private' or 'published'
            <tag name='permission' value='private' />
            or
            <tag name='permission' value='published' />
                    
            Image is a multi-file compressed archive, should be uncompressed and images ingested individually:
            <tag name='type' value='zip-multi-file' />
            or
            Image is a compressed archive containing multiple files composing a time-series image:        
            <tag name='type' value='zip-time-series' />
            or
            Image is a compressed archive containing multiple files composing a z-stack image:                
            <tag name='type' value='zip-z-stack' />
            or
            Image is a compressed archive containing multiple files composing a 5-D image:
            <tag name='type' value='zip-5d-image' />
            This tag must have two additional tags with numbers of T and Z planes:
            <tag name='number_z' value='XXXX' />
            <tag name='number_t' value='XXXXX' />                
    
        </tag>
    </resource>
    
    Example for a file "example.zip":
    
    <resource>
        <tag name='any tag' value='any value' />
        <tag name='ingest'>
            <tag name='permission' value='published' />
            <tag name='type' value='zip-5d-image' />
            <tag name='number_z' value='XXXX' />
            <tag name='number_t' value='XXXXX' />
        </tag>
    </resource>

------------------------------------------------------------------------------

  
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

function renderer_resource(r) {
    return 'Created a resource of type <b>'+r.resource_type+'</b>';
}

function renderer_image(r) {
    var s = '';
    s += 'Created an <b>image</b> with geometry: ';
    if (r.x) s += 'x: '+r.x+' ';
    if (r.y) s += 'y: '+r.y+' ';
    if (r.z) s += 'z: '+r.z+' ';
    if (r.t) s += 't: '+r.t+' ';
    if (r.ch) s += 'ch: '+r.ch+' ';                                                
    return s;    
}

function renderer_dataset(r) {
    var m = r.getMembers();
    return 'Created a <b>dataset</b> with '+ m.values.length +' images';
}

var resource_renderers = { 'image': renderer_image, 'dataset': renderer_dataset };

function render_resource(r) {
    var f = renderer_resource;
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
    //extend: 'Ext.panel.Panel',
    extend: 'Ext.container.Container', // container is much faster to be insterted
    alias: 'widget.uploaditem',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    border: 0,
    height: 110,
    closable: true,
    cls: 'uploaditem',
    bodyStyle: 'padding: 10px',
    //autoScroll: true,
    layout: 'anchor',  
    //bodyStyle: 'margin: 15px',
    defaults: { border: 0, height_normal: 120, hysteresis: 100, }, // hysteresis in ms
            
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
            text: (this.file.name || this.file.fileName),
            cls: 'title',
            indent: true,
        });        

        var s = '<h4><em>Size: </em>' + formatFileSize(this.file.size || this.file.fileSize);
        s += this.file.type == ''? '': ' <em>Type: </em>'+this.file.type;
        s += '</h4>';
        this.fileSize = Ext.create('Ext.toolbar.TextItem', {
            text: s,
            indent: true,
        });            
        
        this.closeButton = Ext.create('Ext.button.Button', {
            iconCls: 'close', 
            cls: 'flatbutton button-close',
            scale: 'small',
            tooltip: 'Cancel uploading this file',          
            handler: Ext.Function.bind( this.destroy, this ),
        });

        this.permissionButton = Ext.create('Ext.button.Button', {
            cls: 'flatbutton button-permission',
            text: BQ.upload.Item.PERMISSIONS_STRINGS[BQ.upload.Item.PERMISSIONS.PRIVATE],
            scale: 'small',
            tooltip: 'Change file access permission',          
            handler: Ext.Function.bind( this.togglePermission, this ),
        });
        
        this.items = [ 
            this.closeButton,
            this.permissionButton,
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

    setState : function(state) {
        this.state = state;
        this.updateUi();
    }, 
  
    togglePermission : function() {
        if (this.permission)
            this.setPermission( BQ.upload.Item.PERMISSIONS.PRIVATE );
        else
            this.setPermission( BQ.upload.Item.PERMISSIONS.PUBLISHED );
    },      
   
    setPermission : function(new_perm) {
        if (this.state >= BQ.upload.Item.STATES.UPLOADING) return;
        this.permission = new_perm;
        if (this.permission)
            this.permissionButton.addCls('published'); 
        else
            this.permissionButton.removeCls('published');                       
        this.permissionButton.setText(BQ.upload.Item.PERMISSIONS_STRINGS[this.permission]);  
    },      
   
    upload : function() {
        if (this.state >= BQ.upload.Item.STATES.UPLOADING) return;          
        //this.time_started = new Date();
        this.state = BQ.upload.Item.STATES.UPLOADING;
        this.constructAnnotation();
        this.fup = new BQFileUpload(this.file, {
            uploadComplete: Ext.Function.bind( this.onComplete, this ),
            uploadFailed:   Ext.Function.bind( this.onFailed, this ),
            uploadCanceled: Ext.Function.bind( this.onCanceled, this ),
            uploadTransferProgress: Ext.Function.bind( this.onProgress, this ),
            uploadTransferStart:    Ext.Function.bind( this.onTransferStart, this ),
            uploadTransferEnd:      Ext.Function.bind( this.onTransferEnd, this ),                                    
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

    onTransferStart : function(e) {
        //BQ.ui.notification('Started');
        this.time_started = new Date();
    }, 

    onTransferEnd : function(e) {
        //BQ.ui.notification('ended');
        this.time_finished_upload = new Date();
        this.state = BQ.upload.Item.STATES.INGESTING;
        this.progress.updateProgress( 1.0 );
        this.updateUi();         
    }, 

    doProgress : function() {
        this.progress_timeout = null; clearTimeout (this.progress_timeout);
        var e = this._progress_event;
        if (this.state != BQ.upload.Item.STATES.UPLOADING) return;
        this.updateUi(); 
        var elapsed = (new Date() - this.time_started)/1000;
        this.progress.updateProgress( e.loaded/e.total, 'Uploading at ' + formatFileSize(e.loaded/elapsed) +'/s' );
    }, 

    onProgress : function(e) {
        this._progress_event = e;
        if (this.progress_timeout) return;
        this.progress_timeout = setTimeout( Ext.Function.bind( this.doProgress, this ), this.hysteresis );
    }, 

    onComplete : function(e) {
        this.progress.updateProgress( 1.0 );
        this.state = BQ.upload.Item.STATES.ERROR;
        this.time_finished = new Date();
        if (!this.time_finished_upload) 
            this.time_finished_upload = this.time_finished;

        var elapsed = (this.time_finished_upload - this.time_started)/1000;
        var speed = formatFileSize(this.file.size/elapsed)+'/s';
        var timing = ' in '+ this.time_finished.diff(this.time_started).toString() +
                     ' at '+ speed;      
                   
        this.fileName.setText( 'Uploaded <b>'+this.file.name+'</b>'+timing );                
        this.fileSize.setText( '<h4>Unfortunately some error happened during upload...</h4>' );                    
                 
        // parse response
        if (e && e.target && e.target.responseXML) {
            this.resource = BQFactory.createFromXml(e.target.responseXML.firstChild.firstChild);

            if (this.resource.uri) {
                // image inserted correctly
                this.state = BQ.upload.Item.STATES.DONE;                
                var s = 'Uploaded <a href="'+view_resource+encodeURIComponent(this.resource.uri)+'">'+this.file.name+'</a>'+timing;
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
        
        // add access permission annotation
        if (this.permission) {
            if (!this.annotation_dict) 
                this.annotation_dict = {};
            this.annotation_dict['permission'] = BQ.upload.Item.PERMISSIONS_STRINGS[this.permission];
        }

        // add tagger annotations
        if (this.tagger) {
            //resource.tags = this.tagger.getTagDocument();
            resource.addtags( this.tagger.getTagDocument(), true );
        }
        
        // create the ingest tag
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
    'INGESTING' : 3,    
    'DONE'      : 4,
    'CANCELED'  : 5,
    'ERROR'     : 6,        
};

BQ.upload.Item.STATE_STRINGS = {
    0: 'Needs annotations',
    1: 'Ready',
    2: 'Uploading',
    3: 'Ingesting',    
    4: 'Done',
    5: 'Canceled',
    6: 'Error',
};

BQ.upload.Item.PERMISSIONS = {
    'PRIVATE': 0,
    'PUBLISHED': 1,
};

BQ.upload.Item.PERMISSIONS_STRINGS = {
    0: 'private',
    1: 'published',
};


//--------------------------------------------------------------------------------------
// BQ.upload.Panel
// upload manages items and all other UI aspects like drag and drop
//-------------------------------------------------------------------------------------- 

BQ.upload.UPLOAD_STRING = 'Uploading';

BQ.upload.DATASET_CONFIGS = {
    'NORMAL'   : 0,
    'REQUIRE'  : 1,
    'PROHIBIT' : 2,
};

BQ.upload.DEFAULTS = {
    heading: 'File upload',
    maxFiles: 0, // use 1 for single file
    maxFileSize: 0, // maximum file size in bytes, 0 no limit
    //allowedFileTypes: undefined, // currently not supported, ex: { mime: ['image/tiff', 'image/jpeg'], exts: ['pptx', 'zip'] }
    //limitConcurrentUploads: undefined, // currently not supported, use 1 for sequential uploads
    dataset_configs: BQ.upload.DATASET_CONFIGS.NORMAL,
    hysteresis: 500,  
};

Ext.define('BQ.upload.Panel', {
    alias: 'widget.upload',    
    extend: 'Ext.panel.Panel',
    requires: ['Ext.toolbar.Toolbar', 'Ext.tip.QuickTipManager', 'Ext.tip.QuickTip'],

    border: 0,
    autoScroll: true,
    layout: 'fit',            
    defaults: BQ.upload.DEFAULTS,

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

    processConfig: function() {
        if (this.maxFiles == 1)
            this.dataset_configs = BQ.upload.DATASET_CONFIGS.PROHIBIT;
    },

    initComponent : function() {
        
        this.processConfig();
        
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
            text: BQ.upload.UPLOAD_STRING,
            flex: 1,
            height: 30,
            style: 'margin-left: 30px; margin-right: 30px;',
            animate: false,
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
        
        var dataset_btn_visible = true;
        var dataset_btn_preseed = false;
        if (this.dataset_configs > BQ.upload.DATASET_CONFIGS.NORMAL)
            dataset_btn_visible = false;
        if (this.dataset_configs == BQ.upload.DATASET_CONFIGS.REQUIRE)
            dataset_btn_preseed = true;               
        
        this.btn_dataset = Ext.create('Ext.button.Button', {
            text: 'Create a dataset', 
            //iconCls: 'cancel', 
            scale: 'large', 
            enableToggle: true,
            pressed: dataset_btn_preseed,
            hidden: !dataset_btn_visible,
            cls: 'x-btn-default-large', 
            tooltip: 'Wrap all uploaded images into a dataset, if selected all images will be added into a dataset after upload',   
            
            handler: function(){ 
                if (this.pressed)
                    BQ.ui.notification('All images will be wraped in a dataset', 1000);
                else 
                    BQ.ui.notification('Dataset will not be created', 1000);                    
            },
        });
        
        this.btn_reupload = Ext.create('Ext.button.Button', {
            text: 'Re-upload failed', 
            //disabled: true,   
            hidden: true,         
            iconCls: 'upload', 
            scale: 'large', 
            cls: 'x-btn-default-large',            
            tooltip: 'Re-upload all failed files',            
            handler: Ext.Function.bind( this.reupload, this ),
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
            autoScroll: true,
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
            defaults: { scale: 'large'  },
            allowBlank: false,
            cls: 'tools', 
            layout: {
                overflowHandler: 'Menu'
            },            
            items: [{ xtype:'tbtext', html: '<h1>'+this.heading+':</h1>', },
                     this.fileChooser, 
                     {
                         xtype:'splitbutton',
                         text: 'Toggle permissions',
                         cls: 'x-btn-default-large', 
                         tooltip: 'Toggle access right to all images, only works before the upload have started',                                                   
                         //iconCls: 'add16',
                         scope: this,
                         handler: function() { this.setPermissionsToggle(); },
                         menu: [{ 
                                   text: 'Set all published', 
                                   scope: this, 
                                   handler: function() { this.setPermissions(BQ.upload.Item.PERMISSIONS.PUBLISHED); },  
                                }, {
                                   text: 'Set all private',   
                                   scope: this, 
                                   handler: function() { this.setPermissions(BQ.upload.Item.PERMISSIONS.PRIVATE); },  
                                },]
                     }, { 
                        xtype: 'tbfill',
                     }, {
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
            items: [ this.btn_dataset, this.btn_upload, this.btn_cancel, this.btn_reupload, this.progress, ]            
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
        this.cancel(true);
        this.callParent();        
    },   
   
    chooseFiles : function(field, value, opts) {
        var files = field.fileInputEl.dom.files;
        this.addFiles(files);
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

    // private at this point, noui - should be true if you don't want file to be added to the list right here
    addFile : function(f, noui) {
        // first check if the file is already included       
        if (this.checkFile(f)) {
            BQ.ui.notification('File already in the upload queue: '+f.name);
            return;
        }
        
        if (this.maxFileSize && this.maxFileSize>0 && this.maxFileSize > f.size) {
            BQ.ui.notification('File is too large: '+f.name);
            return;
        }        
        
        if (this.maxFiles && this.maxFiles>0 && this.maxFiles <= this.uploadPanel.items.getCount()) {
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

        if (!noui) {
            this.uploadPanel.add(fp);
            this.btn_upload.setDisabled(false);
            this.btn_cancel.setDisabled(false);        
        }
        this.fireEvent( 'fileadded', fp);          
        return fp;
    },   

    doProgress : function() {
        this.progress_timeout = null; clearTimeout (this.progress_timeout);
        var e = this._progress_event;
        this.progress.updateProgress( e.pos, e.message );
    }, 

    updateProgress : function(pos, message) {
        this._progress_event = {pos: pos, message: message};
        if (this.progress_timeout) return;
        this.progress_timeout = setTimeout( Ext.Function.bind( this.doProgress, this ), this.hysteresis );
    }, 
   
    addFilesPrivate : function(pos) {
        var total = this._files.length;
        if (pos>=total) {
            this.uploadPanel.add(this._fps);
            this.uploadPanel.removeCls('waiting');

            //var time_finished = new Date();
            //this.progress.updateProgress(100, 'Inserted in '+time_finished.diff(this._time_started).toString() );
            this.progress.setVisible(false);            
            this.btn_upload.setDisabled(false);
            this.btn_cancel.setDisabled(false);  
            this._files = undefined;
            this._fps = undefined;            
            return;
        }
           
        var f = this._files[pos];
        var fp = this.addFile(f, true);
        if (fp) this._fps.push(fp);
        
        if (pos+1<total) {
            this.updateProgress( pos/total, 'Inserting files: '+(pos+1)+' of '+total );
        } else {
            clearTimeout (this.progress_timeout); this.progress_timeout = null;        
            this.progress.updateProgress( 1, 'Rendering inserted files, wait a bit...' );             
        }
        
        var me = this;
        setTimeout( function() { me.addFilesPrivate(pos+1); }, 1);
    },
   
    addFiles : function(files) {
        this.progress.setVisible(true);        
        this._files = files;
        this._fps = [];
        this.uploadPanel.addCls('waiting');
        this._time_started = new Date(); 
        this.addFilesPrivate(0);
    }, 
   
    upload : function() {
        this.all_done = false;        
        this.files_uploaded = 0;
        this._time_started = new Date();  
        this.progress.setVisible(true);
        this.progress.updateProgress(0, BQ.upload.UPLOAD_STRING);
        this.uploadPanel.items.each( function() { if (this.upload) this.upload(); } );
    },     

    cancel : function(ondestroy) {
        this.uploadPanel.items.each( function() { if (this.cancel) this.cancel(); } );
        if (!ondestroy) {
            this.testDone(true);        
            this.fireEvent( 'filescanceled', this); 
        }
    },     
   
    setPermissionsToggle : function() {
        this.uploadPanel.items.each( function() { if (this.togglePermission) this.togglePermission(); } );
    },      
    
    setPermissions : function(new_perm) {
        this.uploadPanel.items.each( function() { if (this.setPermission) this.setPermission(new_perm); } );
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
        this.addFiles(files);            
    },

    testDone : function(nomessage) {
        var total = this.uploadPanel.items.getCount();
        this.progress.updateProgress( this.files_uploaded/total, 'Uploaded '+this.files_uploaded+'/'+total );
        
        var e = this.uploadPanel.items.findBy( function(){ return (this.getState && this.getState()<BQ.upload.Item.STATES.DONE); } );
        if (!e && this.files_uploaded==total && !this.all_done) {
            this.all_done = true;

            // first find out if some files had upload error
            var failed = this.testFailed();
            if (!nomessage) {
                var time_finished = new Date();
                var s = ''+(total-failed)+' files uploaded successfully in '+time_finished.diff(this._time_started).toString();
                if (failed>0) s += '<br>Although '+failed+' files have failed to upload.'
                BQ.ui.notification(s);
            }

            this.progress.setVisible(false);                    
            this.btn_upload.setDisabled(true);
            this.btn_cancel.setDisabled(true); 
            if (this.btn_dataset.pressed) 
                this.wrapDataset();

            // fire all files uploaded event
            var res = [];
            this.uploadPanel.items.each( function() { 
                if (this.resource && this.resource.uri)
                    res.push( this.resource );
            });                
            this.fireEvent( 'filesuploaded', res, this);
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
    
    isDatasetMode : function() {    
        return this.btn_dataset.pressed;      
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
    
    testFailed : function () {
        var failed=0;
        this.uploadPanel.items.each( function() { 
            if (this.state != BQ.upload.Item.STATES.DONE)
                failed++;
        });        
        if (failed>0)
            this.btn_reupload.setVisible(true);
        else
            this.btn_reupload.setVisible(false);                        
        return failed;
    }, 
       
    reupload : function () {
        this.uploadPanel.items.each( function() { 
            if (this.state == BQ.upload.Item.STATES.DONE) {
                this.destroy();
            } else
            if (this.state > BQ.upload.Item.STATES.DONE) {
                this.setState( BQ.upload.Item.STATES.READY );
            }
        });         
        this.btn_reupload.setVisible(false);        
        this.upload();
    }, 
});

//--------------------------------------------------------------------------------------
// BQ.upload.Dialog
// Instantiates upload panel in a modal window
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.upload.Dialog', {
    extend : 'Ext.window.Window',
    
    layout : 'fit',
    modal : true,
    border : false,
    width : '85%',
    height : '85%',
    
    constructor : function(config) {
        
        this.addEvents({
            'uploaded'   : true,
        });

        var uploader_config = { 
            border: 0, 
            flex:2, 
            heading: config.title || 'Image upload',
            formconf: { form_action: '/import/transfer', form_file: 'file', form_tags: 'file_tags' },
            listeners: {
                    filesuploaded: this.onFilesUploaded,
                    datasetcreated: this.onDatasetCreated,
                    scope: this,
            },               
        };

        // move the config options that belong to the uploader
        for (var c in config)
            if (c in BQ.upload.DEFAULTS)
                 uploader_config[c] = config[c];
    
        this.upload_panel = Ext.create('BQ.upload.Panel', uploader_config);         
        this.items = [this.upload_panel];
        config.title = undefined;
        
        this.callParent(arguments);
       
        this.show();
        return this;
    },

    onFilesUploaded : function(res, uploader) {
        if (this.upload_panel.isDatasetMode()) return;
        this.fireEvent( 'uploaded', res);
        this.destroy();
    },  
    
    onDatasetCreated : function(dataset) {
        this.fireEvent( 'uploaded', [dataset]);
        this.destroy();
    },     
    
});

