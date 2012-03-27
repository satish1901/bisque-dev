%% GetCentroidDescriptors3D - return descriptors for each location
%   right now it returns a sum of intensities of the voxels in the ellipsoid
%   this used to be called: BOMaskDescriptor3D
%  dt = GetCentroidDescriptors3D(im, imlog, np, ns, all)
%
%   INPUT:
%       im      - nuclear channel
%       imlog   - LoG of nuclear channel
%       np      - detected nuclei positions, is a matrix of form:
%                   np(:,1) -> Y coordinate (starting at 1)
%                   np(:,2) -> X coordinate (starting at 1)
%                   np(:,3) -> Z coordinate (starting at 1)
%                   np(:,4) -> point IDs
%       ns      - nuclear size
%       all     - optional: if present then all measures will be computed
%
%   OUTPUT:
%       dt      - descriptor values, a cell with structs containing:
%                 dt{i}.sum      - intensity sum for the image
%                 dt{i}.mean     - intensity mean for the image
%                 dt{i}.log_mean - intensity mean for the LoG image
%                 dt{i}.mad      - intensity MAD for the image
%                 
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 Revision
%       0.3 - 24/09/2010 Speed up
%       0.4 - 2011-06-04 by Dmitry: complete rewrite with speed improvement by 2.5X
%%

function dt = GetCentroidDescriptors3D(im, imlog, np, ns, all)
    if nargin<5, all=0; end

    %% Construct ellipsoid of ns size    
    dt = cell(size(np,1),1);    
    ellipsoid = Ellipsoid3D(ns);
    
    %% transpose ellipsoid and get a descriptor
    for i=1:size(np,1)
        idx = TransposeEllipsoid( ellipsoid, np(i,:), size(im) );

        s = struct();        
        v = im(idx); 
        s.sum = sum(v(:));       
        
        if all==1,
            vlog = imlog(idx);  
            s.mean = mean(v(:));
            s.log_mean = mean(vlog(:));
            s.mad = MedAD(v(:));
        end
        
        dt{i} = s;
    end
end

function c = Ellipsoid3D(r)  
    % create a universal ellipse
    r = round(r);
    [xg,yg,zg] = meshgrid(-r(1):r(1), -r(2):r(2), -r(3):r(3));
    idx1 = find( ( (xg/r(1)).^2 + (yg/r(2)).^2 + (zg/r(3)).^2 ) <= 1);
    c = [xg(idx1), yg(idx1), zg(idx1)];
end

function idx = TransposeEllipsoid( c, p, imgsz )  
    % transpose and crop the ellipse to the position p in the image of size 

    e = [c(:,1)+p(1), c(:,2)+p(2), c(:,3)+p(3)];
    [j, ~] = find(e(:,1)>0 & e(:,2)>0 & e(:,3)>0 & ...
                  e(:,1)<=imgsz(1) & e(:,2)<=imgsz(2) & e(:,3)<=imgsz(3) );
    e = e(j,:);
    idx = sub2ind(imgsz, e(:,1), e(:,2), e(:,3) );
end

