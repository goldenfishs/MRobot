import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class PolyFitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多项式拟合工具")
        self.data_x = []
        self.data_y = []
        self.last_coeffs = None

        # ===== 主布局 =====
        main_frame = ttk.Frame(root, padding=8)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # ===== 左侧区 =====
        left_frame = ttk.Frame(main_frame, width=320, height=580)  # 设置固定宽度
        left_frame.grid(row=0, column=0, sticky="nsw")  # 只贴左侧
        left_frame.columnconfigure(0, weight=1)
        left_frame.grid_propagate(False)  # 防止自动缩放

        # --- 数据输入区 ---
        input_frame = ttk.LabelFrame(left_frame, text="数据输入", padding=6)
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        input_frame.columnconfigure(0, weight=1)

        self.excel_btn = ttk.Button(input_frame, text="导入excel文件", command=self.load_excel)
        self.excel_btn.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        # 滚动区域
        self.scroll_canvas = tk.Canvas(input_frame, height=200)
        self.scroll_canvas.grid(row=1, column=0, sticky="ew", pady=4)
        self.scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.manual_frame = ttk.Frame(self.scroll_canvas)
        self.manual_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
        self.scroll_canvas.create_window((0, 0), window=self.manual_frame, anchor="nw")

        self.point_rows = []
        self.add_row_btn = ttk.Button(input_frame, text="添加数据", command=self.add_point_row)
        self.add_row_btn.grid(row=2, column=0, sticky="ew", padx=2, pady=2)

        # --- 参数区 ---
        param_frame = ttk.LabelFrame(left_frame, text="拟合参数", padding=6)
        param_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(param_frame, text="选择多项式阶数:").grid(row=0, column=0, padx=2, pady=2, sticky="e")
        self.order_spin = ttk.Spinbox(param_frame, from_=1, to=10, width=5)
        self.order_spin.set(2)
        self.order_spin.grid(row=0, column=1, padx=2, pady=2, sticky="w")
        # 优化复选框和拟合按钮同一行
        self.fit_btn = ttk.Button(param_frame, text="拟合并显示", command=self.fit_and_plot)
        self.fit_btn.grid(row=1, column=0, padx=2, pady=4, sticky="ew")
        self.optimize_var = tk.BooleanVar(value=True)
        self.optimize_check = ttk.Checkbutton(param_frame, text="优化曲线（防止突起）", variable=self.optimize_var)
        self.optimize_check.grid(row=1, column=1, padx=2, pady=4, sticky="w")

        # --- 输出区 ---
        output_frame = ttk.LabelFrame(left_frame, text="表达式与代码", padding=6)
        output_frame.grid(row=2, column=0, sticky="ew")
        self.output = tk.Text(output_frame, height=6, width=40, font=("Consolas", 10))
        self.output.grid(row=0, column=0, columnspan=3, padx=2, pady=2)
        ttk.Label(output_frame, text="输出代码格式:").grid(row=1, column=0, padx=2, pady=2, sticky="e")
        self.code_type = ttk.Combobox(output_frame, values=["C", "C++", "Python"], width=8)
        self.code_type.set("C")
        self.code_type.grid(row=1, column=1, padx=2, pady=2, sticky="w")
        self.gen_code_btn = ttk.Button(output_frame, text="生成函数代码", command=self.generate_code)
        self.gen_code_btn.grid(row=1, column=2, padx=2, pady=2, sticky="ew")

        # ===== 右侧区 =====
        right_frame = ttk.Frame(main_frame)
        # right_frame.grid(row=0, column=1, sticky="nsew")  # 填满剩余空间
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        plot_frame = ttk.LabelFrame(right_frame, text="拟合曲线", padding=6)
        plot_frame.grid(row=0, column=0, sticky="nsew")
        plot_frame.rowconfigure(0, weight=1)
        plot_frame.columnconfigure(0, weight=1)
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)


    def _on_mousewheel(self, event):
        # Windows下event.delta为120的倍数，负值向下
        self.scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_point_row(self, x_val="", y_val=""):
        row = {}
        idx = len(self.point_rows)
        row['x'] = ttk.Entry(self.manual_frame, width=10)
        row['x'].insert(0, str(x_val))
        row['y'] = ttk.Entry(self.manual_frame, width=10)
        row['y'].insert(0, str(y_val))
        row['del'] = ttk.Button(self.manual_frame, text="删除", width=5, command=lambda r=idx: self.delete_point_row(r))
        row['x'].grid(row=idx, column=0, padx=1, pady=1)
        row['y'].grid(row=idx, column=1, padx=1, pady=1)
        row['del'].grid(row=idx, column=2, padx=1, pady=1)
        self.point_rows.append(row)
        self.refresh_point_rows()

    def delete_point_row(self, idx):
        for widget in self.point_rows[idx].values():
            widget.grid_forget()
            widget.destroy()
        self.point_rows.pop(idx)
        self.refresh_point_rows()

    def refresh_point_rows(self):
        for i, row in enumerate(self.point_rows):
            row['x'].grid(row=i, column=0, padx=1, pady=1)
            row['y'].grid(row=i, column=1, padx=1, pady=1)
            row['del'].config(command=lambda r=i: self.delete_point_row(r))
            row['del'].grid(row=i, column=2, padx=1, pady=1)

    def load_excel(self):
        file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file:
            try:
                data = pd.read_excel(file, usecols=[0, 1])
                new_x = data.iloc[:, 0].values.tolist()
                new_y = data.iloc[:, 1].values.tolist()
                messagebox.showinfo("成功", "数据导入成功！")
                for x, y in zip(new_x, new_y):
                    self.add_point_row(x, y)
            except Exception as e:
                messagebox.showerror("错误", f"读取Excel失败: {e}")

    def get_manual_points(self):
        x_list, y_list = [], []
        for row in self.point_rows:
            try:
                x = float(row['x'].get())
                y = float(row['y'].get())
                x_list.append(x)
                y_list.append(y)
            except ValueError:
                continue
        return x_list, y_list


    def fit_and_plot(self):
        # 始终以手动输入区为准
        self.data_x, self.data_y = self.get_manual_points()
        try:
            order = int(self.order_spin.get())
        except ValueError:
            messagebox.showwarning("输入错误", "阶数必须为整数！")
            return
        n_points = len(self.data_x)
        if n_points < order + 1:
            messagebox.showwarning("数据不足", "数据点数量不足以拟合该阶多项式！")
            return

        # 阶数过高判断，只提示不强制修改
        max_order = max(2, min(6, n_points // 3))
        if order > max_order:
            messagebox.showwarning("阶数过高", f"当前数据点数为{n_points}，建议阶数不超过{max_order}，否则容易出现异常突起！")

        x = np.array(self.data_x, dtype=np.float64)
        y = np.array(self.data_y, dtype=np.float64)

        # ----------- 新增归一化 -----------
        x_min, x_max = x.min(), x.max()
        if x_max - x_min == 0:
            messagebox.showwarning("数据错误", "所有x值都相同，无法拟合！")
            return
        x_norm = (x - x_min) / (x_max - x_min)
        # ---------------------------------

        try:
            if self.optimize_var.get():
                # 优化：加大rcond，减少高阶影响
                coeffs = np.polyfit(x_norm, y, order, rcond=1e-3)
            else:
                coeffs = np.polyfit(x_norm, y, order)
        except Exception as e:
            messagebox.showerror("拟合错误", f"多项式拟合失败：{e}")
            return
        poly = np.poly1d(coeffs)
        expr = "y = " + " + ".join([f"{c:.6g}*x_norm^{order-i}" for i, c in enumerate(coeffs)])
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, f"归一化x: x_norm=(x-{x_min:.6g})/({x_max:.6g}-{x_min:.6g})\n")
        self.output.insert(tk.END, expr + "\n")
        # 绘图
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(x, y, color='red', label='数据点')
        x_fit = np.linspace(x_min, x_max, 200)
        x_fit_norm = (x_fit - x_min) / (x_max - x_min)
        y_fit = poly(x_fit_norm)
        ax.plot(x_fit, y_fit, label='拟合曲线')
        ax.legend()
        self.canvas.draw()
        self.last_coeffs = coeffs
        self.last_xmin = x_min
        self.last_xmax = x_max

    def generate_code(self):
        if self.last_coeffs is None:
            messagebox.showwarning("未拟合", "请先拟合数据！")
            return
        coeffs = self.last_coeffs
        order = len(coeffs) - 1
        code_type = self.code_type.get()
        if code_type == "C":
            code = self.create_c_function(coeffs)
        elif code_type == "C++":
            code = self.create_cpp_function(coeffs)
        else:
            code = self.create_py_function(coeffs)
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, code)

    def create_c_function(self, coeffs):
        lines = ["#include <math.h>", "double polynomial(double x) {", "    return "]
        n = len(coeffs)
        terms = []
        for i, c in enumerate(coeffs):
            exp = n - i - 1
            if exp == 0:
                terms.append(f"{c:.8g}")
            elif exp == 1:
                terms.append(f"{c:.8g}*x")
            else:
                terms.append(f"{c:.8g}*pow(x,{exp})")
        lines[-1] += " + ".join(terms) + ";"
        lines.append("}")
        return "\n".join(lines)

    def create_cpp_function(self, coeffs):
        lines = ["#include <cmath>", "double polynomial(double x) {", "    return "]
        n = len(coeffs)
        terms = []
        for i, c in enumerate(coeffs):
            exp = n - i - 1
            if exp == 0:
                terms.append(f"{c:.8g}")
            elif exp == 1:
                terms.append(f"{c:.8g}*x")
            else:
                terms.append(f"{c:.8g}*pow(x,{exp})")
        lines[-1] += " + ".join(terms) + ";"
        lines.append("}")
        return "\n".join(lines)

    def create_py_function(self, coeffs):
        n = len(coeffs)
        lines = ["def polynomial(x):", "    return "]
        terms = []
        for i, c in enumerate(coeffs):
            exp = n - i - 1
            if exp == 0:
                terms.append(f"{c:.8g}")
            elif exp == 1:
                terms.append(f"{c:.8g}*x")
            else:
                terms.append(f"{c:.8g}*x**{exp}")
        lines[-1] += " + ".join(terms)
        return "\n".join(lines)

if __name__ == "__main__":
    root = tk.Tk()
    app = PolyFitApp(root)
    root.mainloop()