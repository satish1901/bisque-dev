/*******************************************************************************
bioWeb3D - a WebGL based volumue renderer component for the Bisque system
@author John Delaney

Configurations:
resource   - url string or bqimage (required)
phys       - image phys BQImagePhys (preferred)
preferences - BQPpreferences object (preferred)

Events:
loaded     - event fired when the viewer is loaded

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

Ext.require([
		'Ext.chart.*',
		'Ext.data.*',
		'Ext.Window',
		'BQ.viewer.Volume.ThreejsPanel',
		'Ext.tip.QuickTipManager',
		'Ext.menu.*',
		'Ext.form.field.ComboBox',
		'Ext.layout.container.Table',
		'Ext.layout.container.Accordion',
		'Ext.container.ButtonGroup',
		'Ext.fx.target.Sprite',
	]);

Ext.define('BQ.viewer.Volume.volumeScene', {
	mixins : {
		observable : 'Ext.util.Observable'
	},

	alias : 'widget.volumeScene',

	constructor : function (config) {
		// The Observable constructor copies all of the properties of `config` on
		// to `this` using Ext.apply. Further, the `listeners` property is
		// processed to add listeners.
		//
		this.mixins.observable.constructor.call(this, config);

		this.shaders = {};
		this.materials = {};
		this.uniforms = {};

		this.scene = new THREE.Scene();
		this.sceneData = new THREE.Scene();
		this.sceneDataColor = new THREE.Scene();

		var material = new THREE.MeshBasicMaterial({
				color : 0xffff00
			});

		this.cube = new THREE.CubeGeometry(1.0, 1.0, 1.0);
		this.cubeMesh = new THREE.Mesh(this.cube, material);
		this.scene.add(this.cubeMesh);

		this.light = new THREE.PointLight(0xFFFFFF, 1, 100);
		this.scene.add(this.light);
		this.canvas3D.scene = this.scene;

		this.canvas3D.scene = this.scene;

		this.canvas3D.plane = this.plane;
		this.setMaxSteps = 32;
		//this.renderingQueued = false;
		this.oldScale = new THREE.Vector3(0.5, 0.5, 0.5);
		this.currentScale = new THREE.Vector3(0.5, 0.5, 0.5);

	},

	initComponent : function () {},

	setUniform : function (name, value, reset, timeOut) {
		//console.log('bef',reset);
		if (typeof(reset) === 'undefined')
			reset = true;
		//console.log('aft',reset);
		this.uniforms[name].value = value;
		stepVal = reset ? 32 : this.setMaxSteps;

		if (timeOut)
			this.renderingQueued = setTimeout(callback(this, function () {
						this.canvas3D.rerender();
						this.setMaxSteps = stepVal;
						this.renderingQueued = null;
					}), 200);
		else {
			this.canvas3D.rerender();
			this.setMaxSteps = stepVal;
		}
	},

	initUniform : function (name, type, value) {

		this.uniforms[name] = {
			type : type,
			value : value
		};
		this.setMaxSteps = 32;
		this.canvas3D.rerender();
	},

	getMaterial : function (index) {
		return this.materials[index];
	},

	scaleCube : function (inScale) {

		this.setUniform('BOX_SIZE', inScale);

		var cube = this.cube;
		var bMax = cube.vertices[0];
		var scale = inScale.clone();

		scale.divide(this.currentScale);

		this.oldScale = this.currentScale.clone();
		this.currentScale = inScale.clone();

		cube.dynamic = true;
		cube.verticesNeedUpdate = true;
		var mat = new THREE.Matrix4().scale(scale);
		this.cube.applyMatrix(mat);
		this.canvas3D.rerender();
	},

	getRescale : function () {
		//since we scale locally, we lose the old scale that we scaled from, so we track
		//it then return the new scaling parameter
		var scale = this.currentScale.clone();
		scale.divide(this.oldScale);
		return scale;
	},

	getHalf : function () {
		var cube = this.cube;
		return cube.vertices[0];
	},

    setConfigurable : function(materialID, shaderType, config){
        var shader = this.materials[materialID][shaderType];
        shader.set(config);
        var fragmentKey = shader.getID();
		if (!this.shaders[fragmentKey]){
		    this.shaders[fragmentKey] = shader.getSource();
        };
        var threeShader = this.materials[materialID].threeShader;
		var type = shaderType + 'Shader';
        threeShader[type] = this.shaders[fragmentKey];
        threeShader.needsUpdate = true;
        this.updateMaterials();
        this.canvas3D.rerender();
    },

	constructMaterial : function (material) {

		//if (material.built === true)
		//	return true;

		var vertexKey   = material.vertex.getID();
		var fragmentKey = material.fragment.getID();
        this.shaders[vertexKey]   = material.vertex.getSource();
		this.shaders[fragmentKey] = material.fragment.getSource();

		material.threeShader.vertexShader = this.shaders[vertexKey];
		material.threeShader.fragmentShader = this.shaders[fragmentKey];
	},

	updateMaterials : function () {
		var me = this;
		for (var prop in this.materials) {
			this.constructMaterial(this.materials[prop]);
		}
	},
/*
	fetchFragments : function (url, storeId, manip) {
		var me = this;
		var manipulate = manip;
		var id = storeId;
		Ext.Ajax.request({
			url : url,
			callback : function (opts, succsess, response) {
				if (response.status >= 400)
					BQ.ui.error(response.responseText);
				else {
					var fetchedText = response.responseText;
					me.shaders[id] = fetchedText;
					if (manipulate) {
						var newText = manipulate(fetchedText);
						me.shaders[id] = newText;
					}
					me.updateMaterials();
				}
			},
			scope : this,
			disableCaching : false,
			listeners : {
				scope : this,
				beforerequest : function () {
					this.setLoading('Loading images...');
				},
				requestcomplete : function () {
					this.setLoading(false);
				},
				requestexception : function () {
					this.setLoading(false);
				},
			},
		});
	},

	initFragment : function (url, id, manipulate) {

		if (!this.shaders[url]) {
			this.shaders[url] = ''; //placeholder so we don't fetch this fragment many times
			this.fetchFragments(url, id, manipulate);
		} else {
			if (manipulate) {
				var shader = this.shaders[url];
				var newText = manipulate(shader);
				this.shaders[id] = newText;
				this.updateMaterials();
			}
		}
	},
*/
    initFragmentByConfig : function (config, id) {
        //console.log(shaderConfig().rayCastShader(config));
        this.shaders[id] = shaderConfig().rayCastShader(config);
        this.updateMaterials();
	},

	initMaterial : function (config) {
        var me = this;
		var name = config.name;
		var vertUrl = config.vertex.url;
		var fragUrl = config.fragment.url;
		var vertId = vertUrl;
		var fragId = fragUrl;
		var uniforms = config.uniforms ? config.uniforms : this.uniforms;

		if (config.vertex.id)
			vertId = config.vertex.id;
		if (config.fragment.id)
			fragId = config.fragment.id;

		var threeMaterial = new THREE.ShaderMaterial({
				uniforms : uniforms,
				vertexShader : "",
				fragmentShader : "",
				side : THREE.DoubleSide,
			});

		var newMaterial = {
			name : name,
			vertexId : vertId,
			fragmentId : fragId,
			built : false,
            shader : {},
			threeShader : threeMaterial,
			buildFunc : this.defaultBuildFunc,
		};
		this.materials[name] = newMaterial;
        /*
		this.initFragment(vertUrl, vertId, config.vertex.manipulate);
        */
        //init the fragment shader,
        var shaderTypes = ["fragment", "vertex"];
        for(var i = 0; i < shaderTypes.length; i++){
            var type = shaderTypes[i];

            if(config[type].url){ //here we hard code getting shader by URL for convenience
                var newConfig = {
			        url : config[type].url,
                    loader : me,
                    onloaded: function(){
                        me.updateMaterials();
                    }
                }
                var newShader = new UrlShader(newConfig);
                newMaterial[type] = newShader;
                this.shaders[newShader.getID()] = newShader.getSource();

            }
            else if(config[type].config){
                var ctor   = config[type].ctor;
                var fconfig = config[type].config;
                var newShader = new ctor(fconfig);
                newMaterial[type] = newShader;
                this.shaders[newShader.getID()] = newShader.getSource();
            }
        };

	},

	loadMaterial : function (name) {
		this.cubeMesh.material = this.materials[name].threeShader;
		this.canvas3D.rerender();
	}

});

