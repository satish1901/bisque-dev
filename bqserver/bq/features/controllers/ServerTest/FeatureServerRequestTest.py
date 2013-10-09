import unittest
#from bq.api.comm import BQSession
from lxml import etree
from bqapi.comm import BQSession


##class TestParameters():
##    self.feature_name = 'HTD'
##    self.root = 'http://128.111.185.26:8080'
##    self.user = 'admin'
##    self.pwd  = 'admin'
##    self.dataset = 'http://128.111.185.26:8080/data_service/dataset/257970' #test dataset to post features
##    self.image = 'http://128.111.185.26:8080/image_service/image/JWfRGcDzmqgFyzP7tvgytW' #test image to get features
##    self.polygon = ''    
    

class TestFeatureRequests(unittest.TestCase):
    """
        Test the deferent kind of request that can
        be given to the feature server
    """
    @classmethod
    def setUpClass(self):
        
        self.feature_name = 'FFTSD'
        self.root = 'http://128.111.185.26:8080'
        self.user = 'admin'
        self.pwd  = 'admin'
        self.dataset = 'http://128.111.185.26:8080/data_service/dataset/257970' #test dataset to post features
        self.image = 'http://128.111.185.26:8080/image_service/image/JWfRGcDzmqgFyzP7tvgytW' #test image to get features
        self.polygon = ''
        self.query = 'polygon=http://128.111.185.26:8080/data_service/image/419333/gobject/419334/gobject/419352'
        
        #initalize bq session for testing
        self.session = BQSession().init_local(self.user, self.pwd,  bisque_root=self.root, create_mex=False)
        
        #fetch and compose dataset for posting to the feature server
        dataset_xml = self.session.fetchxml(self.dataset+'/value')

        dataset = etree.Element('dataset')
        for i,image in enumerate(dataset_xml.xpath('image')):
            value = etree.SubElement(dataset,'value',type='query')
            value.text = 'polygon=http://128.111.185.26:8080/data_service/image/419333/gobject/419334/gobject/419352'
            #value.text = 'image=http%3A%2F%2F128.111.185.26%3A8080%2Fimage_service%2Fimage%2FJWfRGcDzmqgFyzP7tvgytW%3Froi%3D1%2C1%2C500%2C500%26format%3Dtiff'+'&mask=http%3A%2F%2F128.111.185.26%3A8080%2Fimage_service%2Fimage%2FjZCZtRKRkTJzY8CJsR2SdH%3Froi%3D1%2C1%2C500%2C500%26format%3Dtiff'
            break
            if i>1:
                break
        self.feature_request_document = etree.tostring(dataset)
     
    #testing get cached features returns
    def test_get_cached_feature_xml(self):
        
        uri = self.root+'/features/'+self.feature_name+'/'+'xml?'+self.query        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
        
    def test_get_cached_feature_none(self):
        
        uri = self.root+'/features/'+self.feature_name+'/'+'xml?'+self.query        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_get_cached_feature_hdf(self):
        uri = self.root+'/features/'+self.feature_name+'/'+'xml?'+self.query        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_get_cached_feature_csv(self):
        uri = self.root+'/features/'+self.feature_name+'/'+'xml?'+self.query        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)



    
    #testing post cached features returns
    def test_post_cached_feature_xml(self):
        uri = self.root+'/features/'+self.feature_name+'/'+'xml'
        
        #manually set up request
        headers = self.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = self.session.c.http.request(uri, 
                                                      headers = headers,
                                                      body = self.feature_request_document,
                                                      method='POST')
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_post_cached_feature_none(self):
        uri = self.root+'/features/'+self.feature_name+'/'+'none'
        
        #manually set up request
        headers = self.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = self.session.c.http.request(uri, 
                                                      headers = headers,
                                                      body = self.feature_request_document,
                                                      method='POST')
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_post_cached_feature_hdf(self):
        uri = self.root+'/features/'+self.feature_name+'/'+'hdf'
        
        #manually set up request
        headers = self.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = self.session.c.http.request(uri, 
                                                      headers = headers,
                                                      body = self.feature_request_document,
                                                      method='POST')
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_post_cached_feature_csv(self):
        uri = self.root+'/features/'+self.feature_name+'/'+'csv'
        
        #manually set up request
        headers = self.session.c.prepare_headers({'Content-Type':'text/xml', 'Accept':'text/xml'})
        header, content = self.session.c.http.request(uri, 
                                                      headers = headers,
                                                      body = self.feature_request_document,
                                                      method='POST')
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)

    
#    #testing get uncached features
#    def test_get_cached_feature_xml(self):
#        pass
#    
#    def test_get_cached_feature_none(self):
#        pass
#    
#    def test_get_cached_feature_hdf(self):
#        pass
#    
#    def test_get_cached_feature_csv(self):
#        pass
#    
#    #testing post uncached features
#    def test_post_cached_feature_xml(self):
#        pass
#    
#    def test_post_cached_feature_none(self):
#        pass
#    
#    def test_post_cached_feature_hdf(self):
#        pass
#    
#    def test_post_cached_feature_csv(self):
#        pass
#    
    #documentation
    def test_feature_main(self):
        uri = self.root+'/features'
        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_feature_list(self):
        uri = self.root+'/features/list'
        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
    def test_formats(self):
        uri = self.root+'/features/formats'
        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
        
    def test_feature(self):
        uri = self.root+'/features/'+self.feature_name
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)
    
