import nose
from nose import with_setup
from nose import with_setup

from bqapi import bqnode
from bqapi.bqnode import BQResource, BQUser

from collections import OrderedDict
from lxml import etree

from bq.preference.controllers.service import mergeDocuments, to_dict, to_etree, update_level, TagValueNode, TagNameNode


class BQPreference(BQResource):
    TAG = xmltag = 'preference'
    xmlfields = ['uri', 'ts', 'resource_uniq']

class BQTemplate(BQResource):
    TAG = xmltag = 'template'
    xmlfields = []

def compare_dict(answer, result):
    """
        Compare Dict
        
        @param: answer - dict with TagValueNode elements and TagNameNode elements
        @param: result - dict with TagValueNode elements and TagNameNode elements
        
        @assert: checks if answer is equal to result
    """
    def compare(answer, result):
        assert (type(result) == TagNameNode), 'result not TagNameNode'
        assert (type(result) == TagNameNode), 'answer not TagNameNode'
        assert (answer.sub_node_dict.keys() == result.sub_node_dict.keys()), 'answer does not have the same keys or order as results'
        assert len(answer.sub_none_tag_node) == len(result.sub_none_tag_node), 'Sub tag nodes not the same length'
        
        #check untagged sub node
        for i,t in enumerate(answer.sub_none_tag_node):
            compare_etree(answer.sub_none_tag_node[i], result.sub_none_tag_node[i])
        
        for k in answer.sub_node_dict.keys():
            assert type(result.sub_node_dict[k]) == type(answer.sub_node_dict[k]), ('%s types are not equal'%k)
            if type(result.sub_node_dict[k]) == TagNameNode:
                #check attribute node
                result_attrib = result.sub_node_dict[k].node_attrib
                answer_attrib = answer.sub_node_dict[k].node_attrib
                assert sorted(result_attrib.keys()) == sorted(answer_attrib.keys()), 'answer attrib does not have the same keys as results attrib'
                for sk in answer_attrib.keys():
                    assert answer_attrib[sk] == result_attrib[sk], 'sub attribute node doesnt match'
                    
                #check sub dict
                compare(answer.sub_node_dict[k], result.sub_node_dict[k])
                
            elif type(result.sub_node_dict[k]) == TagValueNode:
                #check value
                assert result.sub_node_dict[k].value == answer.sub_node_dict[k].value, 'Values not equal'
                
                result_attrib = result.sub_node_dict[k].node_attrib
                answer_attrib = answer.sub_node_dict[k].node_attrib
                assert sorted(result_attrib.keys()) == sorted(answer_attrib.keys()), 'answer attrib does not have the same keys as results attrib'
                for sk in answer_attrib.keys():
                    assert answer_attrib[sk] == result_attrib[sk], 'sub attribute node doesnt match'
                    
                for i,n in enumerate(answer.sub_node_dict[k].sub_node):
                    compare_etree(answer.sub_node_dict[k].sub_node[i], result.sub_node_dict[k].sub_node[i])
            else:
                assert 0, ('%s not an excepted type'%type(result.sub_node_dict[k]))
            
    compare(answer, result)
    
    
def compare_etree(answer, result):
    """
        Compare Etree
        
        @param: answer - etree element
        @param: result - etree element
        
        @assert: checks if answer is equal to result
    """
    def compare(answer, result):
        #check tags
        assert answer.tag == result.tag, 'Tags are not equal'
        #check attrib
        result_attrib = result.attrib
        answer_attrib = answer.attrib
        assert sorted(result_attrib.keys()) == sorted(answer_attrib.keys()), 'answer attrib does not have the same keys as results attrib'
        for sk in answer_attrib.keys():
            assert answer_attrib[sk] == result_attrib[sk], 'attribute node doesnt match'
            
        for i,t in enumerate(answer):
            compare(answer[i],result[i])
                    
    compare(answer, result)
    
    