Ext.define('BQ.viewer.Volume.renderProgress', {
	extend : 'Ext.ProgressBar',

	alias : 'widget.renderProgress',
	border : false,
	requires : ['Ext.window.MessageBox'],

	initComponent : function () {},

	afterFirstLayout : function () {
		////////////////////
		this.callParent();
		this.doUpdate();
	},

	doUpdate : function () {
		var renderProgress = this.setMaxSteps / 512;
		this.updateProgress(renderProgress);
		var me = this;
		requestAnimationFrame(function () {
			me.doUpdate()
		});
	},
});

Ext.define('BQ.viewer.Volume.Panel', {
	alias : 'widget.bq_volume_panel',
	extend : 'Ext.container.Container',
	border : 0,
	cls : 'bq-three-container',
	layout : 'fit',

	initComponent : function () {
		this.update_delay_ms = 50;
		this.addListener('resize', this.onresize, this);
        var me = this;
        var restep = function(event){
            if(event.button >= 0){
                me.sceneVolume.setMaxSteps = 32;
                me.rerender();
            }
        };

		this.canvas3D = Ext.create('BQ.viewer.Volume.ThreejsPanel', {
			itemId : 'canvas3D',
            listeners: {
                mousemove : restep,
                mousedown : restep,
                mousewheel: restep,
                //DOMMouseScrool: restep,
            }
				//onAnimate : callback(this, this.onAnimate),
				//onAnimateOverride : callback(this, this.onAnimateOverride),
		});
		this.canvas3D.animate_funcs[1] = callback(this, this.onAnimate);

        this.sceneVolume = new BQ.viewer.Volume.volumeScene({
				canvas3D : this.canvas3D
		});

		//-------------------------------------
		//Platform and browser version checking
		//-------------------------------------

		var fragUrl, usePow;
		if (Ext.isWindows) {
			if (Ext.isChrome) {
				if (Ext.chromeVersion < 37)
					usePow = false;
                else
                	usePow = true;

			} else
				usePow = true;
		} else
				usePow = true;

        this.maxSteps = 64;
        this.numChannels = 3;
        this.shaderConfig = {
            lighting: {
                phong: false,
                deep: false,
            },
            transfer: false,
            pow: true,
            highlight: false,
            //gradientType: 'sobel',
            //gradientType: 'directional',
            gradientType: 'std',
            maxSteps: this.maxSteps,
            usePow: usePow,
        };

		this.sceneVolume.initMaterial({
			name : 'default',
			vertex : {
                ctor : UrlShader,
                config : {
				    url : "/js/volume/shaders/rayCast.vs",
                    loader: this.sceneVolume,
                    onloaded: function(){
                        me.sceneVolume.updateMaterials();
                    }
                }
			},

			fragment : {
                ctor: VolumeShader,
				config: this.shaderConfig,
                //url : fragUrl,
			}
		});

		this.plug_ins = [new VolumeTime(this), new VolumeAtlas(this),
			new VolumeDisplay(this), new VolumeFormat(this)];

		this.preMultiplyAlpha = false;
		this.currentTime = 0;
		//this.createPlaybackPanel();
		//debugger;

		var me = this;

		this.items = [this.canvas3D,{
			xtype : 'component',
			itemId : 'button-fullscreen-vol',
			autoEl : {
				tag : 'span',
				cls : 'control fullscreen',
			},
			listeners : {
				scope : this,
				click : {
					element : 'el', //bind to the underlying el property on the panel
					fn : this.onFullScreenClick,
				},
			},
		}, {
			xtype : 'component',
			itemId : 'button-menu',
			autoEl : {
				tag : 'span',
				cls : 'control viewoptions',
			},
			listeners : {
				scope : this,
				click : {
					element : 'el', //bind to the underlying el property on the panel
					fn : this.onMenuClick,
				},
			},
		}, {
			xtype : 'component',
			itemId : 'tool-menu',
			autoEl : {
				tag : 'span',
				cls : 'control tooloptions',
			},
			listeners : {
				scope : this,
				click : {
					element : 'el', //bind to the underlying el property on the panel
					fn : this.onToolMenuClick,
				},
			},
		}];

		this.on({
            afterlayout: function () {
                if(this.firstLoad) return;
                me.createViewMenu();


                me.BQImageRequest();
                me.initHistogram();
                me.createToolPanel();
				//me.createClipSlider();
				me.createZoomSlider();

				me.createAnimPanel();
				me.createPlaybackPanel();
			    me.createToolMenu();

				//this.showAnimPanel();
                this.playbackPanel.hide();
                this.animPanel.hide();

                this.firstLoad = true;
				//this.setLoading(false);

            },

			loaded : function () {
				console.log(this.constructAtlasUrl());
				me.initUniforms();
				me.wipeTextureTimeBuffer();
				me.updateTextureUniform();
                me.fetchHistogram();
                me.canvas3D.doAnimate();
			},
			scope : me,
		});

//        console.log(shaderConfig().rayCastShader);

		this.callParent();
	},

    setModel : function (field, value){
        this.shaderConfig[field] = value;
        this.sceneVolume.updateShader
    },

	onresize : function (comp, w, h, ow, oh, eOpts) {
		if (this.sceneVolume.uniforms['iResolution']) {
			var pw = this.canvas3D.getPixelWidth();
			var ph = this.canvas3D.getPixelHeight();
			var newRes =
				new THREE.Vector2(pw, ph);
			this.sceneVolume.setUniform('iResolution', newRes);

			this.screenBuffer
				 = new THREE.WebGLRenderTarget(pw, ph, {
					minFilter : THREE.LinearFilter,
					magFilter : THREE.NearestFilter,
					format : THREE.RGBAFormat
				});
            /*
			this.accumBuffer1
				= new THREE.WebGLRenderTarget(w, h, {
					minFilter : THREE.LinearFilter,
					magFilter : THREE.NearestFilter,
					format : THREE.RGBAFormat
				});
            */
			var materialScreen = this.sceneVolume.getMaterial('screen');
			materialScreen.depthWrite = false;
			materialScreen.threeShader.uniforms.tDiffuse.value = this.accumulationBuffer;

            //this is necessary to update the quad which renders the scene and captures
            //the texture map to allow compositing

			var quad = this.sceneScreen.children[0];

			quad.geometry.width = pw;
			quad.geometry.height = ph;
			quad.geometry.vertices[0] = new THREE.Vector3(-pw / 2, ph / 2, 0);
			quad.geometry.vertices[1] = new THREE.Vector3(pw / 2, ph / 2, 0);
			quad.geometry.vertices[2] = new THREE.Vector3(-pw / 2, -ph / 2, 0);
			quad.geometry.vertices[3] = new THREE.Vector3(pw / 2, -ph / 2, 0);

			quad.geometry.verticesNeedUpdate = true;
			quad.geometry.dynamic = true;

			//this.sceneScreen.children[0] =

			this.orthoCamera.left = -pw / 2;
			this.orthoCamera.right = pw / 2;
			this.orthoCamera.top = ph / 2;
			this.orthoCamera.bottom = -ph / 2;
			this.orthoCamera.updateProjectionMatrix();
            //this.sceneVolume.setConfigurable("default",
            //                                 "fragment",
            //                                 this.shaderConfig);
			this.rerender();
		}
	},

	rerender : function (input) {

		if (!input){
			input = 32;
            this.progressive = true;
        }
        else this.progressive = false;
		setTimeout(callback(this, function () {
			this.canvas3D.rerender();
			this.sceneVolume.setMaxSteps = input;
		}), this.update_delay_ms);

    },

	onAnimate : function () {
		//if (this.canvas3D.mousedown)
		//	this.sceneVolume.setMaxSteps = 32;
        if(!this.progressive){
            this.sceneVolume.setUniform('BREAK_STEPS',
				                        this.sceneVolume.setMaxSteps, false);
			this.canvas3D.needs_render = false;
            return;
        }

		if (this.sceneVolume.setMaxSteps < this.maxSteps) {
			//console.log('multiplying',this.sceneVolume.setMaxSteps);

			this.sceneVolume.setUniform('BREAK_STEPS',
				                        this.sceneVolume.setMaxSteps, false);
			this.sceneVolume.setMaxSteps *= 1.5;
		} else {
			this.sceneVolume.setMaxSteps = this.maxSteps;
			this.canvas3D.needs_render = false;
		}
	},

    initHistogram : function() {
		var me = this;

        this.model = {
            histogramRaw: {r:[], g:[], b:[]},
            histogram: {r:[], g:[], b:[]},
            gamma: {min: 0, max: 1.0, scale: 1.0},
            loaded: false,
            updateHistogram : function(){
                for(var chan in this.histogramRaw){
                    var hist    = this.histogramRaw[chan];
                    var newHist = this.histogram[chan];

                    var maxVal = 0;
                    var minVal = 999;
                    var min = this.gamma.min;
                    var max = this.gamma.max;
                    var C   = this.gamma.scale;
                    //var C = 1.0;
                    var start = Math.floor(this.gamma.min * hist.length);
                    var end = Math.floor(this.gamma.max * hist.length);

                    var lookUp = new Array();
                    var avg = 0;
                    hist.forEach(function(val,i,a){
                        avg += val;
                        minVal = val < minVal ? val : minVal;
                        maxVal = val > maxVal ? val : maxVal;
                    });

                    avg /= hist.length;
                    var l = hist.length;
                    for (var i = 0; i < newHist.length; i++) {
                        lookUp[i] = 0;
                        newHist[i] = 0;
                        if (i > start && i < end) {
                            var val = l*(i - start) / (end - start);
                            var plogy = C * Math.log(val);
                            var modVal = Math.exp(plogy);
                            modVal = modVal < 0 ? 0 : (modVal > hist.length ? hist.length : modVal);
                            var newBin = Math.floor(modVal);
                            newBin = newBin < hist.length - 1 ? newBin : hist.length - 1;
                            lookUp[i] = newBin;
                            if(C == 1) lookUp[i] = i;
                        }
                        if(i < start)
                            lookUp[i] = 0;
                        if(i > end)
                            lookUp[i] = newHist.length - 1;

                    }
                    var spread = Math.ceil(hist.length/(end - start));
                    for (var i = 0; i < lookUp.length - spread; i++) {
                        newHist[lookUp[i]] += 1.0/spread * hist[i];
                    }
                }
                me.fireEvent("histogramupdate", me);
            }
        }
    },

    BQImageRequest : function () {
        var me = this;

		if (!this.resource) {
			BQ.ui.error('No image defined...');
			return;
		}

		this.setLoading('Loading...');

		if (typeof this.resource === 'string') {
			BQFactory.request({
				uri : this.resource,
				uri_params : {
					view : 'short'
				},
				cb : callback(this, this.onImage),
				errorcb : callback(this, this.onerror),
			});
		} else if (this.resource instanceof BQImage) {
			this.onImage(this.resource);
		}
    },

	afterFirstLayout : function () {
        var me = this;

        /////////////////////////////////////////////////
		// begin setup backbuffer rendering:
		// putting it here for experimentation
		/////////////////////////////////////////////////

		this.screenBuffer
			 = new THREE.WebGLRenderTarget(this.getWidth(), this.getHeight(), {
				minFilter : THREE.LinearFilter,
				magFilter : THREE.NearestFilter,
				format : THREE.RGBAFormat
			});

	    this.toggle = true;

		this.orthoCamera = new THREE.OrthographicCamera(-this.getWidth() / 2,
				this.getWidth() / 2,
				this.getHeight() / 2,
				-this.getHeight() / 2,
				-10000, 10000);
		this.orthoCamera.position.z = 1000;

		var screenUniforms = {
			tDiffuse : {
				type : "t",
				value : this.screenBuffer
			}
		};

		this.sceneVolume.initMaterial({
			name : 'screen',
			vertex : {
				url : "/js/volume/shaders/screen.vs"
			},
			fragment : {
				url : "/js/volume/shaders/screen.fs",
			},
			uniforms : screenUniforms,
		});

		var materialScreen = this.sceneVolume.getMaterial('screen');
		materialScreen.depthWrite = false;

		this.sceneScreen = new THREE.Scene();

		var plane = new THREE.PlaneGeometry(this.getWidth(), this.getHeight());
		var quad = new THREE.Mesh(plane, materialScreen.threeShader);
		quad.position.z = -100;

		this.sceneScreen.add(quad);
		this.canvas3D.render_override = true;
		this.canvas3D.renderer.preserveDrawingBuffer = true;

		/////////////////////////////////////////////////
		/////////////////////////////////////////////////

		//query the maximum render buffer size from the gpu
		//

		this.callParent();
	},

	getMaxTextureSize : function () {
		if (!this.maxTextureSize) {
			var ctx = this.canvas3D.renderer.getContext();
			this.maxTextureSize = 0.5 * ctx.getParameter(ctx.MAX_TEXTURE_SIZE);
		}
		return this.maxTextureSize;
	},

    fetchHistogram : function () {
        url = this.constructAtlasUrl().replace('format=jpeg','histogram');

        console.log("hist url: ", url);
        if(!this.model)
            this.initHistogram();
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
                    var rChan = BQ.util.xpath_nodes(xmlDoc, "resource/histogram[@name='channel']/value");

                    var dim = 0;
                    for (var chan in this.model.histogram) {
                        if(!rChan[dim]) continue;
                        var tmp = rChan[dim].innerHTML.split(",");
                        if (this.model.histogram.hasOwnProperty(chan)) {
                            var channel = this.model.histogram[chan];
                            if(channel.length == 0) channel == tmp;
                            tmp.forEach(function(e,i,a){
                                channel[i] = parseInt(tmp[i]);
                            });
                        }
                        dim++;
                        this.numChannels = dim;
                        this.model.histogramRaw[chan] = this.model.histogram[chan].slice(0);
                    }
                    this.model.loaded = true;
                    this.fireEvent("histogramloaded",this);
                    this.sceneVolume.initUniform('NUM_CHANNELS', "i", this.numChannels);
                    this.model.updateHistogram();

                }
            },
        });
    },

	fetchDimensions : function (url, type) {
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
					if (type == 'slice' || type == 'atlas' || type == 'resized') {
						var xRes = BQ.util.xpath_nodes(xmlDoc, "//tag[@name='image_num_x']/@value");
						var yRes = BQ.util.xpath_nodes(xmlDoc, "//tag[@name='image_num_y']/@value");
						if (type == 'atlas') {
							this.loadedDimFullAtlas = true;
							this.dims.atlas.x = xRes[0].value;
							this.dims.atlas.y = yRes[0].value;
						}
						if (type == 'resized') {
							this.loadedDimResizedAtlas = true;
							this.dims.atlasResized.x = xRes[0].value;
							this.dims.atlasResized.y = yRes[0].value;
						}
					}

					if (this.loadedDimFullAtlas && this.loadedDimResizedAtlas) {

						this.xTexSizeRatio = this.dims.atlasResized.x / this.dims.atlas.x;
						this.yTexSizeRatio = this.dims.atlasResized.y / this.dims.atlas.y;

						//a lot of information is already loaded by the phys object:
						//this.setLoading(false);
						//this.sceneVolume.loadMaterial('forwardDiffuse');
						this.tempMaterial
							 = new THREE.MeshBasicMaterial({
								color : 0xffffff
							});
						this.sceneVolume.cubeMesh.material = this.tempMaterial;
						this.sceneVolume.loadMaterial('default');

						this.fireEvent('loaded', this);

					}
				}
			},
		});
	},

	//----------------------------------------------------------------------
	// texture loadi
	//----------------------------------------------------------------------

	updateTextureUniform : function () {
		var me = this;

		if (!this.textureTimeBuffer[this.currentTime]) {
			//var textureAtlas' = new Array();
			var textureAtlas = new THREE.ImageUtils.loadTexture(this.constructAtlasUrl(), undefined, function () {
                me.setLoading(false);
				me.rerender()
			});
			textureAtlas.generateMipmaps = false;
			textureAtlas.magFilter = THREE.LinearFilter;
			textureAtlas.minFilter = THREE.LinearFilter;
			textureAtlas.wrapS = THREE.MirroredRepeatWrapping;
			textureAtlas.wrapT = THREE.MirroredRepeatWrapping;

			this.textureTimeBuffer[this.currentTime] = textureAtlas;
			//this.uniforms.textureAtlas.value = textureAtlas;
		}
		this.sceneVolume.setUniform('textureAtlas', this.textureTimeBuffer[this.currentTime]);
		this.update = true;
	},

	initTextures : function () {
		var resUniqueUrl = (this.hostName ? this.hostName : '') + '/image_service/image/' + this.resource.resource_uniq;
		var slice;
		this.dims.slice.x = this.phys.x;
		this.dims.slice.y = this.phys.y;
		this.dims.slice.z = this.phys.z;

		this.dims.t = this.phys.t;
		this.dims.pixel.x = this.phys.pixel_size[0] === 0 ? 1 : this.phys.pixel_size[0];
		this.dims.pixel.y = this.phys.pixel_size[1] === 0 ? 1 : this.phys.pixel_size[1];
		this.dims.pixel.z = this.phys.pixel_size[2] === 0 ? 1 : this.phys.pixel_size[2];
		if (this.dims.pixel.z < 0.1)
			this.dims.pixel.z = 0.1;
		console.log(this.dims.pixel.z);
		console.log("phys: ", this.phys);

		if (this.dims.t > 1 && this.dims.slice.z == 1) {
			var z = this.dims.t;
			this.dims.t = this.dims.slice.z;
			this.dims.slice.z = z;
			slice = 'slice=,,,,';
			this.dims.timeSeries = true;
		} else {
			slice = 'slice=,,,1';
            if(this.dims.t === 1)
                this.useAnimation = false;
        }
		var dims = '&dims';
		var meta = '&meta';
		var atlas = '&textureatlas';
		var maxTexture = this.getMaxTextureSize();
		var resize = '&resize=' + this.maxTextureSize + ',' + this.maxTextureSize + ',BC,MX';
		var baseUrl = resUniqueUrl + '?' + dims;
		var sliceUrl = resUniqueUrl + '?' + slice + dims;
		var sliceUrlMeta = resUniqueUrl + '?' + slice + meta;
		var fullAtlasUrl = resUniqueUrl + '?' + slice + atlas + dims;
		var resizeAtlasUrl = resUniqueUrl + '?' + slice + atlas + resize + dims;
		this.loadedDimFullAtlas = false;
		this.loadedDimResizeAtlas = false;

		//Ajax request the values pertinent to the volume atlases
		this.fetchDimensions(fullAtlasUrl, 'atlas');
		this.fetchDimensions(resizeAtlasUrl, 'resized');
        //this.fetchHistogram();
	},

	wipeTextureTimeBuffer : function () {
		this.textureTimeBuffer = new Array();
	},

	initUniforms : function () {
		var res = new THREE.Vector2(this.canvas3D.getPixelWidth(), this.canvas3D.getPixelHeight());
		this.sceneVolume.initUniform('iResolution', "v2", res);

		this.sceneVolume.initUniform('BREAK_STEPS', "i", this.setMaxSteps);
		this.sceneVolume.initUniform('FOV', "f", this.canvas3D.fov);

        this.sceneVolume.initUniform('TEX_RES_X', "i", this.xTexSizeRatio * this.dims.slice.x);
		this.sceneVolume.initUniform('TEX_RES_Y', "i", this.yTexSizeRatio * this.dims.slice.y);
		this.sceneVolume.initUniform('ATLAS_X', "i", this.dims.atlas.x / this.dims.slice.x);
		this.sceneVolume.initUniform('ATLAS_Y', "i", this.dims.atlas.y / this.dims.slice.y);
		this.sceneVolume.initUniform('SLICES', "i", this.dims.slice.z);
		this.sceneVolume.initUniform('BLOCK_RES_X', "i", 1);
		this.sceneVolume.initUniform('BLOCK_RES_Y', "i", 1);
		this.sceneVolume.initUniform('BLOCK_RES_Z', "i", 1);
		this.sceneVolume.initUniform('textureAtlas', "t", 1);

		this.sceneVolume.initUniform('STEP', "i", 0);
		this.sceneVolume.initUniform('BACKGROUND_DEPTH', "t", this.screenBuffer);
		this.sceneVolume.initUniform('BACKGROUND_COLOR', "t", this.screenBuffer);

		/*
		var pixels = new Uint8Array([0,0,0, 0,
		50, 20, 2, 40,
		50, 15, 20, 40,
		80, 10, 10, 80,
		50, 10, 1, 80,
		40, 10, 1, 100,
		50,50,50, 200,
		50,50,50, 200,
		]);

		rampTex = new THREE.DataTexture( pixels, 8, 1, THREE.RGBAFormat );
		rampTex.needsUpdate = true;
		this.sceneVolume.initUniform('transfer', "t", rampTex);
		this.sceneVolume.initUniform('TRANSFER_SIZE', "i", 6);
		 */
	},

	onImage : function (resource) {
		//build custom atlas dims here, maybe this can get cuter...

		var textureAtlas = new THREE.ImageUtils.loadTexture('/images/bisque_logo_400.png');
		textureAtlas.generateMipmaps = false;
		textureAtlas.magFilter = THREE.LinearFilter;
		textureAtlas.minFilter = THREE.LinearFilter;
		this.dims = {
			slice : {
				x : 0,
				y : 0,
				z : 0
			},
			atlas : {
				x : 0,
				y : 0,
				z : 1
			},
			atlasResized : {
				x : 0,
				y : 0,
				z : 1
			},
			pixel : {
				x : 0,
				y : 0,
				z : 0
			},
			t : 0
		};

		if (!resource)
			return;
		this.resource = resource;
		if (!this.phys) {
			var phys = new BQImagePhys(this.resource);
			phys.load(callback(this, this.onPhys));
		}

		this.onPartFetch();
	},

	onPhys : function (phys) {
		if (!phys)
			return;
		this.phys = phys;
		this.onPartFetch();
	},

	onPartFetch : function () {
		if (!this.resource || !this.phys)
			return;
		this.initTextures();

		//this.createToolMenu();
		for (var i = 0; (plugin = this.plug_ins[i]); i++)
			plugin.init();
	},

	onerror : function (error) {

		if (this.hasListeners.error)
			this.fireEvent('error', error);
		else {
			console.log('error, bisque service not available.');
			//BQ.ui.error(error.message_short);
			/*
			this.xTexSizeRatio = 1.0;
			this.yTexSizeRatio = 1.0;
			this.initUniforms();
			this.uniforms.TEX_RES_X.value = 1;
			this.uniforms.TEX_RES_Y.value = 1;
			this.uniforms.ATLAS_X.value   = 1;
			this.uniforms.ATLAS_Y.value   = 1;
			this.uniforms.SLICES.value    = 1;

			this.setLoading(false);

			this.canvas3D.initScene(this.uniforms);
			var dataBase0 = new Array();
			dataBase0[0] = null;
			this.uniforms.dataBase0.value = dataBase0;
			this.fireEvent('loaded', this);
			this.textureTimeBuffer = new Array();
			this.textureTimeBuffer[0] = null;
			this.setLoading(false);
			this.canvas3D.doAnimate();
			 */
		}
	},

	constructAtlasUrl : function (opts) {
		var command = [];
		var plugin = undefined;
		for (var i = 0; (plugin = this.plug_ins[i]); i++)
			plugin.addCommand(command, opts);
		return (this.hostName ? this.hostName : '') + '/image_service/image/'
		 + this.resource.resource_uniq + '?' + command.join('&');
	},