##    #strange cases
##    def test_multible_element_types(self):
##        pass



    
    #fail casses
    def test_multible_same_element_types(self):
        """
            testing the case when many inputs for the same name are given
        """
        uri = self.root+'/features/'+self.feature_name+'/'+'none?'+self.query+'&'+self.query

        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 400)


    
    def test_nonlisted_feature(self):
        """
            testing the case when the resource to calculate the feature on
            is not in the system
        """        
        uri = self.root+'/features/asdf/'+'none?'+self.query
        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 404)
        
    
    def test_nonlisted_format(self):
        """
            testing non-listed format
        """
        uri = self.root+'/features/'+self.feature_name+'/'+'safd?'+self.query
        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 404)
        
            
    def test_incorrect_resource_input_type(self):
        """
            testing incorrect input resource type
        """
        uri = self.root+'/features/'+self.feature_name+'/'+'none?stuff="'+self.query
        
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 400)
        
    
    def test_resource_type_not_found(self):
        """
            testing non-listed format
        """
        self.notfoundimage = 'http://128.111.185.26:8080/image_service/image/'+'asdfasdhg'
        uri = self.root+'/features/'+self.feature_name+'/'+'none?image="'+self.notfoundimage+'"'
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid
        self.assertEqual(header.status, 200)


                #feature                           #expected output
feature_list = {
                #VRL
                'HTD'                           :  [0,0,0,0,0,0,0,0,0,0],
                'EHD'                           :  [0,0,0,0,0,0,0,0,0,0],
                
                #MPEG7Flex
                'CLD'                           :  [0,0,0,0,0,0,0,0,0,0],
                'CSD'                           :  [0,0,0,0,0,0,0,0,0,0],
                'SCD'                           :  [0,0,0,0,0,0,0,0,0,0],
                'DCD'                           :  [0,0,0,0,0,0,0,0,0,0],
                'HTD2'                          :  [0,0,0,0,0,0,0,0,0,0],
                'EHD2'                          :  [0,0,0,0,0,0,0,0,0,0],

                #WNDCharm
                'Chebishev_Statistics'          :  [0,0,0,0,0,0,0,0,0,0],
                'Chebyshev_Fourier_Transform'   :  [0,0,0,0,0,0,0,0,0,0],
                'Color_Histogram'               :  [0,0,0,0,0,0,0,0,0,0],
                'Comb_Moments'                  :  [0,0,0,0,0,0,0,0,0,0],
                'Edge_Features'                 :  [0,0,0,0,0,0,0,0,0,0],
                'Fractal_Features'              :  [0,0,0,0,0,0,0,0,0,0],
                'Gini_Coefficient'              :  [0,0,0,0,0,0,0,0,0,0],
                'Gabor_Textures'                :  [0,0,0,0,0,0,0,0,0,0],
                'Haralick_Textures'             :  [0,0,0,0,0,0,0,0,0,0],
                'Multiscale_Historgram'         :  [0,0,0,0,0,0,0,0,0,0],
                'Object_Feature'                :  [0,0,0,0,0,0,0,0,0,0],
                'Inverse_Object_Features'       :  [0,0,0,0,0,0,0,0,0,0],
                'Pixel_Intensity_Statistics'    :  [0,0,0,0,0,0,0,0,0,0],
                'Radon_Coefficients'            :  [0,0,0,0,0,0,0,0,0,0],
                'Tamura_Textures'               :  [0,0,0,0,0,0,0,0,0,0],
                'Zernike_Coefficients'          :  [0,0,0,0,0,0,0,0,0,0],

                #OpenCV
                'BRISK'                         :  [0,0,0,0,0,0,0,0,0,0],
                'ORB'                           :  [0,0,0,0,0,0,0,0,0,0],
                'SIFT'                          :  [0,0,0,0,0,0,0,0,0,0],
                'SURF'                          :  [0,0,0,0,0,0,0,0,0,0],
                

                #Mahotas
                'LBP'                           :  [0,0,0,0,0,0,0,0,0,0],
                'PFTAS'                         :  [0,0,0,0,0,0,0,0,0,0],
                'TAS'                           :  [0,0,0,0,0,0,0,0,0,0],
                'ZM'                            :  [0,0,0,0,0,0,0,0,0,0],
                
               }




class FeatureTest(unittest.TestCase):
    """
        Test Features
    """
    
    @classmethod
    def setUpClass(self):
        
        self.root = 'http://128.111.185.26:8080'
        self.user = 'admin'
        self.pwd  = 'admin'        
        
        #initalize bq session for testing
        self.session = BQSession().init_local(self.user, self.pwd,  bisque_root=self.root, create_mex=False)
    

##    @classmethod
##    def tearDownClass(self):

def feature_test_generator(feature_name,expected_ouptut):
    def test(self):
        """
            generates feature tests
        """
        image = 'http://128.111.185.26:8080/image_service/image/JWfRGcDzmqgFyzP7tvgytW'
        uri = self.root+'/features/'+feature_name+'/'+'csv?image="'+image+'"'
        #manually set up request
        headers = self.session.c.prepare_headers(None)
        header, content = self.session.c.http.request(uri, headers = headers)
        
        #check to see if the resulting response code is valid        
        self.assertEqual(header.status,200)        
    return test


def run_feature_test(feature_name=None):
    if feature_name:
        test_name = 'test_%s' % feature_name
        test = feature_test_generator(feature_name , feature_list[feature_name])
        setattr(FeatureTest, test_name, test)
    else:
        for f in feature_list.keys():
            test_name = 'test_%s' % f
            test = feature_test_generator(f , feature_list[f])
            setattr(FeatureTest, test_name, test)
        
    suite = unittest.TestLoader().loadTestsFromTestCase(FeatureTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
        
if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFeatureRequests)
    unittest.TextTestRunner(verbosity=2).run(suite)
    #run_feature_test()













    
           
