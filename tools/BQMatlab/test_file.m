url = 'http://bisque.ece.ucsb.edu/data_service/file/1974936';
user = '';
pass = '';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% using bq.File
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
file = bq.Factory.make(url, [], user, pass);
fn = file.fetch( [] );


