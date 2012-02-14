/*
  Image Converter widget
  Authors: Boguslaw Obara, Dmitry Fedorov
  Center for BioImage Informatics, 2007
*/

// <![CDATA[


function openImageConverter( parent_id, image_resource ) {
 
  if (this._imgConv2 == null) {
    this._imgConv2 = new ImageConverter( this._img_resourceURI  );	
    this._imgConv2.GetImageInfo( this._image_url );
	  var optdiv = getObj(parent_id);
	  optdiv.appendChild( this._imgConv2.maindiv );  	  
  }
	
	if (this._imgConv2.maindiv.style.display == "none") 
	  this._imgConv2.maindiv.style.display = "";
  else 
    this._imgConv2.maindiv.style.display = "none";
}

function openDownloadOriginal( parent_id ) {
  window.location = this._image_url;
}

function downloadAnnotations( parent_id ) {
  var requesturl = this._img_resourceURI + "/gobject?view=deep,canonical";
  window.location = requesturl;
  //makeRequest( requesturl, parseImageTagsXML, null, "get", "" );
}

function downloadTags( parent_id ) {
  var requesturl = this._img_resourceURI + "/tag?view=deep";
  window.location = requesturl;
  //makeRequest( requesturl, parseImageTagsXML, null, "get", "" );
}

function ImageInfoClass() {
  this.size_x = null;
  this.size_y = null;
  this.size_c = null;
  this.size_z = null;
  this.size_t = null;
  this.depth = null;
  this.format = null;
} 

function ImageConverter (resourceURI) {
  
  this.imageInfo = new ImageInfoClass();
  this.maindiv = document.createElementNS(xhtmlns, "div");
  this.resourceURI = resourceURI;
  
  this.widgets = new Array();

  this.maindiv.style.display = "none";
  this.maindiv.className = "optionswidget"; 
  this.maindiv.style.overflow = "visible"; 
  
  this.widgets.getWidgetByName = function ( name ) {
      w = null;
    for (i=0; i<this.length; ++i)
      if (this[i].name == name ) {
              w = this[i];
        break;
        }

      return w;
    } 
  
}

ImageConverter.prototype.getRequestQuery = function () {
  var requestQuery = "";
  
  for (i=0; i<this.widgets.length; i++) {
    str = this.widgets[i].getCallString();
    if (str==null) continue;
    if (requestQuery.length>0 && str.length>0) requestQuery += "&";
    requestQuery += str;
  }
  
  return requestQuery;
}

ImageConverter.prototype.doEnvironmentChanged = function () {
  var requestQuery = this.getRequestQuery();
  for (i=0; i<this.widgets.length; i++) {
    if (this.widgets[i].onEnvironmentChanged == null) continue; 
    this.widgets[i].onEnvironmentChanged( requestQuery );
  }
}



//----------------------------------------------------------------------------------------------------------
// Begin: Base Widget for Image Convert
//----------------------------------------------------------------------------------------------------------

function ImageConverterWidget ( imgcnv, header_label, show_enable ) {

  this.name = header_label;
  this.mydiv = document.createElementNS( xhtmlns, 'div' );
  this.mydiv.className = "imgcnv_s";
  this.imgcnv = imgcnv;
  this.parentdiv = null;
  if (imgcnv.maindiv != null) {
      this.parentdiv = imgcnv.maindiv;
      imgcnv.maindiv.appendChild( this.mydiv );
  }
  
  //this.mydiv.style.padding = "10px 10px 10px 10px";

  if (show_enable) {
    this.checker = document.createElementNS( xhtmlns,'input');
    this.checker.type = "checkbox";
    this.checker.name = "checker";
    this.checker.value = "";
    this.checker.checked = false;   
    this.checker.className = "imgcnv_check";
    this.checker.widget = this;
    this.mydiv.appendChild( this.checker );   
    this.checker.onclick = this.checkerChanged;   
  }

  if (header_label) {
      this.myheader = document.createElementNS( xhtmlns, 'h3' );
      this.myheader.appendChild(document.createTextNode(header_label));
      this.mydiv.appendChild(this.myheader);  
  }
  
  return this;
}

ImageConverterWidget.prototype.checkerChanged = function () {
  
  for (i=0; i<this.parentNode.childNodes.length; ++i) {
    if (this.parentNode.childNodes[i] != this )
          this.parentNode.childNodes[i].disabled = !this.checked; 
  }
  this.widget.imgcnv.doEnvironmentChanged();
  return this;
}

ImageConverter.prototype.KeyPressEventOnlyNumericInput = function (e) {

  var w = (e.which) ? e.which : e.keyCode;
  var curKey = String.fromCharCode(w).toLowerCase();
  if ((curKey>='0')&&(curKey<='9')){
  }
  else if (((curKey>='a')&&(curKey<='z'))) {
    alert("Use only numeric values!");
    return false;
  }
  else {
  } 
  return true;
}

ImageConverterWidget.prototype.setEnabled = function ( enable ) {
  this.checker.checked = enable;   
  this.checker.onclick();
}

ImageConverterWidget.prototype.getDiv = function () {
  return this.mydiv;
}

