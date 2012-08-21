
// this is used in conjunction with movieplayer.html
// TODO: add channel mapping

function moviePlayer(player_id, resource, flashurl) {

  this.root = flashurl;
  this._size_x = 0;
  this._size_y = 0;
  this._size_t = 0;
  this._size_z = 0;
  this._size_c = 0;
  this._image_url = "";        // base url for building the image href
  
  this._flash_width  = 600; 
  this._flash_height = 400;     
  this._fps = 30; 
  
  this.t1 = 0;
  this.t2 = 0;  
  this.z1 = 0;
  this.z2 = 0;  

  this._player_id    = player_id;

  BQFactory.request( { uri: resource, 
                       cb: callback(this, 'onimage'), 
                       errorcb: callback(this, 'onerror'), 
                       /*uri_params: {view:'deep'},*/  });   
  
}

moviePlayer.prototype.onerror = function (error) {
    var str = error;
    if (typeof(error)=="object") str = error.message;  
    BQ.ui.error(str);
}

moviePlayer.prototype.onimage = function (image) {
    this.image = image;
    BQFactory.request( { uri: image.src+'?meta', 
                         cb: callback(this, 'onmeta'), 
                         errorcb: callback(this, 'onerror'), 
                         /*uri_params: {view:'deep'},*/  });       
}

moviePlayer.prototype.onmeta = function (meta) {
    this.meta = meta.toDict(true);
    this.initPlayer();
}

moviePlayer.prototype.generateVideoUrl = function ( fmt ) {
  var pages = '';
  if (this.t1>0 && this.t2>0 && this.z1>0 && this.z2>0) {
      if (this.t2>this.t1)
        pages = '%26slice%3D,,'+String(this.z1)+','+String(this.t1)+'-'+String(this.t2);
      if (this.z2>this.z1)
        pages = '%26slice%3D,,'+String(this.z1)+'-'+String(this.z2)+','+String(this.t1);
  }

  var size = '';
  if (this._size_x>this._flash_width || this._size_y>this._flash_height) {
    size = '%26resize%3D'+String(this._flash_width)+','+String(this._flash_height)+',BC,MX';
  }
  
  var fu = this._image_url + '%3Fremap%3Ddisplay'+size+pages+'%26format%3D'+fmt;   
  if (this._fps > 0)
    fu += ',fps,'+String(this._fps);  
  return fu;
}

moviePlayer.prototype.generateUrl = function ( fmt ) {
  var pages = '';
  if (this.t1>0 && this.t2>0 && this.z1>0 && this.z2>0) {
      if (this.t2>this.t1)
        pages = '&slice=,,'+String(this.z1)+','+String(this.t1)+'-'+String(this.t2);
      if (this.z2>this.z1)
        pages = '&slice=,,'+String(this.z1)+'-'+String(this.z2)+','+String(this.t1);
  }

  var size = '';
  if (this._size_x>this._flash_width || this._size_y>this._flash_height) {
    size = '&resize='+String(this._flash_width)+','+String(this._flash_height)+',BC,MX';
  }
  
  var fu = this._image_url + '?remap=display'+size+pages+'&format='+fmt;   
  if (this._fps > 0)
    fu += ',fps,'+String(this._fps);  
  return fu;
}

moviePlayer.prototype.generateIconUrl = function () {
  var size = '';
  if (this._size_x>this._flash_width || this._size_y>this._flash_height) {
    size = '%26resize%3D'+String(this._flash_width)+','+String(this._flash_height)+',BC,MX';
  }  
  var fu = this._image_url + '%3Fremap%3Ddisplay'+size+'%26slice%3D,,1,1%26format%3Djpeg';   
  return fu;
}

/*
function toXmlString(xy,s) {
  var str = (s==undefined)?'' : s;
  if(xy.nodeValue==undefined) {
    var multiStr=[],temp='';
    for(var i=0;i<xy.childNodes.length; i++) {
      if (xy.childNodes[i].nodeName.toString().indexOf('#')<0) {
        var nodeNameStart ='<'+xy.childNodes[i].nodeName;
        var nodeNameEnd ='';
        var attsStr=' ',atts = xy.childNodes[i].attributes;
        if (atts!=undefined) {
          for(var j=0;j<atts.length;j++) {
            attsStr+=atts[j].nodeName+'="'+ atts[j].firstChild.nodeValue+'"';
          }
        }
        temp = nodeNameStart + ((attsStr==' ')?'':attsStr ) +'>'+toXmlString(xy.childNodes[i],str) + nodeNameEnd;
        multiStr.push(temp);
        str = temp;
      }else{
        str = toXmlString(xy.childNodes[i],str);
        multiStr.push(str);
      }
    }
    str = multiStr.join('');
  }else{
    return xy.nodeValue;
  }
  return str;
}
*/

