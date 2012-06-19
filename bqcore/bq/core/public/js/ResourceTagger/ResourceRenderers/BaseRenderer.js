// Renderers are defined here for now
Bisque.ResourceTagger.LinkRenderer = function(value, metaData, record)
{
    return Ext.String.format('<a href={0} target="_blank">{1}</a>', value, value);
};

Bisque.ResourceTagger.ResourceRenderer = function(value, metaData, record)
{
    return Ext.String.format('<a href={0} target="_blank">{1}</a>', bq.url("/client_service/view?resource=" + value), value);
};

Bisque.ResourceTagger.VertexRenderer = function(value, metaData, record)
{
    var comboHtml = '<select>';
    var vertices = record.raw.vertices, vertex;

    for(var i = 0; i < vertices.length; i++)
    {
        vertex = vertices[i];
        comboHtml += '<option>';

        for(var j = 0; j < vertex.xmlfields.length; j++)
        if(vertex[vertex.xmlfields[j]] != null || vertex[vertex.xmlfields[j]] != undefined)
            comboHtml += vertex.xmlfields[j] + ':' + vertex[vertex.xmlfields[j]] + ', ';
        comboHtml += '</option>';
    }
    comboHtml += '</select>';

    return comboHtml
};

Bisque.ResourceTagger.RenderersAvailable =
{
    'file' : Bisque.ResourceTagger.LinkRenderer,
    'link' : Bisque.ResourceTagger.LinkRenderer,
    'statistics' : Bisque.ResourceTagger.LinkRenderer,
    'resource' : Bisque.ResourceTagger.ResourceRenderer,
    'image' : Bisque.ResourceTagger.ResourceRenderer,

    // Gobject renderers
    'point' : Bisque.ResourceTagger.VertexRenderer,
    'polyline' : Bisque.ResourceTagger.VertexRenderer,
    'polygon' : Bisque.ResourceTagger.VertexRenderer,
    'rectangle' : Bisque.ResourceTagger.VertexRenderer,
    'square' : Bisque.ResourceTagger.VertexRenderer,
    'circle' : Bisque.ResourceTagger.VertexRenderer,
    'ellipse' : Bisque.ResourceTagger.VertexRenderer
};

Bisque.ResourceTagger.BaseRenderer = function(value, metaData, record)
{
    var renderer = Bisque.ResourceTagger.RenderersAvailable[record.data.type];

    if(renderer)
        return renderer.apply(this, arguments);
    else
        return value;
};
