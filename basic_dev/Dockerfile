# 阶段1：基础镜像（仅安装依赖，不复制源码）
FROM ghcr.io/irobot-algorithm/sentry_navigation/environment:latest AS base

# 更换软件源（可选，加速 apt 下载）
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 更新 ROS 和 librealsense 的 GPG 密钥（解决 EXPKEYSIG 和 NO_PUBKEY）
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F42ED6FBAB17C654 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys FB0B24895113F120

# 将 ROS 源替换为清华源（避免 404）
RUN echo "deb http://mirrors.tuna.tsinghua.edu.cn/ros/ubuntu focal main" > /etc/apt/sources.list.d/ros-latest.list

# 安装依赖（不常变动）
RUN apt update && apt install -y --no-install-recommends \
    python3-catkin-tools \
    ros-noetic-geographic-msgs \
    ros-noetic-tf2-sensor-msgs \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-image-transport \
    ros-noetic-roslint \
    net-tools \
    ros-noetic-mavros \
    liborocos-bfl-dev \
    && rm -rf /var/lib/apt/lists/*

ENV ROS_DISTRO noetic
WORKDIR /basic_dev/

# 阶段2：最终镜像（基于基础镜像，添加源码并编译）
FROM base

# 复制源码（经常变动）
COPY src /basic_dev/src/

# 编译
RUN . /opt/ros/noetic/setup.sh && \
    ./src/livox_ros_driver2/build.sh ROS1 && \
    catkin_make -DCATKIN_WHITELIST_PACKAGES="livox_ros_driver2 airsim_ros fast_lio path_sender ego_planner imu_gps_odometry basic_dev" && \
    ls -l /basic_dev/devel/lib/   # 可选，调试用
# 创建启动脚本
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'source /opt/ros/noetic/setup.bash' >> /start.sh && \
    echo 'source /basic_dev/devel/setup.bash' >> /start.sh && \
    echo 'exec roslaunch basic_dev start.launch' >> /start.sh && \
    chmod +x /start.sh

ENTRYPOINT ["/start.sh"]