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



