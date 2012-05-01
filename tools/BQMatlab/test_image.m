imurl = 'http://bisque.ece.ucsb.edu/data_service/image/161855';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% using bq.Image
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% fetch image as a matrix
image = bq.Factory.fetch(imurl);
im1 = image.remap(1).fetch();
im2 = image.remap(2).fetch();
figure; imagesc(im1(:,:,6));
figure; imagesc(im2(:,:,6));


% fetch image into a file using its original name
image = bq.Factory.fetch(imurl);
filename = image.fetch([]);



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% storing an image matrix into Bisque
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
host = 'http://vidi.ece.ucsb.edu:9090';
user = 'XXXX';
pass = 'XXXX';


% 2D image with no resolution
image = zeros(128, 128, 'double');
args = struct('filename', 'my_2d_double_image.ome.tif');

image = bq.Image.store(image, args, host, user, pass); 
if ~isempty(image),
    image.addTag('about', 'this is a 2D image upload from Matlab API');
    image.save();
end

% 3D image with no resolution
image = zeros(128, 128, 5, 'int16');
args = struct('filename', 'my_3d_XYZ_int16_image.ome.tif');
args.dim = struct('z', 0);
args.res = struct('x', 0.5, 'y', 0.5, 'z', 1.0);

image = bq.Image.store(image, args, host, user, pass); 
if ~isempty(image),
    image.addTag('about', 'this is a 3D image upload from Matlab API');
    image.save();
end

% 4D image with no resolution
image = zeros(128, 128, 2, 5, 'uint16');
args = struct('filename', 'my_3d_XYCZ_uint16_image.ome.tif');
args.dim = struct('c', 0, 'z', 0);
args.res = struct('x', 0.5, 'y', 0.5, 'z', 1.0);

image = bq.Image.store(image, args, host, user, pass); 
if ~isempty(image),
    image.addTag('about', 'this is a 4D image upload from Matlab API');
    image.save();
end

% 5D image with no resolution
image = zeros(128, 128, 2, 5, 10, 'uint8');
args = struct('filename', 'my_3d_XYCZ_uint8_image.ome.tif');
args.res = struct('x', 0.5, 'y', 0.5, 'z', 1.0, 't', 10.0);

image = bq.Image.store(image, args, host, user, pass); 
if ~isempty(image),
    image.addTag('about', 'this is a 5D image upload from Matlab API');
    image.save();
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% storing an image file into Bisque
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
host = 'http://vidi.ece.ucsb.edu:9090';
user = 'XXX';
pass = 'XXX';
filename = 'PATH/test_online.tif';

image = bq.Image.store(filename, [], host, user, pass); 
if ~isempty(image),
    image.addTag('about', 'this is an image upload from Matlab API');
    image.save();
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% lower level API
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% direct reading of a public image by its image service URL
%3D image 512x512x13Zx2C: http://bisque.ece.ucsb.edu/data_service/image/161855
info = bq.iminfo(imurl);
url = bq.Url(info.src);

% read using multi dimentional reader from bisque 
tic;
I4d = bq.imreadND(url.toString());
toc;
figure;
imagesc(I4d(:,:,5));
% Elapsed time is 1.428959 seconds.

url.pushQuery('remap', '1');
tic;
I3d = bq.imreadND(url.toString());
toc;
figure;
imagesc(I3d(:,:,5));
% Elapsed time is 0.787190 seconds.

url.pushQuery('slice', ',,5,');
tic;
I2d = bq.imreadND(url.toString());
toc;
figure;
imagesc(I2d);
% Elapsed time is 0.141409 seconds.

% read using original imread, fetches the temp file and reads using imread
tic;
I2do = bq.imread(url.toString());
toc;
figure;
imagesc(I2do);
% Elapsed time is 0.074946 seconds.