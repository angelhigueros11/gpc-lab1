# Graficas por computador
# Angel Higueros - 20460
# Lab 1

from re import A
import struct
from cube import Obj
from vector import *
import random

# Métodos de escritura
def char(c): 
    return struct.pack('=c', c.encode('ascii'))

def word(w):
    return struct.pack('=h', w)

def dword(d):
    return struct.pack('=l', d)

def color(r, g, b):
    return bytes([b, g, r])

def cross(v0, v1):
    return (
        v0.y * v1.z - v0.z * v1.y,
        v0.z * v1.x - v0.x * v1.z,
        v0.x * v1.y - v0.y * v1.x,
    )


def bounding_box(*vertices):

    xs = [ vertex.x for vertex in vertices ]
    ys = [ vertex.y for vertex in vertices ]
    xs.sort()
    ys.sort()

    return V3(xs[0], ys[0]), V3(xs[-1], ys[-1])


def barycenter(a, b, c, p):
    cx, cy, cz = cross(
        V3(b.x - a.x, c.x - a.x, a.x - p.x), 
        V3(b.y - a.y, c.y - a.y, a.y - p.y)
    )


    if abs(cz) < 1:
        return -1, -1, -1 

    u = cx/cz
    v = cy/cz
    w = 1 - (u + v)

    return w, v, u



