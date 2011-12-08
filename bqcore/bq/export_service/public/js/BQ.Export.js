Ext.define('BQ.Export.Panel', {
    extend : 'Ext.panel.Panel',
    
    constructor : function()
    {
        Ext.apply(this, {
            heading : 'Download Images',
            layout : 'fit',
        });
        
        this.callParent(arguments);
    },
    
    initComponent : function()
    {
        this.dockedItems = [
        {
            xtype : 'toolbar',
            dock : 'top',
            items : [
            {
                xtype: 'tbtext',
                padding: 10,
                html: '<h2>'+this.heading+':</h2>'
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    text: 'Add Images',
                    scale: 'large',
                    width: 140,
                    padding : 3,
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-select-images',
                    handler: this.selectImage,
                    scope: this
                }
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    text: 'Add Dataset',
                    scale: 'large',
                    padding : 3,
                    width: 140,
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-select-dataset',
                    handler: this.selectDataset,
                    scope: this
                }
            }]
        },
        {
            xtype : 'toolbar',
            dock : 'bottom',
            items : [
            {
                xtype : 'tbspacer',
                width : 10,
                padding : 10
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    xtype: 'splitbutton',
                    text: 'Download',
                    scale: 'large',
                    padding : 3,
                    width: 160,
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-download',
                    arrowAlign: 'right',
                    menuAlign: 'bl-tl?',
                    compressionType: 'tar',

                    handler: this.download,
                    scope: this,

                    menu:
                    {
                        items: [{
                            compressionType: 'tar',
                            text: 'as TARball',
                            checked: true,
                            group: 'compression_type',
                            groupCls: Ext.baseCSSClass + 'menu-item-checked',
                            handler: this.download,
                            scope: this,
                        },{
                            compressionType: 'gzip',
                            text: 'as GZip archive',
                            checked: false,
                            group: 'compression_type',
                            groupCls: Ext.baseCSSClass + 'menu-item-checked',
                            handler: this.download,
                            scope: this,
                        },{
                            compressionType: 'bz2',
                            text: 'as BZip2 archive',
                            checked: false,
                            group: 'compression_type',
                            groupCls: Ext.baseCSSClass + 'menu-item-checked',
                            handler: this.download,
                            scope: this,
                        },{
                            compressionType: 'zip',
                            text: 'as (PK)Zip archive',
                            checked: false,
                            group: 'compression_type',
                            groupCls: Ext.baseCSSClass + 'menu-item-checked',
                            handler: this.download,
                            scope: this,
                        }]
                    }
                }
            },
            {
                xtype: 'buttongroup',
                margin: 5,
                items: 
                {
                    text: 'Export to Google Docs',
                    scale: 'large',
                    padding : 3,
                    width: 160,
                    textAlign: 'left',
                    iconCls: 'add',
                    iconAlign: 'left',
                    iconCls: 'icon-gdocs'
                }
            }]
        }]
        
        this.callParent(arguments);
        this.add(this.getResourceGrid())
    },
    
    download : function(btn)
    {
        if (!this.resourceStore.count())
        {
            BQ.ui.message('Download failed', 'Nothing to download! Please add files or datasets first...');
            return;
        }
       
        function findAllbyType(type)
        {
            var index=0, list=[];
            
            while((index = this.resourceStore.find('type', type, index))!=-1)
            {
                list.push(this.resourceStore.getAt(index).get('uri'));
                index++;
            }
            
            return list;
        }
        
        Ext.create('Ext.form.Panel',
        {
            url : '/export/initStream',
            defaultType: 'hiddenfield',
            method : 'GET',
            standardSubmit: true,
            items : [
            {
                name : 'compressionType',
                value : btn.compressionType 
            },
            {
                name : 'files',
                value : findAllbyType.call(this, 'image')
            },
            {
                name : 'datasets',
                value : findAllbyType.call(this, 'dataset')
            }]
        }).submit();
    },
    
    exportResponse : function(response)
    {
        //debugger;
    },

    selectImage : function()
    {
        var rbDialog = Ext.create('Bisque.ResourceBrowser.Dialog', {
            'height' : '85%',
            'width' :  '85%',
            wpublic: 'true',
            listeners : 
            {
                'Select' : this.addToStore,
                scope: this
            }
        });
    },
        
    selectDataset : function()
    {
        var rbDialog = Ext.create('Bisque.DatasetBrowser.Dialog', {
            'height': '85%',
            'width':  '85%',
            wpublic: 'true',
            listeners : 
            {
                'DatasetSelect' : this.addToStore,
                scope: this
            }
        });
    },

    addToStore : function(rb, resource)
    {
        if (resource instanceof Array)
        {
            for (var i=0;i<resource.length;i++)
                this.addToStore(rb, resource[i]);
            return;
        }

        var record = [];

        if (resource.resource_type=='image')
        {
            record.push(resource.src);
            resource.name = resource.name || 'Unknown';
            record.push(resource.name);
            record.push(resource.resource_type, resource.ts, resource.perm, resource.uri, 1);
        }
        else if (resource.resource_type=='dataset')
        {
            record.push(bq.url('../export_service/public/images/folder.png'), resource.name, resource.resource_type, resource.ts, resource.perm || '', resource.uri, 0);
        }
        
        this.resourceStore.loadData([record], true);
    },
    
    getResourceGrid : function()
    {
        this.resourceGrid = Ext.create('Ext.grid.Panel', {
            store : this.getResourceStore(),
            border : 0,
            listeners : 
            {
                scope: this,
                'itemdblclick' : function(view, record, item, index)
                {
                    // delegate resource viewing to ResourceView Dispatcher
                    var newTab = window.open('', "_blank");
                    newTab.location = bq.url('/client_service/view?resource=' + record.get('uri'));
                }
            },
            
            columns : 
            {
                items : [
                {
                    width: 120,
                    dataIndex: 'icon',
                    align:'center',
                    renderer : function(value)
                    {
                        return '<img src='+value+'?thumbnail=40,40&format=jpeg />'
                    } 
                },
                {
                    text: 'Name',
                    flex: 0.6,
                    maxWidth: 350,
                    sortable: true,
                    dataIndex: 'name' 
                },
                {
                    text: 'Type',
                    flex: 0.4,
                    maxWidth: 200,
                    align: 'center',
                    sortable: true,
                    dataIndex: 'type' 
                },
                {
                    text: 'Date created',
                    flex: 0.5,
                    maxWidth: 250,
                    align: 'center',
                    sortable: true,
                    dataIndex: 'ts',
                },
                {
                    text: 'Published',
                    flex: 0.4,
                    maxWidth: 200,
                    align: 'center',
                    sortable: true,
                    dataIndex: 'public',
                },
                {
                    xtype: 'actioncolumn',
                    maxWidth: 80,
                    align: 'center',
                    items: [
                    {
                        icon : bq.url('../export_service/public/images/delete.png'),
                        align : 'center',
                        tooltip: 'Remove',
                        handler: function(grid, rowIndex, colIndex)
                        {
                            var name = grid.store.getAt(rowIndex).get('name');
                            grid.store.removeAt(rowIndex);
                            BQ.ui.message('Export - Remove', 'File ' + name + ' removed!');
                        }
                    }]
                }],
                defaults : 
                {
                    tdCls: 'align'
                }
            }
        });
        
        return this.resourceGrid;
    },
    
    getResourceStore : function()
    {
        this.resourceStore = Ext.create('Ext.data.ArrayStore', {
            fields: 
            [
                'icon',
                'name',
                {name: 'type', convert: function(value){return Ext.String.capitalize(value)}},  
                {name: 'ts', convert: function(value){return Ext.Date.format(Ext.Date.parse(value, 'Y-m-d H:i:s.u'), "F j, Y g:i:s a")}},
                {name: 'public', convert: function(value){return (value==0)?'Yes':'No'}},
                'uri',
                'viewPriority'
            ],
            sorters: 
            [{
                property : 'viewPriority',
                direction : 'ASC'
                
            }]
        });
        
        return this.resourceStore;
    }
})