parser = etree.XMLParser(remove_blank_text=True)
    
    
def test_update_level_1():
    """
        Update Level Test 1
        
        Simple
    """
    current = etree.XML("""
        <preference>
            <tag name="test1" value="old" uri="/data_service/preference/1234/tag/12345"/>
        </preference>
    """, parser=parser)

    new = etree.XML("""
        <preference>
            <tag name="test1" value="new"/>
        </preference>
    """, parser=parser)
    answer = etree.XML("""
        <preference>
            <tag name="test1" value="new" uri="/data_service/preference/1234/tag/12345"/>
        </preference>
    """, parser=parser)
    
    result = update_level(new, current)
    compare_etree(answer, result)
    
def test_update_level_2():
    """
        Update Level Test 2
        
        Adding new tags
    """
    current = etree.XML("""
        <preference>
            <tag name="test1" value="old" uri="/data_service/preference/1234/tag/12345"/>
        </preference>
    """, parser=parser)

    new = etree.XML("""
        <preference>
            <tag name="test2" value="new"/>
        </preference>
    """, parser=parser)
    
    answer = etree.XML("""
        <preference>
            <tag name="test1" value="old" uri="/data_service/preference/1234/tag/12345"/>
            <tag name="test2" value="new"/>
        </preference>
    """, parser=parser)
    
    result = update_level(new, current)
    compare_etree(answer, result)
    
def test_update_level_3():
    """
        Update Level Test 3
        
        
    """
    current = etree.XML("""
        <preference>
            <tag name="test1" value="old" uri="/data_service/preference/1234/tag/12345"/>
        </preference>
    """, parser=parser)
    
    new = etree.XML("""
        <preference>
            <tag name="test2" value="new" type="somethign">
                <template>
                    <tag name="template_name" value="template_value"/>
                </template>
            </tag>
        </preference>
    """, parser=parser)
    
    answer = etree.XML("""
        <preference>
            <tag name="test1" value="old" uri="/data_service/preference/1234/tag/12345" />
            <tag name="test2" value="new" type="somethign" />
        </preference>
    """, parser=parser)
    
    result = update_level(new, current)
    compare_etree(answer, result)
    
    
def test_mergeDocument_1():
    """
        Merge Document Test 1
        
        Simple Test
    """
    
    etree_1 = etree.XML("""
        <preference>
            <tag name="name" value="old"/>
        </preference>
    """, parser=parser)

    etree_2 = etree.XML("""
        <preference>
            <tag name="name" value="new"/>
        </preference>
    """, parser=parser)
    answer = etree.XML("""
        <preference>
            <tag name="name" value="new"/>
        </preference>
    """, parser=parser)
    
    result = mergeDocuments(etree_1, etree_2)
    compare_etree(answer, result)
    
    
def test_mergeDocument_2():
    """
        Merge Document Test 2
        
        With 2 levels 
    """
    etree_1 = etree.XML("""
        <preference>
            <tag name="first_level">
                <tag name="name" value="old"/>
            </tag>
        </preference>
    """, parser=parser)

    etree_2 = etree.XML("""
        <preference>
            <tag name="first_level">
                <tag name="name" value="new"/>
            </tag>
        </preference>
    """, parser=parser)
    answer = etree.XML("""
        <preference>
            <tag name="first_level">
                <tag name="name" value="new"/>
            </tag>
        </preference>
    """, parser=parser)
    
    result = mergeDocuments(etree_1, etree_2)
    compare_etree(answer, result)
    
    
def test_mergeDocument_3():
    """
        Merge Document Test 3
        
        Strange Case
        
        With a tag nusted under a tag with a value 
    """
    etree_1 = etree.XML("""
        <preference>
            <tag name="first_level" value="old">
                <tag name="name" value="old"/>
            </tag>
        </preference>
    """, parser=parser)

    etree_2 = etree.XML("""
        <preference>
            <tag name="first_level">
                <tag name="name" value="new"/>
            </tag>
        </preference>
    """, parser=parser)
    answer = etree.XML("""
        <preference>
            <tag name="first_level" value="old">
                <tag name="name" value="old"/>
            </tag>
        </preference>
    """, parser=parser)
    
    result = mergeDocuments(etree_1, etree_2)
    compare_etree(answer, result)
    
    
