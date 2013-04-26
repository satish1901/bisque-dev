import urllib, urllib2, cookielib
from lxml import etree
import lxml
import time
from bq.api.comm import BQSession
from bq.api.util import fetch_image_pixels

username = 'botanicam'
password = 'plantvrl'

##cj = cookielib.CookieJar()
##opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
##login_data = urllib.urlencode({'username' : username, 'j_password' : password})
##opener.open('http://bisque.ece.ucsb.edu/auth_service/login', login_data)
##resp = opener.open('http://bisque.ece.ucsb.edu/data_service/dataset/2326366?view=deep,clean')
##parser = etree.XMLParser(target = etree.TreeBuilder())
##dataset=etree.XML(resp.read(),parser)
##imageurls=dataset.xpath('value')

Session=BQSession()
Session.init_local(username,password,bisque_root='http://bisque.ece.ucsb.edu')
parser = etree.XMLParser(target = etree.TreeBuilder())
dataset=etree.XML(resp.read(),parser)
imageurls=dataset.xpath('value')

#uri=[]
#for imageurl in imageurls:
    #image=imageurl.text
    #respimage = opener.open(image)
    #tree=etree.XML(respimage.read(),parser)
    #uri.append('http://128.111.185.26:8080'+'/image_service/images/'+tree.attrib['resource_uniq'])

username = 'admin'
password = 'admin'
login_data = urllib.urlencode({'username' : username, 'j_password' : password})
opener.open('http://128.111.185.26:8080/auth_service/login', login_data)

feature_List=['CLD']#['SIFT','SURF','SCD','CSD','CLD','HTD','ORB']
for feature in feature_List:
    
    print 'beginning to post features'
    count = 0
    for image_uri in imageurls:
        start = time.time()
        imageurl = urllib.quote(image_uri,'')
        respfeature = opener.open('http://128.111.185.26:8080/features/get/'+feature+'/none?uri='+imageurl)
        end = time.time()
        elapsetime=end-start
        count+=1
        print 'finish feature extraction:' + str(count)
        print 'time: ' + str(elapsetime)+ ' sec'
        if count==30:
            break

        