class Render(object):

    def glInit(self, filename = 'sr3.bmp'):
        self.filename = filename 
        self.width = 100 
        self.height = 100
        self.viewport_x = 0 
        self.viewport_y = 0 
        self.viewport_width = 100 
        self.viewport_height = 100
        self.current_color = color(255, 255, 255) # por defecto blanco
        self.vertex_color = color(200, 0, 0) # por defecto rojo
        self.framebuffer = []
        self.glClear()

    def glCreateWindow(self, width, height):
        self.width = width
        self.height = height

    def glViewPort(self, x, y, width, height):

        if self.width < x + width or self.height < y + height:
            print("[!] El viewport debe estar dentro de las medidas de la pantalla")
            self.viewport_x = 0
            self.viewport_y = 0
            self.viewport_width = self.width
            self.viewport_height = self.height
            self.glClear()
        else:
            self.viewport_x = x
            self.viewport_y = y
            self.viewport_width = width
            self.viewport_height = height
            self.glClear()

    def glClear(self):
        self.framebuffer= [
            [color(0, 0, 0) for x in range(self.width)]
            for y in range(self.height)
        ]

        self.zbuffer= [
            [-9999 for x in range(self.width)]
            for y in range(self.height)
        ]

        for x in range(self.width):
            for y in range(self.height):
                if x >= self.viewport_x and x <= self.viewport_width and y >= self.viewport_y and y <= self.viewport_height:
                    self.framebuffer[x][y] = self.current_color 

    def glClearColor(self, r, g, b):
        self.current_color = color(r, g, b)

    def glVertex(self, x, y):

        # convertir coordenadas normalizadas a cordenadas del dispositivo
        half_size_width = self.viewport_width / 2
        half_size_height = self.viewport_height / 2

        coord_x = int((( x + 1 ) * half_size_width ))
        coord_y = int((( y + 1 ) * half_size_height ))

        self.framebuffer[coord_x][coord_y] = self.vertex_color

    def point(self, x, y):
        if 0 < x < self.width and 0 < y < self.height:
            self.framebuffer[x][y] = self.vertex_color

       
    def line(self, v1, v2):
        x0 = round(v1.x)
        y0 = round(v1.y)
        x1 = round(v2.x)
        y1 = round(v2.y)

        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        steep = dy > dx

        if steep:
            x0, y0 =  y0, x0
            x1, y1 =  y1, x1

        if x0 > x1:
            x0, x1 = x1, x0 
            y0, y1 = y1, y0 

        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        offset = 0
        threshold = dx
        y =  y0

        for x in range(x0, x1 + 1):

            
            if steep:
                r.point(y, x)
            else:
                r.point(x, y)

            # offset += (dy/dx) * dx * 2
            offset += dy * 2

            if offset > threshold:
                y += 1 if y0 < y1 else  -1
                # threshold += 1 * dx * 2
                threshold += dx * 2


    def transform_vertex(self, vertex, scale, translate):
        return V3(
            (vertex[0] * scale[0]) + translate[0],
            (vertex[1] * scale[1]) + translate[1],
            (vertex[2] * scale[2]) + translate[2],
        )

    def load_model(self, filename, scale_factor = (1, 1, 1), translate_factor = (0, 0, 0)):
        obj = Obj(filename)
        for face in obj.faces:
            if len(face) == 3:
                f1 = face[0][0] - 1
                f2 = face[1][0] - 1
                f3 = face[2][0] - 1

                v1 =  self.transform_vertex(obj.vertices[f1], scale_factor, translate_factor)
                v2 =  self.transform_vertex(obj.vertices[f2], scale_factor, translate_factor)
                v3 =  self.transform_vertex(obj.vertices[f3], scale_factor, translate_factor)

                self.triangle(v1, v2, v3)

    def triangle(self, a, b, c):
        luz = V3(0, 0, -1)
        n = (b - a) * (c - a)
        i = n.norm() @ luz.norm()

        if i < 0:
            return

        grey = round(255 * i)
        self.glColor(grey,  grey, grey)
  

        box_min, box_max = bounding_box(a, b, c)
        box_min.round()
        box_max.round()
        for x in range(box_min.x, box_max.x + 1):
            for y in range(box_min.y, box_max.y + 1):
                w, v, u = barycenter(a, b, c, V3(x, y))

                if (w < 0 or v < 0 or u < 0):
                    continue
                

                z = a.z * w + b.z * v * c.z * u

                if (self.zbuffer[x][y] < z):
                    self.zbuffer[x][y] = z
                    self.point(x, y)


       
        

    def glColor(self, r, g, b):
        self.vertex_color = color(r, g, b)

    def glFinish(self):
        f = open(self.filename, 'bw')

        # Pixel header
        f.write(char('B'))
        f.write(char('M'))
        # tamaño archivo = 14 header + 40  info header + resolucion
        f.write(dword(14 + 40 + self.width * self.height * 3)) 
        f.write(word(0))
        f.write(word(0))
        f.write(dword(14 + 40))

        # Info header
        f.write(dword(40)) # tamaño header
        f.write(dword(self.width)) # ancho
        f.write(dword(self.height)) # alto
        f.write(word(1)) # numero de planos (siempre 1)
        f.write(word(24)) # bits por pixel (24 - rgb)
        f.write(dword(0)) # compresion
        f.write(dword(self.width * self.height * 3)) # tamaño imagen sin header
        f.write(dword(0)) # resolucion
        f.write(dword(0)) # resolucion
        f.write(dword(0)) # resolucion
        f.write(dword(0)) # resolucion


        for x in range(self.height):
            for y in range(self.width):
                f.write(self.framebuffer[y][x])


# IMPLEMENTACION
r = Render()
r.glInit('lab1-polygon.bmp')
r.glCreateWindow(800, 800)
r.glViewPort(0,0, 800, 800)
r.glClearColor(0, 0, 0)
r.glClear()

# Poligono 1
r.triangle(V3(165, 380),  V3(185, 360), V3(180, 330))
r.triangle(V3(207, 345), V3(233, 330),  V3(230, 360))
r.triangle(V3(250, 380), V3(220, 385), V3(205, 410))

# Poligono 2
r.triangle(V3(321, 335),  V3(288, 286), V3(339, 251))


# Poligono 3
r.triangle(V3(377, 249),  V3(411, 197), V3(436, 249))

# Poligono 4
r.triangle(V3(413, 177),  V3(448, 159), V3(502, 88))
r.triangle(V3(553, 53),  V3(532, 36), V3(676, 37))
r.triangle(V3(660, 52),  V3(750, 145), V3(761, 179))
r.triangle(V3(632, 230),  V3(580, 230), V3(597, 215))
r.triangle(V3(552, 214),  V3(517, 114), V3(466, 180))

# Poligono 5
r.triangle(V3(682, 175),  V3(708, 120), V3(735, 682))

r.glFinish()
