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

//////////////////////////////////////////////////////////////////
//
// playback controller
//
//////////////////////////////////////////////////////////////////


Ext.define('BQ.viewer.Volume.playbackcontroller',{
    extend: 'Ext.container.Container',
    alias: 'widget.playback_control',
    border: false,
    endFrame: 1,
    enableTextSelection: false,
    layout: {
	    type: 'vbox',
	    align : 'stretch',
	    //pack  : 'start',
    },

    initComponent : function(){
	    var numFrames = 128;
	    this.loop = false;
	    this.sampleRate = 16;
	    var me = this;

	    this.timeSlider = Ext.create('Ext.slider.Slider', {
	        minValue: 0,
	        flex: 1,
	        //width: 400,
	        listeners: {
		        change: function(slider, value) {
		            var ratio = (value)/(this.timeSlider.maxValue-1);
		            this.panel3D.setCurrentTimeRatio(ratio);
		            this.panel3D.rerender(this.sampleRate);
		            this.frameNumber.setText((value+1) + "/" + this.endFrame);
		        },
		        scope:me
	        }
	    });

	    this.playButton = Ext.create('Ext.Button', {
	        cls: 'bq-btn-play',
	        enableToggle: true,
	        handler: function(){
		        console.log(this.playButton);
		        requestAnimationFrame(function() {me.doAnimate()});

	        },

	        scope:me,
	    });

	    this.frameNumber = Ext.create('Ext.toolbar.TextItem', {
	        text: "1/1",
	    });

        var qualityMenu = Ext.create('Ext.menu.Menu', {
	        text: 'render quality: ',
            //id: 'renderQuality1',
	        floating: true,  // usually you want this set to True (default)
	        items: [{
		        text: 'good',
		        checked: false,
                group: 'quality',
		        checkHandler: function(item, checked){
	                me.sampleRate = 32;
		        },
                scope: me
	        },{
		        text: 'better',
		        checked: false,
                group: 'quality',
		        checkHandler: function(item, checked){
	                me.sampleRate = 96;
		        },
                scope: me
	        },{
		        text: 'best',
		        checked: true,
                group: 'quality',
		        checkHandler: function(item, checked){
	                me.sampleRate = 256;
		        },
                scope: me
	        }]
	    });

        this.endFrame = this.panel3D.dims.t;
		this.timeSlider.setMaxValue(this.endFrame - 1);
		this.frameNumber.setText("1/" + this.endFrame);
	    var toolbar = {
            xtype: 'toolbar',
	        items:[this.playButton,
                   this.timeSlider,
		           this.frameNumber,
                  {
                       xtype: 'button',
                       text: 'render quality',
                       menu: qualityMenu
                   }],
	    };
	    Ext.apply(this, {
	        items:[toolbar]
	    });

	    this.setLoading(true);

	    this.panel3D.on({
	        loaded: function(){

	        },
	        scope: me,
	    });
	    this.callParent();
    },


    doAnimate : function(){
	    var me = this;
	    if(this.playButton.pressed == true){
	        var newVal = this.timeSlider.getValue()+1;
	        var maxVal = this.timeSlider.maxValue;
	        newVal = newVal > maxVal ? 0 : newVal;
	        this.timeSlider.setValue(newVal,false);
            this.panel3D.sceneVolume.setMaxSteps = this.sampleRate;
	        requestAnimationFrame(function() {me.doAnimate()});
	    }
    },

});

//////////////////////////////////////////////////////////////////
//
// keyframe slider
//
//////////////////////////////////////////////////////////////////


