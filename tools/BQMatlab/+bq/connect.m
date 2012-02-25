% [output, info] = bq.connect(method, url, location, input, user, password)
%
% Lowest level communication function that can do HTTP requests
%
% INPUT:
%   method   - HTTP method: GET/POST/PUT/DELETE
%   url      - url to fetch, may contain authentication which will be
%               stripped and sent in the HTTP header:
%               * Basic Auth - http://user:pass@host/path
%               * Bisque Mex - http://Mex:IIII@host/path
%   location - optional: file path to where to store fetched bytes, 
%                give [] if no file should be written but user/pass is req
%   input    - optional: stream to send to the server
%                give [] if no file should be written but user/pass is req
%   user     - optional: string with user name
%   password - optional: string with user password
%
% OUTPUT:
%    output - either byte vector or a file name if location was given 
%    info   - struct with HTTP return code and error string
%
% REQUIREMENTS:
%    For all practical purpouses you need an increased JVM heap
%    in order to get all the commmunication functionality going smoothly 
%    you should increase those settings by copying the file java.opts
%    to your matlab location:
%        MATLAB/YOUR-VERSION/bin/YOUR-ARCH/
%    where:
%        YOUR-VERSION will be something like R2009b, R2011a, ect...
%        YOUR-ARCH may be something like win64
%
% EXAMPLES:
%   s = bq.get('http://user:pass@host/path');
%   [s, info] = bq.get('http://host/path', [], 'user', 'pass');
%   [f, info] = bq.get('http://user:pass@host/path', 'myfile.xml');
%
% AUTHOR:
%   Dmitry Fedorov, www.dimin.net
%
% VERSION:
%   0.1 - 2011-06-27 First implementation
%

function [output, info] = connect(method, url, location, input, user, password)

    error(nargchk(2,6,nargin));
    %if nargin<2 && isempty(strfind(url, '@')),
    %    error('bq.urread:InvalidInput', 'You must provede user credentials if the URL does not contain them.');
    %end

    % This function requires Java
    if ~usejava('jvm')
       error(message('MATLAB:urlwrite:NoJvm'));
    end
    
    % Be sure the proxy settings are set.
    %import com.mathworks.mlwidgets.io.InterruptibleStreamCopier;
    com.mathworks.mlwidgets.html.HTMLPrefs.setProxySettings;
    
    % extract user name-password or Mex auth from the given in the URL
    % url = 'http://UUU:PPP@host.edu/images/1234';
    % url = 'https://Mex:IIII@host.edu/images/1234';
    if strfind(url, '@'),
        % parse the url
        expression = '(?<scheme>\w+)://(?<user>\w+):(?<password>\w+)@(?<path>\S+)';
        R = regexp(url, expression, 'names');
        user = R.user;
        password = R.password;        
        url = [R.scheme '://' R.path];
    end    
    
    % Matlab's urlread() doesn't do HTTP Request params, so work directly with Java
    server = java.net.URL(url);
    connection = server.openConnection();
    %connection.setReadTimeout(3000);
    connection.setRequestMethod(method);
    connection.setRequestProperty('Connection', 'Keep-Alive');
    
    if strcmpi(method, 'GET'),
        connection.setUseCaches(true);
        connection.setDoInput(true);
    elseif strcmpi(method, 'POST') || strcmpi(method, 'PUT'),
        connection.setDoInput(true);
        connection.setDoOutput(true);
        connection.setUseCaches(false);        
    end

    if exist('user', 'var') && exist('password', 'var') && ...
       ~isempty(user) && ~isempty(password),
        if ~strcmpi(user, 'Mex') ,
          connection.setRequestProperty('Authorization', ['Basic ' base64encode([user ':' password])]);
        else
          connection.setRequestProperty('Mex', password);
        end
    end
    
    connection.connect();
    
    if strcmpi(method, 'POST') || strcmpi(method, 'PUT'),
        if ~ischar(input),
            input = bq.xml2str(input);
        end
        out = java.io.OutputStreamWriter(connection.getOutputStream(), 'UTF-8');
        out.write(input);
        out.flush();    
    end    
    
    info.status  = connection.getResponseCode();
    info.error = char(readstream(connection.getErrorStream()));

    if info.status>=300,
        output = [];
    elseif exist('location', 'var') && ~isempty(location),    
        output = stream2file(connection.getInputStream(), location);        
        %output = stream2file( java.io.BufferedInputStream(connection.getInputStream(), 4*1024), location);
    else
        output = readstream(connection.getInputStream());
        %output = readstream( java.io.BufferedInputStream(connection.getInputStream(), 4*1024) );
    end
end

function out = base64encode(str)
    % Uses Sun-specific class, but we know that is the JVM Matlab ships with
    encoder = sun.misc.BASE64Encoder();
    out = char(encoder.encode(java.lang.String(str).getBytes()));
end

function output = readstream(inputStream)
    output = [];
    if isempty(inputStream), return; end
        
    %READSTREAM Read all bytes from stream to uint8
    try
        import com.mathworks.mlwidgets.io.InterruptibleStreamCopier;
        byteStream = java.io.ByteArrayOutputStream();
        isc = InterruptibleStreamCopier.getInterruptibleStreamCopier();
        isc.copyStream(inputStream, byteStream);
        inputStream.close();
        byteStream.close();
        output = typecast(byteStream.toByteArray', 'uint8'); %'
    catch err,
        error('bq.get:StreamCopyFailed', 'Error while downloading URL. Your JVM might not have enough heap memory...');        
    end
end

function output = stream2file(inputStream, location)
    %READSTREAM Read all bytes to a file
    output = [];
    if isempty(inputStream), return; end    

    % Specify the full path to the file so that getAbsolutePath will work when the
    % current directory is not the startup directory and urlwrite is given a
    % relative path.
    file = java.io.File(location);
    if ~file.isAbsolute
       location = fullfile(pwd,location);
       file = java.io.File(location);
    end

    % Make sure the path isn't nonsense.
    try
       file = file.getCanonicalFile;
    catch
       error('MATLAB:urlwrite:InvalidOutputLocation','Could not resolve file "%s".',char(file.getAbsolutePath));
    end

    % Open the output file.
    try
        fileOutputStream = java.io.FileOutputStream(file);
    catch
        error('MATLAB:urlwrite:InvalidOutputLocation','Could not open output file "%s".',char(file.getAbsolutePath));
    end
    
    % do the actual fetch and store file    
    try
        import com.mathworks.mlwidgets.io.InterruptibleStreamCopier;
        isc = InterruptibleStreamCopier.getInterruptibleStreamCopier();
        isc.copyStream(inputStream, fileOutputStream);        
        
        % we can use apache too
        %import org.apache.commons.io.CopyUtils;
        %asc = org.apache.commons.io.CopyUtils();        
        %asc.copy(inputStream, fileOutputStream);
        
        inputStream.close;
        fileOutputStream.close;
        output = char(file.getAbsolutePath);
    catch err,
        fileOutputStream.close;
        delete(file);
        error('bq.get:StreamCopyFailed', 'Error while downloading URL. Your JVM might not have enough heap memory...');
    end
end
