///////////////////////////////////////////////////////
// Resource Tag viewer (and editor)
// Show and manipulate nested tags  associated 
// with a bisque resource.

//////////////////////////////////
// TagPlugin: a plugin base clase
// for TagsetViewer extenstions.
function TagPlugin (viewer, name) {
    this.viewer= viewer || null;   // The top level viewer 
    this.name  = name || "";    // name for logging and such
}
// NEWRESOURCE
//  Called when reloading a new object
TagPlugin.prototype.newResource = function (){}
// CREATE
// Create HTML elements needed by this plugin
TagPlugin.prototype.create = function (parentdiv){
    return parentdiv;
}
// UPDATE
//  Called after the state change, allows plugin to reconfigure
TagPlugin.prototype.update = function (){}
// RENDER/REFRESH?
//  Show (fill out elements ) 
TagPlugin.prototype.refresh = function (){}
function DefaultTagPlugin(view,name){
    this.base = TagPlugin;
    this.base(view,name);
}
///////////////////////////////////////
// TagsetViewer
function TagsetViewer(taggerdiv, resource, user, plugin_list) {
    this.target = getObj(taggerdiv);
    this.user = user;
    this.plugins = []; // Ordered array of plugin 

    this.command_bar = [];
    this.groups = {};
    this.menudiv = document.createElementNS (xhtmlns, "div");
    this.menudiv.setAttributeNS (null, "id", "tagmenu");
    this.menudiv.className = "buttonbar";
    this.target.appendChild (this.menudiv);
    this.tagdiv = document.createElementNS (xhtmlns, "div");
    //this.imagediv.setAttributeNS (null, "id", "tagdiv");
    this.tagdiv.className = "tag_viewer_display";
    this.target.appendChild (this.tagdiv);

    this.state = {};
    // Add requested plugins.
    if (plugin_list==null || plugin_list == "all") {
        plugin_list = "default,editor,mover,ops,filter,links";
    }

    if (!this.user) {
        plugin_list = plugin_list.replace('editor,', '');
    }

    var plugin_names = plugin_list.split(',');
    for (var i=0; i < plugin_names.length; i++) {
        // Parse names s.t. "plugin[(flag1, flag2, ...)]"
        var m = /(\w+)(?:\(([\w,]*)\))?/.exec(plugin_names[i]);
        var name = m[1];
        var flags = m[2];
        
        var ctor = TagsetViewer.plugins[name];
        if (ctor)
            this.addPlugin (new ctor(this, name, flags));
    }
    this.createPlugins(this.tagdiv);
    this.load(resource);
}

TagsetViewer.plugins = {
    'default': DefaultTagPlugin,
    'editor' : TagEditor,
    'mover'  : TagMover,
    'ops'    : TagTypeOps,
    'file'   : UploadFileTag,
    'filter' : FilterUsers,
    'links'  : RewriteLinks,
}
TagsetViewer.prototype.destroy = function  () {
    removeAllChildren (this.target);
    this.top_element.destroy();
}
    
TagsetViewer.prototype.addPlugin = function  (plugin) {
    this.plugins.push (plugin);
    return plugin
};
TagsetViewer.prototype.createPlugins = function (parent) {
    var currentdiv = parent;
    for (var i = 0; i < this.plugins.length; i++) {
        var plugin = this.plugins[i];
        currentdiv = plugin.create (currentdiv);
    }
}
TagsetViewer.prototype.addCommand =function (text, callback, position){
    position = (position==null)? this.command_bar.length : position;

    var button = document.createElementNS (xhtmlns, "button");
    button.innerHTML = text;
    button.setAttribute('id', text);
    button.onclick = callback;
    button.className = "tagview_button";
    //menu.appendChild (button);
    this.command_bar.splice( position, 0, button)

    return button;
}

