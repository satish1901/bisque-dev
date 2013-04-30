#include <cmatrix.h>

#include <stdio.h>
#include <string.h>
#include <iostream>
#include <map>
#include <FeatureAlgorithms.h>
#include <Imagetransforms.h>

int verbosity;

namespace WND_Charm_Map {

	class Extractor_Map {
	private:
        std::map<const std::string, FeatureAlgorithm*> features;
	public:
        Extractor_Map() { init_map(); }
		void init_map() {
			features.insert(std::make_pair("Chebyshev Coefficients", new ChebyshevCoefficients()));
			features.insert(std::make_pair("Chebichev Fourier Transform", new ChebyshevFourierCoefficients()));
			features.insert(std::make_pair("Comb Four Moments", new CombFirstFourMoments()));
			features.insert(std::make_pair("Gabor Textures", new GaborTextures()));
			features.insert(std::make_pair("Haralick Texture", new HaralickTextures()));
			features.insert(std::make_pair("Multi Scale Histogram", new MultiscaleHistograms()));
			features.insert(std::make_pair("Radon Transform", new RadonCoefficients()));
			features.insert(std::make_pair("Tamura Texture", new TamuraTextures()));
			features.insert(std::make_pair("Zernike Coefficients", new ZernikeCoefficients()));
			features.insert(std::make_pair("Pixel Intensity Statistics", new PixelIntensityStatistics()));
			features.insert(std::make_pair("Color Histogram", new ColorHistogram()));
			features.insert(std::make_pair("Fractal Features", new FractalFeatures()));
            features.insert(std::make_pair("Edge Features", new EdgeFeatures()));
            features.insert(std::make_pair("Object Features", new ObjectFeatures()));
            features.insert(std::make_pair("Inverse Object Features", new InverseObjectFeatures()));
            features.insert(std::make_pair("Gini Coefficient", new GiniCoefficient()));
		};

		std::vector<double> execute(const std::string &extractor_name, const ImageMatrix &m) const {
			 return features.at(extractor_name)->execute( m );
		};
	};

	class Transform_Map {
		std::map<const std::string, ImageTransform*> transforms;
	public:
        Transform_Map() { init_map(); }
		void init_map() {
			transforms.insert(std::make_pair("Fourier Transform", new FourierTransform()));
			transforms.insert(std::make_pair("Chebyshev Transform", new ChebyshevTransform()));
			transforms.insert(std::make_pair("Wavelet Transform", new WaveletTransform()));
			transforms.insert(std::make_pair("Edge Transform", new EdgeTransform()));
            transforms.insert(std::make_pair("Color Transform", new ColorTransform()));
            transforms.insert(std::make_pair("Hue Transform", new HueTransform()));
			transforms.insert(std::make_pair("Empty Transform", new EmptyTransform()));
		};
		void execute(const std::string &transform_name, const ImageMatrix &m, ImageMatrix &newm) const {
			transforms.at(transform_name)->execute(m,newm);
		};
	};


}

