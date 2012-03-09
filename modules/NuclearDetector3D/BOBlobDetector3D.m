function imlog = BOBlobDetector3D(im,s)
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
%
%   VERSION:
%       0.1 - 03/06/2010 First implementation
%%
fprintf('BOBlobDetector3D ... \n');
%% 3D LoG
[LoGx1,LoGx2] = BOLoGFilterS1D(s(1));
[LoGy1,LoGy2] = BOLoGFilterS1D(s(2));
[LoGz1,LoGz2] = BOLoGFilterS1D(s(3));
%% Convolving image with 3D LoG
% imlog = convsA(im,{LoGx1,LoGy2,LoGz2}) + ... 
%         convsA(im,{LoGx2,LoGy1,LoGz2}) + ...
%         convsA(im,{LoGx2,LoGy2,LoGz1});
%     
imlog = convsB(im,{LoGx1,LoGy2,LoGz2}) + ... 
        convsB(im,{LoGx2,LoGy1,LoGz2}) + ...
        convsB(im,{LoGx2,LoGy2,LoGz1});
%
% imlog = convsC(im,{LoGx1,LoGy2,LoGz2}) + ... 
%         convsC(im,{LoGx2,LoGy1,LoGz2}) + ...
%         convsC(im,{LoGx2,LoGy2,LoGz1});
%     
% imlog = convnsep(LoGx1,LoGy2,LoGz2,im,'same') + ... 
%         convnsep(LoGx2,LoGy1,LoGz2,im,'same') + ...
%         convnsep(LoGx2,LoGy2,LoGz1,im,'same');
%
% LoG = BOLoGFilter3D(s(1),s(2),s(3));
% imlog = imfilter(im,LoG,'same');
%% Use only hills, valleys are removed
imlog(imlog<0) = 0;
%% Normalize
imlog = (imlog-min(imlog(:)))/(max(imlog(:))-min(imlog(:)));    
end
%% Sepalable Convolution
function C = convsA(im,H)
    N = length(H);
    C = im;
    for k = 1:N,
        orient = ones(1,ndims(im));   
        orient(k) = numel(H{k});
        kernel = reshape(H{k}, orient);
        C = convn(C,kernel,'same');  
    end
end
%% Sepalable Convolution
function C = convsB(im,H)
    N = length(H);
    C = im;
    for k = 1:N,
        orient = ones(1,ndims(im));   
        orient(k) = numel(H{k});
        kernel = reshape(H{k}, orient);
        C = imfilter(C,kernel,'same');  
    end
end
%% Sepalable Convolution v2 - NOT FINISHED
function C = convsC(im,H)
% size(V) = (1000,1000,1000);
% size(G) = 100,100,100.
% tmp=conv2(reshape(V,100,[]), Gx,'same'); %convolution in x
% tmp=conv2(reshape(tmp.',1000,[]), Gy,'same'); %convolution in y
% tmp=conv2(reshape(tmp.',1000,[]), Gz,'same'); %convolution in z
    N = length(H);
    C = im;
    s = size(im);
    for k = 1:N,
        orient = ones(1,ndims(im));   
        orient(k) = numel(H{k});
        kernel = reshape(H{k}, orient);
        kernel = H{k};
        if k == 1
            C = conv2(reshape(C,s(k),[]),kernel,'same');  
        else
            C = conv2(reshape(C.',s(k),[]),kernel,'same');  
        end
    end
end