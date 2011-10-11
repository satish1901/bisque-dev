/*******************************************************************************

  webapp - a fully integrated interface for a module

  This algorithm takes user clicks as inputs and tracks the apex of an organ 
  and reports out the tip angle of the apex. Initially the tip is located with 
  a user click and is subsequently tracked using a corner detector in 
  combination with a nearest neighbor tracking approach.
  
*******************************************************************************/

function WebApp (args) {
    //this.module_url = '/module_service/RootTipMulti'; 
    this.module_url = location.pathname; 
    this.label_run = "Run";  
    //this.require_geometry = { z: 'single', t:'stack', fail_message: 'The image must be a 2D time series!' }; 
    //this.require_gobjects = { gobject: 'point', amount: 'many', fail_message: 'You must select some root tips!' };     
    
    BQWebApp.call(this, args);
}
WebApp.prototype = new BQWebApp();
WebApp.prototype.constructor = WebApp;

WebApp.prototype.run = function () {
    //if (this.require_gobjects && this.image_viewer)
    //    this.run_arguments.frame_number = 1;

    BQWebApp.prototype.run.call(this);
}