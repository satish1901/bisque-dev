

function histogramD3(histogram, gamma, svg, component){
    this.histogram = histogram;
    this.gamma = gamma;
    this.svg = svg;
    this.component = component;
    this.channelFill = {r: [255,0,0],
                        g: [0,255,0],
                        b: [0,0,255]};
    this.init();
};

histogramD3.prototype.getColor = function(channel, opacity){
    var c = this.channelFill[channel];
    c[3] = opacity;
    return "rgba(" + c.join(",") + ")";
};

histogramD3.prototype.getWidth = function(){
    return this.component.getWidth();
};

histogramD3.prototype.getHeight = function(){
    return this.component.getHeight();
};

histogramD3.prototype.init = function(){
    var me = this;

    for (chan in this.histogram){
        var channel = this.histogram[chan];
        if (channel.length == 0) continue;
        var max = 0;
        var min = 999;
        channel.forEach(function(e,i,a){
            var loge = e; //Math.log(e);
            max = max < loge ? loge : max;
            min = min > loge ? loge : min;
        });
        var logd = function(d){ return d >  0? Math.log(d) : 0;};
        var l = this.histogram[chan].length;
        var h = this.getHeight();
        var w = this.getWidth();

        var data = this.histogram[chan];
        var buffer = 0.025*this.getHeight();
        this.xl = d3.scale.linear().domain([0, 256]).range([buffer, me.getWidth()-buffer]);
        this.yl = d3.scale.linear()
            .domain([d3.min(data, logd),d3.max(data, logd)])
            .range([buffer, me.getHeight()- buffer]);

        this.bar = false;
        if(this.bar){
            this.svg.append("g")
                .attr("class", "histogram_" + chan);
            //.attr("transform", "translate(" + me.xl(1) + "," + (-h) + ")scale(-1,-1)")
            //.attr("transform", "translate(" + me.xl(1) + "," + (h - 20) + ")scale(-1,-1)")
        }
        else{

            this.yl = d3.scale.linear()
                .domain([d3.min(data, logd),d3.max(data, logd)])
                .range([me.getHeight()- buffer,buffer]);

            this.area = d3.svg.area()
                .x(function(d,i) { return me.xl(i); })
                .y0(this.getHeight()-buffer)
                .y1(function(d) { return me.yl(logd(d)); });
            this.svg.append("svg:path")
                .datum(this.histogram[chan])
                .attr("class", "histogram_" + chan)
                .attr("fill",   this.getColor(chan, 0.5))
                .attr("d", this.area);
        }

    }
};

histogramD3.prototype.redraw = function(){
    var me = this;
    for (chan in this.histogram){
        var channel = this.histogram[chan];
        if (channel.length == 0) continue;

        var l = this.histogram[chan].length;
        var w = this.getWidth();
        var data = this.histogram[chan];
        var buffer = 0.025*this.getHeight();
        var logd = function(d){ return d >  0? Math.log(d) : 0;};
        this.xl = d3.scale.linear().domain([0, 256]).range([buffer, me.getWidth()-buffer]);
        this.yl = d3.scale.linear()
            .domain([d3.min(data, logd),d3.max(data, logd)])
            .range([buffer, me.getHeight()- buffer]);
        if(this.bar){
            var group = this.svg.select("g.histogram_" + chan)
                .selectAll("rect")
                .data(this.histogram[chan]);
            //update
            group
                .attr("x", function(d,i) {return me.xl(i);})
                .attr("y", function(d,i) {return me.getHeight()-buffer - me.yl(logd(d));})
                .attr("width", function(d,i) { return w/l; })
                .attr("height", function(d,i) {return me.yl(logd(d)); })
                .attr("fill",   this.getColor(chan, 0.5));
            //add
            group
                .enter().append("svg:rect")
                .attr("x", function(d,i) {return me.xl(i);})
                .attr("y", function(d,i) {return me.getHeight()-buffer - me.yl(logd(d));})
                .attr("width", function(d,i) { return w/l; })
                .attr("height", function(d,i) { return console.log(d, me.yl(logd(d))); me.yl(logd(d)); })
                .attr("fill",   this.getColor(chan, 0.5));
            //remove
            group.exit().remove();
        } else {
            this.yl = d3.scale.linear()
                .domain([d3.min(data, logd),d3.max(data, logd)])
                .range([me.getHeight()- buffer,buffer]);
            this.area = d3.svg.area()
                .x(function(d,i) { return me.xl(i); })
                .y0(this.getHeight()-buffer)
                .y1(function(d) { return me.yl(logd(d)); })
                .interpolate("step-before");
            this.svg.select("path.histogram_" + chan).transition()
                .attr("d", this.area);

        }

    }
};

