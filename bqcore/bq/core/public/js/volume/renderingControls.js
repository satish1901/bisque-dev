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
    updateSlider: function(slider,value){
        this.sceneVolume.setUniform(slider.uniform_var, slider.convert(value), true);
    },
});

//////////////////////////////////////////////////////////////////
//
// info from the graphics card
//
//////////////////////////////////////////////////////////////////

Ext.define('BQ.viewer.Volume.glinfo', {
    extend: 'Ext.container.Container',
    cls: 'glinfo',
    alias: 'widget.glinfo',

    changed : function(){
	    if(this.isLoaded){
      	}
    },

    addUniforms : function(){
    },

    displayParameterWindow : function(){
	    var store = Ext.create('Ext.data.ArrayStore', {
	        fields: [
		        {name: 'parameter'},
		        {name: 'value'},
	        ],
	        data: this.params,
	    });

	    Ext.create('Ext.window.Window', {
	        title: 'gl info',
	        height: 200,
	        width: 400,
	        layout: 'fit',
	        items: {  // Let's put an empty grid in just to illustrate fit layout
		        xtype: 'grid',
		        border: false,
		        columns: [
		            {
			            text     : 'Parameter',
			            flex     : 1,
			            sortable : false,
			            dataIndex: 'parameter'
		            },{
			            text     : 'Value',
			            flex     : 1,
			            sortable : false,
			            dataIndex: 'value'
		            },],                 // One header just for show. There's no data,
		        store: store,
	        }
	    }).show();
    },

    initParameters : function(){
    	this.params = new Array();
	    var ctx = this.canvas3D.renderer.getContext();
	    this.params[0] = ['Platform',  navigator.platform];
	    this.params[1] = ['Agent',     navigator.userAgent];
	    if(ctx){
            console.log('opengl context: ', ctx);
	        this.params[2] = ['Vendor',  ctx.getParameter(ctx.VENDOR)];
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

            this.params[13] = ['Max vertex uniform vectors', ctx.getParameter(ctx.MAX_VERTEX_UNIFORM_VECTORS)];
	        //this.params[13] = ['Max Cube Map Texture', ctx.getParameter(ctx.MAX_CUBE_MAP_TEXTURE_SIZE)];

            this.params[20] = ['Max Viewport Dimensions', ctx.getParameter(ctx.MAX_VIEWPORT_DIMS)];
	        this.params[21] = ['Aliased Line Width Range', ctx.getParameter(ctx.ALIASED_LINE_WIDTH_RANGE)];
	        this.params[22] = ['Aliased Point Size Range', ctx.getParameter(ctx.ALIASED_POINT_SIZE_RANGE)];

            for(var i = 0; i < this.params.length; i++ ){

		        var tmp = '';

		        if(typeof(this.params[i][1]) === 'string') continue;
		        if(typeof(this.params[i][1]) === 'number') continue;
		        var field = this.params[i][1];
		        if(!field) continue;

                for(var j = 0; j < this.params[i][1].length; j++ ){
		            tmp += field[j];
		            if(j < field.length - 1)
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

    initComponent : function(){
	    this.initParameters();
	    var me = this;
	    var button = Ext.create('Ext.Button', {
	        text: 'show gl info',
	        cls: 'volume-button',
	        handler: function(button, pressed) {
		        me.displayParameterWindow();
	        },
	        scope:me,
	    });
	    Ext.apply(this, {
	        items:[
		        button
	        ],
	    });
	    this.callParent();
    },

    afterFirstLayout : function(){
    },
});

//////////////////////////////////////////////////////////////////
//
// Gamma controller
//
//////////////////////////////////////////////////////////////////

Ext.define('BQ.viewer.Volume.gammapanel', {
    extend: 'Ext.container.Container',
    alias: 'widget.gamma',
    border: false,

    addUniforms : function(){
        this.sceneVolume.initUniform('GAMMA_MIN', "f", 0.0);
	    this.sceneVolume.initUniform('GAMMA_MAX', "f", 1.0);
        this.sceneVolume.initUniform('GAMMA_SCALE', "f", 0.5);
    },

    fetchHistogram : function(){
	    url = this.panel3D.constructAtlasUrl() + '&histogram';

        var xRes;
        var yRes;
        Ext.Ajax.request({
	        url : url,
	        scope : this,
	        disableCaching : false,
	        callback : function(opts, succsess, response) {
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

    genHistogramSvg : function(hist, color){
	    if(this.data == null) return;
	    if(hist == null) return;

	    var maxVal = 0;
	    var minVal = 999;
	    var min = this.data.min;
	    var max = this.data.max;
	    var C = this.data.scale;
	    //var C = 1.0;
	    var start = Math.floor(this.data.min*hist.length);
	    var end   = Math.floor(this.data.max*hist.length);

	    var newHist = new Array();
	    var lookUp = new Array();
	    var avg = 0;
	    for(var i = 0; i < hist.length; i++){
	        var val = parseInt(hist[i]);
	        avg += val;
	        minVal = val < minVal ? val : minVal;
	        maxVal = val > maxVal ? val : maxVal;
	    }

	    avg /= hist.length;

        for(var i = 0; i < hist.length; i++){
	        lookUp[i] = 0;
	        newHist[i] = 0;
	        if(i > start && i < end) {
		        var val  = (i-start)/(end-start);
		        var plogy = C*Math.log(i);
		        var modVal = Math.exp(plogy);
		        var newBin = Math.ceil(modVal);
		        newBin = newBin < hist.length-1 ? newBin:hist.length-1;
		        lookUp[i] = newBin;
	        }
	    }

	    for(var i = 1; i < lookUp.length-1; i++){
	        newHist[lookUp[i]-1] += 0.25*parseInt(hist[i]);
	        newHist[lookUp[i]+0] += 0.5*parseInt(hist[i]);
	        newHist[lookUp[i]+1] += 0.25*parseInt(hist[i]);
	    }
	    maxVal = maxVal < 1 ? 1 : maxVal;

	    var h = this.getHeight();
	    var w = this.getWidth();

	    var yMargin = 2;
	    var xMargin = 16;
	    var hh = h -2.0*yMargin;
	    var wh = w - 2.0*xMargin;
	    var x0 = xMargin;
	    var y0 = hh - yMargin;
	    var path = x0.toString() + ' ' + (y0-8).toString();

	    var N = wh; var dataScale = 1.0;
	    var dx = wh/newHist.length;

	    for(var i = 0; i < newHist.length; i++){
	        var x = i;
	        x = x0 + i*dx;
            var y = 0.0;
	        if(newHist[i] > 0){
		        //y = 0.1*Math.log(newHist[i]);
                if(0.5*(avg + minVal) > 0.0 )
		            y = newHist[i]/(0.5*(avg + minVal));
	        }
	        else
		        y = 0;
	        //console.log(i, newHist[i], y);
	        y = y0 - hh*y;
	        //console.log(i,newHist[i],(avg),newHist[i]/(avg));
	        path += ' ' + x.toString() + ' ' + y.toString();
	    }
	    path += ' ' + (x0 + end - start).toString() + ' ' + y0.toString();
	    var pathOpen  = '<path d="M'
	    var pathClose0 = '" stroke = '+color+' opacity=0.8 stroke-width=1 fill = none />';
	    var pathClose1 = '" stroke = none opacity=0.15 stroke-width=1 fill='+color+' />';

	    var graph = pathOpen + path + pathClose0 + pathOpen + path + pathClose1;
	    var svg = '<svg width=100% height=100% > <' + graph + ' </svg>';
	    return svg;
    },

    updateColorSvg : function(){
	    if(this.data == null) return;
	    var C = this.data.scale;
	    var min = this.data.min;
	    var max = this.data.max;
	    var h = this.getHeight();
	    var w = this.getWidth();

	    var yMargin = 16;
	    var xMargin = 16;
	    var hh = h -2.0*yMargin;
	    var wh = w - 2.0*xMargin;
	    var x0 = xMargin;
	    var y0 = hh + yMargin;

	    var path = x0.toString() + ' ' + (y0-8).toString();
	    var mid = 0.5*(min+max);
	    var N = wh; var dataScale = 1.0;
	    for(var i = 0; i < N; i++){
	        var x = i;
	        var t = i/N*dataScale;
	        var xi = (t-min)/(max-min);
	        var plogy = C*Math.log(xi);
	        var y = Math.exp(plogy);
	        if(t < min) y = 0;
	        if(t > max) y = 1.0;
	        x = x0 + x;
	        y = y0 - 8 - hh*y;
	        path += ' ' + x.toString() + ' ' + y.toString();
	    }

	    var pathOpen  = '<path d="M'
	    var pathClose1 = '" stroke = gray stroke-width=1 fill="none" />';
	    var pathClose3 = '" stroke = white stroke-width=1 opacity: 0.7 fill="none" />';
	    var xAxis = pathOpen + x0 + ' ' + y0 + ' ' + 0.95*w + ' ' + y0 + pathClose1;
	    var yAxis = pathOpen + x0 + ' ' + y0 + ' ' + x0     + ' ' + y0-hh + pathClose1;
	    var graph = pathOpen + path + pathClose3;
	    var svg = ' <svg width=100% height=100% > <' + xAxis + yAxis + graph + ' </svg>';
	    var rH = this.genHistogramSvg(this.rHist,'red');
	    var gH = this.genHistogramSvg(this.gHist,'green');
	    var bH = this.genHistogramSvg(this.bHist,'blue');

	    this.rampSvg.getEl().dom.innerHTML = ' <svg width=100% height=100% >' + rH + gH + bH + svg + '</svg>';

    },

    getVals : function(min, mid, max){
	    var div = this.getWidth();
	    min /= div;
	    max /= div;
	    var diff = max - min;
	    var x = (mid/div - min)/diff;
	    scale = 4*x*x;
	    return {min: min,
		        scale: scale,
		        max: max};
    },

    initComponent : function(){

	    this.title = 'gamma';
	    var me = this;

	    this.addUniforms();
	    this.fetchHistogram();

	    this.contrastRatio = 0.5;
	    this.slider0 = Ext.create('Ext.slider.Multi', {
            //renderTo: 'multi-slider-horizontal',
            hideLabel: true,
	        fieldLabel: 'gamma',
	        increment: 1,
            values: [10, 50, 90],
            listeners: {
		        change: function(slider, value, thumb) {
		            var div = 200;
		            var minThumb = slider.thumbs[0].value;
		            var conThumb = slider.thumbs[1].value;
		            var maxThumb = slider.thumbs[2].value;

		            var min = minThumb/div;
		            var max = maxThumb/div;
		            var diff = max - min;
		            var x = (conThumb/div - min)/diff;

		            var vals = this.getVals(minThumb,conThumb, maxThumb);


		            if(thumb.index != 1){
			            var posDiff = maxThumb - minThumb;
			            var newVal = this.contrastRatio*posDiff + minThumb;
			            slider.setValue(1,newVal,false);
			            this.middleThumbLock = true;
			            var me = this;
			            setTimeout(function(){
			                me.middleThumbLock = false;
			            },200);
		            } else{
			            if(this.middleThumbLock == false)
			                this.contrastRatio = (conThumb-minThumb)/(maxThumb-minThumb);
		            }

		            var p = 4;
                    this.sceneVolume.setUniform('GAMMA_MIN', vals.min);
	                this.sceneVolume.setUniform('GAMMA_MAX', vals.max);
	                this.sceneVolume.setUniform('GAMMA_SCALE', vals.scale);

		            this.data = vals;
		            //this.canvasPanel.redraw();
		            this.updateColorSvg();

		        },
		        scope:me,
            }
	    });

	    this.data = {min:0,max:0,scale:0};
	    this.rampSvg = Ext.create('Ext.Component',{
	        height: 60,
	    });


	    Ext.apply(this, {
	        items:[ this.rampSvg, this.slider0,],
	    });

	    this.callParent();
    },

    afterFirstLayout : function(){
 	    this.callParent();
	    this.slider0.setMinValue(0.0);
	    this.slider0.setMaxValue(100);
	    var vals = this.getVals(this.slider0.thumbs[0].value,
				                this.slider0.thumbs[1].value,
				                this.slider0.thumbs[2].value);
	    this.data = vals;
        this.slider0.setValue(0,5);
	    this.slider0.setValue(1,55);
        this.slider0.setValue(2,95);
        this.updateColorSvg();
    },
});

Ext.define('BQ.viewer.Volume.materianel', {
    extend: 'Ext.container.Container',
    cls: 'materialcontroller',
    alias: 'widget.material',
    mixins:['BQ.viewer.Volume.uniformUpdate'],
    addUniforms : function(){
        this.sceneVolume.initUniform('brightness', "f", 0.5);
	    this.sceneVolume.initUniform('density', "f", 0.5);
    },

    initComponent : function(){
	    var me = this;

	    this.addUniforms();
	    this.isLoaded = true;

	    this.title = 'material';
	    this.density = 0.5;
	    this.brightness = 1.0;
	    this.densitySlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
	        fieldLabel: 'density',
	        labelWidth: 60,
            minValue: 0,
            maxValue: 100,
            value: 50,
            uniform_var: 'density',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/500.0}
	    });

	    this.brightnessSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            //hideLabel: true,
	        fieldLabel: 'brightness',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 50,
            uniform_var: 'brightness',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/20;}

	    });


	    //modal: true,
	    //this.items = [this.canvasPanel, slider0, this, slider4];
	    Ext.apply(this, {
	        items:[this.densitySlider, this.brightnessSlider],
	    });

	    this.callParent();
    },

    afterFirstLayout : function(){
	    this.densitySlider.setValue(50);
	    this.brightnessSlider.setValue(75);
    },
});

Ext.define('BQ.viewer.Volume.lightpanel', {
    extend: 'Ext.container.Container',
    alias: 'widget.lighting',
    mixins:['BQ.viewer.Volume.uniformUpdate'],

    changed : function(){
        console.log("scene: ", this.sceneVolume);
        this.sceneVolume.loadMaterial(this.materials[this.state]);
    },

    initMaterials : function(){
        this.materials = ['diffuse', 'volumeLighting',
                          'phongLighting', 'phongAndVolumeLighting'];

        this.sceneVolume.initMaterial({
            name:    'volumeLighting',
            vertConfig:{
                url: "/js/volume/shaders/rayCast.vs"
            },
            fragConfig: {
                id: 'volumeLighting',
                url: "/js/volume/shaders/rayCastBlocks.fs",
                manipulate: function(text){
                    return text.replace("LIGHTING 0", "LIGHTING 1");
                }
            }
        });

        this.sceneVolume.initMaterial({
            name:    'phongLighting',
            vertConfig:{
                url: "/js/volume/shaders/rayCast.vs"
            },
            fragConfig: {
                id: 'phongLighting',
                url: "/js/volume/shaders/rayCastBlocks.fs",
                manipulate: function(text){
                    return text.replace("PHONG 0", "PHONG 1");
                }
            }
        });

        this.sceneVolume.initMaterial({
            name:    'phongAndVolumeLighting',
            vertConfig:{
                url: "/js/volume/shaders/rayCast.vs"
            },
            fragConfig: {
                id: 'phongAndVolumeLighting',
                url: "/js/volume/shaders/rayCastBlocks.fs",
                manipulate: function(text){
                    var phong = text.replace("PHONG 0", "PHONG 1");
                    return phong.replace("LIGHTING 0", "LIGHTING 1");
                }
            }
        });
    },

    addUniforms : function(){
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

    initComponent : function(){
	    this.state = 0;
        this.title = 'lighting';
	    var me = this;
	    this.addUniforms();
	    this.initMaterials();

	    this.lighting = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'Advanced Rendering',
	        checked: false,
	        handler: function(){
		        this.state ^= 1;
		        this.changed();
		        if( (this.state&1) === 1){
		            this.depthSlider.show();
		            this.sampleField.show();
		            this.dispSlider.show();
		            this.dispAmtSlider.show();
		        } else {
		            this.depthSlider.hide();
		            this.sampleField.hide();
		            this.dispSlider.hide();
		            this.dispAmtSlider.hide();
		        }
                this.panel3D.rerender();
	        },
	        scope:me,
	    });

	    this.specular = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'Phong Rendering',
	        checked: false,
	        handler: function(){
		        this.state ^= 2;
		        this.changed();
		        if( (this.state & 2) === 2){
		            this.kaSlider.show();
		            this.kdSlider.show();
		            this.normInSlider.show();
		            this.specSizeSlider.show();
		            this.specInSlider.show();
		        } else {
		            console.log(this.state&2, "hide");
		            this.kaSlider.hide();
		            this.kdSlider.hide();

		            this.normInSlider.hide();
		            this.specSizeSlider.hide();
		            this.specInSlider.hide();
		        }
                this.panel3D.rerender();
	        },
	        scope:me,
	    });

	    this.depthSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'depth',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 75,
            uniform_var: 'LIGHT_DEPTH',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/50;}
	    }).hide();

	    this.dispSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'R_dispersion',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 75,
           uniform_var: 'DISPERSION',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/50;}
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
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'Ambient',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 75,
            uniform_var: 'KA',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/100;}
	    }).hide();

	    this.kdSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'diffuse',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 75,
            uniform_var: 'KD',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/100;}
	    }).hide();

	    this.normInSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'edges',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 75,
            uniform_var: 'NORMAL_INTENSITY',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/5.0;}
	    }).hide();

	    this.specSizeSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'size',
	        labelWidth: 60,
            minValue: 2.00,
            maxValue: 50,
            value: 10.0,
            uniform_var: 'SPEC_SIZE',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v;}
	    }).hide();

	    this.specInSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'intensity',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 20,
            value: 0.0,
            uniform_var: 'SPEC_INTENSITY',
            listeners: {
                change: this.updateSlider,
                scope: me,
            },
            convert: function(v) { return v/1.0;}
	    }).hide();


	    this.sampleField = Ext.create('Ext.form.field.Number', {
            name: 'numberfield2',
            fieldLabel: 'samples',
            value: 4,
            minValue: 0,
            maxValue: 16,
            width: 150,
            listeners: {
		        change: function(field, newValue, oldValue) {
                    this.sceneVolume.setUniform('LIGHT_SAMPLES', newValue);
		        },
		        scope:me
            },
	    }).hide();

	    //modal: true,
	    //this.changed();
	    this.items = [this.lighting,
		              this.sampleField, this.depthSlider,
		              this.dispSlider,// this.dispAmtSlider,
		              this.specular, this.kaSlider, this.kdSlider,
		              this.normInSlider, this.specInSlider, this.specSizeSlider];
	    this.changed();
	    this.callParent();
    },
    afterFirstLayout : function(){
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
    extend: 'Ext.container.Container',
    alias: 'widget.lightControl',

    changed : function(){
	    if(this.isLoaded){
            this.sceneVolume.setUniform('LIGHT_POSITION', this.lightObject.position);
	    }
    },

    addUniforms : function(){
	    this.sceneVolume.initUniform('LIGHT_POSITION', "v3", this.lightObject.position);
    },

    initComponent : function(){
        this.title = 'light control';
	    var me = this;
	    this.dist = 1.0;
        this.state = false;
	    this.lighting = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'Modify Light Location',
	        checked: false,
	        handler: function(){
		        this.state ^= 1;
		        this.changed();
		        if((this.state&1) === 1){
                    this.lightObject.visible = true;
		        } else {
                    this.lightObject.visible = false;
		        }
                this.panel3D.rerender();
	        },
	        scope:me,
	    });


        this.distanceSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'distance',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            value: 75,
            listeners: {
		        change: function(slider, value) {
		            this.dist = value/25;
		            this.changed();
		        },
		        scope:me,
            }
	    }).show();

        var me = this;
        var sphere = new THREE.SphereGeometry(0.05,3,3);
        this.lightObject = new THREE.Mesh( sphere,
                                            new THREE.MeshBasicMaterial( {
                                                color: 0xFFFF33,
                                                wireframe: true,
                                            } ) );
        this.sceneVolume.scene.add(this.lightObject);

        this.plane = new THREE.Mesh( new THREE.PlaneGeometry( 2000, 2000, 8, 8 ),
                                new THREE.MeshBasicMaterial( {
                                    color: 0x000000,
                                    opacity: 0.25,
                                    transparent: true,
                                    wireframe: true } ) );
		this.plane.visible = false;
		this.lightObject.visible = false;

        this.sceneVolume.scene.add( this.plane );
        this.lightObject.position.x = 0.0;
		this.lightObject.position.y = 0.0;
		this.lightObject.position.z = 1.0;
        this.sceneVolume.scene.add(this.lightObject);
        this.canvas3D.getEl().dom.addEventListener('mousemove', me.onMouseMove.bind(this),true);
        this.canvas3D.getEl().dom.addEventListener('mouseup', me.onMouseUp.bind(this),true);
        this.canvas3D.getEl().dom.addEventListener('mousedown', me.onMouseDown.bind(this),true);
        this.offset = new THREE.Vector3(),


	    this.addUniforms();
	    this.isLoaded = true;
	    this.changed();
	    this.items = [this.lighting];
	    this.callParent();
    },

    onAnimate : function(){
    },

    onMouseUp: function(){
        this.selectLight = false;
    },

    onMouseDown: function(){
        if(this.state === 0) return;
        var width = this.canvas3D.getWidth();
		var height = this.canvas3D.getHeight();
        var cx = this.canvas3D.getX();
        var cy = this.canvas3D.getY();
        var x =  ((event.clientX - cx)/width ) * 2 - 1;
		var y = -((event.clientY - cy)/height) * 2 + 1;

        var vector = new THREE.Vector3( x, y, 0.5 );
        var camera = this.canvas3D.camera;
		this.canvas3D.projector.unprojectVector( vector, camera );

        var raycaster
            = new THREE.Raycaster( camera.position,
                                   vector.sub( camera.position ).normalize() );
        var objects = [this.lightObject];
        var intersects = raycaster.intersectObjects( objects );
        if(intersects.length > 0){
            this.canvas3D.controls.enabled = false;
            this.selectLight = true;
            this.canvas3D.getEl().dom.style.cursor = 'move';
        }
        else{
            this.canvas3D.getEl().dom.style.cursor = 'auto';
        }
    },

    onMouseMove : function(event){
        event.preventDefault();
        if(this.state === 0) return;
        var width = this.canvas3D.getWidth();
		var height = this.canvas3D.getHeight();
        var cx = this.canvas3D.getX();
        var cy = this.canvas3D.getY();
        var x =  ((event.clientX - cx)/width ) * 2 - 1;
		var y = -((event.clientY - cy)/height) * 2 + 1;

		var vector = new THREE.Vector3( x, y, 0.5 );

        var camera = this.canvas3D.camera;
		this.canvas3D.projector.unprojectVector( vector, camera );

        var raycaster
            = new THREE.Raycaster( camera.position,
                                   vector.sub( camera.position ).normalize() );

        var objects = [this.lightObject];
        var intersects = raycaster.intersectObjects( objects );

		if ( this.selectLight ) {
			var intersects = raycaster.intersectObject( this.plane );
			this.lightObject.position.copy( intersects[ 0 ].point.sub( this.offset ) );
			return;
		}
        if(intersects.length > 0){
            this.canvas3D.getEl().dom.style.cursor = 'move';
			this.plane.position.copy( intersects[0].object.position );
			this.plane.lookAt( camera.position );
        }
        else{
            this.canvas3D.getEl().dom.style.cursor = 'auto';
        }

    },

    afterFirstLayout : function(){
	    this.callParent();
    },
});

