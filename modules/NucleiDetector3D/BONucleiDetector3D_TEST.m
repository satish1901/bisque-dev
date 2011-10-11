%% Clear ALL
clc; clear all; close all;
%% Load image
load 'mat/arabidopsis3D.mat'
%% Normalize
imn = double(imn);  imm = double(imm); 
imn = (imn-min(imn(:)))/(max(imn(:))-min(imn(:)));
imm = (imm-min(imm(:)))/(max(imm(:))-min(imm(:)));
%% Nuclei detection - setup
ns = 1.7; t = 0.2; ns = [ns/resolutionx ns/resolutiony ns/resolutionz];
%% Nuclei detection - run
tic
np = BONucleiDetector3D(imn,[],ns,t);
toc
return
%% Plot 
p = 10; range = 2; p1 = 50; p2 = 60; %size(imn,3); 
%for p=p1:p2
    figure;
    plane = p; 
    immax = zeros(size(imn,1),size(imn,2));
    for i=1:size(imn,3)
        if i>=(plane-range) && i<=(plane+range)
            immax = max(immax,imn(:,:,i));
        end
    end
    imagesc(immax); colormap gray; hold on;
    for i=1:size(np,1)
        if np(i,3)>=(plane-range) && np(i,3)<=(plane+range)
            plot(np(i,2),np(i,1), 'og')
            hold on
        end
    end
    set(gca,'xtick',[]);set(gca,'ytick',[]); colormap gray; axis equal; axis tight;
    pause(0.1)
%end