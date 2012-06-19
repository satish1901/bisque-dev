%function NuclearDetector3D(mex_url, access_token, image_url, nuclear_channel, membrane_channel, nuclear_diameter, ~)
function NuclearDetector3D(mex_url, access_token, image_url, ~, ~, ~, ~)
    session = bq.Session(mex_url, access_token);
    try
        nuclear_channel  = str2num(session.mex.findValue('//tag[@name="inputs"]/tag[@name="nuclear_channel"]'));
        membrane_channel = str2num(session.mex.findValue('//tag[@name="inputs"]/tag[@name="membrane_channel"]', '0'));
        nuclear_diameter = session.mex.findValue('//tag[@name="inputs"]/tag[@name="nuclear_size"]');        
        
        t = session.mex.findNode('//tag[@name="inputs"]/tag[@name="pixel_resolution"]');
        res =  cell2mat(t.getValues('number'));
        %res = [0.439453, 0.439453, 1.0, 1.0]; % image resolution in microns per pixel

        image = session.fetch(image_url);        
        if isfield(image.info, 'pixel_resolution_x') && res(1)<=0,
            res(1) = getfield(image.info, 'pixel_resolution_x');
        end
        if isfield(image.info, 'pixel_resolution_y') && res(2)<=0,
            res(2) = getfield(image.info, 'pixel_resolution_y');
        end    
        if isfield(image.info, 'pixel_resolution_z') && res(3)<=0,
            res(3) = getfield(image.info, 'pixel_resolution_z');
        end    
        if isfield(image.info, 'pixel_resolution_t') && res(4)<=0,
            res(4) = getfield(image.info, 'pixel_resolution_t');
        end
        
        number_t = max(1, image.info.image_num_t);
        np = cell(number_t, 1);
        count = 0;
        for current_t=1:number_t,
            session.update(sprintf('Time %d: 0% - fetching image', current_t));   
            imn = image.slice([],current_t).remap(nuclear_channel).fetch();

            % filter using membraine channel
            if membrane_channel>0,
                imm = image.slice([],current_t).remap(membrane_channel).fetch();
                imn = imdiff(imn, imm);
            end
            
            %% Run
            ns =  (nuclear_diameter/2.0) ./ res;

            t = 0.025:0.025:0.5;
            if isinteger(imn),
               t = t * double(intmax(class(imn)));
            end

            session.update(sprintf('Time %d: 10% - detecting', current_t));
            np{current_t} = BONuclearDetector3D(imn, [], ns, t, session);   
            count = count + length(np{current_t});
        end
        
        %% Store results
        session.update('90% - storing results');    
        outputs = session.mex.addTag('outputs');
        
        summary = outputs.addTag('summary');
        summary.addTag('count', count);

        imref = outputs.addTag('MyImage', image_url, 'image'); 
        g = imref.addGobject('nuclear_centroids', 'nuclear_centroids');

        for j=1:length(np),        
            for i=1:length(np{j}),       
                n = g.addGobject('nucleus', int2str(j*i));        
                v = [np{j}(i,1:3), j];
                p = n.addGobject('point', 'centroid', v );
                p.addTag('confidence', np{j}(i,5)*100, 'number'); 
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