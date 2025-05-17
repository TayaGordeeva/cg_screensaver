import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import sys
import os
from typing import List, Tuple, Optional

def get_texture_path(filename):
    if os.path.exists(filename):
        return filename
    texture_path = os.path.join("textures", filename)
    if os.path.exists(texture_path):
        return texture_path
    return None

def load_texture(image_path: str) -> Optional[int]:
    try:
        texture_surface = pygame.image.load(image_path)
        texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
        width = texture_surface.get_width()
        height = texture_surface.get_height()

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                    GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        return texture_id
    except Exception as e:
        print(f"Ошибка загрузки текстуры {image_path}: {e}")
        return None

class Star:
    def __init__(self):
        self.position = [
            random.uniform(-30, 30),
            random.uniform(-20, 20),
            random.uniform(-25, 0)
        ]
        self.base_intensity = random.uniform(0.3, 0.7)
        self.current_intensity = self.base_intensity
        self.flicker_speed = random.uniform(0.02, 0.05)
        self.flicker_phase = random.uniform(0, math.pi*2)
        
    def update(self):
        self.flicker_phase += self.flicker_speed
        flicker_amount = math.sin(self.flicker_phase) * 0.3
        self.current_intensity = max(0.1, self.base_intensity + flicker_amount)

class CelestialBody:
    def __init__(self, radius: float, color: Tuple[float, float, float], 
                 orbit_radius: float, speed: float, texture_file: Optional[str] = None,
                 rotation_speed: float = 1.0, light_power: float = 1.0):
        self.radius = radius * 1.5
        self.color = color
        self.orbit_radius = orbit_radius * 2
        self.speed = speed
        self.angle = random.uniform(0, 360)
        self.rotation_angle = 0
        self.rotation_speed = rotation_speed
        self.light_power = light_power  # Множитель яркости (1.0 - нормальная, >1.0 - ярче)
        self.position = [0.0, 0.0, 0.0]
        self.texture_id = None
        
        if texture_file:
            texture_path = get_texture_path(texture_file)
            if texture_path:
                self.texture_id = load_texture(texture_path)
                if self.texture_id:
                    print(f"Успешно загружена текстура: {texture_file}")
                else:
                    print(f"Не удалось загрузить текстуру: {texture_file}")
            else:
                print(f"Файл текстуры не найден: {texture_file}")
        
    def update_position(self):
        self.angle += self.speed
        self.rotation_angle += self.rotation_speed
        self.position = [
            math.sin(math.radians(self.angle)) * self.orbit_radius,
            math.cos(math.radians(self.angle)) * self.orbit_radius * 0.5,
            0
        ]
        
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.rotation_angle, 0, 1, 0)  # Вращение вокруг своей оси
        
        if self.texture_id is not None:
            self._draw_textured()
        else:
            self._draw_colored()
            
        glPopMatrix()
        
    def _draw_textured(self):
        try:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            
            quad = gluNewQuadric()
            gluQuadricTexture(quad, GL_TRUE)
            gluQuadricNormals(quad, GLU_SMOOTH)
            
            glMaterialfv(GL_FRONT, GL_AMBIENT, [0.5 * self.light_power, 0.5 * self.light_power, 0.5 * self.light_power, 1.0])
            glMaterialfv(GL_FRONT, GL_DIFFUSE, [1.0 * self.light_power, 1.0 * self.light_power, 1.0 * self.light_power, 1.0])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0 * self.light_power, 1.0 * self.light_power, 1.0 * self.light_power, 1.0])
            glMaterialfv(GL_FRONT, GL_SHININESS, [50.0])
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.3 * self.light_power, 0.3 * self.light_power, 0.3 * self.light_power, 1.0])
            
            gluSphere(quad, self.radius, 32, 32)
            gluDeleteQuadric(quad)
            
            glDisable(GL_TEXTURE_2D)
        except Exception as e:
            print(f"Ошибка при отрисовке текстуры: {e}")
            self._draw_colored()
    
    def _draw_colored(self):
        self._set_material_properties()
        quad = gluNewQuadric()
        gluSphere(quad, self.radius, 32, 32)
        gluDeleteQuadric(quad)
        
    def _set_material_properties(self):
        mat_specular = [1.0 * self.light_power, 1.0 * self.light_power, 1.0 * self.light_power, 0.5]
        mat_shininess = [100.0]
        mat_diffuse = [self.color[0] * self.light_power, 
                      self.color[1] * self.light_power, 
                      self.color[2] * self.light_power, 
                      0.7]
        mat_emission = [0.3 * self.light_power, 0.3 * self.light_power, 0.3 * self.light_power, 1.0]
        
        glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.3, 0.3, 0.3, 0.5])
        glMaterialfv(GL_FRONT, GL_EMISSION, mat_emission)

