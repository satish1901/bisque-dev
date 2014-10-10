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
	var scale = this.volume.getRescale().clone();
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

};

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
        gobject  : this.PointBuffer,
        point    : this.PointBuffer,
        rectangle: this.PolyBuffer,
        square   : this.PolyBuffer,
        ellipse  : this.PolyBuffer,
        circle   : this.PolyBuffer,
        polygon  : this.PolyBuffer,
        polyline : this.LineBuffer,
        line     : this.LineBuffer,
        label    : this.PointBuffer,
    }
};

BQFactory3D.ftormap = {
    point     : function(g) { return g;},
    label     : function(g) { return g;},
    gobject   : function(g) { return g;},
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
    square    : function(g) {
        var p0 = g.vertices[0];
        var p1 = g.vertices[1];
        var dx = g.vertices[1].x - g.vertices[0].x;
        var vertices = [{x: p0.x,    y: p0.y,    z: p0.z},
                        {x: p0.x+dx, y: p0.y,    z: p0.z},
                        {x: p0.x+dx, y: p0.y+dx, z: p0.z},
                        {x: p0.x,    y: p0.y+dx, z: p0.z}
                       ];
        return  {vertices: vertices, color: g.color};
    },
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

        var u = {x: dp0.x/r0, y: dp0.y/r0, z: dp0.z/r0};
        var v = {x:-u.y, y: u.x, z: u.z};

        var N = 16;
        var phase = 0;
        var npi = 2.0*Math.PI/N;

        for(var i = 0; i < 16; i++){
            vertices.push({x: p0.x + r0*u.x*Math.cos(phase) + r1*v.x*Math.sin(phase),
                           y: p0.y + r0*u.y*Math.cos(phase) + r1*v.y*Math.sin(phase),
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
    var buffer = BQFactory3D.buffermap[g.type];
    var ftor   = BQFactory3D.ftormap[g.type];
    buffer.build(g, ftor);
}


function gObjectTool(volume, cls) {
	//renderingTool.call(this, volume);
	this.cls = 'gButton';
    this.base = renderingTool;
    this.base(volume, this.cls);
    this.gobjects = this.volume.phys.image.gobjects;
};

gObjectTool.prototype = new renderingTool();

gObjectTool.prototype.addUniforms = function(){

};

gObjectTool.prototype.toggle = function(button){

	if (button.pressed) {
		this.setVisible(true);
	} else {
		this.setVisible(false);
	}
	this.rescalePoints();
    this.base.prototype.toggle.call(this,button);

	this.volume.rerender();
};

gObjectTool.prototype.buildCube = function (sz) {
	var geometry = new THREE.BufferGeometry();
	geometry.addAttribute('index', new THREE.BufferAttribute(new Uint32Array(36), 1));
	geometry.addAttribute('position', new THREE.BufferAttribute(new Float32Array(8 * 3), 3));

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

};

gObjectTool.prototype.rescalePoints = function () {
	this.currentSet.points.rescale();
	this.currentSet.polylines.rescale();
	this.currentSet.polygons.rescale();
	//console.log(this.points);
};

gObjectTool.prototype.setVisible = function (vis) {
	var t = this.volume.currentTime;
	this.currentSet = this.gObjectBuffers[t];
	for (var item in this.currentSet) {
		if (!item)
			continue;
		var curMesh = this.currentSet[item].mesh;
		curMesh.visible = vis;
	}
};

gObjectTool.prototype.updateScene = function () {
	var t = this.volume.currentTime;

	if (!this.currentSet)
		this.currentSet = {};
	for (var item in this.currentSet) {
		if (!item)
			continue;

		var curMesh = this.currentSet[item].mesh;
		if (curMesh)
			this.volume.sceneData.remove(curMesh); // remove current point set
	}
	this.currentSet = this.gObjectBuffers[t];
	for (var item in this.currentSet) {
		if (!item)
			continue;
		var curMesh = this.currentSet[item].mesh;
		if (curMesh) {
			this.volume.sceneData.add(curMesh); // remove current point set
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
};

gObjectTool.prototype.initBuffers = function(){
    var t = this.volume.currentTime;
	if (this.gObjectBuffers[t]) { //load points in lazily
		this.updateScene();
		return;
	}

	this.gObjectBuffers[t] = {};

	var pBuffer = new polyBuffer(this.volume);
	pBuffer.material = this.polyShaderMaterial;
	this.gObjectBuffers[t].polygons = pBuffer;

	var lBuffer = new lineBuffer(this.volume);
	lBuffer.material = this.polyShaderMaterial;
	this.gObjectBuffers[t].polylines = lBuffer;

	var cBuffer = new pointBuffer(this.volume);
	cBuffer.material = this.pointShaderMaterial;
	this.gObjectBuffers[t].points = cBuffer;

	this.gObjectBuffers[t].polygons = pBuffer;
	//todo: I think we want to build buffers for every frame right here,
	//      rather than load lazily... if we have 10 million gobjects to
	//      sift through, then this will get pretty slow
    BQFactory3D.set(cBuffer, lBuffer, pBuffer);
};

gObjectTool.prototype.loadGObjects = function () {
    var t = this.volume.currentTime;
    this.initBuffers();
    var tStack = [this];
    while(tStack.length > 0){
        var context = tStack[tStack.length-1];
		for (var i = 0; i < context.gobjects.length; i++) {
			var g = context.gobjects[i];
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
};

gObjectTool.prototype.initControls = function(){

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
			this.volume.rerender();
		},
		scope : me,
	});

	var me = this;
	this.plane = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000, 8, 8),
				                new THREE.MeshBasicMaterial({
					                color : 0x808080,
					                opacity : 0.25,
					                transparent : true,
					                wireframe : true
				                }));
	this.plane.visible = false;

	this.volume.scene.add(this.plane);
	//this.volume.sceneVolume.scene.add(this.lightObject);

	var onAnimate = function () {
		if (this.volume.sceneData) {
			var panel = this.volume;
			//move this to background plug-in
			var camPos = this.volume.canvas3D.camera.position;
			this.currentSet.points.sortParticles(camPos);
			panel.canvas3D.renderer.clearTarget(this.accumBuffer0,
				                                true, true, true);
			var buffer = this.accumBuffer0;
			var bufferColor = this.accumBuffer1;

			this.pointShaderMaterial.uniforms.USE_COLOR.value = 0;
			this.polyShaderMaterial.uniforms.USE_COLOR.value = 0;
			this.backGroundShaderMaterial.uniforms.USE_COLOR.value = 0;
			//this.useColor = 0;
			panel.canvas3D.renderer.render(this.volume.sceneData,
				                           panel.canvas3D.camera,
				                           this.depthBuffer);

			this.pointShaderMaterial.transparent = true;
			this.pointShaderMaterial.uniforms.USE_COLOR.value = 1;
			this.polyShaderMaterial.uniforms.USE_COLOR.value = 1;
			this.backGroundShaderMaterial.uniforms.USE_COLOR.value = 1;
			panel.canvas3D.renderer.render(panel.sceneData,
				                           panel.canvas3D.camera,
				                           this.colorBuffer);

			panel.sceneVolume.setUniformNoRerender('BACKGROUND_DEPTH', this.depthBuffer, false);
			panel.sceneVolume.setUniformNoRerender('BACKGROUND_COLOR', this.colorBuffer, false);
		}
	};

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
	};

	var onMouseMove = function (event) {
		event.preventDefault();
		if (this.points.visible === false)
			return;
        var canvas = this.volume.canvas3D;
		var width = canvas.getWidth();
		var height = canvas.getHeight();
		var cx = canvas.getX();
		var cy = canvas.getY();
		var x = ((event.clientX - cx) / width) * 2 - 1;
		var y =  - ((event.clientY - cy) / height) * 2 + 1;

		var camera = canvas.camera;

		var vector = new THREE.Vector3(x, y, 0.5);
		canvas.projector.unprojectVector(vector, camera);
		this.raycaster.ray.set(camera.position, vector.sub(camera.position).normalize());

		var intersections = this.raycaster.intersectObjects(this.pointclouds);
		intersection = (intersections.length) > 0 ? intersections[0] : null;
		if (intersection !== null) {
			//this.sphere.position.copy( intersection.point );
			var gindex = intersections[0].object.geometry.getAttribute('index').array;
			var pos = canvas.projector.projectVector(intersection.point.clone(), camera);
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
			canvas.getEl().dom.appendChild(this.label);
		}
		//this.panel3D.rerender();
	};


	this.volume.canvas3D.getEl().dom.addEventListener('mousemove', onMouseMove.bind(this), true);
	this.volume.canvas3D.getEl().dom.addEventListener('mouseup', onMouseUp.bind(this), true);
	this.volume.canvas3D.getEl().dom.addEventListener('mousedown', onMouseDown.bind(this), true);

	var spriteTex = THREE.ImageUtils.loadTexture('/js/volume/icons/dot.png');
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
		vertexShader : new DepthShader({
            depth: false,
            type: 'vertex',
        }).getSource(),
		fragmentShader : new DepthShader({
            depth: false,
            type: 'fragment',
        }).getSource(),
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
		vertexShader : new DepthShader({
            depth: true,
            type: 'vertex',
        }).getSource(),
		fragmentShader : new DepthShader({
            depth: true,
            type: 'fragment',
        }).getSource(),
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
        /*
		vertexShader : vertDepth,
		fragmentShader : fragDepthBack,
        */
        vertexShader : new DepthShader({
            depth: true,
            type: 'vertex',
        }).getSource(),
		fragmentShader : new DepthShader({
            depth: true,
            type: 'fragment',
            back: true,
        }).getSource(),
		side : THREE.BackSide,
		//transparent: true
	});

	this.gObjectSets = new Array();
	this.gObjectBuffers = new Array();
	this.loadGObjects();

	this.volume.on('time', this.loadGObjects, me);
	this.volume.on('scale', this.rescalePoints, me);

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
	this.volume.sceneData.add(backGround);

	this.addUniforms();
	this.isLoaded = true;
	this.volume.canvas3D.animate_funcs[0] = callback(this, onAnimate);

	this.depthBuffer
		= new THREE.WebGLRenderTarget(this.volume.getWidth(), this.volume.getHeight(), {
			minFilter : THREE.LinearFilter,
			magFilter : THREE.NearestFilter,
			format : THREE.RGBAFormat
		});
	this.colorBuffer
		= new THREE.WebGLRenderTarget(this.volume.getWidth(), this.volume.getHeight(), {
			minFilter : THREE.LinearFilter,
			magFilter : THREE.NearestFilter,
			format : THREE.RGBAFormat
		});

	this.updateScene();
	this.items = [this.lighting];
};
