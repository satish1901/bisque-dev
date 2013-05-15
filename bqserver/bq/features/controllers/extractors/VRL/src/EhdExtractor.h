////////////////////////////////////////////////////////////////////////////////
//  ==========================================================================
//                       MIR - Mega Image Retrieval
//  ==========================================================================
//
//      File Name: EhdExtractor.h
//    Description: Edge Histogram Descriptor based on MPEG7
//  Related Files: EhdExtractor.cpp
//           Date: 12/05/2003
//    Portability: Standard C++
//     References:
//      Author(s): Thiele
//
//  Revision History:
////////////////////////////////////////////////////////////////////////////////

#ifndef EHDEXTRACTOR_H
#define EHDEXTRACTOR_H

//#include "ImageData.h"
#include <cmath>
//#include "EHDescriptor.h"
#include <opencv2/opencv.hpp>

using namespace cv;
using namespace std;

//#include "string"
//#include "filestring.h"

#define	NoEdge				    0
#define	verticalEdge			1
#define	horizontalEdge			2
#define	nonDirectionalEdge		3
#define	diagonal45DegreeEdge	4
#define	diagonal135DegreeEdge	5


typedef	struct Edge_Histogram_Descriptor{
  double LocalEdge[80]; 
} EHD;

class EhdExtractor
{

public:
        EhdExtractor();
        Mat extract(Mat img);
        
private:
      
        unsigned long getBlockSize(unsigned long imageWidth, unsigned long imageHeight, unsigned long desiredNumOfBlocks);       
        Mat EdgeHistogramGeneration(Mat Image, unsigned long imageWidth,unsigned long imageHeight, unsigned long blockSize, int TeValue);
        int GetEdgeFeature(Mat ImgBlock, int blockSize, int TeValue);
        void quantization(EHD*	pEdge_Histogram);
};

#endif // EHDEXTRACTOR_H
