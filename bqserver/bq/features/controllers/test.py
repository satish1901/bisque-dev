import inspect
import traceback
import os
#import Feature
import extractors
import pkgutil
  
feature_module_dict = {}
#moddirs=['extractors\\'+o for o in os.listdir('extractors') if os.path.isdir('extractors\\'+o)]
x=[name for stuff1, name, stuff2 in pkgutil.iter_modules(['extractors'])]
##moddirs = ['ID']
##for modules in moddirs:
##    try:
##    __import__('extractors.'+modules)
##    for n,item in inspect.getmembers(getattr(extractors,modules)):
##            if inspect.isclass(item) and issubclass(item, Feature.Feature):
##                feature_module_dict[item.name] = item
##    except ImportError,e:
##        print 'Error: %s was not found'%modules
##        #print traceback.print_exc()

print os.path(inspect)
