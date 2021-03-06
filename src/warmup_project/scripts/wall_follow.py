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
    	self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    	self.sub = rospy.Subscriber('/scan', LaserScan, self.dataScan)
    	rospy.init_node('wall', anonymous=True)
    	self.r = rospy.Rate(10) # 10hz
        
        self.measurementCount = 0
        self.targetDistance = .5  
        
        self.wallFound = False
        self.distanceSet = False
        
        self.closestPoint =  {"index":-1, "distance":10 }
        self.lastScan = []
        
    def dataScan(self, msg):
        self.lastScan = msg.ranges
    	self.measurementCount+=1
        if self.wallFound:
            self.updateClosestPoint(msg)
        else:
            self.wallFindScan(msg)

    #once the wall if found, we look around the last location of the wall (closestPoint) to see how it has changed.
    def updateClosestPoint(self, msg):

        oldIndex =  self.closestPoint["index"]
        updatedPoint =  {"index":oldIndex, "distance":10 }

        for i in range(-20, 20):
            if msg.ranges[oldIndex +i] > 0: 
                if msg.ranges[oldIndex +i] < updatedPoint['distance']:
                    updatedPoint = {"index": oldIndex +i, "distance": msg.ranges[oldIndex +i] }
        self.closestPoint = updatedPoint
    
    #To find the wall we look all the way around the robot looking for a streak of relevant data.
    #once we identify a streak of at least 7 relevant scan resuls
    # (if there is a wall, there should be many more than 7),
    # then we look for the closest point, which is where the wall is compared to us. 
    def wallFindScan(self, msg):
        streak = 0
        streakMin = {"index":-1, "distance":10 }

        for i in range(360):
            if msg.ranges[i] != 0 and msg.ranges[i] < 7:        
                streak += 1
                if streak > 7:
                    middleFound = True
                    streakMin["distance"] = msg.ranges[i]
                    streakMin["index"] = i
                    
                    #check if any of the next 5 points are closer. If so, this is not the closest point. 
                    for j in range(5):
                        if msg.ranges[i+j] < streakMin['distance']:
                            middleFound = False
                    if middleFound:
                        self.wallFound = True
                        break
                else: 
                    streakMin["distance"] = msg.ranges[i]
                    streakMin["index"] = i
                

            else: 
                streak = 0
        self.closestPoint = streakMin
    
    #if wall not found, drives the robo straight until wall found 
    def findWall(self):
        #waits until we have two measurements before starting
        while self.measurementCount < 2:
            self.r.sleep()
            
        #if no wall found, we'll drive straight until we find one
        while not self.wallFound:
            msg = Twist(linear=Vector3(x=-.2))
        

    #takes a desired angle and turns robot until robot matches the desired angle
    def angleCheck(self, desiredAngle):
        self.angleSet = False
        while not self.angleSet:
            angSpeed = .01*(180 - abs(self.closestPoint['index'] - 180 - desiredAngle))         
            msg = Twist(angular=Vector3(z=angSpeed))
            self.pub.publish(msg)
            if self.closestPoint["index"] is desiredAngle:
                self.angleSet  = True
        
    #Move Robot away from wall until robot is approximately the correct distance away.
    def setDistance(self):
        while not self.distanceSet:
            if self.closestPoint['distance'] > 0.0:
                error = (self.closestPoint['distance'] - self.targetDistance)
                if abs(error) <.01:
                    self.distanceSet = True
                speed = error*.4
                msg = Twist(linear=Vector3(x=speed))
                self.pub.publish(msg)
        
    #once at set distance to wall, goes along wall maintaining the set distance from the wall
    def wallFollow(self, desiredAngle):
        while not rospy.is_shutdown():
            angSpeed = 0 
            if self.closestPoint['distance'] > 0.0:
                angSpeed += .1 * ( self.closestPoint['distance'] - self.targetDistance)
            if self.lastScan[desiredAngle - 45] > 0.0 or self.lastScan[desiredAngle + 45] > 0.0:
                angSpeed += .25* (self.lastScan[desiredAngle - 45] - self.lastScan[desiredAngle + 45])
      
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
