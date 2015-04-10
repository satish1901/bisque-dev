user = '';
pass = '';
image_url = 'http://bisque.ece.ucsb.edu/data_service/00-dcJZKvcHcmKLwQoktSgnfP';

image = bq.Factory.fetch([image_url '?view=deep'], [], user, pass); 

rectangles = image.findNodes('//rectangle');
if length(rectangles)>0,
    roi = rectangles{1}.getVertices();
    im = image.slice(1,1).roi(roi(1, 2), roi(1, 1), roi(2, 2), roi(2, 1)).depth(8, 'f').fetch();
else
    roi = [0,0;0,0];
    im = image.slice(1,1).depth(8, 'f').fetch();
end

imagesc(im);

HSV = rgb2hsv(im);
I = HSV(:,:,1);
I = uint8( (1-I)*255  );

level = graythresh(I);
I = im2bw(I, level);
imagesc(I);

cs = bwboundaries(I, 'noholes');

g = image.addGobject('contours', 'contours');
for j=1:length(cs),
    v = cs{j};
    if length(v) > 20,
        v = v + repmat(roi(1, 1:2), length(v), 1);
        v = reduce_poly(v', 20)';
        name = sprintf('contour-%d', j);
        g.addGobject('polygon', name, v );
    end
end

image.save();