Ext.define('BQ.viewer.Volume.general', {
    extend: 'Ext.container.Container',
    alias: 'widget.general',

    addUniforms : function(){
	    this.sceneVolume.initUniform('DITHERING', "i", this.dithering);
        this.sceneVolume.initUniform('BOX_SIZE', "v3", this.boxSize);
    },

    initComponent : function(){
        this.title = 'general';
	    var me = this;
	    this.dithering = false;
	    this.showBox = false;
	    this.boxSize = new THREE.Vector3(0.5, 0.5, 0.5);
	    var controlBtnSize = 22;

	    var dith = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'dithering',
	        height: controlBtnSize,
	        checked: false,
	        handler: function(){
                this.dithering ^= 1;
                this.sceneVolume.setUniform('DITHERING', this.dithering);
	        },
	        scope:me,
	    });

	    var showBoxBtn = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'proportions',
	        height: controlBtnSize,
	        checked: false,
	        handler: function(){
		        this.showBox ^= 1;
		        if(this.showBox){
		            this.boxX.show();
		            this.boxY.show();
		            this.boxZ.show();
		        }
		        else{
		            this.boxX.hide();
		            this.boxY.hide();
		            this.boxZ.hide();
		        }
	        },
	        scope:me,
	    });

	    this.boxX = Ext.create('Ext.form.field.Number', {
            name: 'box_x',
            fieldLabel: 'x',
            value: 1,
            minValue: 0.1,
            maxValue: 1,
	        step:0.05,
            width: 150,
            listeners: {
		        change: function(field, newValue, oldValue) {
		            if(typeof newValue != 'number') return;
		            newValue = newValue < 0.1 ? 0.1:newValue;
		            this.boxSize.x = 0.5*newValue;
                    this.sceneVolume.scaleCube(this.boxSize);
		        },
		        scope:me
            },
	    });

	    this.boxY = Ext.create('Ext.form.field.Number', {
            name: 'box_y',
            fieldLabel: 'y',
            value: 1,
            minValue: 0.1,
            maxValue: 1,
	        step:0.05,
            width: 150,
            listeners: {
		        change: function(field, newValue, oldValue) {
		            if(typeof newValue != 'number') return;
		            newValue = newValue < 0.1 ? 0.1:newValue;
		            this.boxSize.y = 0.5*newValue;
		            this.sceneVolume.scaleCube(this.boxSize);
		        },
		        scope:me
            },
	    });

	    this.boxZ = Ext.create('Ext.form.field.Number', {
            name: 'box_z',
            fieldLabel: 'z',
            value: 1,
            minValue: 0.1,
            maxValue: 1,
	        step:0.05,
            width: 150,
            listeners: {
		        change: function(field, newValue, oldValue) {
		            if(typeof newValue != 'number') return;
		            newValue = newValue < 0.1 ? 0.1:newValue;
		            this.boxSize.z = 0.5*newValue;
		            this.sceneVolume.scaleCube(this.boxSize);
		        },
		        scope:me
            },
	    });

	    this.addUniforms();

	    this.boxX.hide();
	    this.boxY.hide();
	    this.boxZ.hide();

	    this.boxSize.x = 0.5;
	    if(this.dims){
            this.boxSize.y = 0.5 * this.dims.pixel.x / this.dims.pixel.y;
            this.boxSize.z = 0.5 * this.dims.pixel.x / this.dims.pixel.z;
	    }
	    else{
	        this.boxSize.y = 0.5;
	        this.boxSize.z = 0.5;
	    }

	    this.boxX.setValue(2.0*this.boxSize.x);
	    this.boxY.setValue(2.0*this.boxSize.y);
	    this.boxZ.setValue(2.0*this.boxSize.z);

	    this.isLoaded = true;
	    this.items = [dith, showBoxBtn, this.boxX,this.boxY,this.boxZ];
	    this.callParent();
    },

    afterFirstLayout : function(){
    },
});

