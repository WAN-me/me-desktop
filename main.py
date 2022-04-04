from kivy.uix.screenmanager import *
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout 
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.uix.button import ButtonBehavior
from kivy.uix.image import Image 
from kivy.animation import Animation
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
Builder.load_file('main.kv')

class MessengerBox(BoxLayout):
    pass

class ImageButton(ButtonBehavior,Image):
    def build(slef):
        return kivy.Widget

class msgScreen(Screen):
    ...

class MessengerApp(App):
    screen = None
    def __init__(self, session,  **kwargs):
        session = session
        self.session = session
        for chat in session.chats:
            self.chats.append(chat)
        self.me_id = cache.session.me_id
        #self.sm = ScreenManager()
        #self.sm.add_widget(msgScreen(name="msg_screen"))
        super(MessengerApp, self).__init__(**kwargs)
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

    def build(self):
        self.screen = MessengerBox()
        return self.screen

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
        rv = self.root.ids.rv
        box = self.root.ids.box
        if rv.height < box.height:
            Animation.cancel_all(rv, 'scroll_y')
            Animation(scroll_y=0, t='out_quad', d=.5).start(rv)


    def eventhandler(self,upd):
        print(upd)
        type = upd["type"]
        
        if type ==1:
            self.add_message(upd['object']['text'], upd['object']['from_id'])
            self.scroll_bottom()
        elif type == 2:
            self.add_message(upd['object']['text'], upd['object']['from_id'])



if __name__ == '__main__':
    print('start')

    cache = Db("cache.json")
    session = Session(cache.data.get('me',{}).get('token','token'),cache)
    cache.session = session
    session.chats = session('messages.chats')['items']
    session.me_id = cache.data.get('me',{}).get('id',0)
    app = MessengerApp(session)
    session.start_poll(app.eventhandler)
    print(session('messages.chats'))
    app.run()
