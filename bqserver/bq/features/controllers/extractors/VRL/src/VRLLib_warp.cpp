#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <vector>
#include <string>
#include <fstream>
#include <opencv2/opencv.hpp>

#include "EhdExtractor.h"
#include "HtdExtractor.h"


using namespace cv;
using namespace std;

#if defined(WIN32) || defined(_WIN32) 
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif


//--------------------------------------------------------------------------------
extern "C" {
    DLLEXPORT void extractEHD(int *im, int rows, int columns, double *descriptor) {
	    Mat Image( Size(rows,columns) , CV_64F );
        int i, j;
        for (i=0; i<rows; i++)
            for (j=0; j<columns; j++)
            {
                Image.at<double>(i,j) = (double)(im[i * columns + j]);
            }

	    EhdExtractor extractor;
	    Mat ehd = extractor.extract(Image);

	    int c = ehd.size.p[0];
	    int r = ehd.size.p[1];
        for (i=0; i<r; i++)
            for (j=0; j<c; j++)
            {
                descriptor[i * columns + j] = (double)ehd.at<double>(i,j);
            }
    }
}

extern "C" {
    DLLEXPORT void extractHTD(int *im, int rows, int columns, double *descriptor) {
	    Mat Image( Size(rows,columns) , CV_64F );
        int i, j;
        for (i=0; i<rows; i++)
            for (j=0; j<columns; j++)
            {
                Image.at<double>(i,j) = (double)(im[i * columns + j]);
            }

	    unsigned int sizeY = Image.size.p[0];
	    unsigned int sizeX = Image.size.p[1];

	    HtdExtractor myHtdExtractor(sizeX,sizeY);

	    Mat HTD = myHtdExtractor.extract( Image, sizeX, sizeY );

	    //cout << "HTD " << endl << " " << HTD << endl << endl;
	    int c = HTD.size.p[0];
	    int r = HTD.size.p[1];
        for (i=0; i<r; i++)
            for (j=0; j<c; j++)
            {
                descriptor[i * columns + j] = (double)HTD.at<double>(i,j);
            }
    }
}

