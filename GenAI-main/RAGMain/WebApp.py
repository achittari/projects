#!/usr/bin/env python3
"""This is just a simple authentication example.

Please see the `OAuth2 example at FastAPI <https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/>`_  or
use the great `Authlib package <https://docs.authlib.org/en/v0.13/client/starlette.html#using-fastapi>`_ to implement a classing real authentication system.
Here we just demonstrate the NiceGUI integration.
"""
import asyncio
import time
from asyncio import Task
from typing import Optional

from nicegui import run
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import DataAssets
import traceback

import logging
from RAGQueryEngine import RAGQueryEngine
from RAGChatEngine import RAGChatEngine
from io import StringIO
from nicegui import ui
from CustomLogger import CustomLogger
import sys
from nicegui import Client, app, ui

OPENAI_API_KEY = 'not-set'  # TODO: set your OpenAI API key here
# in reality users passwords would obviously need to be hashed
passwords = {'user1': 'pass1_20240724', 'user2': 'pass2_20240724'}

unrestricted_page_routes = {'/login'}

labelMap = dict(assignButtonStr='Assign Dataset', reloadButtonStr='Reload Dataset')
place_holder_msg = ''

logstream = StringIO()
logger = logging.getLogger('CustomLogger')
logger.addHandler(logging.StreamHandler(stream=logstream))
logger.setLevel(logging.DEBUG)
customLogger = CustomLogger(logger)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
logging.getLogger().addHandler(logging.StreamHandler(stream=logstream))

agent_type = DataAssets.AGENT_TYPES[0]

queryEngine = None
chatEngine = None

if(queryEngine == None and chatEngine == None):
    queryEngine = RAGQueryEngine(None)
    chatEngine = RAGChatEngine()

    data_location = ''
    active_count = 0
    processing = 0
    for x in DataAssets.rows:
        if(x.get('status') == 'active'):
            active_count += 1
            data_location = x.get('data_location')
        if(x.get('status') == 'Processing'):
            processing = 1

    if(processing == 0):
        if(active_count == 0):
            for x in DataAssets.rows:
                if (x.get('name') == "Massage Specialist"):
                    x['status'] = 'active'
                    data_location = x.get('location')
                    break
        queryEngine.initialize(location=data_location,forceRefresh=False)
        queryEngine.setLogger(customLogger)

        chatEngine.initialize(location=data_location, forceRefresh=False)
        chatEngine.setLogger(customLogger)


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)


app.add_middleware(AuthMiddleware)


