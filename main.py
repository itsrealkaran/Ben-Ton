import asyncio
import pygame as pg
import sys
import time
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
from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient, FaucetClient
from aptos_sdk.transactions import TransactionArgument, TransactionPayload, EntryFunction
from aptos_sdk.bcs import Serializer
from aptos_sdk.type_tag import TypeTag, StructTag
from aptos_sdk.account_address import AccountAddress
import hashlib
import aiohttp
import json

NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
FAUCET_URL = "https://faucet.devnet.aptoslabs.com"

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
        self.font = pg.font.Font(None, 46)
        self.leaderboard = []
        self.game_ended = False
        self.show_disclaimer = False
        self.disclaimer_start_time = 0
        self.new_game()
        self.rest_client = RestClient(NODE_URL)
        self.faucet_client = FaucetClient(FAUCET_URL, self.rest_client)
        self.contract_address = "0x69f9fa9f6cc6bf261b1b70900420526ee6df133e4156d55da1595d914064e3d4" 
        self.module_name = "leaderboard"
        self.score = 0
        self.previous_npc_count = 0
        self.generate_wallet()
        self.game_end_triggered = False
        self.game_end_type = None

    def generate_wallet(self):
        self.account = Account.generate()
        self.wallet_address = self.account.address()
        print(f"Wallet created: {self.wallet_address}")
        asyncio.create_task(self.create_and_fund_account())

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
        self.score = 0
        self.previous_npc_count = len(self.object_handler.npc_list)

    async def update(self):
        if self.state == 'GAME':
            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
            
            # Check if NPCs have been killed
            current_npc_count = len([npc for npc in self.object_handler.npc_list if npc.alive])
            if current_npc_count < self.previous_npc_count:
                npcs_killed = self.previous_npc_count - current_npc_count
                self.increment_score(npcs_killed * 10)  
            self.previous_npc_count = current_npc_count

            if self.game_end_triggered:
                await self.handle_game_end()
        
        if self.show_disclaimer:
            current_time = pg.time.get_ticks()
            if current_time - self.disclaimer_start_time > 2000:  
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
        
        if self.show_disclaimer:
            self.object_renderer.game_over()

    def draw_landing(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render('Welcome to Ben-Ton', True, (255, 255, 255))
        start_text = self.font.render('Press SPACE to Start', True, (255, 255, 255))
        leaderboard_text = self.font.render('Press L for Leaderboard', True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        self.screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, HEIGHT // 2 + 50))

    def draw_leaderboard(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render('Leaderboard', True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        for i, entry in enumerate(self.leaderboard):
            address, score = entry
            text = self.font.render(f"{i+1}. {address[:10]}... : {score}", True, (255, 255, 255))
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        back_text = self.font.render('Press B to go back', True, (255, 255, 255))
        self.screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 100))
        replay_text = self.font.render('Press SPACE to replay', True, (255, 255, 255))
        self.screen.blit(replay_text, (WIDTH // 2 - replay_text.get_width() // 2, HEIGHT - 50))

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
                elif self.state == 'LEADERBOARD':
                    if event.key == pg.K_b:
                        self.state = 'LANDING'
                    elif event.key == pg.K_SPACE:
                        self.new_game()
                        self.state = 'GAME'
                        pg.mouse.set_visible(False)
                        pg.event.set_grab(True)
                        pg.mixer.music.play(-1)
            self.player.single_fire_event(event)

    async def update_score(self):
        max_retries = 3
        print(self)
        for attempt in range(max_retries):
            try:
                payload = EntryFunction.natural(
                    f"{self.contract_address}::{self.module_name}",
                    "update_score",
                    [],  # No type arguments needed
                    [TransactionArgument(self.score, Serializer.u64)],
                )
                signed_transaction = await self.rest_client.create_bcs_signed_transaction(
                    self.account, TransactionPayload(payload)
                )
                txn_hash = await self.rest_client.submit_bcs_transaction(signed_transaction)
                await self.rest_client.wait_for_transaction(txn_hash)
                print(f"Score updated for {self.account.address()}: {self.score}")
                return  # Success, exit the function
            except Exception as e:
                print(f"Error updating score (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    print("Failed to update score after maximum retries")
                else:
                    await asyncio.sleep(1)  # Wait a bit before retrying

    async def fetch_leaderboard(self):
        try:
            url = f"{self.rest_client.base_url}/view"
            payload = {
                "function": f"{self.contract_address}::{self.module_name}::get_top_players",
                "type_arguments": [],
                "arguments": []
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        # The exact structure of the response may vary, adjust as needed
                        self.leaderboard = [(entry['address'], int(entry['score'])) for entry in data[0]]
                        if not self.leaderboard:
                            print("Leaderboard is empty.")
                    else:
                        print(f"Error fetching leaderboard: HTTP {response.status}")
                        self.leaderboard = []
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            self.leaderboard = []

    async def get_player_score(self, player_address):
        try:
            url = f"{self.rest_client.base_url}/view"
            payload = {
                "function": f"{self.contract_address}::{self.module_name}::get_player_score",
                "type_arguments": [],
                "arguments": [player_address]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        # The exact structure of the response may vary, adjust as needed
                        return int(data[0])
                    else:
                        print(f"Error getting player score: HTTP {response.status}")
                        return 0
        except Exception as e:
            print(f"Error getting player score: {e}")
            return 0

    async def game_over(self):
        self.game_ended = True
        pg.event.set_grab(False)
        pg.mixer.music.stop()
        self.show_disclaimer = True
        self.disclaimer_start_time = pg.time.get_ticks()
        await self.update_score()
        await self.fetch_leaderboard()
        self.state = 'LEADERBOARD'

    def increment_score(self, amount):
        self.score += amount
        print(f"Score increased by {amount}. New score: {self.score}")
        

    async def create_and_fund_account(self):
        try:
            # Fund the account using faucet
            await self.faucet_client.fund_account(self.account.address(), 100_000_000)  # 1 APT
            print(f"Account funded: {self.account.address()}")
        except Exception as e:
            print(f"Error funding account: {e}")

    def create_resource_address(self, source: str, seed: bytes) -> str:
        """Create a resource address from a source address and seed."""
        source_bytes = bytes.fromhex(source[2:])  # Remove '0x' prefix
        hash_input = b'\x01' + source_bytes + b'\x00' + seed
        hash_bytes = hashlib.sha3_256(hash_input).digest()[:32]  # Take first 32 bytes
        return '0x' + hash_bytes.hex()

    def trigger_game_end(self, end_type):
        self.game_end_triggered = True
        self.game_end_type = end_type

    async def handle_game_end(self):
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        pg.mixer.music.stop()
        
        if self.game_end_type == 'game_over':
            self.object_renderer.game_over()
        elif self.game_end_type == 'victory':
            self.object_renderer.win()
        
        pg.display.flip()
        pg.time.delay(1000)  # Show the end screen for 2 seconds
        
        await self.update_score()
        await self.fetch_leaderboard()
        self.state = 'LEADERBOARD'
        self.game_end_triggered = False
        self.game_end_type = None

async def main():
    game = Game()
    while True:
        game.check_events()
        await game.update()
        game.draw()
        if game.state == 'LEADERBOARD':
            await game.fetch_leaderboard()
        await asyncio.sleep(0)

asyncio.run(main())
