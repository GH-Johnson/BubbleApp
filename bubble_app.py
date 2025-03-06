import pygame
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import random
import sys
import os
import numpy as np

# 常量定义
DEFAULT_SCREEN_SIZE = (800, 600)
MAX_BUBBLE_TEXT_LENGTH = 15
BUBBLE_MIN_RADIUS = 30
BUBBLE_MAX_RADIUS = 60
FPS = 60

# 资源路径处理（解决打包后路径问题）
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 生成泡泡表面（优化颜色处理）
def create_bubble_surface(radius, color):
    try:
        validated_color = pygame.Color(*color)
    except ValueError:
        validated_color = pygame.Color("dodgerblue")
    
    surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(surface, validated_color, (radius, radius), radius)
    
    # 高光效果优化
    for i, alpha in enumerate([100, 75, 50]):
        highlight_size = i*2 + 10
        highlight = pygame.Surface((highlight_size, highlight_size), pygame.SRCALPHA)
        pygame.draw.circle(highlight, (255,255,255,alpha), (i+5, i+5), i+5)
        surface.blit(highlight, (radius//2 - i, radius//3 - i))
    
    return surface

# 生成破裂动画帧（优化参数处理）
def create_burst_frame(radius, progress):
    progress = max(0.0, min(1.0, progress))
    surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    lines = 12  # 增加射线数量
    
    try:
        base_color = pygame.Color(
            random.randint(100,255), 
            random.randint(100,255), 
            random.randint(100,255)
        )
        burst_color = base_color.lerp(pygame.Color("orange"), progress)
    except ValueError:
        burst_color = pygame.Color("orange")
    
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
    def __init__(self, text, screen_width, screen_height):
        self.text = str(text)[:MAX_BUBBLE_TEXT_LENGTH]
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        self.base_radius = random.randint(BUBBLE_MIN_RADIUS, BUBBLE_MAX_RADIUS)
        self.x = random.randint(self.base_radius, screen_width - self.base_radius)
        self.y = random.randint(self.base_radius, screen_height - self.base_radius)
        self.speed = [
            random.uniform(-1.5, 1.5),
            random.uniform(-1.5, 1.5)
        ]
        self.bursting = False
        self.burst_progress = 0.0
        self.normal_surface = create_bubble_surface(self.base_radius, self.color)

    def update(self, screen_width, screen_height):
        """更新泡泡状态（支持动态窗口大小）"""
        if not self.bursting:
            self.x += self.speed[0]
            self.y += self.speed[1]
            
            # 动态边界处理
            if self.x < self.base_radius:
                self.x = self.base_radius
                self.speed[0] *= -1
            elif self.x > screen_width - self.base_radius:
                self.x = screen_width - self.base_radius
                self.speed[0] *= -1
                
            if self.y < self.base_radius:
                self.y = self.base_radius
                self.speed[1] *= -1
            elif self.y > screen_height - self.base_radius:
                self.y = screen_height - self.base_radius
                self.speed[1] *= -1
        else:
            self.burst_progress = min(self.burst_progress + 0.15, 1.0)

    def should_remove(self):
        return self.burst_progress >= 1.0

    def collide_point(self, point):
        """碰撞检测优化"""
        dx = self.x - point[0]
        dy = self.y - point[1]
        return (dx**2 + dy**2) <= self.base_radius**2

    def draw(self, surface):
        """绘制方法（增加抗锯齿处理）"""
        try:
            if not self.bursting:
                pos = (int(self.x - self.base_radius), 
                      int(self.y - self.base_radius))
                surface.blit(self.normal_surface, pos)
                
                # 文字渲染优化
                font_size = max(12, self.base_radius//3)
                try:
                    font = pygame.font.Font(None, font_size)  # 使用默认字体
                except OSError:
                    font = pygame.font.SysFont("Arial", font_size)
                
                text = font.render(self.text, True, (30, 30, 30))
                text_rect = text.get_rect(center=(self.x, self.y))
                surface.blit(text, text_rect)
            else:
                burst_surface = create_burst_frame(self.base_radius, self.burst_progress)
                surface.blit(burst_surface, 
                            (self.x - self.base_radius, 
                             self.y - self.base_radius))
        except Exception as e:
            print(f"绘制错误: {e}")

def load_data_file():
    """文件加载函数（增加取消操作处理）"""
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title="选择数据文件",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
    )
    
    if not file_path:
        return []
    
    try:
        df = pd.read_excel(file_path)
        return df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception as e:
        print(f"文件读取错误: {e}")
        return []

def main():
    # 初始化Pygame
    pygame.init()
    screen = pygame.display.set_mode(DEFAULT_SCREEN_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("泡泡乐园 v1.2")
    clock = pygame.time.Clock()

    # 加载音效（优化错误处理）
    pop_sound = None
    try:
        pop_sound = pygame.mixer.Sound(resource_path('pop.wav'))
    except Exception as e:
        print(f"音效加载失败: {e}")

    # 加载数据
    texts = load_data_file()
    if not texts:
        texts = ["示例文本1", "示例文本2", "点击测试"]
        print("使用示例文本")

    # 初始化泡泡
    screen_width, screen_height = screen.get_size()
    bubbles = [Bubble(text, screen_width, screen_height) for text in texts]

    # 主循环
    running = True
    while running:
        current_width, current_height = screen.get_size()
        screen.fill(pygame.Color("lightblue"))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for bubble in bubbles:
                    if not bubble.bursting and bubble.collide_point(mouse_pos):
                        bubble.bursting = True
                        if pop_sound:
                            try:
                                pop_sound.play()
                            except pygame.error:
                                pass

        # 更新所有泡泡状态
        for bubble in bubbles:
            bubble.update(*screen.get_size())
        
        # 移除已完成动画的泡泡
        bubbles = [b for b in bubbles if not b.should_remove()]
        
        # 绘制所有泡泡
        for bubble in bubbles:
            bubble.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()