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
    'Ext.Window',
    'BQ.viewer.Volume.ThreejsPanel',
    'Ext.tip.QuickTipManager',
    'Ext.menu.*',
    'Ext.form.field.ComboBox',
    'Ext.layout.container.Table',
    'Ext.layout.container.Accordion',
    'Ext.container.ButtonGroup',
]);



Ext.define('BQ.viewer.Volume.volumeScene', {
    mixins: {
        observable: 'Ext.util.Observable'
    },

    alias: 'widget.volumeScene',

    constructor: function (config) {
        // The Observable constructor copies all of the properties of `config` on
        // to `this` using Ext.apply. Further, the `listeners` property is
        // processed to add listeners.
        //
        this.mixins.observable.constructor.call(this, config);

        this.addEvents(
            'fired',
            'quit'
        );

        this.shaders   = {};
        this.materials = {};
        this.uniforms  = {};

        this.scene = new THREE.Scene();
	    var material = new THREE.MeshBasicMaterial( {color: 0xffff00} );

        this.cube = new THREE.CubeGeometry(1.0, 1.0, 1.0 );
        this.cubeMesh = new THREE.Mesh(this.cube, this.material);
        this.scene.add(this.cubeMesh);


        this.light = new THREE.PointLight(  0xFFFFFF, 1, 100 );
        this.scene.add(this.light);
        this.canvas3D.scene = this.scene;

        this.canvas3D.scene = this.scene;

        this.canvas3D.plane = this.plane;
        this.setMaxSteps = 32;
    },

    initComponent : function() {
    },

    setUniform : function(name, value, reset){
        if(typeof(reset) === 'undefine') reset = true;
        this.uniforms[name].value = value;
        if(name != 'setMaxSteps')
            this.setMaxSteps = 32;

        this.canvas3D.rerender();
    },

    initUniform : function(name, type, value){
        this.uniforms[name] = {type: type, value: value};
        this.setMaxSteps = 32;
        this.canvas3D.rerender();
    },

    getMaterial : function(index){
        return this.materials[index];
    },

    scaleCube : function(inScale){
        this.setUniform('BOX_SIZE',inScale);
	    var cube = this.cube;
	    var bMax = cube.vertices[0];
        var scale = inScale.clone();
        scale.divide(bMax);
        cube.dynamic = true;
        cube.verticesNeedUpdate = true;
        for (var i = 0; i < cube.vertices.length; i++) {
		    var corner = cube.vertices[i];
		    cube.vertices[i].multiplyVectors(corner, scale);
        }
        this.canvas3D.rerender();
    },

    constructMaterial : function(material){

        if(material.built === true) return true;

        var vertexKey   = material.vertexId;
        var fragmentKey = material.fragmentId;
        if(!this.shaders[vertexKey]) return false;
        if(!this.shaders[fragmentKey]) return false;

        if(material.threeShader.vertexShader === "")
            material.threeShader.vertexShader = this.shaders[vertexKey];
        if(material.threeShader.fragmentShader === "")
            material.threeShader.fragmentShader = this.shaders[fragmentKey];

        if(material.threeShader.vertexShader    != ""  &&
           material.threeShader.fragmentShader != ""){
            material.built = true;
            return true;
        }
        else
            return false;
    },

    updateMaterials : function(){
        var me = this;
        for(var prop in this.materials){
            this.constructMaterial(this.materials[prop]);
        }
    },

    fetchFragments : function(url, storeId, manip){
        var me = this;
        var manipulate = manip;
        var id = storeId;
        Ext.Ajax.request({
            url: url,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    BQ.ui.error(response.responseText);
                else{
                    var fetchedText = response.responseText;
                    me.shaders[id] = fetchedText;
                    if(manipulate){
                        var newText = manipulate(fetchedText);
                        me.shaders[id] = newText;
                    }
                    me.updateMaterials();
                }
            },
            scope: this,
            disableCaching: false,
            listeners: {
                scope: this,
                beforerequest   : function() { this.setLoading('Loading images...'); },
                requestcomplete : function() { this.setLoading(false); },
                requestexception: function() { this.setLoading(false); },
            },
        });
    },

    initFragment : function(url, id, manipulate){

        if(!this.shaders[url]){
            this.shaders[url] = ''; //placeholder so we don't fetch this fragment many times
            this.fetchFragments(url,id,manipulate);
        }
        else{
            if(manipulate){
                var shader = this.shaders[url];
                var newText = manipulate(shader);
                this.shaders[id] = newText;
                this.updateMaterials();
            }
        }
    },

    initMaterial : function( config ){
        var name = config.name;
        var vertUrl = config.vertConfig.url;
        var fragUrl = config.fragConfig.url;
        var vertId =  vertUrl;
        var fragId =  fragUrl;
        var uniforms = this.uniforms;
        if(config.vertConfig.id) vertId = config.vertConfig.id;
        if(config.fragConfig.id) fragId = config.fragConfig.id;
        if(config.uniforms) uniforms = config.uniforms;

        var threeMaterial = new THREE.ShaderMaterial({
            uniforms : this.uniforms,
            vertexShader : "",
            fragmentShader : ""
        });

        var newMaterial = {name: name,
                           vertexId:   vertId,
                           fragmentId: fragId,
                           built: false,
                           threeShader: threeMaterial,
                           buildFunc:this.defaultBuildFunc ,};

        this.materials[name] = newMaterial;
        this.initFragment(vertUrl, vertId, config.vertConfig.manipulate);
        this.initFragment(fragUrl, fragId, config.fragConfig.manipulate);
    },

    loadMaterial : function(name){
        this.cubeMesh.material = this.materials[name].threeShader;
        this.canvas3D.rerender();
    }

});

