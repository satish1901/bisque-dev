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

//////////////////////////////////////////////////////////////////
//
// info from the graphics card
//
//////////////////////////////////////////////////////////////////

Ext.define('BQ.viewer.Volume.glinfo', {
  extend : 'Ext.container.Container',
  cls : 'glinfo',
  alias : 'widget.glinfo',

  changed : function () {
    if (this.isLoaded) {}
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

//////////////////////////////////////////////////////////////////
//
// Gamma controller
//
//////////////////////////////////////////////////////////////////

Ext.define('BQ.viewer.Volume.gammapanel', {
  extend : 'Ext.container.Container',
  alias : 'widget.gamma',
  border : false,

  addUniforms : function () {
    this.sceneVolume.initUniform('GAMMA_MIN', "f", 0.0);
    this.sceneVolume.initUniform('GAMMA_MAX', "f", 1.0);
    this.sceneVolume.initUniform('GAMMA_SCALE', "f", 0.5);
  },

  fetchHistogram : function () {
    url = this.panel3D.constructAtlasUrl() + '&histogram';

    var xRes;
    var yRes;
    Ext.Ajax.request({
      url : url,
      scope : this,
      disableCaching : false,
      callback : function (opts, succsess, response) {
        if (response.status >= 400)
          BQ.ui.error(response.responseText);
        else {
          if (!response.responseXML)
            return;
          var xmlDoc = response.responseXML;
          console.log('xml response: ', xmlDoc);
          var rChan = evaluateXPath(xmlDoc, "resource/histogram[@name='channel']/value");

          this.rHist = rChan[0].innerHTML.split(",");
          this.gHist = rChan[1].innerHTML.split(",");
          this.bHist = rChan[2].innerHTML.split(",");
          this.updateColorSvg();
        }
      },
    });
  },

  genHistogramSvg : function (hist, color) {
    if (this.data == null)
      return;
    if (hist == null)
      return;

    var maxVal = 0;
    var minVal = 999;
    var min = this.data.min;
    var max = this.data.max;
    var C = this.data.scale;
    //var C = 1.0;
    var start = Math.floor(this.data.min * hist.length);
    var end = Math.floor(this.data.max * hist.length);

    var newHist = new Array();
    var lookUp = new Array();
    var avg = 0;
    for (var i = 0; i < hist.length; i++) {
      var val = parseInt(hist[i]);
      avg += val;
      minVal = val < minVal ? val : minVal;
      maxVal = val > maxVal ? val : maxVal;
    }

    avg /= hist.length;

    for (var i = 0; i < hist.length; i++) {
      lookUp[i] = 0;
      newHist[i] = 0;
      if (i > start && i < end) {
        var val = (i - start) / (end - start);
        var plogy = C * Math.log(i);
        var modVal = Math.exp(plogy);
        var newBin = Math.ceil(modVal);
        newBin = newBin < hist.length - 1 ? newBin : hist.length - 1;
        lookUp[i] = newBin;
      }
    }

    for (var i = 1; i < lookUp.length - 1; i++) {
      newHist[lookUp[i] - 1] += 0.25 * parseInt(hist[i]);
      newHist[lookUp[i] + 0] += 0.5 * parseInt(hist[i]);
      newHist[lookUp[i] + 1] += 0.25 * parseInt(hist[i]);
    }
    maxVal = maxVal < 1 ? 1 : maxVal;

    var h = this.getHeight();
    var w = this.getWidth();

    var yMargin = 2;
    var xMargin = 16;
    var hh = h - 2.0 * yMargin;
    var wh = w - 2.0 * xMargin;
    var x0 = xMargin;
    var y0 = hh - yMargin;
    var path = x0.toString() + ' ' + (y0 - 8).toString();

    var N = wh;
    var dataScale = 1.0;
    var dx = wh / newHist.length;

    for (var i = 0; i < newHist.length; i++) {
      var x = i;
      x = x0 + i * dx;
      var y = 0.0;
      if (newHist[i] > 0) {
        //y = 0.1*Math.log(newHist[i]);
        if (0.5 * (avg + minVal) > 0.0)
          y = newHist[i] / (0.5 * (avg + minVal));
      } else
        y = 0;
      //console.log(i, newHist[i], y);
      y = y0 - hh * y;
      //console.log(i,newHist[i],(avg),newHist[i]/(avg));
      path += ' ' + x.toString() + ' ' + y.toString();
    }
    path += ' ' + (x0 + end - start).toString() + ' ' + y0.toString();
    var pathOpen = '<path d="M'
      var pathClose0 = '" stroke = ' + color + ' opacity=0.8 stroke-width=1 fill = none />';
    var pathClose1 = '" stroke = none opacity=0.15 stroke-width=1 fill=' + color + ' />';

    var graph = pathOpen + path + pathClose0 + pathOpen + path + pathClose1;
    var svg = '<svg width=100% height=100% > <' + graph + ' </svg>';
    return svg;
  },

  updateColorSvg : function () {
    if (this.data == null)
      return;
    var C = this.data.scale;
    var min = this.data.min;
    var max = this.data.max;
    var h = this.getHeight();
    var w = this.getWidth();

    var yMargin = 16;
    var xMargin = 16;
    var hh = h - 2.0 * yMargin;
    var wh = w - 2.0 * xMargin;
    var x0 = xMargin;
    var y0 = hh + yMargin;

    var path = x0.toString() + ' ' + (y0 - 8).toString();
    var mid = 0.5 * (min + max);
    var N = wh;
    var dataScale = 1.0;
    for (var i = 0; i < N; i++) {
      var x = i;
      var t = 0.5 * i / N * dataScale;
      var xi = (t - min) / (max - min);
      var plogy = C * Math.log(xi);
      var y = Math.exp(plogy);
      if (t < min)
        y = 0;
      if (t > max)
        y = 1.0;
      x = x0 + x;
      y = y0 - 8 - hh * y;
      path += ' ' + x.toString() + ' ' + y.toString();
    }

    var pathOpen = '<path d="M'
      var pathClose1 = '" stroke = gray stroke-width=1 fill="none" />';
    var pathClose3 = '" stroke = white stroke-width=1 opacity: 0.7 fill="none" />';
    var xAxis = pathOpen + x0 + ' ' + y0 + ' ' + 0.95 * w + ' ' + y0 + pathClose1;
    var yAxis = pathOpen + x0 + ' ' + y0 + ' ' + x0 + ' ' + y0 - hh + pathClose1;
    var graph = pathOpen + path + pathClose3;
    var svg = ' <svg width=100% height=100% > <' + xAxis + yAxis + graph + ' </svg>';
    var rH = this.genHistogramSvg(this.rHist, 'red');
    var gH = this.genHistogramSvg(this.gHist, 'green');
    var bH = this.genHistogramSvg(this.bHist, 'blue');

    this.rampSvg.getEl().dom.innerHTML = ' <svg width=100% height=100% >' + rH + gH + bH + svg + '</svg>';

  },

  getVals : function (min, mid, max) {
    var div = this.getWidth();
    min /= div;
    max /= div;
    var diff = max - min;
    var x = (mid / div - min) / diff;
    scale = 4 * x * x;
    return {
      min : min,
      scale : scale,
      max : max
    };
  },

  initComponent : function () {

    this.title = 'gamma';
    var me = this;

    this.addUniforms();
    this.fetchHistogram();

    this.contrastRatio = 0.5;
    this.slider0 = Ext.create('Ext.slider.Multi', {
        //renderTo: 'multi-slider-horizontal',
        hideLabel : true,
        fieldLabel : 'gamma',
        increment : 1,
        values : [10, 50, 90],
        listeners : {
          change : function (slider, value, thumb) {
            var div = 200;
            var minThumb = slider.thumbs[0].value;
            var conThumb = slider.thumbs[1].value;
            var maxThumb = slider.thumbs[2].value;

            var min = minThumb / div;
            var max = maxThumb / div;
            var diff = max - min;
            var x = (conThumb / div - min) / diff;

            var vals = this.getVals(minThumb, conThumb, maxThumb);

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
            this.sceneVolume.setUniform('GAMMA_MIN', vals.min, true, true);
            this.sceneVolume.setUniform('GAMMA_MAX', vals.max, true, true);
            this.sceneVolume.setUniform('GAMMA_SCALE', vals.scale, true, true);

            this.data = vals;
            //this.canvasPanel.redraw();
            this.updateColorSvg();

          },
          scope : me,
        }
      });

    this.data = {
      min : 0,
      max : 0,
      scale : 0
    };
    this.rampSvg = Ext.create('Ext.Component', {
        height : 60,
      });

    Ext.apply(this, {
      items : [this.rampSvg, this.slider0, ],
    });

    this.callParent();
  },

  afterFirstLayout : function () {
    this.callParent();
    this.slider0.setMinValue(0.0);
    this.slider0.setMaxValue(100);
    var vals = this.getVals(this.slider0.thumbs[0].value,
        this.slider0.thumbs[1].value,
        this.slider0.thumbs[2].value);
    this.data = vals;
    this.slider0.setValue(0, 5);
    this.slider0.setValue(1, 55);
    this.slider0.setValue(2, 95);
    this.updateColorSvg();
  },
});

Ext.define('BQ.viewer.Volume.materianel', {
  extend : 'Ext.container.Container',
  cls : 'materialcontroller',
  alias : 'widget.material',
  mixins : ['BQ.viewer.Volume.uniformUpdate'],
  addUniforms : function () {
    this.sceneVolume.initUniform('brightness', "f", 0.5);
    this.sceneVolume.initUniform('density', "f", 0.5);
  },

  initComponent : function () {
    var me = this;

    this.addUniforms();
    this.isLoaded = true;

    this.title = 'material';
    this.density = 0.5;
    this.brightness = 1.0;
    this.densitySlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        fieldLabel : 'density',
        labelWidth : 60,
        minValue : 0,
        maxValue : 100,
        value : 50,
        uniform_var : 'density',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 100.0
        }
      });

    this.brightnessSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        //hideLabel: true,
        fieldLabel : 'brightness',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 50,
        uniform_var : 'brightness',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 20;
        }

      });

    //modal: true,
    //this.items = [this.canvasPanel, slider0, this, slider4];
    Ext.apply(this, {
      items : [this.densitySlider, this.brightnessSlider],
    });

    this.callParent();
  },

  afterFirstLayout : function () {
    this.densitySlider.setValue(50);
    this.brightnessSlider.setValue(75);
  },
});

