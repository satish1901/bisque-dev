%%  BONucleiDetector3D - 3D nuclei detector
%   
%   REFERENCE:
%       B. Obara and D. Fedorov and C.D. Banna and B.S. Manjunath,
%       Automatic system for detection and validation of cell nuclei in 
%       3D CLS microscopy imagery, SOON :)
%
%   INPUT:
%       imn     - nuclei channel
%       imm     - membrane channel
%       ns      - half of nuclear size[pixels] = 
%                   ns[microns]*[1/resolutionx 1/resolutiony 1/resolutionz]
%       t       - range of lowest intensity bound
%
%   OUTPUT:
%       np      - detected nuclei positions, is a matrix where
%                   np(:,1) -> Y coordinate (starting at 1)
%                   np(:,2) -> X coordinate (starting at 1)
%                   np(:,3) -> Z coordinate (starting at 1)
%                   np(:,4) -> point IDs
%                   np(:,5) -> confidence estimate 
%                   np(:,6) -> average LoG intensity of nuclei volumes
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 LoG + revision
%       0.3 - 24/09/2010 Speed up
%       0.4 - 2011-06-03 by Dmitry: major rewrite with ~8X speedup, 
%                                   support for image types other than
%                                   double
%%

function np = BONuclearDetector3D(imn, ns, t, session)

    %% imdilate gets impossibly slow for large structuring elements
    % we'll aproximate large kernels by using smaller interpolated data
    max_ns = [25, 25, 11];
    scale = ns ./ max_ns;
    scale(scale<1) = 1;
    if max(scale)>1,
        newsz = round(size(imn) ./ scale);
        imn = imresize3d(imn, newsz, 'cubic');
        ns = ns ./ scale;
    else
        scale = [1,1,1];
    end    

    %% Convolve with LoG
    if exist('session', 'var'), session.update('10% - Blob detection'); end
    imlog = BOBlobDetector3D(imn, ns);

    %% Finding seeds
    if exist('session', 'var'), session.update('40% - Seed search'); end
    t = sort(t);
    np = BOSeedSearch3D(imlog, ns, t);
    
    %% removing unchanging point sets towards low thresholds
    dnp = zeros(size(np,1),1);
    for i=1:size(np,1)-1,
        dnp(i) = size(np{i},1) / size(np{i+1},1);
    end
    [~,idx] = max(dnp);
    np = np(idx:end);
    
    %% Filtering
    if exist('session', 'var'), session.update('70% - Filtering'); end
    for i=1:length(np),
        dt = GetCentroidDescriptors3D(imn,imlog,np{i},ns);
        np{i} = Filter3DPointsByDescriptor(np{i},dt,ns*1.1);
    end

    %% Merging    
    if exist('session', 'var'), session.update('90% - Merging'); end
    np = MergeThresholds(np);
    dt = GetCentroidDescriptors3D(imn, imlog, np, ns, 1);

    %% scaling points to original size, for large kernel case  
    np(:,1) = np(:,1) .* scale(1);
    np(:,2) = np(:,2) .* scale(2);
    np(:,3) = np(:,3) .* scale(3);
    
    %% Producing resuls     
    sz = size(np,1);
    counts = np(:,4);
    sums = zeros(sz,1);
    img_mean = zeros(sz,1);
    img_mad = zeros(sz,1);
    log_mean = zeros(sz,1);
    for i=1:sz,   
        sums(i) = dt{i}.sum;
        img_mean(i) = dt{i}.mean;
        img_mad(i) = dt{i}.mad;    
        log_mean(i) = dt{i}.log_mean;    
    end  

    sums_orig = sums;
    sums = ( sums - min(sums) ) / ( max(sums) - min(sums) );
    img_mean = ( img_mean - min(img_mean) ) / ( max(img_mean) - min(img_mean) );
    img_mad = ( img_mad - min(img_mad) ) / ( max(img_mad) - min(img_mad) );
    log_mean = ( log_mean - min(log_mean) ) / ( max(log_mean) - min(log_mean) );
    counts = ( counts - min(counts) ) / ( max(counts) - min(counts) );

    feature = (6*counts + 4*img_mean)/ 10;
    %feature = (6*counts + 4*img_mad)/ 10;
    feature = ( feature - min(feature) ) / ( max(feature) - min(feature) );


    np(:,5) = feature;
    np(:,6) = counts;
    np(:,7) = sums;
    np(:,8) = img_mean;
    np(:,9) = log_mean;
    np(:,10) = sums_orig;

    np = sortrows(np, 5);

    % figure;
    % hold on
    % plot(np(:,6), 'Color', 'red', 'LineWidth', 2, 'DisplayName', 'counts' );
    % plot(np(:,7), 'Color', 'green', 'LineWidth', 2, 'DisplayName', 'sums');
    % plot(np(:,8), 'Color', 'cyan', 'LineWidth', 2, 'DisplayName', 'img_mean');
    % plot(np(:,9), 'Color', 'yellow', 'LineWidth', 2, 'DisplayName', 'log_mean');
    % plot(np(:,5), 'Color', 'blue', 'LineWidth', 2, 'DisplayName', 'feature');
    % hold off

end
