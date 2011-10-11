function generate_SVM_feature(Ig, svmFeatFile)

[hh,ww,dim]=size(Ig);
%


%     figure;  imshow(I);
%

if dim==3
    Ig=rgb2gray(Ig);  %get the green component (faster than rgb2gray)
end

%
%     figure; imshow(Ig); axis on; grid on;

% %~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% % Extract texture features
% %~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
scale=6;
orientation=6;
window_size=64;
%

GF=get_feature_vector_SeparateMB(Ig,scale,orientation,window_size);

NM=size(GF,1);

% %~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% % save the texture features
% %~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

%
fid=fopen(svmFeatFile,'w'); %open the svm feature file

dummyTag=1;

for nm=1:NM
    fprintf(fid, ' %d', dummyTag);
    %     fwrite(fid, downsampling, 'uint8');
    %     fwrite(fid, rect, 'uint16');
    for fi=1:size(GF,2)
        fprintf(fid, ' %d:%f', fi, GF(nm,fi));
        %             fwrite(fid, meanF(nm,fi) ,'double');
    end
    
    fprintf(fid, '\n');
end

fclose(fid);