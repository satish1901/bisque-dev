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


function gObjectBuffer(volume) {
	this.volume = volume
		this.position = new Array();
	this.index = new Array();
	this.colors = new Array();
};

gObjectBuffer.prototype.rescale = function () {
	var scale = this.volume.sceneVolume.getRescale().clone();
	this.mesh.geometry.dynamic = true;
	this.mesh.geometry.verticesNeedUpdate = true;
	var mat = new THREE.Matrix4().scale(scale);
	this.mesh.geometry.applyMatrix(mat);
	this.mesh.geometry.computeBoundingBox();
};

gObjectBuffer.prototype.pushPosition = function (p, x, positions) {
	var dims = this.volume.dims.slice;
	positions[x * 3 + 0] = (p.x / dims.x - 0.5);
	positions[x * 3 + 1] = (0.5 - p.y / dims.y);
	positions[x * 3 + 2] = (0.5 - p.z / dims.z);
};

gObjectBuffer.prototype.push = function (poly) {}
gObjectBuffer.prototype.allocateMesh = function () {}

gObjectBuffer.prototype.build = function(gObject, ftor){
    this.push(ftor(gObject));
}

gObjectBuffer.prototype.buildBuffer = function () {
	var geometry = new THREE.BufferGeometry();
	geometry.addAttribute('index', new THREE.BufferAttribute(new Uint32Array(this.index.length), 1));
	geometry.addAttribute('position', new THREE.BufferAttribute(new Float32Array(this.position.length * 3), 3));
	geometry.addAttribute('color', new THREE.BufferAttribute(new Float32Array(this.colors.length * 3), 3));
	var gpositions = geometry.getAttribute('position').array;
	var gindex = geometry.getAttribute('index').array;
	var gcolor = geometry.getAttribute('color').array;
	//var check0 = index.slice(0);

	for (var i = 0; i < this.index.length; i++) {
		gindex[i] = this.index[i];
	}

	for (var i = 0; i < this.position.length; i++) {
		this.pushPosition(this.position[i], i, gpositions);
	}

	for (var i = 0; i < this.colors.length; i++) {
		gcolor[3 * i + 0] = this.colors[i].r;
		gcolor[3 * i + 1] = this.colors[i].g;
		gcolor[3 * i + 2] = this.colors[i].b;
	}

	this.mesh = this.allocateMesh(geometry, this.material);
	this.mesh.geometry.dynamic = true;
	this.mesh.geometry.computeBoundingBox();
	this.mesh.geometry.verticesNeedUpdate = true;

}

function pointBuffer(volume) {
	gObjectBuffer.call(this, volume);
	this.volume = volume;
};

pointBuffer.prototype = new gObjectBuffer();

pointBuffer.prototype.push = function (g) {

	var lcolor = {
		r : Math.random(),
		g : Math.random(),
		b : Math.random()
	}
	this.colors.push(lcolor);
	this.position.push(g.vertices[0]); // = positions.concat(poly)
	this.index.push(this.index.length);

	//index.push(lindex);// = index.concat(lindex);
	//console.log('local: ', lindex, 'localpoly: ', poly, 'global: ', index, 'global p: ',positions);
	//triCounter += polys[i].vertices.length;
};

pointBuffer.prototype.allocateMesh = function (geometry, material) {
	var cloud = new THREE.PointCloud(geometry, material);
	return cloud;
};

