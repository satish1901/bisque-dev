CXX = g++
CC = gcc
CFLAGS = -Wall -fPIC
LFLAGS = -shared -Wl

INCLUDE = -I/usr/include/
LINK =   /usr/lib/libfftw3.so /usr/local/lib/libopencv_core.so

ROOT:=
RELEASE:= $(ROOT)release/
LIB:=$(ROOT)lib/
SRC:=$(ROOT)src/
BIN:=$(ROOT)bin/

SRCFile = $(shell find $(SRC) -name "*.cpp")
OBJFile = $(patsubst %.cpp, $(RELEASE)%.o, $(notdir $(SRCFile)))

all: $(BIN)_VRLLib.pyd

$(BIN)_VRLLib.pyd : $(OBJFile)
	$(CXX) $(LFLAGS) $(INCLUDE) $(LINK) -o $(BIN)_VRLLib.pyd $(OBJFile)

$(OBJFile):$(SRCFile)

$(RELEASE)%.o : $(SRC)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) $(LINK) -c $< -o $@

clean:
	rm -f $(RELEASE)*.o $(BIN)*.pyd
