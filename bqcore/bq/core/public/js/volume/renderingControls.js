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

Ext.define('BQ.viewer.Volume.uniformUpdate', {
  updateSlider : function (slider, value) {
    this.sceneVolume.setUniform(slider.uniform_var, slider.convert(value), true, true);
  },
});

function renderingTool(volume, cls){
    this.cls = cls;
    this.volume = volume;
    this.renderToPanel = true;
    this.uniforms = {};
};

renderingTool.prototype.init = function(){
    var me = this;
    this.button = Ext.create('Ext.Button',{
        //xtype: 'button',
        //text : this.cls,
        //layout : 'fit',
        layout : {
			type : 'vbox',
			align : 'stretch',
			pack : 'start',
		},
        width : 36,
        height : 36,
        //cls : 'bq-vol-btn',
        //pressedCls: this.cls + '-pressed',
        iconCls   : this.cls,
        enableToggle: true,
        handler : this.toggle,
        scope : me,
    });

    this.controls = Ext.create('Ext.container.Container', {
        border : false,
		layout : {
			type : 'vbox',
			align : 'stretch',
			pack : 'start',
		},
        //mixins : ['BQ.viewer.Volume.uniformUpdate'],
    }).hide();

    if(this.label){
        this.controls.add([{
            xtype: 'menuseparator',
        },{
            xtype: 'label',
            text: this.label
        }]);
    }

    this.initControls();

    this.addUniforms();
    this.initUniforms();
};

renderingTool.prototype.initUniforms = function(){
    var shaderManager = this.volume.sceneVolume;
    var me = this;
    this.sliders = {};
    for(var key in this.uniforms ){
        var e = this.uniforms[key];
        shaderManager.initUniform(e.name, e.type, e.val);
        //sliders build themselves from uniform variables...
        if(e.slider){
            var k = e.K;
            var slider = Ext.create('Ext.slider.Single', {
                renderTo : Ext.get('slider-ph'),
                fieldLabel : key,
                labelWidth : 60,
                minValue : e.min,
                maxValue : e.max,
                value : e.def,
                uniform_var : e.name,
                listeners : {
                    change : this.updateSlider,
                    scope : me,
                },
                k: k,
                convert : function (v) {
                    return this.k*v;
                }
            });
            this.sliders[key] = slider;
            this.controls.add(slider);
        }
    };
};

renderingTool.prototype.addUniforms = function(){
};

renderingTool.prototype.initControls = function(){
};

renderingTool.prototype.toggle = function(button){
    //default is just to show and hide, but can modify this as well
    if(button.pressed) {
        this.controls.show();
        //this.button.cls = this.cls + '-pressed';
        this.button.setIconCls(this.cls + '-pressed');
    }
    else {
        this.controls.hide();
        this.button.setIconCls(this.cls);
    }
};

renderingTool.prototype.addButton = function(){
    this.volume.toolPanelButtons.add(this.button);
};

renderingTool.prototype.addControls = function(){
    if(this.renderToPanel)
        this.volume.toolPanel.add(this.controls);
};

renderingTool.prototype.updateSlider = function(slider, value){
    this.volume.sceneVolume.setUniform(slider.uniform_var, slider.convert(value), true, true);
};

//////////////////////////////////////////////////////////////////
//
// Gamma controller
//
//////////////////////////////////////////////////////////////////

function gammaTool(volume) {
	//renderingTool.call(this, volume);
	this.label = 'gamma';
    this.cls = 'histoButton';
    this.base = renderingTool;
    this.base(volume, this.cls);

};

gammaTool.prototype = new renderingTool();

gammaTool.prototype.addUniforms = function(){
    this.uniforms['min']   = {name: 'GAMMA_MIN', type: 'f', val: 0.0};
    this.uniforms['max']   = {name: 'GAMMA_MAX', type: 'f', val: 1.0};
    this.uniforms['scale'] = {name: 'GAMMA_SCALE', type: 'f', val: 0.5} ;
    //this.initUniforms();
};