ImageConverterWidget.prototype.onEnvironmentChanged = function ( request_string ) {

}

ImageConverterWidget.prototype.getCallString = function () {
  return '';
}

//----------------------------------------------------------------------------------------------------------
// Rotate Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateRotate = function (widget) {
  
  widget.eselectR = document.createElementNS(xhtmlns, 'select');
  widget.eselectR.className = "imgenh";
  
  widget.eoptionR = new Array();
  widget.eoptionR[0] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[0].text = "None";
  widget.eoptionR[0].value = "0";
  widget.eoptionR[0].selected = true; 
  widget.eselectR.appendChild(widget.eoptionR[0]);
  widget.eoptionR[1] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[1].text = "Left";
  widget.eoptionR[1].value = "270";
  widget.eselectR.appendChild(widget.eoptionR[1]);
  widget.eoptionR[2] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[2].text = "Right";
  widget.eoptionR[2].value = "90";
  widget.eselectR.appendChild(widget.eoptionR[2]);
  widget.eoptionR[3] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[3].text = "180 deg";
  widget.eoptionR[3].value = "180";
  widget.eselectR.appendChild(widget.eoptionR[3]);
  
  widget.mydiv.appendChild(document.createTextNode("Rotate:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.eselectR);
  
  widget.getCallString = function () {
    if (this.eselectR.selectedIndex == 1) return "rotate=270";
    if (this.eselectR.selectedIndex == 2) return "rotate=90";   
    if (this.eselectR.selectedIndex == 3) return "rotate=180";        
    return "";
  }
};


//----------------------------------------------------------------------------------------------------------
// Crop Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateCrop = function (widget, x,y) {
  
  widget.size_x = x;
  widget.size_y = y;  
  
  widget.formROIx1 = document.createElementNS( xhtmlns,'input');
  widget.formROIx1.type = "text";
  widget.formROIx1.name = "formROIx1";
  widget.formROIx1.value = 0;
  widget.formROIx1.className = "imgcnv";
  widget.formROIx1.ownerWidget = widget;  

  widget.formROIy1 = document.createElementNS( xhtmlns,'input');
  widget.formROIy1.type = "text";
  widget.formROIy1.name = "formROIy1";
  widget.formROIy1.value = 0;
  widget.formROIy1.className = "imgcnv";
  widget.formROIy1.ownerWidget = widget;  

  widget.formROIx2 = document.createElementNS( xhtmlns,'input');
  widget.formROIx2.type = "text";
  widget.formROIx2.name = "formROIx2";
  widget.formROIx2.value = x-1;
  widget.formROIx2.className = "imgcnv";
  widget.formROIx2.ownerWidget = widget;  

  widget.formROIy2 = document.createElementNS( xhtmlns,'input');
  widget.formROIy2.type = "text";
  widget.formROIy2.name = "formROIy2";
  widget.formROIy2.value = y-1;
  widget.formROIy2.className = "imgcnv";
  widget.formROIy2.ownerWidget = widget;    

  widget.mydiv.appendChild(document.createTextNode("ROI(x1,y1,x2,y2):"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.formROIx1);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.formROIy1);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.formROIx2);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.formROIy2);
  
  widget.formROIx1.onkeypress = this.KeyPressEventOnlyNumericInput;
  widget.formROIy1.onkeypress = this.KeyPressEventOnlyNumericInput;
  widget.formROIx2.onkeypress = this.KeyPressEventOnlyNumericInput;
  widget.formROIy2.onkeypress = this.KeyPressEventOnlyNumericInput;
  
  widget.formROIx1.onkeyup = this.CropKeyUpEvent; 
  widget.formROIy1.onkeyup = this.CropKeyUpEvent; 
  widget.formROIx2.onkeyup = this.CropKeyUpEvent; 
  widget.formROIy2.onkeyup = this.CropKeyUpEvent;   
  
  widget.setEnabled( false );
  
  widget.getCallString = function () {
    if (!this.checker.checked) return "";
    
    if ( (parseInt(this.formROIx1.value) == 0) &&
       (parseInt(this.formROIy1.value) == 0) &&
       (parseInt(this.formROIx2.value) == this.size_x) &&
       (parseInt(this.formROIy2.value) == this.size_y) ) 
    return "";    

    if ( (parseInt(this.formROIx1.value) >= 0) &&
       (parseInt(this.formROIy1.value) >= 0) &&
       (parseInt(this.formROIx2.value) < this.size_x) &&
       (parseInt(this.formROIy2.value) < this.size_y) ) 
    {
    return "roi=" + this.formROIx1.value + "," + this.formROIy1.value + "," + this.formROIx2.value + "," +  this.formROIy2.value;   
    } else
        return "";
    } 
}

