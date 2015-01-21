// <![CDATA[

function ScaleBar(parent, new_pix_size) {
	this.parent = parent;

	//default parameters 
	me = this;

	//this.dragging = false;
	this.pix_phys_size = 0;
	this.bar_size_in_pix = 0;		
	this.pressed = false; // set if move state is on
	
	this.offsetX = null;
	this.offsetY = null;
	this.color = 'gray';
	this.hideValue = false;
	this.hideBackground = false;
	this.defaultColor = '#FFFFFF';
	this.width_min = 100;
	this.height_min = 38;
	this.opacity = 0.6;
	this.mouseover = false;
	
	//scalebar div
	this.widget = document.createElementNS(xhtmlns, 'div');
	this.widget.className = 'scalebar';
	this.widget.setAttributeNS(null, 'id', 'scalebar_widget');
	this.widget.style.position = "absolute";
	//this.widget.style.backgroundColor = "#222222";
	this.widget.style.zIndex = 30;
	this.widget.style.backgroundColor = "rgba(34,34,34,"+this.opacity+")";
	/*this.widget.style.opacity = 0.6;*/
	
	//scalebar bar div
	this.bar = document.createElementNS(xhtmlns, 'div');
	this.bar.setAttributeNS(null, 'id', 'scalebar_bar');		
	this.bar.innerHTML = "&#xA0;";
	this.bar.style.width = "100%";
	this.bar.style.height = "30%";
	this.bar.style.opacity = this.opacity;
	this.bar.style.backgroundColor = this.defaultColor
	this.bar.style.zIndex = 29;
	
	//scalebar caption div
	this.caption = document.createElementNS(xhtmlns, 'div');
	this.caption.setAttributeNS(null, 'id', 'scalebar_caption');
	this.caption.innerHTML = '0.00 um';
	this.caption.style.height = "70%";
	this.caption.style.overflow = "hidden";
	this.caption.style.zIndex = 28;
	this.caption.style.opacity = this.opacity;
	this.caption.style.color = this.defaultColor;	
	this.setPixSize(new_pix_size);
	this.resetValue()

	//scalebar selectionPanel div
	//panel over the scalebar so no other elements are selected
	this.selectionPanel = document.createElementNS(xhtmlns, 'div');
	this.selectionPanel.setAttributeNS (null, 'id', 'scalebar_selectionPanel');	
	this.selectionPanel.style.position = "absolute";
	this.selectionPanel.style.top = "0px";
	this.selectionPanel.style.left = "0px";
	this.selectionPanel.style.width = "100%";
	this.selectionPanel.style.height = "100%";
	this.selectionPanel.style.zIndex = 31;
	
	//rescale button div
	this.editButton = document.createElementNS(xhtmlns, 'div');
	this.editButton.setAttributeNS (null, 'id', 'scalebar_editButton');
	this.editButton.setAttributeNS(null, 'title', 'edit');
	this.editButton.style.position = "absolute";
	this.editButton.style.top = "2px";
	this.editButton.style.left = "2px";
	this.editButton.style.width = "31px";
	this.editButton.style.height = "31px";
	this.editButton.style.zIndex = 32;
	this.editButton.style.opacity = 1;
	this.editButton.style.visibility = "hidden"	;
	this.editButton.toggle = false;
	
	//rescale button div
	this.rescaleButton = document.createElementNS(xhtmlns, 'div');
	this.rescaleButton.setAttributeNS (null, 'id', 'scalebar_rescaleButton');
	this.rescaleButton.setAttributeNS(null, 'title', 'resize');
	this.rescaleButton.style.position = "absolute";
	this.rescaleButton.style.bottom = "0px";
	this.rescaleButton.style.right = "0px";
	this.rescaleButton.style.width = "20px";
	this.rescaleButton.style.height = "20px";
	this.rescaleButton.style.zIndex = 32;
	this.rescaleButton.style.opacity = 1;
	this.rescaleButton.style.cursor = 'nw-resize';
	this.rescaleButton.style.visibility = "hidden";
	
	this.rescaleButton.pressed = false; //set if resize state is on

	// EVENTS
	
	// show buttons (mouse over the scale bar)
	this.widget.addEventListener("mouseover", function(e) {
		me.rescaleButton.style.visibility = "visible";
		me.editButton.style.visibility = "visible";
		//me.selectionPanel.style.border = "1px solid white";
		me.bar.style.opacity = .3;
		me.editButton.style.opacity = 1;
		me.rescaleButton.style.opacity = 1;
		me.caption.style.opacity = .3; 
		me.mouseover = true;
	}, false);
	
	this.widget.addEventListener("mouseout", function(e) {
		if (!me.rescaleButton.pressed) {me.rescaleButton.style.visibility = "hidden";}
		me.editButton.style.visibility = "hidden";
		//me.selectionPanel.style.border = "";
		me.bar.style.opacity = me.opacity;
		me.caption.style.opacity = me.opacity; 
		me.mouseover = false;
	}, false);
	
	// edit button
	this.editButton.addEventListener("click", function(e) {
		if(me.editor) {
			me.editButton.toggle =!  me.editButton.toggle;
			if (me.editButton.toggle) 
				me.editor.show();
			else
				me.editor.hide();
		} else {
			me.editButton.toggle = true;
			me.createEditor();
			me.editor.show();
		}
	}, false);
	
	// rescale button
	this.rescaleButton.addEventListener("mousedown", function(e) {
		if (!me.rescaleButton.pressed ) {
			var mouse_x = e.clientX || e.pageX;
			var mouse_y = e.clientY || e.pageY;
			
			var parent_bound = me.parent.getBoundingClientRect();
			var widget_bound = me.widget.getBoundingClientRect();
			var rescale_bound = me.rescaleButton.getBoundingClientRect();
			me.rescaleButton.offsetX = rescale_bound.right - mouse_x;
			me.rescaleButton.offsetY = rescale_bound.bottom - mouse_y;
			
			//mouse offset from the top left corner of the object
			me.rescaleButton.initX = widget_bound.left; //+ parent_bound.left;
			me.rescaleButton.initY = widget_bound.top; //+ parent_bound.top;

			me.rescaleButton.pressed = true;
		}
	}, false);
	
	window.addEventListener("mouseup", function(e) {
		if (me.rescaleButton.pressed) {
			var mouse_x = e.clientX || e.pageX;
			var mouse_y = e.clientY || e.pageY;
			me.rescaleButton.pressed = false;
			if (!me.mouseover) {me.rescaleButton.style.visibility = "hidden";}
		}
	}, true);
	
	window.addEventListener("mousemove", function(e) {
		if (me.rescaleButton.pressed) {
			me.blockPropagation(e);
			var mouse_x = e.clientX || e.pageX;
			var mouse_y = e.clientY || e.pageY;
			var width = (mouse_x + me.rescaleButton.offsetX) - me.rescaleButton.initX;
			var height = (mouse_y + me.rescaleButton.offsetY) - me.rescaleButton.initY;
			me.setConstrainedSize(height, width);
		}
	}, true);
	
	// move panel
	this.selectionPanel.addEventListener("mousedown", function(e) {
		if (!me.pressed) {
			var mouse_x = e.clientX || e.pageX; 
			var mouse_y = e.clientY || e.pageY;
			
			var parent_bound = me.parent.getBoundingClientRect()
			//mouse offset from the top left corner of the object
			me.offsetX = e.offsetX + parent_bound.left;
			me.offsetY = e.offsetY + parent_bound.top;

			//this.parent.addEventListener("mouseleave", this.mouseUpBound, false);
			me.selectionPanel.style.cursor = "move";
			me.pressed = true;
		}
	}, false);
	
	window.addEventListener("mouseup", function(e) {
		if (me.pressed) {
			me.selectionPanel.style.cursor = "pointer";
			me.pressed = false;
		}
	}, true);
	
	window.addEventListener("mousemove", function(e) {
		if (me.pressed) {
			me.blockPropagation(e);
			var mouse_x = e.clientX || e.pageX;
			var mouse_y = e.clientY || e.pageY;
			var x = mouse_x - me.offsetX;
			var y = mouse_y - me.offsetY;
			me.setConstrainedPos(x,y);
		}
	}, true);
	
	this.widget.appendChild(this.rescaleButton);
	this.widget.appendChild(this.editButton);
	this.widget.appendChild(this.selectionPanel);
	this.widget.appendChild(this.bar);
	this.widget.appendChild(this.caption);
	this.parent.appendChild(this.widget);
	
}


