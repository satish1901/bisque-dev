
% initing session
s = bq.Session('http://vidi.ece.ucsb.edu:9090/data_service/mex/981', '981');

% while running
s.update('RUNNING');

% fetch input tags as a map
inputs = s.mex.getNameValueMap('//tag[@name="inputs"]/tag');
inm = [inputs.keys; inputs.values]';

% fetch some input tags as a map with default values
tags = { 'image_url', 'str', []; 'threshold', 'int', 0; };
mytags = s.mex.findNameValueMap(tags, '//tag[@name="inputs"]/tag[@name=''%s'']');
mym = [mytags.keys; mytags.values]';

% fetch some input tag as a bq.Node
imageurl = s.mex.findValue('//tag[@name="inputs"]/tag[@name="image_url"]');
% fetch first plane of the first channel
image = s.fetch(imageurl);
im = image.slice(1,1).remap(1).fetch();
imagesc(im);


% fetch some input tags as a cell of bq.Node
ts = s.mex.findNodes('//tag[@name="inputs"]/tag');
value = ts{1}.getAttribute('value');

% navigate in tags by bq.Node
tag = s.mex.tag('inputs');
tag = s.mex.tag('inputs').tag('image_url');
imageurl = tag.getAttribute('value');

s.update('10%');


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% creating results
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

outputs = s.mex.addTag('outputs');
outputs.addTag('my_number_objects', 123);
outputs.addTag('some_float', 456.78);

g = outputs.addGobject('my_gobs2', 'my_gobs2');

g.addGobject('point', '1', [1,2,3] );
g.addGobject('point', '2', [4,5,6] );
g.addGobject('point', '3', [7,8,9] );


p = [1,2,3;4,5,6;7,8,9];
g.addGobject('polyline', 'poly-in-z', p );

p = [1,2,-1,3;4,5,-1,6;7,8,-1,9];
g.addGobject('polyline', 'poly-in-t', p );


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% upload files and images
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

f = s.storeFile('my_file.bin');

image = zeros(128, 128, 'double');
args = struct('filename', 'my_2d_double_image.ome.tif');
im = s.storeimage(image, args);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% finish
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

s.finish();

