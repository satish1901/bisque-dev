url = 'http://128.111.185.26:8080';
user = 'admin';
pass = 'admin';
root = 'http://128.111.185.26:8080';
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% using bq.Feature (Simple Case) 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%Provide the feature name and add a list of resources that the user wants
%to extract. If a file name is provided on fetch an hdf5 file acting as the
%response will be saved to the location provided else a Matlab hdf5 object 
%will be provided.
feature = bq.Feature('EHD', [], user, pass, root);
image_url = 'http://128.111.185.26:8080/image_service/image/00-7rEHGCmefZpdLW3porWsDE';
r = struct('image',image_url);
feature.addResource(r);
image_url = 'http://128.111.185.26:8080/image_service/image/00-JSrYb7cH8Y2EX28DX9PoF3';
r = struct('image',image_url);
feature.addResource(r);

%Saves the response to disk
location = feature.fetch('hdf5file.h5');

%returns hdf5 matlab struct
[response,info] = feature.fetch();

% response = 
% 
%            image: [2000x2 char]
%     feature_type: [20x2 char]
%          feature: [80x2 single]

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Storing images on bisque and then extracting features
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%



%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Using Image Service and Feature Service
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%



%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Extracting Features from a dataset of images
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%





