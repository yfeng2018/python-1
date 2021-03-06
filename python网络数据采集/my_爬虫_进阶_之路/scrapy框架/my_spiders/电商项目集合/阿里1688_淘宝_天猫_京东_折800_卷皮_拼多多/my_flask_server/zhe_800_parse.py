# coding:utf-8

'''
@author = super_fazai
@File    : zhe_800_parse.py
@Time    : 2017/11/13 12:28
@connect : superonesfazai@gmail.com
'''

"""
折800页面采集系统
"""

import time
from random import randint
import json
import requests
import re
from pprint import pprint
from decimal import Decimal
from time import sleep
import datetime
import re
import gc
import pytz

from settings import HEADERS

class Zhe800Parse(object):
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Accept-Encoding:': 'gzip',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'm.zhe800.com',
            'User-Agent': HEADERS[randint(0, 34)]  # 随机一个请求头
        }
        self.result_data = {}

    def get_goods_data(self, goods_id):
        '''
        模拟构造得到data的url
        :param goods_id:
        :return: data   类型dict
        '''
        if goods_id == '':
            self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
            return {}
        else:
            tmp_url = 'https://m.zhe800.com/gateway/app/detail/product?productId=' + str(goods_id)
            # print('------>>>| 得到的detail信息的地址为: ', tmp_url)

            # 设置代理ip
            self.proxies = self.get_proxy_ip_from_ip_pool()  # {'http': ['xx', 'yy', ...]}
            self.proxy = self.proxies['http'][randint(0, len(self.proxies) - 1)]

            tmp_proxies = {
                'http': self.proxy,
            }
            # print('------>>>| 正在使用代理ip: {} 进行爬取... |<<<------'.format(self.proxy))

            try:
                response = requests.get(tmp_url, headers=self.headers, proxies=tmp_proxies, timeout=12)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
                data = response.content.decode('utf-8')
                # print(data)
                data = re.compile(r'(.*)').findall(data)  # 贪婪匹配匹配所有
                # print(data)
            except Exception:
                print('requests.get()请求超时....')
                print('data为空!')
                self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                return {}

            if data != []:
                data = data[0]
                try:
                    data = json.loads(data)
                except Exception:
                    self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                    return {}
                # pprint(data)

                # 处理base
                base = data.get('/app/detail/product/base', '')
                try:
                    base = json.loads(base)
                except Exception:
                    print("json.loads转换出错，得到base值可能为空，此处跳过")
                    base = ''
                    pass

                # 处理profiles
                profiles = data.get('/app/detail/product/profiles', '')
                try:
                    profiles = json.loads(profiles)
                except Exception:
                    print("json.loads转换出错，得到profiles值可能为空，此处跳过")
                    profiles = ''
                    pass

                # 处理score
                score = data.get('/app/detail/product/score', '')
                try:
                    score = json.loads(score)
                    try:
                        score.pop('contents')
                    except:
                        pass
                except Exception:
                    print("json.loads转换出错，得到score值可能为空，此处跳过")
                    score = ''
                    pass

                # 处理sku
                sku = data.get('/app/detail/product/sku', '')
                try:
                    sku = json.loads(sku)
                except Exception:
                    print("json.loads转换出错，得到sku值可能为空，此处跳过")
                    sku = ''
                    pass

                data['/app/detail/product/base'] = base
                data['/app/detail/product/profiles'] = profiles
                data['/app/detail/product/score'] = score
                data['/app/detail/product/sku'] = sku

                # 得到手机版地址
                phone_url = ''
                try:
                    phone_url = 'http://th5.m.zhe800.com/h5/shopdeal?id=' + str(base.get('dealId', ''))
                except AttributeError:
                    print('获取手机版地址失败，此处跳过')
                    self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                    return {}

                print('------>>>| 得到商品手机版地址为: ', phone_url)
                # print('------>>>| 正在使用代理ip: {} 进行爬取... |<<<------'.format(self.proxy))

                # 得到并处理detail(即图文详情显示信息)
                # http://m.zhe800.com/gateway/app/detail/graph?productId=
                tmp_detail_url = 'https://m.zhe800.com/gateway/app/detail/graph?productId=' + str(goods_id)
                try:
                    response = requests.get(tmp_detail_url, headers=self.headers, proxies=tmp_proxies, timeout=10)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
                    detail_data = response.content.decode('utf-8')
                    # print(detail_data)
                    detail_data = re.compile(r'(.*)').findall(detail_data)  # 贪婪匹配匹配所有
                    # print(detail_data)
                except Exception:   # 未拿到图文详情就跳出
                    print('requests.get()请求超时....')
                    print('detail_data为空!')
                    self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                    return {}

                if detail_data != []:
                    detail_data = detail_data[0]
                    try:
                        detail_data = json.loads(detail_data)
                    except Exception:
                        print('json.loads(detail_data)时报错, 此处跳过')
                        self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                        return {}
                    # pprint(detail_data)

                    detail = detail_data.get('/app/detail/graph/detail', '')
                    try:
                        detail = json.loads(detail)
                        try:
                            detail.pop('small')
                        except:
                            pass
                    except:
                        print("json.loads转换出错，得到detail值可能为空，此处跳过")
                        detail = ''
                        pass
                    # print(detail)

                    '''
                    处理detail_data转换成能被html显示页面信息
                    '''
                    tmp_div_desc = ''
                    if isinstance(detail, dict):
                        if detail.get('detailImages') is not None:
                            for item in detail.get('detailImages', []):
                                tmp = ''
                                tmp_big = item.get('big', '')
                                tmp_height = item.get('height', 0)
                                tmp_width = item.get('width', 0)
                                # tmp = r'<img src="{}" style="height:{}px;width:{}px;"/>'.format(tmp_big, tmp_height, tmp_width)
                                tmp = r'<img src="{}" style="height:auto;width:100%;"/>'.format(tmp_big)
                                tmp_div_desc += tmp

                        if detail.get('noticeImage') is not None:
                            if isinstance(detail.get('noticeImage'), dict):
                                item = detail.get('noticeImage')
                                tmp = ''
                                tmp_image = item.get('image', '')
                                tmp_height = item.get('height', 0)
                                tmp_width = item.get('width', 0)
                                # tmp = r'<img src="{}" style="height:{}px;width:{}px;"/>'.format(tmp_image, tmp_height, tmp_width)
                                tmp = r'<img src="{}" style="height:auto;width:100%;"/>'.format(tmp_image)
                                tmp_div_desc += tmp
                            elif isinstance(detail.get('noticeImage'), list):
                                for item in detail.get('noticeImage', []):
                                    tmp = ''
                                    tmp_image = item.get('image', '')
                                    tmp_height = item.get('height', 0)
                                    tmp_width = item.get('width', 0)
                                    # tmp = r'<img src="{}" style="height:{}px;width:{}px;"/>'.format(tmp_image, tmp_height, tmp_width)
                                    tmp = r'<img src="{}" style="height:auto;width:100%;"/>'.format(tmp_image)
                                    tmp_div_desc += tmp
                            else:
                                pass

                            '''
                            处理有尺码的情况(将其加入到div_desc中)
                            '''
                            tmp_size_url = 'https://m.zhe800.com/app/detail/product/size?productId=' + str(goods_id)
                            try:
                                response = requests.get(tmp_size_url, headers=self.headers, proxies=tmp_proxies, timeout=10)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
                                size_data = response.content.decode('utf-8')
                                size_data = re.compile(r'(.*)').findall(size_data)  # 贪婪匹配匹配所有
                                # print(size_data)
                            except Exception:  # 未拿到图文详情就跳出
                                print('requests.get()请求超时....')
                                print('size_data为空!')
                                self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                                return {}

                            if size_data != []:
                                size_data = size_data[0]
                                try:
                                    size_data = json.loads(size_data)
                                except Exception:
                                    print('json.loads(size_data)出错, 此处跳过')
                                    self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                                    return {}

                                # pprint(size_data)

                                tmp_div_desc_2 = ''
                                if size_data is not None:
                                    charts = size_data.get('charts', [])
                                    for item in charts:
                                        # print(item)
                                        tmp = ''
                                        charts_data = item.get('data', [])     # table
                                        title = item.get('title', '')
                                        for item2 in charts_data:        # item为一个list
                                            # print(item2)
                                            charts_item = ''
                                            for i in item2:              # i为一个dict
                                                # print(i)
                                                data_value = i.get('value', '')
                                                tmp_1 = '<td style="vertical-align:inherit;display:table-cell;font-size:12px;color:#666;border:#666 1px solid;">{}</td>'.format(data_value)
                                                charts_item += tmp_1
                                            charts_item = '<tr style="border:#666 1px solid;">' + charts_item + '</tr>'
                                            # print(charts_item)
                                            tmp += charts_item
                                        tmp = '<div>' + '<strong style="color:#666;">'+ title + '</strong>' + '<table style="border-color:grey;border-collapse:collapse;text-align:center;line-height:25px;background:#fff;border-spacing:0;border:#666 1px solid;"><tbody style="border:#666 1px solid;">' + tmp + '</tbody></table></div><br>'
                                        tmp_div_desc_2 += tmp
                                    # print(tmp_div_desc_2)
                                else:
                                    pass
                            else:
                                tmp_div_desc_2 = ''

                        else:
                            tmp_div_desc_2 = ''
                            pass
                        tmp_div_desc = tmp_div_desc_2 + '<div>' + tmp_div_desc + '</div>'

                    # print(tmp_div_desc)
                    data['/app/detail/graph/detail'] = tmp_div_desc

                    '''
                    得到shop_name
                    '''
                    seller_id = data.get('/app/detail/product/base', {}).get('sellerId', 0)
                    tmp_seller_id_url = 'https://m.zhe800.com/api/getsellerandswitch?sellerId=' + str(seller_id)

                    try:
                        response = requests.get(tmp_seller_id_url, headers=self.headers, proxies=tmp_proxies, timeout=10)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
                        seller_info = response.content.decode('utf-8')
                        seller_info = re.compile(r'(.*)').findall(seller_info)  # 贪婪匹配匹配所有
                        # print(seller_info)
                    except Exception:  # 未拿到图文详情就跳出
                        print('requests.get()请求超时....')
                        print('seller_info为空!')
                        self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                        return {}

                    if seller_info != []:
                        seller_info = seller_info[0]
                        try:
                            seller_info = json.loads(seller_info)
                        except Exception:
                            print('卖家信息在转换时出现错误, 此处跳过')
                            self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                            return {}

                        # pprint(seller_info)
                        shop_name = seller_info.get('sellerInfo', {}).get('nickName', '')
                    else:
                        shop_name = ''
                    # print(shop_name)
                    data['shop_name'] = shop_name

                    '''
                    得到秒杀开始时间和结束时间
                    '''
                    schedule_and_stock_url = 'https://m.zhe800.com/gateway/app/detail/status?productId=' + str(goods_id)
                    try:
                        response = requests.get(schedule_and_stock_url, headers=self.headers, proxies=tmp_proxies, timeout=10)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
                        schedule_and_stock_info = response.content.decode('utf-8')
                        schedule_and_stock_info = re.compile(r'(.*)').findall(schedule_and_stock_info)  # 贪婪匹配匹配所有
                        # print(schedule_and_stock_info)
                    except Exception:  # 未拿到图文详情就跳出
                        print('requests.get()请求超时....')
                        print('schedule_and_stock_info为空!')
                        self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                        return {}

                    if schedule_and_stock_info != []:
                        schedule_and_stock_info = schedule_and_stock_info[0]
                        try:
                            schedule_and_stock_info = json.loads(schedule_and_stock_info)
                        except Exception:
                            print('得到秒杀开始时间和结束时间时错误, 此处跳过')
                            self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                            return {}

                        schedule = schedule_and_stock_info.get('/app/detail/status/schedule')
                        if schedule is None:
                            schedule = {}
                        else:
                            try:
                                schedule = json.loads(schedule)
                            except:
                                schedule = {}

                        stock = schedule_and_stock_info.get('/app/detail/status/stock')
                        if stock is None:
                            stock = {}
                        else:
                            try:
                                stock = json.loads(stock)
                            except:
                                stock = {}
                    else:
                        schedule = {}
                        stock = {}
                    data['schedule'] = schedule
                    data['stock'] = stock

                    # pprint(data)
                    self.result_data = data
                    return data

                else:
                    print('detail_data为空!')
                    self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                    return {}

            else:
                print('data为空!')
                self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                return {}

    def deal_with_data(self):
        '''
        处理result_data, 返回需要的信息
        :return: 字典类型
        '''
        data = self.result_data
        if data != {}:
            # 店铺名称
            shop_name = data.get('shop_name', '')
            # print(shop_name)

            # 掌柜
            account = ''

            # 商品名称
            title = data.get('/app/detail/product/base', {}).get('title', '')
            # print(title)

            # 子标题
            sub_title = ''

            # 商品库存
            # 商品标签属性对应的值

            # 要存储的每个标签对应规格的价格及其库存
            try:
                tmp_price_info_list = data.get('/app/detail/product/sku', {}).get('items')
            except AttributeError as e:     # 表示获取失败
                print('AttributeError属性报错，为: ', e)
                print("data.get('/app/detail/product/sku', {}).get('items')获取失败, 此处跳过")
                return {}

            # pprint(tmp_price_info_list)
            detail_name_list = []   # 初始化
            price_info_list = []
            price = ''              # 先初始化
            taobao_price = ''
            # pprint(tmp_price_info_list)
            if len(tmp_price_info_list) == 1:     # 说明没有规格属性, 只有价格
                is_spec = False
                if tmp_price_info_list[0].get('curPrice', '') != '':
                    # 商品价格
                    # 淘宝价
                    price = round(float(tmp_price_info_list[0].get('curPrice', '')), 2)
                    taobao_price = price
                else:
                    price = round(float(tmp_price_info_list[0].get('orgPrice', '')), 2)
                    taobao_price = price
            else:                               # 有规格属性
                is_spec = True
                stock_items = data.get('stock', {}).get('stockItems')   # [{'count': 100, 'lockCount': 0, 'skuNum': '1-1001:2-1121'}, ...]
                # pprint(stock_items)
                for index in range(1, len(tmp_price_info_list)):
                    # 商品标签属性名称
                    detail_name_list = [{'spec_name': item.split('-')[0]} for item in tmp_price_info_list[index].get('propertyName').split(':')]
                    tmp_spec_value_1 = [str(item.split('-')[1]) for item in tmp_price_info_list[index].get('propertyName').split(':')]  # ['红格', 'S']
                    tmp_spec_value_2 = '|'.join(tmp_spec_value_1)   # '红格|S'
                    # print(tmp_spec_value_2)
                    property_num = tmp_price_info_list[index].get('propertyNum', '')
                    picture = tmp_price_info_list[index].get('vPictureBig', '')
                    if stock_items is None:     # 没有规格时, price,taobao_price值的设定
                        is_spec = False
                        price_info_list = []
                        if tmp_price_info_list[0].get('curPrice', '') != '':
                            price = tmp_price_info_list[0].get('curPrice', '')
                            taobao_price = price
                        else:
                            price = tmp_price_info_list[0].get('orgPrice', '')
                            taobao_price = price
                    else:   # 有规格的情况
                        is_spec = True
                        # 每个规格对应的库存量
                        count = [item.get('count', 0) for item in stock_items if property_num == item.get('skuNum', '')][0]
                        if tmp_price_info_list[index].get('curPrice', '') != '':    # 促销价不为空
                            tmp = {
                                'spec_value': tmp_spec_value_2,
                                'detail_price': tmp_price_info_list[index].get('curPrice', ''),
                                'rest_number': count,
                                'img_url': picture,
                            }
                        else:   # 促销价为空值
                            tmp = {
                                'spec_value': tmp_spec_value_2,
                                'detail_price': tmp_price_info_list[index].get('orgPrice', ''),
                                'rest_number': count,
                                'img_url': picture,
                            }
                        price_info_list.append(tmp)

            if is_spec:     # 得到有规格时的最高价和最低价
                tmp_price_list = sorted([round(float(item.get('detail_price', '')), 2) for item in price_info_list])
                price = tmp_price_list[-1]          # 商品价格
                taobao_price = tmp_price_list[0]    # 淘宝价

            # print('最高价为: ', price)
            # print('最低价为: ', taobao_price)
            # print(detail_name_list)
            # pprint(price_info_list)

            # 所有示例图片地址
            tmp_all_img_url = data.get('/app/detail/product/base', {}).get('images', [])
            all_img_url = [{'img_url': item['big']} for item in tmp_all_img_url]
            # pprint(all_img_url)

            # 详细信息标签名对应属性
            try:
                profiles = data.get('/app/detail/product/profiles', {}).get('profiles')
            except AttributeError as e:
                print('AttributeError属性报错，为: ', e)
                print("data.get('/app/detail/product/profiles', {}).get('profiles')获取失败, 此处跳过")
                return {}

            if profiles is None:
                p_info = []
            else:
                p_info = [{'p_name': item['name'], 'p_value': item['value']} for item in profiles]
            # pprint(p_info)

            # div_desc
            div_desc = data.get('/app/detail/graph/detail', '')

            # 用于判断商品是否已经下架
            is_delete = 0
            schedule = data.get('schedule')
            # pprint(schedule)
            if schedule is None:
                is_delete = 1       # 没有活动时间就表示已经下架
                schedule = []
            else:   # 开始的和未开始的都是能拿到时间的，所以没问题，嘿嘿-_-!!
                schedule = [{
                    'begin_time': schedule.get('beginTime', ''),
                    'end_time': schedule.get('endTime', '')
                }]
            # pprint(schedule)

            result = {
                'shop_name': shop_name,                     # 店铺名称
                'account': account,                         # 掌柜
                'title': title,                             # 商品名称
                'sub_title': sub_title,                     # 子标题
                # 'shop_name_url': shop_name_url,            # 店铺主页地址
                'price': price,                             # 商品价格
                'taobao_price': taobao_price,               # 淘宝价
                # 'goods_stock': goods_stock,                # 商品库存
                'detail_name_list': detail_name_list,       # 商品标签属性名称
                # 'detail_value_list': detail_value_list,    # 商品标签属性对应的值
                'price_info_list': price_info_list,         # 要存储的每个标签对应规格的价格及其库存
                'all_img_url': all_img_url,                 # 所有示例图片地址
                'p_info': p_info,                           # 详细信息标签名对应属性
                'div_desc': div_desc,                       # div_desc
                'schedule': schedule,                       # 商品开卖时间和结束开卖时间
                'is_delete': is_delete                      # 用于判断商品是否已经下架
            }
            pprint(result)
            # print(result)
            # wait_to_send_data = {
            #     'reason': 'success',
            #     'data': result,
            #     'code': 1
            # }
            # json_data = json.dumps(wait_to_send_data, ensure_ascii=False)
            # print(json_data)
            return result

        else:
            print('待处理的data为空的dict, 该商品可能已经转移或者下架')
            # return {
            #     'is_delete': 1,
            # }
            return {}

    def to_right_and_update_data(self, data, pipeline):
        data_list = data
        tmp = {}
        tmp['goods_id'] = data_list['goods_id']  # 官方商品id

        '''
        时区处理，时间处理到上海时间
        '''
        tz = pytz.timezone('Asia/Shanghai')  # 创建时区对象
        now_time = datetime.datetime.now(tz)
        # 处理为精确到秒位，删除时区信息
        now_time = re.compile(r'\..*').sub('', str(now_time))
        # 将字符串类型转换为datetime类型
        now_time = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')

        tmp['modfiy_time'] = now_time  # 修改时间

        tmp['shop_name'] = data_list['shop_name']  # 公司名称
        tmp['title'] = data_list['title']  # 商品名称
        tmp['sub_title'] = data_list['sub_title']  # 商品子标题
        tmp['link_name'] = ''  # 卖家姓名
        tmp['account'] = data_list['account']  # 掌柜名称

        # 设置最高价price， 最低价taobao_price
        tmp['price'] = Decimal(data_list['price']).__round__(2)
        tmp['taobao_price'] = Decimal(data_list['taobao_price']).__round__(2)
        tmp['price_info'] = []  # 价格信息

        tmp['detail_name_list'] = data_list['detail_name_list']  # 标签属性名称

        """
        得到sku_map
        """
        tmp['price_info_list'] = data_list.get('price_info_list')  # 每个规格对应价格及其库存

        tmp['all_img_url'] = data_list.get('all_img_url')  # 所有示例图片地址

        tmp['p_info'] = data_list.get('p_info')  # 详细信息
        tmp['div_desc'] = data_list.get('div_desc')  # 下方div

        tmp['schedule'] = data_list.get('schedule')

        # 采集的来源地
        # tmp['site_id'] = 11  # 采集来源地(折800常规商品)

        tmp['is_delete'] = data_list.get('is_delete')  # 逻辑删除, 未删除为0, 删除为1
        tmp['my_shelf_and_down_time'] = data_list.get('my_shelf_and_down_time')
        tmp['delete_time'] = data_list.get('delete_time')

        pipeline.update_zhe_800_table(item=tmp)

    def insert_into_zhe_800_xianshimiaosha_table(self, data, pipeline):
        data_list = data
        tmp = {}
        tmp['goods_id'] = data_list['goods_id']  # 官方商品id
        tmp['spider_url'] = data_list['spider_url']  # 商品地址
        tmp['username'] = data_list['username']  # 操作人员username

        '''
        时区处理，时间处理到上海时间
        '''
        tz = pytz.timezone('Asia/Shanghai')  # 创建时区对象
        now_time = datetime.datetime.now(tz)
        # 处理为精确到秒位，删除时区信息
        now_time = re.compile(r'\..*').sub('', str(now_time))
        # 将字符串类型转换为datetime类型
        now_time = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')

        tmp['deal_with_time'] = now_time  # 操作时间
        tmp['modfiy_time'] = now_time  # 修改时间

        tmp['shop_name'] = data_list['shop_name']  # 公司名称
        tmp['title'] = data_list['title']          # 商品名称
        tmp['sub_title'] = data_list['sub_title']

        # 设置最高价price， 最低价taobao_price
        try:
            tmp['price'] = Decimal(data_list['price']).__round__(2)
            tmp['taobao_price'] = Decimal(data_list['taobao_price']).__round__(2)
        except:     # 此处抓到的可能是折800秒杀券所以跳过
            print('此处抓到的可能是折800秒杀券所以跳过')
            return None

        tmp['detail_name_list'] = data_list['detail_name_list']  # 标签属性名称

        """
        得到sku_map
        """
        tmp['price_info_list'] = data_list.get('price_info_list')  # 每个规格对应价格及其库存

        tmp['all_img_url'] = data_list.get('all_img_url')  # 所有示例图片地址

        tmp['p_info'] = data_list.get('p_info')  # 详细信息
        tmp['div_desc'] = data_list.get('div_desc')  # 下方div

        tmp['schedule'] = data_list.get('schedule')
        tmp['stock_info'] = data_list.get('stock_info')
        tmp['miaosha_time'] = data_list.get('miaosha_time')
        tmp['session_id'] = data_list.get('session_id')

        # 采集的来源地
        tmp['site_id'] = 14  # 采集来源地(折800秒杀商品)

        tmp['miaosha_begin_time'] = data_list.get('miaosha_begin_time')
        tmp['miaosha_end_time'] = data_list.get('miaosha_end_time')

        tmp['is_delete'] = data_list.get('is_delete')  # 逻辑删除, 未删除为0, 删除为1
        # print('is_delete=', tmp['is_delete'])

        # print('------>>> | 待存储的数据信息为: |', tmp)
        print('------>>> | 待存储的数据信息为: |', tmp.get('goods_id'))

        pipeline.insert_into_zhe_800_xianshimiaosha_table(tmp)

    def to_update_zhe_800_xianshimiaosha_table(self, data, pipeline):
        data_list = data
        tmp = {}
        tmp['goods_id'] = data_list['goods_id']  # 官方商品id

        '''
        时区处理，时间处理到上海时间
        '''
        tz = pytz.timezone('Asia/Shanghai')  # 创建时区对象
        now_time = datetime.datetime.now(tz)
        # 处理为精确到秒位，删除时区信息
        now_time = re.compile(r'\..*').sub('', str(now_time))
        # 将字符串类型转换为datetime类型
        now_time = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')

        tmp['modfiy_time'] = now_time  # 修改时间

        tmp['shop_name'] = data_list['shop_name']  # 公司名称
        tmp['title'] = data_list['title']          # 商品名称
        tmp['sub_title'] = data_list['sub_title']

        # 设置最高价price， 最低价taobao_price
        tmp['price'] = Decimal(data_list['price']).__round__(2)
        tmp['taobao_price'] = Decimal(data_list['taobao_price']).__round__(2)

        tmp['detail_name_list'] = data_list['detail_name_list']  # 标签属性名称

        """
        得到sku_map
        """
        tmp['price_info_list'] = data_list.get('price_info_list')  # 每个规格对应价格及其库存

        tmp['all_img_url'] = data_list.get('all_img_url')  # 所有示例图片地址

        tmp['p_info'] = data_list.get('p_info')  # 详细信息
        tmp['div_desc'] = data_list.get('div_desc')  # 下方div

        tmp['schedule'] = data_list.get('schedule')
        tmp['stock_info'] = data_list.get('stock_info')
        tmp['miaosha_time'] = data_list.get('miaosha_time')
        tmp['miaosha_begin_time'] = data_list.get('miaosha_begin_time')
        tmp['miaosha_end_time'] = data_list.get('miaosha_end_time')

        tmp['is_delete'] = data_list.get('is_delete')  # 逻辑删除, 未删除为0, 删除为1
        # print('is_delete=', tmp['is_delete'])

        # print('------>>> | 待存储的数据信息为: |', tmp)
        print('------>>> | 待存储的数据信息为: |', tmp.get('goods_id'))

        pipeline.update_zhe_800_xianshimiaosha_table(tmp)

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

    def get_goods_id_from_url(self, zhe_800_url):
        '''
        得到goods_id
        :param zhe_800_url:
        :return: goods_id (类型str)
        '''
        is_zhe_800_url = re.compile(r'https://shop.zhe800.com/products/.*?').findall(zhe_800_url)
        if is_zhe_800_url != []:
            if re.compile(r'https://shop.zhe800.com/products/(.*?)\?.*?').findall(zhe_800_url) != []:
                tmp_zhe_800_url = re.compile(r'https://shop.zhe800.com/products/(.*?)\?.*?').findall(zhe_800_url)[0]
                if tmp_zhe_800_url != '':
                    goods_id = tmp_zhe_800_url
                else:
                    zhe_800_url = re.compile(r';').sub('', zhe_800_url)
                    goods_id = re.compile(r'https://shop.zhe800.com/products/(.*?)\?.*?').findall(zhe_800_url)[0]
                print('------>>>| 得到的折800商品id为:', goods_id)
                return goods_id
            else:   # 处理从数据库中取出的数据
                zhe_800_url = re.compile(r';').sub('', zhe_800_url)
                goods_id = re.compile(r'https://shop.zhe800.com/products/(.*)').findall(zhe_800_url)[0]
                print('------>>>| 得到的折800商品id为:', goods_id)
                return goods_id
        else:
            is_miao_sha_url = re.compile(r'https://miao.zhe800.com/products/.*?').findall(zhe_800_url)
            if is_miao_sha_url != []:   # 先不处理这种链接的情况
                if re.compile(r'https://miao.zhe800.com/products/(.*?)\?.*?').findall(zhe_800_url) != []:
                    tmp_zhe_800_url = re.compile(r'https://miao.zhe800.com/products/(.*?)\?.*?').findall(zhe_800_url)[0]
                    if tmp_zhe_800_url != '':
                        goods_id = tmp_zhe_800_url
                    else:
                        zhe_800_url = re.compile(r';').sub('', zhe_800_url)
                        goods_id = re.compile(r'https://miao.zhe800.com/products/(.*?)\?.*?').findall(zhe_800_url)[0]
                    print('------>>>| 得到的限时秒杀折800商品id为:', goods_id)
                    print('由于这种商品开头的量少, 此处先不处理这种开头的')
                    # return goods_id
                    return ''
                else:  # 处理从数据库中取出的数据
                    zhe_800_url = re.compile(r';').sub('', zhe_800_url)
                    goods_id = re.compile(r'https://miao.zhe800.com/products/(.*)').findall(zhe_800_url)[0]
                    print('------>>>| 得到的限时秒杀折800商品id为:', goods_id)
                    print('由于这种商品开头的量少, 此处先不处理这种开头的')
                    # return goods_id
                    return ''
            else:
                print('折800商品url错误, 非正规的url, 请参照格式(https://shop.zhe800.com/products/)开头的...')
                return ''

    def __del__(self):
        gc.collect()

if __name__ == '__main__':
    zhe_800 = Zhe800Parse()
    while True:
        zhe_800_url = input('请输入待爬取的折800商品地址: ')
        zhe_800_url.strip('\n').strip(';')
        goods_id = zhe_800.get_goods_id_from_url(zhe_800_url)
        data = zhe_800.get_goods_data(goods_id=goods_id)
        zhe_800.deal_with_data()

