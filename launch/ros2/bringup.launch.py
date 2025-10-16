#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2024 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2024-12-23
################################################################

import xacro
from launch import LaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # arg
    visual_flag = DeclareLaunchArgument(
        'visual_flag',
        default_value='false',
    )
    sim_time_flag = DeclareLaunchArgument(
        'sim_time_flag',
        default_value='false',
    )
    hardware_flag = DeclareLaunchArgument(
        'hardware_flag',
        default_value='true',
    )
    url = DeclareLaunchArgument(
        'url',
        default_value='ws://192.168.177.1:8439',
        description='The URL of the robot.'
    )
    read_only = DeclareLaunchArgument(
        'read_only',
        default_value='false',
        description='Whether to read only the chassis state.'
    )
    frame_id = DeclareLaunchArgument(
        'frame_id',
        default_value='base_link',
        description='Frame ID of the chassis.'
    )
    simple_mode = DeclareLaunchArgument(
        'simple_mode',
        default_value='true',
        description='Simple mode of the chassis.'
    )

    # visual
    urdf_file_path = FindPackageShare('hex_toolkit_ark').find(
        'hex_toolkit_ark') + '/urdf/ark.urdf'
    rviz_file_path = FindPackageShare('hex_toolkit_ark').find(
        'hex_toolkit_ark') + '/config/ros2/display.rviz'
    visual_group = GroupAction(
        [
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='robot_state_publisher',
                output='screen',
                parameters=[{
                    'use_sim_time':
                    LaunchConfiguration('sim_time_flag'),
                    'robot_description':
                    xacro.process_file(urdf_file_path).toxml(),
                }],
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz',
                output='screen',
                parameters=[{
                    'use_sim_time':
                    LaunchConfiguration('sim_time_flag'),
                }],
                arguments=['-d', rviz_file_path],
            ),
        ],
        condition=IfCondition(LaunchConfiguration('visual_flag')),
    )

    # sim
    odom_sim_param = FindPackageShare('hex_toolkit_ark').find(
        'hex_toolkit_ark') + '/config/ros2/odom_sim.yaml'
    sim_group = GroupAction(
        [
            Node(
                package='hex_toolkit_general_chasssis',
                executable='odom_sim',
                name='odom_sim',
                output='screen',
                emulate_tty=True,
                parameters=[
                    {
                        'use_sim_time': LaunchConfiguration('sim_time_flag'),
                    },
                    odom_sim_param,
                ],
                remappings=[
                    # subscribe
                    ('/cmd_vel', '/cmd_vel'),
                    # publish
                    ('/odom', '/odom'),
                ],
            ),
        ],
        condition=UnlessCondition(LaunchConfiguration('hardware_flag')),
    )

    # real
    real_group = GroupAction(
        [
            Node(
                package='xpkg_bridge',
                executable='xnode_bridge',
                name='xnode_bridge',
                output='screen',
                emulate_tty=True,
                parameters=[{
                    'url': LaunchConfiguration('url'),
                    'read_only': LaunchConfiguration('read_only'),
                }],
                remappings=[
                    # subscribe
                    ('/ws_down', '/ws_down'),
                    # publish
                    ('/ws_up', '/ws_up')
                ]
            ),
            Node(
                package='hex_vehicle',
                executable='chassis_trans',
                name='hex_chassis',
                output='screen',
                emulate_tty=True,
                parameters=[{
                    'frame_id': LaunchConfiguration('frame_id'),
                    'simple_mode': LaunchConfiguration('simple_mode'),
                }],
                remappings=[
                    # publish
                    ('/motor_status', '/motor_states'),
                    ('/real_vel', '/real_vel'),
                    ('/odom', '/odom'),
                    # subscribe
                    ('/joint_ctrl', '/joint_ctrl'),
                    ('/cmd_vel', '/cmd_vel'),
                    ('/clear_err', '/clear_err')
                ]
            ),
        ],
        condition=IfCondition(LaunchConfiguration('hardware_flag')),
    )

    return LaunchDescription([
        # arg
        visual_flag,
        sim_time_flag,
        hardware_flag,
        url,
        read_only,
        frame_id,
        simple_mode,
        # visual
        visual_group,
        # sim
        sim_group,
        # real
        real_group,
    ])
