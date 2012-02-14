/*
***GMAP Window***
8/11
Google Map in ExtJS 4 Wrapper

This file is derived from the Google Maps Wrapper Class Demo from http://www.sencha.com/.
The Demo uses Google Maps API V2, but this class updates to Google Maps API V3.

This class extends Ext.window.Window to be a container filled with a Google Map. In the afterRender function, a
an AJAX request is made to the given URL so that it made receive an XML document. That XML document will contain
GPS data (about a photo) which is passed to the map. The map sets a marker and centers on that location.
*/
/**
 * @class Ext.ux.GMapPanel
 * @extends Ext.Panel
 * @author Shea Frederick
 * @revised Alex Tovar
 */

Ext.define('BQ.gmap.GMapPanel3', {
    extend: 'Ext.panel.Panel',
    
    alias: 'gmappanel3',
    
    requires: ['Ext.window.MessageBox'],
    
    initComponent : function(){
        
        var defConfig = {
            plain: true,
            zoomLevel: 3,
            yaw: 180,
            pitch: 0,
            zoom: 0,
            border: false
        };
        
        Ext.applyIf(this,defConfig);
        this.callParent();        
    },
    
    afterRender : function(){
        this.callParent();     
        this.gmap = new google.maps.Map(this.body.dom, {
        zoom: 1,
        center: new google.maps.LatLng(42.6507,14.866),
        mapTypeId: google.maps.MapTypeId.ROADMAP
        });
        infoWindow = new google.maps.InfoWindow({content:null, maxWidth: 450}); // make one info window
          
        //this.addManyMarkers(this.markers);
        Ext.Ajax.request({
            url: this.url,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    Ext.Msg.alert(response.responseText);
                else
                    this.onImageLoaded(response);
            },
            scope: this,
        });
    },
    
    onImageLoaded : function(res) {
        center = this.findGPS(res.responseXML);
            if(center!=null) {
                this.gmap.setCenter(center);
                this.gmap.setZoom(this.zoomLevel);
                this.addMarker(center);
            }else{
                Ext.Msg.alert('Boo','GPS coordinates unavailable');
                //var myMask = new Ext.Mask(Ext.getBody(), {msg:"Please wait..."},{renderTo:this.gmap});
                //myMask.show();
            }
    },
    
    setSize : function() {
        this.callParent(arguments);
        if (this.gmap) google.maps.event.trigger(this.gmap, 'resize');
    },    
    
    getMap : function(){
        
        return this.gmap;
        
    },
    addManyMarkers : function(markers) {
        
        if (Ext.isArray(markers)){
            for (var i = 0; i < markers.length; i++) {
                var mkr_point = new google.maps.LatLng(markers[i].lat,markers[i].lng);
                this.addMarker(mkr_point,markers[i].marker,false,markers[i].setCenter, markers[i].listeners);
            }
        }
        
    },
    addMarker : function(point, marker, clear, center, listeners){

        if (clear === true){
            this.getMap().onRemove();
        }
        if (center === true) {
            this.getMap().setCenter(point);
            this.getMap().setZoom(this.zoomLevel);
        }

        var marker = new google.maps.Marker({position:point, map: this.gmap});
        google.maps.event.addListener(this.gmap, 'click', function() {
        infoWindow.close();
        });
    
        google.maps.event.addListener(marker, 'click', this.onMarkerClick);
    },
    
    onMarkerClick : function() {
        var marker = this;
        var latLng = marker.getPosition();
        var s = '';
        s += '<b>IMAGE LOCATION</b>';
        s += '<br /><b>Latitude: </b>' + latLng.Oa;
        s +=  '<br /><b>Longitude: </b>' + latLng.Pa;
        infoWindow.setContent(s); 
        infoWindow.open(this.getMap(), marker);
    },
    
    gpsParser : function(gpsString, direction){
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

        if(xmlDoc!=null){
        var latituderef = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLatitudeRef']/@value");
        var longituderef = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLongitudeRef']/@value");
        var latitude = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLatitude']/@value");
        var longitude = this.evaluateXPath(xmlDoc, "//tag[@name='GPSLongitude']/@value");
        
        var thelat = this.gpsParser(latitude, latituderef);
        var thelon = this.gpsParser(longitude, longituderef);
        
        point = new google.maps.LatLng(thelat,thelon);
        return point;}
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
    
    loadXML: function (url, context, callback)  {
        var xhttp=null;
        if (window.XMLHttpRequest)
            xhttp=new XMLHttpRequest();
        else
           xhttp=new ActiveXObject("Microsoft.XMLHTTP");
        xhttp.open("GET", url, true);
        
        xhttp.onreadystatechange = function (aEvt) {
          if (xhttp.readyState == 4) {
              if (xhttp.status==200 || xhttp.status==0)
                  context[callback](xhttp.responseXML);
          }
        };    
        xhttp.send();
    }
});