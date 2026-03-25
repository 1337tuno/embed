import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
import os
from dotenv import load_dotenv
from flask import Flask  # For Railway health check

# Load environment variables
load_dotenv()

# Flask app for health checks (Railway)
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health_check():
    return {'status': 'healthy', 'bot': str(bot.user)}, 200

# Define Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ================= CONFIGURATION =================
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
SUPPORT_ROLE_IDS = [
    int(id.strip()) for id in os.getenv("SUPPORT_ROLE_IDS", "").split(",") if id.strip()
]
# =================================================

class ServiceModal(Modal):
    def __init__(self, service_name: str):
        super().__init__(title=f"Order: {service_name}")
        self.service_name = service_name
        
        self.address = TextInput(
            label="Address",
            placeholder="Enter your delivery/service address",
            required=True,
            style=discord.TextStyle.long
        )
        
        self.payment = TextInput(
            label="Payment Method",
            placeholder="Crypto, Cash App, Zelle, etc.",
            required=True,
            style=discord.TextStyle.short
        )
        
        self.notes = TextInput(
            label="Additional Notes (Optional)",
            placeholder="Any special instructions...",
            required=False,
            style=discord.TextStyle.long
        )
        
        self.add_item(self.address)
        self.add_item(self.payment)
        self.add_item(self.notes)
    
    async def on_submit(self, interaction: discord.Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("❌ Ticket category not found.", ephemeral=True)
            return

        channel_name = f"ticket-{self.service_name.lower().replace(' ', '-').replace('/', '-')}-{interaction.user.id}"
        channel_name = "".join(c for c in channel_name if c.isalnum() or c in "-").lower()
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel = await interaction.guild.create_text_channel(
            name=channel_name[:48],
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {interaction.user}"
        )
        
        role_mentions = " ".join([f"<@&{role_id}>" for role_id in SUPPORT_ROLE_IDS])
        
        embed = discord.Embed(
            title=f"🎫 Ticket: {self.service_name}",
            description=f"Ticket created by {interaction.user.mention}\n\n{role_mentions}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="📍 Address", value=self.address.value or "Not provided", inline=False)
        embed.add_field(name="💳 Payment Method", value=self.payment.value or "Not provided", inline=False)
        if self.notes.value:
            embed.add_field(name="📝 Additional Notes", value=self.notes.value, inline=False)
        
        embed.set_footer(text=f"Ticket ID: {channel.id} | User ID: {interaction.user.id}")
        
        view = TicketCloseView()
        await channel.send(embed=embed, view=view)
        await channel.send(f"{interaction.user.mention} Your ticket has been created!")
        
        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        user_roles = [role.id for role in interaction.user.roles]
        is_support = any(role_id in SUPPORT_ROLE_IDS for role_id in user_roles)
        
        channel_name = interaction.channel.name
        user_id = channel_name.split('-')[-1] if '-' in channel_name else None
        is_creator = user_id and str(interaction.user.id) == user_id
        
        if not is_support and not is_creator:
            await interaction.response.send_message("❌ Permission denied!", ephemeral=True)
            return
        
        await interaction.response.send_message("🔒 Closing in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ServiceButton(Button):
    def __init__(self, label: str, emoji: str, service_name: str):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.red)
        self.service_name = service_name
    
    async def callback(self, interaction: discord.Interaction):
        modal = ServiceModal(self.service_name)
        await interaction.response.send_modal(modal)

class MainServiceView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # 🔥 FIRST BUTTON: FOOD with 🍔 emoji
        self.add_item(ServiceButton(label="FOOD", emoji="🍔", service_name="FOOD"))
        
        # Rest of buttons
        self.add_item(ServiceButton(label="Hotel", emoji="🏨", service_name="Hotel"))
        self.add_item(ServiceButton(label="Airbnb", emoji="🏠", service_name="Airbnb"))
        self.add_item(ServiceButton(label="Car Rental", emoji="🚗", service_name="Car-Rental"))
        self.add_item(ServiceButton(label="Flights", emoji="✈️", service_name="Flights"))
        self.add_item(ServiceButton(label="Movie", emoji="🎬", service_name="Movie"))
        self.add_item(ServiceButton(label="Concerts/Viator", emoji="🎵", service_name="Concerts-Viator"))
        self.add_item(ServiceButton(label="Event / Experience", emoji="🎪", service_name="Event-Experience"))
        self.add_item(ServiceButton(label="IKEA", emoji="🛋️", service_name="IKEA"))
        self.add_item(ServiceButton(label="URides", emoji="🚕", service_name="URides"))
        self.add_item(ServiceButton(label="UEats", emoji="🛒", service_name="UEats"))
        self.add_item(ServiceButton(label="Groceries", emoji="🛍️", service_name="Groceries"))
        self.add_item(ServiceButton(label="Other Services", emoji="🔧", service_name="Other-Services"))
        self.add_item(ServiceButton(label="Any Type Tickets", emoji="🎟️", service_name="Any-Type-Tickets"))

class TicketsView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServiceButton(label="Tickets", emoji="🎟️", service_name="Tickets"))

@bot.command(name='services')
@commands.has_permissions(administrator=True)
async def services_command(ctx):
    embed = discord.Embed(
        title="🔥❤️ 30–50% OFF Everyday Purchases & Services 🔥❤️",  # 🔥❤️ at top
        description="Select a service below to begin your Beast order.",
        color=discord.Color.red()
    )

    embed.add_field(name="🍔 Food", value="Fast food • Casual dining • Local restaurants • + more", inline=False)
    embed.add_field(
        name="🍽️ Restaurants (Min $40 cart)",
        value="CAVA • Jersey Mike's • Domino's • Wingstop • Applebee's • Five Guys • Panda Express • Chipotle • Pizza Hut • Papa John's • Jet's Pizza • Marco's Pizza • Sweetgreen • Carl's Jr • Habit Burger • Smashburger • Biryani • Pf Chang's • Jollibee • Nordstrom • Chuy's • A1 Wings • Church's • Square Eatmanaao (Thai) • Pizza151 • Bawarchi Biryani • Mod Pizza • Pizza King NY • Don Martin Modern Mexican • Hungry Howie's • Clover • Cafe Veloce • Square Platform Websites • + more",
        inline=False
    )
    embed.add_field(name="✈️ Travel & Stays", value="Car Rentals (Avis, Budget) • Flights • Bus • Train\nHotels • Airbnb", inline=False)
    embed.add_field(name="🎬 Entertainment & Events", value="Movie Tickets – Regal, Cinemark, Marcus, Showcase, Apple Cinemas + more\nEvent Tickets • Concerts • Sports & more", inline=False)
    embed.add_field(name="🛍️ Shopping", value="IKEA • + more", inline=False)
    embed.add_field(name="🔧 Other Services", value="Dine-in bills • Rent payments • Utility/Bill payments • + more", inline=False)
    embed.add_field(name="💳 Payment Methods", value="Crypto (+5% extra discount)\nCash App • Zelle", inline=False)

    await ctx.send(embed=embed, view=MainServiceView())

@bot.command(name='tickets')
@commands.has_permissions(administrator=True)
async def tickets_command(ctx):
    embed = discord.Embed(title="🎟️ Tickets", description="Click below to order tickets", color=discord.Color.blue())
    await ctx.send(embed=embed, view=TicketsView())

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    print(f'🔗 Invite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot')

# Run both Flask and Discord bot
def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

if __name__ == "__main__":
    # Start Flask in background thread for health checks
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    # Start Discord bot
    bot.run(os.getenv("DISCORD_TOKEN"))