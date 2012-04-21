% bq.Image
% A class wrapping a Bisque image along with it's pixels
%   Constructor:
%       Image(doc, element, user, password)
%         doc      - URL string or DOM document
%         element  - optional: DOM element
%         user     - optional: string
%         password - optional: string
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

classdef Image < bq.File
    
    properties
        info = [];
        pixels_url = [];
    end % properties
    
    methods

        % doc      - URL string or DOM document
        % element  - optional: DOM element
        % user     - optional: string
        % password - optional: string
        function [self] = Image(doc, element, user, password)
            supargs = {};
            if exist('doc', 'var'), supargs{1} = doc; end
            if exist('element', 'var'), supargs{2} = element; end            
            if exist('user', 'var'), supargs{3} = user; end 
            if exist('password', 'var'), supargs{4} = password; end             
            self = self@bq.File(supargs{:});            
            self.init(); 
        end % constructor

        function init(self)
            if isempty(self.doc) || ~self.hasAttribute('uri'),
                return;
            end
            
            uri = self.getAttribute('uri');   
            if ~isempty(self.user) && ~isempty(self.password),
                self.info = bq.iminfo(uri, self.user, self.password);
            else
                self.info = bq.iminfo(uri);                
            end
            self.pixels_url = bq.Url(self.info.pixles_url);            
        end % init   
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Pixels
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        
        % filename - optional: if given and not empty represents a filename to save the image into
        %                      if given but is empty instructs to use resource's name
        % im - the actual image matrix data if no filename was provided or 
        %      the filename where the image was stored        
        function im = fetch(self, filename)
            if exist('filename', 'var'),
                im = self.fetch@bq.File(filename); 
            else
                im = bq.imreadND(self.pixels_url.toString(), self.user, self.password );
            end
        end % fetch  

        function imo = command(self, command, params)
            imo = copy(self);
            imo.pixels_url.pushQuery(command, params);
        end % command          
        
        function imo = slice(self, z, t)
            if exist('z', 'var') && exist('t', 'var') && ~isempty(z) && ~isempty(t), 
                params = sprintf(',,%d,%d', z, t);
            elseif exist('z', 'var') && (~exist('t', 'var') || isempty(t)), 
                params = sprintf(',,%d,', z);               
            elseif (~exist('z', 'var') || isempty(z)) && exist('t', 'var'), 
                params = sprintf(',,,%d', t);               
            end
            imo = self.command('slice', params);
        end % command           
        
        % m = im.remap(1).fetch();
        % m = im.remap([3,2,1]).fetch();
        function imo = remap(self, c)
            params = '';
            for i=1:length(c),
                params = [params sprintf('%d', c(i))];
            end
            imo = self.command('remap', params);
        end % command         
        
    end% methods
    
    methods(Access = protected)
        % Override copyElement method:
        function cpObj = copyElement(obj)
            % Make a shallow copy of all four properties
            cpObj = copyElement@matlab.mixin.Copyable(obj);
            % Make a deep copy of the DeepCp object
            cpObj.pixels_url = copy(obj.pixels_url);
        end
    end    
    
end% classdef
