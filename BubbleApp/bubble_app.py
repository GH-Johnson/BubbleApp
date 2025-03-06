import pygame
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import random
import sys
import os
import numpy as np

# 资源路径处理
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 生成渐变泡泡表面
def create_bubble_surface(radius, color):
    surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    
    # 基础颜色
    pygame.draw.circle(surface, color, (radius, radius), radius)
    
    # 添加高光
    highlight_pos = (int(radius*0.7), int(radius*0.3))
    for i in range(5, 0, -1):
        alpha = int(120 * (i/5))
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.circle(surface, highlight_color, highlight_pos, i)
    
    return surface

# 生成破裂动画帧
def create_burst_frame(radius, progress):
    surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    lines = 8  # 破裂射线数量
    
    # 动态颜色（从原色过渡到橙色）
    base_color = pygame.Color(random.randint(0,255), random.randint(0,255), random.randint(0,255))
    burst_color = base_color.lerp(pygame.Color(255, 165, 0), progress)
    
    # 生成破裂射线
    for i in range(lines):
        angle = 2 * np.pi * i / lines
        length = radius * (0.5 + progress*1.5)
        end_pos = (
            radius + length * np.cos(angle),
            radius + length * np.sin(angle)
        )
        pygame.draw.line(
            surface, burst_color, 
            (radius, radius), end_pos, 
            width=random.randint(2,4)
        )
    
    return surface

# 泡泡类
class Bubble:
    def __init__(self, text):
        self.text = text
        self.color = (random.randint(100,255), random.randint(100,255), random.randint(100,255))
        self.base_radius = random.randint(30, 60)
        self.x = random.randint(100, 700)
        self.y = random.randint(100, 500)
        self.speed = [random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)]
        self.bursting = False
        self.burst_progress = 0
        
        # 生成泡泡表面
        self.normal_surface = create_bubble_surface(self.base_radius, self.color)

    def move(self):
        if not self.bursting:
            # 随机运动
            self.x += self.speed[0] + random.uniform(-0.3, 0.3)
            self.y += self.speed[1] + random.uniform(-0.3, 0.3)
            
            # 边界弹性
            if self.x < self.base_radius or self.x > 800 - self.base_radius:
                self.speed[0] *= -1
            if self.y < self.base_radius or self.y > 600 - self.base_radius:
                self.speed[1] *= -1

    def draw(self, surface):
        if not self.bursting:
            # 绘制泡泡
            pos = (int(self.x - self.base_radius), int(self.y - self.base_radius))
            surface.blit(self.normal_surface, pos)
            
            # 文字渲染
            font_size = max(12, self.base_radius//2)
            font = pygame.font.SysFont('comicsansms', font_size)
            text = font.render(self.text, True, (30,30,30))
            text_rect = text.get_rect(center=(self.x, self.y))
            surface.blit(text, text_rect)
        else:
            # 破裂动画
            burst_surface = create_burst_frame(self.base_radius, self.burst_progress)
            surface.blit(burst_surface, (self.x - self.base_radius, self.y - self.base_radius))
            self.burst_progress += 0.2

# 主程序初始化
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])

df = pd.read_excel(file_path)
texts = df.iloc[:, 0].astype(str).tolist()

pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("AutoBubble 1.0")
clock = pygame.time.Clock()

# 加载音效
pop_sound = pygame.mixer.Sound(resource_path('pop.wav'))

# 创建泡泡实例
bubbles = [Bubble(text) for text in texts]

# 主循环
running = True
while running:
    screen.fill((173, 216, 230))  # 浅蓝色背景
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for bubble in bubbles:
                if not bubble.bursting and \
                   bubble.x - bubble.base_radius < mouse_pos[0] < bubble.x + bubble.base_radius and \
                   bubble.y - bubble.base_radius < mouse_pos[1] < bubble.y + bubble.base_radius:
                    bubble.bursting = True
                    pop_sound.play()

    for bubble in bubbles:
        bubble.move()
        bubble.draw(screen)
    
    # 移除已完成破裂的泡泡
    bubbles = [b for b in bubbles if b.burst_progress < 1.5]

    pygame.display.flip()
    clock.tick(30)

pygame.quit()