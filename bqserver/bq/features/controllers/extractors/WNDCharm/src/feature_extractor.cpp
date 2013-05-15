#include <cmatrix.h>

#include <stdio.h>
#include <string.h>
#include <iostream>
#include <map>
#include <FeatureAlgorithms.h>
#include <ImageTransforms.h>

#if defined(WIN32) || defined(_WIN32) 
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

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



extern "C"{
DLLEXPORT void WNDCharmFeatures(int* im, int height, int width, char* extractor, char* transform1, char* transform2, double* vec,  bool color ) {
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