Ext.define('BQ.viewer.Volume.lightpanel', {
  extend : 'Ext.container.Container',
  alias : 'widget.lighting',
  mixins : ['BQ.viewer.Volume.uniformUpdate'],

  changed : function () {
    console.log("scene: ", this.sceneVolume);
    this.sceneVolume.loadMaterial(this.materials[this.state]);
  },

  initMaterials : function () {
    this.materials = ['diffuse', 'volumeLighting',
      'phongLighting', 'phongAndVolumeLighting'];

    this.sceneVolume.initMaterial({
      name : 'volumeLighting',
      vertConfig : {
        url : "/js/volume/shaders/rayCast.vs"
      },
      fragConfig : {
        id : 'volumeLighting',
        url : "/js/volume/shaders/rayCastBlocks.fs",
        manipulate : function (text) {
          return text.replace("LIGHTING 0", "LIGHTING 1");
        }
      }
    });

    this.sceneVolume.initMaterial({
      name : 'phongLighting',
      vertConfig : {
        url : "/js/volume/shaders/rayCast.vs"
      },
      fragConfig : {
        id : 'phongLighting',
        url : "/js/volume/shaders/rayCastBlocks.fs",
        manipulate : function (text) {
          return text.replace("PHONG 0", "PHONG 1");
        }
      }
    });

    this.sceneVolume.initMaterial({
      name : 'phongAndVolumeLighting',
      vertConfig : {
        url : "/js/volume/shaders/rayCast.vs"
      },
      fragConfig : {
        id : 'phongAndVolumeLighting',
        url : "/js/volume/shaders/rayCastBlocks.fs",
        manipulate : function (text) {
          var phong = text.replace("PHONG 0", "PHONG 1");
          return phong.replace("LIGHTING 0", "LIGHTING 1");
        }
      }
    });
  },

  addUniforms : function () {
    this.sceneVolume.initUniform('LIGHT_SAMPLES', "i", 4);
    this.sceneVolume.initUniform('LIGHT_DEPTH', "f", 0.1);
    this.sceneVolume.initUniform('LIGHT_SIG', "f", 0.5);
    this.sceneVolume.initUniform('DISPERSION', "f", 0.5);
    this.sceneVolume.initUniform('DISP_SIG', "f", 0.5);
    this.sceneVolume.initUniform('KA', "f", 0.5);
    this.sceneVolume.initUniform('KD', "f", 0.5);
    this.sceneVolume.initUniform('NORMAL_INTENSITY', "f", 0.0);
    this.sceneVolume.initUniform('SPEC_SIZE', "f", 0.0);
    this.sceneVolume.initUniform('SPEC_INTENSITY', "f", 0.0);
  },

  initComponent : function () {
    this.state = 0;
    this.title = 'lighting';
    var me = this;
    this.addUniforms();
    this.initMaterials();

    this.lighting = Ext.create('Ext.form.field.Checkbox', {
        boxLabel : 'Advanced Rendering',
        checked : false,
        handler : function () {
          this.state ^= 1;
          this.changed();
          if ((this.state & 1) === 1) {
            this.depthSlider.show();
            this.sampleField.show();
            this.dispSlider.show();

          } else {
            this.depthSlider.hide();
            this.sampleField.hide();
            this.dispSlider.hide();

          }
          this.panel3D.rerender();
        },
        scope : me,
      });

    this.specular = Ext.create('Ext.form.field.Checkbox', {
        boxLabel : 'Phong Rendering',
        checked : false,
        handler : function () {
          this.state ^= 2;
          this.changed();
          if ((this.state & 2) === 2) {
            this.kaSlider.show();
            this.kdSlider.show();
            //this.normInSlider.show();
            this.specSizeSlider.show();
            this.specInSlider.show();
          } else {
            console.log(this.state & 2, "hide");
            this.kaSlider.hide();
            this.kdSlider.hide();

            //this.normInSlider.hide();
            this.specSizeSlider.hide();
            this.specInSlider.hide();
          }
          this.panel3D.rerender();
        },
        scope : me,
      });

    this.depthSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'depth',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 75,
        uniform_var : 'LIGHT_DEPTH',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 50;
        }
      }).hide();

    this.dispSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'R_dispersion',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 75,
        uniform_var : 'DISPERSION',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 50;
        }
      }).hide();
    /*
    this.dispAmtSlider = Ext.create('Ext.slider.Single', {
    renderTo: Ext.get('slider-ph'),
    hideLabel: false,
    fieldLabel: 'K_dispersion',
    labelWidth: 60,
    minValue: 10.0,
    maxValue: 110.0,
    value: 75,
    uniform_var: 'DISP_SIG',
    listeners: {
    change: this.updateSlider,
    scope: me,
    },
    convert: function(v) { return v/150.0;}
    }).hide();
     */

    this.kaSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'Ambient',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 75,
        uniform_var : 'KA',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 100;
        }
      }).hide();

    this.kdSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'diffuse',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 75,
        uniform_var : 'KD',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 100;
        }
      }).hide();

    this.normInSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'edges',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 75,
        uniform_var : 'NORMAL_INTENSITY',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 5.0;
        }
      }).hide();

    this.specSizeSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'size',
        labelWidth : 60,
        minValue : 2.00,
        maxValue : 50,
        value : 10.0,
        uniform_var : 'SPEC_SIZE',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v;
        }
      }).hide();

    this.specInSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'intensity',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 20,
        value : 0.0,
        uniform_var : 'SPEC_INTENSITY',
        listeners : {
          change : this.updateSlider,
          scope : me,
        },
        convert : function (v) {
          return v / 1.0;
        }
      }).hide();

    this.sampleField = Ext.create('Ext.form.field.Number', {
        name : 'numberfield2',
        fieldLabel : 'samples',
        value : 4,
        minValue : 0,
        maxValue : 16,
        width : 150,
        listeners : {
          change : function (field, newValue, oldValue) {
            this.sceneVolume.setUniform('LIGHT_SAMPLES', newValue, true, true);
          },
          scope : me
        },
      }).hide();

    //modal: true,
    //this.changed();
    this.items = [this.lighting,
      this.sampleField, this.depthSlider,
      this.dispSlider, // this.dispAmtSlider,
      this.specular, this.kaSlider, this.kdSlider, this.specInSlider, this.specSizeSlider];
    this.changed();
    this.callParent();
  },
  afterFirstLayout : function () {
    this.lighting,
    this.sampleField,
    this.depthSlider.setValue(50);
    this.dispSlider.setValue(10);

    this.kaSlider.setValue(85);
    this.kdSlider.setValue(50);
    this.specInSlider.setValue(0);
    this.specSizeSlider.setValue(0);
  }
});