moviePlayer.prototype.initPlayer = function () {
  if (!this.image || !this.meta) {
      BQ.ui.error('Image information could not be retrieved...');
      return;  
  } 
  
  this._size_x = parseInt(this.meta.image_num_x);
  this._size_y = parseInt(this.meta.image_num_y);
  this._size_c = parseInt(this.meta.image_num_c);
  this._size_z = parseInt(this.meta.image_num_z);
  this._size_t = parseInt(this.meta.image_num_t);
  this._image_url = this.image.src;
  
  var _num_pages = this._size_t * this._size_z;
  var _bitrate = 1000;  
  //if (_num_pages < 60) this._fps = Math.round(_num_pages / 3.5);   

  //if (_num_pages < 900) this._fps = 15;   
  if (_num_pages < 450) this._fps = 12;   
  if (_num_pages < 225) this._fps = 6;   
  if (_num_pages < 100) this._fps = 3;   
  if (_num_pages < 50) this._fps = 1;     
  
  //-----------------------------------------------------------------------
  // Update play parameters
  //-----------------------------------------------------------------------   
  var fps_edit = document.getElementById("fps");
  fps_edit.value = this._fps;
  
  var time_select = document.getElementById("timeCombo");
  var depth_select = document.getElementById("depthCombo");
  var update_btn = document.getElementById("update_video");   

  time_select.onchange  = callback(this, 'axisChanged');
  depth_select.onchange = callback(this, 'axisChanged');
  update_btn.onclick    = callback(this, 'reloadVideo');  

  if ( this._size_z <= 1 || this._size_t <= 1 ) {
    time_select.disabled = true;
    depth_select.disabled = true; 
  } else
  if ( this._size_z > 1 && this._size_t > 1 ) {
    var o = initPlanes( this._size_z );
    setSelectOption( depth_select, o );   
    depth_select.disabled = false;

    var o = initPlanes( this._size_t );
    setSelectOption( time_select, o );      
    time_select.disabled = false;
    
    if (this._size_z > 2)
      depth_select.selectedIndex = this._size_z/2;
    else
      depth_select.selectedIndex = 1;     
  } 
  this.axisChanged();

  //-----------------------------------------------------------------------
  // Create flash player
  //----------------------------------------------------------------------- 

  //var _mediaplayer  = 'mediaplayer.swf';     
  //var _mediaplayer  = 'player4.4.swf'; // working best   
  var _mediaplayer  = 'player4.5.swf'; // skips abruptly?
  //var _mediaplayer  = 'player4.6.swf'; // hanging badly
  //var _mediaplayer  = 'player4.7.swf'; // hanging badly  
  //var _mediaplayer  = 'player5.0.swf'; // shortcuts do not work   
  //var _mediaplayer  = 'player5.1.swf'; // 
  //var _mediaplayer  = 'player5.2.swf';        
  var _icon_url  = this.generateIconUrl();   
  var _flash_url = this.generateVideoUrl('flv');   
  
  var flash_vars_value = //'&width=' + _flash_width + '&height=' + _flash_height + 
    '&showstop=true&autostart=true&lightcolor=0xFF9900';
  flash_vars_value += '&usefullscreen=true&javascriptid=MDPlayer&enablejs=true';
  flash_vars_value += '&image=' + _icon_url;        
  flash_vars_value += '&repeat=always';
  //flash_vars_value += '&autostart=true';
  flash_vars_value += '&skin='+this.root+'/skins/stylish.swf';
  //flash_vars_value += '&plugins=/static/flash/plugins/shortcuts.swf'; //v 5
  flash_vars_value += '&plugins=shortcuts-1'; //v 4.4-4.5
  flash_vars_value += '&shortcuts.slowmotion=true';
  flash_vars_value += '&displayclick=play';                  
  //so.addVariable('stretching','fill');
  //flash_vars_value += '&icons=false'; 
  flash_vars_value += '&logo=false'; // v4 
  //flash_vars_value += '&logo.hide=false'; // v5  
    
  //flash_vars_value += '&type=flv'; // v3-4.3
  flash_vars_value += '&type=video'; // v4.5-4.7
  flash_vars_value += '&provider=video'; //v5
  flash_vars_value += '&file=' + _flash_url;
    
  var o = getObj( this._player_id );
  
  this.mp = document.createElementNS( xhtmlns, 'object' );
  this.mp.setAttribute('classid', 'clsid:D27CDB6E-AE6D-11cf-96B8-444553540000');
  this.mp.setAttribute('codebase', 'http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=7,0,0,0');    
  this.mp.setAttribute('width', this._flash_width);  
  this.mp.setAttribute('height', this._flash_height);          
  this.mp.setAttribute('allowfullscreen', 'true');      
  
  this.mprm1 = document.createElementNS( xhtmlns, 'param' );
  this.mprm1.setAttribute('name', 'movie');
  this.mprm1.setAttribute('value', this.root+'/'+_mediaplayer);    
  this.mp.appendChild(this.mprm1);           
  
  this.mprm2 = document.createElementNS( xhtmlns, 'param' );
  this.mprm2.setAttribute('name', 'FlashVars');
  this.mprm2.setAttribute('value', flash_vars_value);    
  this.mp.appendChild(this.mprm2);           
  
  this.mamp = document.createElementNS( xhtmlns, 'embed' );
  this.mamp.setAttribute('name', 'MDPlayer');
  this.mamp.setAttribute('id', 'MDPlayer');    
  this.mamp.setAttribute('width', this._flash_width);  
  this.mamp.setAttribute('height', this._flash_height);   
  this.mamp.setAttribute('allowfullscreen', 'true'); 
  this.mamp.setAttribute('allowscriptaccess', 'always');    
  this.mamp.setAttribute('quality', 'high');    
  this.mamp.setAttribute('src', this.root+'/'+_mediaplayer);              
  this.mamp.setAttribute('type', 'application/x-shockwave-flash');      
  this.mamp.setAttribute('flashvars', flash_vars_value);
  this.mp.appendChild(this.mamp);  
   
  o.appendChild(this.mp);    
  

  // HTML5 video tag stuff
   /*
    <source id="html5MP4src" src="pr6.mp4" type='video/mp4' />
    <source id="html5OGGsrc" src="pr6.ogv" type='video/ogg' />   
   */  

  //var html5MP4src = document.getElementById("html5MP4src");
  //var html5OGGsrc = document.getElementById("html5OGGsrc"); 
  //html5MP4src.src = this.generateVideoUrl('mpeg4');
  //html5OGGsrc.src = this.generateVideoUrl('ogg');  
}

