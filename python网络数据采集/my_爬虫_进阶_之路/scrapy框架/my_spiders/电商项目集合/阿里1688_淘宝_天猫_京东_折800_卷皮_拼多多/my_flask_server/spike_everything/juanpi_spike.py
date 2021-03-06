# coding:utf-8

'''
@author = super_fazai
@File    : juanpi_spike.py
@Time    : 2017/11/20 16:57
@connect : superonesfazai@gmail.com
'''

from random import randint
import json
import requests
import re
import time
from pprint import pprint
import gc
import pytz
from selenium import webdriver
import selenium.webdriver.support.ui as ui
from time import sleep
import os

import sys
sys.path.append('..')

from settings import HEADERS
from juanpi_parse import JuanPiParse
from my_pipeline import SqlServerMyPageInfoSaveItemPipeline
from settings import IS_BACKGROUND_RUNNING
import datetime

class JuanPiSpike(object):
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Accept-Encoding:': 'gzip',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'm.juanpi.com',
            'User-Agent': HEADERS[randint(0, 34)]  # 随机一个请求头
        }

    def get_spike_hour_goods_info(self):
        '''
        模拟构造得到data的url，得到近期所有的限时秒杀商品信息
        :return:
        '''
        tab_id_list = [11, 12, 13, 21, 22, 23, 31, 32, 33]      # notice

        for tab_id in tab_id_list:
            for index in range(0, 50):
                tmp_url = 'https://m.juanpi.com/act/timebuy-xrgoodslist?tab_id={0}&page={1}'.format(
                    str(tab_id), str(index)
                )
                print('待抓取的限时秒杀地址为: ', tmp_url)

                # 设置代理ip
                self.proxies = self.get_proxy_ip_from_ip_pool()  # {'http': ['xx', 'yy', ...]}
                self.proxy = self.proxies['http'][randint(0, len(self.proxies) - 1)]

                tmp_proxies = {
                    'http': self.proxy,
                }
                # print('------>>>| 正在使用代理ip: {} 进行爬取... |<<<------'.format(self.proxy))

                try:
                    response = requests.get(tmp_url, headers=self.headers, proxies=tmp_proxies, timeout=10)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
                    data = response.content.decode('utf-8')
                    # print(data)
                except Exception:
                    print('requests.get()请求超时....')
                    print('data为空!')
                    break

                try:
                    data = json.loads(data)
                    data = data.get('data', {})
                    # print(data)
                except:
                    break

                if data.get('goodslist') == []:
                    print('tab_id={0}, page={1}的goodslist为[], 此处跳过'.format(tab_id, index))
                    break
                else:
                    data = data.get('goodslist', [])
                    # print(data)
                    if data == []:
                        print('goodslist为[], 此处跳过')
                        pass
                    else:
                        miaosha_goods_list = self.get_miaoshao_goods_info_list(data=data)
                        print(miaosha_goods_list)

                        juanpi = JuanPiParse()
                        my_pipeline = SqlServerMyPageInfoSaveItemPipeline()
                        if my_pipeline.is_connect_success:
                            if my_pipeline.select_juanpi_xianshimiaosha_all_goods_id() is None:
                                db_goods_id_list = []
                            else:
                                db_goods_id_list = [item[0] for item in list(my_pipeline.select_juanpi_xianshimiaosha_all_goods_id())]

                            for item in miaosha_goods_list:
                                if item.get('goods_id', '') in db_goods_id_list:
                                    print('该goods_id已经存在于数据库中, 此处跳过')
                                    pass
                                else:
                                    tmp_url = 'http://shop.juanpi.com/deal/' + item.get('goods_id')
                                    juanpi.get_goods_data(goods_id=item.get('goods_id'))
                                    goods_data = juanpi.deal_with_data()

                                    if goods_data == {}:    # 返回的data为空则跳过
                                        pass
                                    else:       # 否则就解析并插入
                                        goods_data['stock_info'] = item.get('stock_info')
                                        goods_data['goods_id'] = item.get('goods_id')
                                        goods_data['spider_url'] = tmp_url
                                        goods_data['username'] = '18698570079'
                                        goods_data['price'] = item.get('price')                 # 秒杀前的原特价
                                        goods_data['taobao_price'] = item.get('taobao_price')   # 秒杀价
                                        goods_data['sub_title'] = item.get('sub_title', '')
                                        goods_data['miaosha_time'] = item.get('miaosha_time')
                                        goods_data['miaosha_begin_time'], goods_data['miaosha_end_time'] = self.get_miaosha_begin_time_and_miaosha_end_time(miaosha_time=item.get('miaosha_time'))
                                        goods_data['tab_id'] = tab_id
                                        goods_data['page'] = index

                                        # print(goods_data)
                                        juanpi.insert_into_juanpi_xianshimiaosha_table(data=goods_data, pipeline=my_pipeline)
                                        sleep(.4)   # 短暂sleep下避免出错跳出
                            sleep(.65)
                        else:
                            pass
                        try:
                            del juanpi
                        except:
                            pass
                        gc.collect()

                        # else:           # 下面这3句用于跳出2层for循环
            #     continue    # continue表示执行成功就继续
            # break           # break表示执行失败就跳出

    def get_miaosha_begin_time_and_miaosha_end_time(self, miaosha_time):
        '''
        返回秒杀开始和结束时间
        :param miaosha_time:
        :return: tuple  miaosha_begin_time, miaosha_end_time
        '''
        miaosha_begin_time = miaosha_time.get('miaosha_begin_time')
        miaosha_end_time = miaosha_time.get('miaosha_end_time')
        # 将字符串转换为datetime类型
        miaosha_begin_time = datetime.datetime.strptime(miaosha_begin_time, '%Y-%m-%d %H:%M:%S')
        miaosha_end_time = datetime.datetime.strptime(miaosha_end_time, '%Y-%m-%d %H:%M:%S')

        return miaosha_begin_time, miaosha_end_time

    def get_miaoshao_goods_info_list(self, data):
        '''
        得到秒杀商品有用信息
        :param data: 待解析的data
        :return: 有用信息list
        '''
        miaosha_goods_list = []
        for item in data:
            tmp = {}
            tmp['miaosha_time'] = {
                'miaosha_begin_time': self.timestamp_to_regulartime(int(item.get('start_time'))),
                'miaosha_end_time': self.timestamp_to_regulartime(int(item.get('end_time'))),
            }
            stock = item.get('stock', 0)
            # 卷皮商品的goods_id
            tmp['goods_id'] = item.get('goods_id')
            # 限时秒杀库存信息
            tmp['stock_info'] = {
                'activity_stock': int(item.get('stock', 0)*(item.get('rate', 0)/100)),
                'stock': item.get('stock', 0),
            }
            # 原始价格
            tmp['price'] = round(float(item.get('oprice', '0')), 2)
            tmp['taobao_price'] = round(float(item.get('cprice', '0')), 2)
            miaosha_goods_list.append(tmp)

        return miaosha_goods_list

    def timestamp_to_regulartime(self, timestamp):
        '''
        将时间戳转换成时间
        '''
        # 利用localtime()函数将时间戳转化成localtime的格式
        # 利用strftime()函数重新格式化时间

        # 转换成localtime
        time_local = time.localtime(timestamp)
        # 转换成新的时间格式(2016-05-05 20:28:54)
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)

        return dt

    def get_proxy_ip_from_ip_pool(self):
        '''
        从代理ip池中获取到对应ip
        :return: dict类型 {'http': ['http://183.136.218.253:80', ...]}
        '''
        base_url = 'http://127.0.0.1:8000'
        result = requests.get(base_url).json()

        result_ip_list = {}
        result_ip_list['http'] = []
        for item in result:
            if item[2] > 7:
                tmp_url = 'http://' + str(item[0]) + ':' + str(item[1])
                result_ip_list['http'].append(tmp_url)
            else:
                delete_url = 'http://127.0.0.1:8000/delete?ip='
                delete_info = requests.get(delete_url + item[0])
        # pprint(result_ip_list)
        return result_ip_list

    def __del__(self):
        gc.collect()

