

from bq import data_service

def registration_cb (action, user=None):
    if action == 'update_user':
        data_service.cache_invalidate('/data_service/users')
        

        
        


