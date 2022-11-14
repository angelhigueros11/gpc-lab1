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
        self.current_color = color(255, 255, 255) # por defecto blanco
        self.framebuffer = []
        self.glClear()

    def glCreateWindow(self, width, height):
        self.width = width
        self.height = height

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
                self.framebuffer[x][y] = color(0, 0, 0) 

    def glColor(self, r, g, b):
        self.current_color = color(r, g, b)


    def point(self, x, y):
        if 0 < x < self.width and 0 < y < self.height:
            self.framebuffer[x][y] = self.current_color

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

            offset += dy * 2

            if offset >= threshold:
                y += 1 if y0 < y1 else  -1
                threshold += dx * 2


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

        if a.y < b.y:
            a, b = b, a

        if a.y < c.y:
            a, c = c, a

        if b.y < c.y:
            b, c = c, b

        box_min, box_max = bounding_box(a, b, c)
        box_min.round()
        box_max.round()

        if a.y == b.y:
            x = c.x
            y = c.x

            xo, yo = c.y, a.y + 1
            x, y = int(x), int(y)

            for i in range(xo, yo):
                self.line(
                    V3(int(x), i), 
                    V3(int(y), i)
                )
                x += (c.x - a.x) / (c.y - a.y)
                y += (c.x - b.x) / (c.y - b.y)

            for x in range(box_min.x, box_max.x + 1):
                for y in range(box_min.y, box_max.y + 1):
                    w, v, u = barycenter(a, b, c, V3(x, y))

                    if (w < 0 or v < 0 or u < 0):
                        continue

        elif b.y == c.y:
            x = b.x
            y = c.x
            
            xo, yo = b.y, a.y + 1
            x, y = int(x), int(y)

            for i in range(xo, yo):
                self.line(
                    V3(x, i),
                    V3(y, i)
                )
                x += (b.x - a.x) / (b.y - a.y)
                y +=  (c.x - a.x) / (c.y - a.y)

            for x in range(box_min.x, box_max.x + 1):
                for y in range(box_min.y, box_max.y + 1):
                    w, v, u = barycenter(a, b, c, V3(x, y))

                    if (w < 0 or v < 0 or u < 0):
                        continue
        else:

            z = a.x + ((b.y - a.y) / (c.y - a.y)) * (c.x - a.x)
            w = V3(z, b.y)    
            x = b.x
            y = w.x
            
            xo, yo = b.y, a.y + 1
            x, y = int(x), int(y)

            for i in range(xo, yo):
                self.line(V3(x, i), V3(y, i))

                x += (b.x - a.x) / (b.y - a.y)
                y +=  (w.x - a.x) / (w.y - a.y)

            mca = (c.x - b.x) / (c.y - b.y)
            mcb = (c.x - w.x) / (c.y - w.y)
            x1 = c.x
            x2 = c.x

            for y in range(c.y, b.y + 1):
                self.line(V3(int(x1), y), V3(int(x2), y))
                x1 += mca
                x2 += mcb


    def draw(self, fig, c):
        r.current_color = c
        for i in range(len(fig)):
            r.triangle(
                V3(fig[i][0][0], fig[i][0][1]),
                V3(fig[i][1][0], fig[i][1][1]), 
                V3(fig[i][2][0], fig[i][2][1])
            )
            
        

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
r.glClear()
r.glColor(255, 255, 255)

fig1 = [
    [[205, 410], [193, 383], [220, 385]],
    [[165, 380], [193, 383], [185, 360]],
    [[207, 345], [180, 330], [185, 360]],
    [[207, 345], [233, 330], [230, 360]],
    [[230, 360], [250, 380], [220, 385]],
    [[208, 366], [185, 360], [207, 345]],
    [[208, 366], [193, 383], [220, 385]],
    [[208, 366], [185, 360], [205, 411]],
    [[208, 366], [220, 385], [230, 360]],
    [[208, 366], [230, 360], [207, 345]]
]

fig2 = [
    [[205, 410], [193, 383], [220, 385]],
    [[321, 335], [374, 302], [288, 286]],
    [[339, 251], [374, 302], [288, 286]],
    [[377, 249], [411, 197], [436, 249]]
]

fig3 = [
    [[205, 410], [193, 383], [220, 385]],
    [[413, 177], [466, 180], [448, 159]],
    [[517, 144], [466, 180], [448, 159]],
    [[517, 144], [502, 88], [448, 159]],
    [[517, 144], [502, 88],  [553, 53]],
    [[553, 53], [660, 52], [535, 36]],
    [[535, 36], [660, 52], [676, 37]],
    [[517, 144], [553, 53], [614, 132]],
    [[517, 144], [552, 214], [614, 132]],
    [[552, 214], [597, 215], [614, 132]],
    [[597, 215], [615, 214], [614, 132]],
    [[597, 215], [580, 214], [609, 230]],
    [[597, 215], [609, 230], [615, 214]],
    [[609, 230], [615, 214], [632, 230]],
    [[615, 214], [659, 214], [614, 132]],
    [[659, 214], [672, 192], [614, 132]],
    [[672, 192], [761, 179], [750, 145]],
    [[672, 192], [750, 145], [614, 132]],
    [[750, 145], [614, 132], [660, 52]],
    [[614, 132], [553, 53], [660, 52]]
]


fig4 = [
    [[205, 410], [193, 383], [220, 385]],
    [[682, 175], [710, 160], [739, 170]],
    [[739, 170], [710, 160], [735, 148]],
    [[708, 120], [710, 160], [735, 148]],
    [[682, 175], [710, 160], [708, 120]],
]


r.draw(fig1, color(0, 255, 0))
r.draw(fig2, color(255, 0, 0))
r.draw(fig3, color(100, 50, 0))
r.draw(fig4, color(100, 50, 0))
# r.draw(fig2)
# r.draw(fig3)
# r.draw(fig4)
# r.draw(fig5)

r.glFinish()
