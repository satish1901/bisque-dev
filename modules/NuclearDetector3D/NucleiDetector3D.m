function [gobject_url nuclei_count ErrorMsg] = ...
         NucleiDetector3D(bqroot, mex_url, image_url, cellSize, thValue, channel_Nuclei, channel_Membrane, access_token)

     
%[gobject_url nuclei_count_url ErrorMsg] =
%NucleiDetector3D('http://bodzio.ece.ucsb.edu:8080','http://bodzio.ece.ucsb.edu:8080/ds/mex/11930','http://bodzio.ece.ucsb.edu:8080/ds/images/4169', '3.4', '0.22', '2', '1', 'admin', 'admin')
%%Declarations
ErrorMsg = '';
gobject_url = '';
nuclei_count = '';
%return
%% 
%kernelSize = str2double(cellSize) * 0.7; % best F measure estimation for old detector, not sure whats with the new one
kernelSize = str2double(cellSize);
thValue = str2double(thValue);
%% Path
javaaddpath('./bisque.jar');
import bisque.*

%% PROGRAM
BQ = bisque.BQMatlab;
%BQ.initServers(client_server,client_server);
%BQ.login(user, password);
%mex = BQ.loadMEX(mex_url);
mex = BQ.initialize(bqroot, mex_url, access_token);
try
    %% Load data
    %% MetaData
    BQ.updateProgress(mex, '0% - fetching image');    
    [image imageNuclei, imageMembrane, resolutionXY, resolutionZ] = BOGetImageData(BQ, image_url, channel_Nuclei, channel_Membrane);    
    
    %% RUN
    %BQ.updateProgress(mex, '10% - starting detection');        
    kernelSize = [kernelSize/resolutionXY kernelSize/resolutionXY kernelSize/resolutionZ];
    nucleiPositions = BONucleiDetector3D(imageNuclei, imageMembrane, kernelSize, thValue, BQ, mex);

    %% SAVE RESULTS
    BQ.updateProgress(mex, '90% - storing results');    
    go = BQ.createGObject('NucleiDetector3D', datestr(now));
    for i=1:length(nucleiPositions(:,2))
        p = BQ.createGObject('point',num2str(i));
        v = [nucleiPositions(i,2)-1 nucleiPositions(i,1)-1 int32(nucleiPositions(i,3)-1)];
        BQ.addVertices(p,v);
        
        BQ.addTag(p, 'probability_intensity', num2str(nucleiPositions(i,5)*100) );
        BQ.addTag(p, 'probability_LoG', num2str(nucleiPositions(i,6)*100) );
        BQ.addGObject(go, p);
    end
    %BQ.saveObjectToXMLFile(go, '/home/boguslaw/result.xml');
    %image = BQ.loadImage(image_url);
    gobject_url = char(BQ.saveGObjectURL(image,go));
    nuclei_count = num2str(length(nucleiPositions));
    
    % update image tags
    nuclei3dTag = BQ.createTag('Detected_Nuclei_Centroids', '');    
    BQ.addTag(nuclei3dTag, 'date_time', datestr(now, 'yyyy-mm-dd HH:MM:SS') );    
    BQ.addTag(nuclei3dTag, 'nuclei_count', nuclei_count);
    BQ.addTag(nuclei3dTag, 'gobject_url', gobject_url);
    BQ.addTag(nuclei3dTag, 'mex_url', mex_url);        
    BQ.saveTag(image, nuclei3dTag);    

    % update MEX tags
    BQ.addTag(mex, 'gobject_url', gobject_url);
    BQ.addTag(mex, 'nuclei_count', nuclei_count );

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