TagsetViewer.prototype.createCombo = function (name, items, defval,cb , position){
    position = (position==null)? this.command_bar.length : position;
    var combo= document.createElementNS(xhtmlns, 'select');
    combo.className = "tagview_button";
    for (var i=0; i< items.length; i++) {
        var option = this.addComboOption (combo, items[i]);
        option.selected = (option.text == defval);
    }
    var labelcombo = document.createElementNS(xhtmlns, 'span');
    var label = document.createElementNS(xhtmlns, 'label');
    label.textContent = name;
   
    labelcombo.className = "tagview_button";
    labelcombo.appendChild (label);
    labelcombo.appendChild (combo);    
    //this.menudiv.appendChild (div);
    this.command_bar.splice(position, 0, labelcombo)

  	combo.onchange = cb;
    return combo;
}
TagsetViewer.prototype.addComboOption = function (combo, item){
    var option = document.createElementNS(xhtmlns, 'option');
    option.text =  item[0];
    option.value = item[1];
    combo.appendChild (option);
    return option;
}

TagsetViewer.prototype.remCommand =function (button){
    var menu= this.menudiv;
    bt = menu.firstChild ;
    while (bt) {
        if (bt == button){
            menu.removeChild(bt);
            return;
        }
        bt = bt.nextSibling;
    }
}

TagsetViewer.prototype.load = function (resource){
    if (resource instanceof BQObject){
        this.resourceuri = resource.uri;
        this.newResource(resource);
    }else{
        this.resourceuri = resource;
        BQFactory.load (this.resourceuri, callback(this, "load_tags"));
    }
};
TagsetViewer.prototype.newResource = function (bq){
    bq.load_tags(callback (this, 'loaded', bq) );
}

TagsetViewer.prototype.save = function (){
    this.top_tag.save_(this.resourceuri);
    delete this.state['need_save'];
    this.refresh();
};

TagsetViewer.prototype.loaded = function (bq) {
    this.resource = bq;

    //this.top_tag = new BQResource(bq.uri +'/tags', bq.doc);
    this.top_tag = new BQResource(bq.uri +'/tags'); // Make it it's own doc for the moment
    this.top_tag.tags = bq.tags;
    //if (this.resourceuri) 
    //    this.top_tag.uri = this.resourceuri + "/tags";

    this.top_tag.name = "Tags";
    this.top_tag.value = "";
    //this.top_tag.owner = this.user;


    this.createElements();
    this.top_element.editable = false;
    this.top_element.opened = true;

    this.command_bar = [];
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.newResource ();
    }
    this.update ();
}


TagsetViewer.prototype.createElements = function () {
    this.top_element = new TagElement (this.top_tag);
    var stack = [];
    stack.push ([this.top_tag, this.top_element, null]);
    while (stack.length != 0) {
        var el = stack.shift();
        var node = el[0];
        var elem = el[1];
        var parent = el[2];
        if (elem == null) 
            elem = new TagElement (node, parent);
        if (parent) 
            parent.children.push (elem);
        if (node.tags)
            for (var i=0; i < node.tags.length; i++ ) 
		     if (node.tags[i] != null) 
                stack.push ([node.tags[i], null, elem]);
    }
}
TagsetViewer.prototype.index_elements = function () {
	this.top_element.index_element(0);
}


// Update the current tag tree by calling update_element 
// on each plugin in uplugin order..
TagsetViewer.prototype.update = function () {
    removeAllChildren(this.tagdiv);    
    this.createDivs();
    this.index_elements();
	
    visit_all (this.top_element, callback(this, 'update_element'));

    this.refresh();
}


TagsetViewer.prototype.update_element = function (tel) {
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.update_element (tel);
    }
}

