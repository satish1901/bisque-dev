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

function get_string_from_URL (url) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open ("GET", url, false);
    xmlhttp.send ();
    return xmlhttp.responseText;
}


// http://paulirish.com/2011/requestanimationframe-for-smart-animating/
// http://my.opera.com/emoller/blog/2011/12/20/requestanimationframe-for-smart-er-animating

// requestAnimationFrame polyfill by Erik Möller
// fixes from Paul Irish and Tino Zijdel

(function() {
    var lastTime = 0;
    var vendors = ['ms', 'moz', 'webkit', 'o'];
    for(var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
        window.requestAnimationFrame = window[vendors[x]+'RequestAnimationFrame'];
        window.cancelAnimationFrame = window[vendors[x]+'CancelAnimationFrame']
            || window[vendors[x]+'CancelRequestAnimationFrame'];
    }

    if (!window.requestAnimationFrame)
        window.requestAnimationFrame = function(callback, element) {
            var currTime = new Date().getTime();
            var timeToCall = Math.max(0, 16 - (currTime - lastTime));
            var id = window.setTimeout(function() { callback(currTime + timeToCall); },
				                       timeToCall);
            lastTime = currTime + timeToCall;
            return id;
        };

    if (!window.cancelAnimationFrame)
        window.cancelAnimationFrame = function(id) {
            clearTimeout(id);
        };
}());


Ext.define('BQ.viewer.Volume.ThreejsPanel', {
    //extend: 'Ext.container.Container',
    extend : 'Ext.Component',
    alias : 'widget.threejs_panel',
    border : 0,
    frame : false,
   // layout : 'fit',

    autoEl: {
        tag: 'canvas',
        cls: 'threejsComponent',
    },

    listeners: {
        scope: this,
        /*
        el:{
            mousedown:  this.onMouseDown,
            mouseup: this.onMouseUp,
            DOMMouseScroll:this.onMouseWheel,
            mousewheel: this.onMouseWheel,
            mousemove:this.onMouseMove,
        }


        //mousedown: this.onMouseDown,


        mousedown: {
            element: 'el',
            fn: this.onMouseDown
        },
        mouseup: {
            element: 'el',
            fn: this.onMouseUp
        },
        DOMMouseScroll: {
            element: 'el',
            fn : this.onMouseWheel,
        },
        mousewheel: {
            element: 'el',
            fn : this.onMouseWheel,
        },
        mousemove: {
            element: 'el',
            fn : this.onMouseMove,
        },
        */
    },

    initComponent : function() {
        this.on('resize', this.onresize);
	    this.zooming     = false;
        this.selectLight = false;
	    this.animate_funcs = new Array();
        this.mousedown = false;
        this.needs_render = true;
        this.callParent();

    },

    initScene : function(uniforms) {
        //this.fireEvent("initscene");
    },

    afterRender : function() {
        this.callParent();
    },

    afterFirstLayout : function() {
        var me = this;

        var thisDom = this.getEl().dom;

        this.renderer = new THREE.WebGLRenderer({
            canvas: thisDom,
            preserveDrawingBuffer : true,
            clearAlpha: 1,
            sortObjects: true,
        });
        this.renderer.setClearColor(0xC0C0C0, 1);
        var aspect = this.getWidth() / this.getHeight();
        this.fov = 40;
        this.camera = new THREE.PerspectiveCamera(this.fov, aspect, .01, 20);

        //this.controls = new THREE.TrackballControls(this.camera, thisDom);
        this.controls = new THREE.OrbitControls(this.camera, thisDom);

        this.controls.noRoll = true;
        this.projector = new THREE.Projector();

        this.camera.position.z = 5.0;
        this.getEl().on({
            scope : this,
            mouseup : this.onMouseUp,
            mousedown : this.onMouseDown,
            mousemove : this.onMouseMove,
            mousewheel: this.onMouseWheel,
            DOMMouseScrool: this.onMouseWheel,
        });

        //this.anaglyph = new THREE.AnaglyphEffect( this.renderer );
		//this.anaglyph.setSize( this.getWidth(), this.getHeight() );

        this.fireEvent('loaded', this);
        this.callParent();
        this.renderer.render(this.scene, this.camera);
    },

    getPixelWidth : function(){
        return this.renderer.context.canvas.width;
        //return this.getWidth();
    },

    getPixelHeight : function(){
        return this.renderer.context.canvas.height;
        //return this.getHeight();
    },

    onMouseWheel : function(event) {
	    this.zooming = true;
        this.mousedown = true;
        this.needs_render = true;
        var me = this;

        setTimeout(function() {
	        me.zooming = false;
	        me.mousedown = false;
            me.controls.enabled = true;
        }, 200);
        this.fireEvent('mousewheel', event);
    },

    onMouseDown : function(event) {
        this.mousedown = true;
        this.zooming = false;
		this.controls.noRotate = false;
		this.controls.noPan = false;

        this.controls.update();
        var me = this;
	    if(event.button == 1){
	        this.zooming = true;
	    }
        this.needs_render = true;
        this.fireEvent('mousedown', event);
    },

    onMouseUp : function(event) {
        this.controls.enabled = true;
        this.mousedown   = false;
        this.needs_render = true;
        this.fireEvent('mousemove', event);
    },

    onMouseMove : function(event){
        this.fireEvent('mousemove', event);
    },

    onresize : function(comp, w, h, ow, oh, eOpts) {
        //console.log(args);
        var aspect = w / h;
        this.camera.aspect = aspect;
        this.camera.updateProjectionMatrix();

        this.renderer.setSize(w, h);
        //this.anaglyph.setSize(w, h);
        this.mousedown = false;
    },

    rerender : function() {
        this.needs_render = true;
    },

    doAnimate : function() {
        var me = this;
	    if(this.onAnimate)
	        this.onAnimate();
        if(this.needs_render){
            //if(this.render_override)
                //this.onAnimateOverride();
            //else
            for(var i = 0; i < this.animate_funcs.length; i++){
                this.animate_funcs[i]();
            }
            this.renderer.render(this.scene, this.camera);
            this.fireEvent('render', this);
            //this.anaglyph.render(this.scene, this.camera);
        }

        this.controls.update();
        requestAnimationFrame(function() {
            me.doAnimate()
        });
    },

});


Ext.define('BQ.viewer.Volume.Axis', {
    //extend: 'Ext.container.Container',
    extend : 'BQ.viewer.Volume.ThreejsPanel',
    alias : 'widget.axis_panel',
    border : 0,
    frame : false,

    initComponent : function() {
        this.callParent();
    },

    initScene : function(uniforms) {
        //this.fireEvent("initscene");
    },

    afterRender : function() {
        this.callParent();
    },

    afterFirstLayout : function() {
        var me = this;
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
        this.callParent();
        this.camera = new THREE.OrthographicCamera( -this.getWidth()/100, this.getWidth()/100,
                                                    this.getHeight()/100, -this.getHeight()/100, 1, 20 );
        this.camera.position.set(0,0,10);
        //this.camera.fov = 10;
        this.renderer.render(this.scene, this.camera);
    },

    doAnimate : function() {
        var me = this;
        this.axisHelper.rotation.setFromRotationMatrix(this.followingCam.matrixWorldInverse);
        this.cubeMesh.rotation.setFromRotationMatrix(this.followingCam.matrixWorldInverse);

        this.callParent();
    },
});