#
#
#
from base_env import ModuleEnvironmentError, ModuleEnvironment, BaseEnvironment
from staged_env import StagedEnvironment
from matlab_env import MatlabEnvironment
from script_env import ScriptEnvironment
MODULE_ENVS = [ BaseEnvironment,
                StagedEnvironment,
                MatlabEnvironment,
                ScriptEnvironment ]

