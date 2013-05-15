CXX = g++
CC = gcc
CFLAGS = -Wall -fPIC
LFLAGS = -shared -Wl

INCLUDE = -I/usr/include/ -I$(SRC) -I$(COLOR) -I$(GSL) -I$(STATISTICS) -I$(TEXTURES) -I$(TRANSFORMS) -I$(UTIL) 
LINK =   /usr/lib/libfftw3.so /usr/lib/libtiff.so
#LINK =   -llibfftw3.so -llibtiff.so

ROOT:= 
RELEASE:= $(ROOT)release/
LIB:=$(ROOT)Lib/
SRC:=$(ROOT)src/
BIN:=$(ROOT)bin/

COLOR:=$(SRC)colors/
GSL:=$(SRC)gsl/
STATISTICS:=$(SRC)statistics/
TEXTURES:=$(SRC)textures/
HARALICK:=$(TEXTURES)/haralick/
ZERNIKE:=$(TEXTURES)/zernike/
TRANSFORMS:=$(SRC)transforms/
WAVELET:=$(TRANSFORMS)wavelet/
UTIL:=$(SRC)util/

SRCFile = $(shell find $(SRC) -name "*.cpp")
OBJFile = $(patsubst %.cpp, $(RELEASE)%.o, $(notdir $(SRCFile)))
SRCcFile = $(shell find $(UTIL) -name "*.c")
OBJcFile = $(patsubst %.c, $(RELEASE)%.o, $(notdir $(SRCcFile)))

all: $(BIN)_WNDCharmLib.pyd

$(BIN)_WNDCharmLib.pyd : $(OBJFile) $(OBJcFile)
	$(CXX) $(LFLAGS) $(INCLUDE) $(LINK) -o $(BIN)_WNDCharmLib.pyd $(OBJcFile) $(OBJFile) 


$(OBJcFile) : $(SRCcFile)

$(RELEASE)%.o : $(UTIL)%.c
	$(CC) $(CFLAGS) $(INCLUDE) -c $< -o $@


$(OBJFile):$(SRCFile)

$(RELEASE)%.o : $(COLOR)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(GSL)%.cpp 
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(STATISTICS)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(TEXTURES)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(HARALICK)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(ZERNIKE)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(TRANSFORMS)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(WAVELET)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(UTIL)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(SRC)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@


clean:
	rm -f $(RELEASE)*.o $(BIN)*.pyd
