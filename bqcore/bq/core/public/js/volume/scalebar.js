/*******************************************************************************

@author John Delaney


 *******************************************************************************/

/*
LICENSE

Center for Bio-Image Informatics, University of California at Santa Barbara

Copyright (c) 2007-2014 by the Regents of the University of California
All rights reserved

Redistribution and use in source and binary forms, in whole or in parts, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright
notice, this list of conditions, and the following disclaimer.

Redistributions in binary form must reproduce the above copyright
notice, this list of conditions, and the following disclaimer in
the documentation and/or other materials provided with the
distribution.

Use or redistribution must display the attribution with the logo
or project name and the project URL link in a location commonly
visible by the end users, unless specifically permitted by the
license holders.

THIS SOFTWARE IS PROVIDED BY THE REGENTS OF THE UNIVERSITY OF CALIFORNIA ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OF THE UNIVERSITY OF CALIFORNIA OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

/*
ViewerPlugin.prototype.updatePosition = function (){
};

ViewerPlugin.prototype.setSize = function (size)
{
    if (size.height)
        this.imagediv.style.height = size.height+"px";
    if (size.width)
        this.imagediv.style.width = size.width+"px";
};
*/

function VolScaleBar ( parent, new_pix_size ) {
	this.parent = parent;
	this.dragging = false;
	this.pix_phys_size = 0;
	this.bar_size_in_pix = 0;


	this.bar = document.createElementNS(xhtmlns, 'div');
    this.bar.setAttributeNS (null, 'id', 'scalebar_bar_vol');
	this.bar.innerHTML = "&#xA0;";
    this.bar.style.width = "100%";
    this.bar.style.height = "5px";
    this.bar.style.background =  '#FFFFFF';
	this.caption = document.createElementNS(xhtmlns, 'div');
    this.caption.setAttributeNS (null, 'id', 'scalebar_caption_vol');
	this.caption.innerHTML = '0.00 um';

	this.setValue( new_pix_size );

	this.parent.appendChild(this.bar);
	this.parent.appendChild(this.caption);
	//this.parent.appendChild(this.widget);
}

VolScaleBar.prototype.setPos = function ( x,y ) {
	this.widget.style.left = x + "px";
	this.widget.style.top = y + "px";
}

VolScaleBar.prototype.setValue = function ( val ) {
  if (this.pix_phys_size==val && this.bar_size_in_pix==this.bar.clientWidth) return;

  this.pix_phys_size = val;
  this.bar_size_in_pix = this.bar.clientWidth;
  var bar_size_in_um  = this.bar_size_in_pix * this.pix_phys_size;
  var capt = '' + bar_size_in_um.toFixed(4) + ' um';

  this.caption.innerHTML = capt;
}

function VolScaleBarTool (volume){
    this.base = renderingTool;
    this.base (volume, null);
}

VolScaleBarTool.prototype = new renderingTool();

VolScaleBarTool.prototype.addButton = function () {
    //blank since we don't actually add anything
};

VolScaleBarTool.prototype.initControls = function () {
    var me = this;
    var thisDom = this.volume.getEl().dom;

    this.volume.on('loaded', function () {
        if(me.scalePanel) return;
        var dim = me.volume.dim;
        var imgphys = me.volume.phys;

        if (imgphys==null || imgphys.pixel_size[0]==undefined || imgphys.pixel_size[0]==0.0000) {
            return;
        }

        me.scalePanel = Ext.create('Ext.panel.Panel', {
		    collapsible : false,
		    header : false,
		    renderTo : thisDom,
            layout : 'fit',
		    cls : 'vol-scalebar',

            listeners : {
                afterlayout: function(){

                    me.parentdiv = this.getEl().dom;
                    me.volume.addFade(this);
                    me.updateImage();
                }
            }
	    });
        me.volume.canvas3D.on({
            scope: me,
            render: me.updatePosition
        });
        //me.updateImage();


    });
};

