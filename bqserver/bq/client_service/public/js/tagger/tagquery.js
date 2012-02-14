// <![CDATA[

function TagQuery (divParent, tagvalue) {
	_tagq = this;
	this.divParent = divParent;
	this.tagvalue = tagvalue;
	this.serverURL = "/bisquik/query_db?url=";
	this.divW = null;
	this.divWTitle = null;
	this.divWText = null;
	this.divWLink = null;
	this.aWLink = null;
	this.divPM = null;
	this.divPMTitle = null;
	this.divPMText = null;
	this.divPMLink = null;
	this.aPMLink = null;
	this.divGenomeProtein = new Array();
	this.divGenome = new Array();
	this.divProtein = new Array();
	this.tableDB_G = new Array();
	this.tableDB_P = new Array();
	this.tableDB_W_URLs = new Array();
	this.tableDB_PUBMED_URLs = new Array();
	this.tableDB_G_URLs = new Array();
	this.tableDB_P_URLs = new Array();
	this.tablePubmedFullDBNameXML = new Array();
	this.tablePubmedDBNameXML = new Array();
	this.tablePubmedCountXML = new Array();
	this.tablePubmedIDsXML = new Array();
	this.selectedPubmedDB = null;
	this.wikipediaDefText = "";
	this.pPapers = new PubmedPapers();
	this.divParent.onmouseover = function () { this.style.display = ""};
	this.divParent.onmouseout = function () { this.style.display = "none"};

	if (this.divParent.style.display=="none") {
		this.divParent.style.display="";
	}
	else {
		//this.divParent.style.display="none";
	}
	
	if (this.divParent.style.display=="") {
		removeAllChildren(this.divParent);
		this.DataBaseNames();
		this.DataBaseURLs();
		//this.CreateDivW();
		//this.CreateDivP();
		//this.CreateDivGP();
		//this.CreateDivGPP();
		//this.CreateDivGPG();
		this.CreateProcessing();
		this.GetXML(0);
	}
}


TagQuery.prototype.DataBaseNames = function () {
	this.tableDB_G[0] = "Genome_1";
	this.tableDB_G[1] = "Genome_2";
	this.tableDB_G[2] = "Genome_3";
	this.tableDB_G[3] = "Genome_4";
	this.tableDB_G[4] = "Genome_5";
	this.tableDB_G[5] = "Genome_6";
	this.tableDB_P[0] = "Protein_1";
	this.tableDB_P[1] = "Protein_2";
	this.tableDB_P[2] = "Protein_3";
	this.tableDB_P[3] = "Protein_4";
	this.tableDB_P[4] = "Protein_5";
	this.tableDB_P[5] = "Protein_6";
}

TagQuery.prototype.DataBaseURLs = function () {
	this.tableDB_W_URLs[0] = "http://en.wikipedia.org/wiki/Special:Export/";
	this.tableDB_PUBMED_URLs[0] = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/egquery.fcgi";
	this.tableDB_PUBMED_URLs[1] = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi";
	this.tableDB_PUBMED_URLs[2] = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi";

	this.tableDB_G_URLs[0] = "Genome_1";
	this.tableDB_G_URLs[1] = "Genome_2";
	this.tableDB_G_URLs[2] = "Genome_3";
	this.tableDB_G_URLs[3] = "Genome_4";
	this.tableDB_G_URLs[4] = "Genome_5";
	this.tableDB_G_URLs[5] = "Genome_6";
	this.tableDB_P_URLs[0] = "Protein_1";
	this.tableDB_P_URLs[1] = "Protein_2";
	this.tableDB_P_URLs[2] = "Protein_3";
	this.tableDB_P_URLs[3] = "Protein_4";
	this.tableDB_P_URLs[4] = "Protein_5";
	this.tableDB_P_URLs[5] = "Protein_6";
}
TagQuery.prototype.CreateProcessing = function () {
	this.divParent.appendChild(document.createElementNS(xhtmlns,'br'));
	this.divParent.appendChild(document.createTextNode("Processing ..."));
	this.divParent.appendChild(document.createElementNS(xhtmlns,'br'));
}


