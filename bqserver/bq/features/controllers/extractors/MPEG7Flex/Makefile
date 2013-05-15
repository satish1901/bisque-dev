CXX = g++
CC = gcc
CFLAGS = -Wall -fPIC
LFLAGS = -shared -Wl

INCLUDE = -I/usr/include/ -I$(ROOT) -I$(EXDIR) -I$(DESCDIR) -I$(ADDRDIR)
LINK =  /usr/local/lib/libopencv_core.so

ROOT:=

RELEASE:= $(ROOT)release/
BIN:=$(ROOT)bin/
EXDIR := $(ROOT)src/Extraction/
DESCDIR := $(ROOT)src/Descriptors/
ADDRDIR := $(ROOT)src/AddressLib/
SRCDIR := $(ROOT)src/

#list of src and obj files
#DESCSRC = $(shell find $(DESCDIR) -type f -name "*.cpp")
#DESCOBJ = $(patsubst %.cpp, $(RELEASE)%.o, $(notdir $(DESCSRC)))

ADDRSRC = $(shell find $(ADDRDIR) -name "*.c")
ADDROBJ = $(patsubst %.c, $(RELEASE)%.o, $(notdir $(ADDRSRC)))

#EXSRC = $(shell find $(EXDIR) -name "*.cpp")
#EXOBJ = $(patsubst %.cpp, $(RELEASE)%.o, $(notdir $(EXSRC)))

EXSRCc = $(shell find $(EXDIR) -name "*.c")
EXOBJc = $(patsubst %.c, $(RELEASE)%.o, $(notdir $(EXSRCc)))

SRC =  $(shell find $(SRCDIR) -name "*.cpp")
OBJ = $(patsubst %.cpp, $(RELEASE)%.o, $(notdir $(SRC)))

#commands

all: $(BIN)_MPEG7FlexLib.pyd

clean: 
	rm -f $(RELEASE)*.o $(BIN)*.pyd

#builds each group

$(BIN)_MPEG7FlexLib.pyd : $(DESCOBJ) $(ADDROBJ) $(EXOBJ) $(EXOBJc) $(OBJ)
	$(CXX) $(LFLAGS) $(INCLUDE) $(LINK) -o  $(BIN)_MPEG7FlexLib.pyd $(DESCOBJ) $(ADDROBJ) $(EXOBJ) $(EXOBJc) $(OBJ)


$(DESCOBJ):$(DESCSRC)

$(RELEASE)%.o : $(DESCDIR)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) -c $< -o $@


$(ADDROBJ):$(ADDRSRC)

$(RELEASE)%.o : $(ADDRDIR)%.c
	$(CC) $(CFLAGS) $(INCLUDE) -c $< -o $@


$(EXOBJ): $(EXSRC)

$(RELEASE)%.o : $(EXDIR)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) -c $< -o $@


$(EXOBJc): $(EXSRCc)

$(RELEASE)%.o : $(EXDIR)%.c
	$(CC) $(CFLAGS) $(INCLUDE) -c $< -o $@


$(OBJ): $(SRC)

$(RELEASE)%.o : $(SRCDIR)%.cpp
	$(CXX) $(CFLAGS) $(INCLUDE) -c $< -o $@


