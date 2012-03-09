
% direct reading of a public image by its image service URL
%3D image 512x512x13Zx2C: http://bisque.ece.ucsb.edu/data_service/image/161855
imurl = 'http://bisque.ece.ucsb.edu/data_service/image/161855';
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