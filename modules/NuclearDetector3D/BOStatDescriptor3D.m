function npp = BOStatDescriptor3D(im,np,dt,ns)
%% BOStatDescriptor3D - pruning nuclei position based on statistical
%% measures
%
%   INPUT:
%       im      - nuclei channel
%       np      - detected nuclei positions
%       dt      - descriptor values
%       ns      - nuclei size
%
%   OUTPUT:
%       npp     - pruned nuclei positions
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 Revision
%       0.3 - 24/09/2010 Speed up
%%
fprintf('BOStatDescriptor3D ... \n');
%% Settings
dmax = sqrt( ns(1)^2 + ns(2)^2 + ns(3)^2 ); 
npp = np; ts = size(npp,1);
stop = 1; stopmin = 0; j = 1;
xy2z = ns(1)/ns(3); % X/Z resolution
%xy2z = 1;
%% Loop
while(stop>0)
    ix = 1;
    if j>ts; break; end
    m = 10000000;
    for i=1:ts
        if i~=j 
            d = sqrt(   (npp(i,1)-npp(j,1))^2 + ... 
                        (npp(i,2)-npp(j,2))^2 + ... 
                        (xy2z*npp(i,3)-xy2z*npp(j,3))^2);
            if m > d
                m = d; ix = i; jx = j;
            end
        end
    end
%%  
    if (m<dmax)
        s1 = dt(npp(jx,4),3);        
        s2 = dt(npp(ix,4),3);        
        if s1<s2
            npp(jx,:) = [];
        else
            npp(ix,:) = [];
        end
        stopmin = 1;
        ts = size(npp,1);   
    end
    j = j + 1;
    if j>ts
        if stopmin>0
            stopmin = 0;
            j = 1;
        else
            stop = 0;
        end
    end
end
%% Sort
npp = sortrows(npp,4);
end