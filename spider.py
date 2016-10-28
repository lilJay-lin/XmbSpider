import requests
import os
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class Spider:
    sites = set()
    visited = set()
    seed_url = ''
    domain = ''
    save_path = 'e:\spider'

    @classmethod
    def start(cls, **arg):
        save = True
        if 'url' in arg:
            url = arg['url']
        else:
            print('url no defined, nothing being to spider...')
            return
        if 'save_path' in arg:
            cls.save_path = arg['save_path']
        if 'save' in arg:
            save = arg['save']
        cls.seed_url = url
        parse_obj = urlparse(url)
        cls.domain = parse_obj.netloc
        cls.dfs(url, save)

    @staticmethod
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

    @staticmethod
    # 解析css
    def resolve_style(content):
        urls = re.findall(r"url\s*\(\*?[\'\"]?([^\(\'\"\)]*)[\'\"]?\*?\)", content)
        return urls

    @staticmethod
    # 去除结尾/
    def trip(url):
        start = 0
        end = len(url)
        if url[0] == '/':
            start = 1
        if url[end - 1] == '/':
            end -= 1
        return url[start:end]

    @staticmethod
    # 校验目录，并创建目录
    def check_dictionary(base, path):
        base_path = base + path
        if os.path.exists(base_path) is False:
            os.makedirs(base_path)

    @staticmethod
    # 是否是html
    def is_html(url):
        pattern = re.compile(r"(?:.+)\.html$")
        m = pattern.match(url)
        if m:
            return True
        else:
            return False

    @staticmethod
    # css解析下级链接
    def is_css(url):
        pattern = re.compile(r"(?:.+)\.css")
        m = pattern.match(url)
        if m:
            return True
        else:
            return False

    @staticmethod
    # 判断地址是否有效 TODO: 地址过滤, 目前无扩展名的地址全部过滤掉了
    def is_validate_url(url):
        if url.startswith('javascript') or url.startswith('#') or url == '':
            return False
        url_arr = url.split('/')
        last = url_arr.pop()
        if last.find('.') == -1:
            return False
        return True

    @classmethod
    # 解析出页面的所有url地址
    def get_urls(cls, url, save, max_repeat_time=5):
        urls = []
        repeat_time = 0
        if url[len(url) - 1] == '/':
            url += 'index.html'
        if cls.is_validate_url(url) is False:
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
            urls.extend(cls.fixed_url(url, cls.spider_content(url, f)))
            # 保存内容
            if save:
                cls.save_file(url, f)
        return urls

    @classmethod
    # 解析内容
    def spider_content(cls, url, f):
        urls = []
        if cls.is_html(url) is True:
            print("Reading the web ...")
            urls.extend(cls.resolve_html(f.content))
        if cls.is_css(url) is True:
            print("Reading the stylesheet ...")
            urls.extend(cls.resolve_style(f.text))

        return urls

    @classmethod
    # 保存数据
    def save_file(cls, url, res):
        delimiter = '/'
        parse_obj = urlparse(url)
        path = parse_obj.path
        p_url_arr = path.split('/')
        file_name = p_url_arr.pop()
        path = delimiter + delimiter.join(p_url_arr) + delimiter
        cls.check_dictionary(cls.save_path, path)
        search = file_name.find('?')
        if search != -1:
            file_name = file_name[0:search]
        file_name = re.sub(r'[\\\/:\*\?\"\'<>\|]', '_', file_name)
        name = cls.save_path + path + file_name
        with open(name, 'wb') as code:
            code.write(res.content)

    @classmethod
    # 地址补全
    def fixed_url(cls, original, urls):
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
                rel_url = scheme + '://' + netloc + '/' + cls.get_relative_url(path, url)
                fixed_urls.append(rel_url)
        return fixed_urls

    @classmethod
    # 获取相对路径地址
    def get_relative_url(cls, rel_path, url):
        p_len = len(rel_path)
        rel_path = cls.trip(rel_path)
        url = cls.trip(url)
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

    @classmethod
    # dfs深度优先遍历全站
    def dfs(cls, url, save):
        cls.visited.add(url)
        all_urls = cls.get_urls(url, save)
        if len(all_urls) == 0:
            return
        for page in all_urls:
            if page not in cls.sites:
                cls.sites.add(page)
            # TODO: url过滤不够严谨
            if page not in cls.visited and page.find(cls.domain) != -1:
                print("Visiting page", page)
                cls.dfs(page, save)
        print("success", url)