Ext.define('BQ.graph.d3', {
    //extend: 'Ext.container.Container',
    extend : 'Ext.Component',
    alias : 'widget.d3_component',
    border : 0,
    frame : false,

    initD3 : function(){
        var me = this;

        function nozoom() {
            d3.event.preventDefault();
        }

        var thisDom = this.getEl().dom;
        this.handle = Math.floor(99999*Math.random());
        this.svg = d3.select('#' + thisDom.id)
            .on("touchstart", nozoom)
            .on("touchmove", nozoom)
            .append("svg:svg")
            .attr("id", "ext_svg-"+this.handle)
            .attr("width", "100%")
            .attr("height","100%")
            .append("svg:g")
            .on("mousedown", function(){me.findInterval(me); me.fireEvent("mousedown");})
            .on("mouseup", function(){me.fireEvent("mouseup");});

        this.svg
            .append("rect")
            .attr("id", "background-"+this.handle)
            .attr("width", "100%")
            .attr("height","100%");

    },

    setBackgroundColor : function(color){
        //takes a string to set the background color
        this.svg.select("#background-" +this.handle)
            .attr("fill", color);
    },

    redraw : function(){
    },

    afterRender : function() {
        this.callParent();
    },

    afterFirstLayout : function() {
        this.callParent();
        this.addListener('resize', this.onresize, this);
        this.initD3();
    },

    onresize : function(){
        this.redraw();
    }
});


