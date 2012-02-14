// config: query

Ext.define('BQ.gmap.BigMap', {
    extend: 'Ext.panel.Panel',
    //extend: 'Ext.window.Window',    
    requires: ['BQ.gmap.BIGMapPanel', '*'],

    layout: {
        type: 'hbox',
        pack: 'start',
        align: 'stretch'
    },

    initComponent : function() {
        if (!this.items) this.items = [];

        var but = Ext.create('Ext.Button', {
            text: 'Search',
            border:true,
            id: 'submission',
            name: 'submission',
        });
    
        
        //    /data_service/images?tag_values="species"&wpublic=true
        Ext.regModel('Queries', {
            fields: [
                {type: 'string', name: 'name'},
                {type: 'string', name: 'value'},
            ]
        });
        
        var store = Ext.create('Ext.data.Store', {
            model: 'Queries',
            //data: states
        });
        
        var queryCombo = Ext.create('Ext.form.field.ComboBox', {
            fieldLabel: 'Query',
            displayField: 'value',
            width: 300,
            store: store,
            queryMode: 'local',
            typeAhead: true,
            id: 'input_query',
        });        
    
        this.tbar = [queryCombo, but];

        
        var map = Ext.create('BQ.gmap.BIGMapPanel', {
            region : 'center',
            flex: 1, 
            combo: queryCombo,
            imageQuery: this.imageQuery,
        });

        this.items.push(map);

        this.items.push({ xtype:'tbtext',
                          collapsible: true, split: true,
                          region: 'east',
                          border : false,
                          width: 300,
                          html: '<select id="chooser" multiple style="width: 100%; height: 100%;"></select>',
                          name: 'chooser'
                          //flex: 1,
        } );
        
        this.callParent();
        
        but.on( 'click', function(){ map.makeQuery('*"'+queryCombo.getValue()+'"*'); } );             
            
        /*
        var selection = Ext.getDom("chooser");
        var me = this;
        selection.onchange = function() { //run some code when "onchange" event fires
            var chosenoption=this.options[this.selectedIndex] //this refers to "selection"
            me.onMarkerClick2 (chosenoption.marker);
        }
        */
            
    },

});