/*
	constructAtlasUrlNoJpg : function (opts) {
		var command = [];
		var plugin = undefined;
		for (var i = 0; (plugin = this.plug_ins[i]); i++)
			plugin.addCommand(command, opts);
		return (this.hostName ? this.hostName : '') + '/image_service/image/'
		 + this.resource.resource_uniq + '?' + command.join('&');
	},
*/
	scaleCube : function (inScale) {
		this.sceneVolume.scaleCube(inScale);
		this.fireEvent('scale', this);
	},

	setCurrentTime : function (time) {
		if (this.dims.t == 1)
			return;
		else {
			if (this.currentTime != time) {
				this.currentTime = time;
				this.updateFrameLabel(time);
				this.needs_update();
				this.fireEvent('time', this);
			}

		}
	},

	setCurrentTimeRatio : function (k) {
		if (this.dims.t == 1)
			return;
		else {
			if (this.currentTime != time) {
				var time = Math.floor(this.dims.t * k);
				this.currentTime = time;
				this.updateFrameLabel(time);
				this.needs_update();
				this.fireEvent('time', this);
			}

		}
	},

	doUpdate : function () {
		this.update_needed = undefined;
		// dima: image service is serving bad h264 right now
		//this.viewer.src = this.constructAtlasUrl();
		this.updateTextureUniform();
        this.fetchHistogram();
		//this.sourceH264.setAttribute('src', this.constructMovieUrl('h264'));
		//this.sourceWEBM.setAttribute('src', this.constructMovieUrl('webm'));
	},

    update_image : function (){
        this.fetchHistogram();
    },

	needs_update : function () {
		this.requires_update = undefined;

		if (this.update_needed)
			clearTimeout(this.update_needed);
		this.update_needed = setTimeout(callback(this, this.doUpdate), this.update_delay_ms);
	},

	//----------------------------------------------------------------------
	// Add fadeout to a panel
	//---------------------------------------------------------------------

	addFade : function (Panel) {
		var panel = Panel;
		Panel.usingPanel = false;
		Panel.getEl().dom.addEventListener('mouseenter', function () {
			panel.usingPanel = true;
			panel.getEl().fadeIn({
				opacity : 0.8,
				duration : 200
			});
		}, false);

		Panel.getEl().dom.addEventListener('mouseleave', function () {
			panel.usingPanel = false;
			setTimeout(function () {
				if (!panel.usingPanel) {
					panel.getEl().fadeOut({
						opacity : 0.1,
						duration : 2000
					});
				}
			}, 3000);

		}, false);
	},

	//----------------------------------------------------------------------
	// Animation Panel
	//---------------------------------------------------------------------

	createAnimPanel : function () {
		var thisDom = this.getEl().dom;
		this.animPanel = Ext.create('Ext.panel.Panel', {
				collapsible : false,
				header : false,
				renderTo : thisDom,
				cls : 'bq-volume-playback',
				items : [{
						xtype : 'anim_control',
						panel3D : this,
					}
				],
			});
		this.addFade(this.animPanel);
	},

	//----------------------------------------------------------------------
	// Playback Panel
	//---------------------------------------------------------------------

	createPlaybackPanel : function () {
		var thisDom = this.getEl().dom;
		this.playbackPanel = Ext.create('Ext.panel.Panel', {
				collapsible : true,
				header : false,
				renderTo : thisDom,
				cls : 'bq-volume-playback',
				items : [{
						xtype : 'playback_control',
						panel3D : this
					}
				],
			});
		this.addFade(this.playbackPanel);

	},

	//----------------------------------------------------------------------
	// Tool Panel
	//---------------------------------------------------------------------

	createToolPanel : function () {
		var items = [];

        this.toolPanelButtons = Ext.create('Ext.container.Container',{
            //id: 'toolbar-buttons',
            layout: {
                type: 'table',
                columns: 8
            },
        });

        items.push(this.toolPanelButtons);

		items.push({
			xtype : 'glinfo'
		});

		if (!this.toolPanel) {
			var thisDom = this.getEl().dom;

			this.toolPanel = Ext.create('Ext.panel.Panel', {
					renderTo : thisDom,
					title : 'Settings',
					cls : 'bq-volume-toolbar',
					split : true,
					collapsible : true,
					floatable : true,

					defaults : {
						collapsible : true,
						sceneVolume : this.sceneVolume,
						panel3D : this,
						canvas3D : this.canvas3D,
						layout : {
							type : 'vbox',
							align : 'stretch',
							pack : 'start',
						},
						border : false,
					},
					items : items,
				});
			this.addFade(this.toolPanel);

            this.tools = [
                new ditherTool(this),
                new boxTool(this),
                new gammaTool(this),
                new materialTool(this),];

            if (Ext.isWindows) {
			    if (Ext.isChrome && Ext.chromeVersion >= 37) {
				    this.tools.push(new phongTool(this),
                                    new deepTool(this),
                                    new lightTool(this));
			    }
		    } else {
			    this.tools.push(new phongTool(this),
                                new deepTool(this),
                                new lightTool(this));
		    }

            this.tools.push(new transferTool(this),
                            new gObjectTool(this),
                            new clipTool(this),
                            new VolScaleBarTool(this),
                            new VolAxisTool(this));

            this.tools.forEach(function(e,i,a){
                e.init();
                e.addButton();
		        e.addControls();
            });

		}

	},
    //----------------------
	// Zoom Slider
	//---------------------------------------------------------------------

	createZoomSlider : function () {
		if(this.zoomSlider) return;
        var me = this;
		var thisDom = this.getEl().dom;
        this.zoomSlider = Ext.create('Ext.slider.Single', {
				renderTo : thisDom,
				//id : 'zoom-slider',
				cls : 'bq-zoom-slider',
				hideLabel : true,
				minValue : 0,
				maxValue : 100,
				increment : 1,
				height : 300,
				x : 10,
				y : 10,
				style : {
					position : 'absolute',
					'z-index' : 9999999
				},
				layout : {
					type : 'vbox',
					align : 'left',
					clearInnerCtOnLayout : true,
					bindToOwnerCtContainer : false
				},
				vertical : true,
				value : 0,
				animation : false,
				listeners : {
					change : function (slider, value) {

						if (!this.canvas3D.zooming) {
							var scale = 10.0 * (1.0 - value / slider.maxValue);
							scale = scale < 0.25 ? 0.25 : scale;
                            console.log(me.canvas3D.controls);
							me.canvas3D.controls.enabled = false;
							me.canvas3D.controls.setRadius(scale);
                           	//me.canvas3D.controls.enabled = false;;
							//me.canvas3D.controls.noPan = true;
							this.rerender();
						}
					},
					changecomplete : function (slider, value) {
						me.canvas3D.controls.enabled = true;
						me.canvas3D.controls.update();
					},
					scope : me,
				}
			});

		thisDom.addEventListener('mousewheel', function () {
			var distFromCenter = me.canvas3D.camera.position.length();
			var newSliderVal = Math.floor((10.0 - distFromCenter) * 10.0);
			var curSliderVal = me.zoomSlider.getValue(0);
			if (newSliderVal != curSliderVal) {
				me.zoomSlider.setValue(newSliderVal);
			}
		}, false);

		this.zoomSlider.setValue(50);
		this.canvas3D.controls.noRoate = false;
		this.canvas3D.controls.noPan = false;
		this.addFade(this.zoomSlider);
	},
	//----------------------------------------------------------------------
	// tool combo
	//---------------------------------------------------------------------


	createToolMenu : function () {
        var me = this;
	    if (this.toolMenu)return;
        var showAnimPanel = function() {
            if(me.useAnimation == false){
                //this.
                me.playbackPanel.hide();
			    me.animPanel.hide();
                return;
            }

            if(me.animStyle == 1) {
                me.playbackPanel.hide();
			    me.animPanel.show();
            } else {
                me.playbackPanel.show();
			    me.animPanel.hide();
            }
        };

	    var toolMenuRadioHandler = function () {
		    var
            radio1 = this.toolMenu.queryById('toolRadio1'),
		    radio2 = this.toolMenu.queryById('toolRadio2');
		    if (radio2.getValue()) {
                me.animStyle = 1;
		    } else {
                me.animStyle = 2;
		    }

            showAnimPanel();
		    return;
	    };

        var menubutton = this.queryById('tool-menu');
		this.toolMenu = Ext.create('Ext.tip.ToolTip', {
			target : menubutton.getEl(),
			anchor : 'top',
			anchorToTarget : true,
			cls : 'bq-volume-menu',
			maxWidth : 460,
			anchorOffset : -10,
			autoHide : false,
			shadow : false,
			closable : true,
			layout : {
				type : 'vbox',
			},

		});

        var radioOpts = Ext.create('Ext.container.Container',{

			defaults : {
				xtype : 'radio',
				width : 200,
				name : 'tools',
				cls : 'toolItem',
                handler : toolMenuRadioHandler,
                scope : this,
            },

            items:[{
				fieldLabel : 'standard player',
				checked : true,
				itemId : 'toolRadio1',
			}, {
				fieldLabel : 'animation player',
				itemId : 'toolRadio2',
			},]
        }).hide();

        var qualityCheck = function(item, checked){
            console.log(item, checked);
            if(checked === false) return;
            if (item.text === 'low'){
                me.maxSteps = 64;
            }
            if (item.text === 'medium'){
                me.maxSteps = 128;
            }
            if (item.text === 'high'){
                me.maxSteps = 256;
            }
            if (item.text === 'ultra'){
                me.maxSteps = 512;
            }
            if (item.text === 'extreme'){
                me.maxSteps = 1024;
            }
            me.shaderConfig.maxSteps = me.maxSteps;
            me.sceneVolume.setConfigurable("default",
                                           "fragment",
                                           me.shaderConfig);
            me.rerender();
        };

        var qualityMenu = Ext.create('Ext.menu.Menu', {
            //id: 'mainMenu',
            style: {
                overflow: 'visible'     // For the Combo popup
            },
            items: [
                '<b class="menu-title">Choose a Theme</b>',
                {
                    text: 'low',
                    checked: true,
                    group: 'theme',
                    checkHandler: qualityCheck
                }, {
                    text: 'medium',
                    checked: false,
                    group: 'theme',
                    checkHandler: qualityCheck
                }, {
                    text: 'high',
                    checked: false,
                    group: 'theme',
                    checkHandler: qualityCheck
                }, {
                    text: 'ultra',
                    checked: false,
                    group: 'theme',
                    checkHandler: qualityCheck
                },{
                    text: 'extreme',
                    checked: false,
                    group: 'theme',
                    checkHandler: qualityCheck
                },

            ]
        });

		this.toolMenu.add([{
			boxLabel : 'settings',
			checked : true,
			width : 200,
			cls : 'toolItem',
			xtype : 'checkbox',
			handler : function (item, checked) {
				if (checked) {
					me.toolPanel.show();
				} else
					me.toolPanel.hide();
			},
		},{
			boxLabel : 'animation',
			checked : this.useAnimation,
			width : 200,
			cls : 'toolItem',
			xtype : 'checkbox',
			handler : function (item, checked) {
				if (checked) {
					radioOpts.show();
                    me.useAnimation = true;
                    showAnimPanel();

				} else{
					radioOpts.hide();
                    me.useAnimation = false;
                    showAnimPanel();

                }
			},
		}, radioOpts, {
            xtype: 'button',
            width : 100,
            text:'rendering quality',
            //iconCls: 'bmenu',  // <-- icon
            menu: qualityMenu  // assign menu by instance
        }]);
        showAnimPanel();

	},

	onToolMenuClick : function (e, btn) {
		e.preventDefault();
		e.stopPropagation();
		if (this.toolMenu.isVisible())
			this.toolMenu.hide();
		else
			this.toolMenu.show();
	},

	//----------------------------------------------------------------------
	// view menu
	//----------------------------------------------------------------------

	createCombo : function (label, items, def, scope, cb, id) {
		var ot
		var options = Ext.create('Ext.data.Store', {
				fields : ['value', 'text'],
				data : items
			});
		var combo = this.menu.add({
				xtype : 'combobox',
				itemId : id ? id : undefined,
				width : 380,
				fieldLabel : label,
				store : options,
				queryMode : 'local',
				displayField : 'text',
				valueField : 'value',
				forceSelection : true,
				editable : false,
				value : def,
				listeners : {
					scope : scope,
					'select' : cb,
				},
			});
		return combo;
	},

	createViewMenu : function () {

		if (!this.menu) {
			var menubutton = this.queryById('button-menu');
			this.menu = Ext.create('Ext.tip.ToolTip', {
					target : menubutton.getEl(),
					anchor : 'top',
					anchorToTarget : true,
					cls : 'bq-volume-menu',
					maxWidth : 460,
					anchorOffset : -10,
					autoHide : false,
					shadow : false,
					closable : true,
					layout : {
						type : 'vbox',
						//align: 'stretch',
					},
					defaults : {
						labelSeparator : '',
						labelWidth : 200,
					},
				});
		}
	},

	onMenuClick : function (e, btn) {
		e.preventDefault();
		e.stopPropagation();
		if (this.menu.isVisible())
			this.menu.hide();
		else
			this.menu.show();
	},

    onFullScreenClick: function (e, btn) {
        e.preventDefault();
        e.stopPropagation();
        this.doFullScreen();
    },

    doFullScreen: function () {
        var maximized = (document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement || document.msFullscreenElement),
        vd = this.getEl().dom,
            has_fs = vd.requestFullscreen || vd.webkitRequestFullscreen || vd.msRequestFullscreen || vd.mozRequestFullScreen;
        if (!has_fs) return;

        if (!maximized) {
            if (vd.requestFullscreen) {
                vd.requestFullscreen();
            } else if (vd.webkitRequestFullscreen) {
                vd.webkitRequestFullscreen();
            } else if (vd.msRequestFullscreen) {
                vd.msRequestFullscreen();
            } else if (vd.mozRequestFullScreen) {
                vd.mozRequestFullScreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            }
        }
    },
});

