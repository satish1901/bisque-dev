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
from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
from pylons.controllers.util import abort

import bq
from bq import data_service
from bq.core.service import ServiceController
from bq.core import identity

from bq.util.hash import is_uniq_code

log = logging.getLogger('bq.preference')



LEVEL = {
            'system':0,
            'user':1,
            'resource':2
         }





#TagValueNode: leaf node is a node no other tag resources in its first level children
#    - value: the value of the tag resource (in prepartation for .06 xml syntax change since the value will not be stored in he attribute node)
#    - node_attrib: dictionary of the node attributes for the node
#    - sub_node: list of sub nodes attached to the TagValueNode
TagValueNode = namedtuple('TagValueNode',['value','node_attrib','sub_node'])
TagValueNode.__new__.__defaults__ = ('', {}, [])

#TagNameNode: parent node is a node with tag resources in its first level children (values will be removed during dict 2 etree conversion)
#    - sub_node_dict: stores an ordered dictionary of either TagValueNode or TagNomeNode referenced by the tag resource's name attribute
#    - node_attrib: dictionary of the node attributes for the node (Note: value attribute will be removed)
#    - sub_none_tag_node: list of none tag resource elements (ex. templates)
TagNameNode = namedtuple('TagNameNode',['sub_node_dict','node_attrib', 'sub_none_tag_node'])
TagNameNode.__new__.__defaults__ = (OrderedDict(), {}, [])

def mergeDocuments(current, new, attrib={}):
    """
        Merges two xml documents. Current document elements are replace with new document elements.
        
        
        @param: current - preference etree document
        @param: new - preference etree document
        @param: attrib - top level attribute for the new merged document
    """
    currentDict = to_dict(current)
    newDict = to_dict(new)
    
    def merge(new, current):
        #merges the new docucument to the current one
        for k in new.sub_node_dict.keys():
            if k in current.sub_node_dict: 
                #deals with the cases when the current needs to be merged with the new document
                #case 1: both current and new are parent nodes
                if (type(current.sub_node_dict[k]) is TagNameNode) and (type(new.sub_node_dict[k]) is TagNameNode):
                    node_attrib = new.sub_node_dict[k].node_attrib
                    #type and templates are added from the current node and all other attributes are appended from the
                    #new node
                    if 'type' in current.sub_node_dict[k].node_attrib:
                        node_attrib['type'] = current.sub_node_dict[k].node_attrib['type']
                    current.sub_node_dict[k] = TagNameNode(
                        sub_node_dict = current.sub_node_dict[k].sub_node_dict,
                        node_attrib = node_attrib,
                        sub_none_tag_node = current.sub_node_dict[k].sub_none_tag_node
                    )
                    #merge the parents' children
                    merge(new.sub_node_dict[k], current.sub_node_dict[k])
                    
                #case 2: both are leaf nodes
                elif (type(current.sub_node_dict[k]) is TagValueNode) and (type(new.sub_node_dict[k]) is TagValueNode):
                    #type and templates are added from the minor node and all other attributes are appended from the
                    #major node
                    node_attrib = new.sub_node_dict[k].node_attrib
                    if 'type' in current.sub_node_dict[k].node_attrib:
                        node_attrib['type'] = current.sub_node_dict[k].node_attrib['type']
                    current.sub_node_dict[k] = TagValueNode(
                        value = new.sub_node_dict[k].value,
                        node_attrib = node_attrib,
                        sub_node = current.sub_node_dict[k].sub_node
                    )
                
                #case 3: current node is a parent node and new node is a leaf
                elif (type(current.sub_node_dict[k]) is TagNameNode) and (type(new.sub_node_dict[k]) is TagValueNode):
                    # replaces the parent node of the current node with the leaf node
                    current.sub_node_dict[k] = TagValueNode(
                        value = new.sub_node_dict[k].value,
                        node_attrib = new.sub_node_dict[k].node_attrib,
                    )
                    
                #case 4: current node is a leaf node and new node is a parent
                elif (type(current.sub_node_dict[k]) is TagNameNode) and (type(new.sub_node_dict[k]) is TagValueNode):
                    #nothing is changed in the current node and the new node is skipped
                    #keeps users from modifying existing structure of the preferences
                    pass
                
            #deals with the case when the major document appends new nodes
            else:
                #add the child node to the document
                if (type(new.sub_node_dict[k]) is TagValueNode):
                    current.sub_node_dict[k] = TagValueNode(
                        value = new.sub_node_dict[k].value,
                        node_attrib = new.sub_node_dict[k].node_attrib,
                    )
                    
                #adds the parent node to the document with all of its children
                elif (type(new.sub_node_dict[k]) is TagNameNode):
                    current.sub_node_dict[k] = new.sub_node_dict[k]
                    
            #all nodes in the current are added to the document by default 
             
        return current
    
    m_dict = merge(newDict, currentDict)
    
    return to_etree(m_dict, attrib=attrib)


