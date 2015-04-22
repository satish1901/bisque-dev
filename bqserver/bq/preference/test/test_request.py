from bqapi import BQSession



class TestNameSpace(object):
    """
        A container for variable that need
        to be passed between the setups/teardowns
        and tests themselves
    """
    def __init__(self):
        pass
    
    
    
NS = TestNameSpace()
    
    
    
def check_response(answer, result):
    """
        
    """
    
def check_resource():
    """
        
    """
    
def setUp():
    """ Setup feature requests test """
    NS.bq_admin = BQSession()
    NS.bq_admin.init_local('admin', 'admin', bisque_root='http://128.111.185.26:8080')
    NS.bq_user = BQSession()
    NS.bq_user.init_local('asdf', 'asdf', bisque_root='http://128.111.185.26:8080')
    NS.bq_no_user = BQSession()
    
    #copy system document locally to be re-uploaded after test
    
    #upload test system document
    
    #create new test user
    NS.bq_user = BQSession()
    NS.bq_user.init_local('asdf', 'asdf', bisque_root='http://128.111.185.26:8080')
    NS.bq_no_user = BQSession()
    
    #create test user documented private
    
    #create public user document
    
    
def tearDown():
    """ Teardown feature requests test """
    #utils.tear_down_simple_feature_test(NS)
    
    #remove test system document
    
    #upload system document

def setup_image_upload():
    utils.setup_image_upload(NS)
    
def teardown_image_remove():
    utils.teardown_image_remove(NS)
    
def setup_dataset_upload():
    utils.setup_dataset_upload(NS)
    
def teardown_dataset_remove():
    utils.teardown_dataset_remove(NS)
    
    
    
def test_admin():
    """
       test admin user against preferences 
    """
    #get system preference
    check_response(answer, result)
    
    #post to system preference
    check_response(answer, result)
    
    #put to system preference
    check_response(answer, result)
    
    #delete from system preference
    check_response(answer, result)
    
    #delete system preference
    check_response(answer, result)
    
    
def test_user():
    """
        test a normal user against preferences 
    """
    #get system preference
    check_response(answer, result)
    
    #post to system preference (fail)
    check_response(answer, result)
    
    #put to system preference (fail)
    check_response(answer, result)
    
    #delete from system preference (fail)
    check_response(answer, result)
    
    #delete system preference (fail)
    check_response(answer, result)
    
    #put to user preference
    
    #get user preference
    
    #post to user preference
    
    #delete element
    
    #delete user preference
    
    #put to resource preference
    
    #get resource preference
    
    #post to resource preference
    
    #delete element from resource preference
    
    #delete resource preference

def test_no_user():
    """
        test a logged out user against
    """
    #get system preference
    check_response(answer, result)
    
    #post to system preference (fail)
    check_response(answer, result)
    
    #put to system preference (fail)
    check_response(answer, result)
    
    #delete from system preference (fail)
    check_response(answer, result)
    
    #delete system preference (fail)
    check_response(answer, result)
    
    #put to user preference (fail)
    
    #get user preference (returns system preference)
    
    #post to user preference (fail)
    
    #delete element (fail)
    
    #delete user preference (fail)
    
    #put to resource preference (fail)
    
    #get resource preference with access
    
    #get resource preference without access (fail)
    
    #post to resource preference (fail)
    
    #delete element from resource preference (fail)
    
    #delete resource preference (fail))