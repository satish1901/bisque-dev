
function ResourceCard(node, resource) {
    this.resource = resource;
    this.node = node;
    this.fields = {};
};


ResourceCard.prototype.populateFields = function (xnode) {};

ResourceCard.prototype.addField = function (field, attribute, className) {
    this.fields[field] = {attribute: attribute, className:className};
};

ResourceCard.prototype.getSpan = function (field) {
    var cname = this.fields[field].className;
    var attr  = this.fields[field].attribute;
    var max = 15;
    if(attr.length > max){
        var sub = attr.substring(0,max);
        sub += '...';
        var attr = sub;
    }
    return "<span>"+field+ ":  <em class="+cname+">"  + attr + "</em></span>";
};

ResourceCard.prototype.buildHtml = function () {
    var html = "<div class= "+this.cardType+" id="+this.resource+">";
    //html += "<span class=status></span>";

    html += "<span class=resource>"  + this.cardType + "</span>";
    for(var field in this.fields){
        html += this.getSpan(field);
    }
    /*
    html += "<span> module:   <em class=name>"  + this.fields['name'] + "</em></span>";
    html += "<span> status:   <em class=value>" + this.fields['name'] xnode.getAttribute('value') + "</em></span>";
    //html += "<span class=date><span class=counter>"+worker.count+"</span></span>";
    html += "<span> finished: <em class=date>" + xnode.getAttribute('ts') + "</em></span>";
    */
    html += "</div>";

    this.node.rx = this.node.ry = 5;
    this.node.labelType = "html";
    this.node.label = html;
};

ResourceCard.prototype.getUrl = function (resource_uniq) {
	return '/client_service/view?resource=/data_service/' + resource_uniq;
};


function MexCard(node, resource) {
    this.resource = resource;
    this.cardType = 'mex';
	this.node = node;

    ResourceCard.call(this,node, resource);
};

MexCard.prototype = new ResourceCard();

MexCard.prototype.populateFields = function (xnode) {
    this.addField('module', xnode.getAttribute('name'), 'name');
    this.addField('status', xnode.getAttribute('value'), 'value');
    this.addField('finished', xnode.getAttribute('ts').split('T')[0], 'date');
};

MexCard.prototype.getUrl = function (resource_uniq) {
	return '/module_service/' + this.fields['module']['attribute'] + '/?mex=/data_service/' + resource_uniq;
};

function DataSetCard(node, resource) {
    this.resource = resource;
    this.cardType = 'dataset';
	this.node = node;
    ResourceCard.call(this,node, resource);
};

DataSetCard.prototype = new ResourceCard();

DataSetCard.prototype.populateFields = function (xnode) {
    this.addField('name', xnode.getAttribute('name'), 'name');
};


function ImageCard(node, resource) {
    this.resource = resource;
    this.cardType = 'image';
	this.node = node;
    ResourceCard.call(this,node, resource);
};

ImageCard.prototype = new ResourceCard();

ImageCard.prototype.populateFields = function (xnode) {
    this.addField('name', xnode.getAttribute('name'), 'name');
};


function TableCard(node, resource) {
    this.resource = resource;
    this.cardType = 'table';
	this.node = node;
    ResourceCard.call(this,node, resource);
};

TableCard.prototype = new ResourceCard();

TableCard.prototype.populateFields = function (xnode) {
    this.addField('name', xnode.getAttribute('name'), 'name');
};


function PipelineCard(node, resource) {
    this.resource = resource;
    this.cardType = 'dream3d_pipeline';
	this.node = node;
    ResourceCard.call(this,node, resource);
};

PipelineCard.prototype = new ResourceCard();

PipelineCard.prototype.populateFields = function (xnode) {
    this.addField('name', xnode.getAttribute('name'), 'name');
};


function BQFactoryGraph(){
};