Ext.define('BQ.viewer.Volume.lightControl', {
  extend : 'Ext.container.Container',
  alias : 'widget.lightControl',

  changed : function () {
    if (this.isLoaded) {
      this.sceneVolume.setUniform('LIGHT_POSITION', this.lightObject.position, true, true);
    }
  },

  addUniforms : function () {
    this.sceneVolume.initUniform('LIGHT_POSITION', "v3", this.lightObject.position);
  },

  initComponent : function () {
    this.title = 'light control';
    var me = this;
    this.dist = 1.0;
    this.state = false;
    this.lighting = Ext.create('Ext.form.field.Checkbox', {
        boxLabel : 'Modify Light Location',
        checked : false,
        handler : function () {
          this.state ^= 1;
          this.changed();
          if ((this.state & 1) === 1) {
            this.lightObject.visible = true;
          } else {
            this.lightObject.visible = false;
          }
          this.panel3D.rerender();
        },
        scope : me,
      });

    this.distanceSlider = Ext.create('Ext.slider.Single', {
        renderTo : Ext.get('slider-ph'),
        hideLabel : false,
        fieldLabel : 'distance',
        labelWidth : 60,
        minValue : 0.00,
        maxValue : 100,
        value : 75,
        listeners : {
          change : function (slider, value) {
            this.dist = value / 25;
            this.changed();
          },
          scope : me,
        }
      }).show();

    var me = this;
    var sphere = new THREE.SphereGeometry(0.05, 3, 3);
    this.lightObject = new THREE.Mesh(sphere,
        new THREE.MeshBasicMaterial({
          color : 0xFFFF33,
          wireframe : true,
        }));
    this.sceneVolume.scene.add(this.lightObject);

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
    this.canvas3D.getEl().dom.addEventListener('mousemove', me.onMouseMove.bind(this), true);
    this.canvas3D.getEl().dom.addEventListener('mouseup', me.onMouseUp.bind(this), true);
    this.canvas3D.getEl().dom.addEventListener('mousedown', me.onMouseDown.bind(this), true);
    this.offset = new THREE.Vector3(),

    this.addUniforms();
    this.isLoaded = true;
    this.changed();
    this.items = [this.lighting];
    this.callParent();
  },

  onAnimate : function () {},

  onMouseUp : function () {
    this.selectLight = false;
  },

  onMouseDown : function () {
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
  },

  onMouseMove : function (event) {
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

  },

  afterFirstLayout : function () {
    this.callParent();
  },
});