def test_mergeDocument_4():
    """
        Merge Document Test 4
        
        More Strange Case
        
        
    """
    etree_1 = etree.XML("""
        <preference>
            <template>
                <tag name="name" value="template_name_old"/>
                <tag name="type" value="template_type_old"/>
            </template>
            <tag name="first_level">
                <template>
                    <tag name="name" value="template_name"/>
                    <tag name="type" value="template_type"/>
                </template>
                <tag name= "node1" value="value1_old"/>
                <tag name= "node2" value="value2_old"/>
            </tag>
        </preference>
    """, parser=parser)
    
    etree_2 = etree.XML("""
        <preference>
            <template>
                <tag name="name" value="template_name_new"/>
                <tag name="type" value="template_type_new"/>
            </template>
            <tag name="first_level">
                <template>
                    <tag name="name" value="template_name_new"/>
                    <tag name="type" value="template_type_new"/>
                </template>
                <tag name= "node1" value="value1_new"/>
            </tag>
        </preference>
    """, parser=parser)
    
    answer = etree.XML("""
        <preference>
            <template>
                <tag name="name" value="template_name_old"/>
                <tag name="type" value="template_type_old"/>
            </template>
            <tag name="first_level">
                <template>
                    <tag name="name" value="template_name"/>
                    <tag name="type" value="template_type"/>
                </template>
                <tag name= "node1" value="value1_new"/>
                <tag name= "node2" value="value2_old"/>
            </tag>
        </preference>
    """, parser=parser)
    
    result = mergeDocuments(etree_1, etree_2)
    compare_etree(answer, result)
    
    
    
def test_mergeDocument_5():
    """
        Merge Document Test 5
        
        Normal Use Case
        
        order get mest up
    """
    etree_1 = etree.XML("""
        <preference>
            <tag name="test1" value="test1_old"/>
            <tag name="test2" value="test2_old"/>
            <tag name="first_level">
                <tag name="test1" value="test1_old"/>
                <tag name="test2" value="test2_old">
                    <template>
                        <tag name="template_param_1" value="template_config_1"/>
                        <tag name="template_param_2" value="template_config_2"/>
                    </template>
                </tag>
                <tag name="second_level">
                    <tag name="test1" value="test1_old"/>
                    <tag name="test2" value="test2_old"/>
                </tag>
            </tag>
        </preference>
    """, parser=parser)
    
    etree_2 = etree.XML("""
        <preference>
            <tag name="test2" value="test2_new"/>
            <tag name="first_level">
                <tag name="test1" value="test1_new">
                    <template>
                        <tag name="template_param_1" value="template_config_1"/>
                        <tag name="template_param_2" value="template_config_2"/>
                    </template>                    
                </tag>
                <tag name="test2" value="test2_new"/>
                <tag name="second_level">
                    <tag name="test1" value="test1_new"/>
                </tag>
            </tag>
        </preference>
    """, parser=parser)
    
    answer = etree.XML("""
        <preference>
            <tag name="test1" value="test1_old"/>
            <tag name="test2" value="test2_new"/>
            <tag name="first_level">
                <tag name="test1" value="test1_new"/>
                <tag name="test2" value="test2_new">
                    <template>
                        <tag name="template_param_1" value="template_config_1"/>
                        <tag name="template_param_2" value="template_config_2"/>
                    </template>
                </tag>
                <tag name="second_level">
                    <tag name="test1" value="test1_new"/>
                    <tag name="test2" value="test2_old"/>
                </tag>
            </tag>
        </preference>
    """, parser=parser)
    
    result = mergeDocuments(etree_1, etree_2)
    compare_etree(answer, result)
    
    
