function dt = BOMaskDescriptor3D(im,imlog,np,ns)
%% BOMaskDescriptor3D - table with descriptor measures
%
%   INPUT:
%       im      - nuclei channel
%       imlog   - LoG of nuclei channel
%       np      - detected nuclei positions
%       ns      - nuclei size
%
%   OUTPUT:
%       dt      - descriptor values
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 Revision
%       0.3 - 24/09/2010 Speed up
%%
fprintf('BOMaskDescriptor3D ... \n');
%% Setup
[xn,yn,zn] = size(im);
dt = zeros(size(np,1),5);
%% Loop
for i=1:size(np,1)
    idx = BOEllipsoid3D(xn,yn,zn,np(i,1),np(i,2),np(1,3),ns(1),ns(2),ns(3));        
    v = im(idx);    
    vlog = imlog(idx);    
    m = mean(double(v(:)));
    mlog = mean(double(vlog(:)));
    s = sum(double(v(:)));    
    dt(i,1) = m;
    dt(i,2) = mlog;
    dt(i,3) = s;    
end
end