TagsetViewer.prototype.createDivs = function () {
    this.top_element.create_divs(this.tagdiv);
}
TagsetViewer.prototype.renderElements = function (){
}
TagsetViewer.prototype.need_update = function () {
    this.update();
}
TagsetViewer.prototype.refresh = function (){
    // Refresh plugins
    for (var i = 0; i < this.plugins.length; i++) {
        plugin = this.plugins[i];
        plugin.refresh ();
    }
    // Refresh command bar
    removeAllChildren(this.menudiv);    
    for (var i = 0; i < this.command_bar.length; i++) {
        var c = this.command_bar[i];
        if (c != null) 
            this.menudiv.appendChild (c);
    }    

    // Refresh Tagelements
    visit_all (this.top_element, 
               function (tel) {
                   if (tel.renderer) tel.renderer(tel);
               });


}
//////////////////////////////////////////////////
//////////////////////////////////////////////////
// TagElement 
// A single (nested) tag and it's display properties
// Tag Elements are held is a parallel hierarchy of the tags
// themselves and contains the display components needed to view 
// the tags tree.
function TagElement (bqtag,  parent){
    this.tag = bqtag;
    this.parent = parent;       // MEMORY LEAK HERE
    this.visible = true;
    this.editable = true;
    this.children = [];
    this.commands = [];

    this.opened = false;        // Show children
    this.renderer = null;
    this.divs = null;
}
TagElement.prototype.destroy = function() {
    this.parent = null;
    for (var i=0; i < this.children.length; i++ ) 
        this.children[i].destroy ();
    this.children = null;
    //delete this;
}

TagElement.prototype.getkids = function() {
    return  this.children
}


TagElement.prototype.addEvent =function (event, cb) {
    this.divs.view[event] = cb;
}

TagElement.prototype.create_element_divs = function (){
    // Element ->
    //  Lcommand : commands : view : [children] 
    //
    var element = document.createElementNS(xhtmlns, 'div');
    element.className = "tagelement";
    if (this.children.length > 0) {
        var lcommands = document.createElementNS(xhtmlns, 'div');
        lcommands.className = "tagelement_lcommand";
        element.appendChild(lcommands);
    }
    var commands = document.createElementNS(xhtmlns, 'div');
    commands.id = "commands";
    commands.className = "tagelement_rcommand";
    element.appendChild(commands);

    var view = document.createElementNS(xhtmlns, 'div');
    view.id = 'view';
    view.className = "tagelement_view";
    element.appendChild(view);

    if (this.children.length > 0) {
        var children = document.createElementNS(xhtmlns, 'div');
        children.id = 'children';
        children.className = 'tagelement_children';
        element.appendChild(children)
    }    
    
    return { element:element, 
             lcommands:lcommands, 
             commands: commands,
             view:view, 
             children:children };
}
TagElement.prototype.create_divs = function (parent_div){
    this.divs = this.create_element_divs();
    parent_div.appendChild (this.divs.element);
    for (var i=0; i < this.children.length; i++ ) 
        this.children[i].create_divs (this.divs.children);
}
TagElement.prototype.index_element = function (index){
	this.tag.index = index;
	for (var i=0; i < this.children.length; i++ ) 
	   this.children[i].index_element (i);
}


TagElement.prototype.show_subdivs = function(x) {
    if (x== true) x = "";
    else x = "none";

    this.divs.view.style.display = x;
    this.divs.commands.style.display = x;
    if (this.divs.lcommands ) this.divs.lcommands.style.display = x;
    if (this.divs.children) this.divs.children.style.display = x;
}

TagElement.prototype.addCommand = function (title, help, cb, kind){
    //this.commands.push ([ title, help, cb]);
    
    var com = document.createElementNS(xhtmlns, 'span');
    com.className = "tagview_command"; 
    com.setAttribute('id', title);       
    //com.style.marginRight = "4px";
    com.textContent = title;
    com.title = help;
    com.onmousedown = cb;
    com.onmouseover = function () { this.style.cursor = "pointer"; }

    if (kind && kind == "control") 
        this.divs.lcommands.appendChild(com);
    else
        this.divs.commands.appendChild(com);
    
    return com;
}

TagElement.prototype.render_commands = function (command_list, div){
    for (var i=0; i<command_list.length; i++){
        var item = command_list[i];
        var title = item[0];
        var help = item[1];
        var cb = item[2];
        /*
        var com = document.createElementNS(xhtmlns, 'span');
        com.style.marginRight = "4px";
        com.textContent = title;
        com.title = help;
        com.onmousedown = cb;
        com.onmouseover = function () { this.style.cursor = "pointer"; }
        */
        
        var com = document.createElementNS (xhtmlns, "button");
        com.className = "tagview_speedbutton";
        com.setAttribute('id', title);
        com.innerHTML = title;
        com.title = help;    
        com.onclick = cb;
        
        div.appendChild(com);
    }
}
//////////////////////////////////////////////////
//////////////////////////////////////////////////
// Default tag plugin:
// Basic viewing of tags as a tree.
DefaultTagPlugin.prototype=new TagPlugin();