def test_to_dict_1():
    """
        To Dict Test 1
        
        Simple Test
    """
    xml = etree.XML("""
        <preference>
            <tag name="test1" value="test1_old"/>
            <tag name="test2" value="test2_old"/>
            <tag name="first_level">
                <tag name="test1" value="test1_old"/>
                <tag name="test2" value="test2_old"/>
                <tag name="second_level">
                    <tag name="test1" value="test1_old"/>
                    <tag name="test2" value="test2_old"/>
                </tag>
            </tag>
        </preference>
    """, parser=parser)
    
    answer = TagNameNode(
        sub_node_dict = OrderedDict([(
            'test1', TagValueNode(
                value = 'test1_old',
                node_attrib = {
                    'name':'test1', 
                    'value':'test1_old'
                }
        )),(
            'test2', TagValueNode(
                value = 'test2_old',
                node_attrib = {
                    'name':'test2', 
                    'value':'test2_old'
                }
        )),(
            'first_level', TagNameNode(
                sub_node_dict = OrderedDict([(
                    'test1' , TagValueNode(
                        value = 'test1_old',
                        node_attrib = {
                            'name':'test1', 
                            'value':'test1_old'
                        },
                )), (
                    'test2' , TagValueNode(
                        value = 'test2_old',
                        node_attrib = {
                            'name':'test2', 
                            'value':'test2_old',
                        }
                )), (
                    'second_level' , TagNameNode(
                        sub_node_dict =  OrderedDict([(
                            'test1' , TagValueNode(
                                value = 'test1_old',
                                node_attrib = {
                                    'name':'test1', 
                                    'value':'test1_old'
                                },
                        )),(
                            'test2' , TagValueNode(
                                value = 'test2_old',
                                node_attrib = {
                                    'name':'test2', 
                                    'value':'test2_old'
                                },
                        ))]),
                        node_attrib = {
                            'name':'second_level'
                        }
                ))]),
                node_attrib = {
                    'name':'first_level'
                }
            )
        )])
    )
    
    result = to_dict(xml)
    compare_dict(answer, result)
    
    
def test_to_dict_2():
    """
        To Dict Test 2
        
        Simple Test
        
        Value node with children
    """
    xml = etree.XML("""
        <preference>
            <tag name="test1" value="test1_old"/>
            <tag name="test2" value="test2_old"/>
            <tag name="first_level" value ="test">
                <tag name="test1" value="test1_old"/>
                <tag name="test2" value="test2_old"/>
            </tag>
        </preference>
    """, parser=parser)
    
    answer = TagNameNode(
        sub_node_dict = OrderedDict([(
            'test1', TagValueNode(
                value = 'test1_old',
                node_attrib = {
                    'name'  : 'test1',
                    'value' : 'test1_old',
                },
            )
        ), (
            'test2', TagValueNode(
                value = 'test2_old',
                node_attrib = {
                    'name'  : 'test2',
                    'value' : 'test2_old',
                },
            )
        ), (
            'first_level', TagValueNode(
                value = 'test',
                node_attrib = {
                    'name'  : 'first_level',
                    'value' : 'test',
                },
                sub_node = [
                    etree.Element('tag', name='test1', value='test1_old'),
                    etree.Element('tag', name='test2', value='test2_old'),
                ],
            )
        )])
    )
    
    result = to_dict(xml)
    compare_dict(answer, result)
    
    
def test_to_dict_3():
    """
        To Dict Test 3
        
        Top level None Tag Nodes
    """
    xml = etree.XML("""
        <preference>
            <template>
                <tag name="test1" value="templateTest"/>
            </template>
            <tag name="test1" value="test1_old"/>
        </preference>
    """, parser=parser)
    
    template = etree.Element('template')
    etree.SubElement(template, 'tag', name='test1', value="templateTest")
    
    answer = TagNameNode(
        sub_node_dict = OrderedDict([(
            'test1', TagValueNode(
                value = 'test1_old',
                node_attrib = {
                    'name'  : 'test1',
                    'value' : 'test1_old',
                },
            )
        )]),
        sub_none_tag_node =[
            template
        ]
    )
    
    result = to_dict(xml)
    compare_dict(answer, result)
    
    
