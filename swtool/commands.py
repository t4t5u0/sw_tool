import inspect
import sys
import sqlite3

from swtool import subcommands
from swtool.color import Color

class Commands():

    current_character = ''

    def __init__(self):
        pass

    def append(self, char):
        for item in char:
            print(f'add "{item}"')

    def change(self,arg):
        self.current_character = arg[0]
        print(f'{self.current_character} を追跡しています')

    def ls(self):
        pass

    def kill(self):
        pass

    def check(self, arg):
        conn = sqlite3.connect('./db/character_list.db', detect_types=sqlite3.PARSE_DECLTYPES)
        #conn = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        for row in c.execute('SELECT skill_name, skill_effect, round FROM character_list WHERE chara_name == ?;', (arg[0],)):
            print(row)
        conn.close()

    def start(self):
        pass

    def end(self):
        pass

    def add(self, arg):
        if self.current_character == '':
            print('対象にするキャラクタを設定してください')
        else:
            for item in arg:
                print(f'{item} to {self.current_character}')
        return None

    def remove(self):
        pass

    def neko(self):
        print('にゃーん')

    def help(self):
        print(
    f'''コマンド一覧を表示
    {'─'*100}
    {'name':^10}| {'explanation':^40}| {'arguments':^50}
    {'─'*100}
    {'append':<10}| キャラクタを追加{' '*(40-subcommands.get_east_asian_count('キャラクタを追加'))}| キャラクタ1 キャラクタ2 キャラクタ3 ...{' '*(50-subcommands.get_east_asian_count('キャラクタ1 キャラクタ2 キャラクタ3 ...'))}
    {'change':<10}| 状態を変更したいキャラクタを変更{' '*(40-subcommands.get_east_asian_count('状態を変更したいキャラクタを変更'))}| キャラクタ/キャラクタID{' '*(50-subcommands.get_east_asian_count('キャラクタ/キャラクタID'))}
    {'ls':<10}| キャラクタ一覧を表示{' '*(40-subcommands.get_east_asian_count('キャラクタ一覧を表示'))}| 引数なし{' '*(50-subcommands.get_east_asian_count('引数なし'))}
    {'kill':<10}| キャラクタを消去{' '*(40-subcommands.get_east_asian_count('キャラクタを消去'))}| キャラクタ/キャラクタID{' '*(50-subcommands.get_east_asian_count('キャラクタ/キャラクタID'))}
    {'add':<10}| 技能・呪文などを付与{' '*(40-subcommands.get_east_asian_count('技能・呪文などを付与'))}| 技能・呪文など 効果ラウンド上書き(オプショナル){' '*(50-subcommands.get_east_asian_count('技能・呪文など 効果ラウンド上書き(オプショナル)'))}
    {'remove':<10}| 技能・呪文などを消去{' '*(40-subcommands.get_east_asian_count('技能・呪文などを消去'))}| 技能・呪文など/状態ID{' '*(50-subcommands.get_east_asian_count('技能・呪文など/状態ID'))}
    {'check':<10}| 技能・呪文などの一覧を表示{' '*(40-subcommands.get_east_asian_count('技能・呪文などの一覧を表示'))}| 引数なし/キャラクタ/キャラクタID{' '*(50-subcommands.get_east_asian_count('引数なし/キャラクタ/キャラクタID'))}
    {'start':<10}| 手番を開始{' '*(40-subcommands.get_east_asian_count('手番を開始'))}| 引数なし{' '*(50-subcommands.get_east_asian_count('引数なし'))}
    {'end':<10}| 手番を終了{' '*(40-subcommands.get_east_asian_count('手番を終了'))}| 引数なし{' '*(50-subcommands.get_east_asian_count('引数なし'))}
    {'neko':<10}| にゃーん{' '*(40-subcommands.get_east_asian_count('にゃーん'))}| 引数なし{' '*(50-subcommands.get_east_asian_count('引数なし'))}
    {'help':<10}| これ{' '*(40-subcommands.get_east_asian_count('これ'))}| 引数なし{' '*(50-subcommands.get_east_asian_count('引数なし'))}
    {'stop':<10}| アプリケーションを終了させる{' '*(40-subcommands.get_east_asian_count('アプリケーションを終了させる'))}| 引数なし{' '*(50-subcommands.get_east_asian_count('引数なし'))}
    {'─'*100}''')

    def stop(self):
        x = input(f'[Y/n]\n{Color.GREEN}> {Color.RESET}')
        if  x == 'Y' or x == 'y':
            exit()
        elif x == 'N' or x == 'n':
            return
        else:
            stop()
'''
class Commands:
    def __init__(self):
        self.name = ''
        self.exp = ''
        self.arg = ''

    def stop(self):
        name = sys._getframe().f_code.co_name
        exp = 'アプリケーションを終了させる'
        arg = '引数なし '
        x = input(f'[Y/n]\n{Color.GREEN}>{Color.RESET}')
        if  x == 'Y' or x == 'y':
            exit()
        else:
            return

    def help(self):
        self.name = sys._getframe().f_code.co_name
        self.exp = 'これ'
        self.arg = '引数なし'
        print(help.name)
        hoge = Commands()
        print(inspect.getmembers(Commands(), inspect.ismethod))
        for x in inspect.getmembers(Commands(), inspect.ismethod):
            print(eval(f'Commands.{x}.name'))

command = Commands()
command.stop()
'''