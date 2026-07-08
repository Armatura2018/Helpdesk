import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio
import os

# --- ЦВЕТОВАЯ ПАЛИТРА БРЕНДА ---
EMBED_COLOR = discord.Color(0xbddc03) # Твой кастомный цвет #bddc03

# --- ЛОКАЛИЗАЦИЯ И ТЕКСТЫ (Официальный стиль S7 Airlines) ---
TRANSLATIONS = {
    'ru': {
        'dm_welcome_title': "Спасибо за открытие обращения",
        'dm_welcome_desc': "-# Для того чтобы наша команда могла оказать вам помощь как можно быстрее, пожалуйста, опишите ваш запрос максимально подробно. Мы оперативно передадим его дежурным агентам поддержки.",
        'footer_bot': "Вы сейчас разговариваете с ботом",
        'footer_agent': "Вы сейчас разговариваете с агентом",
        'check_dm_title': "Обращение формируется",
        'check_dm_desc': "Пожалуйста, проверьте ваши личные сообщения для продолжения диалога.",
        'check_dm_btn': "Перейти в ЛС",
        'ticket_opened_title': "Обращение открыто",
        'ticket_opened_desc': "> Ваш запрос был успешно зарегистрирован. Агенты клиентской службы уведомлены о вашем обращении. Благодарим за ожидание.",
        'eta_text': "\n\nОжидаемое время ответа агента составляет: **{eta}**.\n-# Данное время является ориентировочным. В периоды высокой загрузки службы поддержки время ожидания может быть увеличено.",
        'rejected_title': "Запрос отклонен",
        'rejected_desc': "Приносим свои извинения, но агенты поддержки посчитали ваш запрос некорректным или недостаточно информативным для открытия сессии.",
        'accepted_title': "Клиентская поддержка", # Убрали слэш
        'accepted_desc': "### Ваш запрос был принят в работу\n> Благодарим за обращение в службу поддержки S7 Airlines. Вы были успешно подключены к нашему агенту. Мы стремимся к обеспечению наивысшего уровня сервиса и надеемся предоставить вам всю необходимую помощь.",
        'accepted_instruction': "\n\n-# Чтобы мы могли оказать вам более эффективную помощь, пожалуйста, формулируйте свой запрос четко и кратко, это позволит нам предоставить точную и своевременную поддержку. Просим вас проявить терпение и вежливость, пока мы работаем над тем, чтобы помочь вам.",
        'still_here_title': "Вы еще здесь?",
        'still_here_desc': "> Поскольку мы не получили от вас ответа по решению вашего вопроса, мы просим подтвердить актуальность вашего обращения.",
        'still_here_warning': "\n\n-# Если вам требуется дополнительное время для сбора информации или у вас остались вопросы, пожалуйста, отправьте любое сообщение в этот чат. В противном случае запрос будет автоматически закрыт через 6 часов.",
        'closed_title': "Вопрос решен",
        'closed_desc': "> Благодарим за обращение в службу поддержки S7 Airlines. Мы были рады помочь вам в решении вашего вопроса. Пожалуйста, не стесняйтесь обращаться к нам снова при возникновении трудностей.",
        'closed_footer': "\n-# Мы всегда доступны для решения ваших вопросов. Спасибо за выбор S7 Airlines.",
        'closed_action_footer': "Отвечая на это сообщение, вы откроете новое обращение"
    },
    'en': {
        'dm_welcome_title': "Thank you for opening a ticket",
        'dm_welcome_desc': "-# To help our team assist you as quickly as possible, please describe your request in maximum detail. We will promptly forward it to our support agents.",
        'footer_bot': "You are currently talking to a bot",
        'footer_agent': "You are currently talking to an agent",
        'check_dm_title': "Ticket is being created",
        'check_dm_desc': "Please check your Direct Messages to continue.",
        'check_dm_btn': "Go to DMs",
        'ticket_opened_title': "Ticket Opened",
        'ticket_opened_desc': "> Your request has been successfully registered. Support agents have been notified. Thank you for your patience.",
        'eta_text': "\n\nExpected response time: **{eta}**.\n-# This time is approximate. During peak hours, response times may be longer.",
        'rejected_title': "Request Rejected",
        'rejected_desc': "We apologize, but our support agents deemed your request incorrect or insufficient to open a support session.",
        'accepted_title': "Customer Support", # Убрали слэш
        'accepted_desc': "### Your request has been accepted\n> Thank you for contacting S7 Airlines Support. You have been successfully connected to our support agent. We strive to provide the highest level of service and hope to resolve your request efficiently.",
        'accepted_instruction': "\n\n-# To help us assist you more effectively, please keep your responses clear and concise. This allows us to provide accurate and timely support. We kindly ask for your patience and courtesy while we work to assist you.",
        'still_here_title': "Are you still here?",
        'still_here_desc': "> As we have not received a response regarding your issue, we kindly ask you to confirm if you still need assistance.",
        'still_here_warning': "\n\n-# If you need additional time or have further questions, please send a message in this chat. Otherwise, this ticket will automatically close in 6 hours.",
        'closed_title': "Issue Resolved",
        'closed_desc': "> Thank you for contacting S7 Airlines Support. It was our pleasure to assist you. Please do not hesitate to reach out to us again if you encounter any issues.",
        'closed_footer': "\n-# We are always available to resolve your issues. Thank you for choosing S7 Airlines.",
        'closed_action_footer': "Replying to this message will open a new support ticket"
    }
}

