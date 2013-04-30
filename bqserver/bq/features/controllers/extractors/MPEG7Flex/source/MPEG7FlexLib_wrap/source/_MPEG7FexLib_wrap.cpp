/* _MPEG7fexLib_wrap.cpp : 
//		Wrap of the MPEG7FexLib feature library
//
Inlcudes
	Color
		computeCSD
		computeSCD
		computeCLD
		computeDCD

	Texture
		computeHTD
		computeEHD

	Shape
		computeRSD

Need to ADD

		computeCShD

*/

#include <iostream>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include "Feature.h"

using namespace cv;
using namespace std;

#if defined(WIN32) || defined(_WIN32) 
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

extern "C"{

DLLEXPORT void computeCSD( int *im, int descSize, int rows, int columns, double *results) {
	 //size: (16, 32, 64, 128, 256)
	
	Mat Image(columns, rows , CV_16UC3 );
    int i, j, k;
	int channel = 3;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
			for (k=0; k<channel; k++)
				{
					Image.at<Vec3b>(i,j)[k] = (unsigned char)(im[i*rows*channel+channel*j+k]); //im[i,j,k]; (double)(im[i*rows + j]);
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setImage(Image);

	XM::ColorStructureDescriptor* csd = Feature::getColorStructureD(frame, descSize);

	// return to python as a numpy
	for(unsigned int i = 0; i < csd->GetSize(); i++)
		results[i] = (int)csd->GetElement(i);


	// release descriptor
	delete csd;
	delete frame;
}

DLLEXPORT void computeSCD( int *im, int descSize, int rows, int columns, double *results) {
	 //size: (16, 32, 64, 128, 256)
	
	Mat Image(columns, rows , CV_16UC3 );
    int i, j, k;
	int channel = 3;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
			for (k=0; k<channel; k++)
				{
					Image.at<Vec3b>(i,j)[k] = (unsigned char)(im[i*rows*channel+channel*j+k]); //im[i,j,k]; (double)(im[i*rows + j]);
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setImage(Image);

	bool maskFlag = true;
	XM::ScalableColorDescriptor* scd = Feature::getScalableColorD( frame, maskFlag, descSize );

	// return to python as a numpy
	for(unsigned int i = 0; i < scd->GetNumberOfCoefficients(); i++)
		results[i] = (int)scd->GetCoefficient(i);


	// release descriptor
	delete scd;
	delete frame;
}

DLLEXPORT void computeCLD( int *im, int numYCoef, int numCCoef, int rows, int columns, double *results) {
	 //size: (16, 32, 64, 128, 256)
	
	Mat Image(columns, rows , CV_16UC3 );
    int i, j, k;
	int channel = 3;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
			for (k=0; k<channel; k++)
				{
					Image.at<Vec3b>(i,j)[k] = (unsigned char)(im[i*rows*channel+channel*j+k]); 
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setImage(Image);

	XM::ColorLayoutDescriptor* cld = Feature::getColorLayoutD( frame, numYCoef, numCCoef );

	// number of coefficients
	int numberOfYCoeff = cld->GetNumberOfYCoeff();
	int numberOfCCoeff = cld->GetNumberOfCCoeff();


	// values
	int *y_coeff, *cb_coeff, *cr_coeff;
	y_coeff = cld->GetYCoeff();
	cb_coeff = cld->GetCbCoeff();
	cr_coeff = cld->GetCrCoeff();

	// return to python as a numpy array
	j = 0;
	// Y coeff (DC and AC)
	for ( i = 0; i < numberOfYCoeff; i++ )
	{
		results[j] = (int) y_coeff[i];
		j+=1;
	}
	//Cb coeff  (DC and AC)
	for ( i = 0; i < numberOfCCoeff; i++ )
	{
		results[j] = (int) cb_coeff[i];
		j+=1;
	}

	//Cr coeff  (DC and AC)
	for ( i = 0; i < numberOfCCoeff; i++ )
	{
		results[j] = (int) cr_coeff[i];
		j+=1;
	}
	// release pointers
	delete cld;
	delete frame;
}


DLLEXPORT void* computeDCD( int *im, bool normalize, bool variance, bool spatial, int bin1, int bin2, int bin3, int rows, int columns, int *ndc) {
	 //size: (16, 32, 64, 128, 256)
	
	Mat Image(columns, rows , CV_16UC3 );
    int i, j, k;
	int channel = 3;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
			for (k=0; k<channel; k++)
				{
					Image.at<Vec3b>(i,j)[k] = (unsigned char)(im[i*rows*channel+channel*j+k]); //im[i,j,k]; (double)(im[i*rows + j]);
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setImage(Image);

	XM::DominantColorDescriptor* dcd = Feature::getDominantColorD( frame, normalize, variance, spatial, bin1, bin2, bin3 );

	// number of dominant colors
	ndc[0] = dcd->GetDominantColorsNumber();

	// release descriptor
	delete frame;
	return dcd;

}
//DCD has varying outputs so first the length of the feature has to be returned before returing the feature
DLLEXPORT void returnDCD(XM::DominantColorDescriptor* dcd , bool variance, bool spatial, double *results, int *output_spatial){
	// dominant colors: percentage(1) centroid value (3) color variance (3)


	// spatial coherency need to read output
	if(spatial)
        //std::cout << dcd->GetSpatialCoherency();
		output_spatial[0] = dcd->GetSpatialCoherency();

	int ndc = dcd->GetDominantColorsNumber();

	XM::DOMCOL* domcol = dcd->GetDominantColors();
	int j = 0;

	for( int i = 0; i < ndc; i++ ) {
		results[j] = (float) domcol[i].m_Percentage;
		j+=1;
        results[j] = (float) domcol[i].m_ColorValue[0];
		j+=1;
        results[j] = (float) domcol[i].m_ColorValue[1];
		j+=1;
        results[j] = (float) domcol[i].m_ColorValue[2];
		j+=1;

        if(variance) {
			results[j] = (float) domcol[i].m_ColorVariance[0];
			j+=1;
			results[j] = (float) domcol[i].m_ColorVariance[1];
			j+=1;
			results[j] = (float) domcol[i].m_ColorVariance[2];
			j+=1;
		}
	}
}


DLLEXPORT void computeHTD( int *im, bool layerFlag, int rows, int columns, double *results) {
	//image size need to be bigger then 128 x 128
	Mat Image(columns, rows , CV_16U );
    int i, j;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
				{
					Image.at<unsigned char>(i,j) = (unsigned char)(im[i*rows+j]); //must be grayscale
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setGray(Image);

	XM::HomogeneousTextureDescriptor* htd = Feature::getHomogeneousTextureD( frame, layerFlag );

	int* elements = htd->GetHomogeneousTextureFeature();

	// return to python as a numpy
	for(i = 0; i < 32; i++)
		results[i] = elements[i];

    // if full layer, print values[32-61] (energy deviation)
    if(layerFlag)
        for(i = 32; i < 62; i++)
            results[i] = elements[i];


	// release descriptor
	delete htd;
	delete frame;
}

DLLEXPORT void computeEHD( int *im, int rows, int columns, double *results) {
	
	Mat Image(columns, rows , CV_16UC3 );
    int i, j, k;
	int channel = 3;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
			for (k=0; k<channel; k++)
				{
					Image.at<Vec3b>(i,j)[k] = (unsigned char)(im[i*rows*channel+channel*j+k]); 
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setImage(Image);

	XM::EdgeHistogramDescriptor* ehd = Feature::getEdgeHistogramD( frame );

	// get a pointer to the values
	char* de = ehd->GetEdgeHistogramElement();

	// return to python as a numpy
	for( unsigned int i = 0; i < ehd->GetSize(); i++)
		results[i] = (int)de[i];


	// release descriptor
	delete ehd;
	delete frame;
}


DLLEXPORT void computeRSD( int *im, int *immask, int rows, int columns, double *results) {
	
	Mat Image( columns, rows , CV_16UC3 );
    int i, j, k;
	int channel = 3;
    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
			for (k=0; k<channel; k++)
				{
					Image.at<Vec3b>(i,j)[k] = (unsigned char)(im[i*rows*channel+channel*j+k]); 
				}

	Frame* frame = new Frame( Image.cols, Image.rows, true, true, true);
	frame->setImage(Image);

	//forground is 1 and background is 0
	int regVal = 1;
	Mat mask( columns, rows, CV_8UC1, Scalar(0) );

    for (i=0; i<columns; i++)
        for (j=0; j<rows; j++)
				{
					mask.at<unsigned char>(i,j) = (unsigned char)(immask[i*rows+j]); //must be grayscale
				}

	frame->setMaskAll( mask, regVal, 255, 0 );

	XM::RegionShapeDescriptor* rsd = Feature::getRegionShapeD( frame );

	k=0;
	// return to python as a numpy
	// result length = 35
	for(i=0; i<ART_ANGULAR; i++)
		for(j=0; j<ART_RADIAL; j++)
			if(i != 0 || j != 0)
			{
				results[k] = (int)rsd->GetElement(i, j);
				k+=1;
			}
	// release descriptor
	delete rsd;
	delete frame;
}






}