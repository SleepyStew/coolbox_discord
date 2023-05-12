import os
import time

import discord
from discord.ui import Item
from fastapi import FastAPI
from uvicorn import Config, Server
import dotenv
import requests

dotenv.load_dotenv()

app = FastAPI()
bot = discord.Client()


@app.get("/")
async def root(user: str, id: int, name: str, title: str, due: int, assessment: str = None):
    response = await send_message(user, id, name, title, assessment, due)
    return response


epoch_key = {
    "5 minutes": 300,
    "10 minutes": 600,
    "20 minutes": 1200,
    "30 minutes": 1800,
    "1 hour": 3600,
    "Tomorrow": 86400,
}


class MyView(discord.ui.View):
    def __init__(self, user, title, assessment, due, *items: Item):
        super().__init__(*items)
        self.user = user
        self.title = title
        self.assessment = assessment
        self.due = due

    @discord.ui.select(  # the decorator that lets you specify the properties of the select menu
        placeholder="Remind me in...",  # the placeholder text that will be displayed if nothing is selected
        min_values=1,  # the minimum number of values that must be selected by the users
        max_values=1,  # the maximum number of values that can be selected by the users
        options=[  # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="5 minutes",
                description="I'll resend you this reminder here in 5 minutes."
            ),
            discord.SelectOption(
                label="10 minutes",
                description="I'll resend you this reminder here in 10 minutes."
            ),
            discord.SelectOption(
                label="20 minutes",
                description="I'll resend you this reminder here in 20 minutes."
            ),
            discord.SelectOption(
                label="30 minutes",
                description="I'll resend you this reminder here in 30 minutes."
            ),
            discord.SelectOption(
                label="1 hour",
                description="I'll resend you this reminder here in 1 hour."
            ),
            discord.SelectOption(
                label="Tomorrow",
                description="I'll resend you this reminder here same time tomorrow."
            ),
        ]
    )
    async def select_callback(self, select, interaction):  # the function called when the discord_user is done selecting options
        select.disabled = True
        await self.message.edit(view=self)

        json = {
            "title": self.title,
            "due": int((self.due + epoch_key[select.values[0]] * 1000) if select.values[0] == "Tomorrow" else (time.time() * 1000 + epoch_key[select.values[0]] * 1000)),
            "method": "discord",
            "assessment": None if self.assessment is None else int(self.assessment),
            "user": self.user
        }

        print(json)

        headers = {
            "authorization": "Bearer " + os.environ.get("PERMANENT_TOKEN")
        }

        response = requests.post(os.environ.get("SERVER_URL") + "reminders/reschedule", json=json, headers=headers)

        print(response)
        print(response.json())

        if response.status_code == 200:
            if select.values[0] == "Tomorrow":
                await interaction.response.send_message(f"Alright, I'll remind you same time tomorrow 👍")
            else:
                await interaction.response.send_message(f"Alright, I'll remind you in {select.values[0]} 👍")
        else:
            await interaction.response.send_message(f"Somethings not working right now, if this continues please report this to <@566951727182381057>.")


async def send_message(user, id, name, title, assessment, due):
    discord_user = await bot.fetch_user(id)
    if discord_user is None:
        return {"status": "error"}
    # get discord_user by username and tag

    title = title.replace('\\n', '\n')
    try:
        embed = discord.Embed(title="CoolBox Reminder", url="https://schoolbox.donvale.vic.edu.au/", description=f"Hey {name} :wave: You have a reminder.",
                              colour=discord.Colour.from_rgb(88, 101, 242))
        embed.add_field(name="Reminder", value=title, inline=True)
        await discord_user.send(embed=embed, view=MyView(user, title, assessment, due))
        return {"status": "success"}
    except:
        return {"status": "error"}


config = Config(app=app, host="0.0.0.0", port=30022)
server = Server(config)
bot.loop.create_task(server.serve())
bot.run(os.environ.get("TOKEN"))
