import time
from kivy.uix.screenmanager import *
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout 
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.toast import toast
from kivy.properties import ObjectProperty, BooleanProperty, ListProperty
from kivy.uix.button import ButtonBehavior
from kivy.uix.image import Image 
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
import kivy
from kivy.core.window import Window


from itertools import chain

from kivy.graphics.texture import Texture
from jsondb import Db
from classes import Session



class Gradient(object):

    @staticmethod
    def horizontal(*args):
        texture = Texture.create(size=(2, 1), colorfmt='rgba')
        buf = bytes([int(v * 255) for v in chain(*args)])  # flattens

        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(*args):
        texture = Texture.create(size=(1, len(args)), colorfmt='rgba')
        buf = bytes([int(v * 255) for v in chain(*args)])  # flattens
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture


class MainScreen(Screen):

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

class AuthScreen(Screen):
    pwd = ObjectProperty(None)
    eact = BooleanProperty(True)
    def __init__(self, **kwargs):
        super(AuthScreen, self).__init__(**kwargs)

    def Login(self):
        passwd = self.ids['password'].text
        login = self.ids['login'].text
        res = app.session("users.auth",{"email":login, 'password':passwd})
        if 'token' in res:
            session = Session(res['token'],cache)
            cache.data['me'] = {}
            cache.data['me'] = session('users.get')
            cache.data['me']['token'] = session.token
            cache.save()
            toast("Авторизованно!")
            time.sleep(2)
            app.stop()
            
        else: 
            toast(res['error']['text'])

    

class MessengerApp(MDApp):
    def draw_checkbox(self):
        sm.get_screen("auth_screen").remove_widget(self.eye)
        
        pwd = sm.get_screen("auth_screen").pwd
        eye = self.eye
        
        eye.y = pwd.y + pwd.height / 2 - eye.height / 2
        eye.x = pwd.x + pwd.width - (eye.y - pwd.y) - eye.width
        
        sm.get_screen("auth_screen").add_widget(self.eye)
    screen = None
    def __init__(self, session,  **kwargs):
        session = session
        self.session = session
        global sm
        sm = ScreenManager()
        if token:
            for chat in session.chats:
                self.chats.append(chat)
            self.me_id = cache.session.me_id
        #self.sm = ScreenManager()
        #self.sm.add_widget(msgScreen(name="msg_screen"))
        super().__init__(**kwargs)

    
    def chat_select(self, label):
        print(label.id)
        for chat in session.chats:
            if chat['id'] == label.id:
                cache.data['chat'] = chat
        session.messages = session.gethistory(cache.data['chat']['id'])['items']
        session.messages.reverse()
        self.messages = []
        
        for msg in session.messages:
            self.add_message(msg['text'], msg['from_id'])
        self.scroll_bottom()
    messages = ListProperty()
    chats = ListProperty()
    def refreshaeye(self,d):
        print((self,d))
        global sm
        sm.get_screen("auth_screen").eact=d.active
    def build(self):
        global sm
        sm = ScreenManager(transition=SlideTransition())
        if 'token' in cache.data.get('me',{}):
            sm.add_widget(MainScreen(name="msg_screen"))
        else:
            sm.add_widget(AuthScreen(name="auth_screen"))
            self.eye = CheckBox(size_hint=[None, None], size=[50, 50],active=True,background_checkbox_normal="img/hidden.png",background_checkbox_down="img/show.png",on_release=self.refreshaeye)
            sm.get_screen("auth_screen").add_widget(self.eye)
        return sm

    def add_message(self, text, fromid):
        self.messages.append({
            'message_id': len(self.messages),
            'text': text,
            'from_id': fromid,
            'text_size': [None, None],
        })

    def update_message_size(self, message_id, texture_size, max_width):
        # when the label is updated, we want to make sure the displayed size is
        # proper
        if max_width == 0:
            return

        one_line = dp(50)  # a bit of  hack, YMMV

        # if the texture is too big, limit its size
        if texture_size[0] >= max_width * 2 / 3:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
            }

        # if it was limited, but is now too small to be limited, raise the limit
        elif texture_size[0] < max_width * 2 / 3 and \
                texture_size[1] > one_line:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
                '_size': texture_size,
            }

        # just set the size
        else:
            self.messages[message_id] = {
                **self.messages[message_id],
                '_size': texture_size,
            }

    @staticmethod
    def focus_textinput(textinput):
        textinput.focus = True

    def send_message(self, textinput):
        text = textinput.text
        textinput.text = ''
        self.focus_textinput(textinput)
        Clock.schedule_once(lambda *args: cache.session.sendmsg(text, cache.data['chat']['id']), 1)
        self.scroll_bottom()


    def scroll_bottom(self):
        global sm
        rv = sm.get_screen('msg_screen').ids.rv
        box = sm.get_screen('msg_screen').ids.box
        if rv.height < box.height:
            Animation.cancel_all(rv, 'scroll_y')
            Animation(scroll_y=0, t='out_quad', d=.5).start(rv)

    def eventhandler(self,upd):
        print(upd)
        type = upd["type"]
        if cache.data['chat']['id'] in (upd['object']['to_id'], upd['object']['from_id'] ):
            if type ==1:
                self.add_message(upd['object']['text'], upd['object']['from_id'])
                self.session.notif()
            elif type == 2:
                self.add_message(upd['object']['text'], upd['object']['from_id'])
                self.scroll_bottom()



if __name__ == '__main__':
    print('start')
    Builder.load_string("""
    #:include main.kv
    #:include mainscreen.kv
    #:include authscreen.kv
    #:import Clock __main__.Clock
    """)
    cache = Db("cache.json")
    token = cache.data.get('me',{}).get('token')
    session = Session(token,cache)
    cache.session = session
    if token:
        session.chats = session('messages.chats')['items'] # auth
        session.me_id = cache.data.get('me',{}).get('id',0) # auth
    app = MessengerApp(session)
    if token:
        session.start_poll(app.eventhandler) # auth
    app.run()
    

