function ScaleBar ( parent, new_pix_size, units ) {
	this.parent = parent;
	this.dragging = false;
	this.pix_phys_size = 0;
	this.bar_size_in_pix = 0;
	this.units = units || 'um';

	this.widget = document.createElementNS(xhtmlns, 'div');
	this.widget.className = 'scalebar';
    this.widget.setAttributeNS (null, 'id', 'scalebar_widget');

	this.bar = document.createElementNS(xhtmlns, 'div');
    this.bar.setAttributeNS (null, 'id', 'scalebar_bar');
	this.bar.innerHTML = "&#xA0;";
    this.bar.style.width = "100%";
    this.bar.style.height = "5px";

	this.caption = document.createElementNS(xhtmlns, 'div');
    this.caption.setAttributeNS (null, 'id', 'scalebar_caption');
	this.caption.innerHTML = '0.00 '+this.units;

	this.setValue( new_pix_size );

	this.widget.appendChild(this.bar);
	this.widget.appendChild(this.caption);
	this.parent.appendChild(this.widget);
}

ScaleBar.prototype.setPos = function ( x,y ) {
	this.widget.style.left = x + "px";
	this.widget.style.top = y + "px";
};

ScaleBar.prototype.setValue = function ( val ) {
    if (this.pix_phys_size==val && this.bar_size_in_pix==this.bar.clientWidth) return;

    this.pix_phys_size = val;
    this.bar_size_in_pix = this.bar.clientWidth;
    var bar_size_in_um  = this.bar_size_in_pix * this.pix_phys_size;
    var capt = '' + bar_size_in_um.toFixed(4) + ' ' + this.units;

    this.caption.innerHTML = capt;
};

