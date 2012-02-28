% bq.Node
% A class wrapping a DOM XML node with Bisque functionality
%
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

classdef Node < handle
    
    properties
        doc = [];
        element = [];        
    end % properties
    
    methods
        
        function [self] = Node(doc, element)
            self.doc = doc;
            if nargin>1 && ~isempty(element),
                self.element = element;  
            else
                self.element = self.doc.getDocumentElement();
            end            
        end % constructor
        
        function tag = addTag(name, value, type)
            t = self.doc.createElement('tag');
            t.setAttribute('name', name);

            if nargin>1 && ~isempty(value),
                if isa(value, 'numeric'),
                    value = num2str(value);
                end        
                t.setAttribute('value', value);
            end

            if nargin>2 && ~isempty(type),
                t.setAttribute('type', type);
            end

            self.element.appendChild(t); 
            tag = bq.Node(self.doc, t);
        end % addTag
        
        function gob = addGobject(type, name, vertices)
            if isa(name, 'numeric'),
                name = num2str(name);
            end
            g = self.doc.createElement('gobject');
            g.setAttribute('type', type);
            g.setAttribute('name', name);

            if nargin>2 && ~isempty(vertices),
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

            self.element.appendChild(g); 
            gob = bq.Node(self.doc, g);
        end % addGobject 

    end% methods
end% classdef
