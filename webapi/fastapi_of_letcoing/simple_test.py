#!/usr/bin/env python3
"""
简单测试脚本

用于验证 Flask 框架及其基础依赖是否已正确安装。
在部署或环境配置后，可以通过运行此脚本快速检查环境是否就绪。
"""

print("开始简单测试...")

# 测试 Flask 框架能否正常导入
try:
    print("正在导入 Flask...")
    from flask import Flask
    print("Flask 导入成功！")
except Exception as e:
    print(f"导入 Flask 时出错: {e}")

print("测试完成！")