BQFactoryGraph.make = function(node, resource){
    this.buffermap = {
        mex      : MexCard,
        dataset  : DataSetCard,
        image    : ImageCard,
        table    : TableCard,
        dream3d_pipeline : PipelineCard,
    };
    card = this.buffermap[node.label];
    if (!card) {
        // for all other types, use ResourceCard
        card = ResourceCard;
    }
    return new card(node,resource);
};


Ext.define('BQ.graphviewer', {
    //extend: 'Ext.container.Container',
    extend : 'BQ.graph.d3',
    alias : 'widget.bq_graphviewer',
    border : 0,
    frame : false,
    initComponent: function() {
        this.numLoaded = 0;
        this.loaded = false;
        this.callParent();
    },
    registerMouseEvents: function(){

    },

    fetchNode : function(resource_uniq, node){
        var me = this;
        var resUniqueUrl = (this.hostName ? this.hostName : '') + '/data_service/' + resource_uniq;
        var gnode = node;
        console.log(node);
        var g = this.g;
        Ext.Ajax.request({
			url : resUniqueUrl,
			scope : this,
			disableCaching : false,
			callback : function (opts, succsess, response) {
				if (response.status >= 400)
					BQ.ui.error(response.responseText);
				else {
					if (!response.responseXML)
						return;
					var xmlDoc = response.responseXML;
                    console.log(xmlDoc);
                    var xnode = xmlDoc.childNodes[0];
                    if(gnode && gnode.card){
                        gnode.card.populateFields(xnode);
                        gnode.card.buildHtml();
                    }
                    me.numLoaded++;
                    if(me.numLoaded === g.nodes().length){
                        me.render(me.group, g);
                        me.forceRefresh(0);
                        me.zoomExtents();
                        var svgNodes = me.group.selectAll("g.node");
                        var svgEdges = me.group.selectAll("g.edgePath");

                        me.highLightProvenance(g, me.resource.resource_uniq, svgNodes, svgEdges, me);
                        me.selection = me.highLightEdges(g, me.resource.resource_uniq, svgNodes, svgEdges);

                        me.fireEvent("loaded", me);
                    }
				}
			},
		});
    },

    fetchNodeInfo : function(){
        var me = this;
        var g = this.g;

        g.nodes().forEach(function(v) {
            var node = g.node(v);
            me.fetchNode(v,node);

            node.rx = node.ry = 5;
            node.padding = 1.5;
        });
    },

    traverse : function(g, i, func, scope){
        var stack = [i];
        var traversed = [];
        for(var i = 0; i < g.nodeCount(); i++)
            traversed[i] = false;

        while(stack.length > 0){
            var nIndex = stack.pop();
            var node = g.node(nIndex);
            var edges = g.nodeEdges(nIndex);
            edges.forEach(function(e, i, a){
                var oIndex = e.v == nIndex ? e.w : e.v;
                if(!traversed[oIndex] && func(oIndex, e, traversed[oIndex])){
                    stack.push(oIndex);
                }
                traversed[nIndex] = true;
            });
        }
    },

    highLightProvenance : function(g, i, svgNodes, svgEdges, scope){
        var nodes = [];
        var edges = [];
        svgEdges.attr('class', 'edgePath');
        svgNodes.attr('class', function(v){return 'node ' + g.node(v).card.cardType});

        scope.traverse(g, i, function(n,e,t){
            if(n == e.v){
                if(!t){
                    nodes.push(n);
                }
                edges.push(e);
                return true;
            }
            return false;
        }, scope);
        scope.traverse(g, i, function(n,e, t){
            if(n == e.w) {
                if(!t)
                    nodes.push(n);

                edges.push(e);
                return true;
            }
            return false;
        }, scope);

        nodes.forEach(function(e,i,a){
            var localNodes = svgNodes
                .filter(function(d){return (d===e) ? this : null;});
            var node = g.node(e);
            var selCls = 'node ' + node.card.cardType + ' watershed';
            localNodes.attr('class', selCls);

        });


        edges.forEach(function(e,i,a){
            var localEdges = svgEdges
                .filter(function(d){return (d.v===e.v && d.w===e.w) ? this : null;});
            localEdges.attr('class', 'edgePathHighlighted');
        });

    },

    highLightEdges : function(g, i, svgNodes, svgEdges){
        var node = g.node(i);
        var nodeEdges = g.nodeEdges(i);
        var localEdgesIn = svgEdges
            .filter(function(d){
                return (d.w === i) ? this : null;});

        var localEdgesOut = svgEdges
            .filter(function(d){
                return (d.v === i) ? this : null;});

        var localNodes = svgNodes
            .filter(function(d){return (d===i) ? this : null;});


        var selCls = 'node ' + node.card.cardType + ' selected';
        localNodes.attr('class', selCls);

        localEdgesOut.attr('class', 'edgePathSelectedOut');
        localEdgesIn.attr('class', 'edgePathSelectedIn');
        return [localNodes,localEdgesIn,localEdgesOut];
    },

    forceRefresh : function(timeOutDuration){
        //unfortunatley there can be a refresh problem, so I refresh the div
        //during animation to enable smooth animation
        var me = this;
        var force = function(){
            var el = me.getEl().dom;
            el.style.cssText += ';-webkit-transform:rotateZ(0deg)';
            el.offsetHeight;
            el.style.cssText += ';-webkit-transform:none';

        };

        if(timeOutDuration === 0){
            force();
        }

        else{
            var refreshing = true;
            var refreshTimer = function(){
                requestAnimationFrame(function() {
                    if(refreshing){
                        force();
                        refreshTimer();
                    }
                });
            };
            refreshTimer();
            setTimeout(
                callback(this, function () {
			        refreshing = false;
                }), timeOutDuration);
        }
    },

    getTranslation : function(d3node){
        var trans = d3node.attr("transform");
        var ts = trans.indexOf("(");
        var te = trans.indexOf(")");
        trans = trans.slice(ts + 1, te);
        trans = trans.split(",");
        trans = [parseFloat(trans[0]),parseFloat(trans[1])];
        return trans;
    },

    zoomExtents : function(){
        var me = this;
        var el = this.getEl().dom;

        var margin = 50;
        var w = this.getWidth()  - margin;
        var h = this.getHeight() - margin;

        var bbox = this.group.selectAll("g").node().getBBox();
        var bbw = bbox.width;
        var bbh = bbox.height;
        var min = w/bbw < h/bbh ? w/bbw : h/bbh;
        var trans = [(w-min*bbw)/2 + margin/2, (h-min*bbh)/2 + margin/2];
        this.zoom.scale(min);
        this.scale = min;
        this.group
            .transition()
            .duration(750)
            .attr("transform", "translate(" + trans + ")" +
                        "scale(" + min + ")");
            this.forceRefresh(760);

    },

    zoomToCurrent : function(){
        if(!this.selection){
            this.zoomExtents();
            return;
        }
        var me = this;
        var el = this.getEl().dom;
        var bbox = this.group.selectAll("g").node().getBBox();
        var bboxSel =  this.selection[0].node().getBBox();

        var w = this.getWidth();
        var h = this.getHeight();

        var bbw = bboxSel.width;
        var bbh = bbox.height;

        var bbsw = bboxSel.width;
        var bbsh = bboxSel.height;
        //var bby = bboxSel.y;
        var elTrans = this.getTranslation(this.selection[0]);

        var min = w/bbw < h/bbh ? w/bbw : h/bbh;
        var mins = bbw/bbsw < bbh/bbsh ? bbw/bbsw : bbh/bbsh;
        var newScale = 2.0*mins;
        if(newScale < this.scale) newScale = this.scale;

        var trans = [w/2 - newScale*elTrans[0],
                     h/2 - newScale*elTrans[1]];

        this.zoom.scale(newScale);
        this.scale = newScale;
        this.group
            .transition()
            .duration(750)
            .attr("transform", "translate(" + trans + ")" +
                        "scale(" + newScale + ")");
        this.forceRefresh(760);

    },

    buildGraph : function(nodes, edges, members){
        var me = this;
        var data1 = this.data;

        var svg = this.svg;
        var color = d3.scale.category20();


        var window = this.svg
            .insert("rect", "g")
            .attr("width", "100%")
            .attr("height","100%")
            .attr("fill", "rgb(200,200,200)")
            .attr("opacity", 0.5);

        var g = new dagreD3.graphlib.Graph()
            .setGraph({})
            .setDefaultEdgeLabel(function() {return {}; });

        this.g = g;

        nodes.forEach(function(e,i,t){
            var t = e.getAttribute('type');
            var val = e.getAttribute('value');
            g.setNode(val, {label: t});
        });

        edges.forEach(function(e,i,a){
            var val = e.getAttribute('value').split(':');
            g.setEdge(val[0], val[1],{
                lineInterpolate: 'basis'
            });
        });

        members.forEach(function(e,i,a){
            var val = e.getAttribute('value').split(':');
            g.setEdge(val[0], val[1],{
            	style: "stroke-dasharray: 5, 5; fill: none;",
            	arrowhead: "undirected"
            });
        });

/* Le Mis data
        this.graph.nodes.forEach(function(e,i,a){
            //g.setNode(i, {label: e["name"], class: e["group"]});
            g.setNode(i, {label: e["name"]});

        });

        this.graph.links.forEach(function(e,i,a){
            g.setEdge(e["source"], e["target"],{
                lineInterpolate: 'basis'
            });
        });
*/
        g.nodes().forEach(function(v) {
            var node = g.node(v);
            console.log(v, g.node(v));
            // Round the corners of the nodes
            node.rx = node.ry = 5;
            node.padding = 0.0;
            node.card = BQFactoryGraph.make(node, v);
        });


        g.graph().rankdir = "LR";
        g.graph().nodeSep = 20;
        g.graph().edgeSep = 10;
        g.graph().rankSep = 20;
        // Create the renderer
        this.render = new dagreD3.render();

        // Set up an SVG group so that we can translate the final graph.
        //var svgGroup = svg.append("g");
        // Set up zoom support

        var svgGroup = this.group;
        this.trans = [0,0];

        var wheel = false;
        var smx, smy;
        this.zoom = d3.behavior.zoom().on("zoom", function() {

            var w = me.getWidth();
            var h = me.getHeight();
            var bbox = me.group.selectAll("g").node().getBBox();
            var bbw = bbox.width;
            var bbh = bbox.height;

            var dx = d3.event.sourceEvent.movementX;
            var dy = d3.event.sourceEvent.movementY;
            var mx = d3.event.sourceEvent.offsetX;
            var my = d3.event.sourceEvent.offsetY;
            var scale = d3.event.scale;

            var ctrans = me.getTranslation(me.group);
            ctrans[0] += dx;
            ctrans[1] += dy;

            //there is some drifting going on, so wheel lock the
            //if(!wheel){
            smx = (mx - ctrans[0]);
            smy = (my - ctrans[1]);
            smx = smx*scale/me.scale - smx;
            smy = smy*scale/me.scale - smy;
            me.scale = scale;
            //}
            //console.log(smx/scale, smy/scale, me.group.selectAll("g").node().getBBox());
            wheel = (d3.event.sourceEvent.type === "wheel");
            if(wheel){
                //var trans = [me.trans[0],[me.trans[1]];
                ctrans[0] -= smx;
                ctrans[1] -= smy;
                wheel = true;
            }

            svgGroup.attr("transform", "translate(" + ctrans + ")" +
                          "scale(" + scale + ")");


            //force refresh:
            me.forceRefresh(0);
        });
        this.svg.call(this.zoom);

        // Run the renderer. This is what draws the final graph.
        this.render(svgGroup, g);

        var svgNodes = svgGroup.selectAll("g.node");
        var svgEdges = svgGroup.selectAll("g.edgePath");

        this.selection;
        svgGroup.selectAll("g.node")
            //.attr("title", function(v) { return styleTooltip(v, g.node(v).description) })
            .on("mousedown", function(d){
                if(me.selection){
                    me.selection[0].attr('class', 'node ' + g.node(d).card.cardType);
                    me.selection[1].attr('class', 'edgePath');
                    me.selection[2].attr('class', 'edgePath');
                    selection = [];
                }
                me.highLightProvenance(g, d, svgNodes, svgEdges, me);
                me.selection = me.highLightEdges(g, d, svgNodes, svgEdges);
                //force refresh:
                me.forceRefresh(0);
                var div = this.getElementsByTagName('div')[1];
                var mouse = d3.event;
                if(mouse.button === 0){
                    me.fireEvent('mousedown', d, div, me);
                    //me.zoom.interrupt();
                }
                if(mouse.button === 2){
                    me.fireEvent('context', d, div, me);
                    //me.zoom.interrupt();
                }
            });

        /*
        svgGroup.selectAll("g.node")
            .attr("title", function(v) {
                return "tooltip";
                return styleTooltip(v, g.node(v).description)
            }).each(function(v) { $(this).tipsy({ gravity: "w", opacity: 1, html: true }); });;
            */

        svgGroup.selectAll("g.node")
            .attr("class", function(v) {
                return 'node ' + g.node(v).card.cardType;
            });

        //this.zoomExtents();
    },

    buildGraphForce : function(){
        var me = this;
        var data1 = this.data;

        var svg = this.svg;
        var color = d3.scale.category20();

        var window = this.svg
            .append("rect")
            .attr("width", "100%")
            .attr("height","100%")
            .attr("fill", "rgb(200,200,200)")
            .attr("opacity", 0.5);

        this.force = d3.layout.force()
            .charge(-120)
            .linkDistance(30)
            .linkStrength(2)
            .size([this.getWidth(), this.getHeight()]);

        this.force
            .nodes(this.graph.nodes)
            .links(this.graph.links)
            .start();

        var link = svg.selectAll(".link")
            .data(this.graph.links)
            .enter().append("line")
            .attr("class", "link")
            .style("stroke", "rgb(128,128,128)")
            .style("stroke-width", function(d) { return Math.sqrt(d.value); });

        var node = svg.selectAll(".node")
            .data(this.graph.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", 5)
            .style("fill", function(d) { return color(d.group); })
            .call(this.force.drag);

        node.append("title")
            .text(function(d) { return d.name; });

        this.force.on("tick", function() {
            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node.attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });
        });

    },

    findInterval : function(me) {
    },

    updateScale : function(){
    },

    redraw : function(){
    },

    updateGraph : function(dp){
    },

    afterRender : function() {
        this.callParent();
        this.gridSizeX = 1;
        this.gridSizeY = 1;
    },

    afterFirstLayout : function() {
        this.callParent();
        //this.initBrush();
        //this.buildGraph();

    },

});