TagQuery.prototype.CreateDivW = function () {
	removeAllChildren(this.divParent);
	//this.divW = document.createElementNS(xhtmlns,'div');
	this.divW = document.createElementNS(xhtmlns, "div");
    this.divW.className = "tagq_row";
    this.divWTitle = document.createElementNS(xhtmlns,'div');
    this.divWTitle.className = "tagq_t";
	this.divWTitle.appendChild(document.createTextNode("Wikipedia"));
	this.divW.appendChild(this.divWTitle);
    
	this.divWText = document.createElementNS(xhtmlns,'div');
	this.divWText.className = "tagq_tx";
	this.divW.appendChild(this.divWText);

	this.divWLink = document.createElementNS(xhtmlns,'div');
	this.divWLink.className = "tagq_l";
		this.aWLink = document.createElementNS(xhtmlns,'a');
		this.aWLink.href = "#nowhere";
		this.aWLink.onclick = createMethodReference(this, "onclickWMore");
		this.aWLink.appendChild(document.createTextNode("more ..."));
		this.divWLink.appendChild(this.aWLink);
	this.divWLink.appendChild(document.createElementNS(xhtmlns,'br'));
	this.divW.appendChild(this.divWLink);
	this.divParent.appendChild(this.divW);
}
TagQuery.prototype.onclickWMore = function (e) {
	var link = "http://en.wikipedia.org/wiki/" + this.tagvalue;
	window.open(link,'Wikipedia','width=800,height=800,toolbar=yes,location=yes,directories=yes,status=yes,menubar=yes,scrollbars=yes,copyhistory=yes,resizable=yes');
}
TagQuery.prototype.CreateDivP = function () {
	this.divPM = document.createElementNS(xhtmlns,'div');
    this.divPM.className = "tagq_row";
    this.divPMTitle = document.createElementNS(xhtmlns,'div');
    this.divPMTitle.className = "tagq_t";
	this.divPMTitle.appendChild(document.createTextNode("PubMed"));
	this.divPM.appendChild(this.divPMTitle);
    
	this.divPMText = document.createElementNS(xhtmlns,'div');
	this.divPMText.className = "tagq_tx";
	this.divPM.appendChild(this.divPMText);
	this.divParent.appendChild(this.divPM);
}

TagQuery.prototype.CreateDivWText = function () {
	removeAllChildren(this.divWText);
	this.divWText.appendChild(document.createTextNode(this.wikipediaDefText));
}

TagQuery.prototype.CreateDivPCountList = function () {
	removeAllChildren(this.divPMText);

	var ol = document.createElementNS(xhtmlns,'ol');
	ol.className = "tagq";
	for(var i=0; i<this.pPapers.title.length	; i++) {
		var li = document.createElementNS(xhtmlns,'li');
		li.className = "tagq";
		var linkDB = document.createElementNS(xhtmlns,'a');
		linkDB.href = "#nowhere";
		linkDB.value = this.tablePubmedIDsXML[i];
		linkDB.onclick = createMethodReference(this, "onclickPPapers");
  		linkDB.appendChild(document.createTextNode(this.pPapers.title[i] + ", " + this.pPapers.journal[i] + ", " + this.pPapers.date[i]));
		li.appendChild(linkDB);
		ol.appendChild(li);
	}
	var ul = document.createElementNS(xhtmlns,'ul');
	ul.className = "tagq";
	for(var i=0; i<this.tablePubmedDBNameXML.length; i++) {
		var li = document.createElementNS(xhtmlns,'li');
		var linkDB = document.createElementNS(xhtmlns,'a');
		linkDB.href = "#nowhere";
		linkDB.value = this.tablePubmedDBNameXML[i];
		linkDB.onclick = createMethodReference(this, "onclickPList");
  		linkDB.appendChild(document.createTextNode(this.tablePubmedFullDBNameXML[i] + ": " +  this.tablePubmedCountXML[i]) );
		li.appendChild(linkDB);
  		ul.appendChild(li);
	}

	var p = document.createElementNS(xhtmlns,'p');
	p.innerHTML = "----------------------------";
	p.className = "tagq";

	this.divPMText.appendChild(ol);
	this.divPMText.appendChild(p);		
	//this.divPMText.appendChild(document.createTextNode('----------------------------'));
	this.divPMText.appendChild(ul);
}

