function [ErrorMsg] = PlantRecognizer(bqroot, mex_url, image_url, access_token)

ErrorMsg = '';
javaaddpath('./bisque.jar');
import bisque.*

%% PROGRAM
BQ = bisque.BQMatlab;
%BQ.initServers(client_server,client_server);
%BQ.login(user, password);
%mex = BQ.loadMEX(mex_url);
mex = BQ.initialize(bqroot, mex_url, access_token);
try
	% get image from database
	BQ.updateProgress(mex, '0% - fetching image');  
	image = BQ.loadImage([image_url '?view=deep']);
 	im = uint8(BQ.loadImageDataParam(image,'depth=8,d'));
   min(size(im,3),3)
   im=im(:,:,1:min(size(im,3),3)); 
  
   
    gobjects=[];
	for ii = 0:mex.tags.size()-1
	   T = mex.tags.get(ii);
	   if strcmp(T.name,'$gobjects')
		  gobjects = T.gobjects;
	   end
	 end 
     
     
    % we ll get the first rectangle
    rectangle=[];    
    if ~isempty(gobjects) && size(gobjects) > 0,
       % read first and second index
       gob = gobjects.get(0);
       if ~isempty(gob),
         rectangle=[ gobjects.get(0).vertices.get(0).y.doubleValue
                     gobjects.get(0).vertices.get(0).x.doubleValue
                     gobjects.get(0).vertices.get(1).y.doubleValue
                     gobjects.get(0).vertices.get(1).x.doubleValue ];
    end          
    end        
    
    rectangle
    
    if ~isempty(rectangle),    
      % crop image here
      disp('nothing');
      im=im(rectangle(1)+1:rectangle(2)+1, rectangle(3)+1:rectangle(4)+1,:);
    end
    
     size(im)
    
     %% RUN
    BQ.updateProgress(mex, '20% - recognizing');        
    [genus,specie, confidence, commonName ,url] = run_gplant_recognizer(im);
    

    %% SAVE RESULTS
    BQ.updateProgress(mex, '90% - storing results');    

    
    % update image tags
    %nuclei3dTag = BQ.createTag('Detected_Nuclei_Centroids', '');    
    %BQ.addTag(nuclei3dTag, 'date_time', datestr(now, 'yyyy-mm-dd HH:MM:SS') );    
    %BQ.addTag(nuclei3dTag, 'nuclei_count', nuclei_count);
    %BQ.saveTag(image, nuclei3dTag);    

    % update MEX tags
    BQ.addTag(mex, 'Genus', genus);
    BQ.addTag(mex, 'species', specie);
    BQ.addTag(mex, 'common_name', commonName);   
    BQ.addTag(mex, 'wikipeda', url);   
    BQ.addTag(mex, 'confidence', confidence);   

    BQ.finished(mex, '');
catch 
    err = lasterror;
    ErrorMsg = [err.message, 10, 'Stack:', 10];
    for i=1:size(err.stack,1)
      ErrorMsg = [ErrorMsg, '     ', err.stack(i,1).file, ':', num2str(err.stack(i,1).line), ':', err.stack(i,1).name, 10];
    end
    BQ.failed(mex, ErrorMsg);
    return; 
end
