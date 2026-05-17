import rclpy
from nclpy.node import Node
from geometry_msg.msg import Twist

class Turtle(Node):
    def __init__(self):
        super().__init__('turtle')
        self_publisher = self.create_publisher(Twist, 'turel/cmd_vel', 10)
        time = 0.1 
        self.timer = self.create_timer(time, self.timer_callback)
    
    def timer_callback(self):
        msg = Twist()
        msg.linear.x = 2.0
        msg.angular.z = 1.0
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Turtle()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()