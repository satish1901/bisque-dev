CXX = g++
CC = gcc
CFLAGS = -Wall -fPIC
LFLAGS = -shared -Wl

INCLUDE = -I/usr/include/ -I$(SRC) -I$(COLOR) -I$(GSL) -I$(STATISTICS) -I$(TEXTURES) -I$(TRANSFORMS) -I$(UTIL) 
#LINK =   /usr/lib/libfftw3.so /usr/lib/libtiff.so
LINK =   -llibfftw3.so -llibtiff.so

ROOT:= 
RELEASE:= $(ROOT)release/
LIB:=$(ROOT)Lib/
SRC:=$(ROOT)src/

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

all: $(LIB)_WNDCharmLib.pyd

$(LIB)_WNDCharmLib.pyd : $(OBJFile) $(OBJcFile)
	mkdir $(LIB); $(CXX) $(LFLAGS) $(INCLUDE) $(LINK) -o $(LIB)_WNDCharmLib.pyd $(OBJcFile) $(OBJFile)


$(OBJcFile) : $(SRCcFile)

$(RELEASE)%.o : $(UTIL)%.c
	mkdir $(RELEASE); $(CC) $(CFLAGS) $(INCLUDE) -c $< -o $@


$(OBJFile):$(SRCFile)

$(RELEASE)%.o : $(COLOR)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(GSL)%.cpp 
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(STATISTICS)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(TEXTURES)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(HARALICK)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(ZERNIKE)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(TRANSFORMS)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(WAVELET)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(UTIL)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

$(RELEASE)%.o : $(SRC)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@


clean:
	rm -f $(RELEASE)*.o $(BIN)*.pyd