ImageConverter.prototype.CropKeyUpEvent = function (e) {
    var widget = this.ownerWidget;
  
    if (parseInt(widget.formROIx1.value) < 0) widget.formROIx1.value = 0;
    if (parseInt(widget.formROIx1.value) >= widget.size_x) widget.formROIx1.value = widget.size_x-1;
    if (parseInt(widget.formROIy1.value) < 0) widget.formROIy1.value = 0;
    if (parseInt(widget.formROIy1.value) >= widget.size_y) widget.formROIy1.value = widget.size_y-1;
  
    if (parseInt(widget.formROIx2.value) < 0) widget.formROIx2.value = 0; 
    if (parseInt(widget.formROIx2.value) >= widget.size_x) widget.formROIx2.value = widget.size_x-1;
    if (parseInt(widget.formROIy2.value) < 0) widget.formROIy2.value = 0;   
    if (parseInt(widget.formROIy2.value) >= widget.size_y) widget.formROIy2.value =  widget.size_y-1; 
  
  return true;
}

//----------------------------------------------------------------------------------------------------------
// Planes Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreatePlanes = function (widget, nt, nz) {
  
  widget.eselectR = document.createElementNS(xhtmlns, 'select');
  widget.eselectR.className = "imgenh";
  
  widget.eoptionR = new Array();
  widget.eoptionR[0] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[0].text = "Original";
  widget.eoptionR[0].value = "0";
  widget.eoptionR[0].selected = true; 
  widget.eselectR.appendChild(widget.eoptionR[0]);
  widget.eoptionR[1] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[1].text = "Project by max intensity";
  widget.eoptionR[1].value = "projectmax";
  widget.eselectR.appendChild(widget.eoptionR[1]);
  widget.eoptionR[2] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[2].text = "Project by min intensity";
  widget.eoptionR[2].value = "projectmin";
  widget.eselectR.appendChild(widget.eoptionR[2]);
  widget.eoptionR[3] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[3].text = "Extract planes";
  widget.eoptionR[3].value = "extract";
  widget.eselectR.appendChild(widget.eoptionR[3]);
  widget.eoptionR[4] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[4].text = "Sample planes";
  widget.eoptionR[4].value = "sample";
  widget.eselectR.appendChild(widget.eoptionR[4]);

  widget.eoptionR[5] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[5].text = "Advanced";
  widget.eoptionR[5].value = "advanced";
  widget.eselectR.appendChild(widget.eoptionR[5]);
 
  widget.eselectR.ownerWidget = widget;      
  
  widget.eselectR.onclick = this.onPlanesTypeChanged;  
  
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.eselectR);  
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));  
  
  
  
  widget.size_z = nz;
  widget.size_t = nt; 

  widget.selectZ = document.createElementNS( xhtmlns,'select');
  widget.selectZ.className = "imgcnv";
  widget.selectZ.widget = widget;
  widget.selectZ.onclick = this.onPlanesEvent;  
  widget.optionZ = new Array();
  for (var i=0; i<=widget.size_z; i++) {
    widget.optionZ[i] = document.createElementNS( xhtmlns,'option');
    if (i==0)
        widget.optionZ[i].text = 'All';   
    else
        widget.optionZ[i].text = i;
    widget.optionZ[i].value = i;
    widget.selectZ.appendChild(widget.optionZ[i]);
  }
  widget.mydiv.appendChild(document.createTextNode("Z:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectZ);

  widget.selectT = document.createElementNS( xhtmlns,'select');
  widget.selectT.className = "imgcnv";
  widget.selectT.widget = widget; 
  widget.selectT.onclick = this.onPlanesEvent;
  widget.optionT = new Array(); 
  for(var i=0; i<=widget.size_t; i++) {
    widget.optionT[i] = document.createElementNS( xhtmlns,'option');
    if (i==0)
        widget.optionT[i].text = 'All';   
    else
        widget.optionT[i].text = i;   
    widget.optionT[i].value = i;
    widget.selectT.appendChild(widget.optionT[i]);
  }
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("T:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectT);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  
  
  //////////////////////////////////////////////////////////////////////  
  // Sampling
  //////////////////////////////////////////////////////////////////////      
  widget.formSample = document.createElementNS( xhtmlns,'input');
  widget.formSample.onkeypress = this.KeyPressEventOnlyNumericInput;
  //widget.formSample.onkeyup = this.ResizeYKeyUpEvent;    
  widget.formSample.type = "text";
  widget.formSample.name = "formSample";
  widget.formSample.value = "10";
  widget.formSample.className = "imgcnv";
  widget.formSample.ownerWidget = widget;      
  
  widget.mydiv.appendChild(document.createTextNode("Sample every Nth:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));  
  widget.mydiv.appendChild(widget.formSample);  
  
  
  //////////////////////////////////////////////////////////////////////  
  // Advanced
  //////////////////////////////////////////////////////////////////////    
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Advanced:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  
  widget.formAdv = document.createElementNS( xhtmlns,'input');
  //widget.formAdv.onkeypress = this.KeyPressEventOnlyNumericInput;
  widget.formAdv.type = "text";
  widget.formAdv.name = "formAdv";
  widget.formAdv.value = "1,-," + (nz*nt);
  widget.formAdv.className = "imgcnv";
  widget.formAdv.ownerWidget = widget;        
  widget.mydiv.appendChild(widget.formAdv);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));  
  widget.mydiv.appendChild(document.createTextNode("1,2,4 or 1,-,4 or 1,- or -,5"));   
  
  //////////////////////////////////////////////////////////////////////  
  // General 
  //////////////////////////////////////////////////////////////////////    
  widget.selectZ.disabled = true;
  widget.selectT.disabled = true;
  widget.formSample.disabled = true;  
  widget.formAdv.disabled = true;    
  
  widget.getCallString = function () {
    if (this.eselectR.selectedIndex == 0) return "";
    if (this.eselectR.selectedIndex == 1) return "projectmax";   
    if (this.eselectR.selectedIndex == 2) return "projectmin";     
    if (this.eselectR.selectedIndex == 3)
      return "slice=,," + this.selectZ.selectedIndex + "," + this.selectT.selectedIndex + ",";
    if (this.eselectR.selectedIndex == 4)
      return "sampleframes=" + this.formSample.value;
    if (this.eselectR.selectedIndex == 5)
      return "frames=" + this.formAdv.value;      
  } 
}

ImageConverter.prototype.onPlanesEvent = function (e) {
  this.widget.imgcnv.doEnvironmentChanged();
}

ImageConverter.prototype.onPlanesTypeChanged = function (e) {
  var widget = this.ownerWidget;

  widget.selectZ.disabled = true;
  widget.selectT.disabled = true;
  widget.formSample.disabled = true;
  widget.formAdv.disabled = true;  

  if (widget.eselectR.selectedIndex == 3) {
    widget.selectZ.disabled = false;
    widget.selectT.disabled = false;
  } else 
  if (widget.eselectR.selectedIndex == 4) {
    widget.formSample.disabled = false;
  }  else 
  if (widget.eselectR.selectedIndex == 5) {
    widget.formAdv.disabled = false;
  }
 
  widget.imgcnv.doEnvironmentChanged();  
}


//----------------------------------------------------------------------------------------------------------
// Size Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateSize = function (widget, x,y) {
  
  widget.size_x = x;
  widget.size_y = y;
  
  widget.formResizex = document.createElementNS( xhtmlns,'input');
  widget.formResizex.onkeypress = this.KeyPressEventOnlyNumericInput;
  widget.formResizex.onkeyup = this.ResizeXKeyUpEvent;  
  widget.formResizex.type = "text";
  widget.formResizex.name = "formResizex";
  widget.formResizex.value = x;
  widget.formResizex.className = "imgcnv";
  widget.formResizex.ownerWidget = widget;    
  
  widget.formResizey = document.createElementNS( xhtmlns,'input');
  widget.formResizey.onkeypress = this.KeyPressEventOnlyNumericInput;
  widget.formResizey.onkeyup = this.ResizeYKeyUpEvent;    
  widget.formResizey.type = "text";
  widget.formResizey.name = "formResizey";
  widget.formResizey.value = y;
  widget.formResizey.className = "imgcnv";
  widget.formResizey.ownerWidget = widget;    

  widget.boxResize = document.createElementNS( xhtmlns,'input');
  widget.boxResize.type = "checkbox";
  widget.boxResize.name = "boxUse";
  widget.boxResize.value = "";
  widget.boxResize.checked = false;
  widget.selectResize=document.createElementNS( xhtmlns,'select');
  widget.selectResize.className = "imgcnv";
  widget.selectResize.onclick = createMethodReference(this, "EventCHMA");
  widget.optionResize = new Array();
  widget.optionResize[0] = document.createElementNS( xhtmlns,'option');
  widget.optionResize[0].text = "Nearest";
  widget.optionResize[0].value = "NN";
  widget.optionResize[1] = document.createElementNS( xhtmlns,'option');
  widget.optionResize[1].text = "Linear";
  widget.optionResize[1].value = "BL";
  widget.optionResize[1].selected = true;
  widget.optionResize[2] = document.createElementNS( xhtmlns,'option');
  widget.optionResize[2].text = "Cubic";
  widget.optionResize[2].value = "BC";
  widget.selectResize.appendChild(widget.optionResize[0]);
  widget.selectResize.appendChild(widget.optionResize[1]);
  widget.selectResize.appendChild(widget.optionResize[2]);

  widget.mydiv.appendChild(document.createTextNode("Resize (W,H):"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.formResizex);
  widget.mydiv.appendChild(widget.formResizey);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Proportional:"));
  widget.mydiv.appendChild(widget.boxResize);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectResize);
  
  widget.setEnabled( false );  
  
  widget.getCallString = function () {
    if (!this.checker.checked) return "";
    if ((parseInt(this.formResizex.value) == this.size_x) && (parseInt(this.formResizey.value) == this.size_y)) return "";
    if ((parseInt(this.formResizex.value) > this.size_x) || (parseInt(this.formResizey.value) > this.size_y)) return ""; 
      return "resize=" + this.formResizex.value + "," + this.formResizey.value + "," +  this.selectResize.options[this.selectResize.selectedIndex].value;
    } 
}

ImageConverter.prototype.ResizeXKeyUpEvent = function (e) {
  var widget = this.ownerWidget;
  
  if (widget.boxResize.checked == true)
    widget.formResizey.value = (parseInt(widget.formResizex.value)*widget.size_y)/widget.size_x;  
  
  if (parseInt(widget.formResizex.value) < 0) widget.formResizex.value = 0;
  if (parseInt(widget.formResizex.value) > widget.size_x) widget.formResizex.value = widget.size_x;
  if (parseInt(widget.formResizey.value) < 0) widget.formResizey.value = 0;
  if (parseInt(widget.formResizey.value) > widget.size_y) widget.formResizey.value = widget.size_y;
  
  return true;  
}

ImageConverter.prototype.ResizeYKeyUpEvent = function (e) {
  var widget = this.ownerWidget;
  
  if (widget.boxResize.checked == true)
    widget.formResizex.value = (parseInt(widget.formResizey.value)*widget.size_x)/widget.size_y;
    
  if (parseInt(widget.formResizex.value) < 0) widget.formResizex.value = 0;
  if (parseInt(widget.formResizex.value) > widget.size_x) widget.formResizex.value = widget.size_x;
  if (parseInt(widget.formResizey.value) < 0) widget.formResizey.value = 0;
  if (parseInt(widget.formResizey.value) > widget.size_y) widget.formResizey.value = widget.size_y;
  
  return true;    
}

//----------------------------------------------------------------------------------------------------------
// Format Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateFormat = function (widget, format) {
  
  widget.selectFormat = document.createElementNS( xhtmlns,'select');
  widget.selectFormat.className = "imgcnv";
  
  widget.formatsAll = new Array();  
  widget.formatsAll.push( "TIFF" );
  widget.formatsAll.push( "PNG" );
  widget.formatsAll.push( "JPEG" );
  widget.formatsAll.push( "RAW" );
  widget.formatsAll.push( "BMP" );
  widget.formatsAll.push( "GIF" );  
  widget.formatsAll.push( "Flash" );
  widget.formatsAll.push( "FLV" );  
  widget.formatsAll.push( "AVI" );
  widget.formatsAll.push( "QuickTime" );
  widget.formatsAll.push( "MPEG" );    
  widget.formatsAll.push( "MPEG2" );    
  widget.formatsAll.push( "MPEG4" );        
  widget.formatsAll.push( "WMV" );      
  
  widget.formats16bit = new Array();  
  widget.formats16bit.push( "TIFF" );
  widget.formats16bit.push( "PNG" );
  widget.formats16bit.push( "RAW" );
  
  widget.formatsMultiPage = new Array();  
  widget.formatsMultiPage.push( "TIFF" );
  widget.formatsMultiPage.push( "RAW" );  
  widget.formatsMultiPage.push( "Flash" );
  widget.formatsMultiPage.push( "FLV" );    
  widget.formatsMultiPage.push( "AVI" );
  widget.formatsMultiPage.push( "QuickTime" );
  widget.formatsMultiPage.push( "MPEG" );    
  widget.formatsMultiPage.push( "MPEG2" );    
  widget.formatsMultiPage.push( "MPEG4" );        
  widget.formatsMultiPage.push( "WMV" );        

  
  //widget.currentFormats = widget.formatsAll;  
  widget.currentFormats = widget.formatsMultiPage;    
  
  
  this.reCreateFormatCombo (widget, format);
  
  widget.mydiv.appendChild(document.createTextNode("Format:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectFormat);

  widget.getCallString = function () {
      return "format=" + this.selectFormat.options[this.selectFormat.selectedIndex].text + ",stream";
    } 
	
  widget.onEnvironmentChanged = function ( request_string ) {
	 
	  var num_channels = widget.imgcnv.imageInfo.size_c;
	  var num_planes = widget.imgcnv.imageInfo.size_z * widget.imgcnv.imageInfo.size_t;	  
	  var num_bits = widget.imgcnv.imageInfo.depth;	  
	  
	  if ( request_string.indexOf("depth=32") != -1 ) num_bits = 32;
	  if ( request_string.indexOf("depth=16") != -1 ) num_bits = 16; 
	  if ( request_string.indexOf("depth=8") != -1 ) num_bits = 8; 	 
	  
	  if ( request_string.indexOf("slice=") != -1 ) {
		  var slice_str = request_string.substr( request_string.indexOf("slice=")+6 );
		  if (slice_str.indexOf("&") != -1)
		    slice_str = slice_str.substr( 0, slice_str.indexOf("&") );

      //"slice=,,0,0"
		  var sliceList = slice_str.split(",");
		  var z = sliceList[2];
	   	var t = sliceList[3];
      if (z > 0) num_planes = num_planes / widget.imgcnv.imageInfo.size_z;	  
      if (t > 0) num_planes = num_planes / widget.imgcnv.imageInfo.size_t;	  		
	  }	
	  
	  if ( request_string.indexOf("projectmax")!=-1 || request_string.indexOf("projectmin")!=-1 ) {
      num_planes = 1;	  
	  }	  	    
	  
	  if ( request_string.indexOf("remap=") != -1 ) {
		  var remap_str = request_string.substr( request_string.indexOf("remap=")+6 );
		  if (remap_str.indexOf("&") != -1)
		    remap_str = remap_str.substr( 0, remap_str.indexOf("&") );

      //"slice=,,0,0"
		  var remapList = remap_str.split(",");
		  num_channels = remapList.length;
	  }	  	  
	 
	  if ( num_planes>1 || num_bits==32 || num_channels>4 ) {
	    // most restrictive - multipage formats
        this.currentFormats = this.formatsMultiPage; 
        this.imgcnv.reCreateFormatCombo (this, "TIFF");		
	  } else
      if ( num_bits == 16 || num_channels==4 ) {
	    // less restrictive - 16 bits formats
        this.currentFormats = this.formats16bit; 
        this.imgcnv.reCreateFormatCombo (this, "TIFF");		
	  } else {
	    // not restrictive - all formats		  
        this.currentFormats = this.formatsAll; 
        this.imgcnv.reCreateFormatCombo (this, "TIFF");
	  }
	  
	}	
}

ImageConverter.prototype.reCreateFormatCombo = function (widget, format) {
  
  var index = null;
  removeAllChildren(widget.selectFormat);   
  widget.optionFormat = new Array();  
  for(var i=0; i<widget.currentFormats.length; i++) {
    widget.optionFormat[i] = document.createElementNS( xhtmlns,'option');
    widget.optionFormat[i].text = widget.currentFormats[i];
    widget.optionFormat[i].value = i;
    if (widget.optionFormat[i].text == format) index = i;
    widget.selectFormat.appendChild( widget.optionFormat[i] );
  }
  if (index != null)
      widget.optionFormat[index].selected = true; 
}

//----------------------------------------------------------------------------------------------------------
// Colors Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateColors = function (widget, depth) {
  
  widget.selectD = document.createElementNS( xhtmlns,'select');
  widget.selectD.className = "imgcnv";
  widget.selectD.onclick = this.onDepthEvent;
  widget.selectD.widget = widget;  
  var index = null;
  var ix = 0;
  widget.optionD = new Array();
  for(var i=0; i<4; i++) {
    if ((i*8+8)!=24) {
      widget.optionD[ix] = document.createElementNS( xhtmlns,'option');
      widget.optionD[ix].text = i*8+8;
      widget.optionD[ix].value = i*8+8;
      var v = i*8+8;
      if(v.toString() == depth)
        index = i;
      widget.selectD.appendChild(widget.optionD[ix]);
      ix++; 
    }
  }
  if (index != null)
      widget.optionD[index].selected = true;

  widget.optionDD = new Array();  
  widget.selectDD = document.createElementNS( xhtmlns,'select');
  widget.selectDD.className = "imgcnv";
  widget.selectDD.style.minWidth = "100px";
  widget.optionDD[0] = document.createElementNS( xhtmlns,'option');
  widget.optionDD[0].text = "Data range";
  widget.optionDD[0].value = "d";
  widget.selectDD.appendChild(widget.optionDD[0]);
  widget.optionDD[1] = document.createElementNS( xhtmlns,'option');
  widget.optionDD[1].text = "Full range";
  widget.optionDD[1].value = "f";
  widget.optionDD[1].selected = true;
  widget.selectDD.appendChild(widget.optionDD[1]);
  widget.optionDD[2] = document.createElementNS( xhtmlns,'option');
  widget.optionDD[2].text = "Data+tolerance";
  widget.optionDD[2].value = "t";
  widget.selectDD.appendChild(widget.optionDD[2]);
  widget.optionDD[3] = document.createElementNS( xhtmlns,'option');
  widget.optionDD[3].text = "Equalized";
  widget.optionDD[3].value = "e";
  widget.selectDD.appendChild(widget.optionDD[3]);

  widget.mydiv.appendChild(document.createTextNode("Bits p/ channel:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectD);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Enhancement:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectDD);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  
  widget.setEnabled( false );  

  widget.getCallString = function () {
    if (!this.checker.checked) return ""; 
    
    return "depth=" + this.selectD.options[this.selectD.selectedIndex].text + "," + this.selectDD.options[this.selectDD.selectedIndex].value;   
  } 
}

ImageConverter.prototype.onDepthEvent = function (e) {
  this.widget.imgcnv.doEnvironmentChanged();
}


//----------------------------------------------------------------------------------------------------------
// Channels Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateChannelCombo = function (widget, nr) {

  var cb = document.createElementNS( xhtmlns,'select');
  cb.className = "imgcnv";
  var cb_option = new Array();    
  for(var i=0; i<(nr+1); i++) {
    cb_option[i] = document.createElementNS( xhtmlns,'option');
    if (i==0)
      cb_option[i].text = "Empty";
    else
      cb_option[i].text = i;
      cb_option[i].value = i+1;
    cb.appendChild(cb_option[i]);
  } 
  return cb;
}

ImageConverter.prototype.CreateChannels = function (widget, nr) {
  
  widget.size_c = nr;
  
  widget.selectCHType=document.createElementNS( xhtmlns,'select');
  widget.selectCHType.className = "imgcnv";
  widget.selectCHType.ownerWidget = widget;
  widget.selectCHType.style.minWidth = "100px"; 
  widget.selectCHType.onclick = this.OnChannelsTypeChanged;

  widget.optionCHType = new Array();    
  widget.optionCHType[0] = document.createElementNS( xhtmlns,'option');
  widget.optionCHType[0].text = "None";
  widget.optionCHType[0].value = 0;
  widget.optionCHType[1] = document.createElementNS( xhtmlns,'option');
  widget.optionCHType[1].text = "Simple";
  widget.optionCHType[1].value = 1;
  widget.optionCHType[2] = document.createElementNS( xhtmlns,'option');
  widget.optionCHType[2].text = "Advanced";
  widget.optionCHType[2].value = 2;
  widget.selectCHType.appendChild(widget.optionCHType[0]);
  widget.selectCHType.appendChild(widget.optionCHType[1]);
  widget.selectCHType.appendChild(widget.optionCHType[2]);

  widget.selectCHr = this.CreateChannelCombo(widget, nr);
  widget.selectCHg = this.CreateChannelCombo(widget, nr);
  widget.selectCHb = this.CreateChannelCombo(widget, nr); 
  
  widget.selectCHr.selectedIndex = 1;
  widget.selectCHg.selectedIndex = 1;
  widget.selectCHb.selectedIndex = 1; 
  if (nr >= 2) {
      widget.selectCHg.selectedIndex = 2; 
      widget.selectCHb.selectedIndex = 0;     
  }

  if (nr >= 3)
      widget.selectCHb.selectedIndex = 3;     
  
  widget.selectCHr.disabled = true;
  widget.selectCHg.disabled = true;
  widget.selectCHb.disabled = true;

  widget.formCHa = document.createElementNS( xhtmlns,'input');
  widget.formCHa.onkeyup = this.OnChannelsAdvancedChanged;
  widget.formCHa.type = "text";
  widget.formCHa.widget = widget;  
  widget.formCHa.name = "formCHa";
  if(nr==1)
    widget.formCHa.value = "";
  else {
    for(var i=1; i<=nr-1; i++)
        widget.formCHa.value += i + ",";
    widget.formCHa.value += nr;
  }
  widget.formCHa.disabled = true;
  widget.formCHa.className = "imgcnv_ch";

  widget.mydiv.appendChild(document.createTextNode("Channel Remapping"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectCHType);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Red:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectCHr);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Green:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectCHg);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Blue:"))
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.selectCHb);

  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(document.createTextNode("Advanced:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.formCHa);
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));  
  widget.mydiv.appendChild(document.createTextNode("(0 - is an empty channel)")); 

  //widget.formCHa.style.display = "none";
  
  widget.getCallString = function () {
    if (this.selectCHType.selectedIndex == 0) return "";
    if (this.selectCHType.selectedIndex == 1)
        return "remap=" + this.selectCHr.selectedIndex + "," + this.selectCHg.selectedIndex + "," + this.selectCHb.selectedIndex;
    if (this.selectCHType.selectedIndex == 2)
        return "&remap="+ this.formCHa.value;
    } 
}