VolScaleBarTool.prototype.updateImage = function () {
    //var view = this.viewer.current_view;
    var dim = this.volume.dim;
    var imgphys = this.volume.phys;

    if (imgphys==null || imgphys.pixel_size[0]==undefined || imgphys.pixel_size[0]==0.0000) {
      if (this.scalebar != null) {
        this.div.removeChild (this.scalebar.widget);
        delete this.scalebar;
      }
      this.scalebar = null;
      return;
    }

    var surf = this.parentdiv;
    //if (this.viewer.viewer_controls_surface) surf = this.viewer.viewer_controls_surface;

    if (this.scalebar == null)
        this.scalebar = new VolScaleBar ( surf, imgphys.pixel_size[0] );
    //this.scalebar.setValue( imgphys.pixel_size[0]/view.scale );
    this.scalebar.setValue( imgphys.pixel_size[0]);
};

VolScaleBarTool.prototype.updatePosition = function () {
    if (this.scalebar == null) return;
    var camPos = this.volume.canvas3D.camera.position;
    var fov = this.volume.canvas3D.fov;
    var l = camPos.length();
    var d = 2.0*l/Math.tan(fov/2);
    var imgphys = this.volume.phys;

    this.scalebar.setValue( d*imgphys.pixel_size[0] );
};

/*******************************************************************************
Temp home for the axis tool
*******************************************************************************/

function VolAxisTool (volume){
    this.base = renderingTool;
    this.base (volume, null);
}

VolAxisTool.prototype = new renderingTool();

VolAxisTool.prototype.addButton = function () {
    //blank since we don't actually add anything
};

VolAxisTool.prototype.initControls = function () {
    var me = this;
    var thisDom = this.volume.getEl().dom;

    this.Panel = Ext.create('Ext.container.Container', {
		collapsible : false,
		header : false,
		renderTo : thisDom,
        layout : 'fit',
		cls : 'vol-axis',
        items: [{xtype: 'threejs_panel',
                 itemId: 'axis_panel',
                 doAnimate : function() {
                     var me = this;
                     this.renderer.render(this.scene, this.camera);
                     this.axisHelper.rotation.setFromRotationMatrix(this.followingCam.matrixWorldInverse);
                     this.cubeMesh.rotation.setFromRotationMatrix(this.followingCam.matrixWorldInverse);
                     requestAnimationFrame(function() {
                         me.doAnimate()
                     });
                 },

                 buildScene: function() {
                     var thisDom = this.getEl().dom;

                     this.scene = new THREE.Scene();
		             var material = new THREE.MeshBasicMaterial({
			             color : 0xffff00
		             });

                     this.cube = new THREE.CubeGeometry(0.25, 0.25, 0.25);
		             this.cubeMesh = new THREE.Mesh(this.cube, material);
		             this.scene.add(this.cubeMesh);

                     this.axisHelper = new THREE.AxisHelper( 1 );
                     this.scene.add( this.axisHelper );
                     this.camera = new THREE.OrthographicCamera( -this.getWidth()/100, this.getWidth()/100,
                                                                 this.getHeight()/100, -this.getHeight()/100, 1, 20 );
                     //this.setClearColor(0xC0C0C0, 0.0);
                     //this.setClearColor(0xC0C0C0,1.0);
                     this.renderer.setClearColor(0x808080,0.001);

                     this.camera.position.set(0,0,10);
                 }

                }],
        listeners : {
            afterlayout: function(){
                var canvas = this.queryById('axis_panel');
                canvas.followingCam = me.volume.canvas3D.camera;
                canvas.doAnimate();
                me.parentdiv = this.getEl().dom;
                me.volume.addFade(this);
            }
        }
	});

    this.volume.on('loaded', function () {
        me.volume.canvas3D.on({
            scope: me,
            //render: me.updatePosition
        });
        //me.updateImage();


    });
};
