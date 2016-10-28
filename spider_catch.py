import time
from spider import Spider
start = time.clock()
Spider.start(url='http://www.jq22.com/demo/bootstrap-150308231052/index.html')
end = time.clock()
print('total cost %f s' % (end - start))
print('------------------------all-sites-map-------------------------')
print(Spider.sites)