//--------------------------------------------------------------------------------------
// Dialogue Box
//--------------------------------------------------------------------------------------

Ext.define('BQ.viewer.Volume.Dialog', {
	extend : 'Ext.window.Window',
	alias : 'widget.bq_volume_dialog',
	border : 0,
	layout : 'fit',
	modal : true,
	border : false,
	width : '75%',
	height : '75%',
	buttonAlign : 'center',
	autoScroll : true,
	title : 'volume viewer',

	constructor : function (config) {
		config = config || {};

		Ext.apply(this, {
			title : 'Move for ' + config.resource.name,
			items : [{
					xtype : 'bq_volume_panel',
					hostName : config.hostName,
					resource : config.resource
				}
			],
		}, config);

		this.callParent(arguments);
		this.show();
	},
});

//--------------------------------------------------------------------------------------
// Plug-ins - base
//--------------------------------------------------------------------------------------

function VolumePlugin(volume) {
	this.volume = volume;
};

VolumePlugin.prototype.init = function () {};

VolumePlugin.prototype.addCommand = function (command, pars) {};

VolumePlugin.prototype.changed = function () {
	if (!this.update_check || (this.update_check && this.update_check.checked))
	{
	    this.volume.needs_update();

    }

};

function VolumeSize(player) {
	this.base = VolumePlugin;
	this.base(player);

	this.resolutions = {
		'SD' : {
			w : 720,
			h : 480,
		},
		'HD720' : {
			w : 1280,
			h : 720,
		},
		'HD' : {
			w : 1920,
			h : 1080,
		},
		'4K' : {
			w : 3840,
			h : 2160,
		},
	};
};

