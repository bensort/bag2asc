# !/usr/bin/env python3

"""
Author: Qin Pan
Date: 2021-06-03 10:10:04
LastEditTime: 2021-06-03 10:10:04
LastEditors: Qin Pan
Description: unzip bagfile to asc file
FilePath: 
"""

import rosbag
import rospy
import sys, getopt
import os
from datetime import datetime

from rospy import rostime

class RosAscWriter():
    """
	将bag文件中的CAN帧解析为asc文件
	
	Attributes:
        topic: 指定CAN帧的话题名称  
        output_filename：指定输出的文件名称  
        start：指定CAN帧的开始时间  
        end：指定CAN帧的结束时间  
	"""
    # 参数初始化
    def __init__(self, topic="can0/received_messages", output_path = "", start = rospy.Time(0), end = rospy.Time(sys.maxsize)):
        self.opt_topic = topic
        self.out_path = output_path
        self.opt_start = start
        self.opt_end = end

    # 根据话题类型过滤话题
    def filter_can_msgs(self, topic, datatype, md5sum, msg_def, header):
        if(datatype=="can_msgs/Frame"):
                return True;
        return False;

    # 从命令行读参数
    def parseArgs(self, args):
        opts, opt_files = getopt.getopt(args,"hsvr:o:t:p:",["opath=","topic=","start=","end="])
        for opt, arg in opts:
            if opt in ("-o", "--opath"):
                self.out_path = arg
            elif opt in ("-t", "--topic"):
                self.opt_topic = arg
            elif opt in ("--start"):
                self.opt_start = rospy.Time(int(arg))
            elif opt in ("--end"):
                self.opt_end = rospy.Time(int(arg))
        return opt_files

    # 将bag文件中的can信息写入asc文件
    def write_output_asc(self, filename):
        """解析bag文件

        Args:
            filename: bag文件名称

        Returns:
            None

        Raises:
            IOError: 输入输出异常
        """

        # 指定生成的asc文件名称
        if self.out_path == "":
            out_file = bagfile[:-4] + "_can" + ".asc"
        else:
            out_file = self.out_path + bagfile[:-4] + "_can" + ".asc"
        
        if self.out_path != "":
            for f in os.listdir(self.out_path):
                if f.find(bagfile[:-4])>=0 and f.find("_can.asc")>=0:
                    os.remove(self.out_path + f)
        else:
            for f in os.listdir("./"):
                if f.find(bagfile[:-4])>=0 and f.find("_can.asc")>=0:
                    os.remove(self.out_path + f)

        with open(out_file,'w') as file:
            # 写入asc文件表头
            now = datetime.now().strftime("%a %b %m %I:%M:%S.%f %p %Y")
            file.write("date %s\n" % now)
            file.write("base hex  timestamps absolute\n")
            file.write("internal events logged\n")

            # 指定数据写入格式
            FORMAT_MESSAGE = "{channel}  {id:<15} Rx   {dtype} {data}"
            FORMAT_EVENT = "{timestamp:9.6f} {message}\n"

             # 打开bag文件
            bag_file = filename
            bag = rosbag.Bag(bag_file, "r")
            i = 0

            # 读取bag文件里的CAN帧信息，并按指定格式写入asc文件
            for topic, msg, t in bag.read_messages(connection_filter=self.filter_can_msgs, start_time=self.opt_start, end_time=self.opt_end):
                if i == 0:
                    # 捕获第一帧的时间戳，后续CAN帧的时间戳以此时间为基准偏移
                    firstFrameTimeStamp = msg.header.stamp.to_sec()

                timestamp =  msg.header.stamp.to_sec()

                if msg.is_error:
                    message = "{}  ErrorFrame".format(msg.channel)
                    # message = "{}  ErrorFrame".format('1')
                    line = FORMAT_EVENT.format(timestamp=timestamp, message=message)
                    file.write(line)
                    i = i + 1
                    continue

                if msg.is_rtr:
                    dtype = 'r'
                    data = []
                else:       
                    dtype = "d {}".format(msg.dlc)
                    canframe = msg.data[0:msg.dlc]
                    data = ["{:02X}".format(byte) for byte in canframe]

                arb_id = "{:X}".format(msg.id)
                if msg.is_extended:
                    arb_id += 'x'
                
                # ros节点添加Channel后需要添加
                message = FORMAT_MESSAGE.format(channel=msg.channel, id=arb_id, dtype=dtype, data=' '.join(data))
                # message = FORMAT_MESSAGE.format(channel='1', id=arb_id, dtype=dtype, data=' '.join(data))
                if timestamp >= firstFrameTimeStamp:
                    timestamp -= firstFrameTimeStamp  
                line = FORMAT_EVENT.format(timestamp=timestamp, message=message)
                file.write(line)
                i = i + 1

            # 关闭打开的bag文件
            bag.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('请指定bag文件!')
        sys.exit(1)
    else :
        RosAscWriter = RosAscWriter()
        try:
            opt_files = RosAscWriter.parseArgs(sys.argv[1:])
        except getopt.GetoptError:
            sys.exit(2)


    # 遍历指定的bag文件
    for files in range(0,len(opt_files)):
        bagfile = opt_files[files]
        RosAscWriter.write_output_asc(bagfile)
    print("完成！")
