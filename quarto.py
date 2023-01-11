#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame
from math import sqrt
import random
import time

WIDTH, HEIGHT = 600, 300
#sqrt_3 = sqrt(3)
h_sqrt_2 = sqrt(2)/2

class State:
    IDLE = 0
    PLAYING = 1
    END = 2

#tie1 = [0,1,2,12,3,6,11,8,13,10,14,5,4,7,9,15]
#tie2 = [7,5,13,8,10,3,4,15,14,2,9,11,1,12,6,0]

class Game:
    def __init__(self):
        self.state = State.PLAYING
        self.pieces = [Piece(i) for i in range(16)]
        self.board = [[None]*4 for i in range(4)]
        self.turn = 0
        self.choice = None
        #self.choice = 0
        
        self.font = pygame.font.SysFont("Arial", 20)
    
    def render(self, surf):
        width, height = WIDTH/2, HEIGHT
        size = min(width, height)
        margin_x, margin_y = (width-size)/2, (height-size)/2
        cell_r = size/sqrt(2)/8
        
        pygame.draw.circle(surf, (255,255,255), [margin_x+size/2, margin_y+size/2], size/2, 3)
        for y in range(4):
            for x in range(4):
                X = width/2 + (x-y)*2*cell_r * h_sqrt_2
                Y = (x+y+1)*2*cell_r * h_sqrt_2
                pygame.draw.circle(surf, (255,255,255), [X, Y], cell_r-2, 1)
                #pygame.draw.polygon(surf, (255,0,0), [[X, Y-cell_r/h_sqrt_2], [X+cell_r/h_sqrt_2, Y], [X, Y+cell_r/h_sqrt_2], [X-cell_r/h_sqrt_2, Y]], 1)
                
                piece = self.board[y][x]
                if piece:
                    piece.render(surf, X, Y, cell_r)
        
        side_w = WIDTH-width
        side_r = (side_w - 40)/8
        for i, piece in enumerate(self.pieces):
            X = width + 20 + (i%4+0.5)*2*side_r
            Y = 20 + (i//4+0.5)*2*side_r
            piece.render(surf, X, Y, side_r)
            if i == self.choice:
                pygame.draw.rect(surf, (255,255,255), [X-side_r, Y-side_r, 2*side_r, 2*side_r], 1)
        
        """pos = self.screen_to_board(pygame.mouse.get_pos())
        txt = self.font.render(str(pos), True, (0,255,0))
        surf.blit(txt, [0,0])"""
        
        p = ["Your", "Computer's"][min(1,self.turn%3)]
        txt = self.font.render(p+" turn", True, (255,255,255))
        surf.blit(txt, [0,0])
    
    def process(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.turn%3 == 0:
                        pos = self.screen_to_board(event.pos)
                        if self.turn == 3 and isinstance(pos, tuple):
                            self.place(*pos)
                        
                        elif self.turn == 0 and isinstance(pos, int):
                            if 0 <= pos < len(self.pieces):
                                self.choice = pos
                                self.next_turn()
            
            elif event.type == pygame.USEREVENT:
                self.computer()
    
    def next_turn(self):
        self.turn += 1
        self.turn %= 4
        
        if self.turn % 3 != 0:
            pygame.time.set_timer(pygame.USEREVENT, 1000, 1)
    
    def place(self, x, y):
        if self.choice is None: return
        if 0 <= x < 4 and 0 <= y < 4:
            if not self.board[y][x] is None: return
            
            self.board[y][x] = self.pieces.pop(self.choice)
            self.choice = None
            if not self.check(x,y):
                self.next_turn()
            
            else:
                self.end(True)
    
    def screen_to_board(self, pos):
        x, y = pos
        
        width, height = WIDTH/2, HEIGHT
        size = min(width, height)
        margin_x, margin_y = (width-size)/2, (height-size)/2
        cell_r = size/sqrt(2)/8
        
        side_w = WIDTH-width
        side_r = (side_w - 40)/8
        
        dist_c = sqrt((x-width/2-margin_x)**2 + (y-height/2-margin_y)**2)
        # Board
        if dist_c < size/2:
            #X = width/2 + (x-y)*2*cell_r * h_sqrt_2
            #Y = (x+y+1)*2*cell_r * h_sqrt_2
            
            #(X-width/2) = (x-y)*2*cell_r * h_sqrt_2
            #Y = (x+y+1)*2*cell_r * h_sqrt_2
            
            #a = (X-width/2)/(2*cell_r * h_sqrt_2) = x-y  (1)
            #b = Y/(2*cell_r * h_sqrt_2)-1 = x+y          (2)
            
            # (1) + (2): a+b = 2*x
            # => (a+b)/2 = x
            
            # b-x = y
            
            a = (x-width/2)/(2*cell_r * h_sqrt_2)
            b = y/(2*cell_r * h_sqrt_2)
            
            X = (a+b)/2
            Y = b-X
            
            return (int(X), int(Y))
        
        # Side
        elif x > width:
            #X = width + 20 + (i%4+0.5)*2*side_r
            #Y = 20 + (i//4+0.5)*2*side_r
            
            X = (x-width-20)/(2*side_r)
            Y = (y-20)/(2*side_r)
            X, Y = int(X), int(Y)
            
            return X + Y*4
        
        return None
    
    def check(self, x, y):
        row = self.board[y]
        col = [self.board[i][x] for i in range(4)]
        diag1 = [self.board[i][i] for i in range(4)]
        diag2 = [self.board[3-i][i] for i in range(4)]
        
        """print(row)
        print(col)
        print(diag1)
        print(diag2)
        print()"""
        
        row = self.check_list(row)
        col = self.check_list(col)
        diag1 = (x==y) and self.check_list(diag1)
        diag2 = (x==3-y) and self.check_list(diag2)
        print()
        
        return any([row, col, diag1, diag2])
    
    def check_list(self, l):
        if len(l) != 4: return False
        if None in l: return False
        
        s = sum([int(f"{p.id:04b}") for p in l])
        for i in range(4):
            if (s%10) % 4 == 0:
                return True
            s //= 10
        
        return False
    
    def computer(self):
        #time.sleep(0.5)
        if self.turn == 1:
            poss = []
            for y in range(4):
                for x in range(4):
                    if self.board[y][x] is None:
                        poss.append((x,y))
            
            x, y = random.choice(poss)
            self.place(x, y)
        
        elif self.turn == 2:
            self.choice = random.randint(0, len(self.pieces)-1)
            self.next_turn()
    
    def end(self, win):
        self.state = State.END
        if win:
            p = ["Player", "Computer"][min(1,self.turn%3)]
            print(f"{p} has won")
        
        else:
            print("Tie")

class Piece:
    def __init__(self, id_):
        self.id = id_
        self.height = (self.id & 0b1000) >> 3
        self.col = (self.id & 0b100) >> 2
        self.shape = (self.id & 0b10) >> 1
        self.top = self.id & 0b1
    
    def __repr__(self):
        height = ["tall", "short"][self.height]
        col = ["red", "blue"][self.col]
        shape = ["square", "circular"][self.shape]
        top = ["hollow-top", "solid-top"][self.top]
        return f"<{height} / {col} / {shape} / {top}>"
    
    def render(self, surf, x, y, radius):
        col = [(236,69,69), (41,137,232)][self.col]
        r = (self.height*0.2 + 0.6) * radius
        
        if self.shape == 0:
            r2 = r/sqrt(2)
            pygame.draw.rect(surf, col, [x-r2, y-r2, 2*r2, 2*r2])
        
        else:
            pygame.draw.circle(surf, col, [x, y], r)
        
        if self.top == 0:
            pygame.draw.circle(surf, (0,0,0), [x, y], r/2)

if __name__ == "__main__":
    pygame.init()
    
    w = pygame.display.set_mode([WIDTH, HEIGHT])
    
    clock = pygame.time.Clock()
    game = Game()
    
    while game.state == State.PLAYING:
        pygame.display.set_caption(f"Quarto - {clock.get_fps():.2f}fps")
        game.process(pygame.event.get())
        
        w.fill(0)
        
        game.render(w)
        
        pygame.display.flip()
        
        clock.tick(60)
    
    input()