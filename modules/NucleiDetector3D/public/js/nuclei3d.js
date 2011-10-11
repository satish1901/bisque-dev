
nuclei3D.prototype.onImageLoad = function (bqi) {
    this.bqimage = bqi;
    this.bqimagephys = new BQImagePhys (bqi);
    this.bqimagephys.load (callback(this, 'onPhysLoad') ); 
    bqi.load_tags(callback(this,"onTagsLoad"));
}

//------------------------------------------------------------------------------
nuclei3D.prototype.onPhysLoad = function () {
    var bqimg = this.bqimage;
    var bqphys = this.bqimagephys;    
    var select_nuclear_ch = document.getElementById("nuclei3d_nuclear_ch");
    var select_membrane_ch = document.getElementById("nuclei3d_membrane_ch");
    select_nuclear_ch.options.length = 0;
    select_membrane_ch.options.length = 0;
    select_membrane_ch.options[0] = new Option('None', 'None');    
    for( i=0; i<bqimg.ch; i++ ) {
        select_nuclear_ch.options[i] = new Option(bqphys.channel_names[i], i+1 );
        select_membrane_ch.options[i+1] = new Option(bqphys.channel_names[i], i+1 );
    }    
}

//------------------------------------------------------------------------------
nuclei3D.prototype.onTagsLoad = function () {
    var wanted = {  "pixel_resolution_x_y":"pixelResXYTag" , 
                    "pixel_resolution_z":"pixelResZTag",
                    "channel_stain_nuclei":"nuclearChTag" ,
                    "channel_stain_membrain":"membraneChTag"
    };

    for (var i=0; i < this.bqimage.tags.length; i++) {
        if (this.bqimage.tags[i] == null) continue;
        var name = this.bqimage.tags[i].name;
        if (name in wanted) {
            this[wanted[name]] = this.bqimage.tags[i];
        }
    }
    for (var k in wanted) {
        this[wanted[k]] = this.ensureTag(this[wanted[k]], k, null);
    }
    this.updateGUI();
    this.updateParameters();    

    var button_run = document.getElementById("nuclei3d_run_button");
    button_run.disabled = false;

}
//------------------------------------------------------------------------------
nuclei3D.prototype.ensureTag = function ( t, name, value ) {
    if (t == null) {
        t = new BQTag();
        t.name = name;
        t.value = value;
        this.bqimage.tags.push( t );
    }
    return t;
}
//------------------------------------------------------------------------------

	

//------------------------------------------------------------------------------
nuclei3D.prototype.updateGUI = function () {
    var input_pix_xy = document.getElementById("nuclei3d_pixel_size_xy");
    input_pix_xy.value = this.pixelResXYTag.value;

    var input_pix_z = document.getElementById("nuclei3d_pixel_size_z");
    input_pix_z.value = this.pixelResZTag.value;

    var input_kernel = document.getElementById("nuclei3d_kernel");
    input_kernel.value = this.kernelSize;

    var input_thersh = document.getElementById("nuclei3d_intensity");
    input_thersh.value = this.intencityBound;

    var select_nuclear_ch = document.getElementById("nuclei3d_nuclear_ch");
    var select_membrane_ch = document.getElementById("nuclei3d_membrane_ch");
    select_nuclear_ch.options.length = 0;
    select_membrane_ch.options.length = 0;
    select_membrane_ch.options[0] = new Option('None', 'None');
    for( i=0; i<this.bqimage.ch; i++ ) {
        var channel_name = i;
        if (this.bqimagephys != null) channel_name = this.bqimagephys.channel_names[i];
        select_nuclear_ch.options[i] = new Option(channel_name, i+1);
        select_membrane_ch.options[i+1] = new Option(channel_name, i+1);
    }

    select_nuclear_ch.selectedIndex = this.nuclearChTag.value-1;
    if (this.membraneChTag.value && this.membraneChTag.value.toLowerCase() != 'none')
        select_membrane_ch.selectedIndex = this.membraneChTag.value;
    else
        select_membrane_ch.selectedIndex = 0;
}
//------------------------------------------------------------------------------
nuclei3D.prototype.get_checked_value = function ( element_id, errors, str ) {
    var input_element = document.getElementById( element_id );
    if (input_element.value != '' && input_element.value > 0) {
      input_element.className = '';      
    } else {
      input_element.className = 'nuclei3d_needs_update';
      errors.push(str);
    }
    return input_element.value;    
}

