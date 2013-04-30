/*------------------------------------------------------------------------------
 *
 *  Copyright (C) 2003 Open Microscopy Environment
 *      Massachusetts Institute of Technology,
 *      National Institutes of Health,
 *      University of Dundee
 *
 *
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *------------------------------------------------------------------------------
 */




/*------------------------------------------------------------------------------
 *
 * Written by:    Ilya G. Goldberg <igg@nih.gov>
 * 
 *------------------------------------------------------------------------------
 */




/*
* ReadTIFFData
* 
* PROTOTYPE:
int ReadTIFFData(TIFF* tif,unsigned char *buf)
* PURPOSE:
* This routine will read a multi-stripped (or not), compressed (or not), 8 (or 16)
* bits-per-pixel TIFF file (big or little-endian)
* into a single contiguous buffer using libtiff.
* This routine WILL NOT READ:
* TIFF files that are tiled.
* TIFF files that contain more than one sample per pixel or more than one plane of pixels.
* PARAMETERS:
* TIFF *tif - pointer to a TIFF structure as returned by TIFFOpen.
* unsigned char *buf - pointer to a pre-allocated buffer that is large enough
*	to contin the entire TIFF file.
* USAGE:
* you will need to:
#include <tiffio.h>
* This will define TIFF tags, and declare i/o routines from libtiff.
* To get the tif, call:
	tif = TIFFOpen(filename,"r")
		filename is a string containing the filename (just like fopen())
		"r" for reading, "w" for writing, and "a" for appending.
		man TIFFOpen for more details.
* To determine if the file is grayscale:
	if (isGray (tif) < 0) // malformed TIFF - get error text using GetReadTIFFError()
	if (isGray (tif) == 1) // single-plane grayscale tiff
	if (isGray (tif) == 0) // tiff containing multiple planes or multiple samples per pixel
* To determine if the file is RGB:
	if (isRGB (tif) < 0) // malformed TIFF - get error text using GetReadTIFFError()
	if (isRGB (tif) == 1) // Tiff has 3 or 4 planes, or 3 or 4 samples per pixel: readable as RGB
	if (isRGB (tif) == 0) // Tiff is Grayscale
* To determine the size of the TIFF file, call:
	TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bits);
	TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &width);
	TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &height);
		bits is an uint16.
		width and height are uint32.
		This function, types and #defines are defined in tiffio.h
* Allocate an appropriately sized buffer to contain the TIFF file
* For example if reading grayscale TIFFs (8, 16 or 32 bits per pixel):
	buf = (unsigned char *)malloc (width*height*(bits/8));
	or, using the portable TIFF memory allocation:
	buf = (unsigned char *)_TIFFmalloc(width*height*(bits/8));
* If reading RGB TIFFs (8, 16 or 32 bits per channel):
	buf = (unsigned char *)malloc (width*height*(bits/8)*3);
	or, using the portable TIFF memory allocation:
	buf = (unsigned char *)_TIFFmalloc(width*height*(bits/8)*3);
* Call ReadTIFFData to read Grayscale (will return error if an RGB TIFF):
	error = ReadTiffData (tif,buf);
* Call ReadRGBTIFFData to read RGB (will return error if a Grayscale TIFF):
* buf will contain three contiguous planes (R plane then G plane, then B plane)
* For either grayscale or RGB, the pixel depth (8, 16 or 32) will be what was in the TIFF file.
	error = ReadRGBTiffData (tif,buf);
* Do whatever it is you want to the buffer, then call
	free (buf)
*	or, if used _TIFFmalloc, call
	_TIFFfree(buf);
* Note that although the buffer passed to ReadTIFFData must be of type unisigned char,
* this is only because the functions therein deal only in bytes.  They will handle
* 16 bit or 32 bit pixels just fine, though.
* ERROR CODES - return values for ReadTIFFData(), ReadRGBTIFFData(), isRGB(), isGray()
* Call GetReadTIFFError(errNum,errMsg) to get error text copied into errMsg (char *; >= 128 bytes).
* -1  buf is NULL
* -2  TIFF is tiled.
* -3  TIFF is not 8, 16 or 32 bits/pixel.
* -4  Grayscale TIFF has more than one plane or more than one sample/pixel.
* -5  Problem reading strips (error in libtiff's TIFFReadEncodedStrip).
* -6  Could not open file for writing.
* -8  Problem writing strips (error in libtiff's TIFFWriteEncodedStrip). 
* -9  RGB TIFF PlanarConfiguration is not 1 or 2.
* -10 Could not allocate memory for a strip.
* -11 RGB TIFF Samples per pixel is not 3 or 4.
*  0  no errors.
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <tiffio.h>
#include "readTIFF.h"




int
TIFFReadContigStripData(TIFF* tif,unsigned char *buf)
{
	tsize_t scanline = TIFFScanlineSize(tif);


	if (buf)
		{
		uint32 row, h;
		uint32 rowsperstrip = (uint32)-1;

		TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &h);
		TIFFGetField(tif, TIFFTAG_ROWSPERSTRIP, &rowsperstrip);
		for (row = 0; row < h; row += rowsperstrip)
			{
			uint32 nrow = (row+rowsperstrip > h ?
			    h-row : rowsperstrip);
			tstrip_t strip = TIFFComputeStrip(tif, row, 0);
			if (TIFFReadEncodedStrip(tif, strip, buf, nrow*scanline) < 0)
				return (-1);
			buf += (nrow * scanline);
			}
		}
		return (0);
}


int
TIFFReadContigRGBStripData(TIFF* tif,unsigned char *buf)
{
tsize_t nread;
uint32 h, ncols;
tsize_t stripsize;
char *strip_buf;
uint32 rowsperstrip = (uint32)-1;
uint16 pc, spp, bps, bpp; // planar configuration, samples per pixel, bits per sample, bytes per pixel
tstrip_t strip, nstrips;
uint8 *buf8, *samp8p, *r8p, *g8p, *b8p;
uint16 *buf16, *samp16p, *r16p, *g16p, *b16p;
uint32 *buf32, *samp32p, *r32p, *g32p, *b32p;


	if (!buf) return (-1);

	stripsize = TIFFStripSize(tif);
	// Allocate a strip's worth of memory
	if ( (strip_buf = (char *)malloc (stripsize)) == NULL ) {
		return (-10);
	}
	nstrips = TIFFNumberOfStrips(tif);


	TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &h);
	TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &ncols);
	TIFFGetField(tif, TIFFTAG_ROWSPERSTRIP, &rowsperstrip);
	TIFFGetField(tif, TIFFTAG_PLANARCONFIG, &pc);
	TIFFGetField(tif, TIFFTAG_SAMPLESPERPIXEL, &spp);
	TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bps);
	bpp = (bps / 8) * spp; // pre-calculate bytes per pixel for packed pixels


	// set up pointers for different bits per sample
	buf8 = (uint8 *)buf;
	r8p = buf8;
	g8p = buf8+(h*ncols);
	b8p = buf8+(h*ncols*2);

	buf16 = (uint16 *)buf;
	r16p = buf16;
	g16p = buf16+(h*ncols);
	b16p = buf16+(h*ncols*2);

	buf32 = (uint32 *)buf;
	r32p = buf32;
	g32p = buf32+(h*ncols);
	b32p = buf32+(h*ncols*2);

	for (strip = 0; strip < nstrips; strip ++) {

		if ( (nread = TIFFReadEncodedStrip(tif, strip, strip_buf, stripsize)) < 0) {
			free (strip_buf);
			return (-5);
		}
		
		if (pc == 2) { // unpacked (RRR..., GGG..., BBB...)
			memcpy( (void *)buf, (const void *)strip_buf, nread);
			buf += nread;
		} else { // packed (RGB, RGB, RGB...)
			switch (bps) {
				case 8:
					samp8p = (uint8 *)strip_buf;
					while (nread) {
						*r8p++ = *samp8p++;
						*g8p++ = *samp8p++;
						*b8p++ = *samp8p++;
						if (spp == 4) samp8p++; // ignore alpha if present
						nread -= bpp;
					}
				break;
				case 16:
					samp16p = (uint16 *)strip_buf;
					while (nread) {
						*r16p++ = *samp16p++;
						*g16p++ = *samp16p++;
						*b16p++ = *samp16p++;
						if (spp == 4) samp16p++; // ignore alpha if present
						nread -= bpp;
					}
				break;
				case 32:
					samp32p = (uint32 *)strip_buf;
					while (nread) {
						*r32p++ = *samp32p++;
						*g32p++ = *samp32p++;
						*b32p++ = *samp32p++;
						if (spp == 4) samp32p++; // ignore alpha if present
						nread -= bpp;
					}
				break;
			}
		}
	}

	free (strip_buf);
	return (0);
}


/*
  *buf points to float pixels
*/
int
TIFFReadContigRGBStripDataFlt(TIFF* tif,float *buf, int *minBits)
{
tsize_t nread;
uint32 h, ncols;
tsize_t stripsize;
char *strip_buf;
uint32 rowsperstrip = (uint32)-1;
uint16 pc, spp, bps, bpp; // planar configuration, samples per pixel, bits per sample, bytes per pixel
tstrip_t strip, nstrips;
float *Rp, *Gp, *Bp;
uint8 *samp8p;
uint16 *samp16p;
uint32 *samp32p;
int i;
uint32 samp,maxInt,maxRGB=0;

	if (!buf) return (-1);

	stripsize = TIFFStripSize(tif);
	// Allocate a strip's worth of memory
	if ( (strip_buf = (char *)malloc (stripsize)) == NULL ) {
		return (-10);
	}
	nstrips = TIFFNumberOfStrips(tif);


	TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &h);
	TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &ncols);
	TIFFGetField(tif, TIFFTAG_ROWSPERSTRIP, &rowsperstrip);
	TIFFGetField(tif, TIFFTAG_PLANARCONFIG, &pc);
	TIFFGetField(tif, TIFFTAG_SAMPLESPERPIXEL, &spp);
	TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bps);
	bpp = (bps / 8) * spp; // pre-calculate bytes per pixel for packed pixels


	// set up buffer pointers for different planes
	Rp = buf;
	Gp = buf+(h*ncols);
	Bp = buf+(h*ncols*2);

	for (strip = 0; strip < nstrips; strip ++) {

		if ( (nread = TIFFReadEncodedStrip(tif, strip, strip_buf, stripsize)) < 0) {
			free (strip_buf);
			return (-5);
		}
		
		if (pc == 2) { // unpacked (RRR..., GGG..., BBB...)
			switch (bps) {
				case 8:
					samp8p = (uint8 *)strip_buf;
					while (nread) {
						samp = *samp8p++;
						if (samp > maxRGB) maxRGB = samp;
						*buf++ = (float)samp;
						if (spp == 4) samp8p++; // ignore alpha if present
						nread -= 1;
					}
				break;
				case 16:
					samp16p = (uint16 *)strip_buf;
					while (nread) {
						samp = *samp16p++;
						if (samp > maxRGB) maxRGB = samp;
						*buf++ = (float)samp;
						if (spp == 4) samp16p++; // ignore alpha if present
						nread -= 2;
					}
				break;
				case 32:
					samp32p = (uint32 *)strip_buf;
					while (nread) {
						samp = *samp32p++;
						if (samp > maxRGB) maxRGB = samp;
						*buf++ = (float)samp;
						if (spp == 4) samp32p++; // ignore alpha if present
						nread -= 4;
					}
				break;
			}
		} else { // packed (RGB, RGB, RGB...)
			switch (bps) {
				case 8:
					samp8p = (uint8 *)strip_buf;
					while (nread) {
						samp = *samp8p++;
						if (samp > maxRGB) maxRGB = samp;
						*Rp++ = (float)samp;
						samp = *samp8p++;
						if (samp > maxRGB) maxRGB = samp;
						*Gp++ = (float)samp;
						samp = *samp8p++;
						if (samp > maxRGB) maxRGB = samp;
						*Bp++ = (float)samp;
						if (spp == 4) samp8p++; // ignore alpha if present
						nread -= bpp;
					}
				break;
				case 16:
					samp16p = (uint16 *)strip_buf;
					while (nread) {
						samp = *samp16p++;
						if (samp > maxRGB) maxRGB = samp;
						*Rp++ = (float)samp;
						samp = *samp16p++;
						if (samp > maxRGB) maxRGB = samp;
						*Gp++ = (float)samp;
						samp = *samp16p++;
						if (samp > maxRGB) maxRGB = samp;
						*Bp++ = (float)samp;
						if (spp == 4) samp16p++; // ignore alpha if present
						nread -= bpp;
					}
				break;
				case 32:
					samp32p = (uint32 *)strip_buf;
					while (nread) {
						samp = *samp32p++;
						if (samp > maxRGB) maxRGB = samp;
						*Rp++ = (float)samp;
						samp = *samp32p++;
						if (samp > maxRGB) maxRGB = samp;
						*Gp++ = (float)samp;
						samp = *samp32p++;
						if (samp > maxRGB) maxRGB = samp;
						*Bp++ = (float)samp;
						if (spp == 4) samp32p++; // ignore alpha if present
						nread -= bpp;
					}
				break;
			}
		}
	}

	free (strip_buf);

	// calculate the minimum number of bits necessary to express maxRGB
	*minBits = bps;
	maxInt = 256;
	for (i = 8; i <= bps; i++) {
		if (maxRGB < maxInt) {
			*minBits = i;
			break;
		}
		maxInt *= 2;
	}
	
	return (0);
}











