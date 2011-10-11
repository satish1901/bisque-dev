function [genus, specie, confidence, commonName ,url] = run_gplant_recognizer(I)



% number of trained species =11
if size(I,3)==3
    I=rgb2gray(I);
end

%downsampling
[h,w]=size(I);
while max(h,w)>2000
    I=imresize(I,1/2);
    [h,w]=size(I);
end

%...............................................................
%specify the name of feature file to be used by svm classifier

svmFeatFile='queryFeatFile';

generate_SVM_feature(I, svmFeatFile);


%...............................................................
%call the SVM classifier and the trained model

svmOutput='SVMoutput';


% %linux
% system(sprintf('./svm-scale -r g_range %s > %sS',svmFeatFile,svmFeatFile));
% system(sprintf('./svm-predict -b 1 %sS  gtrain.model %s', svmFeatFile, svmOutput));
%  


%windows
system(sprintf('svm-scale -r g_range %s > %sS',svmFeatFile,svmFeatFile));
system(sprintf('svm-predict -b 1 %sS  gtrain.model %s', svmFeatFile, svmOutput));
%...............................................................
%get the final tag prediction from the SVM results

[otags,p1 , p2, p3 ,p4 ,p5, p6 , p7 , p8 ,p9 ,p10, p11] = textread(svmOutput,'%d %f %f %f %f %f %f %f %f %f %f %f','headerlines',1);
prob=[p1 , p2, p3 ,p4 ,p5, p6 , p7 , p8 ,p9 ,p10, p11];
pc=sum(prob)/sum(sum(prob));
% get the class with highest probability
[prob_tag tag]=max(pc);
pc2=pc; pc2(tag)=0;
[prob_tag2 tag2]=max(pc2);
confidence=prob_tag/(prob_tag+prob_tag2);
%...............................................................
%Display the final results
[genus,specie, commonName ,url]=get_specie(tag);
% % clc;
% % disp('.............................................................................');
% % disp(sprintf('The plant is idenified as %s with confidence %f',specie, confidence));