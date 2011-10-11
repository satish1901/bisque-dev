Ext.define('Bisque.Misc.GestureManager',
{
	constructor : function()
	{
		this.loading=true;
		this.listenerQueue=[];
		
		var docHead = Ext.getHead();//document.getElementsByTagName('head')[0];
		var script = Ext.core.DomHelper.createDom(
		{
			tag: 'script',
			type: 'text/javascript',
			src: bq.url('/js/sencha-touch.js'),
		});
		
		script.onload=Ext.bind(function()
		{
			ExtTch.setup(
			{
				onReady: Ext.bind(this.addListenerFromQueue, this),
			});
		}, this);
		
		docHead.appendChild(script);
	},
	
	addListener : function(listenerObj)
	{
		if (Ext.isArray(listenerObj))
			Ext.Array.forEach(listenerObj, this.addListener, this);
		
		if (this.loading)
			this.listenerQueue.push(listenerObj);
		else
		{
			if (Ext.getDom(listenerObj.dom))
				ExtTch.gesture.Manager.addEventListener(listenerObj.dom, listenerObj.eventName, listenerObj.listener, listenerObj.options);
		}
	},
	
	addListenerFromQueue : function()
	{
		this.loading=false;
		
		while(this.listenerQueue.length)
			this.addListener(this.listenerQueue.shift());
	}
});
