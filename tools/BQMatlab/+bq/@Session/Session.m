% bq.Session
% A class wrapping a module session, wich goes in the following sequence:
%
% 1) initing session
% s = bq.Session('MEX_URL', 'AUTH_TOKEN');
%
% 2) while running
% s.update('RUNNING');
% % do stuff....
% s.update('10%');
% % do stuff....
%
% 3) creating results
% s.finish(outputs);
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

classdef Session < handle
    
    properties
        mex = [];
        services = [];
        user = [];
        password = [];
        mex_url = [];
        auth_token = [];
        bisque_root = [];
        
        error = struct();
    end % properties
    
    methods
        
        % mex_url     - url to the MEX documment
        % auth_token  - auth token given by the system
        % bisque_root - optional: server root 
        function [self] = Session(mex_url, auth_token, bisque_root)
            if nargin==2,
                self.init(mex_url, auth_token);
            elseif nargin==3,
                self.init(mex_url, auth_token, bisque_root);
            end
        end % constructor
        
        % mex_url     - url to the MEX documment
        % auth_token  - auth token given by the system
        % bisque_root - optional: server root 
        function init(self, mex_url, auth_token, bisque_root )

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
            
            self.mex = bq.get_xml( [self.mex_url '?view=full'], self.user, self.password );
        end % init
    
        function update(self, status)
            self.error = struct();
            if isempty(self.mex),
                return;
            end
            
            % update MEX document in memory
            m = self.mex.getDocumentElement();
            m.setAttribute('value', status);
            
            % update the document on the server
            input = sprintf('<mex uri="%s" value="%s" />', self.mex_url, status);
            bq.post(self.mex_url, input, self.user, self.password);
        end % update   
 
        function fail(self, message)
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

        function finish(self, outputs)
            if isempty(self.mex),
                return;
            end
            status = 'FINISHED';
            
            % update MEX document in memory
            m = self.mex.getDocumentElement();
            m.setAttribute('value', status);
            
            %append outputs
            if isa(outputs, 'org.apache.xerces.dom.ElementImpl') ||...
               isa(outputs, 'org.apache.xerces.dom.DeferredElementImpl'),
                root = self.mex.getDocumentElement();
                root.appendChild(outputs);
            elseif iscell(outputs),
                t = bq.addTag(self.mex, m, 'outputs');
                % iterate over cell and create all XML elements
                % dima: implement
            end            
            
            % update the document on the server
            bq.put(self.mex_url, self.mex, self.user, self.password);
        end % finish 

    end% methods
end% classdef
