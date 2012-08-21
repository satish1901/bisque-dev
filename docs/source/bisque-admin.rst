


Bisque Administration
=====================

.. toctree::
   :maxdepth: 2



Online Administration
---------------------
The online adminstrator can be found under in user menu under ``WebSite Admin`` when logged 
in as administrator.  There you can add or remove users or images and login as any user.
   



``bq-admin`` Command Reference
------------------------------

Bisque installation and configuration is controlled with the ``bq-admin`` command


``setup``
     Setup a bisque server or engine
     :: 
       bq-admin setup [engine]

``deploy``
     Prepare static files for deployment on a web server

``database``
     database commands that modify and check the integrity of the bisque database
     ::
       bq-admin database clean   

``module``
    Module commands for registration and removal of bisque modules
    ::
      bq-admin module register path/to/module/xml
        
``preferences`` 
    Initialize, read and/or update system config/preferences.xml 
    ::
      bq-admin preference init 
      bq-admin preference read 
      bq-admin preference save 
 


``server``
    Start/stop bisque servers and engine 
    :: 
      bq-admin server start 
      bq-admin server -v stop 


