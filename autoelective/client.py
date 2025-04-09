#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: client.py
# modified: 2019-09-09

# request 第三方库
from requests.models import Request #创建和准备 HTTP 请求
from requests.sessions import Session #Session 对象使多个请求之间共享同一会话状态
from requests.cookies import extract_cookies_to_jar #提取 HTTP 响应中的 cookies 并将其保存到 cookie jar 中（即一个 Python 对象，用于管理 cookies）

class BaseClient(object):

    default_headers = {}
    default_client_timeout = 10

    def __init__(self, *args, **kwargs): #接收可变数量的位置/关键字参数
        if self.__class__ is __class__:
            raise NotImplementedError #抛出异常 某方法/功能尚未实现
        self._timeout = kwargs.get("timeout", self.__class__.default_client_timeout)
        self._session = Session()
        self._session.headers.update(self.__class__.default_headers)

    @property #将一个方法转变为属性
    def user_agent(self): #浏览器或爬虫在每次请求时附带的一个 HTTP 头，告诉服务器客户端的类型和版本
        return self._session.headers.get('User-Agent')

    def _request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):
            #method：HTTP请求类型（GET/POST/...）
            #url：请求的地址（网址）
            #params：url查询参数params = {'q': 'python', 'page': 2} URL会变成 https://example.com/search?q=python&page=2
            #data：发送的表单数据，data = {'username': 'myuser', 'password': 'mypassword'}
            #headers：包含请求额外信息的字典，User-Agent（浏览器信息）、Content-Type（数据类型）、Authorization（身份验证）等
            #cookies：cookies = {'session_id': '1234567890'}
            #files：用来上传文件，通常用于 POST 请求
            #auth：用来进行基本的HTTP认证的元组 (username, password)
            #allow_redirects：是否允许自动跟随HTTP重定向
            #proxies：指定通过代理服务器发送请求，proxies = {'http': 'http://myproxy.com', 'https': 'https://myproxy.com'}
            #hooks：用来设置在请求和响应过程中触发的回调函数
            #stream：是否以流的形式处理响应。默认一次性下载整个响应。如果 stream=True，响应体会被分块接收，可以处理大型文件下载或上传
            #cert：用于设置客户端证书
            #json：用于直接发送JSON数据，json = {"key": "value"}
        # Extended from requests/sessions.py  for '_client' kwargs

        req = Request(
            method=method.upper(), #转大写字符
            url=url,
            headers=headers,
            files=files,
            data=data or {}, #data 有值则data，否则空
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            hooks=hooks,
        )
        prep = self._session.prepare_request(req)
        prep._client = self  # hold the reference to client


        proxies = proxies or {}

        settings = self._session.merge_environment_settings(
            prep.url, proxies, stream, verify, cert
        )

        # Send the request.
        send_kwargs = {
            'timeout': timeout or self._timeout, # set default timeout
            'allow_redirects': allow_redirects,
        }
        send_kwargs.update(settings)
        resp = self._session.send(prep, **send_kwargs)

        return resp

    def _get(self, url, params=None, **kwargs): #请求获取数据
        return self._request('GET', url,  params=params, **kwargs)

    def _post(self, url, data=None, json=None, **kwargs): #请求提交数据
        return self._request('POST', url, data=data, json=json, **kwargs)

    def set_user_agent(self, user_agent):
        self._session.headers["User-Agent"] = user_agent

    def persist_cookies(self, r):
        """
        From requests/sessions.py, Session.send()

        Session.send() 方法会首先 dispatch_hook 然后再 extract_cookies_to_jar

        在该项目中，对于返回信息异常的请求，在 hooks 校验时会将错误抛出，send() 之后的处理将不会执行。
        遇到的错误往往是 SystemException / TipsException ，而这些客户端认为是错误的情况，
        对于服务器端来说并不是错误请求，服务器端在该次请求结束后可能会要求 Set-Cookies
        但是由于 send() 在 dispatch_hook 时遇到错误而中止，导致后面的 extract_cookies_to_jar
        未能调用，因此 Cookies 并未更新。下一次再请求服务器的时候，就会遇到会话过期的情况。

        在这种情况下，需要在捕获错误后手动更新 cookies 以确保能够保持会话

        """
        if r.history:

            # If the hooks create history then we want those cookies too
            for resp in r.history:
                extract_cookies_to_jar(self._session.cookies, resp.request, resp.raw)

        extract_cookies_to_jar(self._session.cookies, r.request, r.raw)

    def clear_cookies(self):
        self._session.cookies.clear()
