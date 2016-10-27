import requests
import os
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# 获取a链接, TODO: 没处理base64和background
def get_tags_href(soup):
    urls = []
    pattern = re.compile("^(?!javascript|#)")
    tags_href = soup.find_all(['link', 'a'], attrs={'href': pattern})
    tags_src = soup.find_all(['img', 'script'], attrs={'src': pattern})
    for tag_a in tags_href:
        urls.append(tag_a['href'])
    for tag_a in tags_src:
        urls.append(tag_a['src'])
    return urls


# 解析出页面的所有url地址
def get_urls(url, save, max_repeat_time=5):
    urls = []
    repeat_time = 0
    if url[len(url) - 1] == '/':
        url += 'index.html'
    if is_validate_url(url) is False:
        return urls
    while True:
        try:
            print("Ready to Open the Web")
            '''time.sleep(1)'''
            print("opening the Web", url)
            f = requests.get(url, timeout=3)
            print("Success to Open the Web")
            break
        except:
            print("Open Url Failed !!! Repeat")
            '''time.sleep(1)'''
            repeat_time += 1
            if repeat_time == max_repeat_time:
                return urls
    status = f.status_code
    if status == 200:
        if save:
            save_file(url, f)
        if is_html(url) is True:
            print("Reading the web ...")
            soup = BeautifulSoup(f.content, "html.parser")
            a_url = get_tags_href(soup)
            urls.extend(fixed_url(url, a_url))
    return urls


# 保存数据
def save_file(url, res):
    p_url_arr = url.split('/')
    name = 'e:/spider/' + p_url_arr.pop()
    with open(name, 'wb') as code:
        print(code)
        code.write(res.content)
        code.close()


# 是否是html
def is_html(url):
    pattern = re.compile(r"(?:.+)\.html$")
    m = pattern.match(url)
    if m:
        return True
    else:
        return False


# 判断是否和html地址 TODO: 地址过滤
def is_validate_url(url):
    if url.startswith('javascript') or url.startswith('#') or url == '':
        return False
    url_arr = url.split('/')
    last = url_arr.pop()
    if last.find('.') == -1:
        return False
    return True


# 地址补全
def fixed_url(original, urls):
    url_obj = urlparse(original)
    scheme = url_obj.scheme
    netloc = url_obj.netloc
    path = url_obj.path
    pattern = re.compile('^https|http|//|' + netloc)
    fixed_urls = []
    for url in urls:
        # TODO:补全协议
        if pattern.match(url):
            fixed_urls.append(url)
        else:
            rel_url = scheme + '://' + netloc + '/' + get_relative_url(path, url)
            fixed_urls.append(rel_url)
    return fixed_urls


# 获取相对路径地址
def get_relative_url(rel_path, url):
    p_len = len(rel_path)
    rel_path = trip(rel_path)
    url = trip(url)
    s_path_arr = rel_path.split('/')
    r_path_arr = url.split('/')
    s_path_arr.pop()
    delimiter = '/'
    while len(r_path_arr) != 0 and len(s_path_arr) != 0:
        u = r_path_arr[0]
        if u == '..':
            s_path_arr.pop()
            del r_path_arr[0]
        elif u == '.':
            del r_path_arr[0]
        else:
            break
    s_path_arr.extend(r_path_arr)
    return delimiter.join(s_path_arr)


# 去除结尾/
def trip(url):
    start = 0
    end = len(url)
    if url[0] == '/':
        start = 1
    if url[end - 1] == '/':
        end -= 1
    return url[start:end]


# dfs深度优先遍历全站
def dfs(url, save):
    global sites
    global visited
    global domain
    visited.add(url)
    all_urls = get_urls(url, save)
    if len(all_urls) == 0:
        return
    for page in all_urls:
        if page not in sites:
            sites.add(page)
        # TODO: url过滤不够严谨
        if page not in visited and page.find(domain) != -1:
            print("Visiting page", page)
            dfs(page, save)
    print("success", url)


# 全站页面扫描
sites = set()
visited = set()
seed_url = 'http://www.jq22.com/demo/bootstrap-150308231052/list.html'
domain = 'www.jq22.com'
start = time.clock()
dfs(seed_url, False)
end = time.clock()
print('total cost %f s' % (end - start))
print('------------------------all-sites-map-------------------------')
print(sites)