int ReadTIFFData(TIFF* tif,unsigned char *buf)
{
	uint16 config;
	uint16 bits;

/*
* if buf isn't a valid pointer, return immediately.
*/
	if (!buf)
		return (-1);

/*
* We don't deal with tiled data.
*/
	if (TIFFIsTiled(tif))
		return (-2);

	TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bits);

/*
* We don't deal with less than 8 bits/pixel.
*/
	if (bits < 8)
		return (-3);


/*
* We don't deal with non-contiguous data - samples per pixel should be 1
*/
	TIFFGetField(tif, TIFFTAG_PLANARCONFIG, &config);
	if (config != PLANARCONFIG_CONTIG)
		return (-4);



/*
* Read the strips.
*/
	if (TIFFReadContigStripData(tif,buf) < 0)
		return (-5);

/*
* Return a pointer to the buffer.
*/
	return (0);
}



int ReadRGBTIFFData(TIFF* tif,unsigned char *buf)
{
	int ret;

/*
* if buf isn't a valid pointer, return immediately.
*/
	if (!buf)
		return (-1);

/*
* Return the error if its not RGB.
*/
	if ( (ret = isRGB (tif)) != 1)
		return (ret);


/*
* Read the strips.
*/
	if ( (ret = TIFFReadContigRGBStripData(tif,buf)) < 0)
		return (ret);

	return (0);
}


