import asyncio
import pygame as pg
import sys
from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *

class Game:
    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        pg.event.set_grab(True)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        self.state = 'LANDING'  # Start with the landing page
        self.font = pg.font.Font(None, 36)
        self.wallet_address = None
        self.leaderboard = []
        self.game_ended = False
        self.show_disclaimer = False
        self.disclaimer_start_time = 0
        self.new_game()

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        pg.mixer.music.play(-1)

    async def update(self):
        if self.state == 'GAME':
            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
        
        if self.show_disclaimer:
            current_time = pg.time.get_ticks()
            if current_time - self.disclaimer_start_time > 2000:  # Show for 2 seconds
                self.show_disclaimer = False
                self.state = 'LEADERBOARD'
        
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f}')

    def draw(self):
        if self.state == 'LANDING':
            self.draw_landing()
        elif self.state == 'LEADERBOARD':
            self.draw_leaderboard()
        elif self.state == 'GAME':
            self.object_renderer.draw()
            self.weapon.draw()
            self.draw_exit_text()
        
        if self.show_disclaimer:
            self.draw_disclaimer()

    def draw_landing(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render('Welcome to Ben-Ton', True, (255, 255, 255))
        start_text = self.font.render('Press SPACE to Start', True, (255, 255, 255))
        leaderboard_text = self.font.render('Press L for Leaderboard', True, (255, 255, 255))
        wallet_text = self.font.render('Press W to Connect Wallet', True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        self.screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, HEIGHT // 2 + 50))
        self.screen.blit(wallet_text, (WIDTH // 2 - wallet_text.get_width() // 2, HEIGHT // 2 + 100))

    def draw_leaderboard(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render('Leaderboard', True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        for i, (address, score) in enumerate(self.leaderboard):
            text = self.font.render(f"{i+1}. {address[:10]}... : {score}", True, (255, 255, 255))
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        back_text = self.font.render('Press B to go back', True, (255, 255, 255))
        self.screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 50))

    def draw_exit_text(self):
        exit_text = self.font.render('Press B to exit game', True, (255, 255, 255))
        self.screen.blit(exit_text, (WIDTH - exit_text.get_width() - 10, 10))

    def draw_disclaimer(self):
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        text = self.font.render('Game Exited', True, (255, 255, 255))
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            elif event.type == pg.KEYDOWN:
                if self.state == 'LANDING':
                    if event.key == pg.K_SPACE:
                        self.state = 'GAME'
                        pg.mouse.set_visible(False)
                        pg.event.set_grab(True)
                        pg.mixer.music.play(-1)
                    elif event.key == pg.K_l:
                        self.state = 'LEADERBOARD'
                    elif event.key == pg.K_w:
                        self.connect_wallet()
                elif self.state == 'LEADERBOARD':
                    if event.key == pg.K_b:
                        self.state = 'LANDING'
                elif self.state == 'GAME':
                    if event.key == pg.K_b:
                        self.game_ended = True
                        pg.event.set_grab(False)
                        pg.mixer.music.stop()
                        self.show_disclaimer = True
                        self.disclaimer_start_time = pg.time.get_ticks()
            self.player.single_fire_event(event)

    def connect_wallet(self):
        # Simulate wallet connection
        self.wallet_address = f"0x{pg.time.get_ticks():x}"
        print(f"Wallet connected: {self.wallet_address}")

    def fetch_leaderboard(self):
        # Simulate fetching leaderboard data
        self.leaderboard = [
            (f"0x{i:x}", 1000 - i * 100) for i in range(10)
        ]

    def update_score(self, score):
        # Simulate updating score on blockchain
        if self.wallet_address:
            print(f"Score updated for {self.wallet_address}: {score}")
            # Update leaderboard
            self.leaderboard.append((self.wallet_address, score))
            self.leaderboard.sort(key=lambda x: x[1], reverse=True)
            self.leaderboard = self.leaderboard[:10]  # Keep top 10

    async def run(self):
        while True:
            self.check_events()
            await self.update()
            self.draw()
            if self.state == 'LEADERBOARD':
                self.fetch_leaderboard()
            await asyncio.sleep(0)

async def main():
    game = Game()
    await game.run()

if __name__ == '__main__':
    asyncio.run(main())
