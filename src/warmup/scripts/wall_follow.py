#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id$
## Simple Wall Finder 

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist, Vector3
from sensor_msgs.msg import LaserScan

class wallFollower:
    
    def __init__(self):
    	print "init"
    	self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    	self.sub = rospy.Subscriber('/scan', LaserScan, self.dataScan)
    	rospy.init_node('wall', anonymous=True)
    	self.r = rospy.Rate(10) # 10hz
        self.measurementCount = 0
        self.wallFound = False
        self.angleSet = False
        self.distance_to_wall = -1.0
        self.targetDistance = 1.0
        self.distanceSet = False
        self.closestPoint =  {"index":-1, "distance":10 }
        print self.measurementCount
    	#set up pub sub and the rest

        # for i in range(360):
        #     if msg.ranges[i] != 0 and msg.ranges[i] < 7:
        #         valid_measurements.append(msg.ranges[i])
        # if len(valid_measurements):
        #     self.distance_to_wall = sum(valid_measurements)/float(len(valid_measurements))
        # else:
        #     self.distance_to_wall = -1.0
        # print self.distance_to_wall
        # #set wallFound here

    def dataScan(self, msg):
    	self.measurementCount+=1
        if self.measurementCount %10 is 0:
            print self.closestPoint
        if self.wallFound:
            self.wallFollowScan(msg)
        else:
            self.wallFindScan(msg)

    def updateClosestPoint(self, msg):

        oldIndex =  self.closestPoint["index"]
        updatedPoint =  {"index":oldIndex, "distance":msg.ranges[oldIndex] }

        for i in range(-20, 20):
            if msg.ranges[oldIndex +i] > 0: 
                if msg.ranges[oldIndex +i] < updatedPoint['distance']:
                    updatedPoint = {"index": oldIndex +i, "distance": msg.ranges[oldIndex +i] }
        self.closestPoint = updatedPoint
    

    def wallFollowScan(self, msg):
        self.updateClosestPoint(msg)
 
    def angleScan(self, msg):
        self.updateClosestPoint(msg)
    
    def wallFindScan(self, msg):
        streak = 0
        streakMin = {"index":-1, "distance":10 }
        print "start"
        for i in range(360):
            # print "try" +str(i) +" is " +str(msg.ranges[i] )
            # if not self.wallFound:
            if msg.ranges[i] != 0 and msg.ranges[i] < 7:
                
                streak += 1
                if streak > 7:
                    middleFound = True
                    for j in range(5):
                        if msg.ranges[i+j] < streakMin['distance']:
                            middleFound = False
                    if middleFound:
                        print "break"
                        self.wallFound = True
                        break
 
                    else:
                        streakMin["distance"] = msg.ranges[i]
                        streakMin["index"] = i
                else: 
                    streakMin["distance"] = msg.ranges[i]
                    streakMin["index"] = i
                

            else: 
                streak = 0
        print streakMin
        self.closestPoint = streakMin
    	
    def findWall(self):
        print "Waiting for more measurements"

        while self.measurementCount < 2:
            self.r.sleep()
            
        #if no wall found, we'll drive straight until we find one
        #at this point, there is no object avoidence, though large objects might register as walls.
        print "Searching for wall"
        while not self.wallFound:
            msg = Twist(linear=Vector3(x=-.2))
            # self.pub.publish(msg)
        print "Wall Found"

    def distanceCheck(self):
    	print "distCheck"
    	#determine distance from wall

    def angleCheck(self, desiredAngle):
    	print "anglecheck"
        self.angleSet = False
        while not self.angleSet:
            angSpeed = .01*(180 - abs(self.closestPoint['index'] - 180 - desiredAngle))
             
            msg = Twist(angular=Vector3(z=angSpeed))
            self.pub.publish(msg)
            if self.closestPoint["index"] is desiredAngle:
                self.angleSet  = True
        
    def setDistance(self):
        while not self.distanceSet:
            error = (self.closestPoint['distance'] - self.targetDistance)
            if abs(error) <.01:
                print "distSet"
                self.distanceSet = True
            speed = error*.2
            msg = Twist(linear=Vector3(x=speed))
            self.pub.publish(msg)
        
    def wallFollow(self, desiredAngle):
        print "wall following"
        while not rospy.is_shutdown():
            #angSpeed = .01*(180 - abs(self.closestPoint['index'] - 180 - desiredAngle))
            
            angSpeed = .1 * ( self.closestPoint['distance'] - self.targetDistance) -  
            
            # do a last five and use the avg to figure out what to do. 
            # lastFive = 
            # use the angle
            
            msg = Twist(linear=Vector3(x=.1), angular=Vector3(z=angSpeed)  )
            self.pub.publish(msg)
            self.r.sleep()
        


    def motionController(self):
        self.findWall()
        self.angleCheck(0)
        self.setDistance()
        self.angleCheck(90)
        self.wallFollow(90)

if __name__ == '__main__':
    try:
    	wf = wallFollower()
        wf.motionController()
    except rospy.ROSInterruptException: pass
