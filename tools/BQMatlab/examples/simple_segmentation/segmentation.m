user = 'dima';
pass = 'bio2008';
image_url = 'http://bisque.ece.ucsb.edu/data_service/00-dcJZKvcHcmKLwQoktSgnfP';

%http://bisque.ece.ucsb.edu/image_service/00-dcJZKvcHcmKLwQoktSgnfP?slice=,,1,1&transform=rgb2hsv&remap=1&depth=8,d,u&negative&threshold=220,both&format=jpeg

image = bq.Factory.fetch([image_url '?view=deep'], [], user, pass); 

rectangles = image.findNodes('//rectangle');
if length(rectangles)>0,
    roi = rectangles{1}.getVertices();
    % we can fetch the image part of interest and then do all the needed processing
    %im = image.slice(1,1).roi(roi(1, 2), roi(1, 1), roi(2, 2), roi(2, 1)).depth(8, 'f').fetch();
    
    % or request exactly what is needed
    im = image.slice(1,1).roi(roi(1, 2), roi(1, 1), roi(2, 2), roi(2, 1)).command('transform', 'rgb2hsv').command('remap', '1').depth(8, 'f').command('negative', '').fetch();
else
    roi = [0,0;0,0];
    %im = image.slice(1,1).depth(8, 'f').fetch();
    im = image.slice(1,1).command('transform', 'rgb2hsv').command('remap', '1').depth(8, 'f').command('negative', '').fetch();
end

imagesc(im);

% if we fetched RGB image, use Hue, skip otherwise
%HSV = rgb2hsv(im);
%I = HSV(:,:,1);
%I = uint8( (1-I)*255  );

% if we fetched processed image
I = im;

level = graythresh(I);
I = im2bw(I, level);
imagesc(I);

cs = bwboundaries(I, 'noholes');

g = image.addGobject('contours', 'contours');
for j=1:length(cs),
    v = cs{j};
    if length(v) > 1, % filter at 20
        v = v + repmat(roi(1, 1:2), length(v), 1);
        if length(v) > 20,
            v = reduce_poly(v', 20)';
        end
        name = sprintf('contour-%d', j);
        g.addGobject('polygon', name, v );
    end
end

image.save();

