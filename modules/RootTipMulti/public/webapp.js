/*******************************************************************************

  multiroot webapp - a fully integrated interface for a module

  This algorithm takes user clicks as inputs and tracks the apex of an organ 
  and reports out the tip angle of the apex. Initially the tip is located with 
  a user click and is subsequently tracked using a corner detector in 
  combination with a nearest neighbor tracking approach.
  
*******************************************************************************/

function multiroot (args) {
    this.module_url = '/module_service/RootTipMulti'; 
    this.label_run = "Track root tips";  
    this.require_geometry = { z: 'single', t:'stack', fail_message: 'The image must be a 2D time series!' }; 
    this.require_gobjects = { gobject: 'point', amount: 'many', fail_message: 'You must select some root tips!' };     
    
    BQWebApp.call(this, args);
}
multiroot.prototype = new BQWebApp();
multiroot.prototype.constructor = multiroot;

multiroot.prototype.run = function () {
    if (this.require_gobjects && this.image_viewer)
        this.run_arguments.frame_number = 1;

    BQWebApp.prototype.run.call(this);
}

multiroot.prototype.createSumary = function () {
    /*
    var summary = '<ul>';
    summary += this.renderSummaryTag('summary/seedcount', 'Total seed count');
    summary += this.renderSummaryTag('summary/mean_area', 'Area mean');   
    summary += this.renderSummaryTag('summary/std_area', 'Area standard deviation');   
    summary += this.renderSummaryTag('summary/mean_majoraxis', 'Major axis mean'); 
    summary += this.renderSummaryTag('summary/std_majoraxis', 'Major axis standard deviation');    
    summary += this.renderSummaryTag('summary/mean_minoraxis', 'Minor axis mean');    
    summary += this.renderSummaryTag('summary/std_minoraxis', 'Minor axis standard deviation');                
    summary += this.renderSummaryTag('summary/mean_threshhold', 'Threshold mean');    
    summary += this.renderSummaryTag('summary/weighted_mean_cluster_1', 'Weighted mean cluster 1');
    summary += this.renderSummaryTag('summary/weighted_mean_cluster_2', 'Weighted mean cluster 2');
    summary += '</ul>';
    
    if (summary.length>0) summary = '<h3>Analysis summary:</h3>'+summary;
    return summary;
    */
    return '';
}

/*
multiroot.prototype.exportToCSV = function() {
    if (!this.gobjectURL) {
      BQ.ui.warning('No resulting graphical annotations found yet. Please, run the module first or change parameters.');    
      return; 
    }  
    
    var url = '/stats/csv?url=' + this.gobjectURL;
    url += '&xpath=' + escape("//tag[@name='area']");
    url += '&xpath1=' + escape("//tag[@name='major']");
    url += '&xpath2=' + escape("//tag[@name='minor']");
    url += '&xmap=tag-value-number&xreduce=vector';
            
    window.open(url);
}
*/

multiroot.prototype.plot = function() {
    var plotter_div = document.getElementById("webapp_results_plotter"); 
    
    if (plotter_div.style.display == 'none') {
      plotter_div.style.display = '';
      var url = this.gobjectURL;
      //var url = 'http://vidi.ece.ucsb.edu:8080/ds/images/886/gobjects';
      var xpath = '/gobject[@name]/gobject[@name]|/*/gobject[@name]/gobject[@name]';
      var xmap = 'gobject-name';
      var xreduce = 'vector';

      showHourGlass(plotter_div, 'Analysing outputs'); // show hour glass here  
      this.accessor = new BQStatisticsAccessor( url, xpath, xmap, xreduce, 
                                            { 'ondone': callback(this, "doPlot"), 'onerror': callback(this, "doPlotError") } );
    } else {
        plotter_div.style.display = 'none';      
        removeAllChildren(plotter_div);        
    }

}

multiroot.prototype.doPlot = function(results) {
    var plotter_div = document.getElementById("webapp_results_plotter");   
    removeAllChildren(plotter_div);  
    var xpath = [];
    var titles = [];  
    for (var i=0; i<results[0].vector.length; i++) {
        if (!results[0].vector[i] || results[0].vector[i]=='') continue;
        if (!results[0].vector[i].indexOf("Tip-")==0) continue;
        xpath.push( '//gobject[@name="'+results[0].vector[i]+'"]//tag[@name="angle"]' );
        titles.push( results[0].vector[i] );
    }
    if (xpath.length<=0) {
        BQ.ui.error('Hm, no root tip objects found...');  
    }
    
    var url = this.gobjectURL;
    //var url = 'http://vidi.ece.ucsb.edu:8080/ds/images/886/gobjects';
    var xmap = 'tag-value-number';
    var xreduce = 'vector';
    
    var opts = { title: 'Tip angle (t)', height:500, titles: titles };
    this.plotter = new BQStatisticsVisualizer( plotter_div, url, xpath, xmap, xreduce, opts );                                      
}

multiroot.prototype.doPlotError = function(e) {
    var plotter_div = document.getElementById("webapp_results_plotter");   
    plotter_div.style.height = 'auto';
    removeAllChildren(plotter_div);
    plotter_div.innerHTML = e.message;  
}

