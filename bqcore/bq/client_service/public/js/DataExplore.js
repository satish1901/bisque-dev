//-------------------------------------------------------------------------
// BQQuery
//-------------------------------------------------------------------------

function BQQuery(uri, parent, callback) {
  this.parent = parent;
  this.tags = new Array();
  this.callback = callback;  
  makeRequest( uri, this.parseResponse, this , "GET", null ); 
} 

BQQuery.prototype.parseResponse = function(o, data) {
  var tags = data.getElementsByTagName("tag");
  for(var i=0; i<tags.length; i++) {
    o.tags[i] = tags[i].getAttribute('value');
  }
  o.callback(o);
}

//-------------------------------------------------------------------------
// TagExplore
//-------------------------------------------------------------------------
function TagExplore(containerDiv, tag_str) {
  this.container = containerDiv;
  this.queryTag( tag_str );
}

TagExplore.prototype.queryTag = function( tag_str ) {
  var v = tag_str.split(':');
  this.title = v[0];
  this.tag = v[1];  
  this.query = new BQQuery("/data_service/images?tag_values="+this.tag, this, this.createValues);
}

/*
<dl id="gray1" title="Current statistics for this BISQUE database.">
	<dt>Datasets</dt>
	<dd>
	<div id="datasetsBody" class="statsscrollable">
  <script type="text/javascript">
		_datasetList = new DatasetList(document.getElementById("datasetsBody"));
  </script><ul/>
	</div>
</dd>
</dl>
*/

TagExplore.prototype.createBox = function( ) {
  /*
  this.box = document.createElement('div');
  this.box.className = 'welcome_box';
 
  var header = document.createElement('h3');
  header.innerHTML = this.title;
  this.box.appendChild(header);
  */
  this.box = document.createElement('dl');
  this.box.className = 'info_box';  
  this.box.id = 'blue';
 
  var header = document.createElement('dt');
  header.innerHTML = this.title;
  this.box.appendChild(header);  
  
  var cb = document.createElement('dd');
  this.box.appendChild(cb);  
  
  this.content = document.createElement('div');
  this.content.className = 'statsscrollable'; 
  //this.box.appendChild(this.content);
  cb.appendChild(this.content);
  
  this.container.appendChild(this.box);  
}

function encodeURLquery(s) {
    return escape(s).replace(/\s/g, '+');
}

TagExplore.prototype.createValues = function( q ) {
  if (q.tags.length <= 0) return;
  
  q.parent.createBox();

  var ol = document.createElement('ul');
  for(var i=0; i<q.tags.length; i++) {
    var li = document.createElement('li');
    
    var lnk = document.createElement('a');
    lnk.innerHTML = q.tags[i];
    ///bisquik/browser?tag_query=experimenter:geoff+lewis
    //encodeURIComponent(this.name)
    lnk.setAttribute('href', '/client_service/browser?tag_query='+q.parent.tag+':"'+encodeURLquery(q.tags[i])+'"' );
    li.appendChild(lnk);    
    
    ol.appendChild(li);    
  }  

  q.parent.content.appendChild(ol);
}

//-------------------------------------------------------------------------
// DataExplore
//-------------------------------------------------------------------------

function DataExplore(containerDiv, tags_str) {
  this.container = containerDiv;
  if (tags_str == '') return;
  this.tags = tags_str.split(';');
  this.boxes = new Array();
  this.createTagBoxes();
}

DataExplore.prototype.createTagBoxes = function( ) {
  for (var i=0; i<this.tags.length; i++) {
    var span = document.createElement('span');
    this.container.appendChild(span);  	
	this.boxes[i] = new TagExplore(span, this.tags[i]);
  }
}


