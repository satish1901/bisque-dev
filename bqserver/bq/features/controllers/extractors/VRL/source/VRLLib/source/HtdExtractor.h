////////////////////////////////////////////////////////////////////////////////
//  ==========================================================================
//                       MIR - Mega Image Retrieval
//  ==========================================================================
//
//      File Name: HtdExtractor.h
//    Description: Homogeneous Texture Descriptor based on MPEG7 and Source Code from Lei Wang and Jelena Tesic
//  Related Files: HtdExtractor.cpp, FFT.cpp, FFT.h
//           Date: 12/05/2003
//    Portability: Standard C++
//     References:
//      Author(s): Thiele
//
//  Revision History:
////////////////////////////////////////////////////////////////////////////////

#ifndef HTDEXTRACTOR_H
#define HTDEXTRACTOR_H

//#include <HTDescriptor.h>
//#include <ImageData.h>
#include <stdio.h>
#include <fftw3.h>
#include <math.h>
#include <opencv2/opencv.hpp>

using namespace cv;
using namespace std;

#define PI 3.141592653589793115997963468544185161590576171875
#define Quant_level 255
#define ERROR_TOLERANCE     1e-4
#define WINDOW_SIZE			9
#define NR_OF_LHTD_CLUSTERS	4

typedef struct {
		unsigned char mean2[5][6];
		unsigned char dev2[5][6];
		unsigned char m_dc;
		unsigned char m_std;
		int image_height;	
		int image_width;
		char fname[1000];
		int frameNo;
		int h_block_coor;
		int v_block_coor;
		int pbc[5];
		int cluster;
		int EHD[80];
		int cluster3;
		int cluster2;
}sFeatureD;

typedef struct {
		double mean2[5][6];
		double dev2[5][6];
		double root[5][6];
		double m_dc;
		double m_std;
}sHTD;


class HtdExtractor
{

public:
        HtdExtractor(int sizeX, int sizeY);
        ~HtdExtractor();
        Mat extract(Mat Image, int sizeX, int sizeY); 
		//HTDescriptor* extractLocal(const ImageData& rImage, int* lhtdPercentage);
        int nx;
		int ny;       
        
private:
		//int* clusterVectors(float** imageVector, float** centroids, int nrOfClusters, int& sampleCount);
		//sHTD* getLocalTexture(unsigned char* image, int* lhtdPercentage);
		//double getRand();
		//int* k_means(float **data, int n, int m, int k, double t, float **centroids);
		//void getLocalStats(double* filteredImage , int windowSize, float** imageVector,int s, int n);
        void Get_Gabors(int row,int col);
		//sHTD* go(unsigned char *image, int sizeX, int sizeY);
		sHTD* FeatureExtraction(unsigned char *image, int width, int height, int w_disp, int h_disp, int patch_width, int patch_height);
		void GaborNew(double** gabor ,int row, int col, int s, int n, double Ul, double Uh, int scale, int orientation,int flag,int verbose,int mode);
        double ** Gabor(int row,int col, int s, int n, int scale, int orientation);
        unsigned char * get_patch(unsigned char *inimage, int im_width, int im_height, int w_disp, int h_disp, int patch_width, int patch_height);
        int mod(int x,int y);

		int scale, orientation;

		double***** gabors;


};
#endif 
