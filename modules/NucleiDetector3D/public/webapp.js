/*******************************************************************************

  nd3d webapp - a fully integrated interface for a module

  This algorithm takes user clicks as inputs and tracks the apex of an organ 
  and reports out the tip angle of the apex. Initially the tip is located with 
  a user click and is subsequently tracked using a corner detector in 
  combination with a nearest neighbor tracking approach.
  
*******************************************************************************/

function nd3d (args) {
    this.module_url = '/module_service/NucleiDetector3D'; 
    this.label_run = "Detect nuclei";  
    this.require_geometry = { z: 'stack', t:'stack', fail_message: 'The image must be 3D or 4D!' }; 
    //this.require_gobjects = { gobject: 'point', amount: 'many', fail_message: 'You must select some root tips!' };     
    
    BQWebApp.call(this, args);
}
nd3d.prototype = new BQWebApp();
nd3d.prototype.constructor = nd3d;

nd3d.prototype.run = function () {
    if (this.require_gobjects && this.image_viewer)
        this.run_arguments.frame_number = 1;

    BQWebApp.prototype.run.call(this);
}

nd3d.prototype.createSumary = function () {
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
nd3d.prototype.exportToCSV = function() {
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

nd3d.prototype.plot = function() {

}
*/

