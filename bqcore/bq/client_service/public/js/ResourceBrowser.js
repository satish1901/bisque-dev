
// FILL in new BROWSER here  .. use div id=newbrowser

function ResourceBrowser(parentdiv) {

    this.window = new Ext.Window ({
        renderTo: parentdiv,
        height : 300,
        width  : 500,
    });
    BQFactory.load ("/ds/images?limit=10", callback(this, 'showimage'));
    this.window.show();
}

ResourceBrowser.prototype.showimage = function (resources) {

    var m = [];
    for (var i = 0; i < resources.children.length; i++) {
        m.push (resources.children[i].uri);
    }
    alert ("my list " + m);
}