Ext.define('BQ.viewer.Volume.general', {
  extend : 'Ext.container.Container',
  alias : 'widget.general',

  addUniforms : function () {
    this.sceneVolume.initUniform('DITHERING', "i", this.dithering);
    this.sceneVolume.initUniform('BOX_SIZE', "v3", this.boxSize);
  },

  initComponent : function () {
    this.title = 'general';
    var me = this;
    this.dithering = false;
    this.showBox = false;
    this.boxSize = new THREE.Vector3(0.5, 0.5, 0.5);
    var controlBtnSize = 22;

    var dith = Ext.create('Ext.form.field.Checkbox', {
        boxLabel : 'dithering',
        height : controlBtnSize,
        checked : false,
        handler : function () {
          this.dithering ^= 1;
          this.sceneVolume.setUniform('DITHERING', this.dithering, true, true);
        },
        scope : me,
      });

    var showBoxBtn = Ext.create('Ext.form.field.Checkbox', {
        boxLabel : 'proportions',
        height : controlBtnSize,
        checked : false,
        handler : function () {
          this.showBox ^= 1;
          if (this.showBox) {
            this.boxX.show();
            this.boxY.show();
            this.boxZ.show();
          } else {
            this.boxX.hide();
            this.boxY.hide();
            this.boxZ.hide();
          }
        },
        scope : me,
      });

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
            this.panel3D.scaleCube(this.boxSize);
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
            this.panel3D.scaleCube(this.boxSize);
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
            this.panel3D.scaleCube(this.boxSize);
          },
          scope : me
        },
      });

    this.addUniforms();

    this.boxX.hide();
    this.boxY.hide();
    this.boxZ.hide();

    this.boxSize.x = 0.5;
    if (this.dims) {
      this.boxSize.y = 0.5 * this.dims.pixel.x / this.dims.pixel.y;
      this.boxSize.z = 0.5 * this.dims.pixel.x / this.dims.pixel.z;
    } else {
      this.boxSize.y = 0.5;
      this.boxSize.z = 0.5;
    }

    this.boxX.setValue(2.0 * this.boxSize.x);
    this.boxY.setValue(2.0 * this.boxSize.y);
    this.boxZ.setValue(2.0 * this.boxSize.z);

    this.isLoaded = true;
    this.items = [dith, showBoxBtn, this.boxX, this.boxY, this.boxZ];
    this.callParent();
  },

  afterFirstLayout : function () {},
});

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

//////////////////////////////////////////////////////////////////
//
// transfer slider
//
//////////////////////////////////////////////////////////////////


