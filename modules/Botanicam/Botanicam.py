#!/usr/bin/env python
from bisquik.util.launcher import StagedLauncher, CondorLauncher

class NucleiDetector3D(StagedLauncher):
#class NucleiDetector3D(CondorLauncher):
    execute  = ['condor_matlab', 'NucleiDetector3D']
    files    = ["condor_matlab", "NucleiDetector3D", "NucleiDetector3D.ctf",
                "NucleiDetector3D.py",
                "bisque.jar", "jai_codec.jar", "jai_core.jar",
                "jai_imageio.jar", "clibwrapper_jiio.jar"]
    transfers= ["NucleiDetector3D", "NucleiDetector3D.ctf", "bisque.jar",
                "jai_codec.jar", "jai_core.jar", "jai_imageio.jar",
                "clibwrapper_jiio.jar"]

    requirements = "&& (Memory > 3000) && IsWholeMachineSlot"
    cmd_extra    = "+RequiresWholeMachine = True"

    #fetch_inputs = False
    #mex_finish   = False
    #@classmethod
    #def before_start(cls): pass
    #def after_finish(cls): pass



# This script is called by the condor CMD and DAG Man
# with start and finish as argument
if __name__ == "__main__":
    NucleiDetector3D().main()