gammaTool.prototype.initControls = function(){
    var me = this;

    this.title = 'gamma';

    //this.addUniforms();
    this.histogram = this.volume.model.histogram;
    this.gamma = this.volume.model.gamma;
    this.contrastRatio = 0.5;

    this.data = {
        min : 0,
        max : 0,
        scale : 0
    };

    this.svg = Ext.create('BQ.graph.d3', {
        height : 60,
    });

    var getVals =  function (min, mid, max) {
        var div = 255; //this.getWidth();
        min /= div;
        max /= div;
        mid /= div;
        var diff = max - min;
        var x = (mid - min) / diff;
        scale = 4 * x * x;
        return {
            min : min,
            scale : scale,
            max : max
        };
    };
    /*
      var setEqualized = function(){
      var hist = me.histogram;
      var thresh = 100;
      var min = 0;
      do {
      var histi = 0;
      for(var c in hist){
      if(hist[c][min]) histi += hist[c][min];
      }
      min++;
      } while(histi < thresh)

      var max = 255;
      do {
      var histi = 0;
      for(var c in hist){
      if(hist[c][max]) histi += hist[c][max];
      }
      max--;
      } while(histi < thresh)


      var mid = 0.5*(min + max);
      console.log("blick block blue: ", hist, min, max, mid);

      this.slider0.setValue(0, min);
      //
      this.slider0.setValue(2, max);
      this.slider0.setValue(1, mid);
      this.data = this.getVals(this.slider0.thumbs[0].value,
      this.slider0.thumbs[1].value,
      this.slider0.thumbs[2].value);
      },
    */
    this.controls.add([
        this.svg,
        {
            xtype: 'multislider',
            hideLabel : true,
            fieldLabel : 'gamma',
            //increment : 1,
            maxValue: 255,
            minValue: 0,
            values : [0, 128, 255],
            listeners : {
                change : function (slider, value, thumb) {
                    //if(!me.histogram) continue;
                    var div = 200;
                    var minThumb = slider.thumbs[0].value;
                    var conThumb = slider.thumbs[1].value;
                    var maxThumb = slider.thumbs[2].value;
                    if(conThumb > maxThumb || conThumb < minThumb) conThumb = 0.5*(minThumb + maxThumb);
                    var min = minThumb / div;
                    var max = maxThumb / div;
                    var diff = max - min;
                    var x = (conThumb / div - min) / diff;

                    var vals = getVals(minThumb, conThumb, maxThumb);

                    if (thumb.index != 1) {
                        var posDiff = maxThumb - minThumb;
                        var newVal = this.contrastRatio * posDiff + minThumb;
                        slider.setValue(1, newVal, false);
                        this.middleThumbLock = true;
                        var me = this;
                        setTimeout(function () {
                            me.middleThumbLock = false;
                        }, 200);
                    } else {
                        if (this.middleThumbLock == false)
                            this.contrastRatio = (conThumb - minThumb) / (maxThumb - minThumb);
                    }

                    var p = 4;

                    this.volume.sceneVolume.setUniform('GAMMA_MIN', vals.min, true, true);
                    this.volume.sceneVolume.setUniform('GAMMA_MAX', vals.max, true, true);
                    this.volume.sceneVolume.setUniform('GAMMA_SCALE', vals.scale, true, true);

                    this.data = vals;
                    this.volume.model.gamma = vals;
                    if(this.histogramSvg){
                        this.volume.model.updateHistogram();
                        this.histogramSvg.redraw();
                    }

                },
                scope : me,
            }
        }]);

    this.controls.on('afterlayout', function () {
        if(this.loaded) return;
        if(me.volume.model.loaded == true){
            me.histogramSvg = new histogramD3(me.histogram, me.gamma, me.svg.svg, me.controls);
            //me.setEqualized();
            me.histogramSvg.redraw();
        }

        me.volume.on("histogramloaded", function(){
            if(!me.histogramSvg)
                me.histogramSvg = new histogramD3(me.histogram, me.gamma, me.svg.svg, me.controls);
            //me.setEqualized();
            me.histogramSvg.redraw();
        })
        this.loaded = true;
    });
};

function materialTool(volume, cls) {
	//renderingTool.call(this, volume);
    this.label = 'brightness/density';
    this.cls = 'materialButton';

	this.base = renderingTool;
    this.base(volume, this.cls);
};

materialTool.prototype = new renderingTool();

materialTool.prototype.addUniforms = function(){
    this.uniforms['brightness'] = {name: 'BRIGHTNESS',
                                   type: 'f',
                                   val: 0.5,
                                   slider: true,
                                   min: 0,
                                   max: 100,
                                   def: 50,
                                   K: 0.02};
    this.uniforms['density']    = {name: 'DENSITY',
                                   type: 'f',
                                   val: 0.5,
                                   slider: true,
                                   min: 0,
                                   max: 100,
                                   def: 50,
                                   K: 0.025};
};

