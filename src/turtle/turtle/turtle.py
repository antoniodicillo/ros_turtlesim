#!/usr/bin/env python3

import rospy
import cv2
import numpy as np

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

pose = None


def pose_callback(msg):
    global pose
    pose = msg


SAMPLE_STEP = 15

IMAGE_PATH = "../../../../img/dog_processed.png"

img = cv2.imread(IMAGE_PATH)

if img is None:
    print("Could not read image.")
    exit()

height, width, _ = img.shape

b = img[:, :, 0]
g = img[:, :, 1]
r = img[:, :, 2]

mask = (r > 200) & (g > 200) & (b < 120)
if mask.sum() == 0:
    intensity = r.astype(np.int32) + g.astype(np.int32) + b.astype(np.int32)
    mask = intensity > 400

ys, xs = np.where(mask)
edge_points = np.column_stack((xs, ys))

print("Total edge pixels found:", len(edge_points))

edge_points = edge_points[::SAMPLE_STEP]

print("Sampled points:", len(edge_points))

if len(edge_points) == 0:
    print("No edge points detected.")
    exit()

ordered = [tuple(edge_points[0])]
remaining = [tuple(p) for p in edge_points[1:]]

while remaining:
    last = ordered[-1]
    nearest = min(
        remaining,
        key=lambda p: (p[0] - last[0]) ** 2 + (p[1] - last[1]) ** 2,
    )
    ordered.append(nearest)
    remaining.remove(nearest)

points = []

for x, y in ordered:
    tx = (x / width) * 11.0
    ty = 11.0 - (y / height) * 11.0
    points.append((tx, ty))

rospy.init_node("image_tracer")

rospy.Subscriber("/turtle1/pose", Pose, pose_callback)

pub = rospy.Publisher("/turtle1/cmd_vel", Twist, queue_size=10)

rate = rospy.Rate(60)

def move_to_goal(x_goal, y_goal):
    global pose

    vel = Twist()

    while not rospy.is_shutdown():
        dx = x_goal - pose.x
        dy = y_goal - pose.y

        distance = np.sqrt(dx * dx + dy * dy)

        # Reached target
        if distance < 0.05:
            break

        target_angle = np.arctan2(dy, dx)

        angle_error = target_angle - pose.theta

        # Normalize angle
        while angle_error > np.pi:
            angle_error -= 2 * np.pi

        while angle_error < -np.pi:
            angle_error += 2 * np.pi

        vel.linear.x = 2.0 * distance
        vel.angular.z = 8.0 * angle_error

        pub.publish(vel)

        rate.sleep()

    vel.linear.x = 0
    vel.angular.z = 0

    pub.publish(vel)

while pose is None and not rospy.is_shutdown():
    rospy.sleep(0.1)

print("Starting trace...")

for x, y in points:

    if rospy.is_shutdown():
        break

    move_to_goal(x, y)

print("Finished tracing.")