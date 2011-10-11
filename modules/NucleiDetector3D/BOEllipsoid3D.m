function idx = BOEllipsoid3D(xn,yn,zn,x0,y0,z0,rx,ry,rz)  
%% BOEllipsoid3D - indices of 3D elipsoid
%
%   INPUT:
%       xn,yn,zn - image size
%       x0,y0,z0 - elipsoid origin point
%       rx,ry,rz - semi-axes are of lengths
%
%   OUTPUT:
%       idx      - indices
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%
%   VERSION:
%       0.1 - 24/09/2010 First implementation
%%
rx = round(rx);
ry = round(ry);
rz = round(rz);
x1 = max(1,x0-rx); x2 = min(xn,x0+rx); 
y1 = max(1,y0-ry); y2 = min(yn,y0+ry); 
z1 = max(1,z0-rz); z2 = min(zn,z0+rz); 
[xg,yg,zg] = meshgrid(x1:x2,y1:y2,z1:z2);
idx1 = find( ( ((xg-x0)/rx).^2 + ((yg-y0)/ry).^2 + ((zg-z0)/rz).^2 ) <= 1);
idx = sub2ind([xn,yn,zn],xg(idx1),yg(idx1),zg(idx1));
end