TagQuery.prototype.onclickPPapers = function (e) {
    var obj = this.eventTrigger (e);
    //alert(obj.value);
	var id = obj.value;
 	//var link = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id="+ id +"&retmode=ref&cmd=prlinks";
	//alert(id);
	//var link = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&db=pubmed&dopt=AbstractPlus&list_uids=" + id;
	var link = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&db=pubmed&term=" + id;
	window.open(link,'PubMed','width=800,height=800,toolbar=yes,location=yes,directories=yes,status=yes,menubar=yes,scrollbars=yes,copyhistory=yes,resizable=yes');
}

TagQuery.prototype.onclickPList = function (e) {
    var obj = this.eventTrigger (e);
    //alert(obj.value);
	var db = obj.value;
	var link = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&db=" + db + "&term=" + this.tagvalue;
	window.open(link,'PubMed','width=800,height=800,toolbar=yes,location=yes,directories=yes,status=yes,menubar=yes,scrollbars=yes,copyhistory=yes,resizable=yes');
}

TagQuery.prototype.eventTrigger = function (e){
    if (! e)
        e = event;
    return e.target || e.srcElement;
}

TagQuery.prototype.CreateDivPPapersList = function() {
	removeAllChildren(this.divPMText);
	var ul = document.createElementNS(xhtmlns,'ul');
	ul.className = "tagq";
	for(var i=0; i<this.tablePubmedDBNameXML.length; i++){
		var li = document.createElementNS(xhtmlns,'li');
		var linkDB = document.createElementNS(xhtmlns,'a');
		linkDB.href = "#nowhere";
		linkDB.value = this.tablePubmedIdsXML[i];
		linkDB.onclick = createMethodReference(this, "onclickPIDsList");
  		linkDB.appendChild( document.createTextNode(this.tablePubmedIdsXML[i]));
		li.appendChild(linkDB);
  		ul.appendChild(li);
	}
	this.divPMText.appendChild(ul);
}

TagQuery.prototype.CreateDivGP = function () {
	this.divGenomeProtein[0] = document.createElementNS(xhtmlns,'div');
    this.divGenomeProtein[0].className = "tagq_column";
	this.divGenomeProtein[0].appendChild(document.createTextNode("Genome DB"));
	this.divParent.appendChild(this.divGenomeProtein[0]);
	this.divGenomeProtein[1] = document.createElementNS(xhtmlns,'div');
    this.divGenomeProtein[1].className = "tagq_column";
	this.divGenomeProtein[1].appendChild(document.createTextNode("Protein DB"));
	this.divParent.appendChild(this.divGenomeProtein[1]);
}
TagQuery.prototype.CreateDivGPG = function () {
    for(var i=0; i<this.tableDB_G.length; i++){
    	this.divGenome[i] = document.createElementNS(xhtmlns,'div');
    	this.divGenome[i].className = "tagq_row_s";
		this.divGenome[i].appendChild(document.createTextNode(this.tableDB_G[i]));
		/*
		this.divPMLink = document.createElementNS(xhtmlns,'div');
		this.divPMLink.className = "tagq_l";
		this.aPMLink = document.createElementNS(xhtmlns,'a');
		this.aPMLink.href = "http://wiki.com";
		this.aPMLink.appendChild(document.createTextNode("more ..."));
		this.divPMLink.appendChild(this.aPMLink);
		this.divPMLink.appendChild(document.createElementNS(xhtmlns,'br'));
		this.divPM.appendChild(this.divPMLink);
		*/
		this.divGenomeProtein[0].appendChild(this.divGenome[i]);
	}
}
TagQuery.prototype.CreateDivGPP = function () {
    for(var i=0; i<this.tableDB_P.length; i++){
    	this.divProtein[i] = document.createElementNS(xhtmlns,'div');
    	this.divProtein[i].className = "tagq_row_s";
		this.divProtein[i].appendChild(document.createTextNode(this.tableDB_P[i]));
		this.divGenomeProtein[1].appendChild(this.divProtein[i]);
	}
}

