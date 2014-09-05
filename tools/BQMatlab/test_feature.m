root_url = 'http://128.111.185.26:8080';
user = 'admin';
pass = 'admin';
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Using bq.Feature 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%Provide the feature name and add a list of resources that the user wants
%to extract. If a file name is provided on fetch an hdf5 file acting as the
%response will be saved to the location provided else a Matlab hdf5 object 
%will be provided.

resource_list = {{'image','http://128.111.185.26:8080/image_service/image/00-JSrYb7cH8Y2EX28DX9PoF3'};
                 {'image','http://128.111.185.26:8080/image_service/image/00-7rEHGCmefZpdLW3porWsDE'}};
m = bq.Feature.fetch(resource_list, 'EHD', root_url, user, pass);
% m = 
% 
%            image: [2000x2 char]
%     feature_type: [20x2 char]
%          feature: [80x2 single]
%

%f = m.feature(:,1)';
% f =
%  0.3182    0.5455         0         0    0.1364    0.6753    0.0649 ...



%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Saves the response to disk
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% The set up is pretty much the same except one can provide a file name and
% the response will be save to disk at the location of the provided file
filename = 'hdf5file.h5';
bq.Feature.fetch(resource_list, 'EHD', root_url, user, pass, filename);

%displaying the hdf5 file 
h5disp('hdf5file.h5','/values');
%
% HDF5 hdf5file.h5 
% Dataset 'values' 
%     Size:  2
%     MaxSize:  Inf
%     Datatype:   H5T_COMPOUND
%         Member 'image':  H5T_STRING
%             String Length: 2000
%             Padding: H5T_STR_NULLTERM
%             Character Set: H5T_CSET_ASCII
%             Character Type: H5T_C_S1
%         Member 'feature_type':  H5T_STRING
%             String Length: 20
%             Padding: H5T_STR_NULLTERM
%             Character Set: H5T_CSET_ASCII
%             Character Type: H5T_C_S1
%         Member 'feature':  H5T_ARRAY
%             Size: 80
%             Base Type:  H5T_IEEE_F32LE (single)
%     ChunkSize:  1792
%     Filters:  none
%     Attributes:
%         'CLASS':  'TABLE'
%         'VERSION':  '2.7'
%         'TITLE':  ''
%         'FIELD_0_NAME':  'image'
%         'FIELD_1_NAME':  'feature_type'
%         'FIELD_2_NAME':  'feature'
%         'FIELD_0_FILL':  ''
%         'FIELD_1_FILL':  ''
%         'FIELD_2_FILL':  0.000000
%         'NROWS':  2

%reading from the table
m = h5read('hdf5file.h5','/values');
%
% m = 
% 
%            image: [2000x2 char]
%     feature_type: [20x2 char]
%          feature: [80x2 single]
%


%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Storing images on bisque and then extracting features (unfinished)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% Alright lets have some fun. We can upload to bisque and then extract
% features from the uploaded image

%Here is a very famous image
I = imread('coins.png'); 

%Lets upload it to bisque
args = struct('filename', 'coins.png');
image = bq.Image.store(I, args, root_url, user, pass); 


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