Ext.define('BQ.viewer.Volume.keySlider',{
    extend: 'Ext.slider.Multi',
    alias: 'widget.key_slider',
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

	    this.callParent();
    },

    dragFunc: function(){
	    var me = this;
	    if(!me.drag) return;
	    var dx = event.clientX - me.currentX;
	    me.currentMatrix[4] += dx;
	    var newMatrix = "matrix(" + me.currentMatrix.join(' ') + ")";
	    me.svgSlider.setAttributeNS(null, "transform", newMatrix);
	    me.currentX = window.event.clientX;

	    me.dragFunc();
    },

    afterRender: function(){
	    this.svgUrl = "http://www.w3.org/2000/svg";
	    this.svgdoc = document.createElementNS(this.svgUrl, "svg");
	    this.svgdoc.setAttributeNS(null, 'class', 'tick-slider');
	    this.el.dom.appendChild(this.svgdoc);
	    this.svgTicks = document.createElementNS(this.svgUrl, "g");
	    this.svgTicks.setAttributeNS(null, 'class', 'tick-slider');
	    this.svgdoc.appendChild(this.svgTicks);
	    this.drawTicks();

	    var me = this;
	    this.timeThumb = new Ext.slider.Thumb({
            ownerCt     : me,
            ownerLayout : me.getComponentLayout(),
            value       : 0,
            slider      : me,
            index       : 999,
            constrain   : me.constrainThumbs,
            disabled    : !!me.readOnly,
	        cls : 'x-slider-head',
        });
	    this.timeThumb.render();
	    this.callParent();
    },

    drawTicks : function(canvas){
	    var Start = this.startFrame;
	    var End   = this.endFrame;
	    var tic = this.tic;
	    var N = End - Start;
	    var path = '';
	    for(var i = 0; i < N+1; i++){
	        var x0, y0, x1, y1;
	        x0 = 1 + 98*i/N + '%';
	        x1 = x0;
	        if(i%tic == 0){
		        y0 = '25%';
		        y1 = '75%';
	        } else {
		        y0 = '40%';
		        y1 = '60%';
	        }
	        path += '<line x1=' + x0 + ' y1=' + y0 + ' x2=' + x1 + ' y2=' + y1 +
		        ' stroke = gray stroke-width=1.5 opacity = 0.7 fill="none" /></line>';
	    }
	    var svg = ' <svg width=100% height=100% >' + path +
	        '</svg>';

	    this.svgTicks.innerHTML = path;
    },


    //----------------------------------------------------------------------
    // event handlers
    //----------------------------------------------------------------------


    changecomplete: function(){
	    this.sortKeys();
	    this.callParent();
    },


    setValue : function(index, value, animate, changeComplete) {
        var me = this,
        thumbs = me.thumbs,
        thumb, len, i, values;
        if(index === 999){
	        thumb = me.timeThumb;
	    }
	    else{
            if (Ext.isArray(index)) {
		        values = index;
		        animate = value;

		        for (i = 0, len = values.length; i < len; ++i) {
                    thumb = thumbs[i];
                    if (thumb) {
			            me.setValue(i, values[i], animate);
                    }
		        }
		        return me;
            }

            thumb = me.thumbs[index];
	    }
        // ensures value is contstrained and snapped
        value = me.normalizeValue(value);

        if (value !== thumb.value && me.fireEvent('beforechange', me, value, thumb.value, thumb) !== false) {
            thumb.value = value;
            if (me.rendered) {
                // TODO this only handles a single value; need a solution for exposing multiple values to aria.
                // Perhaps this should go on each thumb element rather than the outer element.
                me.inputEl.set({
                    'aria-valuenow': value,
                    'aria-valuetext': value
                });

                thumb.move(me.calculateThumbPosition(value), Ext.isDefined(animate) ? animate !== false : me.animate);

                me.fireEvent('change', me, value, thumb);
                me.checkDirty();
                if (changeComplete) {
                    me.fireEvent('changecomplete', me, value, thumb);
                }
            }
        }
        return me;
    },


    onClickChange : function(trackPoint) {
        var me = this,
        thumb, index;

        // How far along the track *from the origin* was the click.
        // If vertical, the origin is the bottom of the slider track.

        //find the nearest thumb to the click event
        thumb = me.getNearest(trackPoint);
	    if (thumb.index == 999)
            if (!thumb.disabled) {
                index = thumb.index;
                me.setValue(index, Ext.util.Format.round(me.reversePixelValue(trackPoint),
						                                 me.decimalPrecision), undefined, true);
	        }
    },

    getCurrentTime : function(){

	    return this.timeThumb.value;
    },

    setHeadValue : function( value, animate ){
	    this.setValue(999,value,animate,true);
    },

    getNearest: function(trackPoint){
	    var me = this;

	    console.log(this);
	    clickValue = me.reversePixelValue(trackPoint);
	    var value = this.timeThumb.value;
	    dist = Math.abs(value - clickValue);
	    console.log("dist: ", dist);
	    if (dist < 10) return this.timeThumb;
	    else {
	        return this.callParent(arguments);
	    }
    },

    onMouseDown : function(e) {
	    var ymin    = this.getY();
	    var height = this.getHeight();
	    var yclick = e.getPageY();
	    var yrel = yclick - ymin;
	    var rat = yrel/height;
	    var me = this;

	    if(rat < 0.75 && rat > 0.25){
	        this.callParent(arguments);
	    }else{
	        trackPoint = this.getTrackpoint(e.getXY());
	        var newVal =  Ext.util.Format.round(me.reversePixelValue(trackPoint), me.decimalPrecision);
	        this.setValue(999, newVal, undefined, true);
	    }
    },


    //----------------------------------------------------------------------
    // get keyframe info
    //----------------------------------------------------------------------

    getFloorFrame : function(value){
	    var i0;

	    for(var i = 0; i < this.keyArray.length - 1; i++){
	        var x0 = this.keyArray[i].time.value;
	        var x1 = this.keyArray[i+1].time.value;
	        if(value == x0){
		        i0 = i;
	        }
	        else if(value > x0 && value < x1){
		        i0 = i;
	        }
	        else if(value >= x1){
		        i0 = i+1;
	        }
	    }
	    //console.log('floor: ', i0);
	    return i0;
    },

    getNearestFrame : function(inTime){
	    var i0 = 0, dist = 9999;
	    for(var i = 0; i < this.keyArray.length; i++){
	        var itTime = this.keyArray[i].time.value;
	        var cdist = Math.abs(inTime-itTime);
	        if(cdist < dist){
		        dist = cdist;
		        i0 = i;
	        }
	    }
	    return i0;
    },

    getInterpolatedValue : function(i, val){
	    if(this.keyArray.length < 2) return;
	    var i0 = i;
	    var i1 = i >= this.keyArray.length-1 ? i : i+1;
	    //console.log(i, i0, i1, this.keyArray.length);
	    var t1 = this.keyArray[i1].time.value;
	    var t0 = this.keyArray[i0].time.value;

	    var t = i >= this.keyArray.length-1 ? 1 : (val-t0)/(t1-t0);


	    var q0 = (new THREE.Quaternion).setFromEuler(this.keyArray[i0].rotation);
	    var q1 = (new THREE.Quaternion).setFromEuler(this.keyArray[i1].rotation);
	    var qi = q0.clone();
	    qi.slerp(q1,t);
	    var ri = new THREE.Euler(0,0,0,'XYZ');
	    ri.setFromQuaternion(qi,'XYZ');

        /*
	      var q0 = (new THREE.Quaternion).setFromEuler(this.keyArray[i+0].rotation);
	      var q1 = (new THREE.Quaternion).setFromEuler(this.keyArray[i+1].rotation);
	      var x0 = q0.x;
	      var x1 = q1.x;
	      var y0 = q0.y;
	      var y1 = q1.y;
	      var z0 = q0.z;
	      var z1 = q1.z;
	      var w0 = q0.w;
	      var w1 = q1.w;

	      var qi = new THREE.Quaternion(x0*(1.0-t) + x1*(t), y0*(1.0-t) + y1*(t), z0*(1.0-t) + z1*(t), w0*(1.0-t) + w1*(t));
	      qi.normalize();
	      var ri = new THREE.Euler(0,0,0,'XYZ');
	      ri.setFromQuaternion(qi,'XYZ');
        */
        /*
	      var x0 = this.keyArray[i+0].rotation.x;
	      var x1 = this.keyArray[i+1].rotation.x;
	      var y0 = this.keyArray[i+0].rotation.y;
	      var y1 = this.keyArray[i+1].rotation.y;
	      var z0 = this.keyArray[i+0].rotation.z;
	      var z1 = this.keyArray[i+1].rotation.z;
	      var ri = new THREE.Euler(x0*(1.0-t) + x1*(t), y0*(1.0-t) + y1*(t), z0*(1.0-t) + z1*(t), 'XYZ');
        */


	    var t0 = this.keyArray[i0].target.clone();
	    var t1 = this.keyArray[i1].target.clone();
	    var ti = t0.clone(); ti.lerp(t1,t);

	    var p0 = this.keyArray[i0].position.clone();
	    var p1 = this.keyArray[i1].position.clone();

	    var d0 = p0.clone(); d0.sub(t0);
	    var d1 = p1.clone(); d1.sub(t1);

	    var l0 = d0.length();
	    var l1 = d1.length();
	    var li = l0*(1.0-t) + l1*(t);

	    var pi = new THREE.Vector3(0.0,0.0,li);
	    pi.applyQuaternion(qi).add(ti);
	    //p0.lerp(p1,t);
	    return {pos:pi,
                targ: ti,
		        rot:ri};
    },

    //----------------------------------------------------------------------
    // update the current keyframe array
    //----------------------------------------------------------------------

    updateCurrentKeyFrame: function(rot, pos, target){
	    var curTime = this.getCurrentTime();
	    var nearestFrame = this.getNearestFrame(curTime);
	    var nearestTime = this.keyArray[nearestFrame].time.value;

	    var dif = Math.abs(curTime - nearestTime);
	    if(!this.autoKey) return;
	    if(dif < this.insertDist){

	        this.keyArray[nearestFrame].rotation = rot.clone();
	        this.keyArray[nearestFrame].position = pos.clone();
	        this.keyArray[nearestFrame].target   = target.clone();
	        var lastFrame = this.keyArray.length-1;
	        console.log(nearestFrame, this.loop);
	        if(nearestFrame == 0 && this.loop == true ){
		        console.log("swoop");
		        this.keyArray[lastFrame].rotation = rot.clone();
		        this.keyArray[lastFrame].position = pos.clone();
		        this.keyArray[lastFrame].target = target.clone();
	        }
	        if(nearestFrame == lastFrame && this.loop == true ){
		        this.keyArray[0].rotation = rot.clone();
		        this.keyArray[0].position = pos.clone();
		        this.keyArray[0].target = target.clone();
	        }
	    }
	    else
	        this.addKeyFrame(curTime);
    },

    sortKeys : function(){
	    this.keyArray.sort(function(a,b){
	        return (a.time.value-b.time.value);
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

    //----------------------------------------------------------------------
    // add and remove key frames frome array
    //----------------------------------------------------------------------

    addKeyFrame : function(frame){
	    //this adds a keyframe based given an input slider value
	    var hit = false;

	    var outKey;
	    for(var i = 0; i < this.keyArray.length; i++){
	        var pos   = this.keyArray[i].time.value;
	        var fudge = 0.01*this.maxValue;
	        var dist  = Math.abs(pos-frame);
	        if(dist < fudge){
		        hit = true;
		        outKey =  this.keyArray[i];
	        }
	    }

	    if(!hit){
	        var rot = this.panel3D.canvas3D.camera.rotation.clone();
	        var pos = this.panel3D.canvas3D.camera.position.clone();
	        var targ = this.panel3D.canvas3D.controls.target.clone();
	        var thumb;
	        if(frame == 0) {
		        thumb = this.thumbs[0];
	        }
	        else thumb = this.addThumb(frame);
	        var newKey = {time:thumb,
			              rotation: rot,
			              position: pos,
			              target: targ,}
	        this.keyArray.push(newKey);
	        this.current = this.keyArray.length - 1;
	        outKey = newKey;
	    }
	    this.sortKeys();
	    return outKey;
    },

    removeKeyFrame : function(frame){

	    if(frame > -1){
	        var it = -1;
	        var minDist = 999;
	        for(var i = 0; i < this.thumbs.length; i++){
		        var dist = Math.abs(frame - this.thumbs[i].value);
		        if(dist < this.insertDist){
		            it = i;
		            minDist = dist;
		        }
	        }

	        if(minDist > this.insertDist) return;
	        if(it >= 0){
		        var innerEl = this.thumbs[it].ownerCt.innerEl.dom;
		        innerEl.removeChild(this.thumbs[it].el.dom);
		        this.thumbs.splice(it,1);
		        for(var i = 0; i < this.thumbs.length; i++){
		            this.thumbs[i].index = i;
		        }
	        }

	        var ik = this.getNearestFrame(frame);
	        this.keyArray.splice(ik,1);
	    }
	    console.log("post: ", this.keyArray, this.keyArray.length);
	    console.log("post: ", this.thumbs);
    },

});

//////////////////////////////////////////////////////////////////
//
// animation controller
//
//////////////////////////////////////////////////////////////////

Ext.define('BQ.viewer.Volume.animationcontroller',{
    extend: 'Ext.container.Container',
    alias: 'widget.anim_control',
    border: false,
    enableTextSelection: false,
    layout: {
	    type: 'vbox',
	    align : 'stretch',
	    //pack  : 'start',
    },

    initComponent : function(){
	    var numFrames = 128;
	    //console.log("number of frames: ", numFrames);
	    this.startFrame = 0;
	    this.endFrame = numFrames > 1 ? numFrames :128;
	    this.chk      = 0;
	    this.tic      = 10;
	    this.lastX    = 0;
	    this.current  = 0;
	    this.renderSteps = 8;
	    this.overCanvas = false;
	    this.insertDist = 3;
	    if(this.panel3D.dims)
	        this.volumeEndFrame = this.panel3D.dims.t;
	    else
	        this.volumeEndFrame = 1;
	    this.loop = false;
	    this.sampleRate = 8;
	    var me = this;

	    this.keySlider = Ext.create('BQ.viewer.Volume.keySlider', {
	        startFrame: this.startFrame,
	        endFrame: this.endFrame,
	        tic:      this.tic,
	        panel3D: this.panel3D,
	        autoKey: false,
	        flex: 1,
            listeners: {
		        change: function(slider, value, thumb) {
		            //console.log(slider, value);
		            if(thumb.index === 999){
			            if (this.keySlider.keyArray.length < 2) return;
			            //var rat = value/slider.maxValue;
			            var ratio = (value)/(slider.maxValue-1);
			            this.panel3D.setCurrentTimeRatio(ratio);
			            this.panel3D.setMaxSteps = this.sampleRate;
			            this.panel3D.rerender(this.sampleRate);

			            var nearFrame = this.keySlider.getFloorFrame(value);
			            var interp = this.keySlider.getInterpolatedValue(nearFrame, value);

			            this.panel3D.canvas3D.camera.rotation.copy(interp.rot);
			            this.panel3D.canvas3D.camera.position.copy(interp.pos);

                        this.panel3D.canvas3D.controls.target.copy(interp.targ);
                        this.panel3D.canvas3D.controls.object.position.copy(interp.pos);
                        this.panel3D.canvas3D.controls.object.rotation.copy(interp.rot);

                        this.panel3D.canvas3D.controls.update();

			            this.keySlider.panelCamera.position.copy( this.panel3D.canvas3D.camera.position );
			            this.keySlider.panelCamera.rotation.copy( this.panel3D.canvas3D.camera.rotation );
			            this.keySlider.panel3D.canvas3D.camera = this.keySlider.panelCamera;
			            var volFrame = Math.floor(ratio*this.volumeEndFrame);
			            this.frameNumber.setText(volFrame + "/" + this.volumeEndFrame);
		            }
		        },
		        changeComplete: function(){
		            this.panel3D.canvas3D.controls.object = this.panel3D.canvas3D.camera;
		            this.panel3D.canvas3D.controls.noRotate = false;
		            this.panel3D.canvas3D.controls.noPan = false;
		        },
		        scope:me
            },
	    });

	    var addKeyButton = Ext.create('Ext.Button', {
	        iconCls: 'addbutton',
	        handler: function(){
		        this.keySlider.addKeyFrame(this.keySlider.getCurrentTime());

	        },
	        scope:me,
	    });

	    var removeKeyButton = Ext.create('Ext.Button', {
	        iconCls: 'deletebutton',
	        handler:function(){
		        this.keySlider.removeKeyFrame(this.keySlider.getCurrentTime());
	        },
	        scope:me,
	    });

	    var playButton = Ext.create('Ext.Button', {
	        //iconCls: 'playbutton',
            cls: 'bq-btn-play',
	        enableToggle: true,

	        handler: function(){
		        if(this.isPlaying) {
		            this.isPlaying = false;
		            this.keySlider.panelCamera.position.copy( this.panel3D.canvas3D.camera.position );
		            this.keySlider.panelCamera.rotation.copy( this.panel3D.canvas3D.camera.rotation );
		            this.keySlider.panel3D.canvas3D.camera = this.keySlider.panelCamera;
		            //if() button.iconCls = 'pausebutton';
		            //else button.setText('autokey on');
		        }
		        else this.isPlaying = true;
		        requestAnimationFrame(function() {me.doAnimate()});
	        },

	        scope:me,
	    });

	    var pauseButton = Ext.create('Ext.Button', {
	        iconCls: 'pausebutton',
	        handler: function(){
		        this.isPlaying = false;
		        this.isRecording = false;
		        this.keySlider.timeSlider.setValue(0,false);
		        this.keySlider.panelCamera.position.copy( this.panel3D.canvas3D.camera.position );
		        this.keySlider.panelCamera.rotation.copy( this.panel3D.canvas3D.camera.rotation );
		        this.keySlider.panel3D.canvas3D.camera = this.keySlider.panelCamera;
	        },
	        scope:me,
	    });

	    var recordButton = Ext.create('Ext.Button', {
	        iconCls: 'recordbutton',
	        handler: function(){
		        this.isRecording = true;
		        var video = new Whammy.Video(15);
		        this.renderSteps = 256;
		        this.doRecord(video);
	        },
	        scope:me,
	    });

	    var autoKeyButton = Ext.create('Ext.Button', {
	        enableToggle: true,
	        iconCls: 'addbutton',

	        handler: function(button, pressed) {
		        this.keySlider.autoKey = this.keySlider.autoKey ? false:true;

	        },
	        scope:me,
	    });

	    var setLoopButton = Ext.create('Ext.Button', {
	        enableToggle: true,
	        iconCls: 'loopbutton',

	        handler: function(button, pressed) {
		        this.keySlider.loop = this.keySlider.loop ? false:true;
		        var lastFrame = this.keySlider.keyArray.length-1;
		        if(this.keySlider.keyArray[lastFrame].time .value != this.endFrame){
		            var newKey = this.keySlider.addKeyFrame(this.keySlider.maxValue);
		            var cam = this.keySlider.panel3D.canvas3D.camera;

		            newKey.rotation = cam.rotation.clone();
		            newKey.position = cam.position.clone();
		            newKey.target =   this.panel3D.canvas3D.controls.target.clone();
		            this.keySlider.sortKeys();
		        }
		        else {
		            this.keySlider.keyArray[lastFrame].rotation.copy(this.keySlider.keyArray[0].rotation);
		            this.keySlider.keyArray[lastFrame].position.copy(this.keySlider.keyArray[0].position);
		            this.keySlider.keyArray[lastFrame].target.copy(this.keySlider.keyArray[0].target);
		        }

	        },
	        scope:me,

	    });

	    var qualityMenu = Ext.create('Ext.menu.Menu', {
	        text: 'render quality: ',
            //id: 'renderQuality2',
	        floating: true,  // usually you want this set to True (default)
	        items: [{
		        text: 'good',
		        checked: false,
                group: 'quality',
		        checkHandler: function(item, checked){
	                me.sampleRate = 32;
		        },
                scope: me
	        },{
		        text: 'better',
		        checked: false,
                group: 'quality',
		        checkHandler: function(item, checked){
	                me.sampleRate = 96;
		        },
                scope: me
	        },{
		        text: 'best',
		        checked: true,
                group: 'quality',
		        checkHandler: function(item, checked){
	                me.sampleRate = 256;
		        },
                scope: me
	        }]
	    });

	    this.numKeyFramesField = Ext.create('Ext.form.field.Number', {
            name: 'numberfield1',
            fieldLabel: 'keyframes',
            value: this.endFrame,
            minValue: 10,
            maxValue: 500,
            width: 200,
            listeners: {
		        change: function(field, newValue, oldValue) {
		            this.updateEndFrame(newValue);
		        },
		        scope:me
            },
	    });

	    this.frameNumber = Ext.create('Ext.toolbar.TextItem', {
	        text: "1/" + this.volumeEndFrame,
	    });
	    var toolbar1 = {
            xtype: 'toolbar',
	        items:[recordButton,
		           autoKeyButton,
		           removeKeyButton,
		           setLoopButton,
		           '->',
		           //sampleRate,
                   {text: 'render quality',
                    menu: qualityMenu,},
		           this.numKeyFramesField
		          ],
	    };
	    var toolbar2 = {
            xtype: 'toolbar',
	        items:[playButton,this.keySlider,
		           this.frameNumber],
	    };

	    Ext.apply(this, {
	        items:[toolbar1,
		           toolbar2,
		          ],
	    });

	    this.callParent();
    },



    afterRender : function(){
	    this.callParent();
	    var me = this;
	    var listener = function(){
            var rot  = me.keySlider.panel3D.canvas3D.camera.rotation;
	        var pos  = me.keySlider.panel3D.canvas3D.camera.position;
	        var targ = me.keySlider.panel3D.canvas3D.controls.target;
	        me.keySlider.updateCurrentKeyFrame(rot,pos,targ);
        }

        //this.keySlider.panel3D.canvas3D.el.addListener('mouseup',listener, me);
        this.keySlider.panel3D.canvas3D.getEl().on({
            //scope : this,
            mouseup : listener,
            mousewheel: listener,
            DOMMouseScrool: listener,
        });
    },

    afterFirstLayout : function(){
	    this.callParent();
	    this.keySlider.addKeyFrame(0);
	    var me = this;
	    var width = this.panel3D.canvas3D.getWidth();
	    var height = this.panel3D.canvas3D.getHeight();

	    var aspect = width/height;

	    this.keySlider.animCamera = new THREE.PerspectiveCamera(20, aspect, .01, 100);
	    this.keySlider.animCamera.position.copy( this.keySlider.panel3D.canvas3D.camera.position );
	    this.keySlider.animCamera.rotation.copy( this.keySlider.panel3D.canvas3D.camera.rotation );
	    this.keySlider.panelCamera = this.keySlider.panel3D.canvas3D.camera;
    },

    //----------------------------------------------------------------------
    // Animate and record stuff
    //----------------------------------------------------------------------
    updateEndFrame : function(newValue){
	    if(newValue > 9){
	        this.keySlider.scaleKeys(newValue);
	        this.keySlider.endFrame = newValue;
	        this.keySlider.setMaxValue(newValue);
	        this.keySlider.drawTicks();
	        this.numKeyFramesField.setValue(newValue);
	    }
    },

    doAnimate : function(){
	    var me = this;
	    if(this.isPlaying){
	        var maxTime = this.keySlider.maxValue;
	        var increment = maxTime/this.keySlider.endFrame;
	        var currentTime = (this.keySlider.timeThumb.value + increment)%maxTime;

	        this.keySlider.setHeadValue(currentTime,false);
	        requestAnimationFrame(function() {me.doAnimate()});
	    }
    },

    doRecord : function(video){
	    var me = this;
	    var context = this.panel3D.canvas3D.renderer.domElement.getContext('webgl');
	    video.add(context);
	    this.chk += 1;

	    var maxTime = this.keySlider.maxValue;
	    var increment = maxTime/this.keySlider.endFrame;
	    var currentTime = (this.keySlider.timeThumb.value + increment)%maxTime;
	    this.keySlider.setHeadValue(currentTime,false);
	    this.timeValue = currentTime;
	    if(currentTime > maxTime-2) {
	        var start_time = +new Date;
	        var output = video.compile();

	        var end_time = +new Date;
	        var url = webkitURL.createObjectURL(output);
	        window.open(url);
	        this.isRecording = false;
	        this.renderSteps = 8;
	    }
	    if(this.isRecording){
	        requestAnimationFrame(function() {me.doRecord(video)});
	    }

    },
});
