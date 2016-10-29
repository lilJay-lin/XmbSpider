import requests
import os
import re
import time
import threading
from queue import Queue
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class VisitThread(threading.Thread):
    def __init__(self, urls_queue, contents_queue, m_visited, m_all_pages, max_repeat_time=5):
        self.urls_queue = urls_queue
        self.contents_queue = contents_queue
        self.max_repeat_time = max_repeat_time
        self.visited = m_visited
        self.all_pages = m_all_pages
        self.over = 0
        self.sleep = time.time()
        threading.Thread.__init__(self)

    def run(self):
        while True:
            url = self.urls_queue.get()
            try:
                if url not in visited:
                    self.request_url(url)
                visited.add(url)
            except:
                pass
            finally:
                self.urls_queue.task_done()

    def request_url(self, url):
        repeat_time = 0
        if url[len(url) - 1] == '/':
            url += 'index.html'
        while True:
            if self.is_validate_url(url):
                try:
                    print("Ready to Open the Web")
                    '''time.sleep(1)'''
                    print("opening the Web", url)
                    f = requests.get(url, timeout=3)
                    status = f.status_code
                    if status == 200:
                        self.contents_queue.put(f)
                    print("Success to Open the Web")
                    break;
                except:
                    print("Open Url Failed !!! Repeat")
                    time.sleep(1)
                    repeat_time += 1
                    # TODO:失败的要存进失败记录
                    if repeat_time == self.max_repeat_time:
                        break
            else:
                break

    # 判断地址是否有效 TODO: 地址过滤, 目前无扩展名的地址全部过滤掉了
    @staticmethod
    def is_validate_url(url):
        if url.startswith('javascript') or url.startswith('#') or url == '':
            return False
        url_arr = url.split('/')
        last = url_arr.pop()
        if last.find('.') == -1:
            return False
        return True


class ResolveThread(threading.Thread):
    save_path = 'e:\spider'

    def __init__(self, urls_queue, contents_queue, m_visited, m_all_pages, m_domain, save_path='e:\spider'):
        self.urls_queue = urls_queue
        self.contents_queue = contents_queue
        self.save_path = save_path
        self.domain = m_domain
        self.visited = m_visited
        self.all_pages = m_all_pages
        self.sleep = time.time()
        threading.Thread.__init__(self)

    def run(self):
        while True:
            response = self.contents_queue.get()
            url = response.url
            print('正在处理请求', url)
            # 解析页面内容的下级链接
            if self.domain in url:
                urls = self.fixed_url(url, self.spider_content(response))
                for _url in urls:
                    if self.domain in _url:
                        self.all_pages.add(_url)
                        self.urls_queue.put(_url)
            # 保存内容
            self.save_file(url, response)
            print('Content had being save')
            self.contents_queue.task_done()

    @classmethod
    # 解析内容
    def spider_content(cls, response):
        urls = []
        content_type = response.headers['Content-Type']
        if content_type.find('text/html') != -1:
            print("Reading the web ...")
            urls.extend(cls.resolve_html(response.content))
        elif content_type.find('text/css') != -1:
            print("Reading the stylesheet ...")
            urls.extend(cls.resolve_style(response.text))

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
            if len(url) == 0:
                continue
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


class CheckOver(threading.Thread):
    def __init__(self, m_all_urls, m_contents,m_visited, m_all):
        self.all_urls = m_all_urls
        self.contents = m_contents
        self.visited = m_visited
        self.all = m_all
        self.all_is_done = False
        self.flag = 0
        threading.Thread.__init__(self)

    def run(self):
        while self.all_is_done is False:
            if len(self.visited) == len(self.all):
                self.flag += 1
                time.sleep(3)
                print('check thread %s' % self.flag)
                if self.flag == 3:
                    self.all_is_done = True
            else:
                self.flag = 0
if __name__ == '__main__':
    contents = Queue()
    all_urls = Queue()
    visited = set()
    all_pages = set()
    all_urls.put('http://www.jq22.com/demo/bootstrap-150308231052/index.html')
    domain = 'www.jq22.com'
    start = time.time()
    threads = 8
    for i in range(threads):
        v = VisitThread(all_urls, contents, visited, all_pages, domain)
        v.start()
    for i in range(threads):
        r = ResolveThread(all_urls, contents, visited, all_pages, domain)
        r.start()
    check = CheckOver(all_urls, contents, visited, all_pages)
    check.start()
    all_urls.join()
    contents.join()
    check.join()
    print("Elapsed Time: %s" % (time.time() - start))



