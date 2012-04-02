% bq.Image
% A class wrapping a Bisque image along with it's pixels
%   Constructor:
%       Image(image_url, user, password)
%           image_url - optional: url of the image resource
%           user      - optional: user name if doc is a URL
%           password  - optional: user password if doc is a URL
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

classdef Image < handle
    
    properties
        image_url = [];
        user = [];        
        password = []; 
        info = [];
        pixels_url = [];
    end % properties
    
    methods
        
        function [self] = Image(image_url, user, password)
            if exist('image_url', 'var'), self.image_url = image_url; end
            if exist('user', 'var'), self.user = user; end
            if exist('password', 'var'), self.password = password; end 
            
            if exist('image_url', 'var'), 
                self.init(); 
            end
        end % constructor

        function init(self)
            if exist('user', 'var') && exist('password', 'var'),
                self.info = bq.iminfo(self.image_url, self.user, self.password);
            else
                self.info = bq.iminfo(self.image_url);                
            end
            self.pixels_url = bq.Url(self.info.pixles_url);            
        end % init   
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Pixels
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        function imo = command(self, command, params)
            self.pixels_url.pushQuery(command, params);
            imo = self;
        end % command              
        
        function im = fetch(self)
            im = bq.imreadND(self.pixels_url.toString(), self.user, self.password );
        end % fetch   
       
        function imo = slice(self, z, t)
            if exist('z', 'var') && exist('t', 'var'), 
                params = sprintf(',,%d,%d', z, t);
            elseif exist('z', 'var') && ~exist('t', 'var'), 
                params = sprintf(',,%d,', z);               
            elseif ~exist('z', 'var') && exist('t', 'var'), 
                params = sprintf(',,,%d', t);               
            end
            imo = self.command('slice', params);
        end % command           
        
        function imo = remap(self, c)
            params = sprintf('%d', c);
            imo = self.command('remap', params);
        end % command         
        
    end% methods
end% classdef