materialTool.prototype.initControls = function(){
    var me = this;
    this.volume.on('loaded', function () {
        me.sliders['density'].setValue(50);
        me.sliders['brightness'].setValue(75);
    });
};

function ditherTool(volume) {
	//renderingTool.call(this, volume);
	this.cls = 'ditherButton';
    this.base = renderingTool;
    this.base(volume, this.cls);
};

ditherTool.prototype = new renderingTool();

ditherTool.prototype.addUniforms = function(){
    this.uniforms['dither'] = {name: 'DITHERING', type: 'i', val: this.dithering};
    //this.initUniforms();
};

ditherTool.prototype.initControls = function(){
    var me = this;
    this.dithering = false;
};

ditherTool.prototype.toggle = function(button){
    this.dithering ^= 1;
    this.volume.sceneVolume.setUniform('DITHERING', this.dithering, true, true);
    this.base.prototype.toggle.call(this,button);

};


function boxTool(volume, cls) {
	//renderingTool.call(this, volume);
    this.label = 'relative dimensions';
    this.cls = 'resizeButton';

	this.base = renderingTool;
    this.base(volume, this.cls);
};

boxTool.prototype = new renderingTool();

boxTool.prototype.addUniforms = function(){
  this.uniforms['box_size'] = {name: 'BOX_SIZE', type: 'v3', val: this.boxSize};
    //this.initUniforms();
};

boxTool.prototype.initControls = function(){
    var me = this;
    this.boxSize = new THREE.Vector3(0.5, 0.5, 0.5);
    var controlBtnSize = 22;

    this.boxX = Ext.create('Ext.form.field.Number', {
        name : 'box_x',
        fieldLabel : 'x',
        value : 1,
        minValue : 0.1,
        maxValue : 1,
        step : 0.05,
        width : 150,
        listeners : {
            change : function (field, newValue, oldValue) {
                if (typeof newValue != 'number')
                    return;
                newValue = newValue < 0.1 ? 0.1 : newValue;
                this.boxSize.x = 0.5 * newValue;
                this.volume.scaleCube(this.boxSize);
            },
            scope : me
        },
    });

    this.boxY = Ext.create('Ext.form.field.Number', {
        name : 'box_y',
        fieldLabel : 'y',
        value : 1,
        minValue : 0.1,
        maxValue : 1,
        step : 0.05,
        width : 150,
        listeners : {
            change : function (field, newValue, oldValue) {
                if (typeof newValue != 'number')
                    return;
                newValue = newValue < 0.1 ? 0.1 : newValue;
                this.boxSize.y = 0.5 * newValue;
                this.volume.scaleCube(this.boxSize);
            },
            scope : me
        },
    });

    this.boxZ = Ext.create('Ext.form.field.Number', {
        name : 'box_z',
        fieldLabel : 'z',
        value : 1,
        minValue : 0.1,
        maxValue : 1,
        step : 0.05,
        width : 150,
        listeners : {
            change : function (field, newValue, oldValue) {
                if (typeof newValue != 'number')
                    return;
                newValue = newValue < 0.1 ? 0.1 : newValue;
                this.boxSize.z = 0.5 * newValue;
                this.volume.scaleCube(this.boxSize);
            },
            scope : me
        },
    });
    this.controls.add([this.boxX, this.boxY, this.boxZ]);
    this.volume.on('loaded', function () {
        me.boxSize.x = 0.5;
        var dims = me.volume.dims;
        if (dims) {
            me.boxSize.y = 0.5 * dims.pixel.x / dims.pixel.y;
            me.boxSize.z = 0.5 * dims.pixel.x / dims.pixel.z;
        } else {
            me.boxSize.y = 0.5;
            me.boxSize.z = 0.5;
        }
        me.boxX.setValue(2.0 * me.boxSize.x);
        me.boxY.setValue(2.0 * me.boxSize.y);
        me.boxZ.setValue(2.0 * me.boxSize.z);
    });
};

function phongTool(volume, cls) {
	//renderingTool.call(this, volume);
    this.label = 'phong rendering';
    this.cls = 'phongButton';

	this.base = renderingTool;
    this.base(volume, this.cls);
};

phongTool.prototype = new renderingTool();

