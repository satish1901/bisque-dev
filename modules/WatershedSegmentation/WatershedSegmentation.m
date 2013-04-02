function WatershedSegmentation(mex_url, access_token, image_url, varargin)
    session = bq.Session(mex_url, access_token);
    try
        addpath( genpath('seg_amir') );
        session.update('0% - fetching image');   
        image = session.fetch([image_url '?view=deep']);        
        im = image.slice(1,1).depth(8, 'd').command('deinterlace', '').fetch();

        points = image.findNodes('//gobject/point[@name="Centroid"]');
        anno = zeros(length(points), 2);
        for i=1:length(points),
            v = points{i}.getVertices();
            anno(i,:) = [v(2) v(1)];
        end
        
        c = seg(im, anno);
        
        %% Store results
        session.update('90% - storing results');    
        outputs = session.mex.addTag('outputs');

        imref = outputs.addTag('MyImage', image_url, 'image'); 
        g = imref.addGobject('contours', 'contours');

        for i=1:length(c),        
            v = fliplr(c{i}');
            g.addGobject('polygon', 'contour', v );
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