class Moon(CelestialBody):
    def __init__(self, planet: CelestialBody, radius: float, 
                 color: Tuple[float, float, float], orbit_radius: float, 
                 speed: float, texture_file: Optional[str] = None,
                 rotation_speed: float = 1.0, light_power: float = 1.0):
        super().__init__(radius, color, orbit_radius, speed, texture_file, rotation_speed, light_power)
        self.planet = planet
        
    def update_position(self):
        self.angle += self.speed
        self.rotation_angle += self.rotation_speed
        self.position = [
            self.planet.position[0] + math.sin(math.radians(self.angle)) * self.orbit_radius,
            self.planet.position[1] + math.cos(math.radians(self.angle)) * self.orbit_radius * 0.7,
            self.planet.position[2] + math.sin(math.radians(self.angle * 1.3)) * 0.5
        ]

class Starfield:
    def __init__(self, star_count: int = 1000):
        self.stars = [Star() for _ in range(star_count)]
        self.vertex_data = None
        self.color_data = None
        self._update_vertex_data()
        
    def _update_vertex_data(self):
        self.vertex_data = []
        self.color_data = []
        for star in self.stars:
            self.vertex_data.extend(star.position)
            self.color_data.extend([star.current_intensity] * 3)
        
    def update(self):
        for star in self.stars:
            star.update()
        self._update_vertex_data()
        
    def draw(self):
        lighting_enabled = glIsEnabled(GL_LIGHTING)
        if lighting_enabled:
            glDisable(GL_LIGHTING)
            
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        
        vertex_ptr = (GLfloat * len(self.vertex_data))(*self.vertex_data)
        color_ptr = (GLfloat * len(self.color_data))(*self.color_data)
        
        glVertexPointer(3, GL_FLOAT, 0, vertex_ptr)
        glColorPointer(3, GL_FLOAT, 0, color_ptr)
        glPointSize(1.0)
        glDrawArrays(GL_POINTS, 0, len(self.stars))
        
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        
        if lighting_enabled:
            glEnable(GL_LIGHTING)

class SolarSystemScreensaver:
    def __init__(self):
        self.display = (1000, 750)
        self.clock = pygame.time.Clock()
        self.running = False
        
        try:
            pygame.init()
            pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
            gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 100.0)
            glTranslatef(0.0, 0.0, -20)
            
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glLightfv(GL_LIGHT0, GL_POSITION, [10, 10, 10, 1])
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
            
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            self.starfield = Starfield()

            self.sun = CelestialBody(
                radius=1.5,
                color=(1.0, 0.8, 0.4), 
                orbit_radius=0.0,
                speed=0.0, 
                texture_file="sun.jpg",
                rotation_speed=0.5, 
                light_power=2.0 
            )
            
            self.earth = Moon(
                planet=self.sun,
                radius=0.8,
                color=(0.1, 0.3, 0.8),
                orbit_radius=4.0,
                speed=0.15,
                texture_file="earth_texture.jpg",
                rotation_speed=0.7,
                light_power=1.5  
            )
            
            self.moon = Moon(
                planet=self.earth,
                radius=0.4,
                color=(0.8, 0.8, 0.8),
                orbit_radius=1.8,
                speed=0.5,
                texture_file="moon_texture.jpg",
                rotation_speed=0.3,
                light_power=1.3  
            )
            
        except Exception as e:
            print(f"Ошибка инициализации: {e}")
            self.cleanup()
            sys.exit(1)
    
    def cleanup(self):
        pygame.quit()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.running = False
    
    def update(self):
        self.starfield.update()
        self.sun.update_position()  
        self.earth.update_position()
        self.moon.update_position()
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        self.starfield.draw()        
        self.sun.draw()
        self.earth.draw()
        self.moon.draw()
        
        pygame.display.flip()
        self.clock.tick(60)
    
    def run(self):
        try:
            self.running = True
            while self.running:
                self.handle_events()
                self.update()
                self.render()
        finally:
            self.cleanup()

if __name__ == "__main__":
    screensaver = SolarSystemScreensaver()
    screensaver.run()
