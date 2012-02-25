% Finds tags of interest and returns their values in proper formats
%   info = bq.iminfo(url, user, password)
%
% INPUT:
%   url      - Bisque DataService URL to an image, may contain 
%              authentication which will be stripped and sent in the HTTP header:
%               * Basic Auth - http://user:pass@host/path
%               * Bisque Mex - http://Mex:IIII@host/path
%   user     - optional: string with user name
%   password - optional: string with user password
%
% OUTPUT:
%   info     - a struct containing image information, some fileds include:
%              info.src                - ImageSrvice url to the image
%              info.image_num_x        - Image width
%              info.pixel_resolution_x - pixel resolution in X axis
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

function info = iminfo(url, user, password)

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
    
    %% fetch image resource document
    if exist('user', 'var') && exist('password', 'var'),
        doc = bq.get_xml( [url '?view=full'], user, password );
    else
        doc = bq.get_xml( [url '?view=full'] );    
    end
   
    exp_image = xpath.compile('//image');
    image = exp_image.evaluate(doc, XPathConstants.NODE);
    
    info = struct();
    info.src = char(image.getAttribute('src'));    
    
    %% fetch metadata from image service
    if exist('user', 'var') && exist('password', 'var'),
        doc_meta = bq.get_xml( [info.src '?meta'], user, password );
    else
        doc_meta = bq.get_xml( [info.src '?meta'] );    
    end    
    template = '//image/tag[@name=''%s'']';
    tags = { 'filename',    'str'; 
             'image_num_x', 'int'; 
             'image_num_y', 'int';              
             'image_num_z', 'int'; 
             'image_num_t', 'int';
             'image_num_c', 'int';             
             'image_pixel_depth',  'int';
             'image_pixel_format', 'str';             
             'pixel_resolution_x', 'double';
             'pixel_resolution_y', 'double';
             'pixel_resolution_z', 'double';
             'pixel_resolution_t', 'double';
           };
    info = parsetags(info, doc_meta, tags, template);
    
    %% parse image resource tags overwriting some tag values
    template = '//image/tag[@name=''%s'']';
    tags = { 'filename',             'str';
             'pixel_resolution_x_y', 'double';             
             'pixel_resolution_x',   'double';
             'pixel_resolution_y',   'double';
             'pixel_resolution_z',   'double';
             'pixel_resolution_t',   'double';
           };
    info = parsetags(info, doc, tags, template);
    
end

function s = parsetags(s, doc, tags, template)
    import javax.xml.xpath.*;
    factory = XPathFactory.newInstance;
    xpath = factory.newXPath;    
    
    for i=1:size(tags,1),
        name = tags{i,1};
        type = tags{i,2};        
        expression = sprintf(template, name);
        t = xpath.evaluate(expression, doc, XPathConstants.NODE);    

        if ~isempty(t) && strcmp(type, 'double'), 
            s.(name) = str2double(t.getAttribute('value')); 
        elseif ~isempty(t) && strcmp(type, 'int'), 
            s.(name) = str2num(t.getAttribute('value')); 
        elseif ~isempty(t), 
            s.(name) = char(t.getAttribute('value')); 
        end
    end
end

% old implementation using BQJavaLib
%     % this requires: javaaddpath('./bisque.jar'); import bisque.*
%     BQ = bisque.BQMatlab;
% 
%     image = BQ.loadImage( [url '?view=full'] );
%     src = image.src;
% 
%     % get image geometry
%     info = struct();
%     info.x = image.x;
%     info.y = image.y;
%     info.z = image.z;
%     info.t = image.t;
%     info.ch = image.ch;
%     info.pixelDepth = image.d;
%     info.pixelFormat = image.f;
% 
%     % get image tags
%     %t = image.findTag('pixel_resolution_x_y');
%     %if ~isempty(t),
%     %  resolutionXY = str2double(char(t.getValue()));
%     %end
