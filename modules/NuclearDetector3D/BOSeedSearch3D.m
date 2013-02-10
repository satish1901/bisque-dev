%% BOSeedSearch3D - finding seeds
%    npo = BOSeedSearch3D(im, ns, t)
%
%   INPUT:
%       im      - LoG of nuclei channel
%       ns      - nuclear size
%       t       - a rannge of lowest intensity bounds
%
%   OUTPUT:
%       npo     - a cell with detected nuclei positions for each threshold
%                 an individual cell is a matrix of form:
%                   npo{t}(:,1) -> Y coordinate (starting at 1)
%                   npo{t}(:,2) -> X coordinate (starting at 1)
%                   npo{t}(:,3) -> Z coordinate (starting at 1)
%                   npo{t}(:,4) -> point IDs
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 Revision
%       0.3 - 24/09/2010 Speed up
%       0.4 - 15/10/2010 New local maxima
%       0.5 - 2011-06-04 by Dmitry: support for a threshold range
%%

function npo = BOSeedSearch3D(im, ns, t)
    % imdilate gets impossibly slow for large structuring elemnts
    % we'll aproximate using smaller interpolated version
    max_ns = [25, 25, 13];
    scale = ns ./ max_ns;
    scale(scale<1) = 1;
    if max(scale)>1,
        newsz = round(size(im) ./ scale);
        im = imresize3d(im, newsz, 'cubic');
        ns = ns ./ scale;
    else
        scale = [1,1,1];
    end
    
    %% cube is 10 times faster - Matlab converts it into 1D line elements
    %se = ones(round(2.0*ns+1.0));
   
    %% ellipsoid
    ns = round(ns);    
    [xg,yg,zg] = meshgrid(-ns(1):ns(1),-ns(2):ns(2),-ns(3):ns(3));
    se = ( (xg/ns(1)).^2 + (yg/ns(2)).^2 + (zg/ns(3)).^2 ) <= 1;
    %se = ( (xg/ns(1)).^2 + (yg/ns(2)).^2 + (zg/ns(3)).^2 ) <= 0.95;    
    %se = strel('arbitrary', se);

    %se = strel('disk', round(ns(1)));

    %% get candidates
    immax = imdilate(im, se, 'notpacked', 'same'); % N1 slowest thing in the code now
    all = find(im==immax);
    
    %% extract candidate locations for given thresholds
    npo = cell(length(t),1);
    for i = length(t):-1:1,
        idx=all;
        idx(im(idx)<t(i)) = [];

        [xc,yc,zc] = ind2sub(size(im),idx);
        np = [xc yc zc];  

        [~,idxs] = sort(im(idx),'descend');
        np = np(idxs,:);    
        np(:,4) = (1:size(np,1))';
        np(:,1) = np(:,1) .* scale(1);
        np(:,2) = np(:,2) .* scale(2);
        np(:,3) = np(:,3) .* scale(3);
        npo{i} = np;
    end
end