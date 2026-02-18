import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

CONFIG_FILE = "config.json"

# ===== CRIAR CONFIG SE NÃO EXISTIR =====
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"canal": None, "cargo_pago": None}, f)

def carregar_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def salvar_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# 🔴 MODAL PAGAMENTO SERASA
# =========================

class SerasaModal(discord.ui.Modal, title="Pagamento - SERASA"):

    nome = discord.ui.TextInput(label="Nome do Membro (@usuario)", required=True)
    id_membro = discord.ui.TextInput(label="ID", required=True)
    cargo = discord.ui.TextInput(label="Cargo", required=True)

    async def on_submit(self, interaction: discord.Interaction):

        config = carregar_config()

        if config["canal"] is None:
            await interaction.response.send_message("❌ Canal não configurado.", ephemeral=True)
            return

        canal = bot.get_channel(config["canal"])
        data_atual = datetime.now().strftime("%d/%m/%Y")

        embed = discord.Embed(
            title="📦 Pagamento SERASA",
            color=discord.Color.red()
        )

        embed.add_field(name="Nome", value=self.nome.value, inline=False)
        embed.add_field(name="ID", value=self.id_membro.value, inline=False)
        embed.add_field(name="Cargo", value=self.cargo.value, inline=False)
        embed.add_field(name="Data", value=data_atual, inline=False)
        embed.add_field(name="Usuário Discord", value=interaction.user.mention, inline=False)

        await canal.send(embed=embed)

        await interaction.response.send_message(
            "✅ Dados enviados! Agora envie a PRINT no canal configurado.",
            ephemeral=True
        )

# =========================
# 🟠 MODAL PEDIR EMPRÉSTIMO
# =========================

class EmprestimoModal(discord.ui.Modal, title="📦 Pedido de Empréstimo"):

    nome = discord.ui.TextInput(label="Nome do Membro (@usuario)", required=True)
    id_membro = discord.ui.TextInput(label="ID", required=True)
    cargo = discord.ui.TextInput(label="Cargo", required=True)
    mercadoria = discord.ui.TextInput(label="Mercadoria Retirada", required=True)
    tipo = discord.ui.TextInput(label="Tipo de Mercadoria", required=True)
    quantidade = discord.ui.TextInput(label="Quantidade", required=True)
    valor = discord.ui.TextInput(label="Valor Estimado", required=True)
    motivo = discord.ui.TextInput(label="Motivo da Retirada", required=True)
    prazo = discord.ui.TextInput(label="Prazo de Devolução (Ex: 04:00)", required=True)

    async def on_submit(self, interaction: discord.Interaction):

        config = carregar_config()

        if config["canal"] is None:
            await interaction.response.send_message("❌ Canal não configurado.", ephemeral=True)
            return

        canal = bot.get_channel(config["canal"])
        data_atual = datetime.now().strftime("%d/%m/%Y")

        embed = discord.Embed(
            title="📦 NOVO PEDIDO DE EMPRÉSTIMO",
            color=discord.Color.orange()
        )

        embed.add_field(name="Nome", value=self.nome.value, inline=False)
        embed.add_field(name="ID", value=self.id_membro.value, inline=False)
        embed.add_field(name="Cargo", value=self.cargo.value, inline=False)
        embed.add_field(name="Data", value=data_atual, inline=False)

        embed.add_field(name="📋 Mercadoria Retirada", value=self.mercadoria.value, inline=False)
        embed.add_field(name="Tipo", value=self.tipo.value, inline=False)
        embed.add_field(name="Quantidade", value=self.quantidade.value, inline=False)
        embed.add_field(name="Valor Estimado", value=self.valor.value, inline=False)
        embed.add_field(name="Motivo", value=self.motivo.value, inline=False)

        embed.add_field(name="⏳ Prazo", value=self.prazo.value, inline=False)
        embed.add_field(name="Data Limite", value=data_atual, inline=False)

        embed.set_footer(text=f"Solicitado por {interaction.user}")

        await canal.send(embed=embed)

        await interaction.response.send_message(
            "✅ Pedido de empréstimo enviado para análise.",
            ephemeral=True
        )

# =========================
# 🛡️ PAINEL ADMIN
# =========================

class PainelAdmin(discord.ui.View):

    @discord.ui.button(label="Ver Configurações", style=discord.ButtonStyle.blurple)
    async def ver_config(self, interaction: discord.Interaction, button: discord.ui.Button):

        config = carregar_config()

        embed = discord.Embed(title="⚙ Configurações Atuais", color=discord.Color.blue())
        embed.add_field(name="Canal", value=str(config["canal"]), inline=False)
        embed.add_field(name="Cargo Pago", value=str(config["cargo_pago"]), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Resetar Config", style=discord.ButtonStyle.red)
    async def resetar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores.", ephemeral=True)
            return

        salvar_config({"canal": None, "cargo_pago": None})
        await interaction.response.send_message("✅ Configurações resetadas.", ephemeral=True)

# =========================
# 📌 COMANDOS SLASH
# =========================

@bot.tree.command(name="serasa", description="Registrar pagamento")
async def serasa(interaction: discord.Interaction):
    await interaction.response.send_modal(SerasaModal())

@bot.tree.command(name="pedir_emprestimo", description="Solicitar empréstimo")
async def pedir_emprestimo(interaction: discord.Interaction):
    await interaction.response.send_modal(EmprestimoModal())

@bot.tree.command(name="configurar_canal", description="Configurar canal de registros")
@app_commands.checks.has_permissions(administrator=True)
async def configurar_canal(interaction: discord.Interaction, canal: discord.TextChannel):

    config = carregar_config()
    config["canal"] = canal.id
    salvar_config(config)

    await interaction.response.send_message(
        f"✅ Canal configurado para {canal.mention}",
        ephemeral=True
    )

@bot.tree.command(name="configurar_cargo_pago", description="Configurar cargo para quem pagar")
@app_commands.checks.has_permissions(administrator=True)
async def configurar_cargo(interaction: discord.Interaction, cargo: discord.Role):

    config = carregar_config()
    config["cargo_pago"] = cargo.id
    salvar_config(config)

    await interaction.response.send_message(
        f"✅ Cargo configurado: {cargo.name}",
        ephemeral=True
    )

@bot.tree.command(name="painel_admin", description="Abrir painel administrativo")
@app_commands.checks.has_permissions(administrator=True)
async def painel_admin(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🛡 Painel Administrativo SERASA",
        view=PainelAdmin(),
        ephemeral=True
    )

# =========================
# 📸 DETECTAR PRINT + DAR CARGO
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    config = carregar_config()

    if config["canal"] and message.channel.id == config["canal"]:
        if message.attachments:

            embed = discord.Embed(
                title="📸 Print Recebida",
                description=f"Enviada por {message.author.mention}",
                color=discord.Color.green()
            )

            embed.set_image(url=message.attachments[0].url)
            await message.channel.send(embed=embed)

            if config["cargo_pago"]:
                cargo = message.guild.get_role(config["cargo_pago"])
                if cargo:
                    await message.author.add_roles(cargo)

    await bot.process_commands(message)

@bot.event
async def setup_hook():
    await bot.tree.sync()

@bot.event
async def on_ready():
    print(f"Bot ligado como {bot.user}")

bot.run(TOKEN)