TagQuery.prototype.GetXML = function (dbType) {
	var requesturl = null;
	if(dbType == 0) {
		requesturl = this.serverURL + this.tableDB_W_URLs[0] + this.tagvalue;
		//alert(requesturl);
    	makeRequest(requesturl, this.parseGetWikiXML, this, "get", "");
	}
	else if(dbType == 1) {
		requesturl = this.serverURL + this.tableDB_PUBMED_URLs[0] + "?term=" + this.tagvalue;
		//alert(requesturl);
    	makeRequest(requesturl, this.parseGetPubmedListXML, this, "get", "");
	}
	else if(dbType == 2) {
		requesturl = this.serverURL + this.tableDB_PUBMED_URLs[1] + this.encodeURL("?db=pubmed" + "&term=" + this.tagvalue + "+AND+review[pt]"); //+ " and review"
		//alert(requesturl);
    	makeRequest(requesturl, this.parseGetPubmedDBXML, this, "get", "");
	}
	else if(dbType == 3) {
		var ids = "";
		for(var i=0; i<5; i++) //this.tablePubmedIDsXML.length
			ids += "" + this.tablePubmedIDsXML[i] + ","
		ids = ids.substring(0,ids.length-1);
		requesturl = this.serverURL + this.tableDB_PUBMED_URLs[2] + this.encodeURL("?db=pubmed" + "&id=" + ids);
		//alert(this.tablePubmedIDsXML[0]);
    	makeRequest(requesturl, this.parseGetPubmedPapersXML, this, "get", "");
	}
}

TagQuery.prototype.parseGetWikiXML = function ( data, results ) {
	//alert( results );
	var tags = results.getElementsByTagName("text");
	if (tags.length==0) {
		clog('Error on Wikipedia response:' + results);
		_tagq.wikipediaDefText = "Invalid response from Wikipedia.";
		_tagq.CreateDivW();
		_tagq.CreateDivP();
		_tagq.CreateDivWText();
		_tagq.GetXML(1);
		return 'error';
	}
	else {
		var text = tags.item(0).childNodes[0];
		//var text = tags.firstChild;
		var str = text.data;
		var pos1 = 0;
		var pos2 = 0;
		var str_r = "";
		var regExp = null;
		//regExp = /[^''']/g;	// ..............'''cell is ...
		//str = str.replace(regExp,"");
		regExp = /:''[^'''](.|\n)*'''/g;	//:''For the fictional extraterrestrial species in British scifi drama Doctor Who, see ..'''
		str = str.replace(regExp,"");

		//alert(str);
		regExp = /\{\{[^\}]*\}\}/g;	//{{TEXT}}
		str = str.replace(regExp,"");
		regExp = /<!--[^-]*-->/g;	//<!-- Comment -->
		str = str.replace(regExp,"");
		regExp = /==/g;	//==
		str = str.replace(regExp,"");
		regExp = /==\*/g;	//==*
		str = str.replace(regExp,"");
		regExp = /\[\[[^\]]*\]\](.|\s)/g;	//see [[List of topics in cell biology]] 
		str = str.replace(regExp,"");
		regExp = /\[\[Image:[^\]]*\]\]/g;	//[[Image: .....]]
		str = str.replace(regExp,"");
		regExp = /<ref>[^<]*<\/ref>/g;	//<ref>{{KMLEref|artery|07-04-17}}</ref> 
		str = str.replace(regExp,"");
		regExp = /""/g;		//"" 
		str = str.replace(regExp,"");
	
		//alert(str);
	
		var str_s = str.split(" ");
		var l = 0;
		if(str_s.length > 50)
			l = 50
		else 
			l = str_s.length;
		for(var i=0; i<l; i++)
			_tagq.wikipediaDefText += str_s[i]+" ";
		//alert(_tagq.wikipediaDefText);	
		_tagq.CreateDivW();
		_tagq.CreateDivP();
		_tagq.CreateDivWText();
		_tagq.GetXML(1);
	}
}