Ext.define('BQ.volume.transfer.graph', {
    //extend: 'Ext.container.Container',
    extend : 'BQ.graph.d3',
    alias : 'widget.bq_volume_transfer_graph',
    border : 0,
    frame : false,


    initBrush: function(){
        var me = this;
        var brush = d3.svg.brush()
            .x(me.xScale)
            .extent([0, 100])
            .on("brushstart", brushstart)
            .on("brush", brushmove)
            .on("brushend", brushend);

        this.brush = this.svg.append("g")
            .attr("class", "brush")
            .call(brush);
        this.brush
            .selectAll("rect")
            .attr("height", 20);

        me.selected = [];
        function brushstart() {
            //svg.classed("selecting", true);
        }

        function brushmove() {
            var s = d3.event.target.extent();

            var circle = me.svg.selectAll("circle")
                .data(me.data, function(d){return d.id;});
            me.data.forEach(function(d,i,a){
                if(d.offset >= s[0] && d.offset <= s[1])
                    d.selected = true;
                else
                    d.selected = false;
            });
            circle.attr("fill", function(d){
                return (d.offset >= s[0] && d.offset <= s[1]) ? "rgb(128,0,0)" : "rgb(128,128,128)";});
        }

        function brushend() {
            me.selected = [];
            me.data.forEach(function(d,i,a){
                if(d.selected)
                    me.selected.push(i);
            });
            console.log(me.selected);
        }
    },

    initCrossHairs : function(){
        var me = this;
        var xMouse = this.svg.append("svg:line")
            .attr("stroke", "rgb(128,128,128)")
            .attr("x1", "0%")
            .attr("x2", "0%")
            .attr("y1", "0%")
            .attr("y2", "100%");

        var yMouse = this.svg.append("svg:line")
            .attr("stroke", "rgb(128,128,128)")
            .attr("x1", "0%")
            .attr("x2", "100%")
            .attr("y1", "0%")
            .attr("y2", "0%");

        var xText = this.svg.append("svg:text")
            .attr("fill", "rgb(128,128,128)")
            .attr("y", "2%")
            .attr("dy", ".71em")
            .attr("text-anchor", "right");

        var yText = this.svg.append("svg:text")
            .attr("fill", "rgb(128,128,128)")
            .attr("x", "2%")
            .attr("dy", ".71em")
            .attr("text-anchor", "right");

        this.svg
            .on("mousemove", function(){
                var xp = d3.event.clientX - me.getX();
                var yp = d3.event.clientY - me.getY();
                var offset = me.xScale.invert(xp);
                var alpha  = me.yScale.invert(yp);

                if(me.snap){
                    offset = Math.floor(offset/me.gridSizeX + 0.5)*me.gridSizeX;
                    alpha = Math.floor( alpha/me.gridSizeY  + 0.5)*me.gridSizeY;
                }

                xMouse
                    .attr("x1", me.xScale(offset))
                    .attr("x2", me.xScale(offset));
                yMouse
                    .attr("y1", me.yScale(alpha))
                    .attr("y2", me.yScale(alpha));

                xText
                    .attr("x", me.xScale(offset) + 2)
                    .text(offset.toFixed(4));
                yText
                    .attr("y", me.yScale(alpha) + 2)
                    .text(alpha.toFixed(4));
            });
    },

    buildGraph : function(){
        var me = this;
        var data1 = this.data;

        var maxval = 0,
        sampsize = 0;
        var label_array = new Array(),
        val_array1 = new Array();

        var selected = this.data[0],
        dragged = null;
        var vis, x, y, w, h;
        //if(!this.svg){

        //append the gradient div
        this.gradient = this.svg.append("svg:defs")
            .append("svg:linearGradient")
            .attr("id", "gradient")
            .attr("x1", "0%")
            .attr("y1", "0%")
            .attr("x2", "100%")
            .attr("y2", "0%")
            .attr("spreadMethod", "pad");

        w = this.getWidth(),
        h = this.getHeight(),
        this.pad = 10,

        this.updateScale();

        var me = this;

        var transform = ["", "-webkit-", "-moz-", "-ms-", "-o-"]
            .reduce(function(p, v) { return v + "transform" in document.body.style ? v : p; }) +
            "transform";

        this.drag = d3.behavior.drag()
            .on("dragstart", dragstarted)
            .on("drag", ondrag)
            .on("dragend", dragended);

        function dragstarted(d) {
            //fooled you! the point keeps jumping from the cursor... ha ha ha, only if you're windows
            if(Math.random() > 0.75 && Ext.isWindows){
                this.fooled = true;
                d.alpha += (0.5 - Math.random())*0.25;
                d.offset +=(0.5 - Math.random())*5;
                d3.select(this).transition()
                    .ease("elastic")
                    .duration(500)
                    .attr("r", 6)
                    .attr("cx", function(d) { return  me.xScale(d.offset); })
                    .attr("cy", function(d) { return  me.yScale(d.alpha); });

                redraw();
                return 0;
            }
            this.fooled = false;
            this.parentNode.appendChild(this);
/*
            var chk = me.svg.select("#circle_"+ me.clicked)
                .attr("fill",function(d){return d.selected ? "rgb(255,0,0)" : "rgb(255,255,255)";});
*/
            //console.log(chk);
            me.clicked = d.id;
            d3.select(this).transition()
                .ease("elastic")
                .duration(500)
                .attr("r", 6)
                .attr("fill",function(d){return d.selected ? "rgb(255,0,0)" : "rgb(255,255,255)";});

            //this.brush
            //    .attr("height", 20);

        }

        function ondrag(d, i) {
            if(this.fooled) return;

            var N = me.data.length;
            var oprev = d.id == 0     ? 0                 : me.data[d.id-1].offset;
            var onext = d.id == N - 1 ? me.data[N-1].offset : me.data[d.id+1].offset;
            var xp = d3.event.x;
            var yp = d3.event.y;

            //me.clicked = d.id;
            if(d.id != 0 && d.id != N - 1){
                var oprime = me.xScale.invert(xp);
                oprime = oprime > onext ? onext : oprime;
                oprime = oprime < oprev ? oprev : oprime;
                //console.log(oprime, Math.floor(oprime/me.gridSizeX)*me.gridSizeX, me.gridSizeX);
                if(me.snap)
                    oprime = Math.floor(oprime/me.gridSizeX + 0.5)*me.gridSizeX;
                d.offset = oprime;

                d3.select(this)
                    .attr("cx", function(d) { return  me.xScale(d.offset); });
            }

            var alpha  = me.yScale.invert(yp);

            alpha = alpha > 1 ? 1 : alpha;
            alpha = alpha < 0 ? 0 : alpha;

            if(me.snap)
                alpha = Math.floor(alpha/me.gridSizeY + 0.5)*me.gridSizeY;
            d.alpha = alpha;
            d3.select(this)
                .attr("cy", function(d) { return  me.yScale(d.alpha); });

            me.gradient.select("#stop_"+d.id)
                .attr("offset",function(d){return d.offset + "%";});

            redraw();
            me.fireEvent('change', me);
        }

        function dragended() {
            d3.select(this).transition()
                .ease("elastic")
                .duration(500)
                .attr("r", 3)
                .attr("fill",function(d){return d.selected ? "rgb(128,0,0)" : "rgb(128,128,128)";});
        }



        this.histogramSvg = new histogramD3(this.histogram, this.gamma, this.svg, this);

        this.svg.append("svg:path")
            .datum(this.data)
            .attr("class", "transfer")
            .attr("fill", "url(#gradient)")
            .attr("stroke", "rgba(0,0,0,0.75)")
            .attr("stroke-width", 2)
            .attr("d", this.area)
            .attr("opacity", "0.7");

        this.initCrossHairs();
        this.initBrush();



        function redraw(){
            var chck = me.svg.select("path.transfer").attr("d", me.area);
        }
        this.updateGraph();
    },

    findInterval : function(me) {
        var xp = d3.event.offsetX;
        var yp = d3.event.offsetY;
        var offset = me.xScale.invert(xp);

        var alpha  = me.yScale.invert(yp);
        var interval = 0;
        me.data.forEach(function(e,i,a){
            if(offset > e.offset) interval = i;
        });
        return {i: interval, offset: offset, alpha: alpha};
    },

    updateScale : function(){
        var me = this;
        samplesize = this.data.length;
        var buffer = 0.025*this.getHeight();

        this.xScale = d3.scale.linear().domain([0, 100]).range([buffer, me.getWidth()-buffer]),
        this.yScale = d3.scale.linear().domain([0, 1.0]).range([me.getHeight()- buffer, buffer]);
        var buffer = 0.025*this.getHeight();
        this.area = d3.svg.area()
            .x(function(d) { return me.xScale(d.offset); })
            .y0(this.getHeight()-buffer)
            .y1(function(d) { return me.yScale(d.alpha); });


    },

    redraw : function(){
        //this updates the graph, but doesn't add new points, also can add
        //transitions here, if you want.
        var me = this;
        this.updateScale();
        var buffer = 0.025*this.getHeight();
        this.area = d3.svg.area()
            .x(function(d) { return me.xScale(d.offset); })
            .y0(this.getHeight()-buffer)
            .y1(function(d) { return me.yScale(d.alpha); });

        this.svg.select("path.transfer").transition()
            .ease("quartic -in")
            .duration(500)
            .attr("d", this.area);

        this.svg.selectAll("circle").transition()
            .ease("quartic -in")
            .duration(500)
            .attr("cx", function(d) { return me.xScale(d.offset); })
            .attr("cy", function(d) { return me.yScale(d.alpha); });
        this.histogramSvg.redraw();
        //this.redrawHistogram();
    },

    updateGraph : function(dp){
        var me = this;

        var circle = this.svg.selectAll("circle")
            .data(this.data, function(d){return d.id;});
        var stops = this.gradient.selectAll("stop")
            .data(this.data, function(d){return d.id;});

        //1. update graph and gradient points
        circle
            .attr("cx", function(d) { return me.xScale(d.offset); })
            .attr("cy", function(d) { return me.yScale(d.alpha); })
            .attr("r", 3)
            .attr("fill", function(d){
                console.log(d.id);
                if(d.id == me.clicked) return "rgb(255,255,255)";
                else  return "rgb(128,128,128)";
            } );

        stops
            .attr("id", function(d, i){return "stop_"+i;})
            .attr("offset",function(d){return d.offset + "%";})
            .attr("stop-color",function(d){return "rgb(" +
                                           Math.floor(d.color[0]) + "," +
                                           Math.floor(d.color[1]) + "," +
                                           Math.floor(d.color[2]) + ")";});
            //.attr("stop-opacity",function(d){return 1.0;});


        //1. add new graph points
        circle
            .enter().append("circle")
            .attr("id", function(d, i){return "circle_"+i;})
            .attr("cx", function(d) { return me.xScale(d.offset); })
            .attr("cy", function(d) { return me.yScale(d.alpha); })
            .attr("r", 3)
            .attr("fill", function(d){
                return "rgb(128,128,128)";
            } )
            .call(this.drag);

        //2. add new gradient stops
        //2.a select most recently added stop
        stops
            .enter().append("svg:stop")
            .attr("id", function(d, i){return "stop_"+i;})
            .attr("offset",function(d){return d.offset + "%";})
            .attr("stop-color",function(d){return "rgb(" +
                                           Math.floor(d.color[0]) + "," +
                                           Math.floor(d.color[1]) + "," +
                                           Math.floor(d.color[2]) + ")";});
            //.attr("stop-opacity",function(d){return 0.85;});

        //2.a select all stops
        stops = this.gradient.selectAll("stop")
            .data(this.data, function(d){return d.id;});
        //2.b d3 appends the div at the end, so we sort the stops so that the gradient draw properly
        stops.sort(function(a,b){return a.id - b.id;}) // could sort via offset, but this is more concrete
            .attr("id", function(d){
                return "stop_"+d.id;
            });;

        //3. remove points on the graph that have been deleted
        circle.exit().remove();
        stops.exit().remove();

        //4. redraw my area

        this.svg.select("path.transfer").transition()
            .attr("d", this.area);
            //.attr("opacity", 50)

    },


    addStopAtOffset : function(i, offset, alpha){
        var me = this;
        var stop0 = i;
        var stop1 = stop0 + 1;
        var d0 = this.data[stop0];
        var d1 = this.data[stop1];

        var t = (offset - d0.offset)/(d1.offset - d0.offset);
        console.log(i, offset, alpha);
        var dp = {
            id: stop0 + 1,
            offset: offset,
            alpha:  alpha,
            color: [
                t*d0.color[0]  + (1.0-t)*d1.color[0],
                t*d0.color[1]  + (1.0-t)*d1.color[1],
                t*d0.color[2]  + (1.0-t)*d1.color[2],
            ]};

        this.data.splice(stop1, 0, dp);
        this.data.forEach(function(e,i,a){e.id = i;});


        this.updateGraph();
    },

    addStopAtIndex : function(stop0, t){
        var me = this;
        var stop0 = 5;
        var stop1 = stop0 + 1;
        var t = 0.2;

        var d0 = this.data[stop0];
        var d1 = this.data[stop1];
        var dp = {
            id: stop0 + 1,
            offset: t*d0.offset + (1.0-t)*d1.offset,
            alpha:  t*d0.alpha  + (1.0-t)*d1.alpha,
            color: [
                t*d0.color[0]  + (1.0-t)*d1.color[0],
                t*d0.color[1]  + (1.0-t)*d1.color[1],
                t*d0.color[2]  + (1.0-t)*d1.color[2],
            ]};

        this.data.splice(stop1, 0, dp);
        this.data.forEach(function(e,i,a){e.id = i;});


        this.updateGraph();
    },

    removeStop : function(stop){
        this.data.splice(stop,1);
        this.data.forEach(function(e,i,a){e.id = i;});

        var offsets = [];
        this.data.forEach(function(e,i,a){offsets.push(e.id);});
        offsets.join(" ");
        this.updateGraph();
    },

    setColor : function(i, col){
        this.data[i].color = col;
        var stops = this.gradient.selectAll("stop")
            .data(this.data, function(d){return d.id;});

        stops
            .attr("id", function(d, i){return "stop_"+i;})
            .attr("offset",function(d){return d.offset + "%";})
            .attr("stop-color",function(d){return "rgb(" +
                                           Math.floor(d.color[0]) + "," +
                                           Math.floor(d.color[1]) + "," +
                                           Math.floor(d.color[2]) + ")";});
            //.attr("stop-opacity",function(d){return 0.75;});
    },

    afterRender : function() {
        this.callParent();
        this.gridSizeX = 1;
        this.gridSizeY = 0.05;
    },

    afterFirstLayout : function() {
        this.callParent();
        this.buildGraph();
    },

});