ScaleBar.prototype.createEditor = function() {
	//scalebar editor
	me = this;
	if (!this.editor) {
		this.editor = Ext.create('Ext.tip.ToolTip', {
			target: this.editButton,
            anchor: 'top',
            anchorToTarget: true,
			closable: true,
			//height: 150,
			width: 300,
			shadow: false,
			cls: 'bq-viewer-menu',
			closeAction: 'hide',
			autoHide: false,
			layout: {
				type: 'vbox',
				align : 'stretch',
			},
		});
		
		var editorColor = this.editor.add({
			xtype:'fieldcontainer',
			padding : '0px 15px 0px 15px',
			fieldLabel: 'Text Color',
		});
		
		this.editorColorButton = editorColor.add({
			xtype: 'button',
			width: '100%',
			//cls: 'bq-form-color',
			style: {
				background: this.defaultColor,
				border: '1px solid #ffffff',
			}
		});
		
		this.editorColorButton.on('click', function(e) {
			this.colorToolTip = Ext.create('Ext.tip.ToolTip', {
				target: this.editorColorButton.getEl(),
				anchor: 'right',
				anchorToTarget: true,
				cls: 'bq-viewer-tip',
				width :  540,
				minWidth: 540,
				minHeight: 85,
				layout: 'fit',
				autoHide: false,
				shadow: false,
				items: [{
					xtype: 'bqcolorpicker',
					listeners: {
						scope: this,
						select: function(field, selColor) {
							this.caption.style.color = "#"+selColor;
							this.bar.style.backgroundColor = "#"+selColor;
							this.color = selColor;
							this.editorColorButton.getEl().setStyle('background','#'+selColor);
						},
					},
					colors : [ 'FFFFFF', // trasparent
							   'FF0000', '00FF00', '0000FF', // RGB
							   '000000', // GRAY
							   '00FFFF', // CYAN
							   'FF00FF', // MAGENTA
							   'FFFF00', // YELLOW
							   'FF6600'  // custom orange
					],                    
					titles : [ 'Default', // trasparent
							   'Red', 'Green', 'Blue', // RGB
							   'Black', //GRAY
							   'Cyan', 'Magenta', 'Yellow', // YMC
							   'Custom' // custom orange
					],                    
				}],
			}).show()
		}, this);
		
		this.editor.add({
			xtype: 'slider',
			text: 'Opacity',
			width: '%100',
			fieldLabel: 'Opacity',
			value: 60,
			padding : '0px 15px 0px 0px',
			increment: 10,
			minValue: 20,
			maxValue: 100,
			listeners: {
				scope: this,
				change: function(el, value) {
					this.opacity = value/100;
					this.bar.style.opacity = this.opacity;
					this.caption.style.opacity = this.opacity;
					this.widget.style.backgroundColor = "rgba(34,34,34,"+this.opacity+")";
				}
			}
		});
		
		this.editor.add({ // toggle button hide value
			xtype: 'checkbox',
			checked: false,
			fieldLabel: 'Hide Value',
			//padding : '10px',
			width: '100%',
			listeners : {
				scope: this,
				change : function(el, newValue, oldValue) {
					this.hideValue = newValue;
					if (this.hideValue) {
						this.caption.style.visibility = "hidden";
					}
					if (!this.hideValue) {
						this.caption.style.visibility = "visible";
					}
				}
			},
		});
		
		this.editor.add({
			xtype: 'checkbox',
			checked: false,
			fieldLabel: 'Hide Background',
			//padding : '10px',
			listeners : {
				scope: this,
				change : function(el, newValue, oldValue) {
					this.hideBackground = newValue;
					if (!this.hideBackground) {
						this.widget.style.visibility = "visible";
						this.bar.style.visibility = "visible";
						this.selectionPanel.style.visibility = "visible";
					}
					if (this.hideBackground)  {
						this.widget.style.visibility = "hidden";
						this.bar.style.visibility = "visible";
						this.selectionPanel.style.visibility = "visible";
						if (!this.hideValue) this.caption.style.visibility = "visible";
					}
				}
			},
		});
	}
}