Ext.define('BQ.viewer.Graph.Panel', {
	alias : 'widget.bq_graphviewer_panel',
	extend : 'Ext.panel.Panel',
	//border : 0,
	cls : 'bq-graph-panel',
	layout : 'fit',

    zoomExtents: function(){
        this.graphView.zoomExtents();
    },

    zoomToCurrent: function(){
        this.graphView.zoomToCurrent();
    },

    fetchGraphData : function(){
        var resUniqueUrl = (this.hostName ? this.hostName : '') +
            '/graph?query=' + this.resource.resource_uniq;
        Ext.Ajax.request({
			url : resUniqueUrl,
			scope : this,
			disableCaching : false,
			callback : function (opts, succsess, response) {
				if (response.status >= 400)
					BQ.ui.error(response.responseText);
				else {
					if (!response.responseXML)
						return;
					var xmlDoc = response.responseXML;
                    var graph = xmlDoc.childNodes[0];

                    console.log(graph);
                    this.graphView.graph = this.graph;

                    var nodes = BQ.util.xpath_nodes(xmlDoc, "graph/node");
                    var edges = BQ.util.xpath_nodes(xmlDoc, "graph/edge");
                    var members = BQ.util.xpath_nodes(xmlDoc, "graph/member");
                    this.graphView.buildGraph(nodes, edges, members);
                    this.graphView.fetchNodeInfo();
                    /*
                    for(var prop in graph.childNodes){
                        //var nodes = BQ.util.xpath_nodes(xmlDoc, "//tag[@name='value']/@value");
                        if(graph.childNodes.hasOwnProperty(prop)){
                            var child = graph.childNodes[prop];
                            //var val = BQ.util.xpath_nodes(xmlDoc, "//tag[@name='value']/@value")
                            var t = child.getAttribute('type');
                            alert(prop + " = " + value);
                        }
                    }*/				}
			},
		});
    },



    initComponent: function(){
        var me = this;

        this.graphView = Ext.create('BQ.graphviewer', {
            resource : this.resource,
            listeners:{
                loaded: function(res, div, comp){
                    me.setLoading(false);
                },
                context: function(res,div,comp){
                    me.fireEvent('context',res, div, comp);
                },
                mousedown: function(res,div,comp){
                    me.fireEvent('mousedown',res, div, comp);
                }
            }
        });

        this.items = [ this.graphView, {
			xtype : 'component',
			itemId : 'button-extents',
			autoEl : {
				tag : 'span',
				cls : 'control zoomextents',
			},

			listeners : {
				scope : this,
				click : {
					element : 'el', //bind to the underlying el property on the panel
					fn : this.zoomExtents,
                    scope: me
				},
			}
        }, {
			xtype : 'component',
			itemId : 'button-tocurrent',
			autoEl : {
				tag : 'span',
				cls : 'control zoomtocurrent',
			},
			listeners : {
				scope : this,
				click : {
					element : 'el', //bind to the underlying el property on the panel
					fn : this.zoomToCurrent,
                    scope: me
				},
			},
		}];
        this.setLoading(true);
		this.callParent();
    },

    afterFirstLayout : function(){
        this.fetchGraphData();
        this.callParent();
    }
});
//--------------------------------------------------------------------------------------
// Dialogue Box
//--------------------------------------------------------------------------------------