phongTool.prototype.addUniforms = function(){
    this.uniforms['ambient']    = {name: 'KA',
                                   type: 'f',
                                   val: 0.5,
                                   slider: true,
                                   min: 0,
                                   max: 100,
                                   def: 50,
                                   K: 0.01};
    this.uniforms['diffuse']    = {name: 'KD',
                                   type: 'f',
                                   val: 0.5,
                                   slider: true,
                                   min: 0,
                                   max: 100,
                                   def: 50,
                                   K: 0.01};
    this.uniforms['size']    = {name: 'SPEC_SIZE',
                                   type: 'f',
                                   val: 0.5,
                                   slider: true,
                                   min: 2,
                                   max: 100,
                                   def: 50,
                                   K: 1.0};
    this.uniforms['intensity']    = {name: 'SPEC_INTENSITY',
                                   type: 'f',
                                   val: 0.5,
                                   slider: true,
                                   min: 0,
                                   max: 100,
                                   def: 50,
                                   K: 1.0};
    //this.initUniforms();
};

phongTool.prototype.initControls = function(){
    var me = this;
    this.phong = 0;
    this.controls.add();
    this.volume.on('loaded', function () {
        me.sliders['ambient'].setValue(10);
        me.sliders['diffuse'].setValue(100);
        me.sliders['size'].setValue(0);
        me.sliders['intensity'].setValue(0);
    });
};

phongTool.prototype.toggle = function(button){
    this.phong ^= 1;
    if(this.phong){
        this.volume.shaderConfig.lighting.phong = true;
    }
    else
        this.volume.shaderConfig.lighting.phong = false;
    this.volume.sceneVolume.setConfigurable("default",
                                            "fragment",
                                            this.volume.shaderConfig);
    this.base.prototype.toggle.call(this,button);
};


function deepTool(volume, cls) {
	//renderingTool.call(this, volume);
    this.label = 'deep rendering';
    this.cls = 'deepButton';

	this.base = renderingTool;
    this.base(volume, this.cls);
};

deepTool.prototype = new renderingTool();

deepTool.prototype.addUniforms = function(){

    this.uniforms['samples']    = {name: 'LIGHT_SAMPLES',
                                   type: 'i',
                                   val: 4};
    this.uniforms['depth']    = {name: 'LIGHT_DEPTH',
                                 type: 'f',
                                 val: 0.5,
                                 slider: true,
                                 min: 0,
                                 max: 100,
                                 def: 50,
                                 K: 0.02};

    this.uniforms['dispersion']    = {name: 'DISPERSION',
                                      type: 'f',
                                      val: 0.5,
                                      slider: true,
                                      min: 0,
                                      max: 100,
                                      def: 50,
                                      K: 0.02};
    //this.initUniforms();
};

deepTool.prototype.initControls = function(){
    var me = this;
    this.state = 0;
    var sampleField = Ext.create('Ext.form.field.Number', {
        name : 'numberfield2',
        fieldLabel : 'samples',
        value : 4,
        minValue : 0,
        maxValue : 16,
        width : 150,
        listeners : {
            change : function (field, newValue, oldValue) {
                this.volume.sceneVolume.setUniform('LIGHT_SAMPLES', newValue, true, true);
            },
            scope : me
        },
    });
    this.controls.add(sampleField);
    this.controls.on('afterlayout', function () {
    });
};

deepTool.prototype.toggle = function(button){
    this.state ^= 1;
    if(this.state){
        this.volume.shaderConfig.lighting.deep = true;
    }
    else
        this.volume.shaderConfig.lighting.deep = false;
    this.volume.sceneVolume.setConfigurable("default",
                                            "fragment",
                                            this.volume.shaderConfig);
    this.base.prototype.toggle.call(this,button);
    //if(button.pressed) this.controls.show();
    //else this.controls.hide();
};



function lightTool(volume, cls) {
	//renderingTool.call(this, volume);
    //this.label = 'gamma';
    this.cls = 'lightButton';

	this.base = renderingTool;
    this.base(volume, this.cls);
};

lightTool.prototype = new renderingTool();

lightTool.prototype.addUniforms = function(){
    this.uniforms['brightness'] = {name: 'LIGHT_POSITION', type: 'v3', val: this.lightObject.position};
    //this.initUniforms();
};

