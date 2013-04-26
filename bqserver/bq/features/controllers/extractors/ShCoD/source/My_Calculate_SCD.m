
function My_Calculate_SCD(filename,filenameoutput,samples)
    %im = imread(filename);
    %im=rgb2gray(im);

    %contour has to be imput
    st=open(filename);
    contour=st.contour;
    %sample the resample contours
    y=double(contour(:,1));
    x=double(contour(:,2));
    y_rep=repmat(y',[1,3]);
    x_rep=repmat(x',[1,3]);
    p=samples; %sample length
    y_rep=resample(y_rep,p-1,length(y));
    x_rep=resample(x_rep,p-1,length(x));
    start=length(y_rep)/3;
    ends=length(y_rep)-start;

    y=y_rep(start:ends)';
    x=x_rep(start:ends)';

    nsamp = length(y); 
    r_inner=1/8;
    r_outer=2;
    nbins_theta=12;
    nbins_r=5; 
    mean_dist=[];
    Tsamp = zeros(1,nsamp);
    Bsamp = [y,x]';
    out_vec=zeros(1,nsamp);
    [BH,mean_dist]=sc_compute(Bsamp,Tsamp,mean_dist,nbins_theta,nbins_r,r_inner,r_outer,out_vec);
    save(filenameoutput,'BH','Bsamp');
end