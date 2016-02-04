url = 'http://BISQUE_HOST:9090';
user = 'username';
pass = 'password';



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% creating a new dataset using higher level API
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

dataset = bq.Factory.new('dataset', 'my-dataset-2');

%add values
dataset.setValues(files);

dataset.save([url '/data_service/dataset'], user, pass);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% rename some tags within the dataset
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

url = 'http://host/data_service/dataset/635?view=deep';
dataset = bq.Factory.fetch(url, [], user, pass);
images = dataset.getValues('object');

for i=1:size(images,2),
    im = bq.Factory.fetch([images{i} '?view=deep'], [], user, pass);
    t = im.tag('height');
    dirty = 0;
    if ~isempty(t),
        t.setAttribute('name', 'Height');
        dirty = 1;        
    end

    t = im.tag('Height ');
    if ~isempty(t),
        t.setAttribute('name', 'Height');
        dirty = 1;                
    end
    
    if dirty == 1,        
        im.save();
    end
end