Ext.define('BQ.viewer.Volume.transferSlider', {
  extend : 'Ext.slider.Multi',
  alias : 'widget.transfer-slider',
  cls : 'key-slider',
  height : 40,
  constructor : function (config) {
    this.callParent(arguments);
    return this;
  },

  initComponent : function () {
    this.keyArray = new Array();
    this.autoKey = false;
    this.insertDist = 2;
    this.sampleRate = 8;
    this.timeValue = 0;
    var me = this;
    this.lastClicked = 0;
    this.stops = [{
        color : [0, 0, 0, 0],
        offset : 0
      }
    ];
    this.callParent();
    me.addEvents('clicked');
    this.addStop([256, 256, 256, 1.0], 100);
  },

  afterRender : function () {
    this.svgUrl = "http://www.w3.org/2000/svg";
    this.svgdoc = document.createElementNS(this.svgUrl, "svg");
    this.svgdoc.setAttributeNS(null, 'class', 'grad-slider');
    this.el.dom.appendChild(this.svgdoc);
    this.svgBackGround = document.createElementNS(this.svgUrl, "g");
    this.svgBackGround.setAttributeNS(null, 'class', 'grad-slider');
    this.svgdoc.appendChild(this.svgBackGround);

    var me = this;

    //this.addStop([50, 15, 20, 0.15],25);
    //this.addStop([80, 10, 10, 0.75],32);
    //this.addStop([50, 10, 1, 0.55],45);
    //this.addStop([40, 10, 1, 0.5],72);
    //this.addStop([50,50,50, .95],82);
    //this.addStop([50,50,50, 0.95],100);
    this.drawBackGround();
    this.callParent();
  },

  drawBackGround : function (canvas) {
    var svgStops = '<defs> <linearGradient id="Gradient1">\n';
    for (var i = 0; i < this.stops.length; i++) {
      var stop = this.stops[i];
      svgStops += '<stop offset="' + stop.offset +
      '%" stop-color="rgba(' +
      stop.color[0] + ', ' +
      stop.color[1] + ', ' +
      stop.color[2] + ', ' +
      stop.color[3] + ')"/>\n';
    }
    svgStops += '</linearGradient> </defs>'
    var rect = ['<rect id="rect1"',
      'x="0" y="0"',
      'rx="3" ry="3"',
      'width="100%"',
      'height="100%"',
      'fill="url(#Gradient1)"',
      '/>'].join(' ');

    var checkRect = [
      '<defs>',
      ' <pattern id="checkerPattern" width="20" height="20"',
      'patternUnits="userSpaceOnUse">',
      '<rect fill="black" x="0" y="0" width="10" height="10" />',
      '<rect fill="white" x="10" y="0" width="10" height="10" />',
      '<rect fill="black" x="10" y="10" width="10" height="10" />',
      '<rect fill="white" x="0" y="10" width="10" height="10" />',
      '</pattern>',
      '</defs>',
      '<rect fill="url(#checkerPattern)" style="stroke:white"',
      'x="0"',
      'y="0"',
      'rx="3"',
      'ry="3"',
      'width="100%" height="100%" />',
      '</g>',
    ].join('\n');

    var svg = [' <svg width=100% height=100% >',
      svgStops,
      checkRect,
      rect,
      '</svg>'].join('\n');

    this.svgBackGround.innerHTML = svg;
  },

  //----------------------------------------------------------------------
  // event handlers
  //----------------------------------------------------------------------


  changecomplete : function () {
    this.sortKeys();
    this.callParent();
  },

  setValue : function (index, value, animate, changeComplete) {

    if (index == 0)
      return;
    if (index == this.stops.length - 1)
      return;
    this.callParent(arguments);
    this.stops[index].offset = value;

    this.drawBackGround();
    this.lastClicked = index;
  },

  onMouseDown : function (e) {
    var me = this,
    thumbClicked = false,
    i = 0,
    thumbs = me.thumbs,
    len = thumbs.length,
    trackPoint;

    if (me.disabled) {
      return;
    }

    //see if the click was on any of the thumbs
    var thumb = 0;
    for (; i < len; i++) {
      thumbClicked = thumbClicked || e.target == thumbs[i].el.dom;
      thumb = e.target == thumbs[i].el.dom ? i : thumb;
    }

    if (thumbClicked) {
      this.lastClicked = thumb;
      me.fireEvent('clicked', me, thumb);
      var thisThumb = this.thumbs[thumb].el;
    }

    if (me.clickToChange && !thumbClicked) {
      trackPoint = me.getTrackpoint(e.getXY());
      if (trackPoint !== undefined) {
        me.onClickChange(trackPoint);
      }
    }
    me.focus();
  },

  sortKeys : function () {
    this.stops.sort(function (a, b) {
      return (a.offset - b.offset);
    });

    this.thumbs.sort(function (a, b) {
      return (a.value - b.value);
    });

    for (var i = 0; i < this.thumbs.length; i++) {
      this.thumbs[i].index = i;
    }
  },

  scaleKeys : function (newScale) {
    var oldScale = this.maxValue;
    if (oldScale == 0)
      return;
    var scale = newScale / oldScale;

    for (var i = 0; i < this.thumbs.length; i++) {
      var newVal = this.thumbs[i].value * scale;
      this.thumbs[i].value = newVal;
    }
  },

  addStop : function (rgba, offset) {
    this.addThumb(offset);
    this.stops.push({
      color : rgba,
      offset : offset
    });
    this.sortKeys();
  },

  removeStop : function (it) {

    if (it >= 0) {
      var innerEl = this.thumbs[it].ownerCt.innerEl.dom;
      innerEl.removeChild(this.thumbs[it].el.dom);
      this.thumbs.splice(it, 1);
      for (var i = 0; i < this.thumbs.length; i++) {
        this.thumbs[i].index = i;
      }

      this.stops.splice(it, 1);
    }
  },

  removeCurrentStop : function () {
    this.removeStop(this.lastClicked);
    this.drawBackGround();
  },

  addNextStop : function () {
    var i0 = this.lastClicked;
    var i1 = i0 + 1;
    if (i0 == this.thumbs.length - 1)
      i1 = i0 - 1;
    var o0 = this.thumbs[i0].value;
    var o1 = this.thumbs[i1].value;
    var c0 = this.stops[i0].color;
    var c1 = this.stops[i1].color;
    var cA = [0.5 * (c0[0] + c1[0]),
      0.5 * (c0[1] + c1[1]),
      0.5 * (c0[2] + c1[2]),
      0.5 * (c0[3] + c1[3])];
    this.addStop(cA, 0.5 * (o0 + o1));
    this.drawBackGround();
  },

  setStopColor : function (value, i, thumb) {
    thumb = typeof thumb == 'undefined' ? this.lastClicked : thumb;
    this.stops[thumb].color[i] = value;
    this.drawBackGround();
  },

});