Ext.define('BQ.viewer.Volume.clip', {
    extend: 'Ext.container.Container',
    alias: 'widget.clip',
    border: false,
    addUniforms : function(){
        this.sceneVolume.initUniform('CLIP_NEAR', "f", 0.0);
	    this.sceneVolume.initUniform('CLIP_FAR', "f", 3.0);
    },

    initComponent : function(){
        this.title = 'clipping';
	    var me = this;
	    this.clipNear  = 0.0;
	    this.clipFar   = 3.0;
        //console.log("slider func: ", this.mixins, this.updateSlider);
	    this.clipSlider = Ext.create('Ext.slider.Multi', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'clip',
	        labelWidth: 60,
            minValue: 0.00,
            maxValue: 100,
            values: [0,100],
            uniform_var: 'CLIP_NEAR',
            listeners: {
		        change: function(slider, value, thumb) {
		            if(thumb.index == 0){
                        this.sceneVolume.setUniform('CLIP_NEAR', value/100);
		            } else{
                        this.sceneVolume.setUniform('CLIP_FAR', value/100);
		            }
                },
                scope: me,
            },
	    });

        this.addUniforms();
	    this.isLoaded = true;

	    this.items = [this.clipSlider];
	    this.callParent();
    },

    afterFirstLayout : function(){

    },
});


