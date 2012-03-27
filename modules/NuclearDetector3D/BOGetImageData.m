function [image imageNuclei imageMembrane resolutionXY resolutionZ] = ...
            BOGetImageData(image_url, channel_Nuclei, channel_Membrane)

    % this requires: javaaddpath('./bisque.jar'); import bisque.*
    BQ = bisque.BQMatlab;
        
    imageNuclei = [];
    imageMembrane = [];
    resolutionXY = 1.0;    
    resolutionZ = 1.0;

    %% MetaData
    image = BQ.loadImage( [image_url '?view=full'] );

    t = image.findTag('pixel_resolution_x_y');
    if ~isempty(t),
      resolutionXY = str2double(char(t.getValue()));
    end

    t = image.findTag('pixel_resolution_z');
    if ~isempty(t),
      resolutionZ = str2double(char(t.getValue())); 
    end

    %% Data
    channel_Nuclei = str2double(channel_Nuclei);
    im = BQ.loadImageDataCH(image, channel_Nuclei);
    %imageNuclei = im(:,:,channel_Nuclei,:);
    imageNuclei = im;
    %imageNuclei = squeeze(imageNuclei);
    imageNuclei = double(imageNuclei)/double(max(imageNuclei(:)));
    if(isempty(imageNuclei)); error(char(BQError.getLastError())); end

    if (~strcmp(channel_Membrane,'None'))
        channel_Membrane = str2double(channel_Membrane);
        im = BQ.loadImageDataCH(image, channel_Membrane);
        %imageMembrane = im(:,:,channel_Membrane,:);
        imageMembrane = im;
        %imageMembrane = squeeze(imageMembrane);
        imageMembrane = double(imageMembrane)/double(max(imageMembrane(:)));
        if(isempty(imageMembrane)); error(char(BQError.getLastError())); end
    end

end