TagQuery.prototype.parseGetPubmedListXML = function ( data, results ) {
	//alert( results );
	var tags = results.getElementsByTagName("ResultItem");
	for (var i = 0 ; i < tags.length ; i++) {
		// get one tag after another
		var tag = tags[i];
		var DbName =  tag.getElementsByTagName("DbName")[0].firstChild.nodeValue;
		var MenuName = tag.getElementsByTagName("MenuName")[0].firstChild.nodeValue;
		var Count = tag.getElementsByTagName("Count")[0].firstChild.nodeValue;
		_tagq.tablePubmedDBNameXML[i] = DbName;
		_tagq.tablePubmedFullDBNameXML[i] = MenuName;
		_tagq.tablePubmedCountXML[i] = Count;
	}
	_tagq.GetXML(2);
}
TagQuery.prototype.parseGetPubmedDBXML = function ( data, results ) {
	//alert( results );
	var tags = results.getElementsByTagName("Id");
	//alert(tags.length);
	for (var i = 0 ; i < tags.length ; i++) {
		// get one tag after another
		var tag = tags[i].firstChild.nodeValue;
		_tagq.tablePubmedIDsXML[i] = tag;
	}
	//alert(_tagq.tablePubmedIDsXML[0]);
	_tagq.GetXML(3)
}

TagQuery.prototype.parseGetPubmedPapersXML = function ( data, results ) {
	var tags = results.getElementsByTagName("DocSum");
	//alert(tags.length);
	var index = 0;
	for (var i = 0; i < tags.length; i++) {
		var tag = tags[i];
		var node = tag.getElementsByTagName("Item")
		//alert(node.length);
		for (var j = 0; j < node.length; j++) {
			var element = node.item(j);
			var name = element.getAttribute("Name");
			if (name == "Title")
				var title = node[j].firstChild.nodeValue;
			else if (name == "PubDate")
				var date = node[j].firstChild.nodeValue;
			else if (name == "Source")
				var journal = node[j].firstChild.nodeValue;
		}
		_tagq.pPapers.title[index] = title;
		_tagq.pPapers.date[index] = date;
		_tagq.pPapers.journal[index] = journal;
		index ++;
	}
	//alert(_tagq.pPapers.title);
	_tagq.CreateDivW();
	_tagq.CreateDivP();
	_tagq.CreateDivWText();
	_tagq.CreateDivPCountList();

}
/*
TagQuery.prototype.encodeURL = function (str) {
	var result = "";
	for (i = 0; i < str.length; i++) {
		if (str.charAt(i) == " ") result += "+"; //was "+"
		else result += str.charAt(i);
	}
	return escape(result);
}
*/
TagQuery.prototype.encodeURL = function (str) {
    return escape(str)
       .replace(/\+/g, '%2B')
          .replace(/\"/g,'%22')
             .replace(/\'/g, '%27');
}

function PubmedPapers() {
	this.title = new Array();
	this.journal = new Array();
	this.date = new Array();
	this.id = new Array();
} 
// ]]>
