import inspect
import json
import pathlib
import re
import sqlite3
import sys
from cmd import Cmd

from swatlib.color import Color
from swatlib.subcommands import (count_east_asian_character,
                                 get_east_asian_count, serch_words_index,
                                 turn_back_text)


class Command(Cmd):

    def __init__(self, path):
        super().__init__()
        self.current_directory = path
        self.prompt = f'{Color.GREEN}> {Color.RESET}'
        self.intro = (
            f'{Color.MAGENTA}Hello{Color.RESET}\n'
            f'{"─"*100}\n'
            f'- コマンド一覧は helps で見ることができます\n'
            f'- help cmd を使用すると cmd の詳細を見ることができます\n'
            f'- 詳しいことは https://github.com/t4t5u0/swat/wiki を確認してください\n'
            f'{"─"*100}'
        )
        self.current_character = ''
        self.turn = None
        self.nick_pattern = re.compile(r'(ch|en|npc|oth)([0-9]*[*]|[0-9]+)')

        # ユーザ定義型 その1
        List = list
        # (lambda l: list(l) if type(l) != list else l)]))
        sqlite3.register_adapter(List, lambda l: ';'.join([str(i) for i in l]))
        sqlite3.register_converter(
            'List', lambda s: [item.decode('utf-8') for item in s.split(bytes(b';'))])

        # ユーザ定義型 その2
        Bool = bool
        sqlite3.register_adapter(Bool, lambda b: str(b))
        sqlite3.register_converter('Bool', lambda l: bool(eval(l)))

    def nick2chara(self, characters: list) -> list:
        conn = sqlite3.connect(
            self.current_directory/"db"/"data.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        tmp = []
        for char in characters:
            if re.match(self.nick_pattern, char):
                if char[-1] == '*':
                    # char[:-1]% で検索する
                    c.execute(
                        'SELECT COUNT(name) FROM character_list WHERE nick LIKE ?', (f'{char[:-1]}%',))
                    cnt = c.fetchone()[0]
                    # 存在してるかどうか
                    if cnt:
                        c.execute(
                            'SELECT name FROM character_list WHERE nick LIKE ?', (f'{char[:-1]}%',))
                        tmp += [skill[0] for skill in (c.fetchall())]
                        # print(tmp)
                    else:
                        print(f'{char}に該当するキャラクタは存在しません')
                else:
                    # charで検索する
                    c.execute(
                        'SELECT COUNT(name) FROM character_list WHERE nick = ?', (char,))
                    cnt = c.fetchone()[0]
                    # 存在してるかどうか
                    if cnt:
                        c.execute(
                            'SELECT name FROM character_list WHERE nick = ?', (char,))
                        tmp += c.fetchone()
                    else:
                        print(f'{char}に該当するキャラクタは存在しません')
            else:
                # 普通に検索
                # なかったらメッセージ出して飛ばす
                c.execute(
                    'SELECT COUNT(name) FROM character_list WHERE name = ?', (char,))
                cnt = c.fetchone()[0]
                if cnt:
                    c.execute(
                        'SELECT name FROM character_list WHERE name = ?', (char,))
                    tmp += c.fetchone()
                else:
                    print(f'{char}というキャラクタは存在しません')
        conn.close()
        characters = list(set(tmp))
        return characters

    def do_append(self, inp):
        ('ap(append) <characters> [-n <nicknames> ]\n'
         '  キャラクタを追加するコマンド。空白区切りで列挙することで、一度に複数のキャラ\n'
         '  クタを追加することができます。追加したキャラクタが一体の場合は、自動的に、技\n'
         '  能を付与する対象として選択されます。\n'
         'オプション\n'
         '  -n\n'
         '    キャラクタにラベルを追加する。使えるのは、ch, en, npc, oth の末尾に数字を付\n'
         '    け加えたものが使えます。これはlsコマンドで確認でき、キャラクタの名前とし\n'
         '    て扱えます。また、ch* とすることで、ch から始まるすべてのキャラクタを対象\n'
         '    にすることができます')

        # 前処理
        # そのうちリファクタする
        try:
            a, b = inp.split('-n')
        except:
            a = inp
            b = ''
        arg = a.split()
        nicks = b.split()
        if len(arg) < len(nicks):
            print('nickの方が長い')
            return
        else:
            nicks += ['' for _ in range(len(arg)-len(nicks))]

        if arg == []:
            print('引数にキャラクタ名を指定してください')
            return
        conn = sqlite3.connect(
            f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()

        for chara, nick in zip(arg, nicks):
            if re.fullmatch(self.nick_pattern, chara):
                print(f'{chara}という名前は使用できません')
                continue
            c.execute(
                'SELECT COUNT (name) FROM character_list WHERE name = ?', (chara,))
            if c.fetchone()[0]:
                print(f'<{chara}> はすでに存在しています')
                continue
            c.execute(
                'INSERT INTO character_list (name, nick) VALUES (?, ?)', (chara, nick))
            print(f'<{chara}> をキャラクタリストに追加しました')
            # 入力されたキャラクタが1つのときは、自動的にcurrent_characterに設定する
            if len(arg) == 1:
                self.current_character = arg[0]
                print(f'<{self.current_character}> を効果の対象にします')
                self.prompt = f'({self.current_character}){Color.GREEN}> {Color.RESET}'
            conn.commit()
        conn.close()

    def do_nick(self, inp):
        ('nick <characters> <-n> <nicknames>\n'
         '  キャラクタにラベルをつけます。append で行ったラベル付けと同等の機能です。\n'
         'オプション\n'
         '  -n\n'
         '    キャラクタにラベルを追加する。使えるのは、ch, en, npc, oth の末尾に数字を付\n'
         '    け加えたものが使えます。これはlsコマンドで確認でき、キャラクタの名前とし\n'
         '    て扱えます。また、ch* とすることで、ch から始まるすべてのキャラクタを対象\n'
         '    にすることができます')

        arg = inp.split()
        characters = []
        nicknames = []

        if '-n' in arg:
            characters = arg[:arg.index('-n')]
            nicknames = arg[arg.index('-n')+1:]
        else:
            print('> nick <characters> -n <nickname>')
            return
        if len(arg) == 0:
            print('ex: nick swift -n ch1')
            return

        for chara, nick in zip(characters, nicknames):
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            # キャラが存在するか確認
            c.execute(
                'SELECT COUNT(name) FROM character_list WHERE name = ?', (chara,))
            exist_chara = c.fetchone()
            exist_chara = int(exist_chara[0])
            if exist_chara:
                if re.fullmatch('(ch|en|npc|oth)[0-9]+', nick):
                    c.execute(
                        'UPDATE character_list SET nick = ? WHERE name = ?', (nick, chara))
                    print(f'{chara} を {nick} として登録します')
                # 非NULLなら警告出したほうが嬉しい？
                else:
                    print('ch, en, npc, oth の末尾に数字をつけた文字列のみを使用できます')
            else:
                print('キャラクタが存在しません')
        conn.commit()
        conn.close()

    def do_change(self, inp):
        ('ch(change) <character>\n'
         '  追従するキャラクタを選択します。引数はキャラクタⅠ体のみです。\n')

        char = inp.split()
        if len(char) == 0:
            print('引数が少なすぎます。changeは引数を１つ取ります。詳細は help change で確認してください。')
            return
        if len(char) >= 2:
            print('引数が多すぎます。changeは引数を１つ取ります。詳細は help change で確認してください。')
            return
        char = self.nick2chara(char)
        if len(char) == 0:
            return
        self.current_character = char[0]
        print(f'<{self.current_character}> を効果の対象にします')
        self.prompt = f'({self.current_character}){Color.GREEN}> {Color.RESET}'

    def do_ls(self, inp):
        ('ls'
         'キャラクタ一覧を確認するコマンド。ラベルも同時に表示されます')
        char = inp.split()
        if len(char) != 0:
            print('ls は引数なしです。詳しくは help ls')
        else:
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            result = c.execute('SELECT name, nick FROM character_list')
            result = c.fetchall()
            if len(result) == 0:
                return
            print(f'{"name":^15}{"nick":^10}')
            print('──────────────────────────')
            for skill in result:
                print(
                    f'{skill[0]:^{15-count_east_asian_character(skill[0])}}{skill[1] if skill[1] else "":^10}')

    def do_kill(self, inp):
        ('kill <characters | --all>\n'
         '  キャラクタを削除するコマンド。紐付けられている効果は全て削除されます。ch1 \n'
         '  ch2 と列挙したり、ch* や en* とすることで、複数対象を選択することができます。\n'
         'オプション\n'
         '  --all\n'
         '    すべてのキャラクタを対象にします'
         )
        char = inp.split()
        if len(char) == 0:
            print('引数を1つ以上とります。')
            return
        elif '--all' in char:
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            c.execute('DELETE FROM character_list')
            c.execute('DELETE FROM status_list')
            self.current_character = ''
            conn.commit()
            conn.close()
            print('すべてのキャラクタを削除しました')
            self.prompt = f'{Color.GREEN}> {Color.RESET}'
        else:
            char = self.nick2chara(char)
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            for skill in char:
                c.execute(
                    'SELECT COUNT (*) FROM character_list WHERE name = ?', (skill,))
                n = c.fetchone()[0]
                if n == 1:
                    c.execute(
                        'DELETE FROM status_list WHERE chara_name = ?', (skill,))
                    c.execute(
                        'DELETE FROM character_list WHERE name = ?', (skill,))
                    print(f'<{skill}> を削除しました。')
                else:
                    print(f'<{skill}> というキャラは存在しません。')
            conn.commit()
            conn.close()
        # 消去するキャラがcurrent_characterならcurrent_chara を初期化
        if self.current_character in char:
            self.current_character = ''
            self.prompt = f'{Color.GREEN}> {Color.RESET}'

    def do_check(self, inp):
        ('ck(check) <characters | --all>\n'
         '  対象の技能を確認するコマンド\n'
         'オプション\n'
         '  --all\n'
         '    すべてのキャラクタの技能を確認します')
        char = inp.split()
        if len(char) == 0:
            if self.current_character == '':
                print('引数が少なすぎます。check は引数を1つとります。', end='')
                print('デフォルトでは、現在追従中のキャラクタが設定されています。', end='')
                print('詳細は help check で確認してください。')
                return
            else:
                # 下の行でスライスするからリストにキャスト
                char = [self.current_character]
        # 複数キャラを見たいという要望があった
        print(f'{"名前":^{15-count_east_asian_character("名前")}}|'
              f'{"スキル名":^{40-count_east_asian_character("スキル名")}}'
              f'{"残りラウンド":^{15-count_east_asian_character("残りラウンド")}}'
              f'{"効果":^{30-count_east_asian_character("効果")}}')
        print('─'*100)
        if '--all' in char:
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            c.execute('SELECT name FROM character_list')
            char = [skill[0] for skill in c.fetchall()]

        char = self.nick2chara(char)
        for ch in char:
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            quely = 'SELECT skill_name, skill_effect, round FROM status_list WHERE chara_name = ?;'
            result = list(c.execute(quely, (ch,)))
            if len(result) == 0:
                print(f"{ch:^15}|{'':^40}{'':^15}{'':<30}")
            else:
                for i, row in enumerate(result):
                    text = turn_back_text(row[1], 30)
                    for j, line in enumerate(text):
                        if j == 0:
                            print(f"{ch if i == 0 else '':^{15-count_east_asian_character(ch if i == 0 else '')}}|"
                                  f"{row[0]:^{max(40-count_east_asian_character(row[0]), 0)}}"
                                  f"{row[2]:^{15-count_east_asian_character(str(row[2]))}}"
                                  #   幅寄せの値が-になるとエラーを起こすからmax(,0)を噛ませる
                                  f"{line:<{max(30-count_east_asian_character(line), 0)}}")
                        else:
                            print(
                                f"{' '*15}|{' '*40}{' '*15}{line:<{max(30-count_east_asian_character(line), 0)}}")
            conn.close()
            print('─'*100)

    def do_start(self, inp):
        ('start <-t characters>\n'
         '  手番の開始を表すコマンド。同時にラウンドも経過します\n'
         'オプション\n'
         '  -t\n'
         '    他のコマンドと同様に、キャラクタ名やラベルを列挙し、複数対象に適用するこ\n'
         '    とができます')
        # デフォルトではself.current_character を渡す。

        def process(c, arg):
            result = c.execute(
                "SELECT DISTINCT chara_name, skill_name, round , use_start FROM status_list WHERE chara_name = ? AND use_start = 'True'", (arg,))
            result = list(result)
            if len(list(result)) == 0:
                print('手番開始時に行う処理はありません')
            else:
                for row in result:
                    print(f'{row[1]}の処理を行ってください')

        characters = inp.split()
        if len(characters) == 0:
            if self.current_character == '':
                print('キャラクタを選択してください。 help start')
                return
            else:
                characters = [self.current_character]
        if '--all' in characters:
            conn = sqlite3.connect(
                f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            c.execute('SELECT name FROM character_list')
            characters = [skill[0] for skill in c.fetchall()]
        else:
            # とりあえず全部キャラクタにする
            characters = self.nick2chara(characters)
        conn = sqlite3.connect(f'{self.current_directory}/db/data.db')
        c = conn.cursor()
        for chara in characters:
            process(c, chara)
            c.execute(
                'SELECT chara_name, skill_name, round FROM status_list WHERE chara_name = ?', (chara,))
            round_list = c.fetchall()
            # 指定されたキャラクタの技能のラウンドをすべて1減少
            # タプルからリストに変形
            round_list = list(map(list, round_list))
            # round_list[i][2] をデクリメントする
            for i, _ in enumerate(round_list):
                if round_list[i][2] > 0:
                    round_list[i][2] -= 1
            # (chara_name, skill_name, round) のタプルで入ってくるがクエリに合わせるために軸を入れ替える
            # (round, chara_name, skill_name) の形にしたい
            round_list = [(skill[2], skill[0], skill[1])
                          for skill in round_list]
            # start したときに、round_list の末尾の要素が全ての要素にコピーされてしまう不具合
            # 技能名を指定していないから、末尾の要素ですべて上書きする
            c.executemany(
                'UPDATE status_list SET round = ? WHERE chara_name = ? AND skill_name = ?', round_list)
            c.execute(
                'DELETE FROM status_list WHERE round = 0 AND chara_name = ?', (chara,))
            conn.commit()

    def do_end(self, inp):
        ('end <-t characters>\n'
         '  手番の開始を表すコマンド。同時にラウンドも経過します\n'
         'オプション\n'
         '  -t\n'
         '    他のコマンドと同様に、キャラクタ名やラベルを列挙し、複数対象に適用するこ'
         '    とができます')
        # 保守性を上げるため、関数内関数を用いる

        def process(c, arg):
            result = c.execute(
                "SELECT DISTINCT chara_name, skill_name, round , use_end FROM status_list WHERE chara_name = ? AND use_end = 'True'", (arg,))
            result = list(result)
            if len(list(result)) == 0:
                print('手番終了時に行う処理はありません')
            else:
                for row in result:
                    print(f'{row[1]}の処理を行ってください')
            # conn.close()

        arg = inp.split()
        conn = sqlite3.connect(f'{self.current_directory}/db/data.db')
        c = conn.cursor()
        if len(arg) == 0:
            if self.current_character == '':
                print('chenge コマンドでキャラクタを指定してください')
            else:
                process(c, self.current_character)
        elif len(arg) == 1:
            process(c, arg[0])
        else:
            print('引数が多すぎます')
            return

    def do_add(self, inp):
        ('ad(add) <skills> [-t <characters> -r <round>]\n'
         '  技能を追加します。空白区切りで列挙することで、複数の技能や効果を同時に追加す\n'
         '  ることができます。技能が複数見つかった場合は、番号を指定し、その番号の技能が\n'
         '  追加されます。デフォルトでは、現在追従中のキャラクタに対して技能を付与します\n'
         'オプション\n'
         '  -r\n'
         '    抵抗短縮などで、技能の効果ラウンドを変更したいときに使用します。\n'
         '  -t\n'
         '    技能を追加する対象を選択します。他のコマンドと同様に、キャラクタ名やラベ\n'
         '    ルを列挙することで、複数対象に技能を付与することができます。')

        # 抵抗短縮の処理
        # 複数キャラに付与できるようにする
        # nickを参照して付与できるようにする
        # それらの複合できるようにする
        # 複数技能削除する？
        # --round を実装する
        # searchすると2個あるときにバグる。.count して個数分かってれば大丈夫
        arg = inp.split()

        r_position = None
        t_position = None
        if '--round' in arg or '-r' in arg:
            if (arg.count('--round') + arg.count('-r')) >= 2:
                print('パラメータが不正です。-r の数は1つでなければいけません')
                return
            else:
                r_position = serch_words_index(arg, ['--round', '-r'])[0]

        if '--target' in arg or '-t' in arg:
            if (arg.count('--target') + arg.count('-t')) >= 2:
                print('パラメータが不正です。-t の数は1つでなければいけません')
                return
            else:
                t_position = serch_words_index(arg, ['--target', '-t'])[0]

        if len(arg) == 0:
            print('引数が少なすぎます。add は1つ以上の引数をとります。詳細は help add で確認してください。')
            return
        if self.current_character == '' and not t_position:
            print('対象にするキャラクタを設定してください')
            return

        # 引数系の処理を全部上でしてしまおう
        skills = []
        characters = []
        rounds = ''
        # -r -t がともに存在する時
        if r_position and t_position:
            # -t が手前に存在するとき
            if t_position < r_position:
                skills = arg[:t_position]
                characters = arg[t_position+1:r_position]
                rounds = arg[r_position+1][0]
            # -r が手前に存在する時
            else:
                skills = arg[:r_position]
                characters = arg[t_position+1:]
                rounds = arg[r_position+1][0]
        # -t のみが存在する時
        elif t_position:
            skills = arg[:t_position]
            characters = arg[t_position+1:]
        # -r のみが存在する時
        elif r_position:
            skills = arg[:r_position]
            rounds = arg[r_position+1][0]
            characters.append(self.current_character)
        # 技能だけの時
        else:
            skills = arg
            characters.append(self.current_character)

        # nick -> chara を関数化した
        characters = self.nick2chara(characters)

        # 外側のループをキャラクタ。
        # 内側のループを技能でやる
        for char in characters:
            for skill in skills:

                # db に追加する処理をする。同じ名前の技能があれば効果ラウンドを上書きする。
                # 抵抗短縮の場合、効果ラウンドが変動するから、1つの技能につき引数を2つ取る
                # この場合、技能名 ラウンド数 としておけば、まだ処理のしようがある。
                # 技能名に対してLIKE検索を行う
                conn = sqlite3.connect(
                    f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
                c = conn.cursor()
                # INSERT する前に技能の検索を行う
                c.execute(
                    'SELECT name FROM skill_list WHERE name LIKE ?', (f'%{skill}%',))
                # fetchall するとタプルのリストで返ってくる
                skill_names = c.fetchall()
                if len(skill_names) > 1:
                    # 検索して複数見つかった場合の処理
                    for i, skill_name in enumerate(skill_names):
                        print(i, skill_name[0])
                    else:
                        try:
                            index = int(input('追加したい技能の番号を入力してください:'))
                            skill_name = skill_names[index][0]
                        except:
                            print('有効な数字を入力してください')
                            return
                elif len(skill_names) == 1:
                    skill_name = skill_names[0][0]
                else:
                    print('技能が存在しません。')
                    return

                # 技能の効果をばらしている
                c.execute(
                    'SELECT effect FROM skill_list WHERE name = ?', (skill_name,))
                # effects = c.fetchone()[0].split(';')
                effects = c.fetchone()[0]

                # choice フラグを見る
                c.execute(
                    'SELECT choice FROM skill_list WHERE name = ?', (skill_name,))
                choice_flag = c.fetchone()[0]
                # print(type(choice_flag[0]))
                if choice_flag:
                    for i, effect in enumerate(effects):
                        print(i, effect)
                    try:
                        index = int(input('追加したい効果の番号を入力してください:'))
                        effects = [effects[index]]
                    except:
                        print('有効な数字を入力してください')
                        return

                # 挿入部分
                # -> ('【エンチャント・ウェポン】',), ('【スペル・エンハンス】',)
                # ここのLIKE句消せるから消す(消した)
                # status_list にアクセスして、技能が存在しているかを確かめる
                # 存在していなかったら、INSERT句を実行する
                # 存在しているときは、UPDATE句を実行する
                # CASE のところをPyでかく。SQLでどうやるかわかんないので

                # 同名技能がすでに存在していたら残りラウンド数を上書きする
                # -r が与えられていたら、それをそのまま使う。
                if r_position is None:
                    c.execute(
                        'SELECT round FROM skill_list WHERE name = ?', (skill_name,))
                    rounds = c.fetchone()[0]
                c.execute('SELECT COUNT(*) FROM status_list WHERE chara_name = ? AND skill_name = ?;',
                          (char, skill_name))
                cnt = c.fetchone()[0]

                # もしウォーリーダー技能だったら、1つしか存在できないから、必ず上書きする
                c.execute(
                    'SELECT type FROM skill_list WHERE name = ?', (skill_name,))
                type_ = c.fetchone()[0]
                if type_ == 'WOR':
                    c.execute(
                        'SELECT COUNT(type = "WOR") FROM status_list WHERE chara_name = ? ', (char,))
                    cnt_wor = c.fetchone()[0]
                    if cnt_wor > 1:
                        c.execute(
                            'DELETE FROM status_list WHERE type = "WOR" and chara_name = ?', (char,))
                        print('鼓砲は1つしか存在できないため既にある鼓砲を削除しました')
                    for effect in effects:
                        c.execute('''
                        INSERT INTO status_list (
                            chara_name, skill_name, skill_effect, round, type, use_start, use_end, count, choice
                        )
                        SELECT ?, name, ?, ?, type, use_start, use_end, count, choice
                        FROM skill_list
                        WHERE name = ?
                        ''', (char, effect, rounds, skill_name))
                        conn.commit()
                    print(f'{char} に {skill_name} を付与しました')
                else:
                    if cnt >= 1:
                        c.execute('UPDATE status_list SET round = ? WHERE chara_name = ? AND skill_name = ?',
                                  (rounds, char, skill_name))
                        print(f'{skill_name}はすでに存在しているため上書きしました')
                    else:
                        # そうでなければ新しく挿入する
                        for effect in effects:
                            c.execute('''
                            INSERT INTO status_list (
                                chara_name, skill_name, skill_effect, round, type, use_start, use_end, count, choice
                            )
                            SELECT ?, name, ?, ?, type, use_start, use_end, count, choice
                            FROM skill_list
                            WHERE name = ?
                            ''', (char, effect, rounds, skill_name))
                            conn.commit()
                        print(f'{char} に {skill_name} を付与しました')

    def do_rm(self, inp):
        ('rm <skills> [-t <characters>\n'
         '  対象の技能を削除するコマンド\n'
         'オプション\n'
         '  -t\n'
         '    技能を削除する対象を選択します。他のコマンドと同様に、キャラクタ名やラベ\n'
         '    ルを列挙することで、複数対象の技能を削することができます。 ')

        arg = inp.split()

        skills = arg
        characters = [self.current_character]
        # -t が存在するか
        if '-t' in arg:
            characters = arg[arg.index('-t')+1:]
            skills = arg[:arg.index('-t')]
        elif self.current_character == '':
            print('対象にするキャラクタを設定してください')
            return

        if len(characters) == 0:
            print('-t の後ろにはキャラクタを1体以上指定してください')
            return

        if len(arg) == 0:
            print('rm は引数を1つ以上取ります。 help rm')
            return

        characters = self.nick2chara(characters)
        if len(characters) == 0:
            return

        conn = sqlite3.connect(f'{self.current_directory}/db/data.db')
        c = conn.cursor()
        for chara in characters:
            for item in skills:
                # skill_list の skill_name をLIKE検索する
                # 同名で複数効果を持っているものがあるから、それに対応する(ヘイストなど)
                # 効果単位ではなく技能単位で消去したい
                c.execute('SELECT skill_name FROM status_list WHERE chara_name = ? AND skill_name LIKE ?',
                          (chara, f'%{item}%'))
                # fetchall するとタプルのリストで返ってくる
                # 技能の重複を削除
                skill = c.fetchall()
                # 見つからなかったら飛ばす
                if len(skill) == 0:
                    print(f'{item} に一致する技能は存在しませんでした')
                    continue

                # 一致した技能全部が入ってる
                skill_names = list(set([item[0] for item in skill]))

                # 複数あったらfor文回す
                if len(skill_names) == 1:
                    skill_name = skill_names[0]
                else:
                    for i, skill_name in enumerate(skill_names):
                        print(i, skill_name)
                    try:
                        index = int(input('追加したい効果の番号を入力してください:'))
                        skill_name = skill_names[index]
                    except:
                        print('有効な数字を入力してください')
                        return
                c.execute('DELETE FROM status_list WHERE chara_name = ? AND skill_name = ?',
                          (chara, skill_name))
                print(f'{skill_name}を削除しました')
                conn.commit()
        conn.close()

    def do_reset(self, inp):
        ('reset\n'
         '  先頭を終了を表すコマンド。ラウンド経過で消滅する技能を消去します')
        arg = inp.split()
        if len(arg) != 0:
            print('reset は引数を取りません')
            return
        conn = sqlite3.connect(
            f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute('DELETE FROM status_list WHERE round > 0')
        conn.commit()
        print('戦闘終了')

    def do_neko(self, inp):
        ('neko\n'
         '  にゃーんと返すコマンド。にゃーんがあると可愛いので')
        l = inp.split()
        if len(l) == 0:
            print('にゃーん')
        else:
            print('neko は引数なしだよ')

    def do_helps(self, inp):
        ('helps\n'
         '  コマンド一覧と簡単な説明を表示するコマンド')
        print('詳しいことは https://github.com/t4t5u0/swat/wiki を確認してください')
        print(f"{'─'*100}")
        print(f"{'name':^10}| {'explanation':^40}| {'arguments':^50}")
        print(f"{'─'*100}")
        print(f"{'append':<10}| キャラクタを追加{' '*(40-get_east_asian_count('キャラクタを追加'))}| キャラクタ1 キャラクタ2 キャラクタ3 ...{' '*(50-get_east_asian_count('キャラクタ1 キャラクタ2 キャラクタ3 ...'))}")
        print(f"{'change':<10}| 状態を変更したいキャラクタを変更{' '*(40-get_east_asian_count('状態を変更したいキャラクタを変更'))}| キャラクタ/キャラクタID{' '*(50-get_east_asian_count('キャラクタ/キャラクタID'))}")
        print(f"{'ls':<10}| キャラクタ一覧を表示{' '*(40-get_east_asian_count('キャラクタ一覧を表示'))}| 引数なし{' '*(50-get_east_asian_count('引数なし'))}")
        print(f"{'kill':<10}| キャラクタを消去{' '*(40-get_east_asian_count('キャラクタを消去'))}| キャラクタ/キャラクタID{' '*(50-get_east_asian_count('キャラクタ/キャラクタID'))}")
        print(f"{'add':<10}| 技能・呪文などを付与{' '*(40-get_east_asian_count('技能・呪文などを付与'))}| 技能・呪文など 効果ラウンド上書き(オプショナル){' '*(50-get_east_asian_count('技能・呪文など 効果ラウンド上書き(オプショナル)'))}")
        print(f"{'remove':<10}| 技能・呪文などを消去{' '*(40-get_east_asian_count('技能・呪文などを消去'))}| 技能・呪文など/状態ID{' '*(50-get_east_asian_count('技能・呪文など/状態ID'))}")
        print(f"{'check':<10}| 技能・呪文などの一覧を表示{' '*(40-get_east_asian_count('技能・呪文などの一覧を表示'))}| 引数なし/キャラクタ/キャラクタID{' '*(50-get_east_asian_count('引数なし/キャラクタ/キャラクタID'))}")
        print(f"{'start':<10}| 手番を開始{' '*(40-get_east_asian_count('手番を開始'))}| 引数なし{' '*(50-get_east_asian_count('引数なし/キャラクタ/キャラクタID'))}")
        print(f"{'end':<10}| 手番を終了{' '*(40-get_east_asian_count('手番を終了'))}| 引数なし{' '*(50-get_east_asian_count('引数なし/キャラクタ/キャラクタID'))}")
        print(f"{'newskill':<10}| 新しい技能を追加{' '*(40-get_east_asian_count('新しい技能を追加'))}| 引数なし{' '*(50-get_east_asian_count('引数なし'))}")
        print(f"{'neko':<10}| にゃーん{' '*(40-get_east_asian_count('にゃーん'))}| 引数なし{' '*(50-get_east_asian_count('引数なし'))}")
        print(f"{'help':<10}| コマンドの詳細を見る{' '*(40-get_east_asian_count('コマンドの詳細を見る'))}| コマンド名{' '*(50-get_east_asian_count('コマンド名'))}")
        print(f"{'helps':<10}| このコマンド{' '*(40-get_east_asian_count('このコマンド'))}| 引数なし{' '*(50-get_east_asian_count('引数なし'))}")
        print(f"{'exit':<10}| アプリケーションを終了させる{' '*(40-get_east_asian_count('アプリケーションを終了させる'))}| 引数なし{' '*(50-get_east_asian_count('引数なし'))}")
        print(f"{'─'*100}")

    def do_exit(self, inp):
        ('exit\n'
         '  プリケーションを終了するコマンド。Yを押すと終了します')
        arg = inp.split()
        if len(arg) == 0:
            x = input('終了しますか？ [Y/n] ')
            if x in ['y', 'Y']:
                sys.exit()
            elif x in ['n', 'N']:
                pass
            else:
                print('中断しました')
        else:
            print('引数が多すぎます。exit は引数を取りません。')

    def do_newskill(self, inp):
        ('newskill\n'
         '  新技能をコマンドラインから追加するコマンド。結果はuser.jsonに吐き出されます\n'
         'name    : 技能名です。重複は許可されていません。\n'
         'effects : 技能の効果です。1つの効果は1行に書いてください。空行を入力すると次の項目に移動します\n'
         'round   : 技能が継続するラウンドです。負整数を入力すると永続となります\n'
         'type    : 技能の種類です。空白でも構いません\n'
         'start   : 手番開始時に処理をするフラグです。デフォルトでは False が渡されています。変更したいときは、True または \n'
         '          true を入力してください。変更する必要がないときは、そのまま空行で構いません\n'
         'end     : 手番終了時に処理をするフラグです。デフォルトでは False が渡されています。変更したいときは、True または \n'
         '          true を入力してください。変更する必要がないときは、そのまま空行で構いません\n'
         'choice  : 技能の効果が複数ある場合にその中から1つを選択するか決定するフラグです。デフォルトでは False が渡されて\n'
         '          います。変更したいときは、True または true を入力してください。変更する必要がないときは、そのまま空行\n'
         '          で構いません\n'
         )
        arg = inp.split()

        conn = sqlite3.connect(
            f'{self.current_directory}/db/data.db', detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()

        if len(arg) != 0:
            print('newskill は引数なしです')
            return
        skill = {'name': '', 'effects': [], 'type': '', 'round': '',
                 'start': False, 'end': False, 'count': False, 'choice': False}
        # 入力を受け取るところ
        for key, value in skill.items():
            tmp = input(f'{key:8}: ')
            if tmp == 'q':
                return
            elif key == 'name':
                if tmp == '':
                    print('技能名を入力してください')
                    return
                c.execute(
                    'SELECT COUNT(name) FROM skill_list WHERE name = ?', (tmp,))
                if c.fetchone()[0] == 0:
                    skill['name'] = tmp
                else:
                    print(f'{tmp}という技能はすでに存在しています')
                    return
            elif key == 'effects':
                while tmp != '':
                    skill['effects'].append(tmp)
                    tmp = input(f'{"effects":8}: ')
                if len(skill['effects']) == 0:
                    print('効果を1つ以上入力してください')
                    return
            elif key == 'type':
                skill['type'] = tmp
            elif key == 'round':
                try:
                    tmp = int(tmp)
                except ValueError:
                    print('整数を入力してください')
                    return
                skill['round'] = tmp
            elif key in ['start', 'end', 'choice', 'count']:
                if key == 'count':
                    skill['count'] = False
                    continue
                if tmp == '':
                    pass
                elif tmp in ['True', 'true']:
                    skill[f'{key}'] = True
                elif tmp in ['False', 'false']:
                    pass
                else:
                    print('不正な入力です')
                    return

        ls = None
        with open(self.current_directory/'json_data'/'user.json', 'r+') as f:
            ls = f.readlines()
            # print(len(ls))
            if ls == []:
                ls.append('[\n')
            if ls[-1] == ']':
                ls[-1] = ','
            # print(f'{ls=}')
            ls.insert(len(ls), f'{json.dumps(skill, ensure_ascii=False)}')
            ls.insert(len(ls), '\n]')

        with open(self.current_directory/'json_data'/'user.json', 'w') as f:
            f.writelines(ls)

        skill['effect'] = ';'.join(skill['effects'])
        c.execute('INSERT INTO skill_list(name, effect, type, round, use_start, use_end, count, choice) VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                  (skill['name'], skill['effect'], skill['type'], skill['round'], skill['start'], skill['end'], skill['count'], skill['choice']))
        conn.commit()
        c.close()

    def help_help(self):
        print('help [cmd]\n'
              '  他のコマンドのhelpを確認するためのコマンド')

    def emptyline(self):
        pass

    # alias
    do_ad = do_add
    do_ch = do_change
    do_ap = do_append
    do_ck = do_check
    dp_ns = do_newskill