Ext.define('BQ.viewer.graphviewer.Dialog', {
	extend : 'Ext.window.Window',
	alias : 'widget.bq_graphviewer_dialog',
	//border : 0,
	layout : 'fit',
	modal : true,
	border : 0,
	width : '75%',
	height : '75%',
	buttonAlign : 'center',
	autoScroll : true,
	title : 'volume viewer',

	constructor : function (config) {
		config = config || {};

		Ext.apply(this, {
			//title : 'Move for ' + config.resource.name,
			items : [{
				xtype : 'bq_graphviewer_panel',
                resource: config.resource,
                //xtype: 'bq_graphviewer',
				//hostName : config.hostName,
				//resource : config.resource
			}],
		}, config);

		this.callParent(arguments);
		this.show();
	},
});

/*
function showGraphTool(volume, cls) {
	//renderingTool.call(this, volume);

    this.name = 'autoRotate';
	this.base = renderingTool;
    this.base(volume, this.cls);
};

showGraphTool.prototype = new renderingTool();

showGraphTool.prototype.init = function(){
    //override the init function,
    var me = this;
    // all we need is the button which has a menu
    this.createButton();
};

showGraphTool.prototype.addButton = function () {
    this.volume.toolMenu.add(this.button);
};

showGraphTool.prototype.createButton = function(){
    var me = this;

    this.button = Ext.create('Ext.Button', {
        width : 36,
        height : 36,
        cls : 'volume-button',
		handler : function (item, checked) {
            Ext.create('BQ.viewer.graphviewer.Dialog', {
                title : 'gl info',
                height : 500,
                width : 960,
                layout : 'fit',
            }).show();
		},
        scope : me,
    });

    this.button.tooltip = 'graph viewer temp';
};
*/