@ui.page('/')
def main_page() -> None:
    #llm = ChatOpenAI(model_name='gpt-3.5-turbo', streaming=True, openai_api_key=OPENAI_API_KEY)
    global queryEngine
    # Setting the custom callback handler as the global handler
    global agent_type
    @ui.refreshable
    async def update_table_details(location, status) -> None:
        global queryEngine
        ui.notify('Update started')
        for row in DataAssets.rows:
            if (row['location'] == location):
                row['status'] = "Processing"
        table.update_rows(DataAssets.rows)
        table.update()

    async def processDataSet(selected_data, refresh) -> None:
        global queryEngine
        if (selected_data != None):
            if (len(selected_data) > 0):
                data = selected_data[0]
                location_str = data.get('location')
                await update_table_details(location_str, data)
                print("Updating to location - ", location_str)
                #result = await run.cpu_bound(queryEngine.initialize, location_str)
                result1 = await run.io_bound(queryEngine.initialize,location_str)
                print(result1)
                result2 = await run.io_bound(chatEngine.initialize, location_str)
                print(result2)
                print("Updated to location Successfully - ", location_str)
                ui.notify('successfully reloaded')

                for row in DataAssets.rows:
                    if (row.get('location') == location_str):
                        row['status'] = 'active'
                        type = row.get("name")
                        agent_label.text = f"{agent_type} - I am a {type}, ask me any questions"
                        agent_label.update()
                    else:
                        row['status'] = 'inactive'
                    print("Post initialize" + str(row))
                table.update_rows(DataAssets.rows)
                table.selected = []
                table.update()
                ui.update(data_assets_tab)

    async def set_agent_type(type):
        global agent_type
        agent_type = type
        print("Setting agent type to ", type)
        for row in DataAssets.rows:
            if (row.get('status') == 'active'):
                name = row.get("name")
                agent_label.text = f"{agent_type} - I am a {name}, ask me any questions"
                agent_label.update()

    async def send() -> None:
        global queryEngine
        global chatEngine

        global agent_type
        question = text.value
        text.value = ''

        with message_container:
            ui.chat_message(text=question, name='You', sent=True).props('style="white-space: pre-line;"')
            response_message = ui.chat_message(name='Bot', sent=False).props('style="white-space: pre-line;"')
            spinner = ui.spinner(type='dots')
        response = ''
        try:
            if (agent_type == DataAssets.AGENT_TYPES[0]):
                result =  await run.io_bound(queryEngine.get_answer, question)
                print("got result successfully ")
                response += str(result)
                response_message.clear()
                with response_message:
                    ui.html(response)
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
            else:
                response_stream = await run.io_bound(chatEngine.get_answer, question)
                for token in response_stream.response_gen:
                    response += str(token)
                    response_message.clear()
                    with response_message:
                        ui.html(response)
                    ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
                print("got result successfully ")
            customLogger.printSuccess(response)
        except Exception as e:
            traceback.print_exc()
            print(str(e))
            response += "Not able to find the answer"

        message_container.remove(spinner)
        log.push(logstream.getvalue())

    selected_data_asset  = ''
    ui.add_css(r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}')

    # the queries below are used to expand the contend down to the footer (content can then use flex-grow to expand)
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    ui.label(f'Hello {app.storage.user["username"]}!').classes('text-2xl')

    with ui.tabs().classes('w-full') as tabs:
        chat_tab = ui.tab('Chat')
        data_assets_tab = ui.tab('Data')
         #strategies_tab = ui.tab("Strategies")
        logs_tab = ui.tab('Logs')
    with ui.tab_panels(tabs, value=chat_tab).classes('w-full max-w-2xl mx-auto flex-grow items-stretch'):
        message_container = ui.tab_panel(chat_tab).classes('items-stretch')
        with ui.tab_panel(data_assets_tab):
            with ui.table(title='Data Assets', columns=DataAssets.columns, rows=DataAssets.rows, selection='single', pagination=10).classes(
                    'w-full max-w-2xl h-full') as table:
                with table.add_slot('top-right'):
                    with ui.input(placeholder='Search').props('type=search').bind_value(table, 'filter').add_slot(
                            'append'):
                        ui.icon('search')
                table.add_slot('bottom-row')
            current_select_label = ui.label().bind_text_from(table, 'selected', lambda val: f'Current selection: {val}')
            assignButton = ui.button('Assign this Dataset', on_click=lambda: processDataSet(table.selected,False))
            assignButton.bind_visibility_from(table, 'selected', backward=lambda val: bool(val))
            assignButton.bind_text(labelMap,"assignButtonStr")
            # Define a single yes/no dialog that gets re-used for all the popups.
            select2 = ui.select([DataAssets.AGENT_TYPES[0],DataAssets.AGENT_TYPES[1]], value=DataAssets.AGENT_TYPES[0]).on_value_change(lambda val : set_agent_type(val.value) )
        with ui.tab_panel(logs_tab):
            log = ui.log().classes('w-full h-full')

    with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            agent_label = ui.label(agent_type + ' - I am a Message Therapy Expert. Ask me any questions').style('color: #37496b; font-size: 150%; font-weight: 150')
        with ui.row().classes('w-full no-wrap items-center'):
            place_holder_msg = 'message' if OPENAI_API_KEY != 'not-set' else \
                'Ask me any questions'
            text = ui.input(placeholder=place_holder_msg).props('rounded outlined input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', send)

    ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout') \
        .props('outline round')

@ui.page('/subpage')
def test_page() -> None:
    ui.label('This is a sub page.')

@ui.page('/login')
def login() -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update({'username': username.value, 'authenticated': True})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
    return None


ui.run(reload=False,storage_secret='THIS_NEEDS_TO_BE_CHANGED',)