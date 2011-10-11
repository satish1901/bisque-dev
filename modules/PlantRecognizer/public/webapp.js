/*******************************************************************************

  PlantRecognizer webapp - a fully integrated interface for a module

  
  
*******************************************************************************/

function PlantRecognizer (args) {
    this.module_url = '/module_service/PlantRecognizer'; 
    this.label_run = "Recognize plant";  
    this.require_geometry = { z: 'single', t:'single', fail_message: 'The image must be a 2D photograph!' }; 
    this.require_gobjects = { gobject: 'rectangle', amount: 'oneornone', fail_message: 'You can select one region of interest!' };     
    
    BQWebApp.call(this, args);
}
PlantRecognizer.prototype = new BQWebApp();
PlantRecognizer.prototype.constructor = PlantRecognizer;

PlantRecognizer.prototype.createSumary = function () {
    var summary = '<ul>';
    summary += this.renderSummaryTag('Genus', 'Genus');
    summary += this.renderSummaryTag('species', 'Specie', this.mexdict['wikipeda'], 'Wikipedia entry' );   
    summary += this.renderSummaryTag('common_name', 'Common name');   
    summary += this.renderSummaryTag('confidence', 'Confidence'); 
    summary += '</ul>';
    if (summary.length>0) summary = '<h3>Plant summary:</h3>'+summary;
    return summary;
}

BQWebApp.prototype.parseResults = function (mex) {
    
    BQWebApp.prototype.parseResults.call(this, arguments); 
    
    var q = 'Genus:"'+this.mexdict.Genus+'" AND species:"'+this.mexdict.species+'"'; 
      
    // show resource browser with example images      
    this.holder_result.show();        
    if (this.resultantResourcesBrowser) this.resultantResourcesBrowser.destroy();
    this.resultantResourcesBrowser = new Bisque.ResourceBrowser.Browser({
        height: '100%',   
        selType: 'SINGLE',
        viewMode : 'ViewerOnly',
        tagQuery : q, 
        listeners: {  'Select': function(me, resource) { 
                       window.open(bq.url('/client_service/view?resource='+resource.uri)); 
                   }, scope: this },
    });    
    this.holder_result.add(this.resultantResourcesBrowser);          
       
}
