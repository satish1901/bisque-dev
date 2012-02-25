% read_stack - load image stack creating 3D matrix
%
% Input:
%   filename - string with file name of image to decode 
%   channel  - the number of the channel to load
%
% Output:
%   img      - 3D matrix of the image in the native format
%
% ex:
%   img = bim.read_stack('myfile.tif', 1);
%
% Notes: 
%   Creates 8,16,32,64 bit arrays in float, signed and unsigned
%   If the input is 1 or 4 bit, that will be converted to 8bits
%

function img = read_stack(filename, channel)

  [im, format, pages, xyzr, metatxt] = bim.bimread( filename, 1 );
  sz = size(im);
  img = zeros(sz(1), sz(2), pages, class(im));
  if length(sz)==2,
     img(:,:,1) = im;
  else
     img(:,:,1) = im(:,:,channel);
  end
  
  for i=2:pages,
    im = bim.bimread( filename, i );
    
    if length(sz)==2,
       img(:,:,i) = im;
    else
       img(:,:,i) = im(:,:,channel);
    end    
    
  end
   
  clear mex;
end