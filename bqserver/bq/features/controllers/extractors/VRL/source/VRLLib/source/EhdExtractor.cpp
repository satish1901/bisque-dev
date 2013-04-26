////////////////////////////////////////////////////////////////////////////////
//  ==========================================================================
//                       MIR - Mega Image Retrieval
//  ==========================================================================
//
//      File Name: EhdExtractor.cpp
//    Description: Edge Histogram Descriptor based on MPEG7
//  Related Files: EhdExtractor.h
//           Date: 12/05/2003
//    Portability: Standard C++
//     References:
//      Author(s): Thiele
//
//  Revision History: 
////////////////////////////////////////////////////////////////////////////////

#include <iostream>
#include <opencv2/opencv.hpp>

#include "EhdExtractor.h"

using namespace cv;
using namespace std;

// Quantization quantization tables
double QuantTable[5][8] = { 

  {0.010867,0.057915,0.099526,0.144849,0.195573,0.260504,0.358031,0.530128}, 
  {0.012266,0.069934,0.125879,0.182307,0.243396,0.314563,0.411728,0.564319},
  {0.004193,0.025852,0.046860,0.068519,0.093286,0.123490,0.161505,0.228960},
  {0.004174,0.025924,0.046232,0.067163,0.089655,0.115391,0.151904,0.217745},
  {0.006778,0.051667,0.108650,0.166257,0.224226,0.285691,0.356375,0.450972},

};

EhdExtractor::EhdExtractor() { //why is this here???
}


Mat EhdExtractor::extract( Mat img ) {
  
	unsigned long size = 80;
	unsigned long desiredNumOfBlocks = 1100; //MPEG-7 uses 1100 Block
  
	unsigned long	blockSize;
	int		TeValue = 11;
	EHD		*pLocalEdge;
	pLocalEdge = NULL;
	pLocalEdge = new EHD[1];
	unsigned char temp[80];
  

	unsigned int sizeY = img.size.p[0];
	unsigned int sizeX = img.size.p[1];

	blockSize = getBlockSize(sizeX, sizeY, desiredNumOfBlocks);
	if(blockSize<2)
	blockSize = 2;
	
	Mat EHD = EdgeHistogramGeneration(img, sizeX, sizeY, blockSize, TeValue);

  
	return EHD;
}

//-----------------------------------------------------------------------------
unsigned long EhdExtractor::getBlockSize(unsigned long imageWidth, unsigned long imageHeight, unsigned long desiredNumOfBlocks) {

	unsigned long	blockSize;
	double		tempSize;
	
	tempSize = (double) sqrt(double(imageWidth*imageHeight)/double(desiredNumOfBlocks));
	blockSize = ((unsigned long) (tempSize/2))*2;
	
	return blockSize;

}

//----------------------------------------------------------------------------
Mat EhdExtractor::EdgeHistogramGeneration(Mat image, unsigned long imageWidth, unsigned long imageHeight, unsigned long blockSize, int TeValue) {

	int CountLocal[16], subLocalIndex;
	int Offset, EdgeTypeOfBlock;
	long	LongTypLocalEdge[80];
	Mat EHD( Size(1,80) , CV_64F );
	
	// Clear
	memset(CountLocal, 0, 16*sizeof(int));		
	memset(LongTypLocalEdge, 0, 80*sizeof(long));

	for(long int j=0; j<=(((long int)(imageHeight))-((long int)(blockSize))-1); j+=blockSize) { //cycles through the height

		  for(long int i=0; i<=(((long int)(imageWidth))-((long int)(blockSize))-1); i+=blockSize) { //cycles through the width

				subLocalIndex = (int)(i*4/imageWidth)+(int)(j*4/imageHeight)*4;
				CountLocal[subLocalIndex]++;
		
				//cut blocks out of the large image
				
				EdgeTypeOfBlock = GetEdgeFeature( image(Range(j,j+blockSize),Range(i,i+blockSize)) , blockSize, TeValue );

				switch(EdgeTypeOfBlock) {

				case NoEdge:
				  break;
				case verticalEdge:
				  LongTypLocalEdge[subLocalIndex*5]++;
				  break;
				case horizontalEdge:
				  LongTypLocalEdge[subLocalIndex*5+1]++;
				  break;
				case diagonal45DegreeEdge:
				  LongTypLocalEdge[subLocalIndex*5+2]++;
				  break;
				case diagonal135DegreeEdge:
				  LongTypLocalEdge[subLocalIndex*5+3]++;
				  break;
				case nonDirectionalEdge:
				  LongTypLocalEdge[subLocalIndex*5+4]++;
				  break;

				} //switch(EdgeTypeOfBlock)

		  } // for( i )

	}
	for(int i=0; i<80; i++) {			// Range 0.0 ~ 1.0
	
	  subLocalIndex = (int)(i/5);
	  EHD.at<double>(0,i) = (double)LongTypLocalEdge[i]/CountLocal[subLocalIndex];
	  
	}
	return EHD;
}