nuclei3D.prototype.updateParameters = function ( user_interaction ) {
    var errors = new Array();
    
    if(!this.imageURL) { return 'No image is selected, select an image!'; }

    this.kernelSize = this.get_checked_value( "nuclei3d_kernel", errors, 'Missing nuclei size' );      
    this.intencityBound = this.get_checked_value( "nuclei3d_intensity", errors, 'Missing intensity bound' );         
    this.pixelResXYTag.value = this.get_checked_value( "nuclei3d_pixel_size_xy", errors, 'Missing pixel resolution X/Y' );   
    this.pixelResZTag.value = this.get_checked_value( "nuclei3d_pixel_size_z", errors, 'Missing pixel resolution Z' );     

    var select_nuclear_ch = document.getElementById("nuclei3d_nuclear_ch");
    var select_membrane_ch = document.getElementById("nuclei3d_membrane_ch");
    this.nuclearChTag.value = select_nuclear_ch.value;
    this.membraneChTag.value = select_membrane_ch.value;
    
    if (errors.length == 0) return null;
    return errors.join(', ');
}


//------------------------------------------------------------------------------
nuclei3D.prototype.generateResults = function (mex) {
    for (var i=0; i<mex.tags.length; i++) {
        var name = mex.tags[i].name;
        var value = mex.tags[i].value;
        if (name == "nuclei_count") this.nucleiCount = value;
        if (name == "gobject_url")  this.gobjectURL = value;
        if (name == "start-time")  this.start_time = value;        
        if (name == "end-time")  this.end_time = value;              
    }  

    var time_string='a couple of moments:)';
    if (this.start_time && this.end_time) {
      var start = new Date();
      var end   = new Date();    
      start.setISO8601(this.start_time);
      end.setISO8601(this.end_time);      
      var elapsed = new DateDiff(end - start);
      time_string = " in "+elapsed.toString();
    }
  
    var result_label = document.getElementById("nuclei3d_result_count");
    if (result_label) 
      result_label.innerHTML = 'Nuclei found: '+this.nucleiCount+" in "+time_string;

    var results_div = document.getElementById("nuclei3d_results_content");
    if (results_div) 
      results_div.style.display = '';
}


//------------------------------------------------------------------------------
nuclei3D.prototype.runNucleiDetector = function () {
    var error = this.updateParameters();
    if (error == null) {
      var results_div = document.getElementById("nuclei3d_results_content");
      results_div.style.display = 'none';
      this.tags_saved = 0;
      this.bqimage.save_tags(callback(this,"tagSaveCallback"));
    } else {
      alert( error );
    }
}
nuclei3D.prototype.tagSaveCallback = function () {
    this.runOnSaved();
}
//------------------------------------------------------------------------------
nuclei3D.prototype.runOnSaved = function () {
    var parameters = {
        image_url : this.imageURL,
        cellSize  : this.kernelSize,
        thValue   : this.intencityBound,
        channel_Nuclei : this.nuclearChTag.value,
        channel_Membrane : this.membraneChTag.value,
    };

    var button_run = document.getElementById("nuclei3d_run_button");
    button_run.disabled = true;
    button_run.childNodes[0].nodeValue = "Running ...";
    this.ms.run(parameters);
}

nuclei3D.prototype.view3D = function() {
    if (this.gobjectURL == null) {
      alert('No resulting gobjects found yet...');
      return; 
    }  
    var user_name = this.bq_user.user_name;
    var pass = this.bq_user.password;  
    var new_url = 'bioview3d://resource/?user='+user_name+'&pass='+pass+'&url='+this.imageURL+'&gobjects='+this.gobjectURL;  
    //window.location = new_url;  
    window.open(new_url);    
}
