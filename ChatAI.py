# このスクリプトは、ユーザーとチャットボットとの対話を行う。
# 設定ファイルから設定を読み込み、OpenAI APIキーを設定し、
# 全会話履歴を読み込む。ユーザーが入力を行い、特定のコマンド
# が入力されると会話履歴の操作が行われる。
# 空行が2回連続で入力されると、ユーザー入力に対してAPIが応答する。
#
# Seiichirou Hiraoka <seiichirou.hiraoka@gmail.com>
#   with Github Copilot and Amazon Code Whisper

# モジュールをインポートする
import os
import openai
import json
from datetime import datetime
import sys

# 変数をグローバル変数に設定する
global openai, historyfile, model, assistant, user, charactor, motd, debug

# 設定を読み込む
def load_config():
    # 変数をグローバル変数に設定する
    global openai, historyfile, model, assistant, user, charactor, motd, debug
    
    # 設定ファイルを読み込む
    with open("config.ini", "r") as f:
        config = {}
        for line in f:
            # コメント行は読み飛ばす
            if line.startswith("#"):
                continue
            key, value = line.split("=")
            # 設定ファイルの値は文字列なので、数値に変換する
            config[key.strip()] = value.strip()

        # 変数を設定する
        # OpenAI API Key(openai.api_key)
        openai.api_key = config["OPENAI_API_KEY"]
        # 会話履歴ファイル(historyfile)
        historyfile = config["HISTORYFILE"]
        # モデル名(model)
        model = config["MODEL"]
        # アシスタント名(assistant)
        assistant = config["ASSISTANT"]
        # ユーザ名(user)
        user = config["USER"]
        # 性格(charactor)
        charactor = config["CHARACTOR"]
        # 会話の開始の文章(motd)
        motd = config["MOTD"]
        # デバッグ(debug)
        debug = config["DEBUG"]

        # デバッグモードが有効な場合、config変数の中身を表示する
        if debug == True:
            for key, value in config.items():
                print(f"{key} = {value}")

# chat_response関数の説明
# user_inputは、ユーザーの入力
# historyは、会話履歴
# APIに会話を送信し、返事を受け取る
# 返事があれば、返事と使用したトークン数を返す
# 返事がなければ、エラーメッセージと0を返す
def chat_response(user_input, history):
    # messagesを定義する
    
    # 性格を定義する
    messages = [
        {"role": "system", "content": charactor},
    ]

    # 会話履歴のJSON形式を読み込んで、ユーザの入力とアシスタントの応答をmessagesに追加する
    # 会話履歴の形式は以下の通り。
    # [
    # {
    #    "user": "こんにちは",
    #    "assistant": "こんにちは！いかがお過ごしですか？何かお手伝いできることはありますか？",
    #    "emotion": "0.0"
    # }
    # ]
    for line in history:
        messages += [
            {"role": "user", "content": line["user"]},
            {"role": "assistant", "content": line["assistant"]},
        ]

    # ユーザの入力をmessagesに追加する
    messages += [
        {"role": "user", "content": user_input},
    ]
   
    # デバッグモードが有効な場合、messagesの中身を表示する
    if debug == True:
        print(f"<messages>\n{json.dumps(messages)}")

    # OpenAI APIに会話を送信し、応答を受け取る
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )

    # 応答があれば、応答と使用したトークン数を返す
    if response.choices:
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        return answer, tokens_used
    # 応答がなければ、エラーメッセージと0を返す
    else:
        return "ごめんなさい。その質問には答えられません。", 0

# 感情スコアを計算する
# -10（悪い）から+10（良い）までの範囲で評価する
# 評価出来ない場合は、0を返す
def get_emotion_score(user_input):
    # 初期の性格をプロンプトで指定します。
    assistant_initial_prompt = "あなたは冷静沈着な心理学者です。"
    # ユーザの入力をプロンプトに追加します。
    prompt = f"以下のテキストの感情を-10（悪い）から+10（良い）までの範囲で評価してください: '{user_input}' 評価: "

    # OpenAI APIに会話を送信し、応答を受け取る
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": assistant_initial_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    # デバッグモードが有効な場合、応答を表示する
    if debug == True:
        print(f"<response>\n{json.dumps(response)}")

    # 応答があれば、応答を返す
    if response.choices:
        answer = response.choices[0].message.content
        return answer
    # 応答がなければ、0 を返す
        return 0

