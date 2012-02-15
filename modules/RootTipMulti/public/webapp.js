
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

