function c = seg(I,anno)
    addpath( genpath('utils') );

% matlabpool;
    F = makeRFSfilters;
    
    FR = zeros(size(I,1), size(I,2), 6);
    FILTlist = 13:18 ;
    Is = single(I);

    parfor ch = 1 : 3
        Is(:,:,ch) = imfilter(single(I(:,:,ch)), fspecial('gauss', [49 49], 5 ), 'same' );
    end


    parfor iter = 1:numel(FILTlist)
        temp = imfilter( Is, F(:,:,FILTlist(iter)), 'same' );
        %tempG = imfilter( Is(:,:,2), F(:,:,FILTlist(iter)), 'same' );
        %tempB = imfilter( Is(:,:,3), F(:,:,FILTlist(iter)), 'same' );
        %FR(:,:,iter) = sqrt(tempR.^2 + tempG.^2 + tempB.^2);
        FR(:,:,iter) = sqrt(temp(:,:,1).^2 + temp(:,:,2).^2 + temp(:,:,3).^2);
    end

    FRmax1 = max(abs(FR(:,:,1:6)),[],3);
    FRthr1 = adaptivethresh( FRmax1 );
    
%     figure(5);imshow(I); hold on;
    for iter = 1 : size(anno,1)
%         figure(5);plot(anno(iter,1),anno(iter,2),'rs','markersize',16)
        FRthr1(anno(iter,2)-3:anno(iter,2)+3,anno(iter,1)-3:anno(iter,1)+3) = -inf;
    end

    ww = watershed(FRthr1);

    % figure;imagesc(ww)

    %%
    for iter = 1 : size(anno,1)
        id = ww(anno(iter,2)-10:anno(iter,2)+10,anno(iter,1)-10:anno(iter,1)+10);
        id = double(id(:));
        id(id==0)=[];
        id(id==1)=[];
        id(id==2)=[];
        id = unique(id);
        temp = false(size(ww));
        for iter2 = 1:numel(id)
            temp = temp | ww==id(iter2);
        end
        
        s = sum(temp(:));
        if s < 50000 && s > 0
            %figure(5); contour(temp);
            c{iter} = contourc(double(temp), [1 1]);
            c{iter}(:,1:2) = [];  
        else
%             figure(5);plot(anno(iter,1),anno(iter,2),'gs','markersize',32)
            temp2 = false(size(ww));
            temp2(anno(iter,2),anno(iter,1)) = true;
            temp2 = imdilate(temp2, strel('disk',32));
            c{iter} = contourc(double(temp2), [1 1]);
            c{iter}(:,1:2) = [];
        end
    end


end