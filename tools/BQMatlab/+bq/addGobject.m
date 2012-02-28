% [g] = bq.addGobject(doc, node, type, name, vertices)
%  addGobject - appends a newly created gobject to the node or document
%
%   INPUT:
%     doc   - XML DOM document
%     node  - Optional: parent XML DOM element, if [] root element will be used
%     type  - string with tag type
%     name  - string with tag name
%     vertices - string with tag value
%
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       1: 2011-03-29 First implementation 
%

function [g] = addGobject(doc, node, type, name, vertices)
    if isempty(node),
        node = doc.getDocumentElement();
    end
    if isa(name, 'numeric'),
        name = num2str(name);
    end
    g = doc.createElement('gobject');
    g.setAttribute('type', type);
    g.setAttribute('name', name);
    
    if nargin>4 && ~isempty(vertices),
        for i=1:size(vertices, 1),
            v = doc.createElement('vertex');

            if ~isempty(vertices(i,:)) && vertices(i,1)>=0,
                v.setAttribute('x', num2str(vertices(i,1)));
            end
            if length(vertices(i,:))>1 && vertices(i,2)>=0,
                v.setAttribute('y', num2str(vertices(i,2)));
            end
            if length(vertices(i,:))>2 && vertices(i,3)>=0,
                v.setAttribute('z', num2str(vertices(i,3)));
            end
            if length(vertices(i,:))>3 && vertices(i,4)>=0,
                v.setAttribute('t', num2str(vertices(i,4)));
            end
            if length(vertices(i,:))>4 && vertices(i,5)>=0,
                v.setAttribute('c', num2str(vertices(i,5)));
            end            
            if size(vertices, 1)>1,
                v.setAttribute('index', num2str(i-1));
            end       
            
            g.appendChild(v); 
        end
    end
    
    node.appendChild(g); 
end 
