import requests
import os
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# 解析html, TODO: 没处理background
def resolve_html(content):
    urls = []
    soup = BeautifulSoup(content, "html.parser")
    pattern = re.compile("^(?!javascript|#)")
    tags_href = soup.find_all(['link', 'a'], attrs={'href': pattern})
    tags_src = soup.find_all(['img', 'script'], attrs={'src': pattern})
    for tag_a in tags_href:
        urls.append(tag_a['href'])
    for tag_a in tags_src:
        urls.append(tag_a['src'])
    return urls


# 解析css
def resolve_style(content):
    urls = re.findall(r"url\([\'\"]?([^\'\"]*)[\'\"]?\)", content)
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
            time.sleep(1)
            repeat_time += 1
            if repeat_time == max_repeat_time:
                return urls
    status = f.status_code
    if status == 200:
        # 解析页面内容的下级链接
        urls.extend(fixed_url(url, spider_content(url, f)))
        # 保存内容
        if save:
            save_file(url, f)
    return urls


# 解析内容
def spider_content(url, f):
    urls = []
    if is_html(url) is True:
        print("Reading the web ...")
        urls.extend(resolve_html(f.content))
    if is_css(url) is True:
        print("Reading the stylesheet ...")
        urls.extend(resolve_style(f.text))

    return urls


# 保存数据
def save_file(url, res):
    delimiter = '/'
    parse_obj = urlparse(url)
    path = parse_obj.path
    p_url_arr = path.split('/')
    file_name = p_url_arr.pop()
    path = delimiter + delimiter.join(p_url_arr) + delimiter
    base = 'e:/spider'
    check_dictionary(base, path)
    '''
    content_type = res.headers['Content-Type']
    if content_type.find('javascript') != -1:
        base += 'js/'
    elif content_type.find('image') != -1:
        base += 'images/'
    elif content_type.find('css') != -1:
        base += 'css/'
    '''
    search = file_name.find('?')
    if search != -1:
        file_name = file_name[0:search]
    file_name = re.sub(r'[\\\/:\*\?\"\'<>\|]', '_', file_name)
    name = base + path + file_name
    with open(name, 'wb') as code:
        code.write(res.content)


# 校验目录，并创建目录
def check_dictionary(base, path):
    base_path = base + path
    if os.path.exists(base_path) is False:
        os.makedirs(base_path)


# 是否是html
def is_html(url):
    pattern = re.compile(r"(?:.+)\.html$")
    m = pattern.match(url)
    if m:
        return True
    else:
        return False


# css解析下级链接
def is_css(url):
    pattern = re.compile(r"(?:.+)\.css")
    m = pattern.match(url)
    if m:
        return True
    else:
        return False


# 判断地址是否有效 TODO: 地址过滤, 目前无扩展名的地址全部过滤掉了
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
seed_url = 'http://www.jq22.com/demo/bootstrap-150308231052/index.html'
domain = 'www.jq22.com'

start = time.clock()
dfs(seed_url, True)
end = time.clock()
print('total cost %f s' % (end - start))
print('------------------------all-sites-map-------------------------')
print(sites)