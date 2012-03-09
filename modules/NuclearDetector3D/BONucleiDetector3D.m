function np = BONucleiDetector3D(imn,imm,ns,t,BQ, mex)
%%  BONucleiDetector3D - 3D nuclei detector
%   
%   REFERENCE:
%       B. Obara and D. Fedorov and C.D. Banna and B.S. Manjunath,
%       Automatic system for detection and validation of cell nuclei in 
%       3D CLS microscopy imagery, SOON :)
%
%   INPUT:
%       imn     - nuclei channel
%       imm     - membrane channel
%       ns      - nuclei size[pixels] = 
%                   ns[microns]*[1/resolutionx 1/resolutiony 1/resolutionz]
%       t       - lowest intensity bound,
%
%   OUTPUT:
%       np      - detected nuclei positions, is a matrix where
%                   np(:,1) -> Y coordinate (starting at 1)
%                   np(:,2) -> X coordinate (starting at 1)
%                   np(:,3) -> Z coordinate (starting at 1)
%                   np(:,4) -> point IDs
%                   np(:,5) -> average intensity of nuclei volumes
%                   np(:,6) -> average LoG intensity of nuclei volumes

%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 LoG + revision
%       0.3 - 24/09/2010 Speed up
%% LoG

BQ.updateProgress(mex, '10% - blob detector');
imlog = BOBlobDetector3D(imn,ns);

%% Finding seeds
BQ.updateProgress(mex, '30% - seed search');
np = BOSeedSearch3D(imlog,ns,t);

%% Filtering
BQ.updateProgress(mex, '60% - masking');
dt = BOMaskDescriptor3D(imn,imlog,np,ns);

BQ.updateProgress(mex, '80% - filtering');
if ~isempty(imm)
    np = BOProfileDescriptor3D(imm,np,dt,ns*1.1);
else
    np = BOStatDescriptor3D(imn,np,dt,ns*1.1);
end

%% Average intensity values          
np(:,5) = dt(np(:,4),1);
np(:,6) = dt(np(:,4),2);

end
