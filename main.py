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
        self.font = pg.font.Font(None, 36)
        self.wallet_address = None
        self.leaderboard = []
        self.game_ended = False
        self.show_disclaimer = False
        self.disclaimer_start_time = 0
        self.new_game()
        self.rest_client = RestClient(NODE_URL)
        self.faucet_client = FaucetClient(FAUCET_URL, self.rest_client)
        self.account = None  # Will be set when connecting wallet
        self.contract_address = "0xc9e9c2805af30b768fd1ac9d4b37ac114a3f16c675abdfc985c44ac5061fcd20"  # Updated to match the Move.toml
        self.module_name = "leaderboard"
        self.score = 0
        self.previous_npc_count = 0

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
            self.object_renderer.game_over()

    def draw_landing(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render('Welcome to Ben-Ton', True, (255, 255, 255))
        start_text = self.font.render('Press SPACE to Start', True, (255, 255, 255))
        leaderboard_text = self.font.render('Press L for Leaderboard', True, (255, 255, 255))
        wallet_text = self.font.render('Press W to Connect Wallet', True, (255, 255, 255))
        test_text = self.font.render('Press T to Test Smart Contract', True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        self.screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, HEIGHT // 2 + 50))
        self.screen.blit(wallet_text, (WIDTH // 2 - wallet_text.get_width() // 2, HEIGHT // 2 + 100))
        self.screen.blit(test_text, (WIDTH // 2 - test_text.get_width() // 2, HEIGHT // 2 + 150))

    def draw_leaderboard(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render('Leaderboard', True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        for i, entry in enumerate(self.leaderboard):
            address, score = entry
            text = self.font.render(f"{i+1}. {address[:10]}... : {score}", True, (255, 255, 255))
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        back_text = self.font.render('Press B to go back', True, (255, 255, 255))
        self.screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 50))

    def draw_exit_text(self):
        exit_text = self.font.render('Press B to exit game', True, (255, 255, 255))
        self.screen.blit(exit_text, (WIDTH - exit_text.get_width() - 40, 20))

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
                    elif event.key == pg.K_t:
                        asyncio.create_task(self.test_smart_contract())
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
                        self.game_over()
            self.player.single_fire_event(event)

    def connect_wallet(self):
        self.account = Account.generate()  # Generate a new account for the player
        self.wallet_address = self.account.address()
        print(f"Wallet created: {self.wallet_address}")
        asyncio.create_task(self.create_and_fund_account())

    async def update_score(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                payload = EntryFunction.natural(
                    f"{self.contract_address}::leaderboard",
                    "update_score",
                    [],
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
            result = await self.rest_client.view_function(
                self.contract_address,
                "leaderboard",
                "get_top_players",
                []
            )
            self.leaderboard = [(entry['address'], entry['score']) for entry in result[0]]  # Assuming the result is returned as a single-element list
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")

    async def get_player_score(self, player_address):
        try:
            result = await self.rest_client.view_function(
                self.contract_address,
                "leaderboard",
                "get_player_score",
                [TransactionArgument(player_address, Serializer.struct)]
            )
            return result[0]  # Assuming the result is returned as a single-element list
        except Exception as e:
            print(f"Error getting player score: {e}")
            return None

    async def test_smart_contract(self):
        print("Testing smart contract functions...")
        
        if not self.account:
            print("No wallet connected. Connecting wallet...")
            self.connect_wallet()
            await asyncio.sleep(2)  # Give some time for the account to be created and funded
        
        await self.create_and_fund_account()
        await asyncio.sleep(2)  # Give some time for the funding to be processed
        
        # Test update_score
        test_score = 100
        self.score = test_score
        await self.update_score()
        
        # Test get_player_score
        player_score = await self.get_player_score(self.account.address())
        if player_score is not None:
            print(f"Player score: {player_score}")
        
        # Test get_top_players
        await self.fetch_leaderboard()
        if self.leaderboard:
            print("Leaderboard:")
            for i, (address, score) in enumerate(self.leaderboard):
                print(f"{i+1}. {address[:10]}... : {score}")
        else:
            print("Leaderboard is empty or could not be fetched.")
        
        print("Smart contract function tests completed.")

    def game_over(self):
        asyncio.create_task(self.update_score())
        asyncio.create_task(self.fetch_leaderboard())
        self.state = 'LEADERBOARD'

    def increment_score(self, amount):
        self.score += amount
        print(f"Score increased by {amount}. New score: {self.score}")

    async def run(self):
        while True:
            self.check_events()
            await self.update()
            self.draw()
            if self.state == 'LEADERBOARD':
                await self.fetch_leaderboard()
            await asyncio.sleep(0)

    async def create_and_fund_account(self):
        try:
            # Fund the account using faucet
            await self.faucet_client.fund_account(self.account.address(), 100_000_000)  # 1 APT
            print(f"Account funded: {self.account.address()}")
        except Exception as e:
            print(f"Error funding account: {e}")

async def main():
    game = Game()
    await game.run()

if __name__ == '__main__':
    asyncio.run(main())