Ext.define('BQ.viewer.volume.transfer.editor', {
    extend: 'Ext.panel.Panel',
    alias : 'widget.bq_volume_transfer_editor',


    layout : {
        type : 'hbox',
        align : 'stretch',
    },

    initComponent : function () {

        this.data = [];
        var N = 8;
        this.data[0] = {
            id: 0,
            offset: 0,
            alpha: 0,
            color: [255,255,255]};
        for(var i = 1; i < N-1; i++){
            this.data[i] = {
                id: i,
                offset: 100*(i + Math.random())/N,
                alpha: i/N + 2.0*Math.random()/N,
                color: [
                    255*Math.random(),
                    255*Math.random(),
                    255*Math.random()
                ]};
        }

        this.data[N-1] = {
            id: N-1,
            offset: 100,
            alpha: 1,
            color: [0,0,0]};
        var panelWidth = 500,
        panelHeight = 500,
        canvasWidth = null,
        canvasHeight = null,
        btnCls = 'btn-peachpuff',
        svg = null,
        gBar = null,
        gYAxis = null,
        gLabel = null,
        gYAxis = null,
        xScale = null,
        yScale = null,
        yAxis = null,
        yAxisScale = null,
        colorScale = d3.scale.category20(),
        barPadding = 5,
        labelDistanceFromBar = 5;
        var me = this;

        this.transferGraph = Ext.create('BQ.volume.transfer.graph', {
            data : this.data,
            cls : 'd3Comp',
            height: '100%',
            margins : {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0,
                leftAxis: 0
            },

            listeners: {
                mousedown: function(){
                    if(me.mode == 1){
                        var interval = me.transferGraph.findInterval(me.transferGraph);
                        me.transferGraph.addStopAtOffset(interval.i, interval.offset, interval.alpha);
                        me.fireEvent('change', me);
                    }
                    if(me.mode == 2){
                        //roll this into find nearest
                        var interval = me.transferGraph.findInterval(me.transferGraph);
                        var offset = interval.offset;
                        var alpha = interval.alpha;
                        var l = me.transferGraph.data.length;
                        var d0 = me.transferGraph.data[interval.i];
                        var d1 = me.transferGraph.data[interval.i+1];
                        var w = 100/me.transferGraph.getWidth();
                        var h = me.transferGraph.getHeight();
                        var dt0 = (offset - d0.offset)*(offset - d0.offset)/w/w + (alpha - d1.alpha)*(alpha - d1.alpha)/h/h;
                        var dt1 = (offset - d1.offset)*(offset - d1.offset)/w/w + (alpha - d1.alpha)*(alpha - d1.alpha)/h/h;
                        //console.log(dt0, dt1);
                        var t = (offset - d0.offset)/(d1.offset - d0.offset);
                        if(dt0 < 25 && interval.i > 0 ){
                            me.transferGraph.removeStop(interval.i);
                        }
                        if(dt1 < 25 && interval.i  < l - 2){
                            console.log(interval.i,l);
                            me.transferGraph.removeStop(interval.i+1);
                        }
                        me.fireEvent('change', me);
                    }

                },
                change: function(){
                    me.fireEvent('change', me);
                },
                //renderTo: Ext.getBody(),

            },
            gamma: this.gamma,
            histogram: this.histogram,
            colorScale : d3.scale.category20(),
            barPadding : 5,
            labelDistanceFromBar : 5,

        });

        this.colorPicker = Ext.create('BQ.viewer.Volume.excolorpicker', {
            //height: '100%',
            height: '100%',
            listeners: {
                change: function(){
                    console.log(me.transferGraph.selected);
                    me.transferGraph.selected.forEach(function(d,i,a){
                        me.transferGraph.setColor(d, me.colorPicker.getColorRgb());
                    });
                }
            },
            region: 'west'
        });

        this.snapBoxX = Ext.create('Ext.form.field.Number', {
            name : 'snapx',
            fieldLabel : 'grid x',
            value : 1,
            minValue : 0,
            maxValue : 10,
            step : 0.5,
            listeners : {
                change : function (field, newValue, oldValue) {
                    me.transferGraph.gridSizeX = newValue;
                },
                scope : me
            },
        }).hide();


        this.snapBoxY = Ext.create('Ext.form.field.Number', {
            name : 'snapy',
            fieldLabel : 'grid y',
            value :0.1,
            minValue : 0.1,
            maxValue : 1,
            step : 0.05,
            listeners : {
                change : function (field, newValue, oldValue) {
                    me.transferGraph.gridSizeY = newValue;
                },
                scope : me
            },
        }).hide();

        Ext.apply(this, {
            tbar : [{
				xtype : 'button',
				text : 'edit',
				width : 'auto',
				enableToggle : true,
				cls : 'toolItem',
                id: 'transButton0',
				handler : function(){
                    var
                    b1 = Ext.getCmp('transButton1'),
                    b2 = Ext.getCmp('transButton2');
                    if(b1.pressed) b1.toggle();
                    if(b2.pressed) b2.toggle();
                    this.mode = 0;
                },
				scope : this,
			}, {
				xtype : 'button',
				text : '+',
				width :'auto',
				enableToggle : true,
				cls : 'toolItem',
                id: 'transButton1',
				handler : function(){
                    var
                    b0 = Ext.getCmp('transButton0'),
                    b2 = Ext.getCmp('transButton2');
                    if(b0.pressed) b0.toggle();
                    if(b2.pressed) b2.toggle();
                    this.mode = 1;
                },
                scope : this,
			},{
				xtype : 'button',
				text : '-',
				width : 'auto',
                enableToggle : true,
                cls : 'toolItem',
                id: 'transButton2',
				handler : function(){
                    var
                    b1 = Ext.getCmp('transButton1'),
                    b0 = Ext.getCmp('transButton0');
                    if(b1.pressed) b1.toggle();
                    if(b0.pressed) b0.toggle();
                    this.mode = 2;
                },
                scope : this,
			},{
			    boxLabel : 'snap',
			    checked : false,
			    cls : 'toolItem',
			    xtype : 'checkbox',
			    handler : function (item, checked) {
				    if (checked) {
					    me.transferGraph.snap = true;
                        me.snapBoxX.show();
					    me.snapBoxY.show();
                    } else {
					    me.transferGraph.snap = false;
					    me.snapBoxX.hide();
                        me.snapBoxY.hide();
                    }}
		    },
                    this.snapBoxX,
                    this.snapBoxY,]
        });

        this.items = [
            this.colorPicker,

            {
                //cls: 'd3Comp',
                xtype: 'container',
                layout: 'fit',
                flex: 1,
                style:{
                    width: "100%",
                    height: "100%",
                },
                items: [this.transferGraph],

            }];
        this.callParent();
    },
});


