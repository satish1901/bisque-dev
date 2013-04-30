////////////////////////////////////////////////////////////////////////////////
//  ==========================================================================
//                       MIR - Mega Image Retrieval
//  ==========================================================================
//
//      File Name: HtdExtractor.cpp
//    Description: Homogeneous Texture Descriptor based on MPEG7 and Source Code from Lei Wang and Jelena Tesic
//  Related Files: HtdExtractor.h, FFT.cpp, FFT.h
//           Date: 12/17/2003
//    Portability: Standard C++
//     References:
//      Author(s): Thiele, Chris
//
//  Revision History:1.1 / uses Gabormx(300,300) and c_image of the same size.
//                 (fills c_image with m_dc of original image and copies the original image) 
//		uses mean2 and dev2 in frequency domain
//
//                   1.2 Added openCV Mat type and removed htddescritpor data type
////////////////////////////////////////////////////////////////////////////////

#include "HtdExtractor.h"
#include <fftw3.h>
#include <math.h>
#include <stdlib.h>
#include <float.h>
#include <opencv2/opencv.hpp>

using namespace cv;
using namespace std;

#define MAX_SAMPLES	2000
HtdExtractor::HtdExtractor(int sizeX, int sizeY)
{
   scale=4;
   orientation=6;
   nx=sizeX;
   ny=sizeY;
   int N=nx*ny;

   gabors= new double****[scale];
   for (int i =  0; i < scale; ++i )
   {
		gabors[i] = new double***[orientation];
		for (int j =  0; j < orientation; ++j )
		{
         	gabors[i][j] = new double**[nx];
			for(int k=0;k<nx;++k)
			{
				gabors[i][j][k] = new double*[ny];
				for(int l=0;l<ny;++l)
				{
					gabors[i][j][k][l] = new double[2];
				}
			}
		}
	}

    fftw_complex *fftwIn, *fftwOut;

    fftwIn = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * N);
    fftwOut = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * N);
    fftw_plan planGabor;

    planGabor = fftw_plan_dft_2d(nx,ny, fftwIn, fftwOut, FFTW_FORWARD, FFTW_ESTIMATE);

    double **sGabor = new double* [sizeof(double*) * nx];
    sGabor[0] = new double [sizeof(double) * N];
    for (int i = 1; i < nx; i++)
        sGabor[i] = sGabor[0] + i * nx;

	for (int s=0;s<scale;s++)
    	for (int n=0;n<orientation;n++)
		{
			GaborNew(sGabor, nx, ny, s, n, 0.05, .5,  scale, orientation ,0 , 0, 1);

            for (int i=0;i<nx;i++)
                for (int j=0;j<ny;j++)
                    fftwIn[i*ny+j][0]=sGabor[i][j];

            GaborNew(sGabor, nx, ny, s, n, 0.05, .5,  scale, orientation ,0 , 0, -1);

            for (int i=0;i<nx;i++)
                for (int j=0;j<ny;j++)
                    fftwIn[i*ny+j][1]=sGabor[i][j];


	    fftw_execute(planGabor);

	    for(int i=0;i<nx;i++)
		for(int j=0;j<ny;j++)
		{
		   gabors[s][n][i][j][0]=	fftwOut[i*ny+j][0];
		   gabors[s][n][i][j][1]=	fftwOut[i*ny+j][1];
		}
	    }

	//fftw_destroy_plan(planGabor);
    fftw_free(fftwIn); fftw_free(fftwOut);

	delete[] sGabor;


}

HtdExtractor::~HtdExtractor()
{
	for (int i =  0; i < scale; ++i )
	{
        for (int j =  0; j < orientation; ++j )
        {
            for(int k=0;k<nx;++k)
            {
                for(int l=0;l<ny;++l)
                {
                    delete[] gabors[i][j][k][l];
                }
                delete[] gabors[i][j][k];
            }
            delete[] gabors[i][j];
        }
        delete[] gabors[i];
    }
    delete[] gabors;

}