DefaultTagPlugin.prototype.update_element = function (tel) {
    var p = this;
    var nm = document.createElementNS(xhtmlns, 'b');
    tel.divs.view.appendChild(nm);
    var val = document.createElementNS(xhtmlns, 'span');
    tel.divs.view.appendChild(nm);
    tel.divs.view.appendChild(val);
    tel.divs.name= nm;
    tel.divs.val= val;
    tel.renderer = DefaultTagPlugin.render_element;
    if (tel.children.length > 0) {
        tel.addCommand(tel.opened?"[- ":"[+ ", "Open/Collapse", 
                       callback(p, "toggle", tel),
                       "control");
    }
}

DefaultTagPlugin.render_element = function (tel) {
    if (tel.children.length > 0) {
        tel.divs.children.style.marginLeft = "20px";
    }

    tel.divs.name.textContent = tel.tag.name + ' : ';
    tel.divs.val.textContent = tel.tag.value;	
    if (tel.divs.children) 
        tel.divs.children.style.display = tel.opened?"":"none";
}



DefaultTagPlugin.prototype.toggle = function (tel) {
    if (tel.opened) {
        tel.divs.children.style.display = "none";
        tel.opened = false;
        tel.divs.lcommands.firstChild.textContent = "[+";
    } else {
        tel.divs.children.style.display = "";
        tel.opened = true;
        tel.divs.lcommands.firstChild.textContent = "[-";
    }
}

//////////////////////////////////////////////////
// Tag Editor 
// Add the ability to edit tags
    function TagEditor (viewer,name, flags){
    this.base = TagPlugin;
    this.base(viewer, name);
    this.flags = flags || "";
}
TagEditor.prototype = new TagPlugin();
TagEditor.prototype.newResource = function () {
    this.btn_add = this.viewer.addCommand ("Add Tag", 
                                           callback(this, "newTag", this.viewer.top_element));
    this.btn_save = this.viewer.addCommand ("Save Changes", 
                                            callback(this.viewer, "save"));
}
TagEditor.prototype.refresh = function () {
    this.refresh_commands();
}

TagEditor.prototype.refresh_commands = function () {
    this.btn_add.style.display=('readonly' in this.viewer.state)?"none":"";
    this.btn_save.style.display=('need_save' in this.viewer.state)?"":"none";
    if ( this.flags.match('nosave'))
        this.btn_save.style.display="none";
}

TagEditor.prototype.update_element = function (tel) {
    var edit = this;
//    if (tel.tag.owner !=  this.viewer.user){
//        return
//    }
    if (tel.editable ) {
        //tel.addEvent('onmouseover', callback(edit,'over_element', tel));
        //tel.addEvent('onmouseout', callback(edit,'out_element', tel));
        //tel.addEvent('onmouseup', callback(edit,'edit', tel));

        tel.divs.view.onmouseover = callback(edit, 'over_element', tel);
        tel.divs.view.onmouseout = callback(edit, 'out_element', tel);
        //tel.divs.view.onmouseup = callback(edit, 'edit', tel);

        tel.divs.name.onmouseup = callback(edit, 'edit', tel);
        tel.divs.val.onmouseup = callback(edit, 'edit', tel);
        
        tel.addCommand("x", "Delete this tag/value pair.", 
                       callback(edit, 'deleteTag', tel));
    }
    tel.addCommand("+tag", "Add Child.", 
                   callback(edit, 'newTag', tel));
}


