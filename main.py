import itchat
# import全部消息类型
from itchat.content import *
import SQL
import model
import datetime
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.base import BaseTrigger
import logging

"""错误日志"""
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='log.txt',
                    filemode='a')

# 处理文本类消息
# 包括文本、位置、名片、通知、分享
# @itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
# def text_reply(msg):
#     # 微信里，每个用户和群聊，都使用很长的ID来区分
#     # msg['FromUserName']就是发送者的ID
#     # 将消息的类型和文本内容返回给发送者
#     itchat.send('%s: %s' % (msg['Type'], msg['Text']), msg['FromUserName'])

# # 处理多媒体类消息
# # 包括图片、录音、文件、视频
# @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
# def download_files(msg):
#     # msg['Text']是一个文件下载函数
#     # 传入文件名，将文件下载下来
#     msg['Text'](msg['FileName'])
#     # 把下载好的文件再发回给发送者
#     return '@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName'])

# # 处理好友添加请求
# @itchat.msg_register(FRIENDS)
# def add_friend(msg):
#     # 该操作会自动将新好友的消息录入，不需要重载通讯录
#     itchat.add_friend(**msg['Text'])
#     # 加完好友后，给好友打个招呼
#     itchat.send_msg('Nice to meet you!', msg['RecommendInfo']['UserName'])}

# 处理群聊消息
'''
msg['User']['NickName']     群昵称
msg['FromUserName']         群ID
msg['ActualNickName']       发送人
msg['Content']              发送内容
msg['CreateTime']           时间戳
'''


def change_time(input_time):
    along = -1 * int(input_time.count('-'))

    new_day = datetime.datetime.now() + datetime.timedelta(days=along)
    new_day = new_day.strftime('%Y-%m-%d')

    input_time = input_time.replace("-", "")

    result = new_day + ' ' + input_time + ":00"

    return result