//---------------------------------------------------------------------------------------------------------
Mat HtdExtractor::extract(Mat Image , int sizeX, int sizeY) {

	//intializing
	Mat HTD( Size(1,2*orientation*scale) , CV_64F );
	
	long int N=sizeX*sizeY;
	double mean=0, std=0;

	fftw_complex *outImage, *fftwIn;
	fftw_complex *imageIn;
	fftw_complex *tmpresult;
	double *result;

	imageIn = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * N);
	tmpresult = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * N);
	result = (double*)fftw_malloc(sizeof(double) * N);
	fftwIn = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * N);
	outImage = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * N);

	fftw_plan planfImage;
	fftw_plan planb;

	planfImage = fftw_plan_dft_2d(sizeX, sizeY, imageIn , outImage,FFTW_FORWARD, FFTW_ESTIMATE );
	planb = fftw_plan_dft_2d(sizeX, sizeY, fftwIn, tmpresult,FFTW_BACKWARD, FFTW_ESTIMATE);
	
	//image fft
	for (int i=0;i<sizeX;i++) {
		for (int j=0;j<sizeY;j++) {

			imageIn[i*sizeY+j][0] = (double) Image.at<uchar>(j,i); //importing image matrix
			imageIn[i*sizeY+j][1] = 0;

		}
	}
	

  	fftw_execute(planfImage);
	
	for(int s=0; s<scale; s++)
		for(int n=0; n<orientation; n++) {

		    mean=0;
		    std=0;

			//Multiply image and gabor in freq domain
			for(int i=0;i<sizeX;i++)
				for(int j=0;j<sizeY;j++)
				{	// real			 =	      a			  *			c			- 		  b			  *		d
					fftwIn[j+sizeY*i][0]=gabors[s][n][i][j][0] * outImage[j+sizeY*i][0] - gabors[s][n][i][j][1] * outImage[j+sizeY*i][1];
					// imag			 =		  a			  *			d			+		  b			  *		c
					fftwIn[j+sizeY*i][1]=gabors[s][n][i][j][0] * outImage[j+sizeY*i][1] + gabors[s][n][i][j][1] * outImage[j+sizeY*i][0];
				}
			//reverse fft result of multiplication of gabor and image
			fftw_execute(planb);

			//calculate mean
			for(int i=0;i<sizeX;i++)
                for(int j=0;j<sizeY;j++)
						result[i*sizeY+j]=sqrt((tmpresult[i*sizeY+j][0]*tmpresult[i*sizeY+j][0])+(tmpresult[i*sizeY+j][1]*tmpresult[i*sizeY+j][1]))/N;

		    for (int i=0;i<sizeX;i++)
		        for (int j=0;j<sizeY;j++)
            		mean+=(double)result[i*sizeY+j];
					
			mean=(mean/(double)N);
    
			//calculate standard deviation
    		for (int i=0;i<sizeX;i++)
        		for (int j=0;j<sizeY;j++)
            		std+=(result[i*sizeY+j]-mean)*(result[i*sizeY+j]-mean);

			std=sqrt(std/(double)N);///stdd[s][n][1];

			//store values in Mat datatype [mean, std]
			HTD.at<double>(s*orientation+n,0) = mean;  //log(1+mean);//stdd[s][n][0];//log(1+mean);
			HTD.at<double>(s*orientation+n+orientation*scale,0) = std;  //log(1+std);///stdd[s][n][1];

		}

	//freeing memory
	fftw_destroy_plan(planfImage);
	fftw_destroy_plan(planb);
	fftw_free(fftwIn); fftw_free(outImage);fftw_free(imageIn);
	fftw_free(result);
	fftw_free(tmpresult);

	return HTD;

}

//-----------------------------------------------------------------------------

void HtdExtractor::GaborNew(double** gabor, int row, int col, int s, int n, double Ul, double Uh, int scale, int orientation, int flag, int verbose, int mode) {

	for(int i=0;i<row;i++)
		for(int j=0;j<col;j++)
			gabor[i][j]=0;

	row=81;
	col=81;

	
    double base, a, u0, X, Y, G, t1, t2, m,  coef, sigmaX, sigmaY, sigmaU, sigmaV, z;
    int x, y, side;

    base = Uh/Ul;

    a = pow(base, 1.0/(double)(scale-1));
   
    u0 = Uh;
  
    sigmaU = ((a-1)*Uh)/((a+1)*sqrt(2*log(double(2))));
    z = -2*log(double(2))*sigmaU*sigmaU/Uh;
    sigmaV = tan(PI/(2*orientation))*(Uh+z)/sqrt(2*log(double(2))-z*z/(sigmaU*sigmaU));

    sigmaY = 1/(2*PI*sigmaV);
    sigmaX = 1/(2*PI*sigmaU);
    coef = 1/(2*PI*sigmaX*sigmaY);

    if (verbose && s==0 && n==0) {
        printf("Using filter function `Gabor'\n");
        printf("a = %f, sigmaX = %f, sigmaY = %f, W = %f\n", a, sigmaX, sigmaY, u0);
    }

    side = (int) (row-1)/2;
	
    t1 = cos((double) PI/orientation*n);
    t2 = sin((double) PI/orientation*n);

    for (x=0;x<2*side+1;x++) {
        for (y=0;y<2*side+1;y++) {
            X = pow(a,-s) * ((double) (x-side)*t1+ (double) (y-side)*t2);
            Y = pow(a,-s) * ((double) -(x-side)*t2+ (double) (y-side)*t1);
            G = coef * pow(a,-s) * exp(-0.5 * ( (X*X)/(sigmaX*sigmaX) + (Y*Y)/(sigmaY*sigmaY) ) );
			
            // exchange x,y indices to keep the same axes as the image (rows x columns)
            if (mode>=0) gabor[y][x] = G*cos(2.0*PI*u0*X);   // realonly or complex
            if (mode==-1) gabor[y][x] = G*sin(2.0*PI*u0*X);  // imag only
            if (mode==0) gabor[y][x] = G*sin(2.0*PI*u0*X);   // complex
        }
    }

    /* if flag == 1, then remove the DC from the real part of Gabor */

    if (flag==1 && mode>=0) {
        m = 0;
        for (x=0;x<2*side+1;x++)
            for (y=0;y<2*side+1;y++)
                m += gabor[x][y];

        m /= pow((double) 2.0*side+1, 2.0);

        for (x=0;x<2*side+1;x++)
            for (y=0;y<2*side+1;y++)
                gabor[x][y] -= m;
    }
}