//sets the size of the text and the bar
//min size is defined , max is the size of the window
ScaleBar.prototype.setConstrainedSize = function( height, width ) {

	var parent_bound = me.parent.getBoundingClientRect();
	var widget_bound = me.widget.getBoundingClientRect();

	if (this.height_min >= height) {}
	else if (parent_bound.bottom <= widget_bound.top + height) {} // stops when an edge is hit
	else {
		this.widget.style.height = height+"px";
		var fontSizeRatio = height/this.height_min *100;
		this.caption.style.fontSize = fontSizeRatio + "%";
	}
	
	if (this.width_min >= width) {}
	else if (parent_bound.right <= widget_bound.left + width) {} // stops when an edge is hit
	else {
		this.widget.style.width = width+"px";
		this.resetValue();
	}
}

ScaleBar.prototype.setPixSize = function(val) {
	this.pix_phys_size = val;
}

ScaleBar.prototype.resetValue = function() {
	var bar_size_in_um = this.pix_phys_size * this.bar.clientWidth;
	var capt = '' + bar_size_in_um.toFixed(4) + ' um';
	this.caption.innerHTML = capt;
}

//taken from panojs
ScaleBar.prototype.blockPropagation = function (e) {
    if (e.stopPropagation) e.stopPropagation(); // DOM Level 2
    else e.cancelBubble = true;                 // IE
    if (e.preventDefault) e.preventDefault(); // prevent image dragging
    else e.returnValue = false;
}