@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    Content = msg['Text']
    NickName = msg['User']['NickName']
    if NickName in ['搬仓管理群', '华中管理层沟通群', '15号仓天图查询群']:
        if '查询进度=' in Content:
            brand = Content.replace("查询进度=", "")
            itchat.send('{}入库进度查询中'.format(brand), msg['FromUserName'])
            query = SQL.WMS(NickName)
            return_content = query.query_rk(brand)
            itchat.send(return_content, msg['FromUserName'])

        if '查询出货=' in Content:
            batch = Content.replace("查询出货=", "")
            query = SQL.WMS(NickName)

            batch = batch.split('.')

            if len(batch) != 3:
                itchat.send("查询参数不符，参数格式：开始时间.结束时间.类型", msg['FromUserName'])
                return

            btime = change_time(batch[0])
            etime = change_time(batch[1])

            print(btime, etime)
            return_content = query.query_ck(btime, etime, batch[2])
            itchat.send(return_content, msg['FromUserName'])

        if '查询产量=' in Content:

            work_type = Content.replace("查询产量=", "")
            work_type = work_type.split('.')
            print(work_type)
            if len(work_type) != 3:
                itchat.send("查询参数不符，参数格式：开始时间.结束时间.操作类型", msg['FromUserName'])
                return

            btime = change_time(work_type[0])
            etime = change_time(work_type[1])

            itchat.send("{}至{},{}产量查询中".format(btime, etime, work_type[2]), msg['FromUserName'])

            fname = datetime.datetime.now()
            fname = fname.strftime('%Y%m%d%H%I%M%S') + ".png"

            n = model.yield_type(btime, etime, work_type[2], fname, NickName)

            if n == "操作类型不存在！目前可供查询：收货,上架,拣货,包装,盘点,移库":
                itchat.send(n, msg['FromUserName'])
            else:
                itchat.send_image(fname, msg['FromUserName'])
                os.remove(fname)

        if '拣货差异=' in Content:
            batch = Content.replace("拣货差异=", "")
            query = SQL.WMS(NickName)

            batch = batch.split('.')

            if len(batch) != 2:
                itchat.send("查询参数不符，参数格式：开始时间.结束时间", msg['FromUserName'])
                return

            btime = batch[0]
            etime = batch[1]

            row = query.chayi(btime, etime)
            if len(row) == 1:
                itchat.send('拣货已完成', msg['FromUserName'])
                return
            else:
                itchat.send('拣货差异生成中', msg['FromUserName'])
                model.chayi(row)
                itchat.send_image('CHAYI.PNG', msg['FromUserName'])
                os.remove('CHAYI.PNG')

        if '条码库存=' in Content:
            batch = Content.replace("条码库存=", "")
            query = SQL.WMS(NickName)
            row = query.kc(batch)
            if len(row) == 1:
                itchat.send('{}查无库存'.format(batch), msg['FromUserName'])
                return
            else:
                model.chayi(row)
                itchat.send_image('CHAYI.PNG', msg['FromUserName'])
                os.remove('CHAYI.PNG')

        if '查询退供=' in Content:
            brand = Content.replace("查询退供=", "")
            query = SQL.WMS(NickName)
            row = query.query_tg(brand)
            if len(row) == 1:
                itchat.send('【{}】近30天内无抛单'.format(brand), msg['FromUserName'])
            else:
                model.chayi(row)
                itchat.send_image('CHAYI.PNG', msg['FromUserName'])
                os.remove('CHAYI.PNG')

        if '未收汇总=' in Content:
            day = int(Content.replace("未收汇总=", ""))
            query = SQL.WMS(NickName)
            row = query.yanshou(day=day)

            itchat.send('近{}天入库单查询中。。。'.format(day), msg['FromUserName'])
            model.chayi(row)
            itchat.send_image('CHAYI.PNG', msg['FromUserName'])
            os.remove('CHAYI.PNG')

        if '待上架汇总=' in Content:
            day = int(Content.replace("待上架汇总=", ""))
            query = SQL.WMS(NickName)
            row = query.shangjia(day)

            itchat.send('近{}天待上架查询。。。'.format(day), msg['FromUserName'])
            model.chayi(row)
            itchat.send_image('CHAYI.PNG', msg['FromUserName'])
            os.remove('CHAYI.PNG')

        if Content == '备份库存':
            file = datetime.datetime.now().strftime('%Y%m%d%H%I%M%S')

            itchat.send('正在备份库存数据，请停止其它查询操作', msg['FromUserName'])
            model.bf(NickName, file)
            itchat.send_file('backups/' + file + '.xlsx', msg['FromUserName'])
            itchat.send('备份完成', msg['FromUserName'])


# itchat.auto_login(enableCmdQR=2)
# 在auto_login()里面提供一个True，即hotReload=True
# 即可保留登陆状态
# 即使程序关闭，一定时间内重新开启也可以不用重新扫码
# itchat.auto_login(hotReload=True)
# itchat.auto_login(hotReload=True)
# itchat.run(True)


def itchat_run():
    print('执行启动')
    itchat.auto_login(enableCmdQR=2)
    itchat.run(True)


def dsbf():
    print("执行定时任务")
    itchat.get_chatrooms(update=True)
    iRoom = itchat.search_chatrooms('搬仓管理群')
    for room in iRoom:
        if room['NickName'] == '搬仓管理群':
            userName = room['UserName']
            break
    file = datetime.datetime.now().strftime('%Y%m%d%H%I%M%S')
    itchat.send('正在备份仓库存数据，请暂时停止查询操作', userName )
    model.bf('搬仓管理群', file)
    itchat.send_file('backups/' + file + '.xlsx', userName)
    itchat.send('备份完成', userName)


scheduler = BlockingScheduler()
scheduler.add_job(func=itchat_run, trigger='date')
scheduler.add_job(func=dsbf, trigger=CronTrigger(hour=10,minute=33))
scheduler._logger = logging
scheduler.start()