ImageConverter.prototype.OnChannelsTypeChanged = function (e) {
  var widget = this.ownerWidget;

  if (widget.selectCHType.selectedIndex == 2) {
      widget.selectCHr.disabled = true;
      widget.selectCHg.disabled = true;
      widget.selectCHb.disabled = true;
    widget.formCHa.disabled = false;
  }
  else 
  if (widget.selectCHType.selectedIndex == 1) {
      widget.selectCHr.disabled = false;
      widget.selectCHg.disabled = false;
      widget.selectCHb.disabled = false;
    widget.formCHa.disabled = true;   
  }
  else 
  if (widget.selectCHType.selectedIndex == 0) {
      widget.selectCHr.disabled = true;
      widget.selectCHg.disabled = true;
      widget.selectCHb.disabled = true;
    widget.formCHa.disabled = true;
  }
  widget.imgcnv.doEnvironmentChanged();  
}

ImageConverter.prototype.OnChannelsAdvancedChanged = function (e) {
  this.widget.imgcnv.doEnvironmentChanged();
}


//----------------------------------------------------------------------------------------------------------
// Negative Widget
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.CreateNegative = function (widget) {
  
  widget.eselectR = document.createElementNS(xhtmlns, 'select');
  widget.eselectR.className = "imgenh";
  
  widget.eoptionR = new Array();
  widget.eoptionR[0] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[0].text = "None";
  widget.eoptionR[0].value = "0";
  widget.eoptionR[0].selected = true; 
  widget.eselectR.appendChild(widget.eoptionR[0]);
  widget.eoptionR[1] = document.createElementNS(xhtmlns, 'option');
  widget.eoptionR[1].text = "Negative";
  widget.eoptionR[1].value = "negative";
  widget.eselectR.appendChild(widget.eoptionR[1]);
  
  widget.mydiv.appendChild(document.createTextNode("Negative:"));
  widget.mydiv.appendChild(document.createElementNS( xhtmlns,'br'));
  widget.mydiv.appendChild(widget.eselectR);
  
  widget.getCallString = function () {
    if (this.eselectR.selectedIndex == 1) return "negative";
    return "";
  }
};

