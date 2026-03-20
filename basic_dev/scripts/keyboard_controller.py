#!/usr/bin/env python3

import rospy
from airsim_ros.msg import VelCmd
from std_msgs.msg import Header
import sys
import os
import threading
from pynput import keyboard

# ------------------ 全局配置 ------------------
MAX_LINEAR = 9       # 前后/左右最大速度 (m/s)
MAX_UPWARD = 3.5     # 上升最大速度 (m/s)
MAX_DOWNWARD = 3.5   # 下降最大速度 (m/s)
MAX_ANG_VEL = 20     # 最大偏航角速度 (rad/s)
ACC_LINEAR = 2.5     # 线加速度 (m/s^2)，每0.01秒增加量
ACC_ANGULAR = 7.0    # 角加速度 (rad/s^2)

# 按键状态字典
key_states = {
    'w': False, 's': False,  # 前后
    'a': False, 'd': False,  # 左右
    'up': False, 'down': False,  # 升降
    'left': False, 'right': False,  # 偏航
    'space': False,  # 紧急停止
}

msg2all = """
使用 键盘 控制 AirSim 无人机！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
W / S       : 前进 / 后退
A / D       : 左移 / 右移  
↑ / ↓       : 上升 / 下降 (方向键上下)
← / →       : 左旋 / 右旋
Space       : 紧急停止 (所有速度归零)
Ctrl+C      : 退出
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def print_status(forward, leftward, upward, angular):
    os.system('clear')
    print(msg2all)
    print("当前速度：\t 前进 %.2f\t 左移 %.2f\t 垂直 %.2f\t 偏航 %.2f " %
          (forward, leftward, upward, angular))
    print("-" * 80)
    print("活跃按键：", [k for k, v in key_states.items() if v])

class KeyboardAirSimController:
    def __init__(self):
        self.forward = 0.0
        self.leftward = 0.0
        self.upward = 0.0
        self.angular = 0.0
        
        # 启动ROS节点
        rospy.init_node('keyboard_airsim_controller', anonymous=True)
        topic = '/airsim_node/drone_1/vel_body_cmd'
        self.vel_pubs = rospy.Publisher(topic, VelCmd, queue_size=1)
        
        # 键盘监听器
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release)
        self.listener.start()
        
        rospy.loginfo("键盘控制器已启动！请确保终端焦点在此窗口...")
        print_status(self.forward, self.leftward, self.upward, self.angular)

    def on_key_press(self, key):
        try:
            if key.char == 'w': key_states['w'] = True
            elif key.char == 's': key_states['s'] = True
            elif key.char == 'a': key_states['a'] = True
            elif key.char == 'd': key_states['d'] = True
            elif key.char == ' ': key_states['space'] = True
        except AttributeError:
            if key == keyboard.Key.left: key_states['left'] = True
            elif key == keyboard.Key.right: key_states['right'] = True
            elif key == keyboard.Key.up: key_states['up'] = True
            elif key == keyboard.Key.down: key_states['down'] = True
            elif key == keyboard.Key.esc:
                rospy.signal_shutdown("用户按下ESC")
                return False

    def on_key_release(self, key):
        try:
            if key.char == 'w': key_states['w'] = False
            elif key.char == 's': key_states['s'] = False
            elif key.char == 'a': key_states['a'] = False
            elif key.char == 'd': key_states['d'] = False
            elif key.char == ' ': key_states['space'] = False
        except AttributeError:
            if key == keyboard.Key.left: key_states['left'] = False
            elif key == keyboard.Key.right: key_states['right'] = False
            elif key == keyboard.Key.up: key_states['up'] = False
            elif key == keyboard.Key.down: key_states['down'] = False

    def update_velocity(self, dt):
        """根据按键状态更新速度（带平滑加速度和限幅）"""
        target_forward = 0.0
        target_leftward = 0.0
        target_upward = 0.0
        target_angular = 0.0
        
        # 计算目标速度
        if key_states['space']:
            # 紧急停止
            target_forward = target_leftward = target_upward = target_angular = 0.0
        else:
            if key_states['w']: target_forward = MAX_LINEAR
            elif key_states['s']: target_forward = -MAX_LINEAR
            
            if key_states['a']: target_leftward = MAX_LINEAR
            elif key_states['d']: target_leftward = -MAX_LINEAR
            
            if key_states['up']: target_upward = MAX_UPWARD
            elif key_states['down']: target_upward = -MAX_DOWNWARD
            
            if key_states['left']: target_angular = -MAX_ANG_VEL
            elif key_states['right']: target_angular = +MAX_ANG_VEL
        
        # 平滑插值（模拟手柄的渐进控制）
        alpha = 0.1  # 插值系数，越大响应越快
        
        self.forward += (target_forward - self.forward) * alpha
        self.leftward += (target_leftward - self.leftward) * alpha
        self.upward += (target_upward - self.upward) * alpha
        self.angular += (target_angular - self.angular) * alpha
        
        # 死区处理（防止微小抖动）
        if abs(self.forward) < 0.1: self.forward = 0
        if abs(self.leftward) < 0.1: self.leftward = 0
        if abs(self.upward) < 0.05: self.upward = 0
        if abs(self.angular) < 0.1: self.angular = 0

    def run(self):
        rate = rospy.Rate(50)  # 50 Hz 发布频率
        count = 0
        
        try:
            while not rospy.is_shutdown():
                self.update_velocity(0.02)  # dt=1/50
                
                count += 1
                if count >= 5:  # 每5个周期（10Hz）刷新一次显示
                    print_status(self.forward, self.leftward, self.upward, self.angular)
                    count = 0
                
                # 构建并发布消息
                header = Header()
                header.stamp = rospy.Time.now()
                
                vel_cmd = VelCmd()
                vel_cmd.header = header
                vel_cmd.yawRate = self.angular
                vel_cmd.vx = self.forward
                vel_cmd.vy = -self.leftward  # AirSim坐标系转换
                vel_cmd.vz = self.upward
                vel_cmd.stop = 0
                vel_cmd.va = 8
                
                self.vel_pubs.publish(vel_cmd)
                rate.sleep()
                
        except KeyboardInterrupt:
            pass
        finally:
            # 停止无人机
            vel_cmd = VelCmd()
            vel_cmd.yawRate = 0
            vel_cmd.vx = 0
            vel_cmd.vy = 0
            vel_cmd.vz = 0
            vel_cmd.stop = 1  # 停止标志
            self.vel_pubs.publish(vel_cmd)
            self.listener.stop()
            rospy.loginfo("控制器已安全退出")

# ------------------ 主函数 ------------------
if __name__ == '__main__':
    # 检查依赖
    try:
        from pynput import keyboard
    except ImportError:
        print("请先安装依赖：pip install pynput")
        sys.exit(1)
        
    controller = KeyboardAirSimController()
    controller.run()