//////////////////////////////////////////////////////////////////
//
// transfer slider
//
//////////////////////////////////////////////////////////////////


Ext.define('BQ.viewer.Volume.transferSlider',{
    extend: 'Ext.slider.Multi',
    alias: 'widget.transfer-slider',
    cls: 'key-slider',
    height: 40,
    constructor : function(config) {
        this.callParent(arguments);
        return this;
    },


    initComponent : function(){
	    this.keyArray = new Array();
	    this.autoKey = false;
	    this.insertDist = 2;
	    this.sampleRate = 8;
	    this.timeValue = 0;
	    var me = this;
        this.lastClicked = 0;
        this.stops = [{color:[0,0,0,0],offset:0}];
	    this.callParent();
        me.addEvents('clicked');
        this.addStop([0, 200, 0, 0.50],50);
        this.addStop([15, 100, 120, 0.10],70);
        this.addStop([250, 20, 2, 0.80],100);
    },

    afterRender: function(){
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

    drawBackGround : function(canvas){
       var svgStops = '<defs> <linearGradient id="Gradient1">\n';
        for (var i=0; i < this.stops.length; i++){
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

        var checkRect=[
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


    changecomplete: function(){
	    this.sortKeys();
	    this.callParent();
    },

    setValue : function(index, value, animate, changeComplete) {
        this.callParent(arguments);
        this.stops[index].offset = value;
        this.drawBackGround();
        this.lastClicked = index;
    },

    onMouseDown : function(e) {
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
            thumb = e.target == thumbs[i].el.dom ? i:thumb;
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

    sortKeys : function(){
	    this.stops.sort(function(a,b){
	        return (a.offset-b.offset);
	    });

	    this.thumbs.sort(function(a,b){
	        return (a.value-b.value);
	    });

	    for(var i = 0; i < this.thumbs.length; i++){
	        this.thumbs[i].index = i;
	    }
    },

    scaleKeys : function(newScale){
	    var oldScale = this.maxValue;
	    if(oldScale == 0) return;
	    var scale = newScale/oldScale;

	    for(var i = 0; i < this.thumbs.length; i++){
	        var newVal = this.thumbs[i].value*scale;
	        this.thumbs[i].value = newVal;
	    }
    },

    addStop : function(rgba, offset){
        this.addThumb(offset);
        this.stops.push({color: rgba, offset: offset});
        this.sortKeys();
    },

    removeStop: function(it){

	    if(it >= 0){
		    var innerEl = this.thumbs[it].ownerCt.innerEl.dom;
		    innerEl.removeChild(this.thumbs[it].el.dom);
		    this.thumbs.splice(it,1);
		    for(var i = 0; i < this.thumbs.length; i++){
		        this.thumbs[i].index = i;
		    }

	        this.stops.splice(it,1);
	    }
    },

    removeCurrentStop : function(){
        this.removeStop(this.lastClicked);
        this.drawBackGround();
    },

    addNextStop : function(){
        var i0 = this.lastClicked;
        var i1 = i0 + 1;
        if(i0 == this.thumbs.length - 1) i1 = i0-1;
        var o0 = this.thumbs[i0].value;
        var o1 = this.thumbs[i1].value;
        var c0 = this.stops[i0].color;
        var c1 = this.stops[i1].color;
        var cA = [0.5*(c0[0] + c1[0]),
                  0.5*(c0[1] + c1[1]),
                  0.5*(c0[2] + c1[2]),
                  0.5*(c0[3] + c1[3])];
        this.addStop(cA, 0.5*(o0 + o1));
        this.drawBackGround();
    },

    setStopColor: function(value, i, thumb){
        thumb = typeof thumb == 'undefined' ? this.lastClicked : thumb;
        this.stops[thumb].color[i] = value;
        this.drawBackGround();
    },

});


//////////////////////////////////////////////////////////////////
//
// value slider
//
//////////////////////////////////////////////////////////////////


Ext.define('BQ.viewer.Volume.valueSlider',{
    extend: 'Ext.slider.Multi',
    alias: 'widget.value-slider',
    cls: 'key-slider',

    constructor : function(config) {
        this.callParent(arguments);
        return this;
    },

    initComponent : function(){
	    this.callParent();
    },

    afterRender: function(){
	    this.svgUrl = "http://www.w3.org/2000/svg";
	    this.svgdoc = document.createElementNS(this.svgUrl, "svg");
	    this.svgdoc.setAttributeNS(null, 'class', 'val-slider-back');
	    this.el.dom.appendChild(this.svgdoc);
	    this.svgBackGround = document.createElementNS(this.svgUrl, "g");
	    this.svgBackGround.setAttributeNS(null, 'class', 'val-slider-back');
	    this.svgdoc.appendChild(this.svgBackGround);

        var me = this;
        this.rgbColor = [25,10,90,1.0];
        this.drawBackGround();
	    this.callParent();
    },

    setColor : function(r, g, b, a){
        this.rgbColor = [r,g,b,a];
        this.drawBackGround();
    },

    setValue : function(index, value, animate){
        this.callParent(arguments);
        this.drawBackGround();
    },

    getStop : function(offset, color){
        svgStop = '<stop offset="' + offset +
            '%" stop-color="rgba(' +
            color[0] + ', ' +
            color[1] + ', ' +
            color[2] + ', ' +
            color[3] + ')"/>\n';
        return svgStop;
    },

    drawBackGround : function(canvas){
        var grad1 = ['<defs>',
                     '<linearGradient id="toBlack" ',
                     'x1="0%" y1="0%" x2="0%" y2="100%">\n'
                    ].join(' ');

        grad1 += this.getStop(0,this.rgbColor); //yellow
        grad1 += this.getStop(100, [0, 0,  0,this.rgbColor[3]]); //green
        grad1 += '</linearGradient> </defs>';

        var rect = ['<rect id="rectVal"',
                    'x="0" y="0"',
                    'rx="3" ry="3"',
                    'width="100%"',
                    'height="100%"',
                    'fill="url(#toBlack)"',
                    '/>'].join(' ');

	    var svg = [' <svg width=100% height=100% >',
                   grad1,
                   rect,
	               '</svg>'].join('\n');

	    this.svgBackGround.innerHTML = svg;
    },


    //----------------------------------------------------------------------
    // event handlers
    //----------------------------------------------------------------------
    changecomplete: function(){
	    this.sortKeys();
	    this.callParent();
    },

});

Ext.define('BQ.viewer.Volume.fieldSlider', {
    extend: 'Ext.Component',
    alias: 'widget.field-slider',
   getStop : function(offset, color){
        svgStop = '<stop offset="' + offset +
            '%" stop-color="rgba(' +
            color[0] + ', ' +
            color[1] + ', ' +
            color[2] + ', ' +
            color[3] + ')"/>\n';
        return svgStop;
    },

    generateHsv : function(){
        var grad1 = '<defs> <linearGradient id="HSV">\n';
        grad1 += this.getStop(          0, [255,  0,  0,1.0]); //red
        grad1 += this.getStop(Math.floor( 60/360*100), [255,255,  0,1.0]); //yellow
        grad1 += this.getStop(Math.floor(120/360*100), [  0,255,  0,1.0]); //green
        grad1 += this.getStop(Math.floor(180/360*100), [  0,255,255,1.0]); //blue-green
        grad1 += this.getStop(Math.floor(240/360*100), [  0,  0,255,1.0]); //blue
        grad1 += this.getStop(Math.floor(300/360*100), [255,  0,255,1.0]); //magenta
        grad1 += this.getStop(Math.floor(360/360*100), [255,  0,  0,1.0]); //red
        grad1 += '</linearGradient> </defs>';

        var grad2 = ['<defs>',
                     '<linearGradient id="overlay" ',
                     'x1="0%" y1="0%" x2="0%" y2="100%">\n'
                    ].join(' ');

        grad2 += this.getStop(  0, [255,255,255,0.0]);
        grad2 += this.getStop(100, [255,255,255,1.0]);
        grad2 += '</linearGradient> </defs>';

        var rect = ['<rect id="rect1"',
                    'x="0" y="0"',
                    'rx="0" ry="0"',
                    'width="100%"',
                    'height="100%"',
                    'fill="url(#HSV)"',
                    '/>'].join(' ');

        var rectOverlay = ['<rect id="rect2"',
                           'x="0" y="0"',
                           'rx="0" ry="0"',
                           'width="100%"',
                           'height="100%"',
                           'fill="url(#overlay)"',
                           '/>'].join(' ');


	    var svg = [' <svg width=100% height=100% >',
                   grad1,
                   grad2,
                   rect,
                   rectOverlay,
	               '</svg>'].join('\n');


	    this.svgField.innerHTML = svg;
    },

    afterRender: function(){
	    this.callParent();
        this.svgUrl = "http://www.w3.org/2000/svg";
	    this.svgdoc = document.createElementNS(this.svgUrl, "svg");
	    this.svgdoc.setAttributeNS(null, 'class', 'color-field');

	    this.el.dom.appendChild(this.svgdoc);
	    this.svgField = document.createElementNS(this.svgUrl, "g");
	    this.svgField.setAttributeNS(null, 'class', 'color-field');
	    this.svgdoc.appendChild(this.svgField);
        this.generateHsv();

        this.dot = document.createElementNS(this.svgUrl, "circle");
	    this.dot.setAttributeNS(null, 'class', 'color_chooser');
	    this.dot.setAttributeNS(null, 'cx', '40');
        this.dot.setAttributeNS(null, 'cy', '20');
        this.dot.setAttributeNS(null, 'r', '5');
        this.dot.setAttributeNS(null, 'fill','rgba(0,0,0,0.5)');
        this.dot.setAttributeNS(null, 'stroke','black');
        this.dot.setAttributeNS(null, 'stroke-width','2');
        this.svgdoc.appendChild(this.dot);

        var me = this;
        var cursorPoint = function(evt){
		    pt.x = evt.clientX; pt.y = evt.clientY;
		    return pt.matrixTransform(me.svgdoc.getScreenCTM().inverse());
	    }

        var offsetPoint = function(evt){
		    pt.x = evt.offsetX; pt.y = evt.offsetY;
		    //return pt.matrixTransform(me.svgdoc.getScreenCTM().inverse());
            return pt;
	    }


        var onMove;
	    var pt    = this.svgdoc.createSVGPoint();

        this.svgField.addEventListener('mousedown',function(e){
            var el = me.dot;
        	var x = 'cx';
			var y = 'cy';
			var elementStart = { x:el[x].animVal.value, y:el[y].animVal.value };
            var current = offsetPoint(e);
			pt.x = current.x;
			pt.y = current.y;
			var m = el.getTransformToElement(me.svgdoc).inverse();
			m.e = m.f = 0;
			pt = pt.matrixTransform(m);
			el.setAttribute(x,pt.x);
			el.setAttribute(y,pt.y);
			console.log(elementStart, pt);
            console.log("event", e);
            if (me.handler)
                me.handler(e, me);

        }, false);

	    this.dot.addEventListener('mousedown',function(e){
            var el = me.dot;
        	var x = 'cx';
			var y = 'cy';
			var mouseStart   = cursorPoint(e);
			var elementStart = { x:el[x].animVal.value, y:el[y].animVal.value };
			onMove = function(e){
				var current = cursorPoint(e);
				pt.x = current.x - mouseStart.x;
				pt.y = current.y - mouseStart.y;
				var m = el.getTransformToElement(me.svgdoc).inverse();
				m.e = m.f = 0;
				pt = pt.matrixTransform(m);
				el.setAttribute(x,elementStart.x+pt.x);
				el.setAttribute(y,elementStart.y+pt.y);
				var dragEvent = document.createEvent("Event");
				dragEvent.initEvent("dragged", true, true);
				el.dispatchEvent(dragEvent);
                if (me.handler)
                    me.handler(e, me);
			};
			document.body.addEventListener('mousemove',onMove,false);
        }, false);

		document.body.addEventListener('mouseup',function(){
            document.body.removeEventListener('mousemove',onMove,false);
		},false);
        var me = this;
    },

    afterFirstLayout : function(){
        this.setColorRgb(0.75,0.86,1.0);
    },

    setValue : function(x,y){
        var w = this.getWidth();
        var h = this.getHeight();

        this.dot.setAttribute('cx', w*x);
        this.dot.setAttribute('cy', h*(1.0 - y));

    },

    getValue : function(){
        var w = this.getWidth();
        var h = this.getHeight();
        var x = this.dot.getAttribute('cx');
        var y = this.dot.getAttribute('cy');
        return {x:x/w, y:y/h}
    },


    setColorRgb : function(r,g,b){
        var hsv = this.RGBtoHSV(r,g,b);
        this.setValue(hsv.h/360, hsv.s);
    },

    setColorHsv : function(h,s,v){
        this.setValue(h/360, s);
    },

    getHsv : function(){
        var val = this.getValue();
        return {h: 360*val.x, s: 1.0 - val.y, v: 1.0}
    },

    getRgb : function(){
        var val = this.getValue();
        return {h: 360*val.x, s: 1.0 - val.y, v: 1.0}
        var rgb = this.HSVtoRGB(360*val.x, 1.0 - val.y, 1.0);
        return rgb;
    },


    RGBtoHSV : function( r, g, b){
        //lazy, just grabbed code
        //http://www.cs.rit.edu/~ncs/color/t_convert.html
        var h,s,v;
	    var min = Math.min( r, Math.min(g, b) );
	    var max = Math.max( r, Math.max(g, b) );
        console.log("min max: ", min, max);
	    v = max;				// v
	    var delta = max - min;

	    if( max != 0 )
		    s = delta / max;		// s
	    else {
		    // r = g = b = 0		// s = 0, v is undefined
		    s = 0;
		    h = -1;
		    return;
	    }
	    if( r == max )
		    h = ( g - b ) / delta;		// between yellow & magenta
	    else if( g == max )
		    h = 2 + ( b - r ) / delta;	// between cyan & yellow
	    else
		    h = 4 + ( r - g ) / delta;	// between magenta & cyan
	    h *= 60;				// degrees
	    if( h < 0 )
		    h += 360;
        return {h:h, s:s, v:v};
    },

    HSVtoRGB : function(h, s, v ){
        var r, g, b;
	    var i;
	    var f, p, q, t;
	    if( s == 0 ) {
		    // achromatic (grey)
            return {r:v, g:v, b:v};
	    }
	    h /= 60;			// sector 0 to 5
	    i = Math.floor( h );
	    f = h - i;			// factorial part of h
	    p = v * ( 1 - s );
	    q = v * ( 1 - s * f );
	    t = v * ( 1 - s * ( 1 - f ) );
        //console.log(h, f,p,q,t);
	    switch( i ) {
		case 0:
			r = v;
			g = t;
			b = p;
			break;
		case 1:
			r = q;
			g = v;
			b = p;
			break;
		case 2:
			r = p;
			g = v;
			b = t;
			break;
		case 3:
			r = p;
			g = q;
			b = v;
			break;
		case 4:
			r = t;
			g = p;
			b = v;
			break;
		default:		// case 5:
			r = v;
			g = p;
			b = q;
			break;
	    }
        return {r:r, g:g, b:b};
    },
});


Ext.define('BQ.viewer.Volume.excolorpicker', {
    extend: 'Ext.container.Container',
    alias: 'widget.excolorpicker',

    layout: {
	    type: 'hbox',
	    align : 'stretch',
	    pack  : 'start',
    },

    initComponent : function(){
	    this.title = 'excolorpicker';
        var me = this;
	    this.rampSvg = Ext.create('BQ.viewer.Volume.fieldSlider',{
            height: 120,
            width: '94%',
	        handler: function(e, slider){
                var hsv = me.rampSvg.getHsv();
                var rgb = me.rampSvg.HSVtoRGB(hsv.h,hsv.s,1.0);
                me.valueSlider.setColor(Math.floor(255*rgb.r),
                                        Math.floor(255*rgb.g),
                                        Math.floor(255*rgb.b),1.0);
                if(me.handler)
                    me.handler(e,me);
            }
        });

        this.valueSlider = Ext.create('BQ.viewer.Volume.valueSlider',{
            xtype: 'value-slider',
            cls: 'val-slider',
            vertical: true,
            minValue: 0.00,
            maxValue: 100,
            width: '5%',
            values: [50],
            listeners: {
                change: function(slider, value, thumb){
                    if(me.handler)
                        me.handler(0,me);
                },
                scope:me,
            }
        });

        Ext.apply(this, {
	        items:[ this.rampSvg,this.valueSlider],
	    });

        this.callParent();
    },

    setColorRgb : function(r,g,b,a){
        var hsv = this.rampSvg.RGBtoHSV(r,g,b);
        var rgb = this.rampSvg.HSVtoRGB(hsv.h,hsv.s,1.0);

        this.rampSvg.setColorHsv(hsv.h, hsv.s, hsv.v);

        this.valueSlider.setColor(Math.floor(255*rgb.r),
                                  Math.floor(255*rgb.g),
                                  Math.floor(255*rgb.b),1.0);

        this.valueSlider.setValue(0,100*hsv.v,true);
    },

    getColorRgb : function(){
        var val = this.valueSlider.getValue(0);
        var hsv = this.rampSvg.getHsv();
        hsv.v = val/100;
        var rgb = this.rampSvg.HSVtoRGB(hsv.h, hsv.s, hsv.v);
        return rgb;
    },

    afterFirstLayout : function(){
        //this.setColorRgb(1.0,0.0,0.0);
        this.callParent();
    },
});

Ext.define('BQ.viewer.Volume.transfer', {
    extend: 'Ext.container.Container',
    cls: 'materialcontroller',
    alias: 'widget.transfer',
    mixins:['BQ.viewer.Volume.uniformUpdate'],
    addUniforms : function(){
        this.sceneVolume.initUniform('transfer', "t", null);
	    this.sceneVolume.initUniform('TRANSFER_SIZE', "i", 64);
        this.sceneVolume.initUniform('USE_TRANSFER', "i", this.transfer);
    },

    changed : function(){
        console.log(this.transferSlider);
        if(this.transferSlider.stops.length < 2) return;
        var pixels = new Uint8Array(256);
        var cStop = 0;
        var ci = 0;
        for(var i = 0; i < 64; i++){
            var stop = this.transferSlider.stops[cStop];
            var nstop = this.transferSlider.stops[cStop+1];

            var per = ci/64*100;

            if(per > nstop.offset-stop.offset){
                ci = 0;
                cStop++;
                stop = this.transferSlider.stops[cStop];
                nstop = this.transferSlider.stops[cStop+1];
            }

            var t = ci/64*100/(nstop.offset - stop.offset);
            //console.log(t, cStop, per, stop, nstop);
            var c0 =   stop.color;
            var c1 =  nstop.color;
            //console.log(i,ci, per,t,nstop.offset,stop.offset);
            pixels[4*i + 0] = (1-t)*c0[0] + t*c1[0];
            pixels[4*i + 1] = (1-t)*c0[1] + t*c1[1];
            pixels[4*i + 2] = (1-t)*c0[2] + t*c1[2];
            pixels[4*i + 3] = 255*((1-t)*c0[3] + t*c1[3]);
            /*
            console.log(pixels[4*i + 0],
                        pixels[4*i + 1],
                        pixels[4*i + 2],
                        pixels[4*i + 3]);
            */
            ci++;
        }
        //conso
        var rampTex = this.panel3D.rampTex;
        rampTex = new THREE.DataTexture( pixels, 64, 1, THREE.RGBAFormat );
        rampTex.needsUpdate = true;
        this.sceneVolume.setUniform('transfer', rampTex);
        this.sceneVolume.setUniform('TRANSFER_SIZE', 64);
    },

    initComponent : function(){
	    var me = this;
        this.transfer = 0;
	    this.title = 'transfer';
        var controlBtnSize = 22;

        var useTransfer = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'use transfer function',
	        height: controlBtnSize,
	        checked: false,
	        handler: function(){
                this.transfer ^= 1;
                this.changed();
                this.sceneVolume.setUniform('USE_TRANSFER', this.transfer);
                if(this.transfer == 1){
		            this.showButton.show();
		        }
                else
                    this.showButton.hide();

	        },
	        scope:me,
	    });

        this.transferSlider = Ext.create('BQ.viewer.Volume.transferSlider', {
	        startFrame: 0,
	        endFrame: 100,
	        //tic:      this.tic,
	        panel3D: this.panel3D,
	        autoKey: false,
	        flex: 1,
            listeners: {
		        clicked: function(slider, thumb) {
		            var c = slider.stops[thumb].color;
                    me.aSlider.setValue(c[3]*255);
                    console.log(c);
                    me.colorPicker.setColorRgb(c[0]/255,c[1]/255,c[2]/255);
		        },
		        change: function(){
                    me.changed();
                },
		        scope:me
            },
            useTips:true,
	    });
        this.addUniforms();
        this.isLoaded = true;

      this.aSlider = Ext.create('Ext.slider.Single', {
            renderTo: Ext.get('slider-ph'),
            hideLabel: false,
	        fieldLabel: 'a',
	        labelWidth: 10,
            minValue: 0.00,
            maxValue: 255,
            value: 75,
            listeners: {
		        change: function(slider, value) {
		            //var lastClicked = this.transferSlider.lastClicked;
                    this.transferSlider.setStopColor(value/255,3);
                    this.changed();
                },
		        scope:me,
            }
	    }).show();

        this.addButton = Ext.create('Ext.Button', {
	        text: '+',
	        //cls: 'volume-button',
	        handler: function(button, pressed) {
		        me.transferSlider.addNextStop();
	        },
	        scope:me,
	    });

        this.subButton = Ext.create('Ext.Button', {
	        text: '-',
	        //cls: 'volume-button',
	        handler: function(button, pressed) {
		        me.transferSlider.removeCurrentStop();
                //me.displayParameterWindow();
	        },
	        scope:me,
	    });


        this.showButton = Ext.create('Ext.Button', {
	        text: 'edit transfer function',
	        //cls: 'volume-button',
	        handler: function(button, pressed) {
                console.log("twindow: ", this.transferWindow);

                if(!this.transferWindow)
                    me.displayColorWindow();
                else
                    this.transferWindow.show();

            },
	        scope:me,
	    });



        this.colorPicker =  Ext.create('BQ.viewer.Volume.excolorpicker',{
            handler: function(e, picker){
                var rgb = picker.getColorRgb();
                me.transferSlider.setStopColor(Math.floor(255*rgb.r),0);
                me.transferSlider.setStopColor(Math.floor(255*rgb.g),1);
                me.transferSlider.setStopColor(Math.floor(255*rgb.b),2);
                me.changed();
            }
        });
        this.showButton.hide();
        this.addUniforms();
	    Ext.apply(this, {
	        items:[useTransfer, this.showButton],
	    });

	    this.callParent();
    },

    displayColorWindow : function(){

	    this.transferWindow = Ext.create('Ext.window.Window', {
	        title: 'transfer function',
	        height: 250,
	        width: 400,

	        items: [{
                xtype: 'panel',
                layout: {
	                type: 'vbox',
	                align : 'stretch',
	                pack  : 'start',
                },
                items: [this.transferSlider, this.colorPicker, this.aSlider],

            }],
            bbar: {
                items: [this.addButton, this.subButton]
            },
            closeAction: 'hide',
	    }).show();
    },

    afterFirstLayout : function(){
        this.transferSlider.show();
        this.changed();
    },
});

Ext.define('BQ.viewer.Volume.pointControl', {
    extend: 'Ext.container.Container',
    alias: 'widget.pointControl',
/*
    changed : function(){
	    if(this.isLoaded){
            this.sceneVolume.setUniform('LIGHT_POSITION', this.lightObject.position);
	    }
    },
*/
    addUniforms : function(){

    },



    rescalePoints : function(){
        var bbhalf = this.panel3D.sceneVolume.getHalf();
        var bbox = this.points.geometry.boundingBox;
        var phalf = bbox.max.clone().sub(bbox.min);
        phalf.multiplyScalar(0.5);
        var scale = bbhalf.clone().divide(phalf);
        var amountOfPoints = 1000;
	    this.points.geometry.dynamic = true;
        this.points.geometry.verticesNeedUpdate = true;
        var mat = new THREE.Matrix4().scale(scale);
        this.points.geometry.applyMatrix(mat);
        this.points.geometry.computeBoundingBox();
        console.log(this.points);
    },

    setVisible : function( vis ){
        var t = this.panel3D.currentTime;
        this.currentSet = this.gObjectBuffers[t];
        for (var item in this.currentSet){
            if(!item) continue;
            var curMesh = this.currentSet[item];
            curMesh.visible = vis;
        }
    },

    updateScene : function(){
        var t = this.panel3D.currentTime;

        if(!this.currentSet) this.currentSet = {};
        for (var item in this.currentSet){
            if(!item) continue;
            var curMesh = this.currentSet[item];
            this.sceneVolume.sceneData.remove( curMesh ); // remove current point set
        }
        this.currentSet = this.gObjectBuffers[t];
        for (var item in this.currentSet){
            if(!item) continue;
            var curMesh = this.currentSet[item];
            this.sceneVolume.sceneData.add( curMesh ); // remove current point set
            if(this.state === 1)
      	        curMesh.visible = true;
            else
      	        curMesh.visible = false;
        }

        this.points   = this.currentSet.points; //set current pointer to loaded set
        this.pointclouds = [this.points];
    },

    loadGObjects : function(){
        var t = this.panel3D.currentTime;
        if(this.gObjectSets[t]) { //load points in lazily
            this.updateScene();
            return;
        }

        this.gObjectBuffers[t] = {};
        this.gObjectSets[t] = {
            points:    new Array(),
            lines:      new Array(),
            circles:    new Array(),
            ellipses:   new Array(),
            polylines:  new Array(),
            polygons:   new Array(),
            rectangles: new Array(),
            squares:    new Array(),
            labels:     new Array(),
            gobjects:     new Array(),
        };

        var thisSet = this.gObjectSets[t];
        var collectedPoints = new Array();
        for(var i = 0; i < this.gobjects.length; i++){
            var g = this.gobjects[i];
            if(g.vertices[0].t == t){
                console.log(g.resource_type);
                /*if(g.resource_type == 'polygon')
                    this.pushPolygon(g.vertices, index, position, color);

                else
                    thisSet[g.resource_type + 's'].push(g);
                */
                thisSet[g.resource_type + 's'].push(g)
            }
        }
        console.log('loadedFrame', thisSet);

        this.loadPoints();
        this.loadPolygons();
    },

    pushPosition : function(p, x, positions){
        var dims  = this.panel3D.dims.slice;
        var scale = { x:this.panel3D.dims.pixel.x,
                      y:this.panel3D.dims.pixel.y,
                      z:this.panel3D.dims.pixel.z };

        scale.y = scale.x/scale.y;
        scale.z = scale.x/scale.z;
        scale.x = 1.0;
        positions[ x * 3 + 0 ] = scale.x*(p.x/dims.x - 0.5);
		positions[ x * 3 + 1 ] = scale.y*(0.5 - p.y/dims.y);
		positions[ x * 3 + 2 ] = scale.z*(0.5 - p.z/dims.z);
    },

    isClockWise : function(poly){
        //use shoelace determinate
        var det = 0;
        for(var i = 0; i < poly.length; i++){
            var cur = poly[i];
            var nex = poly[(i+1)%poly.length];
            det += cur.x*nex.y - cur.y*nex.x;
        }
        return det > 0;
    },

    pushPolygon : function(poly, indices, positions, colors){
        //poly is any object with an x and a y.
        //loads necessary data onto the vertex buffer
        var lindex = [];
        if(!this.isClockWise(poly))
            lindex = POLYGON.tessellate(poly, []);
        else
            lindex = POLYGON.tessellate(poly.reverse(), []);

        for(var j = 0; j < lindex.length; j++){
            lindex[j] += positions.length;
        }

        var lcolor = {r: Math.random(),g: Math.random(),b: Math.random()}
        for(var j = 0; j < poly.length; j++){
            colors.push(lcolor);
        }

        for(var i = 0; i < poly.length; i++){
            positions.push(poly[i]);// = positions.concat(poly)
        };

        for(var i = 0; i < lindex.length; i++){
            indices.push(lindex[i]);// = positions.concat(poly)
        };
        //indices.push(lindex);// = indices.concat(lindex);
        //console.log('local: ', lindex, 'localpoly: ', poly, 'global: ', indices, 'global p: ',positions);
        //triCounter += polys[i].vertices.length;
    },

    loadPolygons : function(){
        var t = this.panel3D.currentTime;
        var amountOfPoints = this.gObjectSets[t].points.length;
        var polys = this.gObjectSets[t].polygons;
        var triCounter = 0;
        var index = new Array();
        var position = new Array();
        var color = new Array();
        var offsets = {};
        for(var i = 0; i < polys.length; i++){
            this.pushPolygon(polys[i].vertices, index, position, color);
            var here;
            /*
            var lindex = [];
            if(!this.isClockWise(polys[i].vertices))
                lindex = POLYGON.tessellate(polys[i].vertices, []);
            else
                lindex = POLYGON.tessellate(polys[i].vertices.reverse(), []);

            for(var j = 0; j < lindex.length; j++){
                lindex[j] += triCounter;
            }

            var lcolor = {r: Math.random(),g: Math.random(),b: Math.random()}
            for(var j = 0; j < polys[i].vertices.length; j++){
                color.push(lcolor);
            }

            position = position.concat(polys[i].vertices);
            index = index.concat(lindex);
            triCounter += polys[i].vertices.length;
            */
        }
        console.log(index, position, color);
        var geometry = new THREE.BufferGeometry();
		geometry.addAttribute( 'index',    new THREE.BufferAttribute( new Uint32Array( index.length ), 1 ));
		geometry.addAttribute( 'position', new THREE.BufferAttribute( new Float32Array( position.length * 3 ), 3 ) );
		geometry.addAttribute( 'color',    new THREE.BufferAttribute( new Float32Array( color.length * 3 ), 3 ) );
        var gpositions = geometry.getAttribute('position').array;
        var gindex     = geometry.getAttribute('index').array;
        var gcolor     = geometry.getAttribute('color').array;
        //var check0 = index.slice(0);

        for(var i = 0; i < index.length; i++){
            gindex[i] = index[i];
        }

        for(var i = 0; i < position.length; i++){
            this.pushPosition(position[i], i, gpositions);
        }

        for(var i = 0; i < color.length; i++){
            gcolor[3*i + 0] = color[i].r;
            gcolor[3*i + 1] = color[i].g;
            gcolor[3*i + 2] = color[i].b;
        }

        var polymesh = new THREE.Mesh( geometry, this.polyShaderMaterial );

        polymesh.geometry.dynamic = true;
        polymesh.geometry.computeBoundingBox();
        polymesh.geometry.verticesNeedUpdate = true;
        this.gObjectBuffers[t].polygons = polymesh;
       this.updateScene();
    },

    loadPoints : function(){
        var t = this.panel3D.currentTime;
        var amountOfPoints = this.gObjectSets[t].points.length;
	    var pointGeom = new THREE.BufferGeometry();

		pointGeom.attributes = {
			position: {
				itemSize: 3,
				array: new Float32Array( amountOfPoints * 3 )
			},

			alpha: {
				itemSize: 1,
				array: new Float32Array( amountOfPoints )
			}

		};

		var positions = pointGeom.attributes.position.array;
		var alphas = pointGeom.attributes.alpha.array;

        var dims  = this.panel3D.dims.slice;
        var scale = { x:this.panel3D.dims.pixel.x,
                      y:this.panel3D.dims.pixel.y,
                      z:this.panel3D.dims.pixel.z };

        scale.y = scale.x/scale.y;
        scale.z = scale.x/scale.z;
        scale.x = 1.0
;
        var x = 0;
        while (x < amountOfPoints){
            var p = this.gObjectSets[t].points[x].vertices[0];
            this.pushPosition(p,x,positions);
            alphas[x] = 1.0;
            x++;
        }
        /* recursive random cluster generator
        while (x < amountOfPoints){

            var seed = [1.0 - 2.0*Math.random() * 1,
                        1.0 - 2.0*Math.random() * 1,
                        1.0 - 2.0*Math.random() * 1];
            var cx = x;
            var clustSize = 20*Math.random();
            for(var y = cx; y < cx + clustSize; y++ ){
                var r = 0.5*Math.random();
                var nseed = [seed [0] + r*(1.0 - 2.0*Math.random() * 1),
                             seed [1] + r*(1.0 - 2.0*Math.random() * 1),
                             seed [1] + r*(1.0 - 2.0*Math.random() * 1),]
                for(var z = cx; z < cx + clustSize*2; z++ ){
                    var r0 = 0.5*r*Math.random();
                    positions[ z * 3 + 0 ] = seed [0] + r0*(1.0 - 2.0*Math.random() * 1);
			        positions[ z * 3 + 1 ] = seed [1] + r0*(1.0 - 2.0*Math.random() * 1);
			        positions[ z * 3 + 2 ] = seed [2] + r0*(1.0 - 2.0*Math.random() * 1);
                    alphas[y] = 1.0;
                    x++;
                }
            }
        }
        */
        var points = new THREE.PointCloud( pointGeom, this.pointShaderMaterial );

        points.geometry.dynamic = true;
        points.geometry.computeBoundingBox();
        points.geometry.verticesNeedUpdate = true;
        if(!this.gObjectSets[t]){
            this.gObjectSets[t] = {};
        }

        this.gObjectBuffers[t].points = points;

        this.updateScene();

        //nsole.log(this.points);

    },

    initComponent : function(){
        this.title = 'show points';
	    var me = this;
	    this.dist = 1.0;
        this.state = 0;
	    this.lighting = Ext.create('Ext.form.field.Checkbox', {
	        boxLabel: 'show points',
	        checked: false,
	        handler: function(){
	            this.state ^= 1;
		        if((this.state&1) === 1){
                    this.setVisible(true);
		        } else {
                    this.setVisible(false);
		        }
                this.rescalePoints();
                this.panel3D.rerender();
	        },
	        scope:me,
	    });


        var me = this;
        this.plane = new THREE.Mesh( new THREE.PlaneGeometry( 2000, 2000, 8, 8 ),
                                new THREE.MeshBasicMaterial( {
                                    color: 0x000000,
                                    opacity: 0.25,
                                    transparent: true,
                                    wireframe: true } ) );
		this.plane.visible = false;


        this.sceneVolume.scene.add( this.plane );

        this.sceneVolume.scene.add(this.lightObject);
        this.canvas3D.getEl().dom.addEventListener('mousemove', me.onMouseMove.bind(this),true);
        this.canvas3D.getEl().dom.addEventListener('mouseup', me.onMouseUp.bind(this),true);
        this.canvas3D.getEl().dom.addEventListener('mousedown', me.onMouseDown.bind(this),true);

        var pack = [
            'vec4 pack (float depth){',
            'const vec4 bitSh = vec4(256 * 256 * 256,',
            '                        256 * 256,',
            '                        256,',
            '                        1.0);',
            'const vec4 bitMsk = vec4(0.0,',
            '                         1.0 / 256.0,',
            '                         1.0 / 256.0,',
            '                         1.0 / 256.0);',
            'highp vec4 comp = fract(depth * bitSh);',
            'comp -= comp.xxyz * bitMsk;',
            'return comp;',
        '}'
        ].join('\n');

        var fragDepth = [
            'varying vec2 vUv;',
            'uniform float near;',
            'uniform float far;',
            //'varying highp float depth;',
            pack,
            'void main() {',
            //' float depth = gl_FragCoord.z/gl_FragCoord.w;',
            //'  float f = smoothstep( near, far, depth );',
            '  gl_FragColor = pack(gl_FragCoord.z);',
            //'  float f = gl_FragCoord.z;',
            //'  gl_FragColor = vec4(f, f, f, 1.0);',
            '}'
        ].join('\n');

        var vertDepth = [
            'varying vec2 vUv;',
            //'varying highp float depth;',
            'void main() {',
			'  vUv = uv;',
			'  vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );',
            '  gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );',
            //'  depth = length(cameraPosition - mvPosition.xyz);',
            '}'
        ].join('\n');

        var spriteTex = THREE.ImageUtils.loadTexture( '/js/volume/icons/redDot.png' );

        var frag = [
            'uniform sampler2D tex1;',
            'uniform float near;',
            'uniform float far;',
            'uniform int USE_COLOR;',
            'varying float vAlpha;',
            //'varying float depth;',
            pack,
            'void main() {',
            ' if(USE_COLOR == 0){',
           '  vec4 C = vec4(texture2D(tex1, gl_PointCoord).a);',
            '  gl_FragColor = pack(gl_FragCoord.z);',
            //'  gl_FragColor = pack(gl_FragCoord.z);',
            '}',
            ' else{',
            '  vec4 C = texture2D(tex1, gl_PointCoord);',
            '  gl_FragColor = C;',
            '  }',
            '}'
        ].join('\n');

        var vert = [
            'attribute float alpha;',
            'varying float vAlpha;',
            'void main() {',
            '  vAlpha = 1.0 - alpha;',
            '  vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );',
            '  gl_PointSize = 0.1 * ( 300.0 / length( mvPosition.xyz ) );',
            '  gl_Position = projectionMatrix * mvPosition;',
            '}'
        ].join('\n');

		this.pointShaderMaterial = new THREE.ShaderMaterial( {
			uniforms: {
				tex1: { type: "t", value: spriteTex },
				zoom: { type: 'f', value: 100.0 },
                near: {type: 'f', value: 0.1},
                far:  {type: 'f', value: 20.0},
                USE_COLOR: {type: 'i', value: 0}
			},
			attributes: {
				alpha: { type: 'f', value: null },
			},
			vertexShader:   vert,
			fragmentShader: frag,
			transparent: false
		});


/*
        backGroundShaderMaterial = new THREE.MeshDepthMaterial( {
            side: THREE.DoubleSide,
		});
*/
        this.polyShaderMaterial = new THREE.ShaderMaterial( {
			uniforms: {
                near: {type: 'f', value: 0.1},
                far:  {type: 'f', value: 20.0},
			},
			vertexShader:   vertDepth,
			fragmentShader: fragDepth,
            side: THREE.DoubleSide,
			//transparent: true
		});

		backGroundShaderMaterial = new THREE.ShaderMaterial( {
			uniforms: {
                near: {type: 'f', value: 0.1},
                far:  {type: 'f', value: 20.0},
			},
			vertexShader:   vertDepth,
			fragmentShader: fragDepth,
            side: THREE.BackSide,
			//transparent: true
		});

        this.gObjectSets = new Array();
        this.gObjectBuffers = new Array();
        this.loadGObjects();
        this.panel3D.on('time', this.loadGObjects, me);


        this.raycaster = new THREE.Raycaster();
        this.raycaster.params.PointCloud.threshold = 0.0025;
/*
		var sphereGeometry = new THREE.SphereGeometry( 0.01, 32, 32 );
		var sphereMaterial = new THREE.MeshBasicMaterial( { color: 0xff0000, shading: THREE.FlatShading } );
		this.sphere =  new THREE.Mesh( sphereGeometry, backGroundShaderMaterial );
        this.sceneVolume.sceneData.add( this.sphere );
*/
        //var backGroundGeometry = new THREE.CubeGeometry(8.0, 8.0, 8.0);
        var backGroundGeometry = new THREE.SphereGeometry( 8.0, 32, 32 );
        var backGround = new THREE.Mesh(backGroundGeometry, backGroundShaderMaterial);
        //backGround.overdraw = true;
        //backGround.doubleSided = true;
        this.sceneVolume.sceneData.add(backGround);


	    this.addUniforms();
	    this.isLoaded = true;
        this.panel3D.canvas3D.animate_funcs[0] = callback(this, this.onAnimate);

        this.depthBuffer
                = new THREE.WebGLRenderTarget(this.panel3D.getWidth(), this.panel3D.getHeight(),
                                              { minFilter: THREE.LinearFilter,
                                                magFilter: THREE.NearestFilter,
                                                format: THREE.RGBAFormat });
        this.colorBuffer
                = new THREE.WebGLRenderTarget(this.panel3D.getWidth(), this.panel3D.getHeight(),
                                              { minFilter: THREE.LinearFilter,
                                                magFilter: THREE.NearestFilter,
                                                format: THREE.RGBAFormat });


        this.items = [this.lighting];
	    this.callParent();
    },

    onAnimate : function(){

        if(this.sceneVolume.sceneData && this.sceneVolume.setMaxSteps == 32){
            var panel = this.panel3D;
            //move this to background plug-in
            panel.canvas3D.renderer.clearTarget(this.accumBuffer0,
                                               true, true, true);
            var buffer = this.accumBuffer0;
            var bufferColor = this.accumBuffer1;

            this.pointShaderMaterial.uniforms.USE_COLOR.value = 0;
            panel.canvas3D.renderer.render(this.sceneVolume.sceneData,
                                           this.canvas3D.camera,
                                           this.depthBuffer);

            this.pointShaderMaterial.uniforms.USE_COLOR.value = 1;
            panel.canvas3D.renderer.render(this.sceneVolume.sceneData,
                                           this.canvas3D.camera,
                                           this.colorBuffer);

            panel.sceneVolume.setUniform('BACKGROUND_DEPTH', this.depthBuffer, false);
            panel.sceneVolume.setUniform('BACKGROUND_COLOR', this.colorBuffer, false);
        }
    },

    onMouseUp: function(){
        this.selectLight = false;
    },

    onMouseDown: function(){
        if(this.state === 0) return;
        var width = this.canvas3D.getWidth();
		var height = this.canvas3D.getHeight();
        var cx = this.canvas3D.getX();
        var cy = this.canvas3D.getY();
        var x =  ((event.clientX - cx)/width ) * 2 - 1;
		var y = -((event.clientY - cy)/height) * 2 + 1;

        var vector = new THREE.Vector3( x, y, 0.5 );
        var camera = this.canvas3D.camera;

        this.canvas3D.projector.unprojectVector( vector, camera );
/*
        var objects = [this.lightObject];
        var intersects = this.raycaster.intersectObjects( objects );
        if(intersects.length > 0){
            this.canvas3D.controls.enabled = false;
            this.selectLight = true;
            this.canvas3D.getEl().dom.style.cursor = 'move';
        }
        else{
            console.log('auto');
            this.canvas3D.getEl().dom.style.cursor = 'auto';
        }
*/
    },

    onMouseMove : function(event){
        event.preventDefault();
        if(this.points.visible === false) return;
        var width = this.canvas3D.getWidth();
		var height = this.canvas3D.getHeight();
        var cx = this.canvas3D.getX();
        var cy = this.canvas3D.getY();
        var x =  ((event.clientX - cx)/width ) * 2 - 1;
		var y = -((event.clientY - cy)/height) * 2 + 1;

        var camera = this.canvas3D.camera;

		var vector = new THREE.Vector3( x, y, 0.5 );
		this.canvas3D.projector.unprojectVector( vector, camera );
        this.raycaster.ray.set( camera.position, vector.sub( camera.position ).normalize() );

		var intersections = this.raycaster.intersectObjects( this.pointclouds );
		intersection = ( intersections.length ) > 0 ? intersections[ 0 ] : null;
        if(intersection !== null){
            //this.sphere.position.copy( intersection.point );
            var pos = this.canvas3D.projector.projectVector(intersection.point.clone(), camera);

            this.label.style.top  = '' + 0.5*height*(1.0-pos.y) + cy + 'px';
            this.label.style.left = '' + 0.5*width*( 1.0+pos.x) - cx  + 'px';
            this.label.textContent = [pos.x,
                                      pos.y,
                                      pos.z].join(",\n");

        }
        if(!this.label){
            this.label = document.createElement('div');
            this.label.textContent = 'Earth';
            this.label.style.backgroundColor = 'white';
            this.label.style.position = 'absolute';
            this.label.style.padding = '1px 4px';
            this.label.style.borderRadius = '2px';
            this.canvas3D.getEl().dom.appendChild(this.label);
        }
        this.panel3D.rerender();
    },

    afterFirstLayout : function(){
	    this.callParent();
    },
});