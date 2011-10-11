function ImgOperations (viewer,name) {
       
    this.default_enhancement = 'd';  // values: 'd', 'f', 't', 'e'                      
    this.default_negative    = '';   // values: '', 'negative'
    this.default_rotate      = 0;    // values: 0, 270, 90, 180
    this.default_autoupdate  = false;
  
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.menu = null;
    this.menu_elements = {};
    
    this.viewer.addCommand ('View', callback (this, 'toggleMenu'));
}
ImgOperations.prototype = new ViewerPlugin();

ImgOperations.prototype.create = function (parent) {
    this.parent = parent;
    return parent;
}

ImgOperations.prototype.newImage = function () {
    this.phys_inited = false;
}
ImgOperations.prototype.updateImage = function () {
}

ImgOperations.prototype.updateView = function (view) {
    if (!this.menu) this.createMenu(); 
    if (this.menu != null) {

        var cb = this.menu_elements['Enhancement'];
        view.addParams  ('depth=8,' + cb.value);

        var r = this.menu_elements['Red'].value;
        var g = this.menu_elements['Green'].value;
        var b = this.menu_elements['Blue'].value;
        view.addParams  ('remap='+r+','+g+','+b);

        cb = this.menu_elements['Rotate'];
        if (cb.value != 0)
            view.addParams  ('rotate=' + cb.value);
        cb.disabled=true; // no rotation for now
        view.rotateTo( parseInt(cb.value) );        

        cb = this.menu_elements['Negative'];
        if (cb.value != "") 
            view.addParams  (cb.value);
    } else {
        view.addParams  ('default');      
    }
      
}

ImgOperations.prototype.doUpdate = function () {
    this.viewer.need_update();
}

ImgOperations.prototype.changed = function () {
  if (!this.update_check || (this.update_check && this.update_check.checked) ) 
    this.viewer.need_update();
}

ImgOperations.prototype.createCombo = function (name, items, defval, parentdiv){
    var combo= document.createElementNS(xhtmlns, 'select');

    for (var i=0; i< items.length; i++) {
        var option = document.createElementNS(xhtmlns, 'option');
        option.text =  items[i][0];
        option.value = items[i][1];
        option.selected = (option.value == defval);
        combo.appendChild (option);
    }
    
    var div = document.createElementNS(xhtmlns, 'div');
    
    var label = document.createElementNS(xhtmlns, 'label');
    label.textContent = name;
   
    div.appendChild (label);
    div.appendChild (combo);    
    parentdiv.appendChild (div);
   
    this.menu_elements[name] = combo;
  	combo.onchange = callback(this, "changed", name);
    return combo;
}

ImgOperations.prototype.reloadCombo = function (name, items, defval) {
    var combo = this.menu_elements[name];    
  	combo.onchange = null;    
  	
  	// clear children
    if ( combo.hasChildNodes() ) {
        while ( combo.childNodes.length >= 1 )
            combo.removeChild( combo.lastChild );       
    }

    // recreate children
    for (var i=0; i< items.length; i++) {
        var option = document.createElementNS(xhtmlns, 'option');
        option.text =  items[i][0];
        option.value = items[i][1];
        option.selected = (option.value == defval);
        combo.appendChild (option);
    }
    
  	combo.onchange = callback(this, "changed", name);
}

ImgOperations.prototype.createGroup = function (name, parentdiv){
    var group = document.createElementNS(xhtmlns, 'div');
    group.setAttribute('id', 'group');

    var label = document.createElementNS(xhtmlns, 'h3');
    label.textContent = name;
    group.appendChild (label);   

    parentdiv.appendChild (group);
    return group;
}

ImgOperations.prototype.createButton = function (parentdiv, name, id, clbk) {
    var bt= document.createElementNS(xhtmlns, 'button');
    bt.innerHTML = name;
    //bt.name = name;    
    bt.setAttribute('id', id);
    bt.onclick = clbk;
    parentdiv.appendChild (bt);    
    return bt;
}

ImgOperations.prototype.createCheckbox = function (parentdiv, caption, id, defval, clbk) {
   
    var p = document.createElementNS( xhtmlns, 'input');
    p.setAttribute('id', id);    
    p.type = "checkbox";
    //p.name = "checker";
    p.value = "";
    p.checked = defval;   
    //p.className = "imgcnv_check";
    p.onclick = clbk;   
    p.setAttribute('style', 'float: left; '); // dima: should not be here, but in CSS, a hack
 
    var label = document.createElementNS(xhtmlns, 'label');
    label.textContent = caption;
    label.setAttribute('style', 'min-width: 200px;'); // dima: should not be here, but in CSS, a hack    

    parentdiv.appendChild (p);       
    parentdiv.appendChild (label);  
            
    return p;
}    

