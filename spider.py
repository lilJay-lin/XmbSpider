import requests
import os
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# 获取a链接
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


# 没处理base64和background
def get_tags_img(soup):
    urls = []
    tags_a = soup.find_all('img')
    for tag_a in tags_a:
        urls.append(tag_a['src'])
    return urls


# 解析出页面的所有url地址
def get_urls(url, max_repeat_time=5):
    urls = []
    repeat_time = 0
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
        print("Reading the web ...")
        soup = BeautifulSoup(f.content, "html.parser")
        a_url = get_tags_href(soup)
        urls.extend(fixed_url(url, a_url))
    return urls


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
    s_path_arr = rel_path.split('/')
    r_path_arr = url.split('/')
    delimiter = '/'
    if rel_path[p_len - 1] != '/':
        s_path_arr.pop()
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


# dfs深度优先遍历全站
sites = set()
visited = set()


def dfs(url):
    visited.add(url)
    all_urls = get_urls(url)
    if len(all_urls) == 0:
        return
    for page in all_urls:
        if page not in sites:
            sites.add(page)
        if page not in visited:
            print("Visiting page", page)
            dfs(url)
    print("success", url)


# 执行区
seed_url = 'http://www.jq22.com/demo/bootstrap-150308231052/list.html'
dfs(seed_url)
print('------------------------all-sites-map-------------------------')
print(sites)

