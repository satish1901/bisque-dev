%% BOBlobDetector3D - enhances 3D blob-like structures
%
%   INPUT:
%       im      - image
%       s       - sigma = [sigmax sigmay sigmaz]
%
%   OUTPUT:
%       imlog   - enhanced output image
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%       Dmitry Fedorov, www.dimin.net
%
%   REFERENCE:
%       A. Huertas and G. Medioni, 
%       Detection of intensity changes with subpixel accuracy using 
%       Laplacian-Gaussian masks,
%       IEEE Transactions on Pattern Analysis and Machine Intelligence, 
%       8, 5, 651-664, 1986.
%
%       D. Sage and F.R. Neumann and F. Hediger and S.M. Gasser and M. Unser 
%       Automatic tracking of individual fluorescence particles: 
%       application to the study of chromosome dynamics,
%       IEEE Transactions on Image Processing, 14, 9, 1372-1383, 2005, 
%
%   VERSION:
%       0.1 - 03/06/2010 First implementation
%       0.2 - code cleanup
%       0.3 - Dmitry: support for non double typed images
%
%%

function imlog = BOBlobDetector3D(im,s)

    %% 3D LoG
    [LoGx,Gx] = BOLoGFilterS1D(s(1));
    [LoGy,Gy] = BOLoGFilterS1D(s(2));
    [LoGz,Gz] = BOLoGFilterS1D(s(3));

    %% convolution - N2 slowest thing in the code now
    % imfilter is paralelized by matlab
    imlog = convsB(im, {LoGx,Gy,Gz}) + ... 
            convsB(im, {Gx,LoGy,Gz}) + ...
            convsB(im, {Gx,Gy,LoGz});


    % LoG = BOLoGFilter3D(s(1),s(2),s(3));
    % imlog = imfilter(im,LoG,'same');

    %% Use only hills, valleys are removed
    imlog(imlog<0) = 0;
    
    %% Normalize
    maxval = 1;
    if isinteger(imlog),
       maxval = intmax(class(imlog));
    end    
    %imlog = (imlog-min(imlog(:)))/(max(imlog(:))-min(imlog(:)));    
    imlog = (imlog-min(imlog(:))) * (maxval / (max(imlog(:))-min(imlog(:))) );    
end

%% Separable Convolution
function im = convsB(im,H)
    N = length(H);
    for k = 1:N,
        orient = ones(1,ndims(im));   
        orient(k) = numel(H{k});
        kernel = reshape(H{k}, orient);
        im = imfilter(im,kernel,'symmetric','same');  
    end
end
