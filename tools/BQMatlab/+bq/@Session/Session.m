% bq.Session ....
%   I = bq.imreadND(url, user, password)
%
% 2.8X faster than using BQLib and more generic returning correct result
% Remember, all the image data is stored within matlab memory, so you can 
% run out of it if loading a very large image!!!
%
% INPUT:
%    url - a url to a Bisque image, may contain authentication inline
%            * Basic Auth - http://user:pass@host/path
%            * Bisque Mex - http://Mex:IIII@host/path
%
% OUTPUT:
%    I   - an ND matrix, with dimensions order: Y X C Z T
%
% EXAMPLES:
%   I = bq.imreadND('http://user:pass@host/imgsrv/XXXXX?slice=,,,2&remap=1');
%     this will fetch a 3D image (all z planes) at time point 2 and only
%     of the first channel
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

classdef Session
    properties
        %c = BQServer()
        mex = [];
        services = [];
        user = [];
        password = [];
        mex_url = [];
        auth_token = [];
        bisque_root = [];
    end % properties
    methods
        % mex_url     - url to the MEX documment
        % auth_token  - auth token given by the system
        % bisque_root - optional: server root 
        function [self] = init(self, mex_url, auth_token, bisque_root )

            self.mex_url    = mex_url;
            self.auth_token = auth_token;
            self.user = 'Mex';
            self.password = self.auth_token;

            % if Bisque root isn't given, try to parse from mex url
            if ~exist('bisque_root', 'var'),
                pattern = [ '^(?<scheme>\w+)://'...
                            '(?<auth>\w+:\w+@)?'...
                            '(?<authority>[\w\.:]+)/'...
                            '(?<path>[-\w~!$+|.,=/]+)'...
                            '(?<query>\?[\w!$+|.,-=/]+)?'...
                            '(?<fragment>#[\w!$+|.,-=/]+)?'];
                PURL = regexp(self.mex_url, pattern, 'names');
                bisque_root = PURL.authority;
            end
            self.bisque_root = bisque_root;   

            % set a global variable pointing to the current session
            %global bq__;
            %bq__ = self;               
            
            self.mex = bq.get_xml( [self.mex_url '?view=full'], self.user, self.password );
            self.update('RUNNING');
        end % init
    
        function [self] = update(self, status)
            if isempty(self.mex),
                return;
            end
            
            % update MEX document in memory
            m = self.mex.getDocumentElement();
            m.setAttribute('value', status);
            
            % update the document on the server
            input = sprintf('<mex uri="%s" value="%s" />', self.mex_url, status);
            [output, info] = bq.post(self.mex_url, input, self.user, self.password);
        end % update   
 
        function [self] = fail(self, message)
            if isempty(self.mex),
                return;
            end
            status = 'FAILED';
            
            % update MEX document in memory
            m = self.mex.getDocumentElement();
            m.setAttribute('value', status);
            bq.addTag(self.mex, m, 'message', message);
            
            % update the document on the server
            bq.put(self.mex_url, self.mex, self.user, self.password);
        end % fail           

        function [self] = finish(self, outputs)
            if isempty(self.mex),
                return;
            end
            status = 'FINISHED';
            
            % update MEX document in memory
            m = self.mex.getDocumentElement();
            m.setAttribute('value', status);
            
            %append outputs
            t = bq.addTag(self.mex, m, 'outputs');
            % dima: needs outputs here !!!!!!!
            
            % update the document on the server
            bq.put(self.mex_url, self.mex, self.user, self.password);
        end % finish 

    end% methods
end% classdef
