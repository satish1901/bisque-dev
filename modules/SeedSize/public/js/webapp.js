/*******************************************************************************

  SeedSize webapp - a fully integrated interface for a module

  Seedsize segments seeds on scanned images and produces gobjects with outlines 
  and estimation of seed areas
  
*******************************************************************************/

function seedsize (args) {
    this.module_url = '/module_service/SeedSize';    
    this.label_run = "Detect seeds";   
    this.require_geometry = { z: 'single', t:'single', fail_message: 'This module only supports 2D images!' };
    
    BQWebApp.call(this, args);
}
seedsize.prototype = new BQWebApp();
seedsize.prototype.constructor = seedsize;

seedsize.prototype.selectFile = function () {

    var uploader = Ext.create('BQ.upload.Dialog', {   
        dataset_configs: BQ.upload.DATASET_CONFIGS.REQUIRE, 
        listeners: {  'uploaded': function(reslist) { 
                       this.onResourceSelected(reslist[0]);
                }, scope: this },              
    });
}

seedsize.prototype.createSumary = function () {
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
}

seedsize.prototype.exportToCSV = function() {
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

seedsize.prototype.plot = function() {
    var plotter_div = document.getElementById("webapp_results_plotter"); 
    
    if (plotter_div.style.display == 'none') {
      plotter_div.style.display = '';
      removeAllChildren(plotter_div);        

      var url = this.gobjectURL;
      var xmap = 'tag-value-number';
      var xreduce = 'histogram';
    
      var surface_area = document.createElementNS(xhtmlns,'div');
      plotter_div.appendChild(surface_area);
      var xpath1 = '//tag[@name="area"]';      
      var opts = { title: 'Distribution of seed areas', height:500, args: {numbins: 18} };
      this.plotter1 = new BQStatisticsVisualizer( surface_area, url, xpath1, xmap, xreduce, opts );

      var surface_major = document.createElementNS(xhtmlns,'div');
      plotter_div.appendChild(surface_major);
      var xpath2 = '//tag[@name="major"]';      
      var opts = { title: 'Distribution of major axis', height:500, args: {numbins: 18} };
      this.plotter2 = new BQStatisticsVisualizer( surface_major, url, xpath2, xmap, xreduce, opts );

      var surface_minor = document.createElementNS(xhtmlns,'div');
      plotter_div.appendChild(surface_minor);
      var xpath3 = '//tag[@name="minor"]';      
      var opts = { title: 'Distribution of minor axis', height:500, args: {numbins: 18} };
      this.plotter3 = new BQStatisticsVisualizer( surface_minor, url, xpath3, xmap, xreduce, opts );
    } else {
        plotter_div.style.display = 'none';      
    }
}