function setSelectOption( _select, _options ) {
  removeAllChildren( _select );   
  for (var i in _options) {
    opt = document.createElementNS( xhtmlns,'option');
    opt.text = _options[i];
    opt.value = i;
    _select.appendChild( opt );
  } 
}

function initPlanes( num ) {
  var opt = new Object(); 
  opt['0'] = 'All'; 
  for (var i=0; i<num; ++i)
      opt[String(i+1)] = String(i+1); 
  return opt;
}


moviePlayer.prototype.axisChanged = function () {
  var time_select = document.getElementById("timeCombo");
  var depth_select = document.getElementById("depthCombo");
  var update_btn = document.getElementById("update_video"); 
  
  if ( time_select.selectedIndex>0 && depth_select.selectedIndex>0 )
    update_btn.disabled = true;
  else
    update_btn.disabled = false;

  this.t1 = 0; this.t2 = 0; this.z1 = 0; this.z2 = 0;  
  
  if (time_select.selectedIndex == 0) {
    this.t1 = 1; 
    this.t2 = this._size_t;     
  } else {
    this.t1 = time_select.selectedIndex; 
    this.t2 = this.t1;        
  }
  
  if (depth_select.selectedIndex == 0) {
    this.z1 = 1; 
    this.z2 = this._size_z;   
  } else {
    this.z1 = depth_select.selectedIndex; 
    this.z2 = this.z1;        
  } 
  
  if ( time_select.selectedIndex==0 && depth_select.selectedIndex==0 ) {
      this.t1 = 0; this.t2 = 0; this.z1 = 0; this.z2 = 0;   
  }
}

moviePlayer.prototype.reloadVideo = function () {
  var fps_edit = document.getElementById("fps");
  this._fps = parseFloat(fps_edit.value);

  var o = { file:this.generateVideoUrl('flv'), type:'flv' };
  var mvp = document.getElementById("MDPlayer");
  
  // old style, v3 version
  //mvp.loadFile(o);
  //mvp.sendEvent('play');  
  
  // new v4/v5 versions
  //mvp.sendEvent("LOAD", this.generateVideoUrl('flv') );
  mvp.sendEvent("LOAD", { file:this.generateVideoUrl('flv'), type:'video' } );
  //mvp.sendEvent("PLAY", "true");
}

moviePlayer.prototype.downloadAs = function ( fmt ) {  
  var u = this.generateUrl(fmt)+',stream';
  window.location = u;
  //window.open(u);    
}