import pygame
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import random
import sys
import os
import numpy as np

# 资源路径处理（解决打包后路径问题）
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 生成泡泡表面（增加颜色校验）
def create_bubble_surface(radius, color):
    # 确保颜色值在合法范围
    r = max(0, min(255, color[0]))
    g = max(0, min(255, color[1]))
    b = max(0, min(255, color[2]))
    validated_color = (r, g, b)
    
    surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(surface, validated_color, (radius, radius), radius)
    
    # 高光效果优化
    for i, alpha in enumerate([100, 75, 50]):
        highlight = pygame.Surface((i*2+10, i*2+10), pygame.SRCALPHA)
        pygame.draw.circle(highlight, (255,255,255,alpha), (i+5,i+5), i+5)
        surface.blit(highlight, (radius//2 - i, radius//3 - i))
    
    return surface

# 生成破裂动画帧（新增参数校验）
def create_burst_frame(radius, progress):
    # 强制限制进度在[0,1]区间
    progress = max(0.0, min(1.0, progress))
    
    surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    lines = 10  # 增加射线数量
    
    try:
        base_color = pygame.Color(random.randint(100,255), 
                                random.randint(100,255), 
                                random.randint(100,255))
        burst_color = base_color.lerp(pygame.Color(255, 165, 0), progress)
    except ValueError:
        burst_color = pygame.Color(255, 165, 0)  # 默认橙色
    
    # 生成动态射线
    for i in range(lines):
        angle = 2 * np.pi * i / lines
        length = radius * (0.8 + progress*1.2)
        start_offset = random.uniform(0.2, 0.5)*radius
        start_pos = (
            radius + start_offset * np.cos(angle),
            radius + start_offset * np.sin(angle)
        )
        end_pos = (
            radius + length * np.cos(angle),
            radius + length * np.sin(angle)
        )
        pygame.draw.line(
            surface, burst_color, 
            start_pos, end_pos, 
            width=random.randint(2,4)
        )
    
    return surface

class Bubble:
    def __init__(self, text):
        self.text = str(text)[:15]  # 限制文字长度
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        self.base_radius = random.randint(30, 60)
        self.x = random.randint(50, 750)
        self.y = random.randint(50, 550)
        self.speed = [
            random.uniform(-1.5, 1.5),
            random.uniform(-1.5, 1.5)
        ]
        self.bursting = False
        self.burst_progress = 0.0
        self.normal_surface = create_bubble_surface(self.base_radius, self.color)

    def update(self):
        """更新泡泡状态（新增运动限制）"""
        if not self.bursting:
            self.x += self.speed[0]
            self.y += self.speed[1]
            
            # 边界弹性碰撞
            if self.x < self.base_radius or self.x > 800 - self.base_radius:
                self.speed[0] *= -1
            if self.y < self.base_radius or self.y > 600 - self.base_radius:
                self.speed[1] *= -1
        else:
            # 控制破裂进度
            self.burst_progress = min(self.burst_progress + 0.15, 1.0)

    def should_remove(self):
        """判断是否需要移除"""
        return self.burst_progress >= 1.0

    def draw(self, surface):
        """绘制方法（增加安全校验）"""
        try:
            if not self.bursting:
                pos = (int(self.x - self.base_radius), 
                      int(self.y - self.base_radius))
                surface.blit(self.normal_surface, pos)
                
                # 文字渲染安全处理
                font_size = max(12, self.base_radius//3)
                font = pygame.font.SysFont('comicsansms', font_size)
                text = font.render(self.text, True, (30, 30, 30))
                text_rect = text.get_rect(center=(self.x, self.y))
                surface.blit(text, text_rect)
            else:
                burst_surface = create_burst_frame(self.base_radius, 
                                                  self.burst_progress)
                surface.blit(burst_surface, 
                            (self.x - self.base_radius, 
                             self.y - self.base_radius))
        except Exception as e:
            print(f"绘制错误: {e}")

# 初始化文件选择
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    filetypes=[("Excel Files", "*.xlsx")]
)

# 数据读取安全处理
try:
    df = pd.read_excel(file_path)
    texts = df.iloc[:, 0].dropna().astype(str).tolist()
except Exception as e:
    print(f"文件读取错误: {e}")
    texts = ["示例文本1", "示例文本2", "点击测试"]

# 初始化Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("泡泡乐园 v1.1")
clock = pygame.time.Clock()

# 加载音效（增加文件存在检查）
try:
    pop_sound = pygame.mixer.Sound(resource_path('pop.wav'))
except Exception as e:
    print(f"音效加载失败: {e}")
    pop_sound = pygame.mixer.Sound(None)  # 静音替代

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
                    try:
                        pop_sound.play()
                    except:
                        pass

    # 更新所有泡泡状态
    for bubble in bubbles:
        bubble.update()
    
    # 移除已完成动画的泡泡
    bubbles = [b for b in bubbles if not b.should_remove()]
    
    # 绘制所有泡泡
    for bubble in bubbles:
        bubble.draw(screen)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()