pointBuffer.prototype.sortParticles = function (pos) {
	var gpositions = this.mesh.geometry.getAttribute('position').array;
	var gindex = this.mesh.geometry.getAttribute('index').array;
	var gcolor = this.mesh.geometry.getAttribute('color').array;

	if (!this.permutation) {
		//preallocate the distance array
		this.permutation = new Array(gindex.length);
		for (var i = 0; i < this.permutation.length; i++) {
			this.permutation[i] = {
				i : i,
				dist : 0.0,
				visited : false
			};
		}
	}

	for (var i = 0; i < this.permutation.length; i++) {
		this.permutation[i].i = i;
		var d0 = pos.x - gpositions[3 * i + 0];
		var d1 = pos.y - gpositions[3 * i + 1];
		var d2 = pos.z - gpositions[3 * i + 2];
		this.permutation[i].dist = d0 * d0 + d1 * d1 + d2 * d2;
	}
	this.permutation.sort(function (a, b) {
		return b.dist - a.dist
	}); //sort the permutations in descending order

	var assign = function (i, bigArr, tmpArr, sz) {
		for (y = 0; y < sz; y++) {
			bigArr[sz * i + y] = tmpArr[y];
		}
	};

	var getSet = function (i, index, pos, col) {
		//var pi = perm[i].i;
		var set = {
			ind : [index[i]],
			col : [col[3 * i + 0],
				col[3 * i + 1],
				col[3 * i + 2]],
			pos : [pos[3 * i + 0],
				pos[3 * i + 1],
				pos[3 * i + 2]],
		};
		return set;
	};

	//debugger;

	for (var i = 0; i < this.permutation.length; i++) {
		var begin = getSet(i, gindex, gpositions, gcolor)
			var k = 0;
		var iterating = 1;
		var ci = i;
		if (this.permutation[i].visited == true)
			continue;
		while (iterating == 1) {
			var swapVars = getSet(this.permutation[ci].i, gindex, gpositions, gcolor);

			assign(ci, gindex, swapVars.ind, 1);
			assign(ci, gpositions, swapVars.pos, 3);
			assign(ci, gcolor, swapVars.col, 3);

			if (this.permutation[ci].i == i) {
				assign(ci, gindex, begin.ind, 1);
				assign(ci, gpositions, begin.pos, 3);
				assign(ci, gcolor, begin.col, 3);
				iterating = false;
				continue;
			}
			ci = this.permutation[ci].i;
			this.permutation[ci].visited = true;
			k++;
		}
	}

	var logOut = '';
	for (var i = 0; i < gpositions.length / 3; i++) {
		var d0 = pos.x - gpositions[3 * i + 0];
		var d1 = pos.y - gpositions[3 * i + 1];
		var d2 = pos.z - gpositions[3 * i + 2];
		logOut += d0 * d0 + d1 * d1 + d2 * d2 + ' ';
	}
	this.mesh.geometry.dynamic = true;
	this.mesh.geometry.verticesNeedUpdate = true;
	this.mesh.geometry.attributes.index.needsUpdate = true;
	this.mesh.geometry.attributes.position.needsUpdate = true;
	this.mesh.geometry.attributes.color.needsUpdate = true;
	//console.log(logOut);
}

function lineBuffer(volume) {
	gObjectBuffer.call(this, volume);
};

lineBuffer.prototype = new gObjectBuffer();
/*
lineBuffer.prototype.push = function(poly){

var lcolor = {r: Math.random(),g: Math.random(),b: Math.random()}

for(var i = 0; i < poly.length; i++){
this.colors.push(lcolor);
this.index.push(this.position.length, this.position.length + 1);// = positions.concat(poly)
//this.index.push(this.position.length + 1);// = positions.concat(poly)

this.position.push(poly[i]);// = positions.concat(poly)
};

//index.push(lindex);// = index.concat(lindex);
//console.log('local: ', lindex, 'localpoly: ', poly, 'global: ', index, 'global p: ',positions);
//triCounter += polys[i].vertices.length;
};
 */

lineBuffer.prototype.isClockWise = function (poly) {
	//use shoelace determinate
	var det = 0;
	for (var i = 0; i < poly.length; i++) {
		var cur = poly[i];
		var nex = poly[(i + 1) % poly.length];
		det += cur.x * nex.y - cur.y * nex.x;
	}
	return det > 0;
};