function VolumeFormat(volume) {
	this.base = VolumePlugin;
	this.base(volume);
};
VolumeFormat.prototype = new VolumePlugin();

VolumeFormat.prototype.init = function () {};

VolumeFormat.prototype.addCommand = function (command, pars) {
	command.push('format=jpeg');
};

function VolumeTime(volume) {
	this.base = VolumePlugin;
	this.base(volume);
};
VolumeTime.prototype = new VolumePlugin();

VolumeTime.prototype.init = function () {};

VolumeTime.prototype.onTime = function () {

	//var nt = parseInt(this.volume.dims.t);
	//var t = this.volume.getValue();
	var t = this.volume.currentTime;
	this.changed();
};

VolumeTime.prototype.addCommand = function (command, pars) {

	if (this.volume.dims)
		if (this.volume.dims.timeSeries)
			command.push('slice=,,,,');
		else {
			var t = this.volume.currentTime + 1;
			command.push('slice=,,,' + (t > 0 ? t : ''));
		}
};

function VolumeAtlas(volume) {
	this.base = VolumePlugin;
	this.base(volume);
};
VolumeAtlas.prototype = new VolumePlugin();

VolumeAtlas.prototype.init = function () {};

VolumeAtlas.prototype.addCommand = function (command, pars) {
	var maxTexture = this.volume.getMaxTextureSize();
	var resize = '&resize=' + maxTexture + ',' + maxTexture + ',BC,MX';
	command.push('textureatlas&' + resize);
	//command.push('textureatlas&resize=4096,4096,BC,MX');
};

