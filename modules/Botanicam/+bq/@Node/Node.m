% bq.Node
% A class wrapping a DOM XML node with Bisque functionality
%   Constructor:
%       Node(doc, element, user, password)
%           doc      - either an XML DOM document or a URL string
%           element  - optional: parent elemnt, only used if doc is DOM
%           user     - optional: user name if doc is a URL
%           password - optional: user password if doc is a URL
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

%classdef Node < handle
classdef Node < matlab.mixin.Copyable
    
    properties
        doc = [];
        element = [];  
        user = [];
        password = [];
    end % properties
    
    methods
        
        % doc      - URL string or DOM document
        % element  - optional: DOM element
        % user     - optional: string
        % password - optional: string
        function [self] = Node(doc, element, user, password)
            if exist('doc', 'var'), self.doc = doc; end            
            if exist('user', 'var'), self.user = user; end
            if exist('password', 'var'), self.password = password; end
            
            % if doc is a URL then fetch it
            if exist('doc', 'var') && ischar(doc),
                if exist('user', 'var') && exist('password', 'var'),
                    self.doc = bq.get_xml( doc, user, password );
                else
                    self.doc = bq.get_xml( doc );    
                end                    
            end
            
            if exist('element', 'var') && ~isempty(element),
                self.element = element;  
            elseif exist('self.doc', 'var') && ~isempty(self.doc),
                self.element = self.doc.getDocumentElement();
            end            
        end % constructor
        
        function save(self)
            url = self.getAttribute('uri');
            bq.post(url, self.doc, self.user, self.password);
        end % save          
        
        function remove(self)
            url = self.getAttribute('uri');
            bq.delete(url, self.user, self.password);
        end % remove              
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Access attributes
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        function value = getAttribute(self, name)
            value = char(self.element.getAttribute(name));
        end % getAttribute        
        
        function setAttribute(self, name, value)
            self.element.setAttribute(name, value);
        end % setAttribute  
        
        function v = hasAttribute(self, name)
            v = self.element.hasAttribute(name);
        end % getAttribute             
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Access values
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%        
        
        function value = getValue(self)
            type = '';
            value = [];
            if self.element.hasAttribute('type'),
                type = char(self.element.getAttribute('type'));  
            end
            if self.element.hasAttribute('value'),            
                value = char(self.element.getAttribute('value'));
            end
            if strcmpi(type, 'number') && ~isempty(value),
                value = str2num(value);
            end
        end % getValue         
        
        function value = setValue(self, value)
            self.element.setAttribute('value', value);
        end % setValue           
        
        function values = getValues(self, type)
            % read the single value
            if ~exist('type', 'var'),
                type = '';
                if self.element.hasAttribute('type'),
                    type = char(self.element.getAttribute('type'));  
                end                
            end
            values = {};   
            if self.element.hasAttribute('value'),
                values{1} = char(self.element.getAttribute('value'));
            end
            
            % find all <value> sub nodes            
            import javax.xml.xpath.*;
            factory = XPathFactory.newInstance;
            xpath = factory.newXPath;    
            xnodes = xpath.evaluate('value', self.element, XPathConstants.NODESET);
            if ~isempty(xnodes) && xnodes.getLength()>0,
                for i=1:xnodes.getLength(),
                    n = xnodes.item(i-1);
                    values{i} = char(n.getTextContent());
                end            
            end            
            
            % convert type if needed    
            if strcmpi(type, 'number') && ~isempty(values),
                for i=1:length(values),
                    values{i} = str2num(values{i});
                end
            end
        end % getValues            
        
        function value = setValues(self)
            % not yet implemented
            %value = char(self.element.getAttribute(name));
        end % setValues                  
        
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
            %node = bq.Node(self.doc, xn);
            if ~isempty(xn),
                node = bq.Factory.fetch(self.doc, xn);
            else
                node = [];
            end
        end             
        
        function v = findValue(self, expression)
            v = [];
            t = self.findNode(expression);
            if ~isempty(t),
                v = t.getValue();            
            end
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
                %nodes{i} = bq.Node(self.doc, xnodes.item(i-1));
                nodes{i} = bq.Factory.fetch(self.doc, xnodes.item(i-1));
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
            %resource = bq.Node(self.doc, r);
            resource = bq.Factory.fetch(self.doc, r);
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
            %gob = bq.Node(self.doc, g);
            gob = bq.Factory.fetch(self.doc, g);
        end % addGobject 

       
    end% methods
end% classdef
