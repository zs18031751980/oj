#!/usr/bin/env python3
print("Starting simple test...")

# 测试基本导入
try:
    print("Importing Flask...")
    from flask import Flask
    print("Flask imported successfully!")
except Exception as e:
    print(f"Error importing Flask: {e}")

print("Test completed!")