//--------------------------------------------------------------------------------------
// Plug-ins - display
//--------------------------------------------------------------------------------------

function VolumeDisplay(volume) {
	this.base = VolumePlugin;
	this.base(volume);
};

VolumeDisplay.prototype = new VolumePlugin();

VolumeDisplay.prototype.init = function () {
	var p = this.volume.preferences || {};
	this.def = {
		enhancement : p.enhancement || 'd', // values: 'd', 'f', 't', 'e'
		enhancement_8bit : p.enhancement8bit || 'f',
		negative : p.negative || '', // values: '', 'negative'
		fusion : p.fusion || 'm', // values: 'a', 'm'
		rotate : p.rotate || 0, // values: 0, 270, 90, 180
		autoupdate : false,
	};
	if (!this.menu)
		this.createMenu();
};

VolumePlugin.prototype.changed = function () {
	if (!this.update_check || (this.update_check && this.update_check.checked))
		this.volume.needs_update();
	this.volume.wipeTextureTimeBuffer();
    this.volume.setLoading("fetching new texture...");
};

VolumeDisplay.prototype.addCommand = function (command, pars) {

	if (!this.menu)
		return;
	command.push('depth=8,' + this.combo_enhancement.getValue());

	var fusion = '';
	for (var i = 0; i < this.channel_colors.length; i++) {
		fusion += this.channel_colors[i].getRed() + ',';
		fusion += this.channel_colors[i].getGreen() + ',';
		fusion += this.channel_colors[i].getBlue() + ';';
	}
	fusion += ':' + this.combo_fusion.getValue();
	command.push('fuse=' + fusion);

	var ang = this.combo_rotation.getValue();
	if (ang && ang !== '' && ang !== 0)
		command.push('rotate=' + ang);

	if (this.combo_negative.getValue()) {
		command.push(this.combo_negative.getValue());
	}
};

