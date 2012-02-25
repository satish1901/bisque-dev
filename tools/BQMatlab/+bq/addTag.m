%  bq.addTag(doc, node, name, value, type)
%  addTag - appends a newly created tag node to the node or document
%
%   INPUT:
%     doc   - XML DOM document
%     node  - Optional: XML DOM element, if [] root element will be used
%     name  - string with tag name
%     value - string with tag value
%     type  - string with tag type
%
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       1 - 2011-03-29 First implementation 
%

function [t] = addTag(doc, node, name, value, type)
    %if isa(nd, 'org.apache.xerces.dom.DeferredDocumentImpl'),
    if isempty(node),
        node = doc.getDocumentElement();
    end
    t = doc.createElement('tag');
    t.setAttribute('name', name);
    if ~isempty(value),
        t.setAttribute('value', value);
    end
    if ~isempty(type),
        t.setAttribute('type', type);
    end
    node.appendChild(t); 
end 
