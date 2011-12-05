 ###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

  Top level web entry point for bisque system

"""

import os
import sys
import random
import logging

import pkg_resources

from urllib import urlencode
from StringIO import StringIO
from lxml import etree

from pylons import app_globals
from pylons.i18n import ugettext as _, lazy_ugettext as l_, N_
from pylons.controllers.util import abort

import tg
from tg import expose, flash, redirect, require
from tg import config, tmpl_context as c
from repoze.what import predicates


import bq
from bq.core.service import ServiceController, service_registry
from bq.client_service import model
from bq.core.exceptions import IllegalOperation
import bq.release as __VERSION__

import aggregate_service
from bq import image_service
from bq import data_service


log = logging.getLogger('bq.client_service')


#  Allow bq.identity to be accessed from templates
#def addBisqueToTemplate(root_vars):
#    bq = dict (identity=bisquik.identity)
#    root_vars.update (dict (bq=bq))
#
#turbogears.view.root_variable_providers += [addBisqueToTemplate]



class ClientServer(ServiceController):
    service_type = "client_service"
    
    def viewlink(self, resource):
        return self.baseuri + "/view?" + urlencode ({'resource': resource})


    @expose(content_type="text/xml")
    def version(self):
        response = etree.Element('resource', type='version')
        etree.SubElement (response, 'tag', name='version', value=__VERSION__)
        server = etree.SubElement (response, 'tag', name='server')
        
        #etree.SubElement (server, 'tag', name='environment', value=config.get('server.environment'))
        return etree.tostring(response)

    @expose(template='bq.client_service.templates.welcome')
    def index(self, **kw):
        log.info("WELCOME")
        wpublic = kw.pop('wpublic', not bq.core.identity.current)
        pybool = {'True': 'true', 'False': 'false'}
        welcome_tags = config.get ('bisque.welcome_tags', "")
        welcome_message = config.get ('bisque.welcome_message', "Welcome to the Bisque image database")
        image_count = aggregate_service.count("image", wpublic=wpublic)

        thumbnail = None
        imageurl = None
        if image_count:
            im = random.randint(0, image_count-1)
            image = aggregate_service.retrieve("image", view=None, wpublic=wpublic)[im]
            imageurl = self.viewlink(image.attrib['uri'])
            #thumbnail = image.attrib['src'] +'?thumbnail'
            thumbnail = "/image_service/images/%s?thumbnail" % image.get('resource_uniq')
       
        return dict(imageurl=imageurl,
                    thumbnail=thumbnail,
                    wpublic = wpublic,
                    wpublicjs = pybool[str(wpublic)],
                    welcome_tags = welcome_tags,
                    welcome_message = welcome_message
                    )

    @expose(template='bq.client_service.templates.browser')
    def browser(self, **kw):
        #query = kw.pop('tag_query', None)
        c.commandbar_enabled = False
        user = bq.core.identity.get_user()
        if user:
            wpublicVal='false'
        else:
            wpublicVal='true'
        
        #log.debug ('DDDDDDDDDDDDDDDDDDDDDD'+query)
        return dict(query=kw.pop('tag_query', None),
                    layout=kw.pop('layout', None),
                    tagOrder=kw.pop('tag_order', None),
                    tagQuery=kw.pop('tag_query', None),
                    offset=kw.pop('offset', None),
                    dataset=kw.pop('dataset', None),
                    search=0,
                    resource = "",
                    user_id = "",
                    page = kw.pop('page', 'null'),
                    view  = kw.pop('view', ''),
                    count = kw.pop ('count', '10'),
                    wpublic = kw.pop('wpublic', wpublicVal),                    
                    analysis = None)

    
    
    
    # Test
    
    @expose(template='bq.client_service.templates.test')
    def test(self):
        """from bq.export_service.controllers.tar_streamer import TarStreamer
        tarStreamer = TarStreamer() 
        tarStreamer.sendResponseHeader('Bisque.tar')
        return tarStreamer.stream(['C:\\Python27\\TarStreamer\\file1.tif', 'C:\\Python27\\TarStreamer\\file2.tif', 'C:\\Python27\\TarStreamer\\file3.tif'])
        """
        return dict()
        
    @expose(content_type="text/xml")
    def images(self, **kw):
        log.debug ("keyargs " + str(kw))
        query = kw.pop('tag_query', None)
        view=kw.pop('view', 'short')
        wpublic = kw.pop('wpublic', not bq.core.identity.not_anonymous())
        offset = int(kw.pop('offset', 0))
        limit = int(kw.pop('limit', 10))

        if view=='count':
            response = etree.Element('response')	
            image_count = aggregate_service.count("image", tag_query = query, wpublic=wpublic)
            etree.SubElement (response, 'count', value=str(image_count))
            return etree.tostring(response)


        response = etree.Element('response')
        images = aggregate_service.query("image" ,
                                         tag_query=query,
                                         view=view,
                                         wpublic=wpublic, **kw)

        for i in images[offset:offset+limit]:
            response.append(i)

        return etree.tostring(response)


    @expose (content_type="application/xml")
    def services(self):
        resource = etree.Element ('resource', uri=tg.url('/services'))
        for service_type, service_list in service_registry.items():
            for service in service_list:
                etree.SubElement (resource, 'tag', name=service_type, value=service.uri)
        
        #tg.response.content_type = "text/xml"
        return etree.tostring(resource)
        


    @expose("bq.import_service.templates.upload")
    @require(predicates.not_anonymous())
    def upload(self, msg="", link = "", **kw):
        """ Show upload form with an optional message """
        return dict(msg = msg, link = link, menu_options = dict (commandbar_enabled=False))
    
    @expose()
    @require(predicates.not_anonymous())
    def upload_handler (self, uploaded = None, **kw):
        log.debug ('upload_handler:' + str (uploaded) +  str(kw))
        upload_filename = os.path.split(uploaded.filename)[1]

        info = image_service.new_image(src=uploaded.file, name=upload_filename)
        if info==None:
            image=None
            raise BQException(_('unable to save file'))
        
        image = data_service.new_image(**info)
        tags = etree.Element('request')
        etree.SubElement(tags, 'tag', name="filename", value=upload_filename)
        data_service.append_resource(image, tree=tags)

        redirect("/client_service/upload",
                 msg="Upload success",
                 link = self.viewlink (image.get('uri')))

    @expose("bq.client_service.templates.view")
    def view(self, **kw):
        query = ''
        resource=kw.pop('resource', None)
        user = bq.core.identity.get_user()
        if user:
            user = data_service.uri() + str(user)
        else:
            user =''

        # Dispatch to controller or Choose template/widgets to
        # instantiate on the viewer by the type of the resource.  ,
        # tag_views=None, wpublic = None, search = None) Have a table
        # of template_name or dispatchable methods (i.e. other classes
        # or controllers) that can be used to generate the proper page
        # for this resource.  Defaults to simple resource display such
        # that the client decides the layout (ResourceDispatch in javascript)

        return dict(resource=resource, user=user) 

    @expose("bq.client_service.templates.view")
    def create(self, **kw):
        query = ''
        type_=kw.pop('type', None)

        user = bq.core.identity.get_user()
        if user:
            user = data_service.uri() + str(user)
        else:
            user =''

        if type_:
            resource = data_service.new_resource (type_, **kw)
        
            # Choose widgets to instantiate on the viewer by the type
            # of the resource.
            log.debug ('created %s  -> %s' % (type_, uri))
            return dict(resource=resource, user=user) #, tag_views=None, wpublic = None, search = None)
        raise IllegalOperation("create operation requires type")

    
    @expose("bq.client_service.templates.movieplayer")
    def movieplayer(self, **kw):
        resource=kw.pop('resource', None)
        return dict(resource=resource)    

    @expose("bq.client_service.templates.help")
    def help(self, **kw):
        resource=kw.pop('resource', None)
        return dict(resource=resource)    


    @expose(content_type="text/xml")
    @require(predicates.not_anonymous())
    def upload_files(self, **kw):
        """Upload files to the blob server
        :param kw: A keyword dictionary of file arguments.

        Each argument should be a readable file uploaded as as
        multipart form.  The files will be stored in the blob server
        and a url list will be returned.
        """
        params = dict (kw)

        response = etree.Element('resource', type='uploaded')
        for f in params.values():
            try:
                info = image_service.new_file(src=f.file, name=f.filename)
                etree.SubElement (response, 'resource',
                                  name=f.filename,
                                  type='file', 
                                  src = info['src'])
                #uploadfilter.upload_finished (f.file, f.filename)

            except Exception, e:
                log.warn('during upload of %s: %s' % (f.filename, e))
                continue
            
        return etree.tostring(response)
            
    @expose(content_type="text/xml")
    @require(predicates.not_anonymous())
    def upload_images(self, **kw):
        """Recieve a multipart form with images and possibly tag documents

        :param kw: A keyword dictionary of file arguments.  The
        arguments are organized as follows: Each datafile and its tag
        document are associated by the parameters named 'x' and
        'x_tags' where x can be any string. 
        
        """
        params = dict (kw)
        files = []
        for pname, f in params.items():
            if (pname.endswith ('_tags')): continue
            if hasattr(f, 'file'):
                # Append a tuple ( imagefile, tagfile )
                files.append ( ( f, params.get (pname+'_tags', None)) )

        #images = []
        response = etree.Element ('resource', type='uploaded')
        for image, tags in files:
            filename = os.path.split(image.filename)[1]
            src = image.file
            info = image_service.new_image(src=src, name=filename)
            #uploadfilter.upload_finished(src, filename)
            if info:
                # Check for extra tags
                resource = etree.Element('image')
                etree.SubElement(resource, 'tag', name="filename", value=filename)
                if tags is not None:
                    tagresource = etree.parse (tags.file).getroot()
                    #uploadfilter.upload_finished(tags.file, tags.filename)

                    if tagresource.tag == 'resource':
                        resource.extend (tagresource.getchildren())
                log.info ("NEW IMAGE %s <= %s" % (info, etree.tostring(resource)))
                image = data_service.new_image(resource = resource, **info)
                #images.append (image)
                response.append (image)
        
        return etree.tostring(response)

    @expose()
#    @identity.require(identity.not_anonymous())
    def upload_raw_image(self, **kw):
        '''Upload a raw image:  required parameter accepted x,y,z,t,c and format
           format should be a string with the order of the bytes i.e.  format=XYZTC
          '''
        #srv = controllers.Root.imgsrv
        log.info('upload_raw_Image: '+str(kw))
        uploaded = kw.pop('upload', None)
        if uploaded is not None:
            log.debug( 'upload_image' + str(uploaded.filename) )
            perm = int( kw.pop('userPerm', 1) )
            log.debug ("calling %s" % (image_service.new_image))
            info = image_service.new_image(src=uploaded.file, name=uploaded.filename, userPerm=perm, **kw)
            log.debug('Image INFO: '+str(info))
            resource = etree.Element('image')
            etree.SubElement(resource, 'tag', name="filename", value=filename)
            image = data_service.new_image(resource = resource, **info)
            return  image.get('uri')
        return ""



class Garbage(ServiceController):

    @expose(content_type="text/xml")
    def dir(self, **kw):
        type_ = kw.pop('type', None)
        query = kw.pop('tag_query', None)
        tag_view=kw.pop('tag_view', None)
        offset = int(kw.pop('offset', 0))
        limit = int(kw.pop('limit', 10))
        response = etree.Element('response')
        if type_:
            resources = aggregate_service.query(type_ ,
                                                tag_query=query,
                                                view=tag_view,
                                                wpublic=None, **kw)
            for i in resources[offset:offset+limit]:
                response.append(i)
        return etree.tostring(response)


#    @expose('bisquik.templates.inlineSearch')
#    @paginate('items')
#    def inlineSearch(self,  **kw):
#        query = kw.pop('query', '')
#        wpublic = kw.pop('wpublic', not identity.not_anonymous())##
#
#        images = aggregate_service.query("image" , tag_query=query, view='full', wpublic=wpublic)
#        return dict(items=images, query=query, item_count = len(images),
#                    wpublic = wpublic
#                    )

    @expose("bisquik.templates.view_image")
    def view(self, **kw):
        query = ''
        resource=kw.pop('resource', None)
        user = bisquik.identity.get_user()
        if user:
            user = data_service.uri() + str(user)
        else:
            user =''

        # Dispatch to controller or Choose template/widgets to
        # instantiate on the viewer by the type of the resource.  ,
        # tag_views=None, wpublic = None, search = None) Have a table
        # of template_name or dispatchable methods (i.e. other classes
        # or controllers) that can be used to generate the proper page
        # for this resource.  Defaults to simple resource display such
        # that the client decides the layout (ResourceDispatch in javascript)

        return dict(resource=resource, query=query, analysis=1, user=user) 

       

#     @expose("bisquik.templates.upload_image")
#     @identity.require(identity.not_anonymous())
#     def upload(self, msg="", **kw):
#         """ Show upload form with an optional message """
#         query = ''
#         if (kw.has_key('link')):
#             return dict(message=msg, link=kw['link'], query=query, 
#                         wpublic = None,
#                         search = None,
#                         analysis = None)
#         else:
#             return dict(message=msg, link=False, query=query, 
#                         wpublic = None,
#                         search = None,
#                         analysis = None)
 
    @expose(template="kid:bisquik.templates.testhttp")
    def testhttp(self):
        return dict()
 

    @expose()
    #@identity.require(identity.not_anonymous())
    def upload_handler(self, **kw):
        # handle the group uploads from static/js/uploader.js
        # a userfilecount var tells how many images are being uploaded now
        # for each of these, there is a userfile0,userfile1, etc.
        # for each userfile, such as userfile0, there is an img0name0,img0name1, img0name2, etc.
        # for each userfile, such as userfile0, there is an img0value0,img0value1, img0value2, etc.
        #m ='image recieved:<br\>'
        #a = kw.pop('userfile0')
        #log.debug("upload_handler:" + str(a.__dict__))
        
        upload_filename = ''              
        for i in xrange (int( kw['userfilecount']) ):
            si = str(i);
            uploaded = kw['userfile' + si]
            upload_filename = uploaded.filename              
            info = image_service.new_image(src=uploaded.file, name=uploaded.filename)
            if info==None:
                image=None
                continue
            image = data_service.new_image(**info)
            tags = etree.Element('request')
            etree.SubElement(tags, 'tag', name="filename", value=uploaded.filename)
            for j in  xrange(int( kw['img' + si + 'tagcount']) ):
                sj =str(j)
                tx = etree.SubElement(tags, 'tag', 
                                      name = kw['img' + si +'name' + sj],
                                      value= kw['img' + si + 'value' + sj],
                                      index= sj)
            log.debug ("CS: appending " + etree.tostring(tags))
            data_service.append_resource(image, tree=tags)

        if image is None:   
            if ('xml' in kw): return 'Format not supported'              
            else: return self.upload(msg="Format is not supported for '%s', upload canceled..."%(upload_filename), link = None)           
        
        if ('xml' in kw):
           return image.get('uri')
        else:
           return self.upload(msg="Image upload successful for '%s'"%(upload_filename),
                              link = self.imagelink (image.get('uri')))

    @expose()
#    @identity.require(identity.not_anonymous())
    def upload_image(self, **kw):
        """Entry point for simple image uploads from clients """
        return self.upload_raw_image (**kw)

    
    #####################################################################################################    
    # NEW IMAGE UPLOADER WITH PROGRESS BAR
    #####################################################################################################
        
    @expose("bisquik.templates.upload_image_progress")
#    @identity.require(identity.not_anonymous())
    def upload_progress(self, msg="", **kw):
        """ Show upload form with an optional message """
        query = ''
        if (kw.has_key('link')):
            return dict(message=msg, link=kw['link'], query=query, 
                        wpublic = None,
                        search = None,
                        analysis = None)
        else:
            return dict(message=msg, link=False, query=query, 
                        wpublic = None,
                        search = None,
                        analysis = None)    

    @expose("bisquik.templates.s3_discovery")
#    @identity.require(identity.not_anonymous())
    def s3_discovery(self, msg="", **kw):
        """ Show upload form with an optional message """
        query = ''
        if (kw.has_key('link')):
            return dict(message=msg, link=kw['link'], query=query, 
                        wpublic = None,
                        search = None,
                        analysis = None)
        else:
            return dict(message=msg, link=False, query=query, 
                        wpublic = None,
                        search = None,
                        analysis = None)    

    
    @expose()
    def upload_handler_progress(self, uploaded, **kw):
        """ Do something with form values and re-show the upload form. """


        # Save any files that were uploaded (ignoring empty form fields)
        if len(uploaded.filename) > 0:
            #self.save_file(os.path.join(tmpdir, os.path.basename(uploaded.filename)), uploaded.file)
            upload_filename = uploaded.filename              
            info = image_service.new_image(src=uploaded.file, name=uploaded.filename)
            # Tell UploadFilter that this transfer is done.
            uploadfilter.upload_finished(uploaded.file, uploaded.filename)
            if info:
                resource = etree.Element('image')
                etree.SubElement(resource, 'tag', name="filename", value=upload_filename)
                image = data_service.new_image(resource = resource, **info)
                
                if ('xml' in kw):
                   #return "<response><image uri='%s' /></response>"%( image.get('uri') )
                   return image.get('uri')                
                
                return self.upload_progress(msg="Image upload successful for '%s'"%(upload_filename), link = self.imagelink (image.get('uri')))
            else:
                if ('xml' in kw): 
                    return "<response><error>Format is not supported for '%s', upload canceled...</error></response>"%(upload_filename)                
                return self.upload_progress(msg="Format is not supported for '%s', upload canceled..."%(upload_filename), link = None)           
                
        else:
            if ('xml' in kw): 
                return "<response><error>Error while uploading file, upload canceled...</error></response>"  
            return self.upload_progress(msg="Error while uploading file, upload canceled...", link = None)                   
            
                    
    #@expose(allow_json=True)
    def get_upload_stats(self, filename, **kw):
        """ Returns a dict containing stats on the active upload """

        log.debug ('upload_stats: %s' % str (cherrypy.file_transfers) )
        # Get stats from UploadFilter.
        # Firefox has a quirky behavior where the POSTed filename
        # contains the path info while the fileinput.value (accessed
        # via javascript) does not contain the path info, so look for
        stats = uploadfilter.get_upload_stats(filename)

        # Assert that UploadFilter is tracking something named filename.
        if not stats:
            # If there are no entries for our IP Address and Filename, then we have nothing.
            turbogears.flash("No active file uploads. IP: %s, FILENAME: %s" % \
                             (cherrypy.request.remote_addr, filename))
            return dict()


            # If the file transfer is finished, the dict should show
            # this, avoiding the odd results that UploadFilter will
            # spit back after a transfer is complete.
        if stats.transferred == True:
            upload_stats_in_kb = dict(filename=filename, speed=1, total=stats.pre_sized, \
                                      transferred=stats.pre_sized, eta=0, percent_done=100)
        else:
            # Convert stats to KBs and save in a new dict called upload_stats_in_kb
            upload_stats_in_kb = {}
            upload_stats_in_kb['filename'] = filename
            upload_stats_in_kb['speed'] = '%9.2f' % (stats.speed / 1024.0) # kb/s
            upload_stats_in_kb['total'] = '%9.2f' % (stats.pre_sized / 1024.0) # kb
            upload_stats_in_kb['transferred'] = '%9.2f' % (stats.transferred / 1024.0) # kb
            upload_stats_in_kb['eta'] = str(int(stats.eta)) # seconds to arrival
            upload_stats_in_kb['percent_done'] = "%d" % int(stats.transferred * 100 / stats.pre_sized)
        
        # Construct the html to display the stats visually
        upload_stats_in_kb['progressbar_xhtml'] = progressbar_template.serialize(**upload_stats_in_kb)
        # Return results as a dict
        return upload_stats_in_kb

    #####################################################################################################    
    # NEW IMAGE UPLOADER WITH PROGRESS BAR - end
    #####################################################################################################
    
    #the following 4 methods are preserved here for compatibility with older DN
    @expose()
    def savefile (self, upload, **kw):
        return dn_service.savefile(upload, **kw)

    @expose()
    def dn_upload(self, **kw):
        return dn_service.notify(**kw)       
            
    @expose()
    def dn_test_uploaded(self, **kw):
        return dn_service.test_uploaded(**kw)            

    @expose()
    def dn_http_upload(self, **kw):
        if 'uploaddir' in kw: kw.pop('uploaddir')
        return dn_service.notify(**kw)        
            
    
    @expose(content_type='text/xml')
    def query_db(self, **kw):
        url = kw.pop('url')
        url_response, content = request (url)
        return content

    @expose(content_type='text/xml')
    def proxy(self, **kw):
        url = kw.pop('url')
        url_response, content = request (url)
        return content


    @expose(content_type='text/xml')
    def monitor(self, **kw):
        try:
            '''url  - should be the address of  XML output of the GANGLIA System Monitor '''
            url = "http://hammer.ece.ucsb.edu:8651/"
            url_response, content = request (url)
            #log.debug (url_response)
            log.debug (content)
            return content
        except Exception, e:
            return "<error>We have a problem to get monitor XML : "  +str(e) + "</error>"
 

    @expose (content_type='text/xml')
    def config (self):
        ds = data_service.uri()
        ms = module_service.uri()
        #cs = client_service.uri()

        response = etree.Element ('resource', uri="/bisquik/config/")
        etree.SubElement (response, 'resource', uri= ds, type="data_server")
        etree.SubElement (response, 'resource', uri= ms, type="module_server")
        #etree.SubElement (response, 'resource', uri= cs, type="client_server")


        return etree.tostring(response)
        
    @expose(content_type='text/xml')
    def error_service(self):
        request = cherrypy.request
        clen = int(request.headers.get('Content-Length')) or 0
        xmldata = request.body.read(clen)
        req = etree.XML(xmldata)
        error = req[0]
        for n in error:
            if n.tag == 'email':
                email = n
            if n.tag == 'comments':
                comments = n
            if n.tag == 'message':
                message = n
                
        log.debug ("Error - user email: %s" %(email.text))
        log.debug ("Error - message: %s" %(message.text))
        log.debug ("Error -comments: %s" %(comments.text))        
        error_text = 'User Email: ' + str(email.text) + ' || Comments: ' + str(comments.text) + ' || Error Message: ' + str(message.text)
        
        self.sendMail( ['bisque-help@biodev.ece.ucsb.edu'], 'BISQUIK - Error Message', str(error_text), [] )
        log.debug (error_text)
        return '<response>OK</response>'   

    def sendMail(self, to, subject, text, files=[],server=None):
        assert type(to)==list
        assert type(files)==list
        #fro = "BISQUIK MEN :) <obara@ece.ucsb.edu>"
        fro = 'bisque-help@biodev.ece.ucsb.edu'

        if server is None:
            server = config.get ('bisquik.smtp_server')
        msg = MIMEMultipart()
        msg['From'] = fro
        msg['To'] = COMMASPACE.join(to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        msg.attach( MIMEText(text) )

        for file in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(file,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file))
            msg.attach(part)
        
        smtp = smtplib.SMTP(server, '25')
        smtp.sendmail(fro, to, msg.as_string() )
        smtp.close()
        log.debug ('Error has been sent ')


    @expose (content_type="text/xml")
    def finduri(self, hash=None):
        if not hash:
            request = cherrypy.request
            clen = int(request.headers.get('Content-Length') or 0 )
            if (clen<=0): return "<response/>"
            xmldata = request.body.read(clen)
            log.debug ("XML = " + xmldata)
            request = etree.XML(xmldata)
            image = request[0]
            hash  = image.attrib['hash']      
      
        uris = image_service.find_uris(hash)

        response = etree.Element ('response')
        for src_uri in uris:
            img_resp = data_service.retrieve ('image', src=src_uri)
            for image in img_resp.getiterator('image'):
                response.append (image)
        return etree.tostring(response)
    @expose("bisquik.templates.termsofuse")
    def termsofuse(self):
        return dict()
    @expose("bisquik.templates.privacypolicy")
    def privacypolicy(self):
        return dict()

    @expose()
    def social_service(self, **kw):
        return "<done />" 

    @expose (content_type='text/xml')
#    @identity.require(identity.not_anonymous())
    def begin_session (self, module_id, **kw):
        x = etree.XML ('<mex module="%s" />' % module_id )
        mex = module_service.begin_execute (x)
        return etree.tostring (mex)        


client_server = None
def initialize(uri):
    global client_server
    client_server = ClientServer(uri)
    return client_server

def uri():
    return client_server.baseuri
   
       