def to_dict(tree):
    """
        @param: etree 
        @return: preference dictionary structure
    """
    def build(tree):
        sub_node_dict = OrderedDict()
        sub_none_tag_node = []
        for e in tree:
            if e.tag == 'tag': #check if tag
                if len(e.xpath('tag'))<1:  #if nodes has no tag children
                    sub_node_dict[e.attrib.get('name','')] = TagValueNode(
                        value = e.attrib.get('value'),
                        node_attrib = e.attrib,
                        sub_node = e.getchildren(),
                    )
                else: #remove the value and add it as a parent node
                    if 'value' in e.attrib: e.attrib.pop('value')
                    sub_node_dict[e.attrib.get('name','')] = build(e)
            else: #append it to the parent node as a none tag element
                sub_none_tag_node.append(e)
        return TagNameNode(
            sub_node_dict = sub_node_dict,
            sub_none_tag_node = sub_none_tag_node,
            node_attrib = tree.attrib
        )
    return build(tree)


def to_etree(dictionary, attrib={}):
    """
        @param: preference dictionary structure
        @return: etree
    """
    def build(dict, node):
        for k in dict.keys():
            if type(dict[k]) is TagValueNode:
                subNode = etree.Element('tag', **dict[k].node_attrib)
                for e in dict[k].sub_node:
                    subNode.append(e)
            else:
                subNode = etree.Element('tag', **dict[k].node_attrib)
                for e in dict[k].sub_none_tag_node:
                    subNode.append(e) #adding none tag nodes to subnode
                build(dict[k].sub_node_dict, subNode)
            node.append(subNode)
        return node
    
    node = etree.Element('preference', **attrib)
    for e in dictionary.sub_none_tag_node:
        node.append(e)
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
                        attrib = current.sub_node_dict[nk].node_attrib
                        #add value and maybe type
                        attrib['value'] = new.sub_node_dict[nk].node_attrib.get('value', '')
                    current.sub_node_dict[nk] = TagValueNode(
                        value = new.sub_node_dict[nk].value,
                        node_attrib = attrib,
                        #non system preferences never get subnodes
                    )
                elif type(new.sub_node_dict[nk]) is TagNameNode:
                    build(new.sub_node_dict[nk], current.sub_node_dict[nk])
            else: #set new node
                if type(new.sub_node_dict[nk]) is TagValueNode:
                    attrib = {}
                    #add value, name and maybe type
                    attrib['name'] = new.sub_node_dict[nk].node_attrib.get('name', '')
                    attrib['value'] = new.sub_node_dict[nk].node_attrib.get('value', '')
                    current.sub_node_dict[nk] = TagValueNode(
                        value = new.sub_node_dict[nk].value,
                        node_attrib = attrib,
                        #non system preferences never get subnodes
                    )
                elif type(new.sub_node_dict[nk]) is TagNameNode:
                    current.sub_node_dict[nk] = new.sub_node_dict[nk]
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
    """
    service_type = "preference"

    @expose(content_type='text/xml')
    def _default(self, *arg, **kw):
        """
            The entry point for the system level preferences
        """
        admin_check = Any(in_group("admin"), in_group('admins')).is_met(request.environ)
        http_method = request.method.upper()
        if http_method == 'GET' and len(arg)<1:
            log.info('GET /preference -> fetching system level preference')
            return self.get(resource_uniq=None, level=0, **kw)
        elif http_method == 'PUT' and admin_check and len(arg)<1:
            if request.body: 
                return self.system_put(body=request.body, **kw)
        elif http_method == 'POST' and admin_check and len(arg)<1:
            if request.body:
                return self.system_post(resource=None, body=request.body, **kw)
        elif http_method == 'DELETE' and admin_check:
            path = arg.join('/')
            return self.system_delete(path=path, **kw)
        abort(404)
        
        
    @expose(content_type='text/xml')
    def user(self, resource_uniq=None, *arg, **kw):
        """
            The entry point for the user and resource level preferences
        """
        not_annon = not_anonymous().is_met(request.environ)
        http_method = request.method.upper()
        if resource_uniq:
            if is_uniq_code(resource_uniq):
                if http_method == 'GET':
                    log.info('GET /preference/user -> fetching user level preference')
                    return self.get(resource_uniq=resource_uniq, level=2, **kw)
                elif http_method == 'PUT' and not_annon:
                    if request.body:
                        return self.resource_put(resource_uniq, body=request.body, **kw)
                elif http_method == 'DELETE' and not_annon:
                    path = '/'.join(arg) #no path deletes the preference
                    return self.resource_delete(resource_uniq, path=path, **kw)
        else:
            if http_method == 'GET':
                log.info('GET /preference/user -> fetching resource level preference for %s',resource_uniq)
                return self.get(resource_uniq=resource_uniq, level=1, **kw)
            elif http_method == 'PUT' and not_annon:
                if request.body:
                    return self.user_put(body=request.body, **kw);
            elif http_method == 'DELETE' and not_annon:
                path = '/'.join(arg) #no path deletes the preference
                return self.user_delete(path=path, **kw)
        abort(404)
        
        
    def get(self, resource_uniq=None, level=0, **kw):
        """
            Returns the virtual prefence document of the requested document for the
            specified level
            
            @param: resource_uniq - the resource_uniq of the resource document to be fetched. Not required if 
            the level is 0-1. (default:None)
            @param: level - the level to cascade the virtual document. (default: 0)
                0: system
                1: user
                2: resource
            @param: kw - pass through query parameters to data_service
        """
        
        #check system preference
        system = data_service.get_resource('/data_service/system', view='full', wpublic=1)
        system_preference_list = system.xpath('//system/preference')
        if len(system_preference_list) > 0:
            system_preference = data_service.get_resource(system_preference_list[0].attrib.get('uri'), wpublic=1, **kw)
        else:
            system_preference  = etree.Element('preference') #no preference found
        if level <= LEVEL['system']:
            return etree.tostring(system_preference)
        
        #check user preference
        user = self.get_current_user(view='full')
        user_preference_list = user.xpath('preference')
        if len(user_preference_list)>0: #if user is not signed in no user preferences are added
            user_preference = data_service.get_resource(user_preference_list[0].attrib.get('uri'), **kw)
            if not user_preference: #handles a bug in the data_service with permissions and full verse deep views
                user_preference = etree.Element('prefererence')
            attrib = {}
            if 'clean' not in kw.get('view', ''):
                attrib = system_preference.attrib
            user_preference = mergeDocuments(system_preference, user_preference, attrib=attrib)
        else:
            user_preference  = system_preference
        
        if level <= LEVEL['user']:
            if 'clean' not in kw.get('view', ''):
                user_preference.attrib['uri'] = request.url.replace('&','&amp;')
                user_preference.attrib['owner'] = user.attrib.get('uri', system_preference.attrib.get('owner', ''))
            return etree.tostring(user_preference)
        
        #check resource preference
        resource = data_service.get_resource('/data_service/%s'%resource_uniq, view='full')
        if not resource:
            abort(404)
        
        resource_preference_list = resource.xpath('preference')
        if len(resource_preference_list)>0:
            resource_preference = data_service.get_resource(resource_preference_list[0].attrib.get('uri'), **kw)
            if not resource_preference: #handles a bug in the data_service with permissions and full verse deep views
                resource_preference = etree.Element('prefererence')
            attrib = {}
            if 'clean' not in kw.get('view',''):
                attrib.update(user_preference.attrib)
                attrib.update(resource_preference.attrib)
            resource_preference = mergeDocuments(user_preference, resource_preference, attrib=attrib)
        else:
            resource_preference = user_preference
        
        #check annotations preference
        annotation = self.get_current_user_annotation(resource_uniq, view='full')
        #annotation_resource = data_service.get_resource('/data_service/annotation/%s'%annotation_uniq, view='full')
        resource_preference_list = annotation.xpath('preference')
        if len(resource_preference_list)>0:
            annotation_preference = data_service.get_resource(resource_preference_list[0].attrib.get('uri'), **kw)
            attrib = {}
            if 'clean' not in kw.get('view', ''):
                attrib.update(resource_preference.attrib)
                attrib.update(annotation_preference.attrib)
            annotation_preference = mergeDocuments(resource_preference, annotation_preference, attrib=attrib)
        else:
            annotation_preference = resource_preference
            
        if level <= LEVEL['resource']:
            if 'clean' not in kw.get('view', ''):
                annotation_preference.attrib['uri'] = request.url.replace('&','&amp;')
                annotation_preference.attrib['owner'] = user.attrib.get('uri', resource.attrib.get('owner', ''))
            return etree.tostring(annotation_preference)
        #raise exception level not known
    
    
    def get_current_user(self, **kw):
        """
            get_current_user
            
            Looks up and fetches the current users document. If no user document is
            found and empty user document is turned.
            
            @param: kw - pass through query parameters to data_service
            @return: etree element
            
        """
        user =  request.identity.get('user')
        if user:
            u = data_service.query(resource_type='user', name=user.user_name, wpublic=1)
            user_list = u.xpath('user')
            if len(user_list)>0:
                return data_service.get_resource('/data_service/%s'%u[0].attrib.get('resource_uniq'), **kw)
        return etree.Element('user') #return empty user
    
    
    def get_current_user_annotation(self, resource_uniq, **kw):
        """
            get_current_user_annotation
            
            Get the annotation document for the provided resource_uniq under the current user. \
            If none found will return an empty annotation document
            
            @param: resource_uniq 
            @param: kw - pass through query parameters to data_service
            
            @return: etree element
        """
        annotation_resource = data_service.get_resource('/data_service/annotation', view='short')
        annotation = annotation_resource.xpath('annotation[@value="%s"]'%resource_uniq)
        if len(annotation)>0:
            log.debug('Annotation document found for document (%s) at /%s'%(resource_uniq,annotation[0].attrib.get('resource_uniq')))
            return data_service.get_resource('/data_service/%s'%annotation[0].attrib.get('resource_uniq'), **kw)
        else:
            log.debug('No annotation document found for document (%s)'%resource_uniq)
            return etree.Element('annotation', value=resource_uniq)
    
    def strip_attributes(self, xml):
        """
        """
        def strip(node):
            for a in node.attrib.keys():
                if a not in set(['name','value','type']):
                    del node.attrib[a]
            for n in node:
                strip(n)
            return node
                
        return strip(xml)
    
    def system_post(self, path=None, body=None, **kw):
        """
            Creates a new preferences or merges the existing one with
            the document provided
            Only admin can change the system level
            the user has to be logged in to make any changes
            
            @param: path
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
            
            @param: path
            @param: body
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
        """
            user_put
            
            Merges preference document put to the preference on the user current sign in user document provided.
            
            @param: body - an xml string of the element being posted back (default: None)
            @param: kw - pass through query parameters to data_service
        """
        try:
            new_preference_etree = etree.fromstring(body)
        except etree.XMLSyntaxError:
            abort(400, 'XML parsing error')
        
        #strip body of all none name, value, tag elements
        new_preference_etree = self.strip_attributes(new_preference_etree)
        
        if new_preference_etree.tag == 'preference':
            #user = data_service.get_resource('/data_service/user', view='full')
            user = self.get_current_user(view='full')
            if 'name' in user.attrib:
                user_preference_list = user.xpath('preference')
            else:
                #raise error
                log.debug('User was not found')
                abort(404)
            
            if len(user_preference_list)>0:
                log.debug('Found user preference.')
                user_preference = data_service.get_resource(user_preference_list[0].attrib['uri'], view='deep')
                user_preference_uri = user_preference_list[0].attrib['uri']
                attrib = {'uri':user_preference_uri}
            else: #no preference found, create a new preferences
                log.debug('No user preference found. Creating new preference resource for user.')
                user_preference = etree.Element('preference')
                attrib = {}
            #merging the new and current user preference documents
            current_preference_etree = update_level(new_preference_etree, user_preference, attrib=attrib)
            user.append(current_preference_etree)
            log.debug('Updating user preference.')
            data_service.update_resource(user.attrib.get('resource_uniq'), new_resource=user)
            return self.get(uniq=None, level=1, **kw) #return the new merged document
        abort(404)
        
        
    def user_delete(self, path=None, **kw):
        """
            user_delete
            
            Deletes the preference resource from the user current sign in user document or the element to the path 
            provided in this document
            
            @param: path - path after preferences to the document element to be deleted (default: None)
            @param: kw - pass through query parameters to data_service
        """
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
        
    
    def resource_put(self, resource_uniq, body=None, **kw):
        """
            resource_put
            
            Merges preference document put to the preference on the resource document provided.
            
            @param: resource_uniq - the resource_uniq to document being addressed
            @param: body - an xml string of the element being posted back(default: None)
            @param: kw - pass through query parameters to data_service
        """
        try:
            new_preference_etree = etree.fromstring(body)
        except etree.XMLSyntaxError:
            abort(400, 'XML parsing error')
        #strip body of all none name, value, tag elements
        new_preference_etree = self.strip_attributes(new_preference_etree)
        
        if new_preference_etree.tag == 'preference':
            resource = data_service.resource_load(resource_uniq, action=RESOURCE_EDIT, view='full')
            if resource:
                log.debug('Reading preference from resource document.')
                resource_preference_list = resource.xpath('preference')
            else:
                log.debug('Reading preference from resource annotation document.')
                resource = self.get_current_user_annotation(resource_uniq)
                if 'resource_uniq' in resource.attrib:
                    resource_preference_list = resource.xpath('preference')
                else: #create annotations document
                    log.debug('No annotation document found. Creating an annotation for document at (%s)'%resource_uniq)
                    resource = data_service.new_resource(resource)
                    resource_preference_list = []
                
            if len(resource_preference_list)>0: #merge the documentes
                resource_preference_uri = resource_preference_list[0].attrib.get('uri')
                log.debug('Preference found at %s' % resource_preference_uri)
                resource_preference = data_service.get_resource(resource_preference_uri, view='deep')
                attrib = {'uri': resource_preference_uri}
            else: #create a new preferences
                log.debug('No resource preference found. Creating new preference resource for resource: %s'%resource.attrib.get('resource_uniq'))
                resource_preference = etree.Element('preference')
                attrib = {}
            
            current_preference_etree = update_level(new_preference_etree, resource_preference, attrib=attrib)
            resource.append(current_preference_etree)
            data_service.update_resource('data_service/%s' % resource.attrib.get('resource_uniq'), new_resource=resource)
            return self.get(resource_uniq=resource_uniq, level=2, **kw) #remerge
        log.debug('Preference was not found!')
        abort(404)
    
    
    def resource_delete(self, resource_uniq, path=None, **kw):
        """
            Removes the tag on the level requested. If there is not 
            tag nothing happens. Returns back the updated document.
            Allows the default value to be set for the level above.
            
            @param: resource_uniq - the resource_uniq to document being addressed
            @param: path - path after preferences to the document element to be deleted
            @param: kw - pass through query parameters to data_service
        """
        # get the preference resource
        resource = data_service.resource_load(resource_uniq, action=RESOURCE_EDIT, view='full')
        if resource:
            log.debug('Reading preference from resource document.')
            resource_preference_list = resource.xpath('preference')
        else:
            log.debug('Reading preference from resource annotation document.')
            resource = self.get_current_user_annotation(resource_uniq, view='deep')
            if resource:
                resource_preference_list = resource.xpath('preference')
            else:
                log.debug('Preference was not found!')
                abort(404)
        
        # search for resource to delete
        if len(resource_preference_list)>0:
            preference_location = resource_preference_list[0].attrib.get('uri')
            log.debug('Preference found at %s'%preference_location)
            if path:
                preference = data_service.get_resource(preference_location, view='deep')
                if len(preference.xpath('//tag[@uri="%s"]'%(preference_location+'/'+path))) == 1:
                    data_service.del_resource(preference_location+'/'+path)
                    log.info('Deleted (%s) preference tag at %s'%(resource_uniq, preference_location+'/'+path))
                    return
            else:
                data_service.del_resource(preference_location)
                log.info('Deleted (%s) preference document'%resource_uniq)
                return
        log.debug('Preference was not found!')
        abort(404)

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
