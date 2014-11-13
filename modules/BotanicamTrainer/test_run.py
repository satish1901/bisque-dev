#test_run.py

import os
import random
import subprocess

USER                  = 'admin'
PASS                  = 'admin'
ROOT                  = 'http://128.111.185.26:8080'
STAGING_PATH          = os.path.join('TestStaging','%s'%str(int(random.random()*10000)))
MODULE_DIR            = 'c:\\bisque5\\modules\\BotanicamTrainer'
RESOURCE_URL          = 'http://128.111.185.26:8080/data_service/00-re326BRuW68V4fsuJ3Vopc'
TAGS                  = 'Genus'
FEATURE_NAME          = 'CLD'
CLASSIFICATION_METHOD = 'svm'

if __name__ == '__main__':
    
    if not os.path.exists('TestStaging'):
        os.mkdir('TestStaging')
    os.mkdir(STAGING_PATH)
    call_list = [
                 'python',
                 'BotanicamTrainer.py',
                 '--user=%s'%USER,
                 '--pwd=%s'%PASS,
                 '--root=%s'%ROOT,
                 '--module_dir=%s'%MODULE_DIR,
                 '--staging_path=%s'%STAGING_PATH,
                 '--resource_url=%s'%RESOURCE_URL,
                 '--Tags=%s'%TAGS,
                 ] 
    
    print 'Call: %s'%' '.join(call_list)
    subprocess.call( ' '.join(call_list), shell=True)
    
    print 'Classificatin complete!'