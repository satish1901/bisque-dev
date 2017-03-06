from bq.blob_service.controllers.blob_plugins import ResourcePlugin

class Dream3DPipelinePlugin (ResourcePlugin):
    '''Dream.3D Pipeline resource''' 
    name = "PipelinePlugin"  
    version = '1.0'
    ext = 'json'
    resource_type = 'dream3d_pipeline'
    mime_type = 'application/json'
    
    def __init__(self):
        pass

class CellprofilerPipelinePlugin (ResourcePlugin):
    '''Cellprofiler Pipeline resource''' 
    name = "PipelinePlugin"  
    version = '1.0'
    ext = 'cp'
    resource_type = 'cellprofiler_pipeline'
    mime_type = 'text/plain'
    
    def __init__(self):
        pass

class CellprofilerPipeline2Plugin (ResourcePlugin):
    '''Cellprofiler Pipeline resource''' 
    name = "PipelinePlugin"  
    version = '1.0'
    ext = 'cppipe'
    resource_type = 'cellprofiler_pipeline'
    mime_type = 'text/plain'
    
    def __init__(self):
        pass