# 会話履歴を読み込む
def load_conversation_history():
    # 会話履歴ファイルはJSON形式で保存されている
    # 読み込んだ結果をhistory変数に格納して返す
    # 履歴ファイルが読み込めない場合は空のリストを返す

    # 会話履歴ファイル名の生成
    file_name = historyfile + ".json"

    # 会話履歴ファイルが存在するか確認する
    if os.path.exists(file_name):

        # 会話履歴ファイルを読み込む
        with open(file_name, "r", encoding="utf-8") as f:
            try:
                # 会話履歴ファイルをJSON形式で読み込む
                history = json.load(f)
                # 会話履歴ファイルが正しい形式の場合は、会話履歴を返す
                return history
            # 会話履歴ファイルが正しい形式ではない場合はエラーを表示する
            except json.decoder.JSONDecodeError as e:
                print(f"エラー: 会話履歴ファイルが正しい形式ではありません。({e})")
                print(f"会話履歴を読み込めませんでした。")
                return []

    # 会話履歴ファイルが存在しない場合はエラーを表示する
    else:
        print(f"エラー: 会話履歴ファイルが存在しません。({file_name})")
        print(f"会話履歴を読み込めませんでした。")
        return []

# JSON形式の会話履歴を表示する
def show_history(history):
    # historyが定義されていなければ終了する
    if not history:
        print("会話履歴がありません。")
        return

    # JSON形式の会話履歴historyを全て表示する
    print (json.dumps(history, indent=4, ensure_ascii=False))

# 会話履歴をJSON形式で保存する
def save_conversation_history(history):
    # historyが定義されていなければ終了する
    if not history:
        print("会話履歴がありません。")
        return

    # デバッグモードが設定されていればhistoryの内容を表示する
    if debug == True:
        show_history(history)

    # 会話履歴をJSON形式で保存する
    # 例: conversation_history.json

    # 会話履歴ファイル名の生成
    file_name = historyfile + ".json"

    # ファイルを開く
    with open(file_name, "w", encoding="utf-8", errors="ignore") as f:
        # JSON形式で保存する
        json.dump(history, f, ensure_ascii=False, indent=4)

    print(f"会話履歴を保存しました。")

# 会話履歴をタイムスタンプ付きで保存する
def save_conversation_history_timestamp(history):
    # historyが定義されていなければ終了する
    if not history:
        print("会話履歴がありません。")
        return

    # デバッグモードが設定されていればhistoryの内容を表示する
    if debug == True:
        show_history(history)
    
    # 会話履歴をJSON形式で保存する
    # ファイル名は、会話履歴ファイル名_YYYYMMDD-hhmmddの日付で保存する
    # 例: conversation_history_20210701-111111.txt
    
    # 会話履歴ファイル名（タイムスタンプ付き）の生成
    file_name = historyfile + f"_{datetime.now():%Y%m%d-%H%M%S}.json"

    # ファイルを開く
    with open(file_name, "w", encoding="utf-8", errors="ignore") as f:
        # JSON形式で保存する
        json.dump(history, f, ensure_ascii=False, indent=4)

    print(f"会話履歴をタイムスタンプ付きで保存しました。")

