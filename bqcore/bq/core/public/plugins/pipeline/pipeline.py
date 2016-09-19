from bq.blob_service.controllers.blob_plugins import ResourcePlugin

class PipelinePlugin (ResourcePlugin):
    '''Pipeline resource''' 
    name = "PipelinePlugin"  
    version = '1.0'
    ext = 'json'
    resource_type = 'dream3d_pipeline'
    mime_type = 'application/json'
    
    def __init__(self):
        pass
