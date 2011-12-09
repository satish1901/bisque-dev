
/// CellProfiler: CellProfiler enables biologists to quantitatively measure phenotypes from thousands of images automatically.

Ext.define('Bisque.Module.CellProfiler',
{
    extend: 'Bisque.Module.AbstractModule', //BQWebApp,

    plot : function()
    {
        var plotter_div = document.getElementById("webapp_results_plotter");
        plotter_div.style.display = '';
    
        var url = this.gobjectURL;
        var xmap = 'tag-value-number';
        var xreduce = 'histogram';
    
        var surface_area = document.createElementNS(xhtmlns, 'div');
        plotter_div.appendChild(surface_area);
        var xpath1 = '//tag[@name="Area"]';
        var opts =
        {
            title : 'Distribution of cell areas',
            height : 500,
            args :
            {
                numbins : 18
            }
        };
        this.plotter1 = new BQStatisticsVisualizer(surface_area, url, xpath1, xmap, xreduce, opts);
    },
    
    tagger : function()
    {
        var tagger = Ext.create('Bisque.ResourceTagger',
        {
            resource : this.mexURI,
            title : 'CellProfiler: Tags',
            height: 500,
            renderTo: 'webapp_results_tagger',
            viewMode : 'ViewerOnly',
        });
    },
    
    view : function()
    {
        document.getElementById("webapp_results_viewer").style.display = ''; 

        var parameters = {    
                             simpleview: '',
                             gobjects: this.gobjectURL
                         };

        var imgViewer = Ext.create('BQ.viewer.Image',
        {
            renderTo: 'webapp_results_viewer',
            resource: this.bq_resource,
            //flex: 1,
            height: 400,
            parameters: parameters,
        });
    },
    
    run : function()
    {
        if (!this.pipeline || this.pipeline=="None")
        {
            BQ.ui.attention('Please select a pipeline!');      
            return;
        }
        this.run_arguments = this.run_arguments || {};
        this.run_arguments['pipeline'] = this.pipeline;
        this.callParent(arguments);
    },
    
    selectPipeline : function()
    {
        this.pipeline = Ext.fly('comboPipeline').getValue();
    }
})