int ReadRGBTIFFDataFlt(TIFF* tif,float *buf, int *minBits)
{
	int ret;

/*
* if buf isn't a valid pointer, return immediately.
*/
	if (!buf)
		return (-1);

/*
* Return the error if its not RGB.
*/
	if ( (ret = isRGB (tif)) != 1)
		return (ret);

/*
* Read the strips.
*/
	if ( (ret = TIFFReadContigRGBStripDataFlt(tif,buf,minBits)) < 0)
		return (ret);

	return (0);
}




int WriteTIFFData (char *file,unsigned char *buf,int bufbps,int rows, int cols) {
TIFF* tiff;
uint32 row;
uint32 rowsperstrip = (uint32)-1;
tsize_t scanline;
	
		
	tiff = TIFFOpen(file,"w");
	if (!tiff ) return -6;
	
	TIFFSetField(tiff, TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG);
	TIFFSetField(tiff, TIFFTAG_BITSPERSAMPLE, bufbps);
	TIFFSetField(tiff, TIFFTAG_SAMPLESPERPIXEL, 1);
	if (! TIFFSetField(tiff, TIFFTAG_COMPRESSION, COMPRESSION_LZW) )
		TIFFSetField(tiff, TIFFTAG_COMPRESSION, COMPRESSION_NONE);
	TIFFSetField(tiff, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK);
	

	TIFFSetField(tiff, TIFFTAG_IMAGEWIDTH, cols);
	TIFFSetField(tiff, TIFFTAG_IMAGELENGTH, rows);
	rowsperstrip = TIFFDefaultStripSize(tiff,0);
	TIFFSetField(tiff, TIFFTAG_ROWSPERSTRIP, rowsperstrip);

	scanline = TIFFScanlineSize(tiff);

	for (row = 0; row < rows; row += rowsperstrip)
		{
		uint32 nrow = (row+rowsperstrip > rows ?
			rows-row : rowsperstrip);
		tstrip_t strip = TIFFComputeStrip(tiff, row, 0);
		if (TIFFWriteEncodedStrip(tiff, strip, buf, nrow*scanline) < 0) {
			TIFFClose (tiff);
			return (-8);
		}
		buf += (nrow * scanline);
		}
	TIFFClose (tiff);
	return (0);
}