def test_to_etree_1():
    """
        To Etree Test 1
        
        Simple Test
    """
    
    dict = TagNameNode(
        sub_node_dict = OrderedDict([(
            'test1', TagValueNode(
                value = 'test1_old',
                node_attrib = {
                    'name':'test1', 
                    'value':'test1_old'
                }
        )),(
            'test2', TagValueNode(
                value = 'test2_old',
                node_attrib = {
                    'name':'test2', 
                    'value':'test2_old'
                }
        )),(
            'first_level', TagNameNode(
                sub_node_dict = OrderedDict([(
                    'test1' , TagValueNode(
                        value = 'test1_old',
                        node_attrib = {
                            'name':'test1', 
                            'value':'test1_old'
                        },
                )), (
                    'test2' , TagValueNode(
                        value = 'test2_old',
                        node_attrib = {
                            'name':'test2', 
                            'value':'test2_old',
                        }
                )), (
                    'second_level' , TagNameNode(
                        sub_node_dict =  OrderedDict([(
                            'test1' , TagValueNode(
                                value = 'test1_old',
                                node_attrib = {
                                    'name':'test1', 
                                    'value':'test1_old'
                                },
                        )),(
                            'test2' , TagValueNode(
                                value = 'test2_old',
                                node_attrib = {
                                    'name':'test2', 
                                    'value':'test2_old'
                                },
                        ))]),
                        node_attrib = {
                            'name':'second_level'
                        }
                ))]),
                node_attrib = {
                    'name':'first_level'
                }
            )
        )])
    )
    
    answer = etree.XML("""
        <preference>
            <tag name="test1" value="test1_old"/>
            <tag name="test2" value="test2_old"/>
            <tag name="first_level">
                <tag name="test1" value="test1_old"/>
                <tag name="test2" value="test2_old">
                </tag>
                <tag name="second_level">
                    <tag name="test1" value="test1_old"/>
                    <tag name="test2" value="test2_old"/>
                </tag>
            </tag>
        </preference>
    """, parser=parser)
    result = to_etree(dict)
    
    compare_etree(answer, result)
    
def test_to_etree_2():
    """
        To Etree Test 2
    """
    dict = TagNameNode(
        sub_node_dict = OrderedDict([(
            'test1', TagValueNode(
                value = 'test1_old',
                node_attrib = {
                    'name'  : 'test1',
                    'value' : 'test1_old',
                },
            )
        ), (
            'test2', TagValueNode(
                value = 'test2_old',
                node_attrib = {
                    'name'  : 'test2',
                    'value' : 'test2_old',
                },
            )
        ), (
            'first_level', TagValueNode(
                value = 'test',
                node_attrib = {
                    'name'  : 'first_level',
                    'value' : 'test',
                },
                sub_node = [
                    etree.Element('tag', name='test1', value='test1_old'),
                    etree.Element('tag', name='test2', value='test2_old'),
                ],
            )
        )])
    )
    
    answer = etree.XML("""
        <preference>
            <tag name="test1" value="test1_old"/>
            <tag name="test2" value="test2_old"/>
            <tag name="first_level" value ="test">
                <tag name="test1" value="test1_old"/>
                <tag name="test2" value="test2_old"/>
            </tag>
        </preference>
    """, parser=parser)
    

    result = to_etree(dict)
    compare_etree(answer, result)


def test_to_etree_3():
    """
        To Etree Test 3
    """
    template = etree.Element('template')
    etree.SubElement(template, 'tag', name='test1', value="templateTest")
    
    dict = TagNameNode(
        sub_node_dict = OrderedDict([(
            'test1', TagValueNode(
                value = 'test1_old',
                node_attrib = {
                    'name'  : 'test1',
                    'value' : 'test1_old',
                },
            )
        )]),
        sub_none_tag_node =[
            template
        ]
    )
    
    answer = etree.XML("""
        <preference>
            <template>
                <tag name="test1" value="templateTest"/>
            </template>
            <tag name="test1" value="test1_old"/>
        </preference>
    """, parser=parser)
    
    result = to_etree(dict)
    compare_etree(answer, result)



    
    
    
    