import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import json
import os

# ページの設定
# st.set_page_config(page_title="Book Reader", layout="wide")
st.set_page_config(page_title="Book Reader")
# アプリのタイトル
st.title("Book Reader")
# メモの保存先
memo_file = "memos.json"

# メモを読み込む関数
def load_memos():
    if os.path.exists(memo_file):
        with open(memo_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# メモを保存する関数
def save_memos(memos):
    with open(memo_file, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=4)

# PDFファイルのアップロード
uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type=["pdf"], key="unique_file_uploader")

# メモを読み込む
memos = load_memos()

if uploaded_file is not None:
    pdf_document = fitz.open(stream=uploaded_file.read())
    total_pages = pdf_document.page_count

    # 現在のページ番号をセッション状態に保存またはJSONファイルから取得
    if uploaded_file.name not in memos:
        st.session_state.page_number = 1  # 表紙のために初期ページを1に設定
        memos[uploaded_file.name] = {
            "current_page": st.session_state.page_number,
            "memo": [],
            "reading_direction": st.session_state.get('reading_direction', 'left_to_right')  # デフォルト値を設定
        }  # 新規ファイルの場合、空のリストを追加
    else:
        st.session_state.page_number = memos[uploaded_file.name].get('current_page', 1)
        st.session_state.reading_direction = memos[uploaded_file.name].get('reading_direction', 'left_to_right')  # ページ送り方向を取得

    # ページ表示
    def display_pages():
        current_page = int(st.session_state.page_number)
        pages_to_display = []

        # 表紙の表示
        if current_page == 1:
            page = pdf_document.load_page(0)  # 表紙のページ
            pix = page.get_pixmap(dpi=300)  # DPIを300に設定
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages_to_display.append(img)

            # 黒塗りの2ページ目を追加
            black_page = Image.new("RGB", img.size, (0, 0, 0))  # 黒塗りのページを作成
            pages_to_display.append(black_page)

        else:
            # 読み方向に応じてページインデックスを変更
            if st.session_state.reading_direction == 'left_to_right':
                for i in range(2):  # 左読みのとき
                    page_index = current_page - 1 + i
                    if page_index < total_pages:
                        page = pdf_document.load_page(page_index)
                        pix = page.get_pixmap(dpi=300)  # DPIを300に設定
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        pages_to_display.append(img)
            else:
                for i in range(2):  # 右読みのとき
                    page_index = current_page - 1 - i
                    if page_index >= 0:
                        page = pdf_document.load_page(page_index)
                        pix = page.get_pixmap(dpi=300)  # DPIを300に設定
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        pages_to_display.append(img)
                pages_to_display.reverse()  # 右読みのときは順番を反転する

        return pages_to_display

    # ページ番号を変更する
    def update_page_number(new_value):
        st.session_state.page_number = new_value
        memos[uploaded_file.name]['current_page'] = new_value  # 現在のページをメモに保存
        save_memos(memos)  # メモを保存

    # PDFを表示するプレースホルダーを一度だけ作成
    pdf_placeholder = st.empty()  # PDF表示用のプレースホルダー

    # ページの画像を表示する関数
    def show_images():
        images = display_pages()  # 現在のページの画像を取得
        
        # PDFプレースホルダーに画像を表示
        if images:
            if len(images) == 1:  # 表紙のみの場合
                pdf_placeholder.image(images[0], use_column_width=True)
            else:
                cols = pdf_placeholder.columns(2)  # 2列を作成
                if st.session_state.reading_direction == 'left_to_right':
                    cols[0].image(images[0], use_column_width=True)  # 左側に1ページ目
                    if len(images) > 1:
                        cols[1].image(images[1], use_column_width=True)  # 右側に2ページ目
                else:
                    cols[1].image(images[0], use_column_width=True)  # 右側に1ページ目
                    if len(images) > 1:
                        cols[0].image(images[1], use_column_width=True)  # 左側に2ページ目


    # スライダーの変更時に画像を更新
    def slider_update():
        update_page_number(st.session_state.page_slider)  # ページ番号を更新
        show_images()  # 画像を表示
        
    # ページ画像の表示エリアと左右のボタンを配置
    cols = st.columns([1.5, 1, 8, 1, 3])  # ボタン, 画像, ボタンのための列配置

    # 表紙表示ボタン
    with cols[0]:
        if st.button("表紙"):
            update_page_number(1)  # 表紙に戻る
            show_images()  # 画像を更新

    # ◀️ ボタン
    with cols[1]:
        if st.button("◀️"):
            if st.session_state.reading_direction == 'left_to_right':
                if int(st.session_state.page_number) > 3:
                    new_page = int(st.session_state.page_number) - 2
                    update_page_number(new_page)  # ページ番号を更新
                    show_images()  # 画像を更新
            else:
                if int(st.session_state.page_number) < total_pages:
                    new_page = int(st.session_state.page_number) + 2
                    update_page_number(new_page)  # ページ番号を更新
                    show_images()  # 画像を更新

    # ▶️ ボタン
    with cols[3]:
        if st.button("▶️"):
            if st.session_state.reading_direction == 'left_to_right':
                if int(st.session_state.page_number) + 1 < total_pages:
                    new_page = int(st.session_state.page_number) + 2
                    update_page_number(new_page)  # ページ番号を更新
                    show_images()  # 画像を更新
            else:
                if int(st.session_state.page_number) > 2:
                    new_page = int(st.session_state.page_number) - 2
                    update_page_number(new_page)  # ページ番号を更新
                    show_images()  # 画像を更新

    # 読み方向切り替えボタン
    with cols[4]:
        if st.button("送り方向切替"):
            st.session_state.reading_direction = 'right_to_left' if st.session_state.reading_direction == 'left_to_right' else 'left_to_right'
            memos[uploaded_file.name]["reading_direction"] = st.session_state.reading_direction  # 新しい方向を保存
            save_memos(memos)  # 設定を保存
            show_images()  # 画像を更新


    # メモの題名と内容を入力するトグル表示
    st.subheader("メモを追加")
    with st.expander("メモの入力", expanded=False):
        # もし未設定なら、デフォルト値を設定
        if 'memo_title' not in st.session_state:
            st.session_state.memo_title = ""
        if 'memo_content' not in st.session_state:
            st.session_state.memo_content = ""

        memo_title = st.text_input("題名を入力してください", value=st.session_state.memo_title)
        memo_content = st.text_area("内容を入力してください", value=st.session_state.memo_content)

        if st.button("メモを保存"):
            if memo_title and memo_content:
                new_memo = {"page": st.session_state.page_number, "title": memo_title, "content": memo_content}

                # メモを保存する準備
                if uploaded_file.name not in memos:
                    memos[uploaded_file.name] = {"current_page": st.session_state.page_number, "memo": [new_memo]}  # 新規ファイルの場合は新しいメモを追加
                else:
                    if "memo" not in memos[uploaded_file.name]:
                        memos[uploaded_file.name]["memo"] = []  # メモがない場合はリストを初期化
                    memos[uploaded_file.name]["memo"].append(new_memo)  # メモを追加

                save_memos(memos)  # メモをファイルに保存

                # 入力フィールドをクリア
                st.session_state.memo_title = ""
                st.session_state.memo_content = ""
                st.success("メモを保存しました。", icon="✅")


    # 保存されたメモを表示
    st.subheader("保存されたメモ")
    if uploaded_file.name in memos and "memo" in memos[uploaded_file.name]:
        memo_list = memos[uploaded_file.name]["memo"]  # メモのリストを取得
        if memo_list:  # メモが存在する場合
            with st.expander("メモの表示", expanded=False):
                for idx, memo in enumerate(memo_list):

                    with st.container():
                        st.write(f"**p. {memo['page']}**")

                        # メモの題名と内容の編集フィールド
                        new_title = st.text_input(f"題名", memo['title'], key=f"edit_title_{idx}")
                        new_content = st.text_area(f"内容", memo['content'], key=f"edit_content_{idx}")

                        col_memo_btn = st.columns([1.2,1,2.8])  # ボタン配置用のカラム

                        # メモのページにジャンプするボタン
                        with col_memo_btn[0]:
                            if st.button(f"p. {memo['page']} へジャンプ", key=f"jump_to_{memo['page']}_{memo['title']}"):                
                                update_page_number(memo['page'])  # メモのページ番号に更新
                                show_images()  # ページを更新して表示

                        # メモを削除するボタン
                        with col_memo_btn[1]:
                            if st.button(f"メモを削除", key=f"delete_{memo['title']}"):
                                memo_list.remove(memo)  # メモを削除
                                save_memos(memos)  # メモをファイルに保存
                                st.rerun()  # ページを再読み込みして更新

                        # メモの更新を保存するボタン
                        with col_memo_btn[2]:
                            if st.button(f"メモを置換", key=f"save_{memo['page']}_{memo['title']}"):
                                # メモの題名や内容が変更されたら保存
                                memo['title'] = new_title
                                memo['content'] = new_content
                                save_memos(memos)  # メモをファイルに保存
                                st.success(f"メモが更新されました (p. {memo['page']}_{memo['title']})")

        else:
            st.info("保存されたメモはありません。")  # メモがない場合のメッセージ

    
    # スライダー切替        
    with cols[2]:
        show_images()

        slider_value = st.slider(
            label="ページ選択",
            label_visibility="collapsed", # ラベル非表示(hiddenより強力)
            min_value=1,  # 表紙を含める
            max_value=total_pages,
            value=int(st.session_state.page_number),  # セッションから現在のページ番号を取得
            step=2,
            key="page_slider",
            on_change=slider_update  # スライダー変更時の処理
        )