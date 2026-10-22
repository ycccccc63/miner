import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import random
import string
import time
import threading

class MiningSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blockchain 挖礦模擬器")
        self.root.geometry("850x700")
        self.root.resizable(True, True)

        # 挖礦狀態控制變數
        self.is_mining = False
        self.start_time = 0
        self.attempts = 0
        self.mining_thread = None

        # 建立 UI 元件
        self._setup_ui()

    def _setup_ui(self):
        # 設定整體內邊距
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----------------------------------------------------
        # 1. 頂部：目標設定區
        # ----------------------------------------------------
        target_frame = ttk.LabelFrame(main_frame, text="設定區", padding="10")
        target_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(target_frame, text="設定目標：").pack(side=tk.LEFT, padx=(0, 5))
        
        self.target_var = tk.StringVar(value="000001111101010101010000010101")
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_var, font=("Consolas", 10))
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.target_entry.bind("<KeyRelease>", self._update_target_length)

        self.target_len_label = ttk.Label(target_frame, text="(30 位數)")
        self.target_len_label.pack(side=tk.LEFT)

        # ----------------------------------------------------
        # 2. 中間：控制面板與 Hash 計算實時表格
        # ----------------------------------------------------
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 2.1 左側控制區
        ctrl_frame = ttk.LabelFrame(middle_frame, text="控制", padding="10")
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.btn_start = ttk.Button(ctrl_frame, text="開始挖礦", command=self.start_mining)
        self.btn_start.pack(fill=tk.X, pady=(5, 5))

        self.btn_stop = ttk.Button(ctrl_frame, text="停止", command=self.stop_mining, state=tk.DISABLED)
        self.btn_stop.pack(fill=tk.X, pady=(5, 5))

        self.btn_clear = ttk.Button(ctrl_frame, text="清除", command=self.clear_fields)
        self.btn_clear.pack(fill=tk.X, pady=(5, 15))

        # 統計資訊標籤
        self.lbl_attempts = ttk.Label(ctrl_frame, text="已嘗試 0 次", font=("Microsoft JhengHei", 9))
        self.lbl_attempts.pack(anchor=tk.W, pady=2)

        self.lbl_elapsed = ttk.Label(ctrl_frame, text="耗時 0.00 秒", font=("Microsoft JhengHei", 9))
        self.lbl_elapsed.pack(anchor=tk.W, pady=2)

        self.lbl_hashrate = ttk.Label(ctrl_frame, text="速率 0 hash/s", font=("Microsoft JhengHei", 9))
        self.lbl_hashrate.pack(anchor=tk.W, pady=2)

        # 2.2 右側列表區 (Input / Hash 流動顯示)
        table_frame = ttk.LabelFrame(middle_frame, text="挖礦日誌流", padding="5")
        table_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        columns = ("input", "binary_hash")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree.heading("input", text="Input")
        self.tree.heading("binary_hash", text="Binary Hash Value")
        self.tree.column("input", width=120, anchor=tk.W)
        self.tree.column("binary_hash", width=420, anchor=tk.W)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_status = ttk.Label(table_frame, text="(待命狀態)", font=("Microsoft JhengHei", 10, "bold"), foreground="gray")
        self.lbl_status.pack(side=tk.BOTTOM, pady=5)

        # ----------------------------------------------------
        # 3. 底部：命中目標結果顯示區
        # ----------------------------------------------------
        hit_frame = ttk.LabelFrame(main_frame, text="命中目標 (結果)", padding="10")
        hit_frame.pack(fill=tk.X)

        # 共測試組資料
        f1 = ttk.Frame(hit_frame)
        f1.pack(fill=tk.X, pady=2)
        ttk.Label(f1, text="共測試：", width=12, anchor=tk.E).pack(side=tk.LEFT)
        self.res_attempts_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.res_attempts_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(f1, text=" 組資料").pack(side=tk.LEFT, padx=(5, 0))

        # 共花費秒數
        f2 = ttk.Frame(hit_frame)
        f2.pack(fill=tk.X, pady=2)
        ttk.Label(f2, text="共花費：", width=12, anchor=tk.E).pack(side=tk.LEFT)
        self.res_time_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self.res_time_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(f2, text=" 秒").pack(side=tk.LEFT, padx=(5, 0))

        # 命中的 input 為
        f3 = ttk.Frame(hit_frame)
        f3.pack(fill=tk.X, pady=2)
        ttk.Label(f3, text="命中的 input 為：", width=12, anchor=tk.E).pack(side=tk.LEFT)
        self.res_input_var = tk.StringVar()
        ttk.Entry(f3, textvariable=self.res_input_var, state="readonly", font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 其 Hash Value
        f4 = ttk.Frame(hit_frame)
        f4.pack(fill=tk.X, pady=2)
        ttk.Label(f4, text="其 Hash Value：", width=12, anchor=tk.E).pack(side=tk.LEFT)
        self.res_hash_var = tk.StringVar()
        ttk.Entry(f4, textvariable=self.res_hash_var, state="readonly", font=("Consolas", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._update_target_length()

    def _update_target_length(self, event=None):
        length = len(self.target_var.get().strip())
        self.target_len_label.config(text=f"({length} 位數)")

    def start_mining(self):
        target = self.target_var.get().strip()
        if not target or not all(c in '01' for c in target):
            messagebox.showerror("錯誤", "請輸入有效的二進位目標字串（只包含 0 與 1）！")
            return

        self.is_mining = True
        self.attempts = 0
        self.start_time = time.time()

        # UI 按鈕狀態切換
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.target_entry.config(state=tk.DISABLED)
        self.lbl_status.config(text="(起動狀態)", foreground="green")

        # 啟動背景計算線程
        self.mining_thread = threading.Thread(target=self._mining_loop, args=(target,), daemon=True)
        self.mining_thread.start()

        # 啟動 UI 數據輪詢更新
        self.root.after(100, self._update_ui_stats)

    def stop_mining(self):
        self.is_mining = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.target_entry.config(state=tk.NORMAL)
        self.lbl_status.config(text="(已停止)", foreground="red")

    def clear_fields(self):
        if self.is_mining:
            return
        # 清空樹狀表格與結果欄位
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.res_attempts_var.set("")
        self.res_time_var.set("")
        self.res_input_var.set("")
        self.res_hash_var.set("")
        self.lbl_attempts.config(text="已嘗試 0 次")
        self.lbl_elapsed.config(text="耗時 0.00 秒")
        self.lbl_hashrate.config(text="速率 0 hash/s")
        self.lbl_status.config(text="(待命狀態)", foreground="gray")

    def _mining_loop(self, target):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        
        while self.is_mining:
            # 隨機產生測試輸入 (Input)
            random_input = ''.join(random.choices(chars, k=10))
            
            # 計算 SHA-256 並轉換為 256 位的二進位字串
            hash_bytes = hashlib.sha256(random_input.encode('utf-8')).digest()
            binary_hash = ''.join(f'{b:08b}' for b in hash_bytes)
            
            self.attempts += 1

            # 控制即時 UI 顯示頻率 (每 50 次顯示更新一次記錄，增強視覺效能)
            if self.attempts % 50 == 0:
                self.root.after(0, self._add_tree_row, random_input, binary_hash)

            # 檢查是否匹配目標前綴
            if binary_hash.startswith(target):
                self.is_mining = False
                elapsed = time.time() - self.start_time
                self.root.after(0, self._on_target_hit, random_input, binary_hash, self.attempts, elapsed)
                break

    def _add_tree_row(self, input_str, binary_hash):
        if len(self.tree.get_children()) > 100:
            # 保持列表最多 100 筆最新紀錄，避免記憶體積累
            first_item = self.tree.get_children()[0]
            self.tree.delete(first_item)
            
        item = self.tree.insert("", tk.END, values=(input_str, binary_hash))
        self.tree.see(item)

    def _update_ui_stats(self):
        if self.is_mining:
            elapsed = time.time() - self.start_time
            rate = int(self.attempts / elapsed) if elapsed > 0 else 0
            
            self.lbl_attempts.config(text=f"已嘗試 {self.attempts:,} 次")
            self.lbl_elapsed.config(text=f"耗時 {elapsed:.2f} 秒")
            self.lbl_hashrate.config(text=f"速率 {rate:,} hash/s")
            
            self.root.after(100, self._update_ui_stats)

    def _on_target_hit(self, hit_input, hit_hash, attempts, elapsed):
        self.stop_mining()
        self.lbl_status.config(text="(命中成功！)", foreground="blue")
        
        # 將命中資料填入底部結果區
        self.res_attempts_var.set(f"{attempts:,}")
        self.res_time_var.set(f"{elapsed:.4f}")
        self.res_input_var.set(hit_input)
        self.res_hash_var.set(hit_hash)
        
        messagebox.showinfo("成功", f"成功命中目標！\n共嘗試 {attempts:,} 次，耗時 {elapsed:.2f} 秒。")

if __name__ == "__main__":
    root = tk.Tk()
    app = MiningSimulatorApp(root)
    root.mainloop()