lineBuffer.prototype.push = function (g) {
	//poly is any object with an x and a y.
	//loads necessary data onto the vertex buffer
    var poly = g.vertices;
	var lindex = [];

	for (var i = 0; i < poly.length - 1; i++) {
		lindex.push(i);
		lindex.push(i + 1);
	}
	//lindex.push(poly.length-1);
	//lindex = POLYGON.tessellate(poly, []);
	/*
	if(!this.isClockWise(poly))
	lindex = POLYGON.tessellate(poly, []);
	else
	lindex = POLYGON.tessellate(poly.reverse(), []);
	 */
	for (var j = 0; j < lindex.length; j++) {
		lindex[j] += this.position.length;
	}

	var lcolor = {
		r : Math.random(),
		g : Math.random(),
		b : Math.random()
	}
	for (var j = 0; j < poly.length; j++) {
		this.colors.push(lcolor);
	}

	for (var i = 0; i < poly.length; i++) {
		this.position.push(poly[i]); // = positions.concat(poly)
	};

	for (var i = 0; i < lindex.length; i++) {
		this.index.push(lindex[i]); // = positions.concat(poly)
	};
	//index.push(lindex);// = index.concat(lindex);
	//console.log('local: ', lindex, 'localpoly: ', poly, 'global: ', index, 'global p: ',positions);
	//triCounter += polys[i].vertices.length;
};

lineBuffer.prototype.allocateMesh = function (geometry, material) {
	return new THREE.Line(geometry, material, THREE.LinePieces);
};

function polyBuffer(volume) {
	gObjectBuffer.call(this, volume);
};

polyBuffer.prototype = new gObjectBuffer();

polyBuffer.prototype.isClockWise = function (poly) {
	//use shoelace determinate
	var det = 0;
	for (var i = 0; i < poly.length; i++) {
		var cur = poly[i];
		var nex = poly[(i + 1) % poly.length];
		det += cur.x * nex.y - cur.y * nex.x;
	}
	return det > 0;
};

polyBuffer.prototype.push = function (g) {
	//poly is any object with an x and a y.
	//loads necessary data onto the vertex buffer
    var poly = g.vertices;
	var lindex = [];
	if (!this.isClockWise(poly))
		lindex = POLYGON.tessellate(poly, []);
	else
		lindex = POLYGON.tessellate(poly.reverse(), []);

	for (var j = 0; j < lindex.length; j++) {
		lindex[j] += this.position.length;
	}

	var lcolor = {
		r : Math.random(),
		g : Math.random(),
		b : Math.random()
	}
	for (var j = 0; j < poly.length; j++) {
		this.colors.push(lcolor);
	}

	for (var i = 0; i < poly.length; i++) {
		this.position.push(poly[i]); // = positions.concat(poly)
	};

	for (var i = 0; i < lindex.length; i++) {
		this.index.push(lindex[i]); // = positions.concat(poly)
	};
	//index.push(lindex);// = index.concat(lindex);
	//console.log('local: ', lindex, 'localpoly: ', poly, 'global: ', index, 'global p: ',positions);
	//triCounter += polys[i].vertices.length;
};

polyBuffer.prototype.allocateMesh = function (geometry, material) {
	return new THREE.Mesh(geometry, material);
};

/*
polyBuffer.prototype.buildBuffer = function(){
var geometry = new THREE.BufferGeometry();
geometry.addAttribute( 'index',    new THREE.BufferAttribute( new Uint32Array( this.index.length ), 1 ));
geometry.addAttribute( 'position', new THREE.BufferAttribute( new Float32Array(this. position.length * 3 ), 3 ) );
geometry.addAttribute( 'color',    new THREE.BufferAttribute( new Float32Array( this.colors.length * 3 ), 3 ) );
var gpositions = geometry.getAttribute('position').array;
var gindex     = geometry.getAttribute('index').array;
var gcolor     = geometry.getAttribute('color').array;
//var check0 = index.slice(0);

for(var i = 0; i < this.index.length; i++){
gindex[i] = this.index[i];
}

for(var i = 0; i < this.position.length; i++){
this.pushPosition(this.position[i], i, gpositions);
}

for(var i = 0; i < this.colors.length; i++){
gcolor[3*i + 0] = this.colors[i].r;
gcolor[3*i + 1] = this.colors[i].g;
gcolor[3*i + 2] = this.colors[i].b;
}

this.mesh = new THREE.Mesh( geometry, this.material);

this.mesh.geometry.dynamic = true;
this.mesh.geometry.computeBoundingBox();
this.mesh.geometry.verticesNeedUpdate = true;
};
 */