lightTool.prototype.initControls = function(){
    var me = this;

    this.sceneVolume = this.volume.sceneVolume;
    this.canvas3D = this.volume.canvas3D;

    var sphere = new THREE.SphereGeometry(0.05, 3, 3);
    this.lightObject = new THREE.Mesh(sphere,
                                      new THREE.MeshBasicMaterial({
                                          color : 0xFFFF33,
                                          wireframe : true,
                                      }));

    this.plane = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000, 8, 8),
                                new THREE.MeshBasicMaterial({
                                    color : 0x000000,
                                    opacity : 0.25,
                                    transparent : true,
                                    wireframe : true
                                }));
    this.plane.visible = false;
    this.lightObject.visible = false;

    this.sceneVolume.scene.add(this.plane);
    this.lightObject.position.x = 0.0;
    this.lightObject.position.y = 0.0;
    this.lightObject.position.z = 1.0;
    this.sceneVolume.scene.add(this.lightObject);
    //this.sceneVolume.sceneData.add(this.lightObject);

    var onMouseUp = function () {
        this.selectLight = false;
    };

    var onMouseDown = function () {
        if (this.state === 0)
            return;
        var width = this.canvas3D.getWidth();
        var height = this.canvas3D.getHeight();
        var cx = this.canvas3D.getX();
        var cy = this.canvas3D.getY();
        var x = ((event.clientX - cx) / width) * 2 - 1;
        var y =  - ((event.clientY - cy) / height) * 2 + 1;

        var vector = new THREE.Vector3(x, y, 0.5);
        var camera = this.canvas3D.camera;
        this.canvas3D.projector.unprojectVector(vector, camera);

        var raycaster
            = new THREE.Raycaster(camera.position,
                                  vector.sub(camera.position).normalize());
        var objects = [this.lightObject];
        var intersects = raycaster.intersectObjects(objects);
        if (intersects.length > 0) {
            this.canvas3D.controls.enabled = false;
            this.selectLight = true;
            this.canvas3D.getEl().dom.style.cursor = 'move';
        } else {
            this.canvas3D.getEl().dom.style.cursor = 'auto';
        }
    };

    var onMouseMove = function (event) {
        event.preventDefault();
        if (this.state === 0)
            return;
        var width = this.canvas3D.getWidth();
        var height = this.canvas3D.getHeight();
        var cx = this.canvas3D.getX();
        var cy = this.canvas3D.getY();
        var x = ((event.clientX - cx) / width) * 2 - 1;
        var y =  - ((event.clientY - cy) / height) * 2 + 1;

        var vector = new THREE.Vector3(x, y, 0.5);

        var camera = this.canvas3D.camera;
        this.canvas3D.projector.unprojectVector(vector, camera);

        var raycaster
            = new THREE.Raycaster(camera.position,
                                  vector.sub(camera.position).normalize());

        var objects = [this.lightObject];
        var intersects = raycaster.intersectObjects(objects);

        if (this.selectLight) {
            var intersects = raycaster.intersectObject(this.plane);
            this.lightObject.position.copy(intersects[0].point.sub(this.offset));
            return;
        }
        if (intersects.length > 0) {
            this.canvas3D.getEl().dom.style.cursor = 'move';
            this.plane.position.copy(intersects[0].object.position);
            this.plane.lookAt(camera.position);
        } else {
            this.canvas3D.getEl().dom.style.cursor = 'auto';
        }
    };

    this.canvas3D.getEl().dom.addEventListener('mousemove', onMouseMove.bind(this), true);
    this.canvas3D.getEl().dom.addEventListener('mouseup', onMouseUp.bind(this), true);
    this.canvas3D.getEl().dom.addEventListener('mousedown', onMouseDown.bind(this), true);
    this.offset = new THREE.Vector3();
};

lightTool.prototype.toggle = function(button){
    if (button.pressed) {
        this.lightObject.visible = true;
    } else {
        this.lightObject.visible = false;
    }
    this.base.prototype.toggle.call(this,button);
    this.volume.rerender();
};

Ext.define('BQ.viewer.Volume.clip', {
  extend : 'Ext.container.Container',
  alias : 'widget.clip',
  border : false,
  addUniforms : function () {
    this.sceneVolume.initUniform('CLIP_NEAR', "f", 0.0);
    this.sceneVolume.initUniform('CLIP_FAR', "f", 3.0);
  },

  initComponent : function () {
    this.title = 'clipping';
    var me = this;
    this.clipNear = 0.0;
    this.clipFar = 3.0;
    //console.log("slider func: ", this.mixins, this.updateSlider);
    this.clipSlider = Ext.create('Ext.slider.Multi', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'clip',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        values : [0, 100],
        uniform_var : 'CLIP_NEAR',
        listeners : {
          change : function (slider, value, thumb) {
              console.log(value/100);
              if (thumb.index == 0) {
                  this.sceneVolume.setUniform('CLIP_NEAR', value / 100, true, true);
              } else {
                  this.sceneVolume.setUniform('CLIP_FAR', value / 100, true, true);
              }

          },
          scope : me,
        },
      });

    this.addUniforms();
    this.isLoaded = true;

    this.items = [this.clipSlider];
    this.callParent();
  },

  afterFirstLayout : function () {},
});


