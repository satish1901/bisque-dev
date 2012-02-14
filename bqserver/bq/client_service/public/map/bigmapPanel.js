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
 */

var server_uri = '';
var viewer_service = '/client_service/view?resource=';
var query_service  = '/data_service/images?tag_query=';
//var default_query = '*COPR*';
var default_query = '';

var thumbnail_apdx = '?thumbnail=200,200';
var resource_apdx = "?view=full";
var metadata_apdx = "?meta";

var tagsInter = {};
tagsInter['Genus'] = "//tag[@name='Genus']/@value | //tag[@name='genus']/@value";
tagsInter['Species'] = "//tag[@name='Species']/@value | //tag[@name='species']/@value";
tagsInter['commonName'] = "//tag[@name='Common name']/@value";
            
var tagsGPS = {};
tagsGPS['latituderef'] = "//tag[@name='GPSLatitudeRef']/@value";
tagsGPS['longituderef'] = "//tag[@name='GPSLongitudeRef']/@value";
tagsGPS['latitude'] = "//tag[@name='GPSLatitude']/@value";
tagsGPS['longitude'] = "//tag[@name='GPSLongitude']/@value";

var fetching=0;
var markersArray = [];

Ext.define('BQ.gmap.BIGMapPanel', {
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
            border: false,
            combo: false,
            imageQuery: default_query,
        };
        
        Ext.applyIf(this, defConfig);
        this.callParent();
        this.selectlist = {};
    },
    
    afterRender : function(){
        this.callParent();
        
        this.gmap = new google.maps.Map(this.body.dom, {
        zoom: 15,
        center: new google.maps.LatLng(34.4115,-119.875),
        mapTypeId: google.maps.MapTypeId.ROADMAP
        });
        this.infoWindow = new google.maps.InfoWindow({content:null, maxWidth: 450}); // make one info window 

        var textbar = Ext.getDom('input_query');
        textbar.value = this.imageQuery;
        if (this.combo) this.combo.setValue(this.imageQuery);

        setTimeout( this.imLoadAjax(query_service+this.imageQuery), 500);
    },
    
    imLoadAjax : function(query) {
        //var parent = Ext.getBody();
        var parent = this.findParentByType('panel');
        Ext.Ajax.on('beforerequest', function(){ parent.setLoading('Loading images...')});
        Ext.Ajax.on('requestcomplete', function(){ parent.setLoading(false)});
        Ext.Ajax.on('requestexception', function(){ parent.setLoading(false)});
        
        Ext.Ajax.request({
            url: server_uri+query,
            scope: this,
            disableCaching: false,            
            timeout: 120000,
            callback: function(opts, succsess, response) {
                if (response.status>=400)
                    Ext.Msg.alert(response.responseText);
                else
                    this.onImagesLoaded(response);
            },
        });
    },
    
    onImagesLoaded : function(xmlDoc) {
        if (!xmlDoc.responseXML) {
            //alert('Request timeout');
            return;
        }
        var imageID = this.evaluateXPath(xmlDoc.responseXML, "//image/@src");      //the source tag, for the location of the thumbnail preview to be displayed in the infowindow
        var tagsLoc = this.evaluateXPath(xmlDoc.responseXML, "//image/@uri");
        
        for (i=0; i< imageID.length; i++) {  
            fetching+=1;    
            var o = this;    
            var r = tagsLoc[i].value+resource_apdx;
            setTimeout( Ext.Ajax.request({
                url: r,
                scope: o,
                disableCaching: false,
                callback: function(opts, succsess, response) {
                    if (response.status>=400)
                        Ext.Msg.alert(response.responseText);
                    else
                        o.renderImage(response);
                },
            }), i*250 );    
        }
        
        var selection = Ext.getDom("chooser");
        var me = this;
        selection.onchange = function() { //run some code when "onchange" event fires
          var chosenoption=this.options[this.selectedIndex] //this refers to "selection"
          me.onMarkerClick2 (chosenoption.marker);
        }
        
        //var textbar = Ext.getDom('input_query');
        //var submission = Ext.getDom('submission');
        //submission.onclick = function(){ me.makeQuery('*'+textbar.value+'*'); };
        
    },
    
    makeQuery : function(q) {
        this.deleteOverlays();
        this.imLoadAjax(query_service + q);
    },
    
    setSize : function() {
        this.callParent(arguments);
        if (this.gmap) google.maps.event.trigger(this.gmap, 'resize');
    },    
    
    getMap : function(){
        return this.gmap;
    },
    
    addMarker : function(lat, lng, thumbLoc, commonname, genus, species, picHome, identifier){

        var marker = new google.maps.Marker({
            position: new google.maps.LatLng(lat, lng),
            map: this.gmap,
            image: '<img src= "' + thumbLoc + '" />',
            commonNameAtt: commonname,
            genusAtt: genus,
            speciesAtt: species,
            picHome: picHome,
            identifier: identifier
        });
        var me = this;
        google.maps.event.addListener(this.gmap, 'click', function() { me.infoWindow.close(); });
        google.maps.event.addListener(marker, 'click', function() { me.onMarkerClick(this); } );
        
        var s = '';
        if (identifier) s += '' + identifier;
        if (genus)      s += '  Genus: ' + genus;
        if (species)    s += '  Species: ' + species;

        var myselect=Ext.getDom("chooser");        
        var opt = new Option(s);
        opt.marker = marker;
        myselect.add(opt, null);
        var id = myselect.length-1;
        
        this.selectlist[marker.identifier] = id;
        markersArray.push(marker);
    },
    
    onMarkerClick : function(marker) {
        var s = '';
        if (marker.speciesAtt) s += '<b>Species: </b>' + marker.speciesAtt;
        if (marker.genusAtt) s +=  '<br /><b>Genus: </b>' + marker.genusAtt;
        if (marker.commonNameAtt) s += '<br /><b>Common Name: </b>' + marker.commonNameAtt;
        s += '<br /><b>ID: </b>' +  marker.identifier +'<br /><a href= "' + marker.picHome + '" target="_blank">'+ marker.image+'</a>';
        this.infoWindow.setContent(s); 
        this.infoWindow.open(this.getMap(), marker);
        
        var myselect=Ext.getDom("chooser");
        myselect.selectedIndex = this.selectlist[marker.identifier];
    },
    
    onMarkerClick2 : function(marker) {
        var map = this.gmap;
        var s = '';
        if (marker.speciesAtt) s += '<b>Species: </b>' + marker.speciesAtt;
        if (marker.genusAtt) s +=  '<br /><b>Genus: </b>' + marker.genusAtt;
        if (marker.commonNameAtt) s += '<br /><b>Common Name: </b>' + marker.commonNameAtt;
        s += '<br /><b>ID: </b>' +  marker.identifier + '<br /><a href= "' + marker.picHome + '" target="_blank">'+ marker.image+'</a>';
        this.infoWindow.setContent(s);  
        this.infoWindow.open(map, marker);
        map.panTo(this.position);
    },
    
    deleteOverlays: function() {     
        if (markersArray) {
            for (i=0; i<markersArray.length; i++) 
                markersArray[i].setMap(null);
            var myselect = Ext.getDom("chooser");
            while(myselect.firstChild) 
                myselect.removeChild(myselect.firstChild);
            markersArray.length = 0;
            this.selectlist=[];
        }
    },
    
    gpsParser : function(gpsString, direction) {
        if (!gpsString || !direction) return;
        var coordinates=gpsString.match(/[\d\.]+/g);  
        var Deg = parseInt(coordinates[0]);
        var Min = parseFloat(coordinates[1]);
        var Sec = parseFloat(coordinates[2]);
        // iPhone pix will only have two array entries, extra-precise "minutes"
        if(coordinates.length <3) Sec = 0;
        var gps = Deg + (Min / 60) + (Sec / 60 / 60);
        if (direction == "South" || direction =="West") gps = -1*gps;
        return gps;
    },
    
    findGPS : function(gpshash){
        if(gpshash!=null){     
            var thelat = this.gpsParser(gpshash.latitude, gpshash.latituderef);
            var thelon = this.gpsParser(gpshash.longitude, gpshash.longituderef);
            if (!thelat || !thelon) return;
            return { lat: thelat, lon: thelon};
        }
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
    
    loadXMLDoc: function(dname)  {
        var xhttp=null;    
        if (window.XMLHttpRequest)
            xhttp=new XMLHttpRequest();
        else
           xhttp=new ActiveXObject("Microsoft.XMLHTTP");
        xhttp.open("GET",dname,false);
        xhttp.send();
        return xhttp.responseXML;
    },
        
    parseTags: function(dict, xml) {
        var r = new Object();
        for (var i in dict) {
              var v = this.evaluateXPath(xml, dict[i]);
              if (v[0] != undefined)
                  r[i] = v[0].value;
        }
        return r;
    },
    
    renderImage: function(xml) {
        fetching-=1;
        var imageID = this.evaluateXPath(xml.responseXML, "//image/@src");      //the source tag, for the location of the thumbnail preview to be displayed in the infowindow
        var tagsLoc = this.evaluateXPath(xml.responseXML, "//image/@uri");
        if (tagsLoc.length<1) return;
        if (imageID.length<1) return;
        var resource_uri = tagsLoc[0].value
        var image_uri = imageID[0].value;
        var resourceNumbs = resource_uri.match(/[\d]+/g);
        var identifier = resourceNumbs[resourceNumbs.length -1];
        var thumbLoc = image_uri + thumbnail_apdx;
        var picHome = viewer_service + tagsLoc[0].value;
    
        if (this.selectlist[identifier] == null) {
            var xmlDoc = this.loadXMLDoc(image_uri + metadata_apdx);
            var xmlDocTags = xml.responseXML;
    
            var tags = this.parseTags(tagsInter, xmlDocTags);
            var gps = this.parseTags(tagsGPS, xmlDoc);
            var place = this.findGPS(gps);
            if (place && place.lat && place.lon) {
                this.addMarker(place.lat, place.lon, thumbLoc, tags.commonName, tags.Genus, tags.Species, picHome, identifier);
            }
        }

    },
    
});