function BQFactory3D(){
};

BQFactory3D.set = function(pointBuffer, lineBuffer, polyBuffer){
    this.PointBuffer = pointBuffer;
    this.LineBuffer = lineBuffer;
    this.PolyBuffer = polyBuffer;

    BQFactory3D.buffermap = {
        //gobject  : BQGObject,
        point    : this.PointBuffer,
        rectangle: this.PolyBuffer,
        square   : this.PolyBuffer,
        ellipse  : this.PolyBuffer,
        circle   : this.PolyBuffer,
        polygon  : this.PolyBuffer,
        polyline : this.LineBuffer,
        line     : this.LineBuffer,
        //label    : BQGObject,
    }
};

BQFactory3D.ftormap = {
    point     : function(g) { return g;},
    rectangle : function(g) {
        var p0 = g.vertices[0];
        var p1 = g.vertices[1];
        var vertices = [{x: p0.x, y: p0.y, z: p0.z},
                        {x: p1.x, y: p0.y, z: p0.z},
                        {x: p1.x, y: p1.y, z: p0.z},
                        {x: p0.x, y: p1.y, z: p0.z}
                       ];
        return  {vertices: vertices, color: g.color};
    },
    square    : function(g) { return g;},
    ellipse    : function(g) {
        var p0 = g.vertices[0];
        var p1 = g.vertices[1];
        var p2 = g.vertices[2];

        var dp0 = {x:p1.x - p0.x,
                  y:p1.y - p0.y,
                  z:p1.z - p0.z};


        var dp1 = {x:p2.x - p0.x,
                  y:p2.y - p0.y,
                  z:p2.z - p0.z};

        var vertices = [];
        var r0 = Math.sqrt(dp0.x*dp0.x + dp0.y*dp0.y + dp0.z*dp0.z);
        var r1 = Math.sqrt(dp1.x*dp1.x + dp1.y*dp1.y + dp1.z*dp1.z);

        var b0 = {x: dp0.x/r0, y: dp0.y/r0, z: dp0.z/r0};
        var b1 = {x:-b0.y, y: b0.x, z: b0.z};
        console.log(r0, r1, b0, b1);
        var N = 16;
        var phase = 0;
        var npi = 2.0*Math.PI/N;
        for(var i = 0; i < 16; i++){
            vertices.push({x: p0.x + r0*b0.x*Math.cos(phase) + r1*b1.x*Math.sin(phase),
                           y: p0.y + r0*b0.y*Math.sin(phase) + r1*b1.y*Math.cos(phase),
                           z: p0.z});

            /*
            vertices.push({x: p0.x + r0*Math.cos(phase),
                           y: p0.y + r1*Math.sin(phase),
                           z: p0.z});
            */
            phase += npi;
        }
        return  {vertices: vertices, color: g.color};
    },
    circle    : function(g) {
        var p0 = g.vertices[0];
        var p1 = g.vertices[1];
        var dp = {x:p1.x - p0.x,
                  y:p1.y - p0.y,
                  z:p1.z - p0.z};

        var vertices = [];
        var r = Math.sqrt(dp.x*dp.x + dp.y*dp.y + dp.z*dp.z);
        var N = 16;
        var phase = 0;
        var npi = 2.0*Math.PI/N;
        for(var i = 0; i < 16; i++){
            vertices.push({x: p0.x + r*Math.cos(phase),
                           y: p0.y + r*Math.sin(phase),
                           z: p0.z});
            phase += npi;
        }
        return  {vertices: vertices, color: g.color};
    },
    polygon   : function(g) { return g;},
    polyline  : function(g) { return g;},
    polyline  : function(g) { return g;},
    line      : function(g) { return g;},
    //label    : BQGObject,
}

