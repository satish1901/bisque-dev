function imd = imdiff(im1, im2)
% Normalized image difference
%
%

    %% normalize diff image
    d_std = std(double(im1(:))) / std(double(im2(:)));
    im2 = im2 * d_std;
    
    d_avg = mean(im1(:)) - mean(im2(:));
    im2 = im2 + d_avg;
       
    imd = im1 - im2;
end    
