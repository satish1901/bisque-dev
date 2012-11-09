url = 'http://vidi.ece.ucsb.edu:9090';
user = 'admin';
pass = 'admin';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% creating a new dataset using lower level post
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

input = [];
input = [input sprintf('<dataset name="my-dataset-1">\n')];
input = [input sprintf('<value index="0" type="object">http://vidi.ece.ucsb.edu:9090/data_service/image/20</value>\n')];
input = [input sprintf('<value index="1" type="object">http://vidi.ece.ucsb.edu:9090/data_service/image/17</value>\n')];
input = [input sprintf('<value index="2" type="object">http://vidi.ece.ucsb.edu:9090/data_service/image/11</value>\n')];
input = [input sprintf('</dataset>\n')];

bq.post([url '/data_service/dataset'], input, user, pass);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% creating a new dataset using higher level API
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

dataset = bq.Factory.new('dataset', 'my-dataset-2');

%add values

dataset.save([url '/data_service/dataset'], user, pass);

