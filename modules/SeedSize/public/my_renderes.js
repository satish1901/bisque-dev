/*******************************************************************************

  BQ.renderers.seedsize.Mex

  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/


// overwrite standard renderer with our own
BQ.renderers.resources.mex = 'BQ.renderers.seedsize.Mex';

// provide our renderer
Ext.define('BQ.renderers.seedsize.Mex', {
    extend: 'BQ.renderers.Mex',

    createMenuExportPackage : function(menu) {
        if (!this.res_uri_for_tools) return;
        if (!this.template_for_tools) return;
        var template = this.template_for_tools || {};
        if (!('export_package' in template) || template['export_package']==false) return; 
        menu.add({
            text: template['export_package/label'] || 'Area, Major and Minor axis as CSV files per image in a GZip package',
            scope: this,
            handler: this.fetchImageFileNames,
        }); 
    }, 

    fetchImageFileNames : function() {
        this.setLoading('Fetching image file names');
        if (!this.mex || !(this.res_uri_for_tools==this.mex.uri)) return;
        var mex = this.mex;
        
        this.image_names = {};
        var myiterable = mex.dict['execute_options/iterable'];
        this.images = Ext.clone(mex.iterables[myiterable]);
        delete this.images['dataset'];
        // fetch image names 
        this.num_requests = 0;
        for (var u in this.images) {
            var sub_mex = this.images[u];
            this.images[u] = { mex: sub_mex.uri, name: null, };
            this.num_requests++;
        }        
        for (var u in this.images) {
            BQFactory.request({ uri: u, 
                                 cb: callback(this, 'onImage'), 
                                 errorcb: callback(this, 'onerror'), 
                                 //uri_params: {view:'short'}, 
                             });            
        }
    },

    onerror: function (e) {
        BQ.ui.error(e.message);  
        this.num_requests--;
        if (e.request.request_url in this.images)
            delete this.images[e.request.request_url];
        if (this.num_requests<=0) this.onAllImages();
    }, 
    
    onImage: function(im) {
        this.num_requests--;        
        this.images[im.uri].name = im.name;
        if (this.num_requests<=0) this.onAllImages();
    },    
    
    onAllImages: function() {
        this.setLoading(false);

        var r = new BQResource();
        var vals = [];
        for (var i in this.images) {
            var u = '/stats/csv?url='+this.images[i].mex;
            u += '&xmap=tag-value-number';
            u += '&xreduce=vector';
            u += "&xpath=//gobject[@type='seed']/tag[@name='area']";
            u += "&xpath1=//gobject[@type='seed']/tag[@name='major']";
            u += "&xpath2=//gobject[@type='seed']/tag[@name='minor']";
            u += "&title=area";
            u += "&title1=major";
            u += "&title2=minor";
            u += "&filename="+this.images[i].name+'.csv';            
            vals.push(u);
        }
        r.setValues(vals);
    
        var payload = r.toXML();
        var url = '/export/initStream?compressionType=gzip';
    
        // dima: this might not work due to AJAX request
        /*
        BQFactory.request({ uri: url, 
                            method: 'post',
                            xmldata: payload,
                            //cb: callback(this, 'onImage'), 
                            //errorcb: callback(this, 'onerror'), 
                         });               
        */
        
        Ext.Ajax.timeout = 1200000; 
        Ext.Ajax.request({
           url: url,
           method: 'POST',
           jsonData: payload,
           scope: this,
           success: function (result, request) {
                Ext.DomHelper.append(document.body, {
                    tag: 'iframe',
                    frameBorder: 0,
                    width: 0,
                    height: 0,
                    src:result,
                    css: 'display:none;visibility:hidden;height:1px;'
                });
            }, //success
            failure: function (response, opts) {
                var msg = 'server-side failure with status code: ' + response.status + ' message: ' + response.statusText;
                BQ.ui.error(msg);  
            },
        });        
    },

});