ImgOperations.prototype.createUpdateButton = function (parentdiv) {
    var group = document.createElementNS(xhtmlns, 'div');
    group.setAttribute('id', 'update_group');
    //group.className = "imgcnv_check";    

    this.update_check = this.createCheckbox(group, 'Auto update', 'update_checkbox', this.default_autoupdate, null );
    this.update_btn = this.createButton(group, 'Update', 'update_button', callback (this, 'doUpdate'));

    parentdiv.appendChild (group);
    return group;
}

ImgOperations.prototype.createMenu = function () {
    if (this.menu != null) return;
    
    this.menu = document.createElementNS(xhtmlns, "div");
    this.menu.className = "imgview_opdiv";
    //this.menu.style.left = this.parent.offsetLeft +10+ "px";
    //this.menu.style.top = this.parent.offsetTop + "px";              

    var dim = this.viewer.imagedim;
    
    this.createChannelMap( );
   
    var view_title = 'View';
    if (this.viewer.imagephys) {
      view_title = 'View ['+this.viewer.imagephys.pixel_depth+'bit p/ channel]';        
    }
    var group_view = this.createGroup (view_title, this.menu);    
    
    this.createCombo ('Enhancement', 
                      [ ["Data range", "d"],
                        ["Full range", "f"],
                        ["Data + tolerance", "t"],
                        ["Equalized", "e"]], this.default_enhancement, group_view);
    
    this.createCombo ('Negative', 
                      [ ["No", ""],
                        ["Negative", "negative"]], this.default_negative, group_view);

                       
    var planes_title = 'Planes [W:'+dim.x+', H:'+dim.y+']';
    var group_planes = this.createGroup (planes_title, this.menu);                            
    this.createCombo ('Rotate', 
                      [ ["None", 0],
                        ["Left", 270],
                        ["Right", 90],
                        ["180", 180]], this.default_rotate,  group_planes);
                 
    //create update button and checkbox
    this.createUpdateButton (this.menu);                  
                        
    this.menu.style.display = "none";
    this.viewer.imagediv.appendChild(this.menu);
}

ImgOperations.prototype.toggleMenu = function () {
    var need_update = false;
    if (this.menu == null) {
        this.createMenu();
        need_update =true;
    } 
    
    if (this.phys_inited != true && this.viewer.imagephys != null) {
        this.initChannels();  
        need_update = true;
    }
    
    this.viewer.active_submenu(this.menu);
    if (this.menu.style.display  == "none" ) { 
        this.menu.style.display = "";
        //var view_top = this.parent.offsetTop;
        //var view_left = this.parent.offsetLeft; 
        //this.menu.style.left = view_left+10 + "px";
        //this.menu.style.top = view_top+10 + "px";             
    } else
        this.menu.style.display = "none";

    if (need_update) 
        this.viewer.need_update();        

}

ImgOperations.prototype.createChannelMap = function ( ) {
    var channel_count = this.viewer.current_view.imagedim.ch;
    var imgphys = this.viewer.imagephys;    
    var channels = new Array (channel_count+1);
    
    channels[0] =  [ 'Empty', 0];
    for (var ch=1; ch <= channel_count; ch++) 
        channels[ch] = [ ch, ch ];

    var r=1, g=1, b=1; 
    if (channel_count == 2) { g=2; b=0; }
    if (channel_count >= 3) { g=2; b=3; }      
    
    var view_title = 'Channels: '+channel_count;       
    var group = this.createGroup (view_title, this.menu);
    this.createCombo ('Red',   channels, channels[r][1], group);
    this.createCombo ('Green', channels, channels[g][1], group);
    this.createCombo ('Blue',  channels, channels[b][1], group);
   
    this.initChannels(); 
}

ImgOperations.prototype.initChannels = function ( ) {
    var channel_count = this.viewer.current_view.imagedim.ch;
    var imgphys = this.viewer.imagephys;   
    
    if (imgphys != null) {
      var channels = new Array (channel_count+1);      
      channels[0] =  [ 'Empty', 0];      
      for (var ch=1; ch <= channel_count; ch++) 
          channels[ch] = [ imgphys.channel_names[ch-1], ch ];
     
      var ri = parseInt(imgphys.display_channels[0]); 
      var gi = parseInt(imgphys.display_channels[1]);
      var bi = parseInt(imgphys.display_channels[2]);    
      var r = channels[ri+1][1];
      var g = channels[gi+1][1];
      var b = channels[bi+1][1]; 

      this.reloadCombo ('Red',   channels, r);
      this.reloadCombo ('Green', channels, g);
      this.reloadCombo ('Blue',  channels, b);
      
      this.phys_inited = true;
    }
}

