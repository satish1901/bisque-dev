/* Abstract Dataset resource definition (inherits from Resource abstract class) */
Ext.define('Bisque.Resource.Dataset',
{
    extend:'Bisque.Resource',
    
    initComponent : function() {
        this.addCls('dataset');	
        this.callParent();			
	},    

    afterRenderFn : function()
    {
        this.setData('renderedRef', this);

        if (this.getData('fetched')==1)
            this.updateContainer();
    },
});

Ext.define('Bisque.Resource.Dataset.Compact',
{
    extend : 'Bisque.Resource.Dataset',
    
   	constructor : function()
	{
        Ext.apply(this,
        {
            layout:
            {
            	type:'vbox',
            	align:'stretch'	
            }
        });
		this.callParent(arguments);
        this.addCls('compact');				
	},
    
    prefetch : function()
    {
        if (!this.getData('fetched'))
        {
            this.setData('fetched', -1);    // -1 = Loading
            this.resource.getMembers(Ext.bind(this.fetchMembers, this));
		}
    },
    
    fetchMembers : function(memberTag)
    {
        BQFactory.request(
        {
            uri:memberTag.uri + '/value',
            cb:Ext.bind(this.loadResource, this),
            errorcb:Ext.emptyFn
        });
    },
    
	loadResource : function(resource)
    {
        var imgs = '<div style = "margin:4px;width:152px;height:152px">'
        var thumbnail, margin;

        for (var i=0;i<resource.children.length && i<4; i++)
        {
                switch (resource.children[i].resource_type)
                {
                    case 'image':
                    {
                        thumbnail = resource.children[i].src+'?thumbnail=75,75&format=jpeg';
                        break;
                    }
                    case 'dataset':
                    {
                        thumbnail = bq.url('../export_service/public/images/folder-large.png');
                        break; 
                    }
                    default :
                        thumbnail = bq.url('../export_service/public/images/file-large.png') 
                }

            margin = (i==1?'margin:0px 0px 0px 2px;':(i==2?'margin:2px 2px 0px 0px;':'')); 
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src='+ thumbnail + ' />'
        }
        
        imgs += '</div>';

        this.setData('fetched', 1); // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
			renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var date = new Date();
        date.setISO(this.resource.ts);
        
        this.update('<div class="labelOnImage" style="width:160px;">'+this.resource.name
        +'<br><span class="smallLabelOnImage">'
        + Ext.Date.format(date, "m/d/Y")+'</span></div>'+this.getData('previewDiv'));       
        this.setLoading(false);
    },
});

Ext.define('Bisque.Resource.Dataset.Card',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
    loadResource : function(resource)
    {
        var imgs = '<div style = "margin:0px 0px 0px 12px;width:258px;height:310px">'
        var thumbnail, margin;

        for (var i=0;i<resource.children.length && i<12; i++)
        {
                switch (resource.children[i].resource_type)
                {
                    case 'image':
                    {
                        thumbnail = resource.children[i].src+'?thumbnail=75,75&format=jpeg';
                        break;
                    }
                    case 'dataset':
                    {
                        thumbnail = bq.url('../export_service/public/images/folder-large.png');
                        break; 
                    }
                    default :
                        thumbnail = bq.url('../export_service/public/images/file-large.png') 
                }

            margin = 'margin:0px 3px 2px 0px;'; 
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src='+ thumbnail + ' />'
        }
        
        imgs += '</div>';

        this.setData('fetched', 1); // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
            renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var date = new Date();
        date.setISO(this.resource.ts);
        
        this.update('<div class="labelOnImage" style="width:260px;">'+this.resource.name
        +'<br><span class="smallLabelOnImage">'
        + Ext.Date.format(date, "m/d/Y")+'</span></div>'+this.getData('previewDiv'));       
        this.setLoading(false);
    },
});


Ext.define('Bisque.Resource.Dataset.Full',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
    constructor : function()
    {
        this.callParent(arguments);

        Ext.apply(this,
        {
            layout: 'fit',
        });
    },
    
    loadResource : function(resource)
    {
        var imgs = '<div style = "margin:0px 0px 0px 12px;width:99%;">'
        var thumbnail, margin;

        for (var i=0;i<resource.children.length; i++)
        {
                switch (resource.children[i].resource_type)
                {
                    case 'image':
                    {
                        thumbnail = resource.children[i].src+'?thumbnail=75,75&format=jpeg';
                        break;
                    }
                    case 'dataset':
                    {
                        thumbnail = bq.url('../export_service/public/images/folder-large.png');
                        break; 
                    }
                    default :
                        thumbnail = bq.url('../export_service/public/images/file-large.png') 
                }

            margin = 'margin:0px 3px 2px 0px;'; 
            imgs += '<img style="display:inline-block;height:75px;width:75px;' + margin + '" src='+ thumbnail + ' />'
        }
        
        imgs += '</div>';

        this.setData('fetched', 1); // 1 = Loaded
        this.setData('previewDiv', imgs);

        var renderedRef=this.getData('renderedRef')
        if (renderedRef)
            renderedRef.updateContainer();
    },
    
    updateContainer : function()
    {
        var date = new Date();
        date.setISO(this.resource.ts);

        var imgDiv = new Ext.get(document.createElement('div'));
        imgDiv.update('<div class="labelOnImage" style="width:99%;">'+this.resource.name
        +'<br><span class="smallLabelOnImage">'
        + Ext.Date.format(date, "m/d/Y")+'</span></div>'+this.getData('previewDiv'));
        
        this.add(Ext.create('Ext.panel.Panel', {
            border  :   0,
            autoScroll : true,
            contentEl : imgDiv,
        }));
        

        this.setLoading(false);
        
    },
});


Ext.define('Bisque.Resource.Dataset.List',
{
    extend : 'Bisque.Resource.Dataset.Compact',
    
   	constructor : function()
	{
		this.callParent(arguments);
		
        Ext.apply(this,
        {
            layout:
            {
            	type:'hbox',
            	align:'middle'	
            }
        });
        this.addCls('list');        
	},
	
    updateContainer : function()
    {
		var datasetName=new Ext.form.Label({
			text:' '+this.resource.name+' ',
			padding:'0 8 0 8',
			cls:'lblModuleName',
		})
		
		var datasetOwner=new Ext.form.Label({
			text:this.getData('owner'),
			padding:'0 0 0 4',
			cls:'lblModuleOwner',
		})

		var date = new Date();
		date.setISO(this.resource.ts);
		
		var datasetDate=new Ext.form.Label({
			text:Ext.Date.format(date, "F j, Y g:i:s a"),
			cls: 'lblModuleDate',	
			flex: 1,		
			//padding:'0 0 0 8',
            //style:'color:#444;font-size:11px;font-family: tahoma, arial, verdana, sans-serif !important;'
		})

		this.add([datasetName, datasetOwner, datasetDate]);
        this.setLoading(false);
    },
});

// Page view for a dataset
Ext.define('Bisque.Resource.Dataset.Page',
{
    extend : 'Bisque.Resource',
    
    constructor : function()
    {
        Ext.apply(this, {
            layout:'fit',
        });
        
        this.callParent(arguments);
    },
    
    updateContainer : function()
    {
        this.setLoading(false);
    
        var renderer = Ext.create('BQ.renderers.dataset', {
            resource: this.resource,
        });
        
        this.add(renderer);
    }
});
