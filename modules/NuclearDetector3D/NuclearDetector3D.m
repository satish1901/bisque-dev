function NuclearDetector3D(mex_url, access_token, image_url, nuclear_channel, nuclear_diameter, ~)
    session = bq.Session(mex_url, access_token);
    try
        %% Load data
        info = session.iminfo(image_url);
        url = bq.Url(info.pixles_url);

        nuclear_channel  = str2num(nuclear_channel);
        nuclear_diameter = str2num(nuclear_diameter);
        
        t = session.mex.findNode('//tag[@name="inputs"]/tag[@name="pixel_resolution"]');
        res =  cell2mat(t.getValues('number'));
        %res = [0.439453, 0.439453, 1.0, 1.0]; % image resolution in microns per pixel

        if isfield(info, 'pixel_resolution_x'),
            res(1) = getfield(info, 'pixel_resolution_x');
        end
        if isfield(info, 'pixel_resolution_y'),
            res(2) = getfield(info, 'pixel_resolution_y');
        end    
        if isfield(info, 'pixel_resolution_z'),
            res(3) = getfield(info, 'pixel_resolution_z');
        end    
        if isfield(info, 'pixel_resolution_t'),
            res(4) = getfield(info, 'pixel_resolution_t');
        end

        
        number_t = max(1, info.image_num_t);
        np = cell(number_t, 1);
        for current_t=1:number_t,
            session.update(sprintf('Time %d: 0% - fetching image', current_t));        
            url.pushQuery('slice', sprintf(',,,%d', current_t)); % fetch first T slice
            url.pushQuery('remap', int2str(nuclear_channel));
            imn = session.imread(url.toString());        

            %% Run
            ns =  (nuclear_diameter/2.0) ./ res;

            t = 0.025:0.025:0.5;
            if isinteger(imn),
               t = t * double(intmax(class(imn)));
            end

            session.update(sprintf('Time %d: 10% - detecting', current_t));
            np{current_t} = BONuclearDetector3D(imn, [], ns, t, session);    
        end
        
        %% Store results
        session.update('90% - storing results');    
        outputs = session.mex.addTag('outputs');
        
        summary = outputs.addTag('summary');
        summary.addTag('count', length(np));

        imref = outputs.addTag('MyImage', image_url, 'image'); 
        g = imref.addGobject('nuclear_centroids', 'nuclear_centroids');

        for j=1:length(np),        
            for i=1:length(np{j}),       
                p = g.addGobject('nucleus', int2str(j*i));        
                v = [np{j}(i,2)-1, np{j}(i,1)-1, np{j}(i,3)-1, j-1.0];
                p.addGobject('point', 'centroid', v );
                p.addTag('confidence', np{j}(i,5), 'number'); 
            end
        end
        
        session.finish();
    catch err
        ErrorMsg = [err.message, 10, 'Stack:', 10];
        for i=1:size(err.stack,1)
            ErrorMsg = [ErrorMsg, '     ', err.stack(i,1).file, ':', num2str(err.stack(i,1).line), ':', err.stack(i,1).name, 10];
        end
        session.fail(ErrorMsg);
    end
end