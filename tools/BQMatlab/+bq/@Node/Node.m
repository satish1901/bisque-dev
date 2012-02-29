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

        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Access elements
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        function value = getAttribute(self, name)
            value = char(self.element.getAttribute(name));
        end % getAttribute        
        
        function setAttribute(self, name, value)
            self.element.setAttribute(name, value);
        end % setAttribute              
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Search for elements
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        function node = tag(self, name)
            expression = ['tag[@name="' name '"]'];
            node = self.findNode(expression);
        end           

        function node = gobject(self, name)
            expression = ['gobject[@name="' name '"]'];
            node = self.findNode(expression);
        end           
        
        % Returns bq.Node found with xpath expression
        %
        % INPUT:
        %    expression - an xpath expression 
        %
        % OUTPUT:
        %    s - a struct containing tag values by their names
        %        for tags example above will produce:
        %            s.width, s.descr, s.pix_res
        %        
        function node = findNode(self, expression)
            import javax.xml.xpath.*;
            factory = XPathFactory.newInstance;
            xpath = factory.newXPath;    
            %xn = xpath.evaluate(expression, self.doc, XPathConstants.NODE);
            xn = xpath.evaluate(expression, self.element, XPathConstants.NODE);
            node = bq.Node(self.doc, xn);
        end             
        
        % Returns a vector of bq.Node found with xpath expression
        %
        % INPUT:
        %    expression - an xpath expression 
        %
        % OUTPUT:
        %    s - a struct containing tag values by their names
        %        for tags example above will produce:
        %            s.width, s.descr, s.pix_res
        %        
        function nodes = findNodes(self, expression)
            import javax.xml.xpath.*;
            factory = XPathFactory.newInstance;
            xpath = factory.newXPath;    
            %xnodes = xpath.evaluate(expression, self.doc, XPathConstants.NODESET);
            xnodes = xpath.evaluate(expression, self.element, XPathConstants.NODESET);
            if isempty(xnodes) || xnodes.getLength()<1,
                nodes = cell(0,1);
                return;
            end            
            nodes = cell(xnodes.getLength(),1);
            for i=1:xnodes.getLength(),
                nodes{i} = bq.Node(self.doc, xnodes.item(i-1));
            end
        end         
        
        % Returns tags found with xpath expression in proper formats
        %
        % INPUT:
        %    expression - an xpath expression 
        %
        % OUTPUT:
        %    s - a struct containing values by their names
        %        for tags example above will produce:
        %            s.width, s.descr, s.pix_res
        %        
        function s = getNameValueMap(self, expression)
            import javax.xml.xpath.*;
            factory = XPathFactory.newInstance;
            xpath = factory.newXPath;    
            s = containers.Map();
            %tl = xpath.evaluate(expression, self.doc, XPathConstants.NODESET);
            tl = xpath.evaluate(expression, self.element, XPathConstants.NODESET);        
            for i=0:tl.getLength()-1,
                t = tl.item(i);
                name  = char(t.getAttribute('name'));
                value = char(t.getAttribute('value'));  
                type  = char(t.getAttribute('type'));  
                
                if ~isempty(type) && strcmp(type, 'double'), 
                    value = str2double(value); 
                elseif ~isempty(type) && strcmp(type, 'int'), 
                    value = str2num(value); 
                end
                s(name) = value;
            end
        end           
        
        % Finds tags of interest and returns their values in proper formats
        % the difference from the getTagValues is in providing default  
        % tag types and tag values
        %
        % INPUT:
        %    tags     - an Nx2 or Nx3 cell with elemnets: 'name', 'type', 'value'
        %               possible types are: 'double', 'int' and 'str'
        %               tags = { 'width', 'int', 10; 'descr', 'str', []; 'pix_res', 'double', '1.5'; }
        %    template - an xpath expression template where %s should indicate
        %               template = '//image/tag[@name=''%s'']';
        %
        % OUTPUT:
        %    s   - a struct containing tag values by their names
        %          for tags example above will produce:
        %            s.width, s.descr, s.pix_res
        %
        function s = findNameValueMap(self, tags, template)
            import javax.xml.xpath.*;
            factory = XPathFactory.newInstance;
            xpath = factory.newXPath;    

            s = containers.Map();
            for i=1:size(tags,1),
                name = tags{i,1};
                type = tags{i,2};       
                expression = sprintf(template, name);
                %t = xpath.evaluate(expression, self.doc, XPathConstants.NODE);    
                t = xpath.evaluate(expression, self.element, XPathConstants.NODE);
                if ~isempty(t) && t.hasAttribute('value'),
                    value = t.getAttribute('value');
                    if ~isempty(value) && strcmp(type, 'double'), 
                        s(name) = str2double(value); 
                    elseif ~isempty(value) && strcmp(type, 'int'), 
                        s(name) = str2num(value); 
                    elseif ~isempty(value), 
                        s(name) = char(value); 
                    end                   
                elseif size(tags,2)>2 && ~isempty(tags{i,3}),
                    s(name) = tags{i,3};                    
                end                
            end
        end               
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Add elements
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        function resource = add(self, resource_type, name, value, type)
            r = self.doc.createElement(resource_type);
            r.setAttribute('name', name);

            if nargin>3 && ~isempty(value),
                if isa(value, 'numeric'),
                    value = num2str(value);
                end        
                r.setAttribute('value', value);
            end

            if nargin>4 && ~isempty(type),
                r.setAttribute('type', type);
            end

            self.element.appendChild(r); 
            resource = bq.Node(self.doc, r);
        end % add
        
        function tag = addTag(self, name, value, type)
            if nargin==2,
                tag = self.add('tag', name);
            elseif nargin==3,
                tag = self.add('tag', name, value);                
            elseif nargin>3,                
                tag = self.add('tag', name, value, type);                
            end  
        end % addTag
        
        function gob = addGobject(self, type, name, vertices)
            if isa(name, 'numeric'),
                name = num2str(name);
            end
            g = self.doc.createElement('gobject');
            g.setAttribute('type', type);
            g.setAttribute('name', name);

            if nargin>3 && ~isempty(vertices),
                for i=1:size(vertices, 1),
                    v = self.doc.createElement('vertex');

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
