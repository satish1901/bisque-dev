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
    layout : 'fit',
    cls : 'bq-three-container',

    constructor : function(config) {
        this.addEvents({
            'loaded' : true,
            'changed' : true,
        });

        this.callParent(arguments);
        return this;
    },

    initComponent : function() {
        this.addListener('resize', this.onresize, this);
	    this.zooming     = false;
        this.selectLight = false;
	    this.callParent();

    },

    initScene : function(uniforms) {

    },


    afterRender : function() {
        this.callParent();
    },

    afterFirstLayout : function() {
        var me = this;
        var thisDom = this.getEl().dom;

        thisDom.addEventListener('mousemove',  me.onMouseMove.bind(this), true);
        thisDom.addEventListener('mousewheel', me.onMouseWheel.bind(this),false);
        thisDom.addEventListener('DOMMouseScroll',me.onMouseWheel, false);


        this.renderer = new THREE.WebGLRenderer({
            preserveDrawingBuffer : true
        });

        this.renderer.setSize(this.getWidth(), this.getHeight());
        this.renderer.setClearColor(0xC0C0C0, 1);
        thisDom.appendChild(this.renderer.domElement);

        var aspect = this.getWidth() / this.getHeight();

        this.camera = new THREE.PerspectiveCamera(20, aspect, .01, 100);
        this.camera.position.z = 5.0;
        this.controls = new THREE.OrbitControls(this.camera, thisDom);

        this.projector = new THREE.Projector();

        this.getEl().on({
            scope : this,
            mousedown : this.onMouseDown,
        });
        this.getEl().on({
            scope : this,
            mouseup : this.onMouseUp,
        });

        ////////////////////
        this.mousedown = false;
        this.needs_render = true;


        this.callParent();
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


    },

    onMouseUp : function(event) {
        this.controls.enabled = true;
        this.mousedown   = false;
        this.needs_render = true;
    },

    onMouseMove : function(event){
    },



    onresize : function() {
        var aspect = this.getWidth() / this.getHeight();
        this.camera.aspect = aspect;
        this.camera.updateProjectionMatrix();

        if (this.renderer && this.scene) {
            this.renderer.setSize(this.getWidth(), this.getHeight());
            this.renderer.render(this.scene, this.camera);
        }
    },

    rerender : function() {
        this.needs_render = true;
    },

    doAnimate : function() {
        var me = this;
	    if(this.onAnimate)
	        this.onAnimate();

        if (this.needs_render) {
            this.renderer.render(this.scene, this.camera);
        }
        this.controls.update();
        requestAnimationFrame(function() {
            me.doAnimate()
        });
    },


    //function onMouseDown( event_info ) {
    /*
      render : function(){
      this.mesh.rotation.x += 0.01;
      this.mesh.rotation.y += 0.02;
      console.log(this.mesh.rotation);
      console.log(this.renderer);
      this.renderer.render(this.rgbScene, this.camera);
      },

      afterComponentLayout : function(w, h){
      this.redraw();
      this.callParent(arguments);
      },

      redraw: function(){
      var renderer = this.renderer;
      if (renderer) {
      this.render();
      }
      }*/

});


