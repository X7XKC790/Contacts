import os
import re
import requests as req
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# 手動設置 TCL_LIBRARY 和 TK_LIBRARY
os.environ['TCL_LIBRARY'] = r'C:\Program Files\Python313\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Program Files\Python313\tcl\tk8.6'

def fetch_data():
    url = url_entry.get()
    try:
        res = req.get(url)
        res.raise_for_status()  # 檢查是否有HTTP錯誤
    except req.exceptions.RequestException as e:
        messagebox.showerror("錯誤", f"無法抓取資料: {e}")
        return

    with open('contacts.html', 'w', encoding='utf-8') as f:
        f.write(res.text)

    with open('contacts.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 定義正規表示式來匹配姓名、職稱及信箱
    name_pattern = re.compile(r'<div class="member_name"><a href="[^"]+">([^<]+)</a>')
    title_pattern = re.compile(r'<div class="member_info_title"><i class="fas fa-briefcase"></i>職稱</div>\s*<div class="member_info_content">([^<]+)</div>')
    email_pattern = re.compile(r'<div class="member_info_title"><i class="fas fa-envelope"></i>信箱</div>\s*<div class="member_info_content"><a href="mailto:([^"]+)">')

    # 使用正規表示式來查找所有匹配項
    names = name_pattern.findall(html)
    titles = title_pattern.findall(html)
    emails = email_pattern.findall(html)

    # 將資料插入到SQLite資料庫，排除重複記錄
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS contacts')
    cursor.execute(
        '''CREATE TABLE contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            email TEXT NOT NULL,
            UNIQUE(name, title, email)
        )'''
    )

    for name, title, email in zip(names, titles, emails):
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO contacts (name, title, email) VALUES (?, ?, ?)',
                (name.strip(), title.strip(), email.strip())
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()

    # 從資料庫中讀取資料
    cursor.execute('SELECT name, title, email FROM contacts')
    contacts = cursor.fetchall()
    conn.close()

    # 清空Treeview
    for item in tree.get_children():
        tree.delete(item)

    # 插入資料到Treeview
    for contact in contacts:
        tree.insert('', tk.END, values=contact)

# 建立Tkinter界面
root = tk.Tk()
root.title("聯絡資訊")
root.geometry("640x480")

# 設置URL輸入框和按鈕
url_frame = tk.Frame(root)
url_frame.pack(fill=tk.X, padx=10, pady=5)

url_label = tk.Label(url_frame, text="URL:")
url_label.pack(side=tk.LEFT)

url_entry = tk.Entry(url_frame, width=50)
url_entry.insert(0, 'https://csie.ncut.edu.tw/content.php?key=86OP82WJQO')
url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

fetch_button = tk.Button(url_frame, text="抓取", command=fetch_data)
fetch_button.pack(side=tk.LEFT)

# 設置Treeview
tree_frame = tk.Frame(root)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tree = ttk.Treeview(tree_frame, columns=('name', 'title', 'email'), show='headings')
tree.heading('name', text='姓名')
tree.heading('title', text='職稱')
tree.heading('email', text='信箱')

# 設置列的寬度
tree.column('name', width=150, anchor='center')
tree.column('title', width=250, anchor='center')
tree.column('email', width=250, anchor='center')

tree.pack(fill=tk.BOTH, expand=True)

# 啟動主循環
root.mainloop()