function clipTool(volume) {
    this.cls = 'clipButton';

	this.base = renderingTool;
    this.base(volume, this.cls);
    this.renderToPanel = false;
};

clipTool.prototype = new renderingTool();

clipTool.prototype.addUniforms = function(){

    this.uniforms['near']    = {name: 'CLIP_NEAR',
                                   type: 'f',
                                   val: 0.0};
    this.uniforms['far']    = {name: 'CLIP_FAR',
                                   type: 'f',
                                   val: 0.0};
    //this.initUniforms();
};

clipTool.prototype.initControls = function(){
    var me = this;

	var clipSlider = Ext.create('Ext.slider.Multi', {
		//renderTo : thisDom,
		itemId : 'clip-slider',
		//cls : 'bq-clip-slider',
		//fieldLabel : 'clip',
        //width: '100%',
		labelWidth : 60,
		minValue : 0.00,
		maxValue : 100,
		values : [0, 100],
		hideLabel : true,
		increment : 0.25,
		listeners : {
			change : function (slider, value, thumb) {

				if (thumb.index == 0) {
					me.volume.sceneVolume.setUniform('CLIP_NEAR', value / 100);
				} else {
					me.volume.sceneVolume.setUniform('CLIP_FAR', 1 - value / 100);
				}
			},
			scope : me,
		},

		vertical : false,
		animation : false,
	});

    //this.controls.add(clipSlider);
    var me = this;
	var thisDom = this.volume.getEl().dom;
    //this.controls.cls = 'bq-clip-slider';
    //this.controls.renderTo = thisDom;

    this.clipPanel = Ext.create('Ext.panel.Panel', {
		collapsible : false,
		header : false,
		renderTo : thisDom,
        layout : 'fit',
		cls : 'bq-volume-playback',
		items : [clipSlider],
	}).hide();

    //this.volume.addFade(this.controls);
    this.volume.on('loaded', function () {
        if(me.isloaded) return;
        me.volume.addFade(me.clipPanel);
        me.isloaded = true;
    });
};

clipTool.prototype.toggle = function(button){

    if(button.pressed) this.clipPanel.show();
    else this.clipPanel.hide();
    this.base.prototype.toggle.call(this,button);

};

//////////////////////////////////////////////////////////////////
//
// info from the graphics card
//
//////////////////////////////////////////////////////////////////