# コマンドを処理する
def handle_command(command, history):
    # #END# 会話履歴を保存して終了する
    if command == "#END#":
        save_conversation_history(history)
        print("会話を終了します。")

        # プログラムを中断する
        sys.exit(0)

    # #CLEAR_HISTORY# 現在の会話履歴をクリアする
    elif command == "#CLEAR_HISTORY#":
        # 本当に会話履歴をクリアして良いか確認する
        while True:
            # y/nを入力させる
            user_input = input("会話履歴をクリアしますか？(y/n): ")
            if user_input.strip() == "y":
                # 会話履歴をクリアする場合は、処理を続行する
                break
            elif user_input.strip() == "n":
                # 会話履歴をクリアしない場合は、会話を継続する
                return history
            else:
                # y/n以外の入力がされた場合は、再度入力を促す
                print("yかnを入力してください。")

        # 会話履歴をクリアする前に、会話履歴をタイムスタンプ付きで保存する
        save_conversation_history(history)

        # 会話履歴をクリアする
        history.clear()
        print("会話履歴をクリアしました。")

        # 会話履歴をクリア後再び会話を継続する
        return history

    # #LOAD_HISTORY# 会話履歴ファイルを読み込む
    elif command == "#LOAD_HISTORY#":
        # 会話履歴をクリアする前に会話履歴をタイムスタンプ付きで保存する
        save_conversation_history_timestamp(history)

        history.clear()
        print("会話履歴をクリアしました。")

        load_conversation_history()
        print("会話履歴を読み込みました。")

        return history
    # #SAVE_HISTORY# 現在の会話履歴を保存する
    elif command == "#SAVE_HISTORY#":
        save_conversation_history(history)

        return history
    # #SHOW_HISTORY# 現在の会話履歴を表示する
    elif command == "#SHOW_HISTORY#":
        # JSON形式のhistory変数の内容をテキストで表示する
        print("<会話履歴>\n")
        print(json.dumps(history, indent=4, ensure_ascii=False))

        return history
    # #DEBUG# デバッグモードを変更する（トグル）
    elif command == "#DEBUG#":
        global debug
        
        debug = not debug
        if debug:
            print("デバッグモードを有効にしました。")
        else:
            print("デバッグモードを無効にしました。")

        return True
    # #HELP# コマンドの一覧を表示する
    elif command == "#HELP#":
        print("#END# 会話履歴を保存して終了する")
        print("#CLEAR_HISTORY# 現在の会話履歴をクリアする")
        print("#LOAD_HISTORY# 会話履歴ファイルを読み込む")
        print("#SAVE_HISTORY# 現在の会話履歴を保存する")
        print("#SHOW_HISTORY# 現在の会話履歴を表示する")
        print("#DEBUG# デバッグモードを変更する（トグル）")
        print("#HELP# コマンドの一覧を表示する")

        return True
    # その他の場合、コマンドが不正なのでFalseを返す
    else:
        print("コマンドが不正です。")
        return False

# 会話履歴要約関数を定義する
def summarize(history):
    # デバッグモードの場合は、history変数の内容を表示する
    if debug == True:
        print("<会話履歴>\n")
        print(json.dumps(history, indent=4, ensure_ascii=False))

    # 初期の性格をプロンプトで指定します。
    assistant_initial_prompt = "あなたは最高の編集者です。"
    # promptを定義する
    prompt = f"次の文章を要約してください: {history}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": assistant_initial_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # アシスタントからの応答を取得する
    summary = response.choices[0]['message']['content'].strip()
    return summary

# handle_conversation()関数を定義する
def handle_conversation(user_input, history):
    # historyが定義されていなければ、空のリストを設定する
    if history is None:
        history = []

    # アシスタントからの応答とトークン数を取得する
    response, token_used = chat_response(user_input, history)

    # ユーザ入力の感情スコアを取得する
    emotion_score = get_emotion_score(user_input)
    
    # デバッグモードが有効な場合、ユーザ入力の感情スコアを表示する
    if debug == True:
        print(f"感情スコア: {emotion_score}")

    # JSON形式の会話履歴の末尾にユーザの入力とアシスタントの応答と感情スコアを追加する
    history.append({"user": user_input, "assistant": response, "emotion": emotion_score})

    # トークン数が1000を超えた場合、会話履歴をタイムスタンプ付きで保存して、会話履歴を要約する
    if token_used > 1000:
        # 会話履歴をタイムスタンプ付きで保存する
        save_conversation_history_timestamp(history)

        # デバッグモードが有効な場合
        if debug == True:
            print(f"会話履歴を保存しました。{history}")

        # 会話履歴を要約する
        summarized_history = summarize_conversation_history(history)

        # デバッグモードが有効な場合
        if debug == True:
            print(f"会話履歴を要約しました。{summarized_history}")

        # 会話履歴を要約したものを、アシスタントの応答として設定する
        response = summarized_history

        # 会話履歴をクリアする
        history.clear()

        # 会話履歴をクリア後に、会話履歴に要約した会話履歴を追加する
        history.append({"user": user_input, "assistant": response, "emotion": emotion_score})

    # アシスタントからの応答と末尾にトークン数と感情スコアを表示する
    print(f"アシスタント: {response} ({token_used} tokens used) emotion: {emotion_score}")

    # summarized_historyが定義されている場合
    if "summarized_history" in locals():
        # 要約した会話履歴を返す
        return summarized_history
    else:
        # 要約した会話履歴が定義されていない場合は、会話履歴を返す
        return history

