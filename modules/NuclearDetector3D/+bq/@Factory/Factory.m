% bq.Factory
% A factory class producing Nodes, Images etc...
%   
% i = bq.Factory.make('http://hjdfhjdhfjd');
%
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

classdef Factory
    
    properties (Constant)
        resources = containers.Map( ...
            {'node', 'image', 'file'}, ... % types
            {'bq.Node', 'bq.Image', 'bq.File'} ... % classes
        )
    end % constant properties
    
    methods (Static)
        
        % doc      - URL string or DOM document
        % element  - optional: DOM element
        % user     - optional: string
        % password - optional: string
        function [node] = make(doc, element, user, password)
            %exist('b', 'var') && ~isempty(eval('b'))            
            creds = exist('user', 'var') && ~isempty(user) && ...
                    exist('password', 'var') && ~isempty(password);
            
            % if doc is a URL then fetch it
            if ischar(doc),
                if creds,
                    doc = bq.get_xml( doc, user, password );
                else
                    doc = bq.get_xml( doc );    
                end                    
            end            
            
            if ~exist('element', 'var') || isempty(element),
                element = doc.getDocumentElement();
            end               
            
            % find class name based on the xml tag name
            tag = char(element.getTagName());
            if ~bq.Factory.resources.isKey(tag),              
                tag = 'node';
            end
            
            % get class and instantiate it
            classname = bq.Factory.resources(tag);
            try
                if creds,
                    node = feval(classname, doc, element, user, password );
                else
                    node = feval(classname, doc, element);
                end                  
            catch error
                warning(error.identifier, error.message);
                node = [];
            end            
        end % make

        
%         % type     - string of a Bisque object type
%         % user     - optional: string
%         % password - optional: string
%         function [node] = new(type, user, password)
%             name = 'node';
%             %bq.Factory.resources('node')
%             
%             try
%                 node = feval(ctorMT.Name,args{:});
%                 node = feval(bq.Factory.resources('node'), 'http://vidi.ece.ucsb.edu:9090/data_service/image/4932');
%             catch ME
%                 warning(ME.identifier, ME.message)
%                 obj = [];
%             end            
%             
%             
%         end % new             
%         
        
        
        
    end% static methods
end% classdef
