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

"""
import os
import logging
from collections import namedtuple
from collections import OrderedDict
from datetime import datetime
from lxml import etree
from tg import expose, controllers, flash, url, response, request
from repoze.what.predicates import is_user, in_group, Any, not_anonymous

from pylons.controllers.util import abort

import bq
from bq import data_service
from bq.core.service import ServiceController
from bq.core import identity


log = logging.getLogger('bq.preference')



LEVEL = {
            'system':0,
            'user':1,
            'resource':2
         }


TagValueNode = namedtuple('TagValueNode',['value','node_attrib','sub_node'])
TagValueNode.__new__.__defaults__ = ('', {}, [])

TagNameNode = namedtuple('TagNameNode',['sub_node_dict','node_attrib', 'sub_none_tag_node'])
TagNameNode.__new__.__defaults__ = (OrderedDict(), {}, [])


def mergeDocuments(minorDoc, majorDoc):
    """
        Merges two xml documents. Minor elements are replace with major.
        
        @param: minorDoc - preference etree
        @param: majorDoc - preference etree
    """
    minorDocDict = to_dict(minorDoc)
    majorDocDict = to_dict(majorDoc)
    def merge(new, current):
        for k in new.sub_node_dict.keys():
            if k in current.sub_node_dict:
                if (type(current.sub_node_dict[k]) is TagNameNode) and (type(new.sub_node_dict[k]) is TagNameNode):
                    merge(new.sub_node_dict[k], current.sub_node_dict[k])
                elif (type(current.sub_node_dict[k]) is TagValueNode) and (type(new.sub_node_dict[k]) is TagValueNode):
                    current.sub_node_dict[k] = TagValueNode(
                        value = new.sub_node_dict[k].value,
                        node_attrib = new.sub_node_dict[k].node_attrib,
                        sub_node = current.sub_node_dict[k].sub_node
                    )
                elif (type(current.sub_node_dict[k]) is TagNameNode) and (type(new.sub_node_dict[k]) is TagValueNode):
                    current.sub_node_dict[k] = TagValueNode(
                        value = new.sub_node_dict[k].value,
                        node_attrib = new.sub_node_dict[k].node_attrib,
                    )
            else:
                if (type(new.sub_node_dict[k]) is TagValueNode):
                    current.sub_node_dict[k] = TagValueNode(
                        value = new.sub_node_dict[k].value,
                        node_attrib = new.sub_node_dict[k].node_attrib,
                    )
                elif (type(new.sub_node_dict[k]) is TagNameNode):
                    current.sub_node_dict[k] = new.sub_node_dict[k]
                
        return current
    m_dict = merge(majorDocDict, minorDocDict)
    
    return to_etree(m_dict, attrib=majorDoc.attrib)


def to_dict(tree):
    """
        @param: etree 
    """
    def build(tree):
        sub_node_dict = OrderedDict()
        sub_none_tag_node = []
        for e in tree:
            if e.tag == 'tag':
                if 'value' in e.attrib: #if it has a value it is an end node
                    sub_node_dict[e.attrib.get('name','')] = TagValueNode(
                        value = e.attrib.get('value'),
                        node_attrib = e.attrib,
                        sub_node = e.getchildren(),
                    )
                else: #continue to add names to the dictionary
                    sub_node_dict[e.attrib.get('name','')] = build(e)
            else:
                sub_none_tag_node.append(e)
        return TagNameNode(
            sub_node_dict = sub_node_dict,
            sub_none_tag_node = sub_none_tag_node,
            node_attrib = tree.attrib
        )
    return build(tree)


def to_etree(dictionary, attrib={}):
    """
        @param: etree
    """
    node = etree.Element('preference', **attrib)
    for e in dictionary.sub_none_tag_node:
        node.append(e)
    def build(dicti, node):
        for (k,v) in dicti.items():
            if type(v) is TagValueNode:
                subNode = etree.Element('tag', **v.node_attrib)
                for e in v.sub_node:
                    subNode.append(e)
            else:
                subNode = etree.Element('tag', **v.node_attrib)
                for e in v.sub_none_tag_node:
                    subNode.append(e)
                build(v.sub_node_dict, subNode)
            node.append(subNode)
        return node
    return build(dictionary.sub_node_dict, node)


def update_level(new_doc, current_doc, attrib={}):
    """
        prepares the new elements to be place in the preference
    """
    new_dict = to_dict(new_doc)
    current_dict = to_dict(current_doc)
    def build(new, current):
        for nk in new.sub_node_dict.keys():
            if nk in current.sub_node_dict: #set current node 
                if type(new.sub_node_dict[nk]) is TagValueNode: #over write the value node
                    if type(current.sub_node_dict[nk]) is TagValueNode:
                        #current.sub_node_dict[nk].node_attrib.update(new.sub_node_dict[nk].node_attrib)
                        attrib = current.sub_node_dict[nk].node_attrib
                        #add value and maybe type
                        attrib['value'] = new.sub_node_dict[nk].node_attrib.get('value', '')
                        if new.sub_node_dict[nk].node_attrib.get('type', ''):
                            attrib['type'] = new.sub_node_dict[nk].node_attrib.get('type', '')
                    current.sub_node_dict[nk] = TagValueNode(
                        value = new.sub_node_dict[nk].value,
                        node_attrib = attrib,
                        #non system preferences never get subnodes
                    )
                else: #assumes it a NameNode
                    build(new.sub_node_dict[nk], current.sub_node_dict[nk])
            else: #set new node
                if type(new.sub_node_dict[nk]) is TagValueNode:
                    current.sub_node_dict[nk] = TagValueNode(
                        value = new.sub_node_dict[nk].value,
                        node_attrib = new.sub_node_dict[nk].node_attrib,
                        #non system preferences never get subnodes
                    )
                else:
                    current.sub_node_dict[nk] = TagNameNode(
                        node_attrib = new.sub_node_dict[nk].node_attrib,
                    )
                    build(new.sub_node_dict[nk], current.sub_node_dict[nk])
        return current
    update_dict = build(new_dict, current_dict)
    return to_etree(update_dict, attrib=attrib)


class PreferenceController(ServiceController):
    """
        The preference controller is a central point for
        a special resource that cascades all the resource levels
        meant as guidence for the bique UI
        (System -> User -> all other Resource) providing 
        
        
        General Format of <preference> resource
        
        <preference>
            <tag name="UI Component"/>
                <tag name="UI preference name 1" value="preference value"/>
                    <template>
                        <tag name="template parameter name" value="template parameter value"/>
                        ...
                    </template>
                <tag name="sub UI component"/>
                    <tag name="sub UI preference name 1" value="preference value"/>
                ...
            ...
        </preference>
        
        Order must be consistant to cascade
    """
    service_type = "preference"

    #allow_only = Any(in_group("admin"), in_group('admins'))
    #allow_only = is_user('admin')
    #admin = BisqueAdminController([User, Group], DBSession)

    @expose(content_type='text/xml')
    def _default(self, *arg, **kw):
        """
            Returns system level preferences
        """
        admin_check = Any(in_group("admin"), in_group('admins')).is_met(request.environ)
        if request.method == 'GET':
            return self.get(resource_uniq=None, level=0, **kw)
        elif request.method == 'PUT' and admin_check:
            if request.body:
                return self.system_put(body=request.body, **kw)
        elif request.method == 'POST' and admin_check:
            if request.body:
                return self.system_post(resource=None, body=request.body, **kw)
        elif request.method == 'DELETE' and admin_check:
            path = arg.join('/')
            return self.system_delete(path=path, level=0, **kw)
        abort(404)
        
        
    @expose(content_type='text/xml')
    def user(self, resource_uniq=None, *arg, **kw):
        """
            checks user level
        """
        not_annon = not_anonymous().is_met(request.environ)
        if resource_uniq:
            if request.method == 'GET':
                return self.get(uniq=resource_uniq, level=2, **kw)
            elif request.method == 'PUT' and not_annon:
                if request.body:
                    return self.resource_put(uniq=resource_uniq, body=request.body, **kw)
            elif request.method == 'DELETE' and not_annon:
                path = arg.join('/') #no path deletes the preference
                return self.resource_delete(uniq=resource_uniq, path=path, **kw)
        else:
            if request.method == 'GET':
                return self.get(uniq=resource_uniq, level=1, **kw)
            elif request.method == 'PUT' and not_annon:
                if request.body:
                    return self.user_put(body=request.body, **kw);
            elif request.method == 'DELETE' and not_annon:
                path = arg.join('/') #no path deletes the preference
                return self.user_delete(path=path, **kw)
                
        abort(404)
        
        
    def get(self, uniq=None, level=0, **kw):
        """
            Merges all the documents
            @param: resource_uniq -
        """
        system = data_service.get_resource('/data_service/system', view='full', wpublic=1)
        system_preference_list = system.xpath('//system/preference')
        if len(system_preference_list) > 0:
            system_preference = data_service.get_resource(system_preference_list[0].attrib['uri'], wpublic=1, **kw)
        else:
            system_preference  = etree.Element('preference') #no preference found
        if level <= LEVEL['system']:
            return etree.tostring(system_preference)
        
        #user = data_service.get_resource('/data_service/user', view='full')
        user = self.get_current_user(view='full')
        user_preference_list = user.xpath('preference')
        if len(user_preference_list)>0: #if user is not signed in no user preferences are added
            user_preference = data_service.get_resource(user_preference_list[0].attrib['uri'], **kw)
            user_preference = mergeDocuments(system_preference, user_preference)
        else:
            user_preference  = system_preference
        
        if level <= LEVEL['user']:
            return etree.tostring(user_preference)
        
        resource = data_service.get_resource('/data_service/%s'%uniq, view='full')
        resource_preference_list = resource.xpath('preference')
        if len(resource_preference_list)>0:
            resource_preference = data_service.get_resource(resource_preference_list[0].attrib['uri'], **kw)
            resource_preference = mergeDocuments(user_preference, resource_preference)
        else:
            resource_preference = user_preference
            
        if level <= LEVEL['resource']:
            return etree.tostring(resource_preference)
        #raise exception level not known
    
    def get_current_user(self, **kw):
        bq_user =  request.identity.get('bisque.bquser')
        if bq_user:
            return data_service.get_resource('/data_service/%s'%bq_user.resource_uniq, **kw)
        else:
            return etree.Element('user') #return empty user
    
    
    def system_post(self, path=None, body=None, **kw):
        """
            Creates a new preferences or merges the existing one with
            the document provided
            Only admin can change the system level
            the user has to be logged in to make any changes
            
            @param: resource
            @param: body
        """
        preference_doc = etree.fromstring(body)
        if preference_doc.tag == 'preference' or path:
            systemList = data_service.get_resource('/data_service/system', view='full', wpublic=1) #if no system found this service will not work
            system_preference_list = systemList[0].xpath('preference')
            if len(system_preference_list) > 0:
                if path:
                    resource = data_service.update_resource(system_preference_list[0].attrib['uri']+'/'+path, preference_doc, **kw)
                else:
                    resource = data_service.update_resource(system_preference_list[0].attrib['uri'], preference_doc, **kw)
            else: #create a new preferences for the system
                systemList[0].uri
                resource = data_service.update_resource(systemList[0].uri, preference_doc, **kw)
                
        else:
            pass
            #raise
        return etree.tostring(resource)
    
    
    def system_put(self, path=None, body=None, **kw):
        """
            Replaces all the preferences with the document at the level
            Only admin can change the system level
            the user has to be logged in to make any changes
            
            @param: resource_uniq
            @param: doc
        """
        preference_doc = etree.fromstring(body)
        if preference_doc.tag == 'preference' or path:
            resource = data_service.get_resource('/data_service/system', view='full', wpublic=1)
            system_preference_list = resource[0].xpath('preference')
            if len(resource_preference_list)>0: #merge the documentes
                if path:
                    resource = data_service.update_resource(resource_preference_list[0].uri+'/'+path, preference_doc, **kw)
                else:
                    resource = data_service.update_resource(resource_preference_list[0].uri, preference_doc, **kw)
            else: #create a new preferences
                pass
                #raise
        else:
            pass
            #raise
        return etree.tostring(resource)
    
    
    def system_delete(self, path=None, **kw):
        """
            removes all or a part of the preferences
            Only admin can change the system level and 
            the user has to be logged in to make any changes
            
            @param: resource_uniq
            @param: doc
        """
        #requires admin privileges
        resource = data_service.get_resource('/data_service/system', view='full', wpublic=1)
        resource_preference_list = resource[0].xpath('preference')
        if len(resource_preference_list)>0:
            preference_location = resource_preference_list[0].uri
            if path:
                data_service.del_resource(preference_location+'/'+path)
            else:
                data_service.del_resource(preference_location)
        else:
            pass
            #raise
        return
    
    
    def user_put(self, body=None, **kw):
        new_preference_etree = etree.fromstring(body) #requires parsing error catch
        if new_preference_etree.tag == 'preference':
            user = data_service.get_resource('/data_service/user', view='full')
            if user:
                user_list = user.xpath('user')
                if len(user_list)>0:
                    user_uri = user_list[0].attrib['uri']
                    user_preference_list = user_list[0].xpath('preference')
                    user = user_list[0]
                else:
                    #user not found
                    abort(404)
            else:
                #raise error
                abort(404)
                #return
            
            if len(user_preference_list)>0: #merge the documentes
                user_preference = data_service.get_resource(user_preference_list[0].attrib['uri'], view='deep')
                current_preference_dict = to_dict(user_preference)
                user_preference_uri = user_preference_list[0].attrib['uri']
                attrib = {'uri':user_preference_uri}
            else: #create a new preferences
                user_preference = etree.Element()
                #current_preference_dict = {}
                attrib = {}
            current_preference_etree = update_level(new_preference_etree, user_preference, attrib=attrib)
            #new_preference_dict = to_dict(new_preference_etree)
            #current_preference_dict = update_level(new_preference_dict, current_preference_dict)
            #current_preference_etree = to_etree(current_preference_dict, attrib=attrib)
            user.append(current_preference_etree)
            data_service.update_resource(user_uri, new_resource=user)
            return self.get(uniq=None, level=1, **kw) #remerge
        abort(404)
        
        
    def user_delete(self, path=None, **kw):
        user = data_service.get_resource('/data_service/user', view='full')
        if user:
            user_list = user.xpath('user')
            if len(user_list)>0:
                user_uri = user_list[0].attrib['uri']
                user_preference_list = user_list[0].xpath('preference')
                user = user_list[0]
            else:
                #user not found
                abort(404)
        else:
            #raise error
            abort(404)
            
        if len(user_preference_list)>0:
            preference_location = user_preference_list[0].uri
            if path:
                data_service.del_resource(preference_location+'/'+path)
            else:
                data_service.del_resource(preference_location)
        else:
            abort(404)
        return
    
    def resource_put(self, uniq=None, path=None, body=None, **kw):
        """
            None admin put to a preference document.
            A resource put on the items preference.
        """
        resourceURL = {
            0: '/data_service/system',
            1: '/data_service/user',
            2: '/data_service/%s' % uniq,
        }
        new_preference_etree = etree.fromstring(body) #requires parsing error catch
        if new_preference_etree.tag == 'preference':
            resource = data_service.get_resource('/data_service/%s'%uniq, view='full')
            if resource:
                resource_preference_list = resource.xpath('preference')
            else:
                #raise error
                abort(404)
                #return
            
            if len(resource_preference_list)>0: #merge the documentes
                resource_preference = data_service.get_resource(resource_preference_list[0].attrib['uri'], view='deep')
                current_preference_dict = to_dict(resource_preference)
                resource_preference_uri = resource_preference_list[0].attrib['uri']
                attrib = {'uri':resource_preference_uri}
            else: #create a new preferences
                resource_preference = etree.Element()
                attrib = {}
            
            current_preference_etree = update_level(new_preference_etree, resource_preference, attrib=attrib)
            #new_preference_dict = to_dict(new_preference_etree)
            #current_preference_dict = update_level(new_preference_dict, current_preference_dict)
            #current_preference_etree = to_etree(current_preference_dict, attrib=attrib)
            resource.append(current_preference_etree)
            data_service.update_resource('data_service/%s'%uniq, new_resource=resource)
            return self.get(uniq=uniq, level=2, **kw) #remerge
        abort(404)
    
    def resource_delete(self, resource_uniq=None, path=None, level=0, **kw):
        """
            Removes the tag on the level requested. If there is not 
            tag nothing happens. Returns back the updated document.
            Allows the default value to be set for the level above.
        """
        resource = data_service.get_resource('/data_service/%s', view='full')
        
        if resource:
            resource_preference_list = resource.xpath('preference')
        else:
            abort(404)
            
        if len(resource_preference_list)>0:
            preference_location = resource_preference_list[0].uri
            if path:
                data_service.del_resource(preference_location+'/'+path)
            else:
                data_service.del_resource(preference_location)
        else:
            abort(404)
        return

def initialize(url):
    """ Initialize the top level server for this microapp"""
    log.debug ("initialize " + url)
    return PreferenceController(url)


#def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("bqserver")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'admin_service', 'public'))]



__controller__ = PreferenceController
__staticdir__ = None
__model__ = None