//----------------------------------------------------------------------------------------------------------
// End: Controls Widget for Image Convert
//----------------------------------------------------------------------------------------------------------

ImageConverter.prototype.GetImageSRC = function () {
  var requesturl = this.resourceURI + "/?view=full";
  makeRequest(requesturl, this.parseGetSRCXML, this, "get", "" );
}

ImageConverter.prototype.parseGetSRCXML = function ( imgcnv, results) {
  checkErrorXML(imgcnv, results);

  var image = results.getElementsByTagName("image")[0];
  if ( image && image.hasChildNodes() ) {
    imgcnv.imageSRC = image.getAttributeNS(null,"src");
    imgcnv.GetImageInfo();
    }
}

ImageConverter.prototype.GetImageInfo = function ( url ) {
  this.imageSRC = url;
  var requesturl = this.imageSRC + "/?info";
    makeRequest(requesturl, this.parseGetInfoXML, this, "get", "" );
}

ImageConverter.prototype.parseGetInfoXML = function ( imgcnv, results  ) {
  checkErrorXML(imgcnv, results);
  
  var tag = results.getElementsByTagName("tag");
  var numSections = tag.length;
  for (var i = 0; i < numSections; i++) {
    var element = tag.item(i);
    var name = element.getAttributeNS(null,"name");
    var type = element.getAttributeNS(null,"type");
    var value = element.getAttributeNS(null,"value");
    if (name == "width")
      imgcnv.imageInfo.size_x = parseInt(value);
    else if (name == "height")
      imgcnv.imageInfo.size_y = parseInt(value);
    else if (name == "channels")
      imgcnv.imageInfo.size_c = parseInt(value);
    else if (name == "zsize")
      imgcnv.imageInfo.size_z = parseInt(value);
    else if (name == "tsize")
      imgcnv.imageInfo.size_t = parseInt(value);
    else if (name == "depth")
      imgcnv.imageInfo.depth = parseInt(value);
    else if (name == "format")
      imgcnv.imageInfo.format = value;
  } 
  var t = imgcnv.imageInfo.size_x + "," +
      imgcnv.imageInfo.size_y + "," +
      imgcnv.imageInfo.size_c + "," +
      imgcnv.imageInfo.size_z + "," +
      imgcnv.imageInfo.size_t + "," +
      imgcnv.imageInfo.depth + "," +
      imgcnv.imageInfo.format;
  //alert(t);
  
  
  imgcnv.widgets = new Array();
   
  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Planes", false) );
  imgcnv.CreatePlanes (imgcnv.widgets[imgcnv.widgets.length-1], imgcnv.imageInfo.size_t, imgcnv.imageInfo.size_z)

  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Crop", true) );
  imgcnv.CreateCrop(imgcnv.widgets[imgcnv.widgets.length-1], imgcnv.imageInfo.size_x, imgcnv.imageInfo.size_y);
  
  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Size", true) );
  imgcnv.CreateSize(imgcnv.widgets[imgcnv.widgets.length-1], imgcnv.imageInfo.size_x, imgcnv.imageInfo.size_y);
  
  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Rotate", false) );
  imgcnv.CreateRotate( imgcnv.widgets[imgcnv.widgets.length-1] );

  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Colors", true) );
  imgcnv.CreateColors( imgcnv.widgets[imgcnv.widgets.length-1], imgcnv.imageInfo.depth ); 
  
  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Channels", false) );
  imgcnv.CreateChannels( imgcnv.widgets[imgcnv.widgets.length-1], imgcnv.imageInfo.size_c );
  
  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Negative", false) );
  imgcnv.CreateNegative( imgcnv.widgets[imgcnv.widgets.length-1] );  

  imgcnv.widgets.push( new ImageConverterWidget(imgcnv, "Format", false) );
  imgcnv.CreateFormat( imgcnv.widgets[imgcnv.widgets.length-1], imgcnv.imageInfo.format );
  
  imgcnv.doEnvironmentChanged();
  
  imgcnv.CreateDIVClear(imgcnv.maindiv);
  imgcnv.CreateButton(imgcnv.maindiv);
}

ImageConverter.prototype.CreateDIVClear = function (divP) {
    this.div_clear = document.createElementNS( xhtmlns,'div');
    this.div_clear.className = "imgcnv_clear";
    divP.appendChild(this.div_clear);
}

ImageConverter.prototype.ConvertRun = function () {
  var requestQuery = null;
  
  //alert( this.getRequestQuery() );
  
  requestQuery = this.imageSRC + "/?";
  requestQuery += this.getRequestQuery(); 
  
  window.location = requestQuery;
}

ImageConverter.prototype.CreateButton = function (divP) {
  this.buttonConvert = document.createElementNS( xhtmlns, 'button');
  //this.buttonConvert.type = "submit";
  this.buttonConvert.value = "Download Image";
  this.buttonConvert.innerHTML = "Download Image";  
  this.buttonConvert.onclick = createMethodReference(this, "ConvertRun");
    divP.appendChild(this.buttonConvert);
}

// ]]>
