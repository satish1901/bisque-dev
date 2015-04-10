user = 'dima';
pass = 'bio2008';
image_url = 'http://bisque.ece.ucsb.edu/data_service/00-dcJZKvcHcmKLwQoktSgnfP';

image = bq.Factory.fetch([image_url '?view=deep'], [], user, pass); 

polygons = image.findNodes('//polygon');
areas = zeros(length(polygons),1);
for i=1:length(polygons),
    poly = polygons{i}.getVertices();
    a = polyarea(poly(:,1), poly(:,2));
    areas(i) = a;
end

idx = kmeans(areas, 3);

colors = cell(3,1);
colors{1} = '#FF0000';
colors{2} = '#FFFF00';
colors{3} = '#0000FF';

for i=1:length(polygons),
    polygons{i}.addTag('area', areas(i) );
    polygons{i}.addTag('class', num2str(idx(i)) );
    polygons{i}.addTag('color', colors{idx(i)} );
end

image.save();

