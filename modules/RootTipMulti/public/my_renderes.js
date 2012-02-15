/*******************************************************************************

  BQ.renderers.multiroot.Image

  Author: Dima Fedorov

  Version: 1
  
  History: 
    2011-09-29 13:57:30 - first creation
    
*******************************************************************************/


// overwrite standard renderer with our own
BQ.renderers.resources.image = 'BQ.renderers.multiroot.Image';

// provide our renderer
Ext.define('BQ.renderers.multiroot.Image', {
    extend: 'BQ.renderers.Image',

    onerror: function (e) {
        this.setLoading(false);
        BQ.ui.error(e.message);  
    }, 

    fetchRoots : function(f) {
        this.setLoading('Analysing outputs');

        var url = this.gobjects[0].uri;
        var xpath = '/gobject[@name]/gobject[@name]|/*/gobject[@name]/gobject[@name]';
        var xmap = 'gobject-name';
        var xreduce = 'vector';
    
        this.accessor = new BQStatisticsAccessor( url, xpath, xmap, xreduce, 
                                                  { 'ondone': callback(this, f), 
                                                    'onerror': callback(this, "onerror"), 
                                                    root: this.root, } );
    },
    
    doPlot : function() {
        this.setLoading(false);        
        if (!this.accessor || !this.accessor.results) {
            this.onerror('Plotting data was not fetched');
            return;   
        }
        var results = this.accessor.results;
        var xpath = [];
        var titles = [];  
        for (var i=0; i<results[0].vector.length; i++) {
            if (!results[0].vector[i] || results[0].vector[i]=='') continue;
            if (!results[0].vector[i].indexOf("tip-")==0) continue;
            xpath.push( '//gobject[@name="'+results[0].vector[i]+'"]//tag[@name="angle"]' );
            titles.push( results[0].vector[i] );
        }
        if (xpath.length<=0) {
            BQ.ui.error('Hm, no root tip objects found...');
            return;  
        }
        
        var url     = this.gobjects[0].uri;
        var xmap    = 'tag-value-number';
        var xreduce = 'vector';
        var title   = 'Tip angles';
        
        //var opts = { title: 'Tip angle (t)', height:500, titles: titles };
        this.plotter = Ext.create('BQ.stats.Dialog', {
            url     : url,
            xpath   : xpath,
            xmap    : xmap,
            xreduce : xreduce,
            title   : title,
            root    : this.root,
            opts    : { titles: titles, },
        });          
    },    

    getPlot : function() {
        if (this.accessor) 
            this.doPlot();
        else
            this.fetchRoots('doPlot');
    },

    createMenuPlot : function(menu) {
        menu.add({
            text: 'Plot tip angles',
            scope: this,
            handler: this.getPlot,
        }); 
    }, 
    
    doCSV : function() {
        this.setLoading(false);        
        if (!this.accessor || !this.accessor.results) {
            this.onerror('Export data was not fetched');
            return;   
        }
        var results = this.accessor.results;
        var xpath = [];
        for (var i=0; i<results[0].vector.length; i++) {
            if (!results[0].vector[i] || results[0].vector[i]=='') continue;
            if (!results[0].vector[i].indexOf("tip-")==0) continue;
            xpath.push( '//gobject[@name="'+results[0].vector[i]+'"]//tag[@name="angle"]' );
        }
        if (xpath.length<=0) {
            BQ.ui.error('Hm, no root tip objects found...');
            return;  
        }
        
        var xmap    = 'tag-value-number';
        var xreduce = 'vector';
        var url = '/stats/csv?url=' + this.gobjects[0].uri;
        if (this.root) url = this.root + url;        
        url += createArgs('xpath', xpath);
        url += createArgs('xmap', xmap);
        url += createArgs('xreduce', xreduce);                                        
        window.open(url);                
    },    

    getCSV : function() {
        if (this.accessor) 
            this.doCSV();
        else
            this.fetchRoots('doCSV');
    },

    createMenuExportCsv : function(menu) {
        menu.add({
            text: 'Tip angles as CSV',
            scope: this,
            handler: this.getCSV,
        }); 
    }, 

});


