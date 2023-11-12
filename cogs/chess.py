# external imports
import discord
from discord import app_commands
from discord.ext import commands

# builtin imports
from json import load as json_load, dumps as json_dumps
from datetime import datetime
from typing import Tuple
import random

# local imports
from chess_handler import ChessHandler

class Chess(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        # alias
        self.bot = bot

        # metadata attributes
        config = self.load_config()
        self.guild_id    = config["guild_id"]
        self.channel_id  = config["channel_id"]
        self.teams       = config["teams"]
        self.game_number = config["game_number"]

        # attributes
        self.vote_minimum = 0

        # initialize
        self.chess_handler = ChessHandler()
    
    """ ----- Private methods ----- """
    def load_config(self) -> dict:
        """ Loads chess_config.json as a python dictionary and returns the contents. """
        try:
            with open("config/chess_config.json") as f:
                return json_load(f)
            
        except Exception as error:
            raise FileNotFoundError(f"{type(error).__name__}: {error}")

    def dump_config(self) -> dict:
        """ Dumps all attributes to the chess_config.json file. """
        # write attributes to a python dictionary
        config = {}
        config["guild_id"]    = self.guild_id
        config["channel_id"]  = self.channel_id
        config["teams"]       = self.teams
        config["game_number"] = self.game_number

        # serialize into json
        json_object = json_dumps(config)

        # write the json object to chess_config.json
        with open("config/chess_config.json") as outfile:
            outfile.write(json_object)

    def save_game(self, pgn: str) -> None:
        """ Saves a pgn the games directory with the date as the file name. """
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            with open(f"games/{current_date}.pgn", "w") as f:
                f.write(pgn)
        
        except Exception as error:
            self.bot.logger.error(f"Failed to save pgn data:{type(error).__name__}: {error}")

    async def try_popular_move(self, interaction: discord.Interaction) -> None:
        """ Checks if there isn't a vote tie and plays the move with the most votes. """

        # if there is a vote tie then display the moves that are tied in votes
        if self.chess_handler.check_vote_tie():
            embed_message = discord.Embed(title = f"There is a tie in votes!", color = discord.Color.gold())
            most_votes = max(self.chess_handler.vote_pool.values())
            [embed_message.add_field(name = move, value = votes, inline = True) for move, votes in self.chess_handler.vote_pool.items() if votes == most_votes]
            await interaction.followup.send(embed = embed_message)
        
        # if the game ended then display the outcome of the game
        elif self.chess_handler.board.outcome != None:
            game_result = self.chess_handler.end_game()

            # save the game result to memory
            self.game_number += 1
            self.save_game(game_result)
            self.dump_config()

            # send the game result
            embed_message = discord.Embed(title = "GAME OVER:", color = discord.Color.gold())
            embed_message.add_field(name = "Game Result:", value=game_result)
            await interaction.followup.send(embed_message)
    
    def get_board_embed(self) -> Tuple[discord.Embed, discord.File]:
        """ Creates a discord.Embed and a discord.File object that represents the board state and returns it. """
        embed_message = discord.Embed(title = self.game.turn, color = discord.Color.gold())
        embed_message.add_field(name = f"{self.vote_minimum} vote(s) required to play move", value="To view possible commands type `/help`")
        embed_message.add_field(name = "Legal moves:", value=self.game.legal_moves_str, inline=False)
        embed_message.set_image(url = 'attachment://board_image.png')
        board_image = discord.File(self.chess_handler.generate_board_image(), filename="board_image.png")

        return embed_message, board_image

    """ ----- Admin commands ------ """
    @app_commands.command(name="start_game", description="Starts a game of team chess.")
    @app_commands.describe(mix_teams="Reasign teams to all users.")
    @app_commands.choices(mix_teams=[
        app_commands.Choice(name="True", value=True),
        app_commands.Choice(name="False", value=False)
    ])
    @app_commands.describe(vote_minimum="Sets the minimum number of votes required to play a move. This value is 2 by default.")
    async def start_game(self, interaction: discord.Interaction, mix_teams: app_commands.Choice[int], vote_minimum: str = "2"):
        try:
            # check if the user has admin
            is_admin = await self.bot.check_perms(interaction)
            if not is_admin:
                return
            
            # check if the command has been run in the correct channel
            if interaction.channel_id != self.channel_id:
                await interaction.response.send_message(f"Games can only be started in https://discord.com/channels/{self.guild_id}/{self.channel_id})")
                return

            # check if there is already a game in session
            if self.game.playing:
                await interaction.response.send_message("The game is already in session!", ephemeral=True)
                return
            
            # check if the vote_minimum parameter is a number
            if not vote_minimum.isnumeric():
                await interaction.response.send_message("vote_minimum needs to be a number!", ephemeral=True)
                return
            self.vote_minimum = int(vote_minimum)

            # start the game
            await interaction.response.send_message("Starting game...")
            self.game.start_game(self.game_number)

            # if the 'mix_teams' parameter is set to True
            if mix_teams.value:
                await interaction.followup.send("Mixing teams...")
                for member in interaction.guild.members:
                    # remove them from their old team
                    for team in self.TEAMS:
                        await member.remove_roles(discord.utils.get(interaction.guild.roles, name=team))
                    self.bot.logger.info(f"Removed roles {self.TEAMS} from {member.name}")

                    # avoid granting roles to bots
                    if "bots" in [role.name for role in interaction.user.roles]:
                        continue

                    # grant them a new team
                    new_team = discord.utils.get(interaction.guild.roles, name=random.choice(self.TEAMS))
                    await member.add_roles(new_team)
                    self.bot.logger.info(f"Granted role '{team}' to {member.name}")
            
            # display the board
            embed, board_image = self.get_board_embed()
            await interaction.followup.send(embed=embed, file=board_image)

        except Exception as error:
            self.bot.logger.error(f"Internal command failure:\n{type(error).__name__}: {error}")
    
    @app_commands.command(name = "end_game", description = "Ends the currently active game of team chess.")
    async def end_game(self, interaction: discord.Interaction) -> None:
        try:
            # check if the user has admin
            is_admin = await self.bot.check_perms(interaction)
            if not is_admin:
                return
            
            # check if the command has been run in the correct channel
            if interaction.channel_id != self.channel_id:
                await interaction.response.send_message(f"Games can only be started in https://discord.com/channels/{self.guild_id}/{self.channel_id})")
                return

            # check if there is a game in session
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return
            
            # end the game
            await interaction.response.send_message("Ending game...")
            game_result = self.game.end_game()

            # save the game result to memory
            self.game_number += 1
            self.save_game(game_result)
            self.dump_config()

            # send the game result
            embed_message = discord.Embed(title="GAME OVER", color=discord.Color.gold())
            embed_message.add_field(name="Game result:", value=game_result)
            await interaction.followup.send(embed=embed_message)

        except Exception as error:
            self.bot.logger.error(f"Internal command failure:\n{type(error).__name__}: {error}")

    """ ----- User commands ----- """
    @app_commands.command(name = "vote", description = "Adds a vote to the voting pool in a game of team chess.")
    async def vote(self, interaction: discord.Interaction, move: str) -> None:
        try:
            # check if the command has been run in the correct channel
            if interaction.channel_id != self.channel_id:
                await interaction.response.send_message(f"Votes can only be made in https://discord.com/channels/{self.guild_id}/{self.channel_id})")

            # check if there is a game in session
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return

            # check which side it is to play and whether or not the user is on the correct team
            if self.chess_handler.turn and "white" not in [role.name for role in interaction.user.roles]:
                await interaction.response.send_message(f"It's not your turn to play! Try again later!", ephemeral=True)
                return
            
            elif "black" not in [role.name for role in interaction.user.roles]:
                await interaction.response.send_message(f"It's not your turn to play! Try again later!", ephemeral=True)
                return
            
            # try to play the move
            vote_success = self.chess_handler.try_add_vote(interaction.user.id, move)

            # send a message if the move is not legal
            if not vote_success:
                await interaction.response.send_message(f'"{move}" is not a legal move!', ephemeral=True)
                return
            
            # send a confirmation message otherwise
            await interaction.response.send_message(f'You voted for "{move}"!', ephemeral=True)
            
            if len(self.chess_handler.votes) >= self.vote_minimum:
                self.try_popular_move(interaction)

        except Exception as error:
            self.bot.logger.error(f"Internal command failure:\n{type(error).__name__}: {error}")
    
    @app_commands.command(name="show_votes", description = "Displays the voting pool.")
    async def show_votes(self, interaction: discord.Interaction) -> None:
        try:
            # check if the command has been run in the correct channel
            if interaction.channel_id != self.channel_id:
                await interaction.response.send_message(f"Game related commands can only be done in https://discord.com/channels/{self.guild_id}/{self.channel_id})")

            # check if there is a game in session
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return
            
            # only grab relevant voting information
            non_zero_votes = {move: votes for move, votes in self.chess_handler.vote_pool.items() if votes != 0}

            # if there are no votes then send a message that indicates such
            if len(non_zero_votes) == 0:
                await interaction.response.send_message("Nobody has voted yet!", ephemeral=True)

            # if there are votes then list them out in an embed
            else:
                embed_message = discord.Embed(title = f"Voting pool:", color = discord.Color.gold())
                [embed_message.add_field(name = move, value = votes, inline = True) for move, votes in non_zero_votes]
                await interaction.followup.send(embed = embed_message)

        except Exception as error:
            self.bot.logger.error(f"Internal command failure:\n{type(error).__name__}: {error}")

    @app_commands.command(name="help", description = "Shows all of the available bot commands.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        try:
            embed_message = discord.Embed(title = "Bot commands", color = discord.Color.green)

            for command in self.bot.commands:
                embed_message.add_field(name = command.name, value = command.description)
            
            await interaction.response.send_message(embed_message)

        except Exception as error:
            self.bot.logger.error(f"Internal command failure:\n{type(error).__name__}: {error}")

# when the bot.load_extension method is called, this function will be called
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Chess(bot))