BQFactory3D.make = function(g){
    var buffer = BQFactory3D.buffermap[g.resource_type];
    var ftor   = BQFactory3D.ftormap[g.resource_type];
    buffer.build(g, ftor);
}

Ext.define('BQ.viewer.Volume.pointControl', {
	extend : 'Ext.container.Container',
	alias : 'widget.pointControl',
	/*
	changed : function(){
	if(this.isLoaded){
	this.sceneVolume.setUniform('LIGHT_POSITION', this.lightObject.position);
	}
	},
	 */
	addUniforms : function () {},
	buildCube : function (sz) {
		var geometry = new THREE.BufferGeometry();
		geometry.addAttribute('index', new THREE.BufferAttribute(new Uint32Array(36), 1));
		geometry.addAttribute('position', new THREE.BufferAttribute(new Float32Array(8 * 3), 3));
		//      geometry.addAttribute( 'color',    new THREE.BufferAttribute( new Float32Array( this.colors.length * 3 ), 3 ) );
		var gpositions = geometry.getAttribute('position').array;
		var gindex = geometry.getAttribute('index').array;

		gindex[0] = 0;
		gindex[1] = 2;
		gindex[2] = 1;
		gindex[3] = 2;
		gindex[4] = 3;
		gindex[5] = 1;
		gindex[6] = 4;
		gindex[7] = 6;
		gindex[8] = 5;
		gindex[9] = 6;
		gindex[10] = 7;
		gindex[11] = 5;
		gindex[12] = 4;
		gindex[13] = 5;
		gindex[14] = 1;
		gindex[15] = 5;
		gindex[16] = 0;
		gindex[17] = 1;

		gindex[18] = 7;
		gindex[19] = 6;
		gindex[20] = 2;
		gindex[21] = 6;
		gindex[22] = 3;
		gindex[23] = 2;
		gindex[24] = 5;
		gindex[25] = 7;
		gindex[26] = 0;
		gindex[27] = 7;
		gindex[28] = 2;
		gindex[29] = 0;
		gindex[30] = 1;
		gindex[31] = 3;
		gindex[32] = 4;
		gindex[33] = 3;
		gindex[34] = 6;
		gindex[35] = 4;

		gpositions[0] = sz;
		gpositions[1] = sz;
		gpositions[2] = sz;
		gpositions[3] = sz;
		gpositions[4] = sz;
		gpositions[5] = -sz;
		gpositions[6] = sz;
		gpositions[7] = -sz;
		gpositions[8] = sz;
		gpositions[9] = sz;
		gpositions[10] = -sz;
		gpositions[11] = -sz;

		gpositions[12] = -sz;
		gpositions[13] = sz;
		gpositions[14] = -sz;
		gpositions[15] = -sz;
		gpositions[16] = sz;
		gpositions[17] = sz;
		gpositions[18] = -sz;
		gpositions[19] = -sz;
		gpositions[20] = -sz;
		gpositions[21] = -sz;
		gpositions[22] = -sz;
		gpositions[23] = sz;

		/*
		for(var i = 0; i < this.colors.length; i++){
		gcolor[3*i + 0] = this.colors[i].r;
		gcolor[3*i + 1] = this.colors[i].g;
		gcolor[3*i + 2] = this.colors[i].b;
		}
		 */
		return geometry;

	},
	rescalePoints : function () {
		this.currentSet.points.rescale();
		this.currentSet.polylines.rescale();
		this.currentSet.polygons.rescale();
		//console.log(this.points);
	},

	setVisible : function (vis) {
		var t = this.panel3D.currentTime;
		this.currentSet = this.gObjectBuffers[t];
		for (var item in this.currentSet) {
			if (!item)
				continue;
			var curMesh = this.currentSet[item].mesh;
			curMesh.visible = vis;
		}
	},

	updateScene : function () {
		var t = this.panel3D.currentTime;

		if (!this.currentSet)
			this.currentSet = {};
		for (var item in this.currentSet) {
			if (!item)
				continue;

			var curMesh = this.currentSet[item].mesh;
			if (curMesh)
				this.sceneVolume.sceneData.remove(curMesh); // remove current point set
		}
		this.currentSet = this.gObjectBuffers[t];
		for (var item in this.currentSet) {
			if (!item)
				continue;
			var curMesh = this.currentSet[item].mesh;
			console.log('item: ', item);
			if (curMesh) {
				this.sceneVolume.sceneData.add(curMesh); // remove current point set
				if (this.state === 1)
					curMesh.visible = true;
				else
					curMesh.visible = false;
			}
		}

		this.points = this.currentSet.points.mesh; //set current pointer to loaded set

		this.pointclouds = new Array();

		for (var c in this.currentSet) {
			if (this.currentSet[c])
				this.pointclouds.push(this.currentSet[c].mesh);
		}
	},

    initBuffers : function(){
        var t = this.panel3D.currentTime;
		if (this.gObjectBuffers[t]) { //load points in lazily
			this.updateScene();
			return;
		}

		this.gObjectBuffers[t] = {};

		var pBuffer = new polyBuffer(this.panel3D);
		pBuffer.material = this.polyShaderMaterial;
		this.gObjectBuffers[t].polygons = pBuffer;

		var lBuffer = new lineBuffer(this.panel3D);
		lBuffer.material = this.polyShaderMaterial;
		this.gObjectBuffers[t].polylines = lBuffer;

		var cBuffer = new pointBuffer(this.panel3D);
		cBuffer.material = this.pointShaderMaterial;
		this.gObjectBuffers[t].points = cBuffer;

		this.gObjectBuffers[t].polygons = pBuffer;
		//todo: I think we want to build buffers for every frame right here,
		//      rather than load lazily... if we have 10 million gobjects to
		//      sift through, then this will get pretty slow
        BQFactory3D.set(cBuffer, lBuffer, pBuffer);
    },

	loadGObjects : function () {
         var t = this.panel3D.currentTime;
        this.initBuffers();
        var tStack = [this];
        while(tStack.length > 0){
            var context = tStack[tStack.length-1];
		    for (var i = 0; i < context.gobjects.length; i++) {
			    var g = context.gobjects[i];
                console.log(g);
                if(g.gobjects.length > 0) tStack.unshift(g);
                else if (!g.vertices[0].t)     BQFactory3D.make(g);
                else if (g.vertices[0].t == t) BQFactory3D.make(g);
		    }
            tStack.pop();
        }

	    this.gObjectBuffers[t].points.buildBuffer();
		this.gObjectBuffers[t].polylines.buildBuffer();
		this.gObjectBuffers[t].polygons.buildBuffer();
		this.updateScene();
		this.rescalePoints();
	},

	initComponent : function () {
		this.title = 'show points';
		var me = this;
		this.dist = 1.0;
		this.state = 0;
		this.lighting = Ext.create('Ext.form.field.Checkbox', {
				boxLabel : 'show points',
				checked : false,
				handler : function () {
					this.state ^= 1;
					if ((this.state & 1) === 1) {
						this.setVisible(true);
					} else {
						this.setVisible(false);
					}
					this.rescalePoints();
					this.panel3D.rerender();
				},
				scope : me,
			});

		var me = this;
		this.plane = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000, 8, 8),
				new THREE.MeshBasicMaterial({
					color : 0x000000,
					opacity : 0.25,
					transparent : true,
					wireframe : true
				}));
		this.plane.visible = false;

		this.sceneVolume.scene.add(this.plane);

		this.sceneVolume.scene.add(this.lightObject);
		this.canvas3D.getEl().dom.addEventListener('mousemove', me.onMouseMove.bind(this), true);
		this.canvas3D.getEl().dom.addEventListener('mouseup', me.onMouseUp.bind(this), true);
		this.canvas3D.getEl().dom.addEventListener('mousedown', me.onMouseDown.bind(this), true);

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
		this.useColor = 0;
		this.pointShaderMaterial = new THREE.ShaderMaterial({
				uniforms : {
					tex1 : {
						type : "t",
						value : spriteTex
					},
					zoom : {
						type : 'f',
						value : 100.0
					},
					near : {
						type : 'f',
						value : 0.1
					},
					far : {
						type : 'f',
						value : 20.0
					},
					USE_COLOR : {
						type : 'i',
						value : this.useColor
					}
				},
				attributes : {
					alpha : {
						type : 'f',
						value : null
					},
				},
				vertexShader : vert,
				fragmentShader : frag,
				side : THREE.DoubleSide,
				alphaTest : 0.5,
				transparent : true
			});

		this.polyShaderMaterial = new THREE.ShaderMaterial({
				uniforms : {
					near : {
						type : 'f',
						value : 0.1
					},
					far : {
						type : 'f',
						value : 20.0
					},
					USE_COLOR : {
						type : 'i',
						value : this.useColor
					}
				},
				vertexShader : vertDepth,
				fragmentShader : fragDepth,
				side : THREE.DoubleSide,
				//transparent: true
			});

		this.backGroundShaderMaterial = new THREE.ShaderMaterial({
				uniforms : {
					near : {
						type : 'f',
						value : 0.1
					},
					far : {
						type : 'f',
						value : 20.0
					},
					USE_COLOR : {
						type : 'i',
						value : this.useColor
					}
				},
				vertexShader : vertDepth,
				fragmentShader : fragDepthBack,
				side : THREE.BackSide,
				//transparent: true
			});

		this.gObjectSets = new Array();
		this.gObjectBuffers = new Array();
		this.loadGObjects();

		this.panel3D.on('time', this.loadGObjects, me);
		this.panel3D.on('scale', this.rescalePoints, me);

		this.raycaster = new THREE.Raycaster();
		this.raycaster.params.PointCloud.threshold = 0.0025;
		/*
		var sphereGeometry = new THREE.SphereGeometry( 0.01, 32, 32 );
		var sphereMaterial = new THREE.MeshBasicMaterial( { color: 0xff0000, shading: THREE.FlatShading } );
		this.sphere =  new THREE.Mesh( sphereGeometry, backGroundShaderMaterial );
		this.sceneVolume.sceneData.add( this.sphere );
		 *///var backGroundGeometry = new THREE.PlaneGeometry(10,10);
		//var backGroundGeometry = new THREE.BoxGeometry(8.0, 8.0, 8.0);
		//var backGroundGeometry = new THREE.SphereGeometry( 8.0, 32, 32 );
		var backGroundGeometry = this.buildCube(6.0);
		var backGround = new THREE.Mesh(backGroundGeometry, this.backGroundShaderMaterial);

		this.backGroundShaderMaterial.needsUpdate = true;
		backGroundGeometry.buffersNeedUpdate = true;
		backGroundGeometry.uvsNeedUpdate = true;

		//backGround.overdraw = true;
		//backGround.doubleSided = true;
		this.sceneVolume.sceneData.add(backGround);

		this.addUniforms();
		this.isLoaded = true;
		this.panel3D.canvas3D.animate_funcs[0] = callback(this, this.onAnimate);

		this.depthBuffer
			 = new THREE.WebGLRenderTarget(this.panel3D.getWidth(), this.panel3D.getHeight(), {
				minFilter : THREE.LinearFilter,
				magFilter : THREE.NearestFilter,
				format : THREE.RGBAFormat
			});
		this.colorBuffer
			 = new THREE.WebGLRenderTarget(this.panel3D.getWidth(), this.panel3D.getHeight(), {
				minFilter : THREE.LinearFilter,
				magFilter : THREE.NearestFilter,
				format : THREE.RGBAFormat
			});

		this.updateScene();
		this.items = [this.lighting];
		this.callParent();
	},

	onAnimate : function () {

		if (this.sceneVolume.sceneData) {

			var panel = this.panel3D;
			//move this to background plug-in
			var camPos = this.panel3D.canvas3D.camera.position;
			this.currentSet.points.sortParticles(camPos);
			panel.canvas3D.renderer.clearTarget(this.accumBuffer0,
				true, true, true);
			var buffer = this.accumBuffer0;
			var bufferColor = this.accumBuffer1;

			this.pointShaderMaterial.uniforms.USE_COLOR.value = 0;
			this.polyShaderMaterial.uniforms.USE_COLOR.value = 0;
			this.backGroundShaderMaterial.uniforms.USE_COLOR.value = 0;
			//this.useColor = 0;
			panel.canvas3D.renderer.render(this.sceneVolume.sceneData,
				this.canvas3D.camera,
				this.depthBuffer);

			this.pointShaderMaterial.transparent = true;
			this.pointShaderMaterial.uniforms.USE_COLOR.value = 1;
			this.polyShaderMaterial.uniforms.USE_COLOR.value = 1;
			this.backGroundShaderMaterial.uniforms.USE_COLOR.value = 1;
			panel.canvas3D.renderer.render(this.sceneVolume.sceneData,
				this.canvas3D.camera,
				this.colorBuffer);

			panel.sceneVolume.setUniform('BACKGROUND_DEPTH', this.depthBuffer, false);
			panel.sceneVolume.setUniform('BACKGROUND_COLOR', this.colorBuffer, false);
		}
	},

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

	onMouseMove : function (event) {
		event.preventDefault();
		if (this.points.visible === false)
			return;
		var width = this.canvas3D.getWidth();
		var height = this.canvas3D.getHeight();
		var cx = this.canvas3D.getX();
		var cy = this.canvas3D.getY();
		var x = ((event.clientX - cx) / width) * 2 - 1;
		var y =  - ((event.clientY - cy) / height) * 2 + 1;

		var camera = this.canvas3D.camera;

		var vector = new THREE.Vector3(x, y, 0.5);
		this.canvas3D.projector.unprojectVector(vector, camera);
		this.raycaster.ray.set(camera.position, vector.sub(camera.position).normalize());

		var intersections = this.raycaster.intersectObjects(this.pointclouds);
		intersection = (intersections.length) > 0 ? intersections[0] : null;
		if (intersection !== null) {
			//this.sphere.position.copy( intersection.point );
			var gindex = intersections[0].object.geometry.getAttribute('index').array;
			var pos = this.canvas3D.projector.projectVector(intersection.point.clone(), camera);
			var index;
			if (intersection.index)
				index = gindex[intersection.index];
			if (intersection.indices)
				index = intersection.indices;
			this.label.style.top = '' + 0.5 * height * (1.0 - pos.y) + cy + 'px';
			this.label.style.left = '' + 0.5 * width * (1.0 + pos.x) - cx + 'px';
			this.label.textContent = [index].join(", ");

		}
		if (!this.label) {
			this.label = document.createElement('div');
			this.label.style.backgroundColor = 'white';
			this.label.style.position = 'absolute';
			this.label.style.padding = '1px 4px';
			this.label.style.borderRadius = '2px';
			this.canvas3D.getEl().dom.appendChild(this.label);
		}
		//this.panel3D.rerender();
	},

	afterFirstLayout : function () {
		this.callParent();
	},
});