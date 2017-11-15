from bq.blob_service.controllers.blob_plugins import ResourcePlugin
from bq.pipeline.controllers.importers.from_cellprofiler import upload_cellprofiler_pipeline
from bq.pipeline.controllers.importers.from_imagej import upload_imagej_pipeline

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
    
    def process_on_import(self, f, intags):
        return upload_cellprofiler_pipeline(f, intags)

class CellprofilerPipeline2Plugin (ResourcePlugin):
    '''Cellprofiler Pipeline resource''' 
    name = "PipelinePlugin"  
    version = '1.0'
    ext = 'cppipe'
    resource_type = 'cellprofiler_pipeline'
    mime_type = 'text/plain'
    
    def __init__(self):
        pass

    def process_on_import(self, f, intags):
        return upload_cellprofiler_pipeline(f, intags)
    
class ImageJPipelinePlugin (ResourcePlugin):
    '''ImageJ Pipeline resource''' 
    name = "PipelinePlugin"  
    version = '1.0'
    ext = 'ijm'
    resource_type = 'imagej_pipeline'
    mime_type = 'text/plain'
    
    def __init__(self):
        pass
    
    def process_on_import(self, f, intags):
        return upload_imagej_pipeline(f, intags)