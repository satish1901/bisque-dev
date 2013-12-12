/*Ext.onReady(function()
 {
 // Dynamically include all the script files associated with ResourceBrowser package
 Ext.Loader.setConfig({enabled:true});
 Ext.Loader.setPath('ResourceBrowser', '/js/ResourceBrowser/');
 Ext.Loader.setPath('ResourceBrowser.ResourceFactory', '/js/ResourceBrowser/ResourceFactory/');

 'ResourceBrowser.Browser',

 'ResourceBrowser.LayoutFactory',
 'ResourceBrowser.Organizer',
 'ResourceBrowser.ResourceQueue',
 'ResourceBrowser.DatasetManager',
 'ResourceBrowser.CommandBar',
 'ResourceBrowser.viewStateManager',

 'ResourceBrowser.ResourceFactory.ResourceFactory',
 //'ResourceBrowser.ResourceFactory.ResourceImage',
 'ResourceBrowser.ResourceFactory.ResourceMex',
 'ResourceBrowser.ResourceFactory.ResourceModule',

 'ResourceBrowser.Misc.MessageBus',
 'ResourceBrowser.Misc.GestureManager',
 'ResourceBrowser.Misc.ComponentDataView',
 'ResourceBrowser.Misc.Slider',
 'ResourceBrowser.Misc.DataTip'

 // ResourceBrowser core files

 Ext.require('/js/ResourceBrowser/Browser');
 Ext.require('/js/ResourceBrowser/LayoutFactory');
 Ext.require('/js/ResourceBrowser/ResourceFactory/ResourceFactory');

 Ext.require('/js/ResourceBrowser/ResourceFactory/ResourceImage');

 /*
 Ext.require('ResourceBrowser.LayoutFactory');
 Ext.require('ResourceBrowser.Organizer');
 Ext.require('ResourceBrowser.ResourceQueue');
 Ext.require('ResourceBrowser.DatasetManager');
 Ext.require('ResourceBrowser.CommandBar');
 Ext.require('ResourceBrowser.viewStateManager');

 // ResourceFactory files
 Ext.require('ResourceBrowser.ResourceFactory.ResourceFactory');
 Ext.require('ResourceBrowser.ResourceFactory.ResourceImage');
 Ext.require('ResourceBrowser.ResourceFactory.ResourceMex');
 Ext.require('ResourceBrowser.ResourceFactory.ResourceModule');

 // Misc
 Ext.require('ResourceBrowser.Misc.MessageBus');
 Ext.require('ResourceBrowser.Misc.GestureManager');
 Ext.require('ResourceBrowser.Misc.ComponentDataView');
 Ext.require('ResourceBrowser.Misc.Slider');
 Ext.require('ResourceBrowser.Misc.DataTip');

 Ext.Loader.onReady(function()
 {debugger;
 var resourceBrowser = new Bisque.ResourceBrowser.Browser(
 {
 'layout'	: 	'${layout}',
 'height'	:	'100%',
 'viewMode'	:	'ViewerOnly',
 'dataset'	:	bq.url('${dataset}'),
 'tagQuery'	:	'${query}',
 'tagOrder'	:	'${tagOrder}',
 'offset'	:	'${offset}',
 'wpublic'	: 	'${wpublic}'
 });

 resourceBrowser.on('Select', function(resourceURL)
 {
 window.open(bq.url('/client_service/view?resource='+resourceURL)); }
 );

 // Add ResourceBrowser to BQApp's centerPanel
 BQApp.main.getComponent('centerEl').add(resourceBrowser);
 });
 });*/

/*
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Browser.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/LayoutFactory.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Organizer.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/ResourceQueue.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/DatasetManager.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/CommandBar.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/viewStateManager.js')}"></script>

 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/ResourceFactory/ResourceFactory.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/ResourceFactory/ResourceImage.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/ResourceFactory/ResourceMex.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/ResourceFactory/ResourceModule.js')}"></script>

 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Misc/MessageBus.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Misc/GestureManager.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Misc/ComponentDataView.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Misc/Slider.js')}"></script>
 <script type="text/javascript" src="${tg.url('/js/ResourceBrowser/Misc/DataTip.js')}"></script>

 function includeJS(fileName) {
 var headID = document.getElementsByTagName('head')[0];
 var newScript = document.createElement('script');

 newScript.type = 'text/javascript';
 newScript.src = '/js/ResourceBrowser/' + fileName;
 headID.appendChild(newScript);
 }

 function includeCSS(fileName) {
 var headID = document.getElementsByTagName("head")[0];
 var cssNode = document.createElement('link');

 cssNode.type = 'text/css';
 cssNode.rel = 'stylesheet';
 cssNode.href = '/js/ResourceBrowser/' + fileName;
 cssNode.media = 'screen';
 headID.appendChild(cssNode);
 }

 includeJS("Browser.js");
 includeJS("LayoutFactory.js");
 includeJS("ResourceFactory.js");
 includeJS("Organizer.js");
 includeJS("ResourceQueue.js");
 includeJS("DatasetManager.js");

 // Misc utilities
 includeJS("Misc/MessageBus.js");
 includeJS("Misc/ComponentDataView.js");
 includeJS("Misc/DataTip.js");

 includeCSS("ResourceBrowser.css");
 */