Ext.define('BQ.viewer.Volume.transferGraph', {
  //extend : 'Ext.Component',
  extend : 'Ext.container.Container',
  alias : 'widget.transfer-graph',
  layout : 'fit',
  
  getStop : function (offset, color) {
    svgStop = '<stop offset="' + offset +
      '%" stop-color="rgba(' +
      color[0] + ', ' +
      color[1] + ', ' +
      color[2] + ', ' +
      color[3] + ')"/>\n';
    return svgStop;
  },

  getGradSvg : function (stops) {
    var me = this;
    var grad1 = ['<defs>',
      '<linearGradient id="transfer" ',
      'x1="0%" y1="0%" x2="0%" y2="100%">\n'
    ].join(' ');

    stops.each(function (record) {
      var color = record.data.color;
      color[3] = 1.0;
      grad1 += me.getStop(record.data.offset, color);
    });

    grad1 += '</linearGradient> </defs>';
    return grad1;
  },

  getGrad : function (id, angle, stops) {
    var stopSvg = {};

    stops.each(function (record) {
      var color = record.data.color;
      stopSvg[record.data.offset / 100] = {
        color : 'rgb(' +
        color[0] + ', ' +
        color[1] + ', ' +
        color[2] + ')'
      }
    });
    /*
    for (var i = 0; i < stops.length; i++) {
    stopSvg[stops[i].offset] = {
    color : 'rgb(' +
    stops[i].color[0] + ', ' +
    stops[i].color[1] + ', ' +
    stops[i].color[2] + ')'
    }
    };
     */
    gradSvg = {
      id : id,
      angle : angle,
      stops : stopSvg,
    };
    return gradSvg;
  },

  updateChartSurface : function () {
    var defs = this.chart.surface.getDefs();
    var oldGrad = this.chart.surface.getDefs().childNodes[0];

    this.chart.surface.getDefs().removeChild(oldGrad);
    var newGrad = this.getGrad('transfer', 0, this.store);
    this.chart.gradients[0] = newGrad;

    gradientEl = this.chart.surface.createSvgElement("linearGradient");
    gradientEl.setAttribute("x1", 0);
    gradientEl.setAttribute("y1", 0);
    gradientEl.setAttribute("x2", 1);
    gradientEl.setAttribute("y2", 0);

    gradientEl.id = newGrad.id;
    this.chart.surface.getDefs().appendChild(gradientEl);
    var me = this;
    this.store.each(function (record) {
      //var color = record.data.color;
      var stop = record.data;
      var color= 
         'rgb(' +
        stop.color[0] + ', ' +
        stop.color[1] + ', ' +
        stop.color[2] + ')';
      
      var stopEl = me.chart.surface.createSvgElement("stop");
      stopEl.setAttribute("offset", stop.offset + "%");
      stopEl.setAttribute("stop-color", color);
      stopEl.setAttribute("stop-opacity", 1.0);
      gradientEl.appendChild(stopEl);
    });
    this.chart.redraw();

  },
  
  getCount : function(){
    return this.store.getCount() 
  },
  
  getStop : function(i){
    return this.store.getAt(i).data;
  },
  
  constructor: function(config){
    
    this.addEvents('selected');
    this.listeners = config.listeners;
    this.callParent(arguments);
  },
  
  initComponent : function () {
    this.lastClicked = 0;
    
    Ext.define('transferStops', {
      extend : 'Ext.data.Model',
      fields : ['color', 'alpha', 'offset']
    });

    this.stops = [{
        color : [0, 0, 0],
        alpha : 0,
        offset : 0
      }, {
        color : [255, 255, 255],
        alpha : 1,
        offset : 100
      }, ];

    var fields = ['offset', 'alpha'];

    this.store = Ext.create('Ext.data.JsonStore', {
        model : 'transferStops',
        fields : fields,
        data : this.stops,
        sorters : [{
            sorterFn : function (o1, o2) {
              var off1 = o1.get('offset');
              var off2 = o2.get('offset');
              if (off1 === off2) {
                return 0;
              }
              return off1 < off2 ? -1 : 1;
            }
          }
        ],

      });

    selectedNode = null;
    var me = this;
    var moveNode = function (e, eOpts) {
      var mxy = e.getXY();
      var cxy = me.chart.getXY();
      var dxy = [mxy[0] - cxy[0], mxy[1] - cxy[1]];
      var bcx = selectedNode.series.bbox.x;
      var bcy = selectedNode.series.bbox.y;
      var blx = selectedNode.series.bbox.width;
      var bly = selectedNode.series.bbox.height;

      var axes = selectedNode.series.chart.axes;
      var xmin = axes.get("bottom").minimum;
      var xmax = axes.get("bottom").maximum;
      var ymin = axes.get("left").minimum;
      var ymax = axes.get("left").maximum;
      var dx = (xmax - xmin) / blx;
      var dy = (ymax - ymin) / bly;

      var offset = dx * (dxy[0] - bcx);
      var alpha = dy * (bly - (dxy[1] - bcy));
      offset = offset >= 100 ? 100 : offset;
      offset = offset <=   0 ?   0 : offset;
      alpha = alpha >= 1 ? 1 : alpha;
      alpha = alpha <= 0 ? 0 : alpha;
      var data = selectedNode.storeItem.data;
      
      if(me.lastClicked != 0 && me.lastClicked != me.store.getCount() - 1){
        data.offset = offset;
      }
      data.alpha = alpha;
      //clamp values
  
      me.fireEvent('update', me, me.lastClicked);
      me.updateChartSurface();
      //console.log(me.chart);
      me.chart.redraw();
    };

    this.chart = Ext.create('Ext.chart.Chart', {
        style : 'background:#fff',
        animate : false,
        //theme : 'Browser:gradients',
        defaultInsets : 30,
        store : this.store,
        gradients : [this.getGrad('transfer', 0, this.store)],
        axes : [{
            type : 'Numeric',
            position : 'left',
            fields : ['alpha'],
            minimum : 0,
            maximum : 1
          }, {
            type : 'Numeric',
            position : 'bottom',
            fields : ['offset'],
            minimum : 0,
            maximum : 100
          }
        ],
        series : [{
            type : 'line',
            axis : 'left',
            //highlight : true,
            markerConfig : {
              type : 'circle',
              size : 4,
              radius : 4,
              fill : 'rgb(0,0,0)',
              'stroke-width' : 0
            },
            listeners : {
              itemmousedown : function (curRecord, eopts) {
                selectedNode = curRecord;

                var oldRecord = me.chart.series.items[0].items[me.lastClicked];
                //oldRecord.sprite.fill =  "rgb(0,0,0)";
                oldRecord.sprite.setStyle('fill','rgb(1,0,0)');
                oldRecord.sprite.setAttributes({
                  scale:{x: 1.0, y: 1.0}
                });
                
                me.lastClicked = me.store.data.indexOf(selectedNode.storeItem);
                selectedNode.sprite.setStyle('fill','rgb(1,0,0)');
                selectedNode.sprite.setAttributes({
                  scale:{x: 1.5, y: 1.5}
                });

                me.chart.redraw();
                me.fireEvent('selected', me, me.lastClicked);
                me.chart.on('mousemove', moveNode, null);

              },
              
              itemmouseup : function (item, eopts) {
                selectedNode = null;
                me.fireEvent('finishupdate', me, me.lastClicked);
                me.chart.un('mousemove', moveNode);
              }
            },
            /*
            tips : {
            trackMouse : true,
            renderer : function (storeItem, item) {
            var d = Ext.Date.format(new Date(storeItem.get('date')), 'M y'),
            percent = storeItem.get(item.storeField) + '%';

            this.setTitle(item.storeField + ' - ' + d + ' - ' + percent);
            }
            },
             */
            xField : 'offset',
            yField : 'alpha',
            fill : true,
            style : {
              fill : 'url(#transfer)',
              lineWidth : 0.5,
              stroke : '#666',
              opacity : 0.86
            }
          }
        ],
        /*
        listeners:{
        mousemove: function(e, eOpts){
        console.log(selectedNode, e);

        },

        }
         */
      });
    this.transferGradient = document.getElementById('transfer');

    this.items = [this.chart];
    
    this.callParent();
  },

  afterFirstLayout : function () {

    var sprite = this.chart.series.items[0].items[0].sprite;
    console.log("sprite: ", sprite);
    sprite.setAttributes({
      fill : 'url(#transfer)'
    }, true);
    this.updateChartSurface();
  },

  sortKeys : function () {
    this.stops.sort(function (a, b) {
      return (a.offset - b.offset);
    });
  },

  scaleKeys : function (newScale) {
    var oldScale = this.maxValue;
    if (oldScale == 0)
      return;
    var scale = newScale / oldScale;

    for (var i = 0; i < this.thumbs.length; i++) {
      var newVal = this.thumbs[i].value * scale;
      this.thumbs[i].value = newVal;
    }
  },

  addStop : function (rgb, alpha, offset) {
    var data = Ext.create('transferStops', {
        color : rgb,
        alpha : alpha,
        offset : offset,
      });
    //this.stops.push(data);
    //this.sortKeys();
    this.store.addSorted(data);

    this.updateChartSurface();
    //console.log(grad, this.chart.el, this.chart.el.dom.firstChild);

    this.store.fireEvent('refresh');
    this.chart.redraw();

    console.log(this.chart);

  },

  removeStop : function (it) {
    var rec = this.store.getAt(it);  
    this.store.remove(rec);
    
    console.log(this.store);
  },

  removeCurrentStop : function () {
    this.removeStop(this.lastClicked);
    this.store.fireEvent('refresh');
    this.chart.redraw();
    this.updateChartSurface();

    //this.drawBackGround();
  },
  
  getRgb : function(i){
  var col = this.store.getAt(i).data.color;
  col[3] = this.store.getAt(i).data.alpha;
    return col;
  },
  
  addNextStop : function () {
    var i0 = this.lastClicked;
    var i1 = i0 + 1;

    if (i0 == this.stops.length - 1)
      i1 = i0 - 1;
    var o0 = this.store.getAt(i0).data.offset;
    var o1 = this.store.getAt(i1).data.offset;
    var a0 = this.store.getAt(i0).data.alpha;
    var a1 = this.store.getAt(i1).data.alpha;
    var c0 = this.store.getAt(i0).data.color;
    var c1 = this.store.getAt(i1).data.color;
    
    var cA = [Math.floor(0.5 * (c0[0] + c1[0])),
              Math.floor(0.5 * (c0[1] + c1[1])),
              Math.floor(0.5 * (c0[2] + c1[2]))]
     
    //var cA = [Math.random(), Math.random(), Math.random()];
    this.addStop(cA, 0.5 * (a0 + a1), 0.5 * (o0 + o1));
    //this.lastClicked++;
    //this.drawBackGround();
  },

  setStopColor : function (value,thumb) {
    thumb = typeof thumb == 'undefined' ? this.lastClicked : thumb;
  
    this.store.getAt(thumb).data.color[0] = value[0];
    this.store.getAt(thumb).data.color[1] = value[1];
    this.store.getAt(thumb).data.color[2] = value[2];
    this.store.getAt(thumb).data.alpha = value[3];

    
    this.updateChartSurface();
    //this.stops[thumb].color[i] = value;
    //this.drawBackGround();
  },
});

