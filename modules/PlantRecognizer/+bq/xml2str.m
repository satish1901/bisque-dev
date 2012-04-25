%  bq.xml2str - converts XML document into string
%
%   INPUT:
%     doc - Document Object Model node
%
%   OUTPUT:
%     str - string
%
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       1 - 2011-03-29 First implementation 
%

function str = xml2str(doc)
    str = xmlwrite(doc);
end 
