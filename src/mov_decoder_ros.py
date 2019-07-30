#!/usr/bin/env python

import av
import argparse
import rospy
from sensor_msgs.msg import Image
from threading import Thread
import numpy as np
from cv_bridge import CvBridge, CvBridgeError

class MovDecoder(Thread):
    def __init__(self, mov_path, index):
        Thread.__init__(self)
        self.mov_path = mov_path
        self.index = index
        self.img_pub = rospy.Publisher('serdp_camera%i' % (index + 1), Image, queue_size=10)  
        self.kill = False
        self.bridge = CvBridge()
    
    def run(self):
        container = av.open(self.mov_path) 
        loop_rate = rospy.Rate(10)
        for frame in container.decode(video=self.index):
            if self.kill:
                break
            img = np.array(frame.to_image().convert('RGB') )
            img = img[:, :, ::-1].copy() 
            try:
              self.img_pub.publish(self.bridge.cv2_to_imgmsg(img, "bgr8"))
            except CvBridgeError as e:
              print(e)
            loop_rate.sleep()
 
        
                   
if __name__ == '__main__':
    rospy.init_node('mov_publisher')
    parser = argparse.ArgumentParser(description='ROS Mov decoder')
    parser.add_argument("--mov_path", help="path to mov for decoding", default = "/home/mitchell/SERDP_WS/serdp_osb_nov_2018/raw_data/11-14-2018/3d2r2/vid_20181114_154433.mov")
    parser.add_argument("--video_files", help="number of video files in the .mov to decode", default = 2, type=int)
    args = parser.parse_args()
    threads = []
    
    for i in range(args.video_files):
        t = MovDecoder(args.mov_path, i)
        t.dameon = True
        threads.append(t)
        t.start()
    threads2 = threads
    while not rospy.is_shutdown() and len(threads2) > 0:
        try:
            # Join all threads using a timeout so it doesn't block
            # Filter out threads which have been joined or are None
            threads2 = [t.join(1) for t in threads if t is not None and t.isAlive()]
        except KeyboardInterrupt:
            for t in threads:
                t.kill = True
    
    for t in threads:
        t.kill = True        