def daemon_init(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    '''
    杀掉父进程，独立子进程
    :param stdin:
    :param stdout:
    :param stderr:
    :return:
    '''
    sys.stdin = open(stdin, 'r')
    sys.stdout = open(stdout, 'a+')
    sys.stderr = open(stderr, 'a+')
    try:
        pid = os.fork()
        if pid > 0:     # 父进程
            os._exit(0)
    except OSError as e:
        sys.stderr.write("first fork failed!!" + e.strerror)
        os._exit(1)

    # 子进程， 由于父进程已经退出，所以子进程变为孤儿进程，由init收养
    '''setsid使子进程成为新的会话首进程，和进程组的组长，与原来的进程组、控制终端和登录会话脱离。'''
    os.setsid()
    '''防止在类似于临时挂载的文件系统下运行，例如/mnt文件夹下，这样守护进程一旦运行，临时挂载的文件系统就无法卸载了，这里我们推荐把当前工作目录切换到根目录下'''
    os.chdir("/")
    '''设置用户创建文件的默认权限，设置的是权限“补码”，这里将文件权限掩码设为0，使得用户创建的文件具有最大的权限。否则，默认权限是从父进程继承得来的'''
    os.umask(0)

    try:
        pid = os.fork()  # 第二次进行fork,为了防止会话首进程意外获得控制终端
        if pid > 0:
            os._exit(0)  # 父进程退出
    except OSError as e:
        sys.stderr.write("second fork failed!!" + e.strerror)
        os._exit(1)

    # 孙进程
    #   for i in range(3, 64):  # 关闭所有可能打开的不需要的文件，UNP中这样处理，但是发现在python中实现不需要。
    #       os.close(i)
    sys.stdout.write("Daemon has been created! with pid: %d\n" % os.getpid())
    sys.stdout.flush()  # 由于这里我们使用的是标准IO，这里应该是行缓冲或全缓冲，因此要调用flush，从内存中刷入日志文件。

def just_fuck_run():
    while True:
        print('一次大抓取即将开始'.center(30, '-'))
        juanpi_spike = JuanPiSpike()
        juanpi_spike.get_spike_hour_goods_info()
        try:
            del juanpi_spike
        except:
            pass
        gc.collect()
        print('一次大抓取完毕, 即将重新开始'.center(30, '-'))

def main():
    '''
    这里的思想是将其转换为孤儿进程，然后在后台运行
    :return:
    '''
    print('========主函数开始========')  # 在调用daemon_init函数前是可以使用print到标准输出的，调用之后就要用把提示信息通过stdout发送到日志系统中了
    daemon_init()  # 调用之后，你的程序已经成为了一个守护进程，可以执行自己的程序入口了
    print('--->>>| 孤儿进程成功被init回收成为单独进程!')
    # time.sleep(10)  # daemon化自己的程序之后，sleep 10秒，模拟阻塞
    just_fuck_run()

if __name__ == '__main__':
    if IS_BACKGROUND_RUNNING:
        main()
    else:
        just_fuck_run()
