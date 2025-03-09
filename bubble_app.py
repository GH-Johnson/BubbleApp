# bubble_app.py （主程序）
import pygame
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import random
import sys
import os
import numpy as np
import importlib_metadata as metadata

if sys.platform == "win32":
    # 禁用高DPI缩放
    if hasattr(sys, "getwindowsversion"):
        if sys.getwindowsversion().major < 8:
            os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(__file__)
            os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"

# 版本检查
try:
    assert metadata.version('pygame') >= '2.0.3'
    assert metadata.version('pandas') >= '1.2.5'
    assert metadata.version('numpy') >= '1.24.3'
except (ImportError, AssertionError) as e:
    print(f"依赖版本不满足: {e}")
    sys.exit(1)

# 常量定义
DEFAULT_SCREEN_SIZE = (1280, 720)  # 更大的默认窗口
MAX_BUBBLE_TEXT_LENGTH = 20
BUBBLE_MIN_RADIUS = 40
BUBBLE_MAX_RADIUS = 80
FPS = 60
BASE_SPEED = 0.4  # 新增基础速度常量
COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEEAD"]  # 预定义颜色方案

# 增强型资源路径处理（仅保留音效资源处理）
def resource_path(relative_path):
    """处理打包后的资源路径问题，支持嵌套目录"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"资源文件缺失: {path}")
    
    return path

# 高级泡泡生成器（保持不变）
class BubbleFactory:
    @staticmethod
    def create_bubble_surface(radius, color):
        """带渐变和动态高光的泡泡表面"""
        try:
            base_color = pygame.Color(color)
        except ValueError:
            base_color = pygame.Color(random.choice(COLORS))
        
        surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        
        # 渐变填充
        for i in range(radius, 0, -1):
            alpha = int(200 * (i/radius))
            grad_color = base_color.lerp("white", 0.2)
            grad_color.a = alpha
            pygame.draw.circle(surface, grad_color, (radius, radius), i)
        
        # 动态高光
        highlight = pygame.Surface((40, 40), pygame.SRCALPHA)
        gradient = pygame.Surface((40, 1), pygame.SRCALPHA)
        for x in range(40):
            gradient.set_at((x, 0), (255, 255, 255, int(200 * (1 - x/40))))
        gradient = pygame.transform.rotate(gradient, 45)
        highlight.blit(gradient, (0, 0))
        surface.blit(highlight, (radius//2, radius//3))
        
        return surface

    @classmethod
    def create_burst_animation(cls, radius, progress):
        """粒子效果破裂动画"""
        surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        particles = []
        
        # 生成粒子
        for _ in range(20):
            angle = random.uniform(0, 2*np.pi)
            speed = random.uniform(3, 8)
            life = random.uniform(0.8, 1.2)
            particles.append({
                "pos": (radius, radius),
                "vel": (speed * np.cos(angle), speed * np.sin(angle)),
                "life": life,
                "color": pygame.Color(random.choice(COLORS))
            })
        
        # 更新粒子
        for p in particles:
            if progress <= p["life"]:
                alpha = int(255 * (1 - progress/p["life"]))
                pos = (
                    radius + p["vel"][0] * progress * 50,
                    radius + p["vel"][1] * progress * 50
                )
                pygame.draw.circle(
                    surface, 
                    p["color"].lerp("white", 0.5),
                    pos,
                    max(2, int(5 * (1 - progress/p["life"]))),
                )
        
        return surface

class Bubble:
    def __init__(self, text, screen_rect):
        self.text = str(text).strip()[:MAX_BUBBLE_TEXT_LENGTH]
        self.color = random.choice(COLORS)
        self.base_radius = random.randint(BUBBLE_MIN_RADIUS, BUBBLE_MAX_RADIUS)
        self.rect = pygame.Rect(
            random.randint(screen_rect.left + self.base_radius, 
                          screen_rect.right - self.base_radius),
            random.randint(screen_rect.top + self.base_radius,
                          screen_rect.bottom - self.base_radius),
            self.base_radius*2, self.base_radius*2
        )
        self.velocity = [
            random.uniform(-BASE_SPEED, BASE_SPEED),
            random.uniform(-BASE_SPEED, BASE_SPEED)
        ]
        self.state = "normal"  # normal/bursting/popped
        self.animation_progress = 0.0
        self.surface_cache = BubbleFactory.create_bubble_surface(self.base_radius, self.color)

    def update(self, screen_rect, dt):
        """物理更新与状态管理"""
        if self.state == "normal":
            # 运动计算
            self.rect.x += self.velocity[0] * dt * 0.8
            self.rect.y += self.velocity[1] * dt * 0.8
            
            # 边界反弹
            if not screen_rect.contains(self.rect):
                if self.rect.left < screen_rect.left or self.rect.right > screen_rect.right:
                    self.velocity[0] *= -0.9
                if self.rect.top < screen_rect.top or self.rect.bottom > screen_rect.bottom:
                    self.velocity[1] *= -0.9
                self.rect.clamp_ip(screen_rect)
                
        elif self.state == "bursting":
            self.animation_progress += dt / 500  # 500ms动画时间
            if self.animation_progress >= 1.0:
                self.state = "popped"

    @property
    def should_remove(self):
        return self.state == "popped"

    def collide_point(self, point):
        return self.rect.collidepoint(point)

    def draw(self, surface):
        """状态驱动的渲染方法"""
        if self.state == "normal":
            surface.blit(self.surface_cache, self.rect.topleft)
            
            # 修改字体加载方式：使用系统默认字体
            font_size = max(16, self.base_radius//2)
            try:
                # 中文字体优先级列表（小写无空格）
                font = pygame.font.SysFont(
                    ['microsoft yahei', 'simhei', 'simsun', 'stheititts', 'wqy-microhei'], 
                    font_size
                )
            except Exception:
                font = pygame.font.SysFont(None, font_size)  # 最后尝试默认字体
            
            text = font.render(self.text, True, (30, 30, 30))
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)
            
        elif self.state == "bursting":
            frame = BubbleFactory.create_burst_animation(self.base_radius, self.animation_progress)
            surface.blit(frame, self.rect.topleft)

class BubbleManager:
    def __init__(self, screen_rect):
        self.bubbles = []
        self.screen_rect = screen_rect
        self.pop_sound = self._load_sound()

    def _load_sound(self):
        try:
            return pygame.mixer.Sound(resource_path("resources/pop.wav"))
        except Exception as e:
            print(f"音效加载失败: {e}")
            return None

    def add_bubble(self, text):
        self.bubbles.append(Bubble(text, self.screen_rect))

    def handle_click(self, pos):
        for bubble in reversed(self.bubbles):
            if bubble.state == "normal" and bubble.collide_point(pos):
                bubble.state = "bursting"
                if self.pop_sound:
                    self.pop_sound.play()
                return True
        return False

    def update_all(self, dt):
        self.bubbles = [b for b in self.bubbles if not b.should_remove]
        for b in self.bubbles:
            b.update(self.screen_rect, dt)

    def draw_all(self, surface):
        for b in self.bubbles:
            b.draw(surface)

def load_dataset():
    """支持多种文件格式的数据加载"""
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title="选择数据文件",
        filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Text", "*.txt")]
    )
    
    if not file_path:
        return []
    
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            with open(file_path) as f:
                return [line.strip() for line in f]
                
        return df.iloc[:, 0].dropna().astype(str).tolist()
    
    except Exception as e:
        print(f"数据加载失败: {e}")
        return []

def main():
    pygame.init()
    screen = pygame.display.set_mode(DEFAULT_SCREEN_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("泡泡乐园 v2.0")
    clock = pygame.time.Clock()
    
    # 初始化管理系统
    manager = BubbleManager(screen.get_rect())
    
    # 加载初始数据
    dataset = load_dataset()
    if dataset:
        for text in dataset:
            manager.add_bubble(text)
    else:
        for text in ["双击添加泡泡", "右键导入数据", "点击爆破!"]:
            manager.add_bubble(text)

    running = True
    while running:
        dt = clock.tick(FPS)
        screen_rect = screen.get_rect()
        screen.fill(pygame.Color("#F0F0F0"))
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                manager.screen_rect = screen.get_rect()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    manager.handle_click(event.pos)
                elif event.button == 3:  # 右键重新加载数据
                    dataset = load_dataset()
                    if dataset:
                        manager.bubbles.clear()
                        for text in dataset:
                            manager.add_bubble(text)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:  # 新建泡泡
                    manager.add_bubble(f"泡泡{len(manager.bubbles)+1}")

        # 更新和绘制
        manager.update_all(dt)
        manager.draw_all(screen)
        
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
