MPEG7Flex = ../MPEG7Flex
VRL = ../VRL
WNDCharm = ../WNDCharm

TARGETS = $(MPEG7Flex) $(VRL) $(WNDCharm) 

.PHONY: all $(TARGETS)

all: $(TARGETS)

$(TARGETS):
	@$(MAKE) -C $@

clean:
	cd $(MPEG7Flex); make clean; cd $(VRL); make clean; cd $(WNDCharm); make clean