int isRGB (TIFF *tif) {
	uint16 spp,config;
	uint16 bits;
/*
* We don't deal with tiled data.
*/
	if (TIFFIsTiled(tif))
		return (-2);


/*
* We don't deal with less than 8 bits/pixel.
*/
	TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bits);
	if ( !(bits == 8 || bits == 16 || bits == 32) )
		return (-3);

/*
* We don't deal with PlanarConfiguration other than 1 or 2.
*/
	TIFFGetField(tif, TIFFTAG_PLANARCONFIG, &config);
	if ( !(config == 1 || config == 2) )
		return (-9);


/*
* We don't deal with samples per pixel other than 3 or 4
*/
	TIFFGetField(tif, TIFFTAG_SAMPLESPERPIXEL, &spp);
	if ( spp == 3 || spp == 4 )
		return (1);  // Can be interpreted as RGB
	else if (spp == 1)
		return (0); // grayscale
	else
		return (-11);
}

int isGray (TIFF *tif) {
	uint16 spp,config;
	uint16 bits;
/*
* We don't deal with tiled data.
*/
	if (TIFFIsTiled(tif))
		return (-2);


/*
* We don't deal with less than 8 bits/pixel.
*/
	TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bits);
	if ( !(bits == 8 || bits == 16 || bits == 32) )
		return (-3);

