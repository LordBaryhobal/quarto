#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame
from math import sqrt
import random
import paho.mqtt.client as mqtt
import struct
import uuid

WIDTH, HEIGHT = 600, 300
h_sqrt_2 = sqrt(2)/2

class State:
    IDLE = 0
    PLAYING = 1
    END = 2

class Game:
    def __init__(self, client):
        self.client = client
        self.state = State.IDLE
        self.pieces = [Piece(i) for i in range(16)]
        self.board = [[None]*4 for i in range(4)]
        self.turn = 0
        self.choice = None
        
        self.font = pygame.font.SysFont("Arial", 20)
    
    def start(self, player):
        print(f"Player {player}")
        self.player = player
        self.state = State.PLAYING
    
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
        
        p = ["Player 1's", "Player 2's"][min(1,self.turn%3)]
        txt = self.font.render(p+" turn", True, (255,255,255))
        surf.blit(txt, [0,0])
    
    def process(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    t = (self.turn+1)%4
                    if t//2 == self.player:
                        pos = self.screen_to_board(event.pos)
                        if self.turn%2 == 1 and isinstance(pos, tuple):
                            self.client.send(f"{Client.TOPIC}/{self.client.uuid}", 3, *pos)
                        
                        elif self.turn%2 == 0 and isinstance(pos, int):
                            if 0 <= pos < len(self.pieces):
                                self.client.send(f"{Client.TOPIC}/{self.client.uuid}", 2, pos)
                        else:
                            print("Wrong action")
                    else:
                        print("Not your turn")
    
    def next_turn(self):
        self.turn += 1
        self.turn %= 4
        self.update()
    
    def choose(self, i):
        if 0 <= i < len(self.pieces):
            self.choice = i
            self.next_turn()
    
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
            a = (x-width/2)/(2*cell_r * h_sqrt_2)
            b = y/(2*cell_r * h_sqrt_2)
            
            X = (a+b)/2
            Y = b-X
            
            return (int(X), int(Y))
        
        # Side
        elif x > width:
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
        
        row = self.check_list(row)
        col = self.check_list(col)
        diag1 = (x==y) and self.check_list(diag1)
        diag2 = (x==3-y) and self.check_list(diag2)
        
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
    
    def end(self, win):
        self.state = State.END
        if win:
            self.client.send(Client.TOPIC, 20, min(1,self.turn%3))
        else:
            self.client.send(Client.TOPIC, 20, 2)
    
    def update(self):
        if self.client.is_server:
            self.client.send(Client.TOPIC, 16, self.turn, self.choice, self.pieces, self.board)

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
        r = (self.height*0.4 + 0.4) * radius
        
        if self.shape == 0:
            r2 = r/sqrt(2)
            pygame.draw.rect(surf, col, [x-r2, y-r2, 2*r2, 2*r2])
        
        else:
            pygame.draw.circle(surf, col, [x, y], r)
        
        if self.top == 0:
            pygame.draw.circle(surf, (0,0,0), [x, y], r/2)

class Client:
    TOPIC = "jeux_lan/quarto"
    
    def __init__(self, is_server=False):
        self.uuid = uuid.uuid4()
        self.is_server = is_server
        
        self.running = True
        self.mqttc = mqtt.Client()

        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_subscribe = self.on_subscribe
        
        self.mqttc.connect("127.0.0.1")

        self.mqttc.loop_start()
        
        self.mqttc.subscribe(self.TOPIC, 1)
        self.mqttc.subscribe(f"{self.TOPIC}/{self.uuid}", 1)
        if self.is_server:
            self.mqttc.subscribe(self.TOPIC+"/+", 1)
        
        self.clients = []
        self.game = Game(self)
        self.send(f"{self.TOPIC}/{self.uuid}", 0)
    
    def process(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()
        
        self.game.process(events)
    
    def render(self, surf):
        if self.game.state != State.IDLE:
            self.game.render(surf)
    
    def on_message(self, client, userdata, msg):
        try:
            type_, args = self.from_bytes(msg.payload)
        except Exception as e:
            print(e)
            return
        #print(type_, args)
        
        pers_top = msg.topic.endswith(str(self.uuid))
        
        if type_ < 16 and self.is_server:
            player = self.clients.index(args[0]) if args[0] in self.clients else None
            
            if type_ == 0:
                if len(self.clients) < 2:
                    print(f"New client: {args[0]}")
                    self.clients.append(args[0])
                    self.send(f"{self.TOPIC}/{args[0]}", 17, len(self.clients)-1)
                else:
                    self.send(f"{self.TOPIC}/{args[0]}", 18)
            
            elif type_ == 1:
                print(f"Client left: {args[0]}")
                self.clients.remove(args[0])
            
            elif type_ == 2:
                if not player is None and player*2 == self.game.turn:
                    print("Player chose piece")
                    self.game.choose(args[1])
            
            elif type_ == 3:
                if not player is None and (1-player)*2+1 == self.game.turn:
                    print("Player placed piece")
                    self.game.place(args[1], args[2])
        
        elif type_ >= 16:
            if type_ == 16 and not self.is_server:
                print("Updated state")
                self.game.turn = args[0]
                self.game.choice = args[1]
                self.game.pieces = args[2]
                self.game.board = args[3]
            
            elif type_ == 17 and pers_top:
                self.game.start(args[0])
            
            elif type_ == 18:
                print("Cannot join")
                self.quit()
            
            elif type_ == 19:
                self.quit()
            
            elif type_ == 20:
                if args[0] < 2:
                    p = ["Player 1", "Player 2"][args[0]]
                    print(f"{p} has won")
                
                else:
                    print("Tie")
    
    def on_connect(self, client, userdata, flags, rc):
        print("Connected")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed")
    
    # 0: join
    # 1: quit
    # 2: select piece
    # 3: select tile
    # 16: state
    # 17: joined
    # 18: reject join
    # 19: closing
    # 20: end
    def to_bytes(self, type_, *args):
        msg = struct.pack(">B", type_)
        
        if type_ < 16:
            msg += self.uuid.bytes
            
            if type_ == 2:
                msg += struct.pack(">B", args[0])
            
            elif type_ == 3:
                msg += struct.pack(">BB", args[0], args[1])
        
        else:
            if type_ == 16:
                msg += struct.pack(">B", self.game.turn)
                c = self.game.choice
                if c is None: c = -1
                msg += struct.pack(">b", c)
                msg += struct.pack(">B", len(self.game.pieces))
                for piece in self.game.pieces:
                    msg += struct.pack(">B", piece.id)
                
                for y in range(4):
                    for x in range(4):
                        if self.game.board[y][x] is None:
                            i = -1
                        else:
                            i = self.game.board[y][x].id
                        
                        msg += struct.pack(">b", i)
            
            elif type_ == 17:
                msg += struct.pack(">B", args[0])
            
            elif type_ == 20:
                msg += struct.pack(">B", args[0])
        
        return msg
    
    def from_bytes(self, msg):
        type_ = struct.unpack(">B", msg[:1])[0]
        msg = msg[1:]
        args = []
        
        if type_ < 16:
            uuid_ = uuid.UUID(bytes=msg[:16])
            args.append(uuid_)
            msg = msg[16:]
            if type_ == 2:
                args += struct.unpack(">B", msg[:1])
            
            elif type_ == 3:
                args += struct.unpack(">BB", msg[:2])
        
        else:
            if type_ == 16:
                turn, choice, p = struct.unpack(">BbB", msg[:3])
                msg = msg[3:]
                if choice == -1: choice = None
                pieces = []
                for i in range(p):
                    pieces.append(Piece(struct.unpack(">B", msg[:1])[0]))
                    msg = msg[1:]
                
                board = [[None]*4 for i in range(4)]
                for y in range(4):
                    for x in range(4):
                        i = struct.unpack(">b", msg[:1])[0]
                        msg = msg[1:]
                        if i > -1:
                            board[y][x] = Piece(i)
                
                args += [turn, choice, pieces, board]
            
            elif type_ == 17:
                args += struct.unpack(">B", msg[:1])
            
            elif type_ == 20:
                args += struct.unpack(">B", msg[:1])
        
        return (type_, args)
    
    def send(self, topic, type_, *args):
        print(f"Send to {topic}, type={type_}, args={args}")
        try:
            msg = self.to_bytes(type_, *args)
        except Exception as e:
            print(e)
            return
        self.mqttc.publish(topic, msg, 1)
    
    def quit(self):
        self.send(f"{self.TOPIC}/{self.uuid}", 1)
        if self.is_server:
            self.send(self.TOPIC, 19)
        
        self.mqttc.disconnect()
        self.running = False

if __name__ == "__main__":
    while True:
        c = input("Join (0) / Create server (1) ? ")
        try:
            c = int(c)
            assert c in [0,1]
            break
        except:
            pass
    
    pygame.init()
    w = pygame.display.set_mode([WIDTH, HEIGHT])
    clock = pygame.time.Clock()
    
    client = Client(bool(c))
    
    while client.running:
        pygame.display.set_caption(f"Quarto - {clock.get_fps():.2f}fps")
        client.process(pygame.event.get())
        
        w.fill(0)
        
        client.render(w)
        
        pygame.display.flip()
        
        clock.tick(60)
    
    #input("Enter to quit")