TagEditor.prototype.over_element = function (tel) {
    tel.divs.view.style.background = "#ffc";
}
TagEditor.prototype.out_element = function (tel) {
    tel.divs.view.style.background = null;
}
TagEditor.prototype.newTag = function (parent) {
    // Append a new element to parent;
    var tag = new BQTag();
    tag.name ="New Tag";
    tag.value ="New Value";
    tag.owner = this.viewer.user;

    parent.tag.addtag (tag);  //? Should we do this already

    var el = new TagElement (tag, parent);
    parent.children.push(el);
    this.viewer.update();
}
TagEditor.prototype.edit = function (tel) {
    if (this.viewer.operation) 
        this.viewer.operation();

    if (tel.edit == null) {
        edit_commands = [];
        edit_commands.push(["Cancel", "Cancel this edit", 
                                callback(this, 'cancelEdit', tel)]);
        edit_commands.push(["Done", "Finish editing this tag", 
                                callback(this, 'closeTag', tel)]);

        var edit = {};
        edit.element = document.createElementNS (xhtmlns, "div");
        edit.element.id ="EDIT";
        edit.view = document.createElementNS (xhtmlns, "div");
        edit.view.className = "tagelement_view";
        edit.commands = document.createElementNS (xhtmlns, "div");
        edit.commands.className="tagelement_rcommand";
        edit.element.appendChild (edit.commands);
        edit.element.appendChild (edit.view);

		    var name = document.createElementNS(xhtmlns, 'input');
		    name.type= 'text';
		    name.className = "tagelement_input";
		    //name.style.marginLeft = "20px";
        edit.name = name;
        edit.view.className = "tagelement_view";
        edit.view.appendChild(name);
		    var value = document.createElementNS(xhtmlns, 'input');
		    value.type= 'text';
		    value.className = "tagelement_input";
		    //value.style.marginLeft = "20px";
        edit.value = value;
        edit.view.appendChild(value);

        tel.edit = edit;
        tel.divs.element.appendChild(tel.edit.element);
        tel.render_commands (edit_commands, tel.edit.commands);
    }
    tel.show_subdivs(false);
    tel.edit.element.style.display = "";
    tel.edit.name.value = tel.tag.name;
    tel.edit.value.value = tel.tag.value;
    this.viewer.operation = callback(this, "closeTag", tel);
}

TagEditor.prototype.cancelEdit =function (tel){
    tel.edit.element.style.display = "none";
    tel.show_subdivs(true);
    this.viewer.operation = null;
}
TagEditor.prototype.deleteTag =function (tel){
    var ok= window.confirm ("Really delete this tag?");
    if (!ok) return;
        
    // Remove the element from the server
    if (tel.tag.uri != null)
        tel.tag.delete_(callback(this, 'deleteResponse', tel));
    else 
        this.deleteResponse(tel, null);
}
TagEditor.prototype.deleteResponse =function (tel, gob){
    var i = tel.parent.children.indexOf (tel);
    if (i!=null) {
        tel.parent.children.splice(i,1);
        tel.parent.tag.remove (tel.tag)
        this.viewer.update();
    }
}


TagEditor.prototype.saveTag =function (tel){
    // Save the element
    var parent_tag = tel.parent.tag;
    clog ("saving tag with " + parent_tag.uri);
    tel.tag.name = tel.edit.name.value;
    tel.tag.value = tel.edit.value.value;
    if (parent_tag.uri == null) {
        clog ("can't save a tag without a parent");
    } else {
        if (! this.flags.match ('nosave')) {
            //parent_tag.addtag(tel.tag) 
            tel.tag.save_(parent_tag.uri);
        }
    }
    this.cancelEdit(tel);
    //this.viewer.update();
    this.viewer.operation = null;
    this.viewer.refresh();
}


TagEditor.prototype.closeTag =function (tel){
    // Save the element
    var parent_tag = tel.parent.tag;
    clog ("saving tag with " + parent_tag.uri);
    if (tel.tag.name != tel.edit.name.value
        ||     tel.tag.value != tel.edit.value.value)
        this.viewer.state['need_save'] = true;
    tel.tag.name = tel.edit.name.value;
    tel.tag.value = tel.edit.value.value;
    this.cancelEdit(tel);
    //this.viewer.update();
    this.viewer.refresh();
    this.viewer.operation = null;
}

