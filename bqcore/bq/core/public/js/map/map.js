/*
***GMAP Window***
8/11
Google Map in ExtJS 4 Wrapper

This file is derived from the Google Maps Wrapper Class Demo from http://www.sencha.com/.
The Demo uses Google Maps API V2, but this class updates to Google Maps API V3.

This class extends Ext.panel.Panel to be a container filled with two main items: a Google Map and a Select list. In the afterRender function, a
a default query (var index_uri) AJAX Request is made to the server to get a list of images. Then the function imLoadAjax iterates through the list
and sends AJAX Requests That XML document will contain
GPS data (about a photo) which is passed to the map. The map sets a marker and centers on that location.
*/
/**
 * @class Ext.ux.GMapPanel
 * @extends Ext.Panel
 * @author Shea Frederick
 * @revised Alex Tovar
 * @revised Dmitry Fedorov
 */

Ext.define('BQ.map.Map', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.bqmap',
    //requires: ['Ext.window.MessageBox'],
    
    plain: true,
    zoomLevel: 3,
    yaw: 180,
    pitch: 0,
    zoom: 0,
    border: false,
    combo: false,
    
    initComponent : function() {
        this.addListener( 'resize', this.resized, this );  
        this.callParent();
    },    
    
    afterRender : function(){
        this.callParent();
        
        this.gmap = new google.maps.Map(this.body.dom, {
            zoom: 1,
            center: new google.maps.LatLng(42.6507,14.866),
            mapTypeId: google.maps.MapTypeId.ROADMAP,
        });
        this.infoWindow = new google.maps.InfoWindow({content:null, maxWidth: 450}); // make one info window 
        this.bound = new google.maps.LatLngBounds();

        // load dataset values
        Ext.Ajax.request({
            url: this.resource.uri + '/value',
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    BQ.ui.error(response.responseText);
                else
                    this.onImagesLoaded(response.responseXML);
            },
            scope: this,
            listeners: {
                scope: this,
                beforerequest   : function() { this.setLoading('Loading images...'); },
                requestcomplete : function() { this.setLoading(false); },
                requestexception: function() { this.setLoading(false); },                                
            },
        });
    },
    
    resized: function() {
        if (this.gmap) 
            google.maps.event.trigger(this.gmap, 'resize');
    },      
    
    onImagesLoaded : function(xml) {
        var unqs = this.evaluateXPath(xml, "//image/@resource_uniq"); 
        var uris = this.evaluateXPath(xml, "//image/@uri"); 
        for (var i=0; i<unqs.length; ++i) {
            var id  = unqs[i].value;
            var uri = uris[i].value;
            var uri_meta = '/image_service/images/' + id + '?meta';
            var image = {
                id: id,
                uri: uri,
                thumbnail : '/image_service/images/' + id + '?thumbnail',
            };
            this.requestMeta(uri_meta, image);
        }
    },
    
    requestMeta: function(uri, image) { 
        var me = this;   
        Ext.Ajax.request({
            url: uri,
            scope: this,
            disableCaching: false,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    BQ.ui.error(response.responseText);
                else
                    me.onMeta(response.responseXML, image);
            },
        });        
    },
    
    onMeta: function(xml, image) {
        var point = this.findGPS(xml);
        if (point)
            this.addMarker(point, image);
    },    
    
    addMarker : function(point, image){
        this.bound.extend(point);
        var marker = new google.maps.Marker({
            position: point,
            map: this.gmap,
            image: image,
        });
        this.gmap.fitBounds(this.bound); // dima: this might have to be activated on timeout with histerisis
        var me = this;
        google.maps.event.addListener(this.gmap, 'click', function() { me.infoWindow.close(); });
        google.maps.event.addListener(marker, 'click', function() { me.onMarkerClick(this); } );
    },
    
    onMarkerClick : function(marker) {
        var map = this.gmap;
        var s = '<img src= "' + marker.image.thumbnail + '" />';
        this.infoWindow.setContent(s);  
        this.infoWindow.open(map, marker);
        map.panTo(marker.position);
    },
    
    gpsParser : function(gpsString, direction) {
        if (!gpsString || gpsString.length<1) return null;
        var coordinates=gpsString[0].value.match(/[\d\.]+/g);  
        var Deg = parseInt(coordinates[0]);
        var Min = parseFloat(coordinates[1]);
        var Sec = parseFloat(coordinates[2]);
        // iPhone pix will only have two array entries, extra-precise "minutes"
        if(coordinates.length <3) Sec = 0;
        var ref = direction[0].value;
        var gps = Deg + (Min / 60) + (Sec / 60 / 60);
        if (ref == "South" || ref =="West") gps = -1*gps;
        return gps;
    },
    
    findGPS : function(xmlDoc){
        if(!xmlDoc) return;
        var latituderef = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLatitudeRef']/@value");
        var longituderef = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLongitudeRef']/@value");
        var latitude = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLatitude']/@value");
        var longitude = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLongitude']/@value");
        
        var thelat = this.gpsParser(latitude, latituderef);
        var thelon = this.gpsParser(longitude, longituderef);
        if (!thelat || !thelon) return;
        
        return new google.maps.LatLng(thelat,thelon);
    },
    
    evaluateXPath: function(aNode, aExpr) {
        var xpe = new XPathEvaluator();
        var nsResolver = xpe.createNSResolver(aNode.ownerDocument == null ?
          aNode.documentElement : aNode.ownerDocument.documentElement);
        var result = xpe.evaluate(aExpr, aNode, nsResolver, 0, null);
        var found = [];
        var res;
        while (res = result.iterateNext())
          found.push(res);
        return found;
    },
    
});