function np = BOSeedSearch3D(im,ns,t,type)
%% BOSeedSearch3D - finding seeds
%
%   INPUT:
%       im      - LoG of nuclei channel
%       ns      - nuclei size
%       t       - lowest intensity bound
%
%   OUTPUT:
%       np      - detected nuclei positions
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 Revision
%       0.3 - 24/09/2010 Speed up
%       0.4 - 15/10/2010 New local maxima
%%
fprintf('BOSeedSearch3D ... \n');
%% Setup
if nargin<4; type = 0; end
%% Regional Max
if type==0
    % cube is 10 times faster - Matlab converts it into 1D line elements
    %se = ones(2*ns+1);
    
    % ellipsoid
    ns = round(ns);
    [xg,yg,zg] = meshgrid(-ns(1):ns(1),-ns(2):ns(2),-ns(3):ns(3));
    se = ( (xg/ns(1)).^2 + (yg/ns(2)).^2 + (zg/ns(3)).^2 ) <= 1;
    
    immax = imdilate(im,se);
    
    idx = find(im==immax);
    idx(im(idx)<t) = [];
    
    [xc,yc,zc] = ind2sub(size(im),idx);
    np = [xc yc zc];    
    
    [s,idxs] = sort(im(idx),'descend');
    np = np(idxs,:);    
    np(:,4) = (1:size(np,1))';
elseif type==1
    %% ----------------- OLD ----------------------------------------------
    immax = imregionalmax(im); 
    immax = immultiply(immax,im>t);
    idx = find(immax);
    [xc,yc,zc] = ind2sub(size(im),idx);
    np = [xc yc zc];
    
    [s,idxs] = sort(im(idx),'descend');
    np = np(idxs,:);    
    
    np(:,4) = (1:size(np,1))';
else
    %% ----------------- OLD ----------------------------------------------
    %% Setup
    np = []; [xn,yn,zn] = size(im);
    %[max_c,idxf] = max(im(:)); 
    max_c = max(im(:)); t = t*max_c; immask = im; 
    %% Loop
    while max_c > t
        flag = 0; 
        while flag==0
            %if ~isempty(idxf) 
            %    flag = 1; 
            %    [yc,xc,zc] = ind2sub([xn,yn,zn],idxf(1));
            %end
            idxf = find(immask==max_c,1,'first');
            [xc,yc,zc] = ind2sub([xn,yn,zn],idxf);
            if ~isempty([xc,yc,zc]); flag = 1; end
        end
        if flag==1
            idx = BOEllipsoid3D(xn,yn,zn,xc,yc,zc,ns(1),ns(2),ns(3));        
            immask(idx) = 0;
            %imagesc(immask(:,:,zc));
            %pause(0.2)
            %[max_c,idxf] = max(immask(:));
            max_c = max(immask(:));
            np = [np; xc yc zc];
        end
    end
    np(:,4) = (1:size(np,1))';
end
end