//////////////////////////////////////////////////
// Tag Editor 
// Add the ability to edit tags
function TagMover (viewer,name){
    this.base = TagPlugin;
    this.base(viewer, name);
}
TagMover.prototype = new TagPlugin();
TagMover.prototype.newResource = function () {
    this.viewer.addCommand ("Sort by name", 
       callback(this, "sortTags", this.viewer.top_element, "name"));
    this.viewer.addCommand ("Sort by index", 
       callback(this, "sortTags", this.viewer.top_element, "index"));
}
TagMover.prototype.update_element = function (tel) {
    // Visit each element and add moving buttons.
    var p = this;
    if (tel.visible && tel.parent != null) {
        tel.addCommand("^", "Raise the tag", callback(p, 'raiseTag', tel));
        tel.addCommand("v", "Move this tag/value pair down in order.",
                       callback(p, 'lowerTag', tel));
    }
}

TagMover.prototype.raiseTag =function (tel){
    var i = tel.parent.children.indexOf (tel);
    if ( i && i -1 >= 0 ) {
        var c = tel.parent.children[i-1];
        tel.parent.children[i-1] = tel.parent.children[i];
        tel.parent.children[i] = c;

        this.viewer.update();
    }	
}

TagMover.prototype.lowerTag =function (tel){
    var i = tel.parent.children.indexOf (tel);
    if ( i && i+1 < tel.parent.children.length ) {
        var c = tel.parent.children[i+1];
        tel.parent.children[i+1] = tel.parent.children[i];
        tel.parent.children[i] = c;

        this.viewer.update();
    }	
}
TagMover.sortByIndex=function (a, b){ return (a.tag.index-b.tag.index);};
TagMover.sortByName=function (a, b){ 
    return a.tag.name.localeCompare(b.tag.name); 
};
TagMover.prototype.sortTags =function (tel, by){
    if (by == "name") {
        tel.children.sort(TagMover.sortByName);
    } else {
        tel.children.sort(TagMover.sortByIndex);
    }
    this.viewer.update();
}
//////////////////////////////////////////////////
// Operations on tags (Should rethink this) 

function TagTypeOps (viewer,name){
    this.base = TagPlugin;
    this.base(viewer, name);
}
TagTypeOps.prototype = new TagPlugin();

TagTypeOps.prototype.update_element = function (tel) {
    var ops = this;
    if (tel.tag.value && tel.tag.value != "") {
        tel.addCommand ("Q", "Query Databases",
                        callback(ops, "query_databases",tel));
    }
    if (tel.tag && tel.tag.type == "file") {
        var thefile = tel.tag.value;
        tel.addCommand ("F", "Download File",
                        function () {
                            window.location = thefile;
                        });
    }
    if (tel.tag 
        && (tel.tag.type == "image"  
            || tel.tag.type == "link"
            || (tel.tag.value &&
                (tel.tag.value.indexOf ("http://") == 0
                 || tel.tag.value.indexOf ("https://") == 0)))) {
	  var theimage = tel.tag.value;
	  tel.addCommand ("U", "View Resource",
			  function () {
                            window.location = "/bisquik/view?resource="+theimage;
			  });
    }
}


TagTypeOps.prototype.query_databases = function (tel) {
	if(tel.divs.querydiv != null) {
		removeAllChildren(tel.divs.querydiv);
		this.viewer.tagdiv.removeChild(tel.divs.querydiv);
	}
	var querydiv = document.createElementNS(xhtmlns, 'div');
	querydiv.className = "tagelement_querydb";
	querydiv.style.left = getX(tel.divs.view)+170 + "px";
	querydiv.style.top  =  getY(tel.divs.view)-10 + 18 + "px";
    tel.divs.querydiv = querydiv;
	var tq = new TagQuery(tel.divs.querydiv, tel.tag.value);
	this.viewer.tagdiv.appendChild( tel.divs.querydiv );
};

