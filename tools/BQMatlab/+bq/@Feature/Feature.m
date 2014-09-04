% bq.Image
% A class wrapping a Bisque image along with it's pixels
%   Constructor:
%       Feature(resource, name, user, password)
%         resource      - URL string or DOM document
%         name     - Feature name
%         user     - optional: string
%         password - optional: string
%   
%   AUTHOR:
%       Chris Wheat
%
%   VERSION:
%       0.1 -  2014-09-03 First implementation
%
classdef Feature < handle
    
    properties 
        info = [];
        resource_list = [];
        user = '';
        password = '';
        name = '';
        root = '';
    end % properties
    
    methods

        % doc      - URL string or DOM document
        % element  - optional: DOM element
        % user     - optional: string
        % password - optional: string
        function [self] = Feature(name, resource, user, password, root)
            self.resource_list = [];
            if exist('resource', 'var'), self.resource_list = [self.resource_list,resource]; end
            if exist('name', 'var'), self.name = name; end
            if exist('user', 'var'), self.user = user; end
            if exist('root', 'var'), self.root = root; end
            if exist('password', 'var'), self.password = password; end
            %self = self@bq.File(supargs{:});
            %self.init();
        end % constructor

%         function init(self)
%             if isempty(self.doc) || ~self.hasAttribute('uri'),
%                 return;
%             end
%             
%             uri = self.getAttribute('uri');
%             if ~isempty(self.user) && ~isempty(self.password),
%                 self.info = bq.iminfo(uri, self.user, self.password);
%             else
%                 self.info = bq.iminfo(uri);                
%             end
%             self.pixels_url = bq.Url(self.info.pixles_url);            
%         end % init
        
        function self = addResource(self, resource)
            if exist('resource', 'var'), self.resource_list = [self.resource_list,resource]; end
        end
        
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Features
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        
        % filename - optional: if given and not empty represents a filename to save the HDF5 file into
        %                      if given but is empty instructs to use resource's name
        % im - the actual image matrix data if no filename was provided or 
        %      the filename where the image was stored        
        function [output, info] = fetch(self, filename)
            body = bq.Factory.new('resource');
            for i = 1:length(self.resource_list)
                f = body.doc.createElement('feature');
                body.element.appendChild(f); 
                resource_names = fieldnames(self.resource_list(i));
                for j = 1:length(resource_names)
                    f.setAttribute(resource_names(j),self.resource_list(i).(char(resource_names(j))))
                end
            end

            source_url = [self.root '/features/' self.name '/hdf'];
            
            supargs{1} = 'POST';
            supargs{2} = source_url;  
            
            if exist('filename', 'var'), supargs{3} = filename; end %save resulting hdf5 file
 
            
            supargs{4} = body;
            if ~isempty(self.user) && ~isempty(self.password)
                supargs{5} = self.user; 
                supargs{6} = self.password;                 
            end
            if exist('filename', 'var')
                [output, info] = bq.connect(supargs{:});
            else
                [output, info] = bq.connect(supargs{:});
                %write everything to a tempfile to read
                ftemp = tempname;
                temp = fopen(ftemp,'w');
                fwrite(temp, output);
                output = h5read(ftemp,'/values');
                fclose(temp); %close temp file
                delete(ftemp); %remove temp
            end
        end % fetch  
    end
    
end% classdef
