url = 'http://bisque.ece.ucsb.edu/data_service/file/1974936';
user = '';
pass = '';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% fetching a file from Bisque
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
file = bq.Factory.make(url, [], user, pass);
% fetch a file with the original file name to the current location
fn = file.fetch( [] );



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% fetching a file from Bisque
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
url = 'http://vidi.ece.ucsb.edu:9090';
user = 'XXX';
pass = 'XXX';

%filename = 'gtrain.model';
filename = 'pr-1z.tif';
file = bq.File.store(filename, url, user, pass); 

file.addTag('about', 'this is a file upload from Matlab API');
file.save();