//set position within the parent
ScaleBar.prototype.setConstrainedPos = function (x, y) {

	parent_bound = this.parent.getBoundingClientRect()
	widget_bound = this.widget.getBoundingClientRect()
	
	//set y position
	if (0 >= y) {
		this.widget.style.top = 0 + "px";
	} else if  (parent_bound.height <= y + widget_bound.height){
		this.widget.style.top = parent_bound.height - widget_bound.height + "px";
	} else {
		this.widget.style.top = y + "px";
	}
	
	//set x position
	if (0 >= x) {
		this.widget.style.left = 0 + "px";
	} else if ( parent_bound.width <= x + widget_bound.width) {
		this.widget.style.left = parent_bound.width - widget_bound.width + "px";
	} else {
		this.widget.style.left = x + "px";
	}
}

//produces a canvas image of the element
ScaleBar.prototype.renderCanvas = function () {
	
	//get styles
	var widget_style = window.getComputedStyle(this.widget);
	var caption_style = window.getComputedStyle(this.caption);
	
	//get bounds
	var widget_bound = this.widget.getBoundingClientRect();
	var bar_bound = this.bar.getBoundingClientRect();
	var caption_bound = this.caption.getBoundingClientRect();
	
	//create canvas element
	var canvas_scalebar = document.createElement('canvas');
	canvas_scalebar.setAttributeNS(null, 'id', 'canvas_scalebar');
	canvas_scalebar.height = widget_bound.height;
	canvas_scalebar.width = widget_bound.width;
	var ctx_scalebar = canvas_scalebar.getContext("2d");

	
	//start blank template
	ctx_scalebar.fillStyle = "rgba(0, 0, 0, 0)";
	ctx_scalebar.fillRect(0, 0, canvas_scalebar.width, canvas_scalebar.height);
	
	// draw background
	if (!this.hideBackground) {
		ctx_scalebar.fillStyle = widget_style.backgroundColor; //this.widget.style.backgroundColor;
		var x = 0;
		var y = 0;
		var width = widget_bound.width;
		var height = widget_bound.height;
		var radius = 5;
		
		//draws round edges
		ctx_scalebar.beginPath();
		ctx_scalebar.moveTo(x + radius, y);
		ctx_scalebar.lineTo(x + width - radius, y);
		ctx_scalebar.quadraticCurveTo(x + width, y, x + width, y + radius);
		ctx_scalebar.lineTo(x + width, y + height - radius);
		ctx_scalebar.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
		ctx_scalebar.lineTo(x + radius, y + height);
		ctx_scalebar.quadraticCurveTo(x, y + height, x, y + height - radius);
		ctx_scalebar.lineTo(x, y + radius);
		ctx_scalebar.quadraticCurveTo(x, y, x + radius, y);
		ctx_scalebar.closePath();
		ctx_scalebar.fill();
	}
	
	//draw bar
	ctx_scalebar.fillStyle = this.bar.style.backgroundColor;
	ctx_scalebar.fillRect(bar_bound.left - widget_bound.left, bar_bound.top - widget_bound.top, bar_bound.width, bar_bound.height);
	
	//draw text
	if (!this.hideValue) {
		ctx_scalebar.textBaseline = 'top';
		ctx_scalebar.font = caption_style.font;
		ctx_scalebar.fillText(this.caption.innerHTML, caption_bound.left - widget_bound.left, caption_bound.top - widget_bound.top);
	}
	
	return canvas_scalebar
		
}
// ]]>