//////////////////////////////////////////////////
// Image Tag Editor 
function ImageTagEditor (viewer,name){
    this.base = TagPlugin;
    this.base(viewer, name);
}
ImageTagEditor.prototype = new TagPlugin();
ImageTagEditor.prototype.update_element = function (tel) {
    if (tel.tag.type == "image") {
        tel.renderer = callback(edit, "render_image");
    }
}
ImageTagEditor.prototype.render_image = function (tel) {
    // Change the view box to be an image.

}


//////////////////////////////////////////////////
// Upload File
// Upload a file a create a tag with the file
function UploadFileTag (viewer,name){
    this.base = TagPlugin;
    this.base(viewer, name);
}
UploadFileTag.prototype = new TagPlugin();
UploadFileTag.prototype.newResource = function () {
    this.viewer.addCommand ("Attach File", callback(this, "uploadFile"));
}
UploadFileTag.prototype.uploadFile = function () {
}

//////////////////////////////////////////////////
// rewiteLinks
// Upload a file a create a tag with the file
function RewriteLinks (viewer,name){
    this.base = TagPlugin;
    this.base(viewer, name);
}
RewriteLinks.prototype = new TagPlugin();
RewriteLinks.prototype.newResource = function () {
    //this.viewer.addCommand ("Attach File", callback(this, "uploadFile"));
}

RewriteLinks.prototype.update_element = function (tel) {
    if (tel.tag.value.indexOf("http:")==0 || tel.tag.value.indexOf ("https:")==0) {
        tel.renderer = this.render_element;
        tel.divs.val.onmouseup = null;        
    }
}
RewriteLinks.prototype.render_element = function (tel) {
    if (tel.children.length > 0) {
        tel.divs.children.style.marginLeft = "20px";
    }

    tel.divs.name.textContent = tel.tag.name + ' : ';
    var a = document.createElementNS (xhtmlns, "a");
    a.href = tel.tag.value;
    a.innerHTML = tel.tag.value;
    a.target = "_blank";
    removeAllChildren(tel.divs.val);
    tel.divs.val.appendChild (a);
    if (tel.divs.children) 
        tel.divs.children.style.display = tel.opened?"":"none";
 
}


//////////////////////////////////////////////////
// Filter user tags
// Show tags by specified user.
function FilterUsers (viewer,name){
    this.base = TagPlugin;
    this.base(viewer, name);
}
FilterUsers.prototype = new TagPlugin();
FilterUsers.prototype.newResource = function () {
    this.current_user = 0;
    // Scan tags for user id 
    var users = [];
    visit_all (this.viewer.top_element, 
               function (tel) {
                   var owner = tel.tag.owner;
                   if (owner && users.indexOf(owner) == -1)
                       users.push (owner);
               });

    this.combo = this.viewer.createCombo ("users", [], null,
                                          callback(this, "set_user"));

    if (users.length > 1) {
        this.viewer.addComboOption(this.combo,["Any" , "Any"]);
    }
    this.current_user = "Any";

    for (var i=0; i < users.length; i++) {
        BQFactory.load (users[i], callback(this, 'addUser'));
    }
}
FilterUsers.prototype.addUser = function (bquser) {
    this.viewer.addComboOption(this.combo,[bquser.display_name,bquser.uri]);
}

FilterUsers.prototype.set_user = function () {
    this.current_user = this.combo.value;
    this.viewer.update();
}
FilterUsers.prototype.toggle_perm = function (tel) {
    tel.tag.perm = (tel.tag.perm=="0")?"1":"0";
    tel.tag.save_();
    this.viewer.update();
}

FilterUsers.prototype.update_element = function (tel) {
    var owner = tel.tag.owner;
    var current = this.current_user;
    var user = this.viewer.user;
    var filter = this;

    // Element is visible 
    //    if current filter is disabled 
    //       or the element has an owner and is current
    if (current == "Any" || (owner == undefined || current == owner)) {
        tel.divs.element.style.display = "";
        
        if (owner && owner == user) 
            tel.addCommand (tel.tag.perm=="0"?"O":"P", 
                            "Toggle Open/Private ",
                            callback(filter, "toggle_perm", tel));
    } else {
        tel.divs.element.style.display = "none";
    }
}



