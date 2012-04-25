function GF=get_feature_vector_SeparateMB(Ig,scale,orientation,window_size)

%Ig : has to be gray level
[height,width]=size(Ig) ;
% --------------- generate the Gabor FFT data ---------------------
disp('generating the Gabor FFT matrix');


Nf = window_size; %filter size
freq = [0.01 0.4];%[0.05 0.4];
flag = 0;

j = sqrt(-1);

for s = 1:scale,
    for n = 1:orientation,
        [Gr,Gi] = Gabor(Nf,[s n],freq,[scale orientation],flag);
        F = fft2(Gr+j*Gi);
        F(1,1) = 0;
        GW(Nf*(s-1)+1:Nf*s,Nf*(n-1)+1:Nf*n) = F;
    end;
end;
% -------------------------------------------------------------------------
% % Divide the image into overlapping patches and compute feature vectors for each patch
disp('computing features');
Nh = floor(height/Nf*2)-1;
Nw = floor(width/Nf*2)-1;

GF=[];
% A = zeros(scale*orientation*2,Nh*Nw);
% meanF=0;
for i = 1:Nh,
    for j = 1:Nw,
        %[i h w]
        patch = Ig((i-1)*Nf/2+1:(i-1)*Nf/2+Nf, (j-1)*Nf/2+1:(j-1)*Nf/2+Nf);
        F = Fea_Gabor_brodatz(patch, GW, Nf, scale, orientation,Nf);
        
        
        GF=[GF; F(:,1)' F(:,2)'];
%         A(:,(i-1)*Nw+j) = [F(:,1); F(:,2)];
    end;
end;