# --- НАСТРОЙКИ БОТА ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class SupportBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False
        self.config = {} 
        self.active_tickets = {} 
        self.eta_time = "15-30 минут" 
        self.ticket_counter = 1

    async def on_ready(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        self.add_view(MainPanelView())
        
        print(f"Служба поддержки S7 Airlines запущена под именем {self.user}")

bot = SupportBot()

def create_embed(title, desc, footer_text):
    """Вспомогательная функция для генерации эмбедов с фирменным цветом"""
    embed = discord.Embed(
        title=title,
        description=desc,
        color=EMBED_COLOR
    )
    embed.set_footer(text=footer_text)
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return embed

# --- СТЕП-БАЙ-СТЕП НАСТРОЙКА /panel ---
class PanelSetupView(discord.ui.View):
    def __init__(self, admin):
        super().__init__(timeout=300)
        self.admin = admin
        self.step = 1
        self.data = {}
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.admin.id:
            await interaction.response.send_message("Эта панель конфигурации вам недоступна.", ephemeral=True)
            return False
        return True

    def update_interface(self, interaction: discord.Interaction):
        self.clear_items()
        guild = interaction.guild

        if self.step == 1:
            select = discord.ui.Select(placeholder="Выберите категорию поддержки...")
            for cat in guild.categories[:25]:
                select.add_option(label=cat.name, value=str(cat.id))
            select.callback = self.save_category
            self.add_item(select)
            return "Шаг 1/4: Выберите **Категорию**, в которой будут создаваться каналы тикетов."

        elif self.step == 2:
            select = discord.ui.Select(placeholder="Выберите категорию для панели...")
            for cat in guild.categories[:25]:
                select.add_option(label=cat.name, value=str(cat.id))
            select.callback = self.save_panel_category
            self.add_item(select)
            return "Шаг 2/4 (Часть 1): Выберите **Категорию**, где находится канал для отправки панели."

        elif self.step == 2.5:
            cat_id = self.data['panel_cat_id']
            category = guild.get_channel(cat_id)
            select = discord.ui.Select(placeholder="Выберите текстовый канал...")
            channels = [ch for ch in category.text_channels][:25]
            if not channels:
                self.step = 2
                return "В выбранной категории нет текстовых каналов! Выберите другую категорию:"
            for ch in channels:
                select.add_option(label=ch.name, value=str(ch.id))
            select.callback = self.save_panel_channel
            self.add_item(select)
            return "Шаг 2/4 (Часть 2): Выберите конкретный **Текстовый канал**, куда прислать панель."

        elif self.step == 3:
            cat_id = self.data['support_cat_id']
            category = guild.get_channel(cat_id)
            select = discord.ui.Select(placeholder="Выберите канал логов...")
            channels = [ch for ch in category.text_channels][:25]
            if not channels:
                channels = [ch for ch in guild.text_channels][:25]
            for ch in channels:
                select.add_option(label=ch.name, value=str(ch.id))
            select.callback = self.save_log_channel
            self.add_item(select)
            return "Шаг 3/4: Выберите **Канал логов** для аудита действий поддержки."

        elif self.step == 4:
            select = discord.ui.Select(placeholder="Выберите роль поддержки...")
            for role in guild.roles[:25]:
                if not role.is_default():
                    select.add_option(label=role.name, value=str(role.id))
            select.callback = self.save_role
            self.add_item(select)
            return "Шаг 4/4: Выберите **Роль поддержки**, сотрудники которой будут видеть тикеты."

        elif self.step == 5:
            ch_id = self.data['panel_channel_id']
            target_channel = guild.get_channel(ch_id)
            
            # Сюда ты можешь вставить кастомные эмодзи строкой, если захочешь (например, emoji="<:yes:1234...>")
            btn_yes = discord.ui.Button(style=discord.ButtonStyle.success, label="Отправить", emoji="✅")
            btn_no = discord.ui.Button(style=discord.ButtonStyle.danger, label="Отмена", emoji="❌")
            
            btn_yes.callback = self.confirm_setup
            btn_no.callback = self.cancel_setup
            
            self.add_item(btn_yes)
            self.add_item(btn_no)
            return f"Конфигурация завершена. Прислать интерактивную панель в канал {target_channel.mention}?"

    async def save_category(self, interaction: discord.Interaction):
        self.data['support_cat_id'] = int(interaction.data['values'][0])
        self.step = 2
        await interaction.response.edit_message(content=self.update_interface(interaction), view=self)

    async def save_panel_category(self, interaction: discord.Interaction):
        self.data['panel_cat_id'] = int(interaction.data['values'][0])
        self.step = 2.5
        await interaction.response.edit_message(content=self.update_interface(interaction), view=self)

    async def save_panel_channel(self, interaction: discord.Interaction):
        self.data['panel_channel_id'] = int(interaction.data['values'][0])
        self.step = 3
        await interaction.response.edit_message(content=self.update_interface(interaction), view=self)

    async def save_log_channel(self, interaction: discord.Interaction):
        self.data['log_channel_id'] = int(interaction.data['values'][0])
        self.step = 4
        await interaction.response.edit_message(content=self.update_interface(interaction), view=self)

    async def save_role(self, interaction: discord.Interaction):
        self.data['support_role_id'] = int(interaction.data['values'][0])
        self.step = 5
        await interaction.response.edit_message(content=self.update_interface(interaction), view=self)

    async def confirm_setup(self, interaction: discord.Interaction):
        bot.config[interaction.guild.id] = self.data
        target_channel = interaction.guild.get_channel(self.data['panel_channel_id'])
        
        main_panel_embed = discord.Embed(
            title="Support / Клиентская поддержка",
            description="If you wish to open a support request, please press the button below.\n\nЕсли вы желаете открыть обращение в службу поддержки, пожалуйста, нажмите кнопку ниже.",
            color=EMBED_COLOR
        )
        main_panel_view = MainPanelView()
        await target_channel.send(embed=main_panel_embed, view=main_panel_view)
        await interaction.response.edit_message(content="Панель успешно установлена и запущена.", view=None)

    async def cancel_setup(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Настройка отменена администратором.", view=None)


# --- ГЛАВНАЯ ПАНЕЛЬ И ВЫБОР ЯЗЫКА ---
class MainPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Request / Открыть обращение", style=discord.ButtonStyle.primary, custom_id="open_request_btn")
    async def open_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.id not in bot.config:
            await interaction.response.send_message("Ошибка: Бот еще не настроен администратором сервера.", ephemeral=True)
            return
            
        if interaction.user.id in bot.active_tickets:
            await interaction.response.send_message("У вас уже есть активная сессия поддержки.", ephemeral=True)
            return

        view = LanguageSelectionView()
        embed = discord.Embed(
            title="Выберите язык | Choose language",
            description="Чтобы наша служба поддержки смогла работать качественнее, пожалуйста, укажите предпочитаемый язык общения.\n\nTo help our customer service provide elite assistance, please select your preferred language.",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class LanguageSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Русский", style=discord.ButtonStyle.secondary, emoji="🇷🇺")
    async def select_ru(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_language(interaction, 'ru')

    @discord.ui.button(label="English", style=discord.ButtonStyle.secondary, emoji="🇬🇧")
    async def select_en(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_language(interaction, 'en')

    async def process_language(self, interaction: discord.Interaction, lang: str):
        user = interaction.user
        
        bot.active_tickets[user.id] = {
            'guild_id': interaction.guild.id,
            'lang': lang,
            'status': 'awaiting_description',
            'channel_id': None,
            'agent_id': None,
            'timer_task': None
        }

        try:
            embed = create_embed(
                title=TRANSLATIONS[lang]['dm_welcome_title'],
                desc=TRANSLATIONS[lang]['dm_welcome_desc'],
                footer_text=TRANSLATIONS[lang]['footer_bot']
            )
            dm_channel = await user.create_dm()
            await dm_channel.send(embed=embed)
        except discord.Forbidden:
            del bot.active_tickets[user.id]
            await interaction.response.edit_message(content="Не удалось отправить сообщение в ЛС. Откройте ЛС в настройках.", embed=None, view=None)
            return

        view_dm = discord.ui.View()
        btn_url = discord.ui.Button(label=TRANSLATIONS[lang]['check_dm_btn'], url=f"https://discord.com/channels/@me/{dm_channel.id}")
        view_dm.add_item(btn_url)
        
        await interaction.response.edit_message(
            content=f"**{TRANSLATIONS[lang]['check_dm_title']}**\n{TRANSLATIONS[lang]['check_dm_desc']}", 
            embed=None, 
            view=view_dm
        )
        
        await asyncio.sleep(20)
        try:
            await interaction.delete_original_response()
        except:
            pass


# --- КНОПКИ ДЛЯ АГЕНТОВ В ТИКЕТ-КАНАЛЕ ---
class AgentTicketActions(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Принять / Accept", style=discord.ButtonStyle.success, custom_id="accept_ticket")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = bot.active_tickets.get(self.user_id)
        if not ticket or ticket['status'] != 'pending_agent':
            await interaction.response.send_message("Тикет уже обработан.", ephemeral=True)
            return

        ticket['status'] = 'chatting'
        ticket['agent_id'] = interaction.user.id
        lang = ticket['lang']

        if ticket['timer_task']:
            ticket['timer_task'].cancel()
        ticket['timer_task'] = asyncio.create_task(start_inactivity_timer(self.user_id, interaction.channel))

        self.clear_items()
        await interaction.response.edit_message(content=f"**Тикет принят агентом {interaction.user.mention}**", view=None)

        user = bot.get_user(self.user_id)
        if user:
            # Отображается строго один язык (без косой черты)
            agent_title = f"{interaction.user.display_name}, {TRANSLATIONS[lang]['accepted_title']}"
            full_desc = TRANSLATIONS[lang]['accepted_desc'] + TRANSLATIONS[lang]['accepted_instruction']
            embed = create_embed(agent_title, full_desc, TRANSLATIONS[lang]['footer_agent'])
            await user.send(embed=embed)

    @discord.ui.button(label="Отклонить / Reject", style=discord.ButtonStyle.danger, custom_id="reject_ticket")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = bot.active_tickets.get(self.user_id)
        if not ticket or ticket['status'] != 'pending_agent':
            await interaction.response.send_message("Тикет уже обработан.", ephemeral=True)
            return

        lang = ticket['lang']
        user = bot.get_user(self.user_id)
        
        if user:
            embed = create_embed(
                TRANSLATIONS[lang]['rejected_title'], 
                TRANSLATIONS[lang]['rejected_desc'], 
                TRANSLATIONS[lang]['footer_bot']
            )
            await user.send(embed=embed)

        if ticket['timer_task']:
            ticket['timer_task'].cancel()
        del bot.active_tickets[self.user_id]
        
        await interaction.response.edit_message(content=f"**Тикет отклонен агентом {interaction.user.mention}**", view=None)
        await asyncio.sleep(5)
        await interaction.channel.delete()


# --- ТАЙМЕРЫ И АВТОЗАКРЫТИЕ ---
async def start_inactivity_timer(user_id, channel):
    try:
        await asyncio.sleep(8 * 3600)
        
        ticket = bot.active_tickets.get(user_id)
        if ticket and ticket['status'] == 'chatting':
            lang = ticket['lang']
            user = bot.get_user(user_id)
            if user:
                embed = create_embed(
                    TRANSLATIONS[lang]['still_here_title'],
                    TRANSLATIONS[lang]['still_here_desc'] + TRANSLATIONS[lang]['still_here_warning'],
                    TRANSLATIONS[lang]['footer_bot']
                )
                await user.send(embed=embed)
                
                # Оформление системного лога в канале тикета
                log_embed = create_embed("⚠️ Ожидание ответа", "> Клиенту отправлено автоматическое уведомление о неактивности. Ожидание завершения: 6 часов.", "Система контроля таймингов")
                await channel.send(embed=log_embed)
            
            await asyncio.sleep(6 * 3600)
            await close_ticket_action(user_id, channel, method="timeout")
            
    except asyncio.CancelledError:
        pass

async def close_ticket_action(user_id, channel, method="manual"):
    ticket = bot.active_tickets.get(user_id)
    if not ticket:
        return

    lang = ticket['lang']
    user = bot.get_user(user_id)
    
    # Сообщение клиенту в ЛС
    if user:
        desc = TRANSLATIONS[lang]['closed_desc'] + TRANSLATIONS[lang]['closed_footer']
        embed = create_embed(TRANSLATIONS[lang]['closed_title'], desc, TRANSLATIONS[lang]['closed_action_footer'])
        await user.send(embed=embed)

    if ticket['timer_task']:
        ticket['timer_task'].cancel()
        
    del bot.active_tickets[user_id]

    # Пункт 4: Оформление закрытия внутри самого канала тикета (Такой же стиль, текст короче)
    staff_reason = "Агентом поддержки" if method == "manual" else "Тайм-аут неактивности клиента"
    staff_embed = create_embed(
        title="Обращение закрыто / Ticket Closed",
        desc=f"> Текущая сессия поддержки была успешно завершена и перемещена в архив.\n\n**Инициатор закрытия:** {staff_reason}",
        footer_text="Архив клиентской службы S7 Airlines"
    )
    await channel.send(embed=staff_embed)


# --- СЛЭШ-КОМАНДЫ ДЛЯ АДМИНИСТРАЦИИ ---
@bot.tree.command(name="panel", description="Запустить интерактивный процесс настройки панели поддержки")
@app_commands.checks.has_permissions(administrator=True)
async def panel_command(interaction: discord.Interaction):
    view = PanelSetupView(interaction.user)
    initial_text = view.update_interface(interaction)
    await interaction.response.send_message(content=initial_text, view=view, ephemeral=True)

@bot.tree.command(name="seteta", description="Изменить ожидаемое время ответа поддержки для клиентов")
@app_commands.checks.has_permissions(manage_messages=True)
async def set_eta(interaction: discord.Interaction, time_val: str):
    bot.eta_time = time_val
    await interaction.response.send_message(f"Ориентировочное время ответа успешно изменено на: **{time_val}**", ephemeral=True)

@bot.tree.command(name="close", description="Закрыть текущую сессию поддержки и зафиксировать тикет")
async def close_command(interaction: discord.Interaction):
    found_user_id = None
    for uid, data in bot.active_tickets.items():
        if data['channel_id'] == interaction.channel.id:
            found_user_id = uid
            break

    if found_user_id:
        await interaction.response.send_message("Запуск процедуры закрытия тикета...", ephemeral=True)
        await close_ticket_action(found_user_id, interaction.channel, method="manual")
    else:
        await interaction.response.send_message("Данный канал не является активным тикетом.", ephemeral=True)


# --- ОБРАБОТКА ВСЕХ СООБЩЕНИЙ (ПЕРЕСЫЛКА ЛС <-> КАНАЛ) ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Клиент пишет боту в ЛС
    if isinstance(message.channel, discord.DMChannel):
        ticket = bot.active_tickets.get(message.author.id)
        if not ticket:
            return

        lang = ticket['lang']
        guild = bot.get_guild(ticket['guild_id'])
        cfg = bot.config.get(guild.id)

        # Первое сообщение (создание тикета)
        if ticket['status'] == 'awaiting_description':
            ticket['status'] = 'pending_agent'
            
            formatted_num = f"{bot.ticket_counter:04d}"
            bot.ticket_counter += 1
            
            support_category = guild.get_channel(cfg['support_cat_id'])
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.get_role(cfg['support_role_id']): discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{formatted_num}",
                category=support_category,
                overwrites=overwrites
            )
            ticket['channel_id'] = ticket_channel.id

            agent_embed = discord.Embed(
                title=f"Запрос от: {message.author.display_name}",
                description=f"> {message.content}",
                color=EMBED_COLOR
            )
            actions_view = AgentTicketActions(message.author.id)
            await ticket_channel.send(embed=agent_embed, view=actions_view)

            eta_desc = TRANSLATIONS[lang]['ticket_opened_desc'] + TRANSLATIONS[lang]['eta_text'].format(eta=bot.eta_time)
            user_embed = create_embed(TRANSLATIONS[lang]['ticket_opened_title'], eta_desc, TRANSLATIONS[lang]['footer_bot'])
            await message.author.send(embed=user_embed)
            return

        # Последующие сообщения клиента (Пункт 3: Оформление ответов клиента как у агента)
        elif ticket['status'] == 'chatting':
            ticket_channel = guild.get_channel(ticket['channel_id'])
            if ticket_channel:
                client_title = f"{message.author.display_name}, Клиент / Client"
                client_embed = create_embed(client_title, f"> {message.content}", TRANSLATIONS[lang]['footer_bot'])
                
                await ticket_channel.send(embed=client_embed)
                
                # Твоя кастомная реакция на сообщения клиента (поставь сюда свой текст эмодзи из инструкции выше, если надо)
                await message.add_reaction("✅")
                
                if ticket['timer_task']:
                    ticket['timer_task'].cancel()
                ticket['timer_task'] = asyncio.create_task(start_inactivity_timer(message.author.id, ticket_channel))

    # Агент пишет в канал тикета на сервере
    else:
        found_user_id = None
        for uid, data in bot.active_tickets.items():
            if data['channel_id'] == message.channel.id:
                found_user_id = uid
                break

        if found_user_id:
            if message.content.startswith(("/", "!")):
                return

            ticket = bot.active_tickets[found_user_id]
            lang = ticket['lang']
            user = bot.get_user(found_user_id)
            
            if user:
                # Динамический заголовок в зависимости от выбранного языка клиента
                agent_title = f"{message.author.display_name}, {TRANSLATIONS[lang]['accepted_title']}"
                embed = create_embed(agent_title, f"> {message.content}", TRANSLATIONS[lang]['footer_agent'])
                await user.send(embed=embed)


# --- ЗАПУСК БОТА ---
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения 'DISCORD_TOKEN' не найдена!")