//----------------------------------------------------------------------------------------------------------------------
int EhdExtractor::GetEdgeFeature(Mat ImgBlock, int blockSize, int TeValue) {

	int i, j;
	double	d1, d2, d3, d4;
	int e_index;
	double dc_th = TeValue;
	double e_h, e_v, e_45, e_135, e_m, e_max;
	
	d1=0.0;
	d2=0.0;
	d3=0.0;
	d4=0.0;

	for(j=0; j<blockSize; j++) {
			for(i=0; i<blockSize; i++) {

				if(j<blockSize/2) {

					if(i<blockSize/2)
						//img.at<int>(y,x)
						d1 += ImgBlock.at<int>(j,i); //reading the the Mat file 
					else
						d2 += ImgBlock.at<int>(j,i);
				}
				else {

					if(i<blockSize/2)
						d3 += ImgBlock.at<int>(j,i);
					else
						d4 += ImgBlock.at<int>(j,i);

				}

			}

	}
	
	d1 = d1/(blockSize*blockSize/4.0);
	d2 = d2/(blockSize*blockSize/4.0);
	d3 = d3/(blockSize*blockSize/4.0);
	d4 = d4/(blockSize*blockSize/4.0);

	e_h = fabs(d1+d2-(d3+d4));
	e_v = fabs(d1+d3-(d2+d4));
	e_45 = sqrt(2.0)*fabs(d1-d4);
	e_135 = sqrt(2.0)*fabs(d2-d3);

	e_m = 2*fabs(d1-d2-d3+d4);

	e_max = e_v;
	e_index = verticalEdge;
	if(e_h>e_max){

		e_max=e_h;
		e_index = horizontalEdge;

	}
	if(e_45>e_max){

		e_max=e_45;
		e_index = diagonal45DegreeEdge;

	}
	if(e_135>e_max){

		e_max=e_135;
		e_index = diagonal135DegreeEdge;

	}
	if(e_m>e_max){

		e_max=e_m;
		e_index = nonDirectionalEdge;

	}
	if(e_max<dc_th)
		e_index = NoEdge;

	return(e_index);
	
}




//-------------------------------------------------------------------------
void EhdExtractor::quantization(EHD* pLocalEdge) {
  int i, j;
  double iQuantValue;
  int temp[80];

  for( i=0; i < 80; i++ ) {
    j=0;
    while(1){

      if( j < 7 ) // SIZI-1 
        iQuantValue = (QuantTable[i%5][j]+QuantTable[i%5][j+1])/2.0;
      else 
        iQuantValue = 1.0;
      if(pLocalEdge->LocalEdge[i] <= iQuantValue)
        break;
      j++;

    }
    temp[i] = j;

  }
  for( i=0; i < 80; i++ ){

    pLocalEdge->LocalEdge[i] = QuantTable[ i%5 ][ temp[i] ];

  }
}