VolumeDisplay.prototype.createMenu = function () {
	if (this.menu)
		return;

	this.menu = this.volume.menu;

	this.createChannelMap();

	var enhancement = this.volume.phys && parseInt(this.volume.phys.pixel_depth) === 8 ? this.def.enhancement_8bit : this.def.enhancement;
	this.menu.add({
		xtype : 'displayfield',
		fieldLabel : 'View',
		cls : 'heading',
	});

	this.combo_fusion = this.volume.createCombo('Fusion', [{
					"value" : "a",
					"text" : "Average"
				}, {
					"value" : "m",
					"text" : "Maximum"
				},
			], this.def.fusion, this, this.changed);

	this.combo_enhancement = this.volume.createCombo('Enhancement', [{
					"value" : "d",
					"text" : "Data range"
				}, {
					"value" : "f",
					"text" : "Full range"
				}, {
					"value" : "t",
					"text" : "Data + tolerance"
				}, {
					"value" : "e",
					"text" : "Equalized"
				}
			], enhancement, this, this.changed);

	this.combo_negative = this.volume.createCombo('Negative', [{
					"value" : "",
					"text" : "No"
				}, {
					"value" : "negative",
					"text" : "Negative"
				},
			], this.def.negative, this, this.changed);

	this.combo_rotation = this.volume.createCombo('Rotation', [{
					"value" : 0,
					"text" : "No"
				}, {
					"value" : 90,
					"text" : "Right 90deg"
				}, {
					"value" : -90,
					"text" : "Left 90deg"
				}, {
					"value" : 180,
					"text" : "180deg"
				},
			], this.def.rotate, this, this.changed);
};

VolumeDisplay.prototype.createChannelMap = function () {
	var channel_count = parseInt(this.volume.phys.ch);
	var phys = this.volume.phys;

	this.menu.add({
		xtype : 'displayfield',
		fieldLabel : 'Channels',
		cls : 'heading',
	});

	this.channel_colors = phys.channel_colors;
	for (var ch = 0; ch < channel_count; ch++) {
		this.menu.add({
			xtype : 'colorfield',
			fieldLabel : '' + phys.channel_names[ch],
			name : 'channel_color_' + ch,
			channel : ch,
			value : this.channel_colors[ch].toString().replace('#', ''),
			listeners : {
				scope : this,
				change : function (field, value) {
					this.channel_colors[field.channel] = Ext.draw.Color.fromString('#' + value);
					this.changed();
				},
			},
		});
	}
};