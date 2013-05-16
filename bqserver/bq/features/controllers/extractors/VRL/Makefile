CXX = g++
CC = gcc
CFLAGS = -Wall -fPIC
LFLAGS = -shared -Wl

INCLUDE = -I/usr/include/
#LINK =   /usr/lib/libfftw3.so /usr/local/lib/libopencv_core.so
LINK =   -llibfftw3.so -llibopencv_core.so

ROOT:=
RELEASE:= $(ROOT)release/
LIB:=$(ROOT)lib/
SRC:=$(ROOT)src/

SRCFile = $(shell find $(SRC) -name "*.cpp")
OBJFile = $(patsubst %.cpp, $(RELEASE)%.o, $(notdir $(SRCFile)))

all: $(BIN)_VRLLib.pyd

$(LIB)_VRLLib.pyd : $(OBJFile)
	mkdir $(LIB); $(CXX) $(LFLAGS) $(INCLUDE) $(LINK) -o $(LIB)_VRLLib.pyd $(OBJFile)

$(OBJFile):$(SRCFile)

$(RELEASE)%.o : $(SRC)%.cpp
	mkdir $(RELEASE); $(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

clean:
	rm -f $(RELEASE)*.o $(LIB)*.pyd