# 会話履歴(history)を以下の通り要約する
# historyを最新から逆順に読みこんでの全ての会話履歴を要約する
# 末尾の3件は要約せずとのまま履歴に追加する
# 末尾から4件から10件は2件ごとに要約する
# 11件以前は3件ごとに要約する
def summarize_conversation_history(history):
    # 会話履歴を要約する
    summarized_history = []
    for i in range(len(history) - 1, -1, -1):
        # 末尾の3件は要約せずそのまま履歴に追加する
        if i >= len(history) - 3:
            summarized_history.append(history[i])
        elif len(history) - 3 > i >= len(history) - 10:
            if i % 2 == 0:
                text_range = min(2, i + 1)
                concatenated_text = ' '.join([entry['user'] + ' ' + entry['assistant'] for entry in history[i - text_range + 1:i + 1]])
                summarized_text = summarize(concatenated_text)
                summarized_history.append({'user': history[i]['user'], 'assistant': summarized_text})
        elif len(history) - 10 > i >= 0:
            if i % 3 == 0:
                text_range = min(3, i + 1)
                concatenated_text = ' '.join([entry['user'] + ' ' + entry['assistant'] for entry in history[i - text_range + 1:i + 1]])
                summarized_text = summarize(concatenated_text)
                summarized_history.append({'user': history[i]['user'], 'assistant': summarized_text})

    # 逆順に読みこんでいたので、要約した会話履歴を最新の会話履歴から順に並べ替える
    summarized_history.reverse()

    return summarized_history

# メイン関数
def main():
    # 設定ファイルを読み込む
    load_config()

    # デバッグモードが有効な場合、読み込んだ変数を表示する
    if debug == True:
        print(f"性格(charactor): {charactor}")
        print(f"モデル名(model): {model}")
        print(f"ユーザー名(user): {user}")
        print(f"アシスタント名(assistant): {assistant}")
        print(f"MOTD(motd): {motd}")
        print(f"デバッグモード(debug): {debug}")

    # JSON形式の会話履歴を初期化する
    history = []
    # 会話履歴を読み込む
    history = load_conversation_history()

    # デバッグモードが有効な場合、読み込んだ内容を出力
    if debug == True:
        show_history(history)

    # 会話を開始する
    print(motd)

    # ループ処理を行う
    while True:
        # 入力内容を初期化する
        user_input_lines = []
        # 空行数を初期化する
        blank_line_count = 0
        # 空行数が2未満の間は入力を続ける
        while blank_line_count < 2:
            # ユーザの入力内容を取得する
            user_input = input("ユーザー: ")

            # user_inputが#で始まり#で終わる場合、コマンドとして実行する
            if user_input.startswith("#") and user_input.endswith("#"):
                # コマンドを実行する
                history = handle_command(user_input, history)

                continue
            # 入力内容が空行の場合は空行数を1増やす
            elif user_input.strip() == "":
                # 空行数を1増やす
                blank_line_count += 1
            # 入力内容が空行でない場合
            else:
                # 空行数を0に戻す
                blank_line_count = 0

                # 入力内容をuser_input_linesに追加する
                user_input_lines.append(user_input)

        # 空行が2行入力された場合、入力内容を改行で連結する
        user_input = "\n".join(user_input_lines)

        # user_inputが\nでない場合、会話処理を行う
        if user_input.strip() != "":
            # 会話処理を行う
            history = handle_conversation(user_input, history)

# メイン関数の呼び出し
if __name__ == "__main__":
    main()
