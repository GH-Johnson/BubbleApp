import pygame
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import random
import sys
import os
import numpy as np

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_bubble_surface(radius, color):
    # ...保持原有实现不变...

 def create_burst_frame(radius, progress):
    progress = max(0.0, min(1.0, progress))  # 参数校验
    # ...保持原有实现不变...

class Bubble:
    # ...保持原有属性和方法不变...
    
    def is_clicked(self, pos):
        """精确碰撞检测"""
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return (dx**2 + dy**2) <= (self.base_radius**2) * 1.2  # 增加10%点击容差

# 修改后的主循环事件处理部分
running = True
while running:
    screen.fill((173, 216, 230))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            clicked_bubble = None
            
            # 反向遍历实现"最后绘制最先点击"的效果
            for bubble in reversed(bubbles):
                if not bubble.bursting and bubble.is_clicked(mouse_pos):
                    clicked_bubble = bubble
                    break  # 找到第一个符合条件的立即停止
                    
            if clicked_bubble:
                clicked_bubble.bursting = True
                try:
                    pop_sound.play()
                except:
                    pass

    # 更新和绘制逻辑保持不变...
    for bubble in bubbles:
        bubble.update()
    
    bubbles = [b for b in bubbles if not b.should_remove()]
    
    # 按Y坐标排序实现视觉层级（下方泡泡先绘制）
    for bubble in sorted(bubbles, key=lambda x: x.y):
        bubble.draw(screen)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()