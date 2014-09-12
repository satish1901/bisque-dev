/*******************************************************************************
shaderConfig -
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

function ShaderSource(config){
    this.source = '';
    this.settings = {};
    this.set(config);
};

ShaderSource.prototype.set = function(config){
    if(arguments.length === 2){
        this.settings[arguments[0]] = arguments[1];
    } else {
        for (var a in config){
            this.settings[a] = config[a];
        }
    }
    this.config(config);
};

ShaderSource.prototype.config = function(config){
};

ShaderSource.prototype.getID = function(){
};

ShaderSource.prototype.getSource = function(){
    return this.source;
};

////////////////////////////////////////////////
//Static shader from URL
////////////////////////////////////////////////
function UrlShader(config){
    ShaderSource.call(this, config);
};

UrlShader.prototype = new ShaderSource();

UrlShader.prototype.getID = function (){
    return this.settings.url;
};

UrlShader.prototype.fetchFragments = function (url, storeId) {
	var me = this;
	var id = storeId;
    var loader = this.settings.loader;
	Ext.Ajax.request({
		url : url,
		callback : function (opts, succsess, response) {
			if (response.status >= 400)
				BQ.ui.error(response.responseText);
			else {

				var fetchedText = response.responseText;
				me.source = fetchedText;
                if (me.settings.manipulate) {
					var newText = me.settings.manipulate(fetchedText);
					me.source = newText;
				}
            }
            me.settings.onloaded(this);
		},
		scope : this,
		disableCaching : false,
		listeners : {
			scope : this,
			beforerequest : function () {
				loader.setLoading('Loading images...');
			},
			requestcomplete : function () {
				loader.setLoading(false);
			},
			requestexception : function () {
				loader.setLoading(false);
			},
		},
	});
};

UrlShader.prototype.config = function(config){
    this.fetchFragments(config.url, config.url);
}

////////////////////////////////////////////////
//Configurable volume rendering shader
////////////////////////////////////////////////
function VolumeShader(config){
    ShaderSource.call(this, config);
};

VolumeShader.prototype = new ShaderSource();

VolumeShader.prototype.getID = function(){
    var base = 12; //maximum number of allowable bits to step through volume
    var PHONG = this.settings.phong ? 1 : 0;
    var DEEP  = this.settings.lighting.deep ? 2 : 0;
    var TRANS = this.settings.transfer ? 4 : 0;
    var HIGH = this.settings.highlight ? 8 : 0;
    //for now we have two gradient operators -> binary flags
    var GRAD = this.settings.gradientType === 'sobel' ? 16 : 0;

    return this.settings.maxSteps + ((PHONG + DEEP + TRANS + HIGH + GRAD) << 12);
};

VolumeShader.prototype.config = function(config){
        var uniformVars = [
        '#ifdef GL_ES',
        'precision highp float;',
        '#endif',

        '#define M_PI 3.14159265358979323846',

        'uniform vec2 iResolution;',
        'uniform vec3 BOX_SIZE;',
        'uniform int   BREAK_STEPS;',
        'uniform int   DITHERING;',
        'uniform float GAMMA_MIN;',
        'uniform float GAMMA_MAX;',
        'uniform float GAMMA_SCALE;',
        'uniform float BRIGHTNESS;',
        'uniform float DENSITY;',

        'uniform sampler2D textureAtlas;',
        'uniform sampler2D BACKGROUND_DEPTH;',
        'uniform sampler2D BACKGROUND_COLOR;',

        'uniform int TEX_RES_X;',
        'uniform int TEX_RES_Y;',
        'uniform int ATLAS_X;',
        'uniform int ATLAS_Y;',
        'uniform int SLICES;',
        'uniform int BLOCK_RES_X;',
        'uniform int BLOCK_RES_Y;',
        'uniform int BLOCK_RES_Z;',

        'uniform float CLIP_NEAR;',
        'uniform float CLIP_FAR;',
    ].join('\n');

    var lightPos = 'uniform vec3 LIGHT_POSITION;';

    var deepVars = [
        'uniform int   LIGHT_SAMPLES;',
        'uniform float LIGHT_DEPTH;',
        'uniform float LIGHT_SIG;',
        'uniform float DISP_SIG;',
        'uniform float DISPERSION;',
    ].join('\n');

    var phongVars = [
        'uniform int   NORMAL_MULT;',
        'uniform float KA;',
        'uniform float KD;',
        'uniform float NORMAL_INTENSITY;',
        'uniform float SPEC_SIZE;',
        'uniform float SPEC_INTENSITY;',
    ].join('\n');

    var transferVars = [
        'uniform sampler2D transfer;',
    ].join('\n');

    var powf = function(lib){
        if(lib === true)
            return [
                'float powf(float a, float b){',
                '  return pow(a,b);',
                '}'
            ].join('\n');

        else {
            var powLow = [
                'float powf(float a, float b){',
                '  //dirty low precision pow function',
                '  float g[20];',
                '  g[0] = 1.0;',
                '  g[1] = 0.5;',
                '  g[2] = 0.333333333;',
                '  g[3] = 0.25;',
                '  g[4] = 0.2;',
                '  g[5] = 0.1666666667;',
                '  g[6] = 0.1428571428571429;',
                '  g[7] = 0.125;',
                '  g[8] = 0.11111111111111;',
                '  g[9] = 0.1;',
                '  g[10] = 0.090909090909;',
                '  g[11] = 0.0833333333333;',
                '  g[12] = 0.07692307692307692307692307692308;',
                '  g[13] = 0.07142857142857142857142857142857;',
                '  g[14] = 0.06666666666666666666666666666667;',
                '  g[15] = 0.0625;',
                '  g[16] = 0.05882352941176470588235294117647;',
                '  g[17] = 0.05555555555555555555555555555556;',
                '  g[18] = 0.05263157894736842105263157894737;',
                '  g[19] = 0.05;',
                '  float f[13];',

                '  f[0] = 1.0;',
                'f[1] = 0.5;',
                'f[2] = 1.6666666667e-1;',
                'f[3] = 4.1666666667e-2;',
                'f[4] = 8.3333333333e-3;',
                'f[5] = 1.3888888888e-3;',
                'f[6] = 1.984126984126984e-4;',
                'f[7] = 2.48015873015873e-5;',
                'f[8] = 2.755731922398589e-6;',
                'f[9] = 2.755731922398589e-7;',
                'f[10] = 2.505210838544172e-8;',
                'f[11] = 2.08767569878681e-9;',
                'f[12] = 1.605904383682161e-10;',

                'float x = 1.0 - a;',
                'float xa = x;',
                'float y = 0.0;',

                'for(int i = 0; i < 20; i++){',
                '    y -= xa*g[i];',
                '    xa *= x;',
                '}',

                'float logy = 1.0;',
                'y *= b;',
                'float ya = y;',
                'for(int i = 0; i < 13; i++){',
                '    logy += ya*f[i];',
                '    ya *= y;',
                '}',

                'return logy;',
                '//return exp(y*log(x));',
                '}',
            ].join('\n');

            return powLow;
        }
    };

    var rand = [
        'float rand(vec2 co){',
        '  float threadId = gl_FragCoord.x/(gl_FragCoord.y + 1.0);',
        '  float bigVal = threadId*1299721.0/911.0;',
        '  float smallVal0 = threadId*7927.0/577.0;',
        '  float smallVal1 = threadId*104743.0/1039.0;',
        '  //return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);',
        '  return fract(sin(dot(co.xy ,vec2(smallVal0,smallVal1))) * bigVal);',
        '}',
    ].join('\n');



    var sampleStack = function(useTransfer, win){

        var getTransfer = [
            'vec4 getTransfer(float density){',
            '  vec4 col  = texture2D(transfer, vec2(density,0.0));',
            '  return col;',
            '}',
        ].join('\n');

        var luma2Alpha = [
            'vec4 luma2Alpha(vec4 color, float min, float max, float C){',
            '  //float x = sqrt(1.0/9.0*(color[0]*color[0] +color[1]*color[1] +color[2]*color[2]));',
            '  float x = 1.0/3.0*(color[0] + color[1] + color[2]);',

            '  //x = clamp(x, 0.0, 1.0);',
            '  float xi = (x-min)/(max-min);',
            '  xi = clamp(xi,0.0,1.0);',
            '  //float b = 0.5*(max + min);',
            '  //float xi = 1.0 / (1.0 + exp(-((x-b)/0.001)));',
            '  float y = pow(xi,C);',
            '  y = clamp(y,0.0,1.0);',
            '  color[3] = y;',
            '  return(color);',
            '}',
        ].join('\n');

        var sampleTexture = [
            'vec2 offsetBackFront(float t, float nx){',
            '  vec2 os = vec2((1.0-mod(t,1.0))*nx-1.0, floor(t));',
            '  return os;',
            '}',

            'vec2 offsetFrontBack(float t, float nx, float ny){',
            '  vec2 os = vec2((mod(t,1.0))*nx, ny - floor(t) - 1.0);',
            '  return os;',
            '}',

            'vec4 sampleAs3DTexture(sampler2D tex, vec4 pos) {',
            '  //vec4 pos = -0.5*(texCoord - 1.0);',
            '  //pos[0] = 1.0 - pos[0];',
            '  //pos[1] = 1.0 - pos[1];',
            '  //pos[2] = 1.0 - pos[2];',
            '  //return pos;',
            '  //vec4 pos = 0.5*(1.0 - texCoord);',
            '  //return vec4(pos.xyz,0.05);',
            '  pos = 0.5*(1.0 - pos);',
            '  pos[0] = 1.0 - pos[0];',
            '  //pos = clamp(pos,0.1,0.9);',
            '  float bounds = float(pos[0] < 1.0 && pos[0] > 0.0 &&',
            '                      pos[1] < 1.0 && pos[1] > 0.0 &&',
            '                      pos[2] < 1.0 && pos[2] > 0.0 );',
            '  float nx      = float(ATLAS_X);',
            '  float ny      = float(ATLAS_Y);',
            '  float nSlices = float(SLICES);',
            '  float sx      = float(TEX_RES_X);',
            '  float sy      = float(TEX_RES_Y);',

            '  vec2 loc = vec2(pos.x/nx,pos.y/ny);',
            '  loc[1] = 1.0/ny - loc[1];',

            '  vec2 pix = vec2(1.0/nx,1.0/ny);',

            '  float iz = pos.z*nSlices;',
            '  float zs = floor(iz);',
            '  float ty  = zs/nx;',
            '  float typ = (zs+1.0)/nx;',

            '  typ = clamp(typ, 0.0, nSlices);',
            '  vec2 o0 = offsetFrontBack(ty,nx,ny)*pix;',
            '  vec2 o1 = offsetFrontBack(typ,nx,ny)*pix;',

            '  //return vec4(o0/vec2(nx,ny),0.0,0.5);',

            '  float t = mod(iz, 1.0);',
            '  vec4 slice0Color = texture2D(tex, loc + o0);',
            '  vec4 slice1Color = texture2D(tex, loc + o1);',
            '  return bounds*mix(slice0Color, slice1Color, t);',
            '}',
        ].join('\n');

        var funcs = [luma2Alpha, sampleTexture];
        if(useTransfer) funcs.push(getTransfer);

        funcs = funcs.join('\n');

        var beg = [
            'vec4 sampleStack(sampler2D tex, vec4 pos) {',
            '  vec4 col = sampleAs3DTexture(tex, pos);'].join('\n');
        var lum =
            '  col = luma2Alpha(col, GAMMA_MIN, GAMMA_MAX, GAMMA_SCALE);';
        var transfer =
            '  col = getTransfer(col[3]);';
        var end = [
            'return col;',
            '}'
        ].join('\n');

        if(useTransfer) return funcs + '\n' + beg + '\n' + lum + '\n' + transfer + '\n' + end + '\n';
        else         return funcs + '\n' + beg + '\n' + lum + '\n' + end + '\n';
    };
    var getNormal = function(type){
        if(type === 'sobel')
            return  [
                '//////////////////////////////////////////////////////////',
                '//Calculate Normal at a point',
                ' ',
                'float intensity(vec4 im){',
                '  return im[0] + im[1] + im[2];',
                '}',
                ' ',
                'vec4 getNormal(sampler2D tex, vec4 texCoord){',
                '  float nx      = float(ATLAS_X);',
                '  float ny      = float(ATLAS_Y);',
                '  float iz = 1.0/float(SLICES);',
                '  float ix      = 1.0/float(TEX_RES_X);',
                '  float iy      = 1.0/float(TEX_RES_Y);',

                '  vec4 pos = texCoord;',
                //012
                //'  vec4 p[27]'
                '  vec4 p000 = vec4(pos[0]-ix,pos[1]-iy,pos[2]-iz,0.0);',
                '  vec4 p001 = vec4(pos[0]-ix,pos[1]-iy,pos[2],0.0);',
                '  vec4 p002 = vec4(pos[0]-ix,pos[1]-iy,pos[2]+iz,0.0);',
                '  vec4 p010 = vec4(pos[0]-ix,pos[1],pos[2]-iz,0.0);',
                '  vec4 p011 = vec4(pos[0]-ix,pos[1],pos[2],0.0);',
                '  vec4 p012 = vec4(pos[0]-ix,pos[1],pos[2]+iz,0.0);',
                '  vec4 p020 = vec4(pos[0]-ix,pos[1]+iy,pos[2]-iz,0.0);',
                '  vec4 p021 = vec4(pos[0]-ix,pos[1]+iy,pos[2],0.0);',
                '  vec4 p022 = vec4(pos[0]-ix,pos[1]+iy,pos[2]+iz,0.0);',

                '  vec4 p100 = vec4(pos[0],pos[1]-iy,pos[2]-iz,0.0);',
                '  vec4 p101 = vec4(pos[0],pos[1]-iy,pos[2],0.0);',
                '  vec4 p102 = vec4(pos[0],pos[1]-iy,pos[2]+iz,0.0);',
                '  vec4 p110 = vec4(pos[0],pos[1],pos[2]-iz,0.0);',
                '  vec4 p111 = vec4(pos[0],pos[1],pos[2],0.0);',
                '  vec4 p112 = vec4(pos[0],pos[1],pos[2]+iz,0.0);',
                '  vec4 p120 = vec4(pos[0],pos[1]+iy,pos[2]-iz,0.0);',
                '  vec4 p121 = vec4(pos[0],pos[1]+iy,pos[2],0.0);',
                '  vec4 p122 = vec4(pos[0],pos[1]+iy,pos[2]+iz,0.0);',

                '  vec4 p200 = vec4(pos[0]+ix,pos[1]-iy,pos[2]-iz,0.0);',
                '  vec4 p201 = vec4(pos[0]+ix,pos[1]-iy,pos[2],0.0);',
                '  vec4 p202 = vec4(pos[0]+ix,pos[1]-iy,pos[2]+iz,0.0);',
                '  vec4 p210 = vec4(pos[0]+ix,pos[1],pos[2]-iz,0.0);',
                '  vec4 p211 = vec4(pos[0]+ix,pos[1],pos[2],0.0);',
                '  vec4 p212 = vec4(pos[0]+ix,pos[1],pos[2]+iz,0.0);',
                '  vec4 p220 = vec4(pos[0]+ix,pos[1]+iy,pos[2]-iz,0.0);',
                '  vec4 p221 = vec4(pos[0]+ix,pos[1]+iy,pos[2],0.0);',
                '  vec4 p222 = vec4(pos[0]+ix,pos[1]+iy,pos[2]+iz,0.0);',

                '  float v000 = intensity(sampleStack(tex, p000));',
                '  float v001 = intensity(sampleStack(tex, p001));',
                '  float v002 = intensity(sampleStack(tex, p002));',
                '  float v010 = intensity(sampleStack(tex, p010));',
                '  float v011 = intensity(sampleStack(tex, p011));',
                '  float v012 = intensity(sampleStack(tex, p012));',
                '  float v020 = intensity(sampleStack(tex, p020));',
                '  float v021 = intensity(sampleStack(tex, p021));',
                '  float v022 = intensity(sampleStack(tex, p022));',

                '  float v100 = intensity(sampleStack(tex, p100));',
                '  float v101 = intensity(sampleStack(tex, p101));',
                '  float v102 = intensity(sampleStack(tex, p102));',
                '  float v110 = intensity(sampleStack(tex, p110));',
                '  float v111 = intensity(sampleStack(tex, p111));',
                '  float v112 = intensity(sampleStack(tex, p112));',
                '  float v120 = intensity(sampleStack(tex, p120));',
                '  float v121 = intensity(sampleStack(tex, p121));',
                '  float v122 = intensity(sampleStack(tex, p122));',

                '  float v200 = intensity(sampleStack(tex, p200));',
                '  float v201 = intensity(sampleStack(tex, p201));',
                '  float v202 = intensity(sampleStack(tex, p202));',
                '  float v210 = intensity(sampleStack(tex, p210));',
                '  float v211 = intensity(sampleStack(tex, p211));',
                '  float v212 = intensity(sampleStack(tex, p212));',
                '  float v220 = intensity(sampleStack(tex, p220));',
                '  float v221 = intensity(sampleStack(tex, p221));',
                '  float v222 = intensity(sampleStack(tex, p222));',

                '  float gx = 1.0*v000 + 2.0*v010 + 1.0*v020 + ',
                '             2.0*v001 + 4.0*v011 + 2.0*v021 + ',
                '             1.0*v002 + 1.0*v012 + 1.0*v022 - ',
                '             1.0*v200 - 2.0*v210 - 1.0*v220 - ',
                '             2.0*v201 - 4.0*v211 - 2.0*v221 - ',
                '             1.0*v202 - 1.0*v212 - 1.0*v222;',

                '  float gy = 1.0*v000 + 2.0*v001 + 1.0*v002 + ',
                '             2.0*v100 + 4.0*v101 + 2.0*v201 + ',
                '             1.0*v200 + 1.0*v102 + 1.0*v202 - ',
                '             1.0*v020 - 2.0*v021 - 1.0*v022 - ',
                '             2.0*v120 - 4.0*v121 - 2.0*v122 - ',
                '             1.0*v220 - 1.0*v122 - 1.0*v222;',

                '  float gz = 1.0*v000 + 2.0*v100 + 1.0*v200 + ',
                '             2.0*v010 + 4.0*v110 + 2.0*v210 + ',
                '             1.0*v020 + 1.0*v120 + 1.0*v220 - ',
                '             1.0*v002 - 2.0*v102 - 1.0*v202 - ',
                '             2.0*v012 - 4.0*v112 - 2.0*v212 - ',
                '             1.0*v022 - 1.0*v122 - 1.0*v222;',
                '  vec3 grad = vec3(gx, gy, gz);',
                '  grad *= ix;',
                '  grad = clamp(grad, -1.0, 1.0);',
                '  float a =  length(grad);',

                '  if(a < 1e-3)',
                '    return vec4(0.0);',
                '  else',
                '    return vec4(normalize(grad),a);',

                '}',
                '//',
                '//////////////////////////////////////////////////////////',
            ].join('\n');
        else return [
            '//////////////////////////////////////////////////////////',
            '//Calculate Normal at a point',

            'vec4 getNormal(sampler2D tex, vec4 texCoord){',
            '  float nx      = float(ATLAS_X);',
            '  float ny      = float(ATLAS_Y);',
            '  float iz = 1.0/float(SLICES);',
            '  float ix      = 1.0/float(TEX_RES_X);',
            '  float iy      = 1.0/float(TEX_RES_Y);',

            '  vec4 pos = texCoord;',
            '  //s[0] = 1.0 - pos[0];',
            '  float C = 2.0;',
            '  float px = float(pos[0] >= (C*ix - 1.0));',
            '  float py = float(pos[1] >= (C*iy - 1.0));',
            '  float pz = float(pos[2] >= (C*iz - 1.0));',
            '  float mx = float(pos[0] <= (1.0 - C*ix));',
            '  float my = float(pos[1] <= (1.0 - C*iy));',
            '  float mz = float(pos[2] <= (1.0 - C*iz));',
            '  vec4 v0 = sampleStack(tex, texCoord + px*vec4(ix, 0., 0., 0.));',
            '  vec4 v1 = sampleStack(tex, texCoord - vec4(ix, 0., 0., 0.));',
            '  vec4 v2 = sampleStack(tex, texCoord + py*vec4(0.,     iy,  0., 0.));',
            '  vec4 v3 = sampleStack(tex, texCoord - my*vec4(0.,     iy,  0., 0.));',
            '  vec4 v4 = sampleStack(tex, texCoord + vec4(0., 0., iz, 0.));',
            '  vec4 v5 = sampleStack(tex, texCoord - mz*vec4(0., 0., iz, 0.));',

            '  float l0 = v0[3];',
            '  float l1 = v1[3];',
            '  float l2 = v2[3];',
            '  float l3 = v4[3];',
            '  float l4 = v4[3];',
            '  float l5 = v5[3];',

            '  vec3 grad = -vec3((l0-l1),(l2-l3),(l4-l5));',
            '  grad *= px*py*pz*mx*my*mz;',

            '  float a =  length(grad);',

            '  if(a < 1e-9)',
            '    return vec4(0.0);',
            '  else',
            '    return vec4(normalize(grad),a);',

            '  //return grad;',
            '}',
            '//',
            '//////////////////////////////////////////////////////////',
        ].join('\n');
    }

    var unpack = [
        'float unpack (vec4 colour)',
        '{',
        '  const vec4 bitShifts = vec4(1.0 / (256.0 * 256.0),',
        '                              1.0 / (256.0),',
        '                              1.0,',
        '                              0.0);',

        '  return dot(colour , bitShifts);',
        '}',
    ].join('\n');



    //float turb(vec3 x){
    //  float t =
    //    snoise(256.0*x)*.375 + snoise(128.0*x)*.125;
    //  t += 0.5*(0.5 - rand(x.xy));
    //  return 1.25*t;
    //}


    var integrate = function(config){
        var intersectBox = [
            ' ',
            '//->intersect box routine',
            '//',
            'bool intersectBox(in vec4 r_o, in vec4 r_d, in vec4 boxmin, in vec4 boxmax,',
            '                  out float tnear, out float tfar){',
            // compute intersection of ray with all six bbox planes
            '  vec4 invR = vec4(1.0,1.0,1.0,0.0) / r_d;',
            '  vec4 tbot = invR * (boxmin - r_o);',
            '  vec4 ttop = invR * (boxmax - r_o);',

            // re-order intersections to find smallest and largest on each axis
            '  vec4 tmin = min(ttop, tbot);',
            '  vec4 tmax = max(ttop, tbot);',

            // find the largest tmin and the smallest tmax
            '  float largest_tmin  = max(max(tmin.x, tmin.y), max(tmin.x, tmin.z));',
            '  float smallest_tmax = min(min(tmax.x, tmax.y), min(tmax.x, tmax.z));',

            '  tnear = largest_tmin;',
            '  tfar = smallest_tmax;',

            '  return(smallest_tmax > largest_tmin);',
            '}',
            '//->',
        ].join('\n');

        var integrateInit = [
            'vec4 integrateVolume(vec4 eye_o,vec4 eye_d,',
            '                     vec4 boxMin, vec4 boxMax,vec4 boxScale,',
            '                     sampler2D textureAtlas,',
            '                     //sampler2D dataBase1[1],',
            '                     ivec4 nBlocks){',

            '  vec2 vUv = gl_FragCoord.xy/iResolution.xy;',
            '  vec4 D = texture2D(BACKGROUND_DEPTH, vUv);',
            '  vec4 C = texture2D(BACKGROUND_COLOR, vUv);',

            '  float zNear = 0.01;',
            '  float zFar = 20.0;',
            '  float z_b = unpack(D);',
            '  //return vec4(z_b);',
            '  float z_n = 2.0 * z_b - 1.0;',
            '  float z_e = 2.0 * zNear * zFar / (zFar + zNear - z_n * (zFar - zNear));',

            '  float tnear, tfar;',

            '  bool hit = intersectBox(eye_o, eye_d, boxMin, boxMax, tnear,  tfar);',

            '  float eyeDist  = length(eye_o.xyz);',
            '  float rayMag   = length(eye_d);',

            '  //float clipNear = eyeDist - (1.0 - CLIP_NEAR);',
            '  float clipNear = eyeDist/rayMag - 0.275 + 0.55*CLIP_NEAR;',
            '  float clipFar = eyeDist/rayMag  + 0.275 - 0.55*CLIP_FAR;//+ (0.25 - CLIP_FAR);',
            '  //clipFar = CLIP_FAR;',
            '  if (!hit || tnear > clipFar || tfar < clipNear) {',
            '     return C;',
            '  }',

            '  // march along ray from back to front, accumulating color',

            '  float tobs   = z_e/rayMag;',
            '  if(tobs < tfar) tfar = tobs;',

            '  float tbegin = tfar;',
            '  float tend   = tnear;',
            '  //determine slice plane normal.  half between the light and the view direction',


            '  //estimate step length',
            '  const int maxSteps = ##MAXSTEPS##;',
            '  float csteps = float(BREAK_STEPS);',
            '  csteps = clamp(csteps,0.0,float(maxSteps));',
            '  float isteps = 1.0/csteps;',

            '  float tstep = 0.90*isteps;',
            '  float tfarsurf = 100.0;',
            '  float overflow = mod((tfarsurf - tfar),tstep);',

            '  float t = tbegin + overflow;',

            '  //float t = 0.5*(tnear + tfar) + overflow;',
            '  float r = 0.5 - 1.0*rand(eye_d.xy);',
            '  t = clamp(t, 0.0, clipFar);',
            '  t += 1.0*float(DITHERING)*r*tstep;',
            '  float A = 0.0;',
            '  float     tdist    = 0.0;',
            '  const int maxStepsLight = 32;',
            '  float T = 1.0;',
            '  int numSteps = 0;',

            //'return (eye_o + eye_d*t)/boxScale;',
            //'return sampleStack(textureAtlas,vec4(0.25,0.5,0.5,0.5));',
            //'return vec4(t);',

        ].join('\n');

        var integrateLoopBegin = [
            ' ',
            '//BEGIN INTEGRATION LOOP',
            'for(int i=0; i<maxSteps; i++){',
        ].join('\n');

        var sampleAt = [
            '  vec4 pos = (eye_o + eye_d*t)/boxScale; // map position to [0, 1] coordinates',
            //'vec4 col = pos;',
            '  vec4 col = sampleStack(textureAtlas,pos);',
        ].join('\n');


        var dl = [
            ' ',
            '//->compute light position and  gradient',
            '  float absorption = 1.;',
            '  vec4 lightPos = 2.0*vec4(LIGHT_POSITION,.0);',
            '  vec4 dl = lightPos - pos;',
            '//->',
        ].join('\n');

        var N =[
            ' ',
            '//->compute normal',
            '    vec4 N = getNormal(textureAtlas,pos);',
            //'return vec4(N.xyz, col[3]);',
            '//->',

        ].join('\n');

        var highlight = [
            ' ',
            '//->add highlights',
            '    col.xyz *= (1.0 -  N[3]);',
            '//->'
        ].join('\n');

        var phongFrag = [
            ' ',
            '//->phong shading computations',
            '//',
            '    float lum = N[3];',

            '    float dist = length(dl);',
            '    dl = normalize(dl);',
            '    vec4 V = -normalize(eye_d);',
            '    vec4 H = dl + V;',
            '    H = normalize(H);',

            '    float lightVal = dot(dl.xyz, N.xyz);',
            '    float spec = pow(abs(dot( N.xyz, H.xyz )),SPEC_SIZE);',
            '    spec = clamp(spec, 0.0, spec);',
            '    // += vec4(vec3(spec),0.0);',

            '    float kn = pow(abs(0.0*N[3]),NORMAL_INTENSITY);',
            '    float ka = KA;',
            '    float kd = KD;',
            '    float ks = 20.0*SPEC_INTENSITY;',
            '    kn = clamp(kn,0.0,1.0);',
            '    //float kn = 1.0;',
            '    col *= (ka + kd*vec4(vec3(lightVal),kn));',
            '    col += col[3]*ks*N[3]*vec4(spec);',
            '    col = clamp(col, 0.0, 1.0);',
            '    //col += H;',
            '    //col = N;',
            '//',
            '//->end phong',
        ].join('\n');

        var deepFrag = [
            ' ',
            '//begin deep shading secondary integration',
            '//',
            '    float lstep = LIGHT_DEPTH/float(LIGHT_SAMPLES);',
            '    float Dl = 0.0;',

            '    vec3 DISP_BIAS = vec3(100.5, 200.3, 0.004);',
            '    dl = normalize(dl);',

            '    vec3 dtemp = cross(dl.xyz,vec3(1.0,1.0,1.0)); dtemp = normalize(dtemp);',
            '    vec3 N1 = cross(dl.xyz,dtemp);',
            '    vec3 N2 = cross(dl.xyz,N1);',
            '    //N1 = normalize(N1);',
            '    //N2 = normalize(N2);',
            '      float r0 = 1.0 - 2.0*rand(pos.xy + eye_d.zx); //create three random numbers for each dimension',
            '      float r1 = 1.0 - 2.0*rand(pos.yz + eye_d.zx);',
            '      float r2 = 1.0 - 2.0*rand(pos.xz + eye_d.yx);',
            '    for(int j=0; j<maxStepsLight; j++){ ',
            '      if (j > LIGHT_SAMPLES) break;',

            '      float lti = (float(j))*lstep;',
            '      vec4 Ni   = DISPERSION*(r0*dl + vec4(r1*N1 + r2*N2, 0.0));',

            '      vec4 lpos = pos + lti*dl;',

            '      r0 = 1.0 - 2.0*rand(lpos.xy + eye_d.zx); //create three random numbers for each dimension',
            '      r1 = 1.0 - 2.0*rand(lpos.yz + eye_d.zx);',
            '      r2 = 1.0 - 2.0*rand(lpos.xz + eye_d.yx);',

            '      lpos += lti*Ni;',
            '      vec4 dens = sampleStack(textureAtlas,lpos);',

            '      float Kdisp = DISP_SIG;',
            '      float sl = float(maxStepsLight)/float(LIGHT_SAMPLES);',
            '      //lti *= dens.w;',

            '      //dens.w = 1.0 - pow(abs(1.0-dens.w), sl);',
            '      dens.w *= 1.0*DENSITY;',
            '      //dens.w = clamp(dens.w, 0.0, 1.0);',
            '      Dl =  (1.0-Dl)*dens.w + Dl;',
            '      //Dl =  (1.0-dens.w)*Dl + dens.w;',
            '    }',
            '    //Dl = clamp(Dl,0.0,1.0);',
            '    //col *= (1.0 - exp(-Dl));',
            '    col.xyz *= (1.0 - Dl);',
            '    col.xyz *= 2.0;',
            '//',
            '//end deep shading secondary integration',
        ].join('\n');

        var integrateLoopEnd = [
            ' ',
            '//Finish up by adding brightness/density',
            //'col = N;',
            '    col.xyz *= BRIGHTNESS;',
            '    float s = 1.0*float(##MAXSTEPS##)/ float(BREAK_STEPS);',
            '    col.w *= DENSITY;',
            '    col.w = clamp(col.w, 0.0,1.0);',
            '    float stepScale = (1.0 - powf((1.0-col.w),s));',
            '    col.w = stepScale;',
            //'    col.w *= DENSITY;',
            '    col.xyz *= col.w;',

            '    C = (1.0-col.w)*C + col;',
            '    //float r0 = 0.5 + 1.0*rand(eye_d.xy);',
            '    t -= tstep;',
            '    numSteps = i;',

            '    if (i > BREAK_STEPS || t  < tend || t < clipNear ) break;',
            '}',
        ].join('\n');

        var integrateEnd = [
            '  //if(!over) C += (1.0-C.w)*vec4(0.5);',
            '  return C;',
            '}',
        ].join('\n');
        var output = [intersectBox, integrateInit, integrateLoopBegin, sampleAt];
        if(config.lighting.phong || config.lighting.deep) output.push(dl);
        if(config.lighting.phong || config.highlight) output.push(N);
        if(config.highlight) output.push(highlight);
        if(config.lighting.phong) output.push(phongFrag);
        if(config.lighting.deep) output.push(deepFrag);
        output.push(integrateLoopEnd);
        output.push(integrateEnd);
        return output.join('\n');
    }

    var main = [
        'void main()',
        '{',
        '  vec4 eyeRay_d, eyeRay_o;',
        '  vec2 fragCoord = gl_FragCoord.xy;',

        '  eyeRay_d.xy = 2.0*fragCoord.xy/iResolution.xy - 1.0;',
        '  eyeRay_d[0] *= iResolution.x/iResolution.y;',

        '  float fovr = 40.*M_PI/180.;',
        '  eyeRay_d[2] = -1.0/tan(fovr*0.5);',
        '  eyeRay_d   = eyeRay_d*viewMatrix;',
        '  eyeRay_d[3] = 0.0;',
        '  //ed = normalize(ed);',
        '  eyeRay_o = vec4(cameraPosition,1.0);',

        '  vec4 boxMin = vec4(-1.0);',
        '  vec4 boxMax = vec4( 1.0);',
        '  vec4 boxTrans = vec4(0.0, 0.0, 0.0, 0.0);',
        '  vec4 boxScale = vec4(BOX_SIZE,1.0);',
        '  //boxScale = vec4(0.5);',
        '  boxMin *= boxScale;',
        '  boxMax *= boxScale;',
        '  boxMin += boxTrans;',
        '  boxMax += boxTrans;',
        '  ivec4 nBlocks = ivec4(BLOCK_RES_X,',
        '                        BLOCK_RES_Y,',
        '                        BLOCK_RES_Z,1);',

        '  vec4 C = integrateVolume(eyeRay_o, eyeRay_d,',
        '                           boxMin, boxMax, boxScale,',
        '                           textureAtlas,nBlocks);',

        '  gl_FragColor = C;',
        '  return;',

        '}',
    ].join('\n');

    var output = [uniformVars];
    if(config.lighting){
        output.push(lightPos);
        if(config.lighting.phong === true)
            output.push(phongVars);
        if(config.lighting.deep === true)
            output.push(deepVars);

    };

    if(config.transfer){
        output.push(transferVars);
    };

    output.push(powf(config.pow));
    output.push(unpack);
    output.push(rand);
    output.push(sampleStack(config.transfer));
    var gradType = config.gradientType ? config.gradientType : 'central';
    if(config.highlight || config.lighting.phong) output.push(getNormal(gradType));
    output.push(integrate(config));
    output.push(main);
    output = output.join('\n')
    output = output.replace(/##MAXSTEPS##/g, config.maxSteps);
    this.source = output;
};



function DepthShader(config){
    ShaderSource.call(this, config);
};

DepthShader.prototype = new ShaderSource();

DepthShader.prototype.getID = function(){
    var depth = this.settings.depth ? 1 : 0;
    var type = this.settings.type == 'fragment' ? 2 : 0;
    return depth + type;
};

DepthShader.prototype.config = function(config){


	if (0) { //shader pack float test routine
		var unpackjs = function (c) {
			var shift = [1 / 256 / 256 / 256, 1 / 256 / 256, 1 / 256, 1];
			var sum = 0;
			shift.forEach(function (e, i, a) {
				sum += a[i] * c[i]
			})
			return sum;
		};

		var packjs = function (d) {
			var bitsh = [256 * 256, 256, 1, 1 / 256];
			var bitMask = [0, 1 / 256, 1 / 256, 1 / 256];
			var comp = [bitsh[0] * d, bitsh[1] * d, bitsh[2] * d, bitsh[3] * d];
			console.log('1: ', comp);
			comp.forEach(function (e, i, a) {
				a[i] = e % 1
			});
			console.log('2: ', comp);
			comp = [comp[0] - comp[0] * bitMask[0],
					comp[1] - comp[0] * bitMask[1],
					comp[2] - comp[1] * bitMask[2],
					comp[3] - comp[2] * bitMask[3]];
			console.log('3: ', comp);
			return comp;
		};

		var unpackjs = function (c) {
			var shift = [1 / 256 / 256, 1 / 256, 1, 256];
			var sum = 0;
			shift.forEach(function (e, i, a) {
				sum += a[i] * c[i]
			})
			return sum;
		};

		var test = [1 / 255, 1 / 127, 1 / 63, 1 / 31, 1 / 15, 1 / 7, 0.0, 2.0, 4.0, 8.0, 16.0, 356 + 1 / 7];
		test.forEach(function (e, i, a) {
			var p = packjs(e);
			var up = unpackjs(p);
			console.log('test ' + i + ': ', e, up, p);
		});
	}

	var pack = [
		'vec4 pack (float depth){',
		'const vec4 bitSh = vec4(256 * 256,',
		'                        256,',
		'                        1.0,',
		'                        0.0);',
		'const vec4 bitMsk = vec4(0.0,',
		'                         1.0 / 256.0,',
		'                         1.0 / 256.0,',
		'                         1.0 / 256.0);',
		'highp vec4 comp = fract(depth * bitSh);',
		'comp -= comp.xxyz * bitMsk;',
		'return comp;',
		'}'
	].join('\n');

	//24 bit precision pack that preserves the alpha value.
	var fragDepthBack = [
		'varying vec2 vUv;',
		'uniform float near;',
		'uniform float far;',
		'uniform int USE_COLOR;',
		'varying vec3 vColor;',
		pack,
		'void main() {',
		' if(USE_COLOR == 0){',
		'  gl_FragColor = pack(0.999999);',
		' } ',
		' else{',
		'  gl_FragColor = vec4(0.5);',
		' }',
		'}'
	].join('\n');

	var fragDepth = [
		'varying vec2 vUv;',
		'uniform float near;',
		'uniform float far;',
		'uniform int USE_COLOR;',
		'varying vec3 vColor;',
		pack,
		'void main() {',
		' if(USE_COLOR == 0){',
		'  gl_FragColor = pack(gl_FragCoord.z);',
		' } ',
		' else{',
		'  gl_FragColor.xyz = vColor;',
		' }',
		'}'
	].join('\n');

	var vertDepth = [
		'attribute vec3 color;',
		'varying vec2 vUv;',
		'varying vec3 vColor;',
		'void main() {',
		'  vUv = uv;',
		'  vColor = color;',
		'  vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );',
		'  gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );',
		'}'
	].join('\n');

	var spriteTex = THREE.ImageUtils.loadTexture('/js/volume/icons/dot.png');

	var frag = [
		'uniform sampler2D tex1;',
		'uniform float near;',
		'uniform float far;',
		'uniform int USE_COLOR;',
		'varying vec3 vColor;',

		//'varying float depth;',
		pack,
		'void main() {',
		' float r2 = dot(gl_PointCoord - vec2(0.5),gl_PointCoord - vec2(0.5));',
		' float sw = float(r2 < 0.25);',
		' if(USE_COLOR == 0){',
		'   vec4 C  = texture2D(tex1, gl_PointCoord);',
		'   float a = C.a;',
		'   float d = gl_FragCoord.z;',
		'   vec4 packd = pack(d);',
		'   packd.a = a;',
		'   gl_FragColor = packd;',
		' }',
		' else{',
		'  vec4 C = vec4(vColor,0.0);',
		'  C.a += sw;',
		//'  gl_FragColor.rgb = vColor;',
		'  gl_FragColor  = texture2D(tex1, gl_PointCoord);',
		'  gl_FragColor.xyz *= vColor;',

		' }',
		'}'
	].join('\n');

	var vert = [
		'attribute vec3 color;',
		'varying vec3 vColor;',
		'void main() {',
		'  vColor = color;',
		'  vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );',
		'  gl_PointSize = 0.1 * ( 300.0 / length( mvPosition.xyz ) );',
		'  gl_Position = projectionMatrix * mvPosition;',
		'}'
	].join('\n');

    if(config.transfer){
        output.push(transferVars);
    };
    var output = [];
    if(config.depth === true){
         if(config.type == 'vertex'){
            output.push(vertDepth);
        }else{
            if(config.back)
                output.push(fragDepthBack);
            else
                output.push(fragDepth);
        }
    }
    else{
        if(config.type == 'vertex'){
            output.push(vert);
        }else{

            output.push(frag);

        }
    }
    output = output.join('\n')

    this.source = output;
};