Ext.define('BQ.viewer.Volume.transfer', {
    extend : 'Ext.container.Container',
    alias : 'widget.bq_volume_transfer',

    mixins : ['BQ.viewer.Volume.uniformUpdate'],
    addUniforms : function () {
        this.tSize = 64;
        this.sceneVolume.initUniform('transfer', "t", null);
        this.sceneVolume.initUniform('TRANSFER_SIZE', "i", this.tSize);
        this.sceneVolume.initUniform('USE_TRANSFER', "i", this.transfer);
    },

    changed : function () {
        if (!this.transferEditor)
            return;
        var pixels = new Uint8Array(4*this.tSize);
        var cStop = 0;
        var ci = 0;
        var data = this.transferEditor.data;
        var l = data.length;
        var stop0 = data[0];
        var stop1 = data[l-1];

        if (stop0.offset != 0)
            return;
        if (stop1.offset != 100)
            return;

        for (var i = 0; i < this.tSize; i++) {
            var stop = data[cStop];
            var nstop = data[cStop+1];

            var per = ci / this.tSize * 100;

            if (per > nstop.offset - stop.offset) {
                ci = 0;
                cStop++;
                stop = data[cStop];
                nstop = data[cStop + 1];
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

        this.transferEditor = Ext.create('BQ.viewer.volume.transfer.editor',{
            histogram: this.panel3D.model.histogram,
            gamma:     this.panel3D.model.gamma,
            listeners: {
                change: function(){
                    me.changed();
                }
            }
        });
        this.panel3D.on('histogramupdate', function(){
            console.log("update");
            if(me.transferEditor.transferGraph.histogramSvg)
                me.transferEditor.transferGraph.histogramSvg.redraw();
        });
        this.showButton.hide();
        this.addUniforms();
        Ext.apply(this, {
            items : [useTransfer, this.showButton],
        });

        this.callParent();
    },

    displayTransferWindow : function () {
        if(!this.transferWindow){
            this.transferWindow = Ext.create('Ext.window.Window',{
                border : 0,
	            layout : 'fit',
	            border : false,
	            autoScroll : true,
	            title : 'transfer function editor',
                cls : 'bq-volume-transfer',
                width: 1200,
                height: 300,
	            x: 40,
	            y: 40,
                minHeight: 300,
                minWidth: 800,
                hidden: false,
                maximizable: true,
                autoShow: true,
                items : [this.transferEditor]
            });
        }
        this.transferWindow.show();
    },

    afterFirstLayout : function () {
        //this.transferSlider.show();
        this.changed();
    },
});