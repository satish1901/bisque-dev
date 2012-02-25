% Loads ND images from the Bisque system without requiring local storage
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

function I = imreadND(url, user, password)

    %% parse the url
    if strfind(url, '@'),
        expression = '(?<scheme>\w+)://(?<user>\w+):(?<password>\w+)@(?<path>\S+)';
        R = regexp(url, expression, 'names');
        user = R.user;
        password = R.password;        
    end    

    %% import necessary XPath includes
    import javax.xml.xpath.*
    factory = XPathFactory.newInstance;
    xpath = factory.newXPath;
    
    %% fetch metadata from image service
    if exist('user', 'var') && exist('password', 'var'),
        doc = bq.get_xml( [url '&dims'], user, password );
    else
        doc = bq.get_xml( [url '&dims'] );    
    end    
    template = '//image/tag[@name=''%s'']';
    tags = { 'zsize',       'int'; 
             'tsize',       'int';              
             'channels',    'int'; 
             'width',       'int';
             'height',      'int';             
             'depth',       'int';
             'pixelType',   'str';
             'pixelFormat', 'str';
           };
    info = bq.parsetags(doc, tags, template);

    %% fetch image data stream and reshape it
    [I, res] = bq.get([url '&format=raw'], [], user, password);
    I = typecast(I, info.pixelFormat);
    I = squeeze(reshape(I, info.height, info.width, info.channels, info.zsize, info.tsize)); 
    
    % matlab uses row-major order, opposite to column-major in Bisque
    % we need to transpose all the image planes
    p = 1:length(size(I));
    p(1:2) = [2 1];
    I = permute(I, p);
end