/*
* We don't deal with PlanarConfiguration other than 1 or 2.
*/
	TIFFGetField(tif, TIFFTAG_PLANARCONFIG, &config);
	if ( !(config == 1 || config == 2) )
		return (-9);
	else if (config == 2)
		return (0); // multiple planes: not Gray


/*
* We don't deal with samples per pixel other than 3 or 4
*/
	TIFFGetField(tif, TIFFTAG_SAMPLESPERPIXEL, &spp);
	if ( spp == 1 )
		return (1);  // Can be interpreted as RGB
	else
		return (0); // RGB or unknown
}




char *GetReadTIFFError (int errNum, char *errMsg)
{


	switch (errNum)
	{
	case -1:
		strcpy (errMsg,"Buffer for reading TIFF was NULL.");
	break;
	case -2:
		strcpy (errMsg,"TIFF file is tiled - cannot read a tiled TIFF file.");
	break;
	case -3:
		strcpy (errMsg,"Pixels in TIFF are not 8, 16 or 32 bits/pixel.");
	break;
	case -4:
		strcpy (errMsg,"Grayscale TIFF has more than one plane or more than one sample/pixel.");
	break;
	case -5:
		strcpy (errMsg,"Problem reading strips (error in libtiff's TIFFReadEncodedStrip).");
	break;

	case -6:
		strcpy (errMsg,"Could not open file for writing.");
	break;

	case -7:
		strcpy (errMsg,"");
	break;
	case -8:
		strcpy (errMsg,"Problem writing strips (error in libtiff's TIFFWriteEncodedStrip).");
	break;

	case -9:
		strcpy (errMsg,"RGB TIFF PlanarConfiguration is not 1 or 2.");
	break;
	case -10:
		strcpy (errMsg,"Could not allocate memory for a strip.");
	break;
	case -11:
		strcpy (errMsg,"RGB TIFF Samples per pixel is not 3 or 4.");
	break;

	case 0:
		strcpy (errMsg,"");
	break;
	}
	
	return (errMsg);
}