void ImageMatrix::LoadImageMat( int *im, unsigned int height, unsigned int width, bool color) {
    //allows for an image matrix from numpy to be imported into ImageMatrix
	unsigned int h,w,x=0,y=0;
	unsigned short int spp=0;
	RGBcolor rgb = {0,0,0};
	ImageMatrix R_matrix, G_matrix, B_matrix;
	Moments2 R_stats, G_stats, B_stats;
    bits = 8;

    if (color == 0) { spp = 1; }
    else { spp = 3; }

	if (!spp) spp=1;  // assume one sample per pixel if nothing is specified (spp = sample per pixel)
	// regardless of how the image comes in, the stored mode is HSV
	if (spp == 3) {
		ColorMode = cmHSV;
		// If the bits are > 8, we do the read into doubles so that later
		// we can scale the image to its actual signal range.
		if (bits > 8) {
			R_matrix.ColorMode = cmGRAY;
			R_matrix.allocate (width, height);
			G_matrix.ColorMode = cmGRAY;
			G_matrix.allocate (width, height);
			B_matrix.ColorMode = cmGRAY;
			B_matrix.allocate (width, height);
		}
	} else {
		ColorMode = cmGRAY;
	}

	// allocate the data 
	allocate (width, height);
	writeablePixels pix_plane = WriteablePixels();
	writeableColors clr_plane = WriteableColors();

	
	for (y = 0; y < height; y++) {
		int col;
		x=0;col=0;
		while (x<width) {
			double val=0;
			int sample_index;
			for (sample_index=0;sample_index<spp;sample_index++) {
				if (spp==3 && bits > 8) {  /* RGB image */
					if (sample_index==0) R_matrix.WriteablePixels()(y,x) = R_stats.add ((double)im[y*width*spp+spp*x+0]);
					if (sample_index==1) G_matrix.WriteablePixels()(y,x) = G_stats.add ((double)im[y*width*spp+x*spp+1]);
					if (sample_index==2) B_matrix.WriteablePixels()(y,x) = B_stats.add ((double)im[y*width*spp+x*spp+2]);
				} else if (spp == 3) {
					if (sample_index==0) rgb.r = (unsigned char)(R_stats.add ((double)im[y*width*spp+x*spp+0]));
					if (sample_index==1) rgb.g = (unsigned char)(G_stats.add ((double)im[y*width*spp+x*spp+1]));
					if (sample_index==2) rgb.b = (unsigned char)(B_stats.add ((double)im[y*width*spp+x*spp+2]));
				}
			}
			if (spp == 3 && bits == 8) {
				clr_plane (y, x) = RGB2HSV(rgb); //adds the colored image and converts it to HSV
			} else if (spp == 1) {
				pix_plane (y, x) = stats.add((double)im[y*width+x]); //adds the grayscale image
			}
			x++;
			col+=spp;
		}
	}
	// Do the conversion to unsigned chars based on the input signal range
	// i.e. scale global RGB min-max to 0-255
	if (spp == 3 && bits > 8) {
		size_t a, num = width*height;
		double RGB_min=0, RGB_max=0, RGB_scale=0;
		R_matrix.finish();
		G_matrix.finish();
		B_matrix.finish();
		// Get the min and max for all 3 channels
		if (R_stats.min() <= G_stats.min() && R_stats.min() <= B_stats.min()) RGB_min = R_stats.min();
		else if (G_stats.min() <= R_stats.min() && G_stats.min() <= B_stats.min()) RGB_min = G_stats.min();
		else if (B_stats.min() <= R_stats.min() && B_stats.min() <= G_stats.min()) RGB_min = B_stats.min();
		if (R_stats.max() >= G_stats.max() && R_stats.max() >= B_stats.max()) RGB_max = R_stats.max();
		else if (G_stats.max() >= R_stats.max() && G_stats.max() >= B_stats.max()) RGB_max = G_stats.max();
		else if (B_stats.max() >= R_stats.max() && B_stats.max() >= G_stats.max()) RGB_max = B_stats.max();
		// Scale the clrData to the global min / max.
		RGB_scale = (255.0/(RGB_max-RGB_min));
		for (a = 0; a < num; a++) {
			rgb.r = (unsigned char)( (R_matrix.ReadablePixels().array().coeff(a) - RGB_min) * RGB_scale);
			rgb.g = (unsigned char)( (G_matrix.ReadablePixels().array().coeff(a) - RGB_min) * RGB_scale);
			rgb.b = (unsigned char)( (B_matrix.ReadablePixels().array().coeff(a) - RGB_min) * RGB_scale);
			clr_plane (y, x) = RGB2HSV(rgb);
		}
	}
}

extern "C"{
__declspec(dllexport) void WNDCharmFeatures(int* im, int height, int width, char* extractor, char* transform1, char* transform2, double* vec,  bool color ) {
    // takes in a numpy array and specified features and outputs a feature
	WND_Charm_Map::Extractor_Map e_map;
	WND_Charm_Map::Transform_Map t_map;
	ImageMatrix m; //inital image
    ImageMatrix t1m; //after first transform
    ImageMatrix t2m; //after second transform

	m.LoadImageMat(im, height, width, color );
    t_map.execute(transform1, m, t1m); // first transform
	t_map.execute(transform2, t1m, t2m); // second transform
	std::vector<double> vec_out = e_map.execute(extractor, t2m); // extractor

    memcpy(vec, &vec_out[0], vec_out.size() * sizeof vec[0]);
}

}



