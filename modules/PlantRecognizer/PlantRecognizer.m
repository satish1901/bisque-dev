function PlantRecognizer(mex_url, access_token, image_url)
    try
        session = bq.Session(mex_url, access_token);        

        % fetch provided ROI
        roi = session.mex.findNode('//tag[@name="inputs"]/tag[@name="image_url"]/gobject[@name="roi"]/rectangle');
        if ~isempty(roi),
            rect = roi.getVertices();
            rect = rect(:,1:2);
        else
            rect = [];
        end;
        
        % fetching image, require 3 channel RGB image with max size of 1024
        session.update('0% - fetching image');   
        image = session.load(image_url); 
        if isempty(rect),
            im = image.slice(1,1).depth(8,'d').resize(2000, 2000, 'BC', 'MX').default().fetch();
        else
            im = image.slice(1,1).depth(8,'d');
            im = im.roi(rect(1,2),rect(1,1),rect(2,2),rect(2,1));
            im = im.resize(1024, 1024, 'BC', 'MX').default().fetch();
        end
        
        
        %% RUN
        session.update('20% - recognizing');   
        [genus, specie, confidence, commonName, url] = run_gplant_recognizer(im);

        
        %% SAVE RESULTS
        session.update('90% - storing results');  
        outputs = session.mex.addTag('outputs');
        
        summary = outputs.addTag('summary');
        summary.addTag('Genus', genus);
        summary.addTag('Species', specie);
        summary.addTag('Common_name', commonName);
        summary.addTag('wikipeda', url, 'link');
        summary.addTag('confidence', confidence);        
        
        query = ['Genus:"' genus '" AND species:"' specie '"'];        
        browser = outputs.addTag('similar_images', query, 'browser');

        session.finish();
    catch err
        ErrorMsg = [err.message, 10, 'Stack:', 10];
        for i=1:size(err.stack,1)
            ErrorMsg = [ErrorMsg, '     ', err.stack(i,1).file, ':', num2str(err.stack(i,1).line), ':', err.stack(i,1).name, 10];
        end
        session.fail(ErrorMsg);
    end
end
    
