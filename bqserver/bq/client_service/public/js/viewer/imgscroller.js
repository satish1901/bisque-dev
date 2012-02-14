// Add scroll bars to images that are too large to fit 
function ImgScroller (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.mouse_click_x = 0;
    this.mouse_click_y = 0;
    this.mouse_pressed = false;	    
}
ImgScroller.prototype = new ViewerPlugin();

ImgScroller.prototype.create = function (parent) {
    this.parent = parent;
    this.div  = document.createElementNS(xhtmlns, "div");
    this.div.className = "imgview_scroller";
    this.parent.appendChild(this.div);
    this.div.onmousemove = callback (this, 'onmousemove');
    this.div.onmouseup = callback (this, 'onmouseup');        
    this.div.onmousedown = callback (this, 'onmousedown');
    return this.div;
}

ImgScroller.prototype.newImage = function () {
}

ImgScroller.prototype.updateImage = function () {
    var view = this.viewer.current_view;
    var view_top = this.parent.offsetTop;
    var view_left = this.parent.offsetLeft; 
    var view_height = Math.min( view.height, document.clientHeight-50 );     
    this.div.style.height = view_height + "px";                
}

ImgScroller.prototype.onmousedown = function (e) {
    if (!e) e = window.event;  // IE event model
    if (e == null) return;
    this.mouse_click_x = e.clientX;
    this.mouse_click_y = e.clientY;
    this.mouse_pressed = true;	
    
    //e.preventDefault();  
    if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
    else e.cancelBubble = true;                 // IE    
    
    if (this.mouse_pressed) {
        this.div.style.cursor = 'move';
    } else {
        this.div.style.cursor = 'default';
    }
}

ImgScroller.prototype.onmouseup = function (e) {
    if (!e) e = window.event;  // IE event model  
    if (e == null) return; 
       
    //e.preventDefault();  
    if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
    else e.cancelBubble = true;                 // IE    
    
    this.mouse_click_x = 0;
    this.mouse_click_y = 0;
    this.mouse_pressed = false;	 
    this.div.style.cursor = 'default';	  
}

ImgScroller.prototype.onmousemove = function (e) {
    if (!e) e = window.event;  // IE event model  
    if (e == null) return;
    if (!this.mouse_pressed) return;
    
    //e.preventDefault();  
    if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
    else e.cancelBubble = true;                 // IE        
  	
	  var dx = this.mouse_click_x - e.clientX;
    var dy = this.mouse_click_y - e.clientY;
    this.div.scrollTop = this.div.scrollTop + dy;
    this.div.scrollLeft = this.div.scrollLeft + dx;		
	
    this.mouse_click_x = e.clientX;
    this.mouse_click_y = e.clientY;		
}