Ext.define('BQ.viewer.Volume.transfer', {
  extend : 'Ext.container.Container',
  //cls : 'materialcontroller',
  alias : 'widget.transfer',
  
  mixins : ['BQ.viewer.Volume.uniformUpdate'],
  addUniforms : function () {
    this.tSize = 64;
    this.sceneVolume.initUniform('transfer', "t", null);
    this.sceneVolume.initUniform('TRANSFER_SIZE', "i", this.tSize);
    this.sceneVolume.initUniform('USE_TRANSFER', "i", this.transfer);
  },

  changed : function () {
    if (this.transferGraph.getCount() < 2)
      return;
    var pixels = new Uint8Array(4*this.tSize);
    var cStop = 0;
    var ci = 0;
    var l = this.transferGraph.getCount();
    var stop0 = this.transferGraph.getStop(0);
    var stop1 = this.transferGraph.getStop(l-1);
    
    if (this.transferGraph.getStop(0).offset != 0)
      return;
    if (this.transferGraph.getStop(l - 1).offset != 100)
      return;
      
    for (var i = 0; i < this.tSize; i++) {
      var stop = this.transferGraph.getStop(cStop);
      var nstop = this.transferGraph.getStop(cStop + 1);
      
      var per = ci / this.tSize * 100;

      if (per > nstop.offset - stop.offset) {
        ci = 0;
        cStop++;
        stop = this.transferGraph.getStop(cStop);
        nstop = this.transferGraph.getStop(cStop + 1);
        console.log("new stops: ", cStop, stop, nstop);
      }

      var t = ci / this.tSize * 100 / (nstop.offset - stop.offset);
      //console.log(t, cStop, per, stop, nstop);
      var c0 = stop.color;
      var c1 = nstop.color;
      c0[3] = stop.alpha;
      c1[3] = nstop.alpha;
      //console.log(i,ci, per,t,nstop.offset,stop.offset);
      pixels[4 * i + 0] = (1 - t) * c0[0] + t * c1[0];
      pixels[4 * i + 1] = (1 - t) * c0[1] + t * c1[1];
      pixels[4 * i + 2] = (1 - t) * c0[2] + t * c1[2];
      pixels[4 * i + 3] = 255 * ((1 - t) * c0[3] + t * c1[3]);
      ci++;
    }
    //conso
    var rampTex = this.panel3D.rampTex;
    rampTex = new THREE.DataTexture(pixels, this.tSize, 1, THREE.RGBAFormat);
    rampTex.needsUpdate = true;
    this.sceneVolume.setUniform('transfer', rampTex);
    this.sceneVolume.setUniform('TRANSFER_SIZE', this.tSize);
  },

  initComponent : function () {
    var me = this;
    this.transfer = 0;
    this.title = 'transfer';
    var controlBtnSize = 22;

    var useTransfer = Ext.create('Ext.form.field.Checkbox', {
        boxLabel : 'use transfer function',
        height : controlBtnSize,
        checked : false,
        handler : function () {
          this.transfer ^= 1;
          this.changed();
          this.sceneVolume.setUniform('USE_TRANSFER', this.transfer);
          if (this.transfer == 1) {
            this.showButton.show();
          } else
            this.showButton.hide();

        },
        scope : me,
      });

    this.transferGraph = Ext.create('BQ.viewer.Volume.transferGraph', {
      listeners : {
        selected : function(graph, i){
            var c = graph.getRgb(i);
            if(me.colorWindow)
              me.colorPicker.setColorRgb(c[0] / 255, c[1] / 255, c[2] / 255, c[3]);
        },
        finishupdate : function(graph, i){
            var c = graph.getRgb(i);
            if(me.colorWindow)
              me.colorPicker.setColorRgb(c[0] / 255, c[1] / 255, c[2] / 255, c[3]);
        }
      }
    });

    this.transferSlider = Ext.create('BQ.viewer.Volume.transferSlider', {
        //tic:      this.tic,
        panel3D : this.panel3D,
        flex : 1,
        animate : false,
        margin : '2 2 2 2',
        listeners : {
          clicked : function (slider, thumb) {
            console.log(slider, thumb);
            var c = slider.stops[thumb].color;
            me.colorPicker.setColorRgb(c[0] / 255, c[1] / 255, c[2] / 255, c[3]);
          },
          change : function (slider, value, thumb) {
            var l = slider.thumbs.length;
            if (thumb.index == 0) {
              slider.setValue(0, 0);
            }
            if (thumb.index == l - 1) {
              slider.setValue(l - 1, 100);
            }
            me.changed();
          },
          scope : me
        },
        useTips : true,
      });
    this.addUniforms();
    this.isLoaded = true;

    this.showButton = Ext.create('Ext.Button', {
        text : 'edit transfer function',
        handler : function (button, pressed) {
          console.log("twindow: ", this.transferWindow);

          if (!this.transferWindow)
            me.displayTransferWindow();
          else
            this.transferWindow.show();
        },
        scope : me,
      });

    this.colorPicker = Ext.create('BQ.viewer.Volume.excolorpicker', {
        listeners:{
        change : function (picker) {
          var rgb = picker.getColorRgb();
          var color = [Math.floor(rgb[0]), Math.floor(rgb[1]), Math.floor(rgb[2]), rgb[3]]
          me.transferGraph.setStopColor(color);
          me.changed();
        }
        }
      });

    this.showButton.hide();
    this.addUniforms();
    Ext.apply(this, {
      items : [useTransfer, this.showButton],
    });

    this.callParent();
  },

  displayTransferWindow : function () {
    var me = this;
    var addButton = Ext.create('Ext.Button', {
        text : '+',
        //cls: 'volume-button',
        handler : function (button, pressed) {
          me.transferGraph.addNextStop();
        },
        scope : me,
      });

    var subButton = Ext.create('Ext.Button', {
        text : '-',
        //cls: 'volume-button',
        handler : function (button, pressed) {
          me.transferGraph.removeCurrentStop();
          //me.displayParameterWindow();
        },
        scope : me,
      });

    var showColorButton = Ext.create('Ext.Button', {
        text : 'show color',
        handler : function (button, pressed) {
          if (!this.colorWindow)
            me.displayColorWindow();
          else
            this.colorWindow.show();

        },
        scope : me,
      });

    this.transferWindow = Ext.create('Ext.window.Window', {
        title : 'transfer function',
        height : 250,
        width : 800,
        layout : 'fit',
        items : [this.transferGraph],
        bbar : {
          items : [addButton, subButton, showColorButton]
        },
        closeAction : 'hide',
      }).show();

  },

  displayColorWindow : function () {
    var me = this;
    this.colorWindow = Ext.create('Ext.window.Window', {
        title : 'color window',
        height : 250,
        width : 300,
        layout : 'fit',
        items : [this.colorPicker],

        closeAction : 'hide',
      }).show();

  },

  afterFirstLayout : function () {
    //this.transferSlider.show();
    this.changed();
  },
});