Ext.define('BQ.viewer.Volume.renderProgress', {
    extend: 'Ext.ProgressBar',

    alias: 'widget.renderProgress',
    border: false,
    requires: ['Ext.window.MessageBox'],

    initComponent : function(){
    },

    afterFirstLayout : function(){
        ////////////////////
        this.callParent();
        this.doUpdate();
    },

    doUpdate: function(){
        var renderProgress = this.setMaxSteps/512;
        this.updateProgress(renderProgress);
        var me = this;
        requestAnimationFrame(function() {me.doUpdate()});
    },
});


Ext.define('BQ.viewer.Volume.Panel', {
    extend : 'Ext.panel.Panel',
    alias: 'widget.bq_volume_panel',
    cls : 'bq-three-container',

    border: 0,
    layout: 'fit',
    border : false,
    buttonAlign: 'center',
    autoScroll: true,

    constructor : function(config) {
        config = config || {};
        this.canvas3D = Ext.create('BQ.viewer.Volume.ThreejsPanel',{
            itemId: 'canvas3D',
            onAnimate : callback(this, this.onAnimate),
            resource: config.resource,
        });
        //var panel3D = this.panel3D;
        this.sceneVolume = new BQ.viewer.Volume.volumeScene({
            canvas3D: this.canvas3D
        });

        //this.sceneVolume.initFragment("/src/shaders/rayCast.vs", null, 10);
        /*
        this.sceneVolume.initMaterial({ name: 'test',
                                        vertUrl: "/src/shaders/rayCast.vs",
                                        fragUrl: "/src/shaders/rayCastBlocks.fs"});
        */
        this.sceneVolume.initMaterial({
            name:    'diffuse',
            vertConfig:{
                url: "/js/volume/shaders/rayCast.vs"
            },
            fragConfig: {
                url: "/js/volume/shaders/rayCastBlocks.fs",
            }
        });

        this.addEvents({
            'loaded' : true,
            'changed' : true,
        });

        Ext.apply(this, {
            bbar: {
                xtype: 'renderProgress',
                panel3D:this
            },
            items: [ this.canvas3D ],
        }, config);

        this.plug_ins = [new VolumeTime(this), new VolumeAtlas(this),
                         new VolumeDisplay(this), new VolumeFormat(this)];
        this.callParent(arguments);
        this.show();
    },

    onresize : function() {
        if (this.sceneVolume.uniforms['iResolution']) {
            var newRes =
                new THREE.Vector2(this.canvas3D.getWidth(), this.canvas3D.getHeight());
            this.sceneVolume.setUniform('iResolution', newRes);
            this.rerender();
        }
    },

    onAnimate : function(){
        if(this.canvas3D.mousedown)
            this.sceneVolume.setMaxSteps = 32;

        if(this.sceneVolume.setMaxSteps < 512){
            this.sceneVolume.setMaxSteps *= 1.5;
            this.sceneVolume.setUniform('setMaxSteps',
                                        this.sceneVolume.setMaxSteps, false);
        }
        else {
            this.sceneVolume.setMaxSteps = 512;
            this.canvas3D.needs_render = false;
        }

    },

    initComponent : function() {
	    this.addListener('resize', this.onresize, this);

        this.preMultiplyAlpha = false;
        this.currentTime = 0;

        this.callParent();
    },

    afterFirstLayout : function() {
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

	    var me = this;
	    this.on({
	        loaded: function(){
		        console.log("creating");
		        me.createAnimPanel();
		        me.createPlaybackPanel();
		        me.createToolPanel();
		        me.createZoomSlider();
		        me.createToolMenu();
		        //this.setLoading(false);
	        },
	        scope: me,
	    });

        this.callParent();
    },

    ajaxDimRequest : function(url, type) {
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
                    if (type == 'slice' || type == 'atlas' || type == 'resized') {
                        var xRes = evaluateXPath(xmlDoc, "//tag[@name='image_num_x']/@value");
                        var yRes = evaluateXPath(xmlDoc, "//tag[@name='image_num_y']/@value");
			            console.log("xRes: ", xRes);
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

                        this.xTexSizeRatio = this.dims.atlasResized.x/this.dims.atlas.x;
                        this.yTexSizeRatio = this.dims.atlasResized.y/this.dims.atlas.y;
                        this.sceneVolume.setUniform('TEX_RES_X', this.xTexSizeRatio * this.dims.slice.x);
                        this.sceneVolume.setUniform('TEX_RES_Y', this.yTexSizeRatio * this.dims.slice.y);

                        this.sceneVolume.setUniform('ATLAS_X', this.dims.atlas.x / this.dims.slice.x);
                        this.sceneVolume.setUniform('ATLAS_Y', this.dims.atlas.y / this.dims.slice.y);
                        this.sceneVolume.setUniform('SLICES', this.dims.slice.z);

                        this.setLoading(false);
                        this.fireEvent('loaded', this);
			            this.textureTimeBuffer = new Array();
			            this.updateTextureUniform();
                        this.sceneVolume.loadMaterial('diffuse');
                        console.log('uniforms: ',this.sceneVolume.uniforms);
                        this.canvas3D.doAnimate();
                    }
                }
            },
        });
    },

    //----------------------------------------------------------------------
    // texture loading
    //----------------------------------------------------------------------
    updateTextureUniform : function() {
        if (!this.textureTimeBuffer[this.currentTime]) {
            var dataBase0 = new Array();
	        console.log("texture atlas: ", this.constructAtlasUrl());
	        dataBase0[0] = new THREE.ImageUtils.loadTexture(this.constructAtlasUrl());
            dataBase0[0].generateMipmaps = false;
            dataBase0[0].magFilter = THREE.LinearFilter;
            dataBase0[0].minFilter = THREE.LinearFilter;

            this.textureTimeBuffer[this.currentTime] = dataBase0;
            //this.uniforms.dataBase0.value = dataBase0;
        }
        this.sceneVolume.setUniform('dataBase0',this.textureTimeBuffer[this.currentTime]);
	    this.update = true;
    },

    initTextures : function() {

        this.initUniforms();

	    var resUniqueUrl = (this.hostName ? this.hostName : '') + '/image_service/image/' + this.resource.resource_uniq;

        //var resUniqueUrl = 'http://vidi.ece.ucsb.edu:9090/image_service/image/' +
	    //    this.resource.resource_uniq;
	    var slice;
	    console.log("init tex dims: ", this.dims);
	    console.log("hostname: ", this.hostName);
	    if(this.dims.t > 1 && this.dims.slice.z == 1){
	        var z = this.dims.t;
	        this.dims.t = this.dims.slice.z;
	        this.dims.slice.z = z;
            slice = 'slice=,,,,';
	        this.dims.timeSeries = true;
	        console.log("slice: ", slice);
	    }
	    else
	        slice = 'slice=,,,1';
        var dims = '&dims';
        var meta = '&meta';
        var atlas = '&textureatlas';
        var baseUrl = resUniqueUrl + '?' + dims;
        var sliceUrl = resUniqueUrl + '?' + slice + dims;
        var sliceUrlMeta = resUniqueUrl + '?' + slice + meta;
        var fullAtlasUrl = resUniqueUrl + '?' + slice + atlas + dims;
        var resizeAtlasUrl = resUniqueUrl + '?' + slice + atlas + '&resize=8192,8192,BC,MX' + dims;
        this.loadedDimFullAtlas = false;
        this.loadedDimResizeAtlas = false;

        //Ajax request the values pertinent to the volume atlases
        this.ajaxDimRequest(fullAtlasUrl, 'atlas');
        this.ajaxDimRequest(resizeAtlasUrl, 'resized');
    },

    wipeTextureTimeBuffer : function() {
        this.textureTimeBuffer = new Array();
    },


    initUniforms : function() {
        var res = new THREE.Vector2(this.canvas3D.getWidth(), this.canvas3D.getHeight());
        this.sceneVolume.initUniform('iResolution', "v2", res);
        this.sceneVolume.initUniform('setMaxSteps', "i", this.setMaxSteps);
        this.sceneVolume.initUniform('TEX_RES_X', "i", 1);
        this.sceneVolume.initUniform('TEX_RES_Y', "i", 1);
        this.sceneVolume.initUniform('ATLAS_X', "i", 1);
        this.sceneVolume.initUniform('ATLAS_Y', "i", 1);
        this.sceneVolume.initUniform('SLICES', "i", 1);
        this.sceneVolume.initUniform('RES_X', "i", 1);
        this.sceneVolume.initUniform('RES_Y', "i", 1);
        this.sceneVolume.initUniform('RES_Z', "i", 1);
        this.sceneVolume.initUniform('dataBase0', "tv", 1);
    },


    onImage : function(resource) {
	    //build custom atlas dims here, maybe this can get cuter...
	    var dataBase0 = new Array();

        dataBase0[0] = new THREE.ImageUtils.loadTexture('/images/bisque_logo_400.png');
        //console.log(dataBase0[0]);
        dataBase0[0].generateMipmaps  = false;
        dataBase0[0].magFilter        = THREE.LinearFilter;
        dataBase0[0].minFilter        = THREE.LinearFilter;
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

    onPhys : function(phys) {
        if (!phys)
            return;
        this.phys = phys;
	    //a lot of information is already loaded by the phys object:
        this.dims.slice.x = this.phys.x;
        this.dims.slice.y = this.phys.y;
        this.dims.slice.z = this.phys.z;
        this.dims.t = this.phys.t;
	    this.initFrameLabel();
        this.dims.pixel.x = this.phys.pixel_size[0] === 0 ? 1 : this.phys.pixel_size[0];
        this.dims.pixel.y = this.phys.pixel_size[1] === 0 ? 1 : this.phys.pixel_size[1];
        this.dims.pixel.z = this.phys.pixel_size[2] === 0 ? 1 : this.phys.pixel_size[2];

        this.onPartFetch();
    },

    onPartFetch : function() {
        if (!this.resource || !this.phys)
            return;
	    console.log(this.hostName);
        this.initTextures();
	    this.createViewMenu();
        for (var i = 0; ( plugin = this.plug_ins[i]); i++)
            plugin.init();
    },

    onerror : function(error) {

        if (this.hasListeners.error)
            this.fireEvent('error', error);
        else
	    {
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

    constructAtlasUrl : function(opts) {
        var command = [];
        var plugin = undefined;
        for (var i = 0; ( plugin = this.plug_ins[i]); i++)
            plugin.addCommand(command, opts);
        return (this.hostName ? this.hostName : '') + '/image_service/image/'
	        + this.resource.resource_uniq + '?' + command.join('&');
    },

    updateFrameLabel: function(frame){
	    if(this.frameLabel)
	        this.frameLabel.innerHTML = "frame: "+frame+"/"+this.dims.t;
    },

    initFrameLabel : function (){
	    this.frameLabel= document.createElement('span');
	    this.frameLabel.className = "framelabel"
	    this.updateFrameLabel(0);
	    this.getEl().dom.appendChild(this.frameLabel);
    },

    setCurrentTime : function(time){
	    if(this.dims.t == 1) return;
	    else{
	        if(this.currentTime != time){
		        this.currentTime = time;
		        this.updateFrameLabel(time);
		        this.needs_update();
	        }

	    }
    },

    setCurrentTimeRatio : function(k){
	    if(this.dims.t == 1) return;
	    else{
	        if(this.currentTime != time){
		        var time = Math.floor(this.dims.t*k);
		        this.currentTime = time;
		        this.updateFrameLabel(time);
		        this.needs_update();
	        }

	    }
    },

    doUpdate : function() {
        this.update_needed = undefined;
        // dima: image service is serving bad h264 right now
        //this.viewer.src = this.constructAtlasUrl();
        this.updateTextureUniform();
        //this.sourceH264.setAttribute('src', this.constructMovieUrl('h264'));
        //this.sourceWEBM.setAttribute('src', this.constructMovieUrl('webm'));
    },

    needs_update : function() {
        this.requires_update = undefined;

        if (this.update_needed)
            clearTimeout(this.update_needed);
        this.update_needed = setTimeout(callback(this, this.doUpdate), this.update_delay_ms);
    },

    rerender : function() {
        this.canvas3D.rerender();
	    this.sceneVolume.setMaxSteps = 32;
    },

    //----------------------------------------------------------------------
    // Add fadeout to a panel
    //---------------------------------------------------------------------

    addFade : function(Panel){
	    var panel = Panel;
	    Panel.usingPanel = false;
	    Panel.getEl().dom.addEventListener('mouseenter', function() {
	        panel.usingPanel = true;
	        panel.getEl().fadeIn({
		        opacity: 0.8,
		        duration : 200
	        });
        }, false);

	    Panel.getEl().dom.addEventListener('mouseleave', function() {
	        panel.usingPanel = false;
	        setTimeout(function() {
		        if(!panel.usingPanel){
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

    createAnimPanel : function(){
	    var thisDom = this.getEl().dom;
	    this.animPanel = Ext.create('Ext.panel.Panel',{
	        collapsible: false,
	        header:      false,
	        renderTo: thisDom,
	        cls: 'bq-volume-playback',
	        items: [{
		        xtype: 'anim_control',
		        panel3D: this,
	        }],
	    });
	    this.addFade(this.animPanel);
    },

    //----------------------------------------------------------------------
    // Playback Panel
    //---------------------------------------------------------------------

    createPlaybackPanel : function(){
	    var thisDom = this.getEl().dom;
	    this.playbackPanel = Ext.create('Ext.panel.Panel',{
	        collapsible: true,
	        header: false,
	        renderTo: thisDom,
	        cls: 'bq-volume-playback',
	        items: [{
		        xtype: 'playback_control',
		        panel3D: this
	        }],
	    });
	    this.addFade(this.playbackPanel);
	    this.playbackPanel.hide();
    },

    //----------------------------------------------------------------------
    // Tool Panel
    //---------------------------------------------------------------------

    createToolPanel : function(){
	    if(!this.toolPanel){
            console.log("dims: ", this.dims);
	        var thisDom = this.getEl().dom;
	        this.toolPanel = Ext.create('Ext.panel.Panel',{
		        renderTo: thisDom,
		        title: 'Settings',
		        cls: 'bq-volume-toolbar',
		        split: true,
		        collapsible: true,
		        floatable: true,

		        defaults: {
		            collapsible: true,
		            sceneVolume: this.sceneVolume,
                    layout: {
	                    type: 'vbox',
	                    align : 'stretch',
	                    pack  : 'start',
                    },
                    border: false,
		        },
		        items:[
		            {
			            xtype: 'general',
                        dims: this.dims,
		            },{
			            xtype: 'material',
		            },{
			            xtype: 'clip'
		            },{
			            xtype: 'gamma',
                        panel3D: this,
		            },{
			            xtype: 'lighting',
		            },{
			            xtype: 'lightControl',
                        canvas3D: this.canvas3D,
		            },{
			            xtype: 'glinfo',
                        canvas3D: this.canvas3D,
		            },]
	        });
	        this.addFade(this.toolPanel);
	    }

    },

    //----------------------------------------------------------------------
    // Zoom Slider
    //---------------------------------------------------------------------

    createZoomSlider : function(){
	    var me = this;
	    var thisDom = this.getEl().dom;
        this.zoomSlider = Ext.create('Ext.slider.Single', {
            renderTo : thisDom,
            id : 'zoom slider',
            hideLabel : true,
            minValue : 0,
            maxValue : 100,
            increment : 1,
            height : 125,
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
                change : function(slider, value) {

                    if(!this.canvas3D.zooming){

			            var scale = 10.0 * (1.0 - value / slider.maxValue);
			            scale = scale < 0.25 ? 0.25 : scale;
			            me.canvas3D.controls.enabled = false;
                        me.canvas3D.controls.setRadius(scale);
			            //me.canvas3D.controls.enabled = false;;
			            //me.canvas3D.controls.noPan = true;
			            this.rerender();

                    }
		        },
                changecomplete : function(slider, value) {
                    me.canvas3D.controls.enabled = true;
                    me.canvas3D.controls.update();
                },
                scope : me,
            }
        });

	    thisDom.addEventListener('mousewheel', function() {
	        var distFromCenter = me.canvas3D.camera.position.length();
            var newSliderVal = Math.floor((10.0 - distFromCenter) * 10.0);
            var curSliderVal = me.zoomSlider.getValue(0);
	        if (newSliderVal !=curSliderVal) {
		        me.zoomSlider.setValue(newSliderVal);
	        }
        }, false);

        this.zoomSlider.setValue(50);
        this.canvas3D.controls.noRotate = false;
        this.canvas3D.controls.noPan = false;
	    this.addFade(this.zoomSlider);
    },
    //----------------------------------------------------------------------
    // tool combo
    //---------------------------------------------------------------------
    createToolMenu : function(){
	    var me = this;
	    var thisDom = this.getEl().dom;
	    this.toolMenu = Ext.create('Ext.menu.Menu', {
	        margin: '0 0 10 0',
	        //renderTo: thisDom,
	        floating: true,  // usually you want this set to True (default)
	        items: [{
		        text: 'settings',
		        checked: true,
		        checkHandler: function(item, checked){
		            if(checked){
			            me.toolPanel.show();
		            }
		            else
			            me.toolPanel.hide();
		        },
	        },{
		        text: 'standard player',
		        checked: false,
		        checkHandler: function(item, checked){
		            var itemOther = me.toolMenu.items.items[2];
		            if(checked){
			            me.playbackPanel.show();
			            me.animPanel.hide();
			            itemOther.setChecked(false);
		            }
		            else
			            me.playbackPanel.hide()
		        }
	        },{
		        text: 'animation player',
		        checked: true,
		        checkHandler: function(item, checked){
		            var itemOther = me.toolMenu.items.items[1];
		            if(checked){
			            me.animPanel.show();
			            me.playbackPanel.hide();
			            itemOther.setChecked(false);
		            }
		            else
			            me.animPanel.hide()
		        }
	        }]
	    });

	    this.toolMenuButton = Ext.create('Ext.panel.Panel', {
	        cls: 'bq-volume-toolbar-menu',
	        renderTo: thisDom,
	        layout: {
		        type: 'vbox',
		        align : 'stretch',
		        //pack  : 'start',
	        },
	        items:[{
		        xtype: 'button',
		        text:'toolbars',
		        menu: this.toolMenu,
	        }]
	    });
	    console.log('tool menu: ', this.toolMenuButton);
	    console.log(this.toolMenu);
    },

    //----------------------------------------------------------------------
    // view menu
    //----------------------------------------------------------------------

    createCombo : function(label, items, def, scope, cb, id) {
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

    createViewMenu : function() {
        if (!this.menubutton) {
            this.menubutton = document.createElement('span');
            // temp fix to work similar to panojs3, will be updated to media queries
            if (isClientTouch())
                this.menubutton.className = 'viewoptions touch';
            else if (isClientPhone())
                this.menubutton.className = 'viewoptions phone';
            else
                this.menubutton.className = 'viewoptions';
            this.getEl().dom.appendChild(this.menubutton);
        }

        if (!this.menu) {
            this.menu = Ext.create('Ext.tip.ToolTip', {
                target : this.menubutton,
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
            var el = Ext.get(this.menubutton);
            el.on('click', this.onMenuClick, this);
        }
    },

    onMenuClick : function(e, btn) {
        e.preventDefault();
        e.stopPropagation();
        if (this.menu.isVisible())
            this.menu.hide();
        else
            this.menu.show();
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

    constructor : function(config) {
        config = config || {};

        Ext.apply(this, {
            title : 'Movie for ' + config.resource.name,
            items : [{
                xtype : 'bq_volume_panel',
		        hostName: config.hostName,
                resource : config.resource
            }],
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

VolumePlugin.prototype.init = function() {
};

VolumePlugin.prototype.addCommand = function(command, pars) {
};

VolumePlugin.prototype.changed = function() {
    if (!this.update_check || (this.update_check && this.update_check.checked))
        this.volume.needs_update();
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

VolumeSize.prototype = new VolumePlugin();

VolumeSize.prototype.init = function() {
    var p = this.player.preferences || {};
    this.def = {
        videoResolution : p.videoResolution || 'HD', // values: 'SD', 'HD720', 'HD', '4K'
    };
    if (!this.menu)
        this.createMenu();
};

VolumeSize.prototype.addCommand = function(command, pars) {
    var r = this.resolutions[this.combo_resolution.getValue()];
    command.push('resize=' + r.w + ',' + r.h + ',BC,MX');
};

VolumeSize.prototype.createMenu = function() {
    if (this.menu)
        return;
    this.menu = this.player.menu;

    this.menu.add({
        xtype : 'displayfield',
        fieldLabel : 'Video',
        cls : 'heading',
    });
    this.combo_resolution = this.player.createCombo('Video Resolution', [{
        "value" : "SD",
        "text" : "SD (720x480)"
    }, {
        "value" : "HD720",
        "text" : "HD 720p (1280x720)"
    }, {
        "value" : "HD",
        "text" : "HD 1080p (1920x1080)"
    }, {
        "value" : "4K",
        "text" : "4K (3840x2160)"
    }], this.def.videoResolution, this, this.changed, 'combo_resolution');

};

function VolumeFormat(volume) {
    this.base = VolumePlugin;
    this.base(volume);
};
VolumeFormat.prototype = new VolumePlugin();

VolumeFormat.prototype.init = function() {
};

VolumeFormat.prototype.addCommand = function(command, pars) {
    command.push('format=jpeg');
};

function VolumeTime(volume) {
    this.base = VolumePlugin;
    this.base(volume);
};
VolumeTime.prototype = new VolumePlugin();

VolumeTime.prototype.init = function() {
};

VolumeTime.prototype.onTime = function() {

    //var nt = parseInt(this.volume.dims.t);
    //var t = this.volume.getValue();
    var t = this.volume.currentTime;
    this.changed();
};

VolumeTime.prototype.addCommand = function(command, pars) {
    if (this.volume.dims)
	    if(this.volume.dims.timeSeries)
	        command.push('slice=,,,,');
    else{
	    var t = this.volume.currentTime + 1;
	    command.push('slice=,,,' + (t > 0 ? t : ''));
    }
};

function VolumeAtlas(volume) {
    this.base = VolumePlugin;
    this.base(volume);
};
VolumeAtlas.prototype = new VolumePlugin();

VolumeAtlas.prototype.init = function() {
};

VolumeAtlas.prototype.addCommand = function(command, pars) {
    command.push('textureatlas&resize=8192,8192,BC,MX');
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

VolumeDisplay.prototype.init = function() {
    console.log("plug init: ", this.volume);
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

VolumePlugin.prototype.changed = function() {
    if (!this.update_check || (this.update_check && this.update_check.checked))
        this.volume.needs_update();
    this.volume.wipeTextureTimeBuffer();
};

VolumeDisplay.prototype.addCommand = function (command, pars) {
    command.push ('remap=display');
    if (!this.menu) return;

    command.push ('depth=8,' + this.combo_enhancement.getValue());

    var b = this.menu.queryById('slider_brightness').getValue();
    var c = this.menu.queryById('slider_contrast').getValue();
    if (b!==0 || c!==0)
        command.push('brightnesscontrast='+b+','+c);

    var fusion='';
    for (var i=0; i<this.channel_colors.length; i++) {
        fusion += this.channel_colors[i].getRed() + ',';
        fusion += this.channel_colors[i].getGreen() + ',';
        fusion += this.channel_colors[i].getBlue() + ';';
    }
    fusion += ':'+this.combo_fusion.getValue();
    command.push('fuse='+fusion);

    var ang = this.combo_rotation.getValue();
    if (ang && ang!==''&& ang!==0)
        command.push ('rotate=' + ang);

    if (this.combo_negative.getValue()) {
        command.push(this.combo_negative.getValue());
    }
};

VolumeDisplay.prototype.createMenu = function () {
    if (this.menu) return;

    this.menu = this.volume.menu;

    this.createChannelMap( );

    var enhancement = this.volume.phys && parseInt(this.volume.phys.pixel_depth)===8 ? this.def.enhancement_8bit : this.def.enhancement;
    this.menu.add({
        xtype: 'displayfield',
        fieldLabel: 'View',
        cls: 'heading',
    });

    this.menu.add({
        xtype: 'slider',
        itemId: 'slider_brightness',
        fieldLabel: 'Brightness',
        width: 400,
        value: 0,
        increment: 1,
        minValue: -100,
        maxValue: 100,
        listeners: {
            scope: this,
            change: this.changed,
        },
    });

    this.menu.add({
        xtype: 'slider',
        itemId: 'slider_contrast',
        fieldLabel: 'Contrast',
        width: 400,
        value: 0,
        increment: 1,
        minValue: -100,
        maxValue: 100,
        zeroBasedSnapping: true,
        listeners: {
            scope: this,
            change: this.changed,
        },
    });

    this.combo_fusion = this.volume.createCombo( 'Fusion', [
        {"value":"a", "text":"Average"},
        {"value":"m", "text":"Maximum"},
    ], this.def.fusion, this, this.changed);

    this.combo_enhancement = this.volume.createCombo( 'Enhancement', [
        {"value":"d", "text":"Data range"},
        {"value":"f", "text":"Full range"},
        {"value":"t", "text":"Data + tolerance"},
        {"value":"e", "text":"Equalized"}
    ], enhancement, this, this.changed);

    this.combo_negative = this.volume.createCombo( 'Negative', [
        {"value":"", "text":"No"},
        {"value":"negative", "text":"Negative"},
    ], this.def.negative, this, this.changed);

    this.combo_rotation = this.volume.createCombo( 'Rotation', [
        {"value":0, "text":"No"},
        {"value":90, "text":"Right 90deg"},
        {"value":-90, "text":"Left 90deg"},
        {"value":180, "text":"180deg"},
    ], this.def.rotate, this, this.changed);
};

VolumeDisplay.prototype.createChannelMap = function() {
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
                change : function(field, value) {
                    this.channel_colors[field.channel] = Ext.draw.Color.fromString('#' + value);
                    this.changed();
                },
            },
        });
    }
};
