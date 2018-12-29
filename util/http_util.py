#!/usr/bin/env python
# -*- coding:utf-8 -*-
import urllib.request
import urllib.parse
import http.cookiejar
import traceback
import socket
import json

__author__ = 'jianghao'


class HttpUtil:
    def __init__(self):
        self.headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
          'Connection': 'keep-alive',
          }
        self.json_headers = {"content-type":"application/json;charset=UTF-8",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
            'Accept':'application/json, text/plain, */*',
            'Connection': 'keep-alive',
            "accept":"application/json, text/plain, */*"
            }
        self.opener = None
        self.url = ""
        self.timeout = 30
        socket.setdefaulttimeout(self.timeout)

    def get(self, host, url, params):
        self.url = 'http://' + host + url
        if params:
            params = urllib.parse.urlencode(params)
            #params = params.encode('UTF-8')
            self.url = self.url + '?' + params
        request = urllib.request.Request(self.url, headers=self.headers)
        try:
            response = urllib.request.urlopen(request)
            res = response.read().decode('utf-8')  # decode函数对获取的字节数据进行解码
            return res,response.getcode()
        except Exception:
            traceback.print_exc()
            return {}

    def json_post(self, host, url, data):
        jdata = json.dumps(data)
        jdata = jdata.encode("utf-8")
        self.url = 'http://' + host + url
        print(self.url)
        print(jdata)
        if not self.opener:
            cj = http.cookiejar.LWPCookieJar()
            cookie_support = urllib.request.HTTPCookieProcessor(cj)
            self.opener = urllib.request.build_opener(cookie_support,urllib.request.HTTPHandler)
        urllib.request.install_opener(self.opener)
        try:
            request = urllib.request.Request(self.url, headers=self.json_headers, data=jdata)
            response = urllib.request.urlopen(request)
            print(response)
            res = response.read().decode('utf-8')
            return res, response.getcode()
        except Exception as e:
            print('no json data returned')
            traceback.print_exc()
            return {}

    def post(self, host, url, data):
        data = urllib.parse.urlencode(data)
        data = data.encode('utf-8')
        self.url = 'http://' + host + url
        if not self.opener:
            cj = http.cookiejar.LWPCookieJar()
            cookie_support = urllib.request.HTTPCookieProcessor(cj)
            self.opener = urllib.request.build_opener(cookie_support,urllib.request.HTTPHandler)
        urllib.request.install_opener(self.opener)
        try:
            request = urllib.request.Request(self.url, headers=self.headers, data=data)
            response = urllib.request.urlopen(request)
            res = response.read().decode('utf-8')
            return res, response.getcode()
        except Exception as e:
            print('no json data returned')
            traceback.print_exc()
            return {}

    def get_url(self):
        return self.url


class HttpConnectMgr:
    http_connect = None

    def __init__(self):
        pass

    @staticmethod
    def get_http_connect():
        if HttpConnectMgr.http_connect is None:
            HttpConnectMgr.http_connect = HttpUtil()
        return HttpConnectMgr.http_connect