Ext.define('BQ.viewer.Volume.glinfo', {
  extend : 'Ext.container.Container',
  cls : 'glinfo',
  alias : 'widget.glinfo',

  changed : function () {    if (this.isLoaded) {}
  },

  addUniforms : function () {},

  displayParameterWindow : function () {
    var store = Ext.create('Ext.data.ArrayStore', {
        fields : [{
            name : 'parameter'
          }, {
            name : 'value'
          },
        ],
        data : this.params,
      });

    Ext.create('Ext.window.Window', {
      title : 'gl info',
      height : 200,
      width : 400,
      layout : 'fit',
      items : { // Let's put an empty grid in just to illustrate fit layout
        xtype : 'grid',
        border : false,
        columns : [{
            text : 'Parameter',
            flex : 1,
            sortable : false,
            dataIndex : 'parameter'
          }, {
            text : 'Value',
            flex : 1,
            sortable : false,
            dataIndex : 'value'
          }, ], // One header just for show. There's no data,
        store : store,
      }
    }).show();
  },

  initParameters : function () {
    this.params = new Array();
    var ctx = this.canvas3D.renderer.getContext();
    console.log("ctx: ", ctx);
    this.params[0] = ['Platform', navigator.platform];
    this.params[1] = ['Agent', navigator.userAgent];
    if (ctx) {
      console.log('opengl context: ', ctx);
      this.params[2] = ['Vendor', ctx.getParameter(ctx.VENDOR)];
      this.params[3] = ['Version', ctx.getParameter(ctx.VERSION)];

      this.params[4] = ['Renderer', ctx.getParameter(ctx.RENDERER)];
      this.params[5] = ['Shading Language', ctx.getParameter(ctx.SHADING_LANGUAGE_VERSION)];
      this.params[6] = ['RGBA Bits', ctx.getParameter(ctx.RED_BITS) + ', ' +
        ctx.getParameter(ctx.GREEN_BITS) + ', ' +
        ctx.getParameter(ctx.BLUE_BITS) + ', ' +
        ctx.getParameter(ctx.ALPHA_BITS)];
      this.params[7] = ['Depth Bits', ctx.getParameter(ctx.DEPTH_BITS)];
      this.params[8] = ['Max Vertex Attribs', ctx.getParameter(ctx.MAX_VERTEX_ATTRIBS)];
      this.params[9] = ['Max Vertex Texture', ctx.getParameter(ctx.MAX_VERTEX_TEXTURE_IMAGE_UNITS)];
      this.params[10] = ['Max Varying Vectors', ctx.getParameter(ctx.MAX_VARYING_VECTORS)];
      this.params[11] = ['Max Uniform Vectors', ctx.getParameter(ctx.MAX_VERTEX_UNIFORM_VECTORS)];

      this.params[12] = ['Max Combined Texture Image Units', ctx.getParameter(ctx.MAX_COMBINED_TEXTURE_IMAGE_UNITS)];
      this.params[13] = ['Max Texture Size', ctx.getParameter(ctx.MAX_TEXTURE_SIZE)];
      this.params[14] = ['Max Cube Map Texture Size', ctx.getParameter(ctx.MAX_CUBE_MAP_TEXTURE_SIZE)];
      //this.params[15] = ['Num. Compressed Texture Formats', ctx.getParameter(ctx.NUM_COMPRESSED_TEXTURE_FORMATS)];

      this.params[15] = ['Max Render Buffer Size', ctx.getParameter(ctx.MAX_RENDERBUFFER_SIZE)];
      this.params[16] = ['Max Cube Map Texture', ctx.getParameter(ctx.MAX_CUBE_MAP_TEXTURE_SIZE)];
      this.params[17] = ['Max Fragment Uniform Vectors', ctx.getParameter(ctx.MAX_FRAGMENT_UNIFORM_VECTORS)];
      this.params[18] = ['Max Render Buffer Size', ctx.getParameter(ctx.RENDERBUFFER_SIZE)];
      this.params[19] = ['Max texture image units', ctx.getParameter(ctx.MAX_TEXTURE_IMAGE_UNITS)];

      this.params[20] = ['Max vertex uniform vectors', ctx.getParameter(ctx.MAX_VERTEX_UNIFORM_VECTORS)];
      //this.params[13] = ['Max Cube Map Texture', ctx.getParameter(ctx.MAX_CUBE_MAP_TEXTURE_SIZE)];

      this.params[21] = ['Max Viewport Dimensions', ctx.getParameter(ctx.MAX_VIEWPORT_DIMS)];
      this.params[22] = ['Aliased Line Width Range', ctx.getParameter(ctx.ALIASED_LINE_WIDTH_RANGE)];
      this.params[23] = ['Aliased Point Size Range', ctx.getParameter(ctx.ALIASED_POINT_SIZE_RANGE)];

      for (var i = 0; i < this.params.length; i++) {

        var tmp = '';

        if (typeof(this.params[i][1]) === 'string')
          continue;
        if (typeof(this.params[i][1]) === 'number')
          continue;
        var field = this.params[i][1];
        if (!field)
          continue;

        for (var j = 0; j < this.params[i][1].length; j++) {
          tmp += field[j];
          if (j < field.length - 1)
            tmp += ', ';
        }
        this.params[i][1] = tmp;
      }
      /*
      still to add:
      addLine('misc', 'Supported Extensions', ctx.getSupportedExtensions().length === 0 ? 'none' : commasToBr(ctx.getSupportedExtensions()));
       */
    }
  },

  initComponent : function () {
    this.initParameters();
    var me = this;
    var button = Ext.create('Ext.Button', {
        text : 'show gl info',
        cls : 'volume-button',
        handler : function (button, pressed) {
          me.displayParameterWindow();
        },
        scope : me,
      });
    Ext.apply(this, {
      items : [
        button
      ],
    });
    this.callParent();
  },

  afterFirstLayout : function () {},
});
