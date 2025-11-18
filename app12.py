import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import json
import os
import io
import re
import threading  # Đảm bảo đã import ở đầu file

# Thêm import cho QwenAgent (chỉ import khi cần)
try:
    from QwenAgent import QwenAgent
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False
    print("QwenAgent không được cài đặt. Chức năng phân tích AI sẽ bị tắt.")

PROMT_A = str({
    "role bot ": "chuyên gia giải thích dễ hiểu không học thuật",
    "job": "user đang đọc file pdf có một số phân không hiểu cần giải thích , nêu chi tiết cho user ",
    "contex pdf file": {}
})


class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced PDF Viewer with AI Analysis")
        self.root.geometry("1200x900")

        # --- Biến trạng thái ---
        self.doc = None
        self.current_page_num = 0
        self.total_pages = 0
        self.page_image = None
        self.photo_image = None
        self.current_tool = "select"  # 'select', 'highlight', 'draw', 'note', 'ocr'
        self.annotations = {}  # {page_num: {'highlights': [...], 'drawings': [...], 'notes': {...}}}
        self.current_file_path = None
        
        # --- Zoom và điều chỉnh ảnh ---
        self.zoom_factor = 1.5
        self.zoom_step = 0.2
        self.max_zoom = 5.0
        self.min_zoom = 0.5

        # --- Canvas Drawing State ---
        self.start_x = None
        self.start_y = None
        self.current_shape_id = None
        self.temp_note_id = None
        self.temp_note_text = ""
        self.current_note_id = None

        # --- OCR & AI State ---
        self.last_ocr_end_pos = None  # Lưu vị trí cuối cùng khi kéo vùng OCR
        self.qwen_agent = None  # Khởi tạo agent sau khi cần

        # --- Tạo giao diện ---
        self.create_menu()
        self.create_toolbar()
        self.create_status_bar()
        self.create_canvas()

        # --- Bind sự kiện chuột ---
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Zoom bằng chuột
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_wheel)  # Zoom bằng Ctrl+chuột

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_pdf)
        file_menu.add_command(label="Save Annotations", command=self.save_annotations_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        menubar.add_cascade(label="View", menu=view_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Select", command=lambda: self.set_tool("select"))
        tools_menu.add_command(label="Highlight", command=lambda: self.set_tool("highlight"))
        tools_menu.add_command(label="Draw", command=lambda: self.set_tool("draw"))
        tools_menu.add_command(label="Add Note", command=lambda: self.set_tool("note"))
        tools_menu.add_command(label="Select Text (OCR)", command=lambda: self.set_tool("ocr"))
        menubar.add_cascade(label="Tools", menu=tools_menu)

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.open_button = ttk.Button(toolbar, text="Open PDF", command=self.open_pdf)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(toolbar, text="Prev", command=self.prev_page).pack(side=tk.LEFT, padx=2, pady=5)
        self.page_label = ttk.Label(toolbar, text="Page: 0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Next", command=self.next_page).pack(side=tk.LEFT, padx=2, pady=5)

        # Thêm nút zoom
        ttk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2, pady=5)
        self.zoom_label = ttk.Label(toolbar, text=f"Zoom: {self.zoom_factor:.1f}x")
        self.zoom_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Radio buttons cho công cụ
        self.tool_var = tk.StringVar(value="select")
        self.tool_var.trace_add("write", self.on_tool_change)
        ttk.Radiobutton(toolbar, text="Select", variable=self.tool_var, value="select").pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Radiobutton(toolbar, text="Highlight", variable=self.tool_var, value="highlight").pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Radiobutton(toolbar, text="Draw", variable=self.tool_var, value="draw").pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Radiobutton(toolbar, text="Note", variable=self.tool_var, value="note").pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Radiobutton(toolbar, text="OCR", variable=self.tool_var, value="ocr").pack(side=tk.LEFT, padx=5, pady=5)

    def create_status_bar(self):
        self.status = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def create_canvas(self):
        # Tạo một frame để chứa canvas và thanh cuộn
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg='white')
        
        # Tạo thanh cuộn
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Đặt canvas và thanh cuộn vào grid
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Cấu hình grid để canvas mở rộng
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

    def set_tool(self, tool):
        self.current_tool = tool
        self.status.config(text=f"Tool: {tool.capitalize()}")
        # Reset trạng thái vẽ tạm thời khi đổi công cụ
        self.reset_temp_drawings()

    def on_tool_change(self, *args):
        # Cập nhật tool từ Radiobutton
        self.set_tool(self.tool_var.get())

    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Open PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(file_path)
            self.current_file_path = file_path
            self.current_page_num = 0
            self.total_pages = len(self.doc)
            self.annotations = {} # Khởi tạo lại annotations cho file mới
            self.load_annotations_from_file() # Thử tải annotations nếu có
            self.render_page()
            self.status.config(text=f"Opened: {os.path.basename(file_path)} | Zoom: {self.zoom_factor:.1f}x")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open PDF: {e}")

    def load_annotations_from_file(self):
        if not self.current_file_path:
            return
        annot_file = self.current_file_path + ".annot.json"
        if os.path.exists(annot_file):
            try:
                with open(annot_file, 'r', encoding='utf-8') as f:
                    self.annotations = json.load(f)
                    # Chuyển key từ string sang int nếu cần
                    self.annotations = {int(k): v for k, v in self.annotations.items()}
            except Exception as e:
                print(f"Warning: Could not load annotations: {e}")

    def save_annotations_to_file(self):
        if not self.current_file_path or not self.annotations:
            return
        annot_file = self.current_file_path + ".annot.json"
        try:
            with open(annot_file, 'w', encoding='utf-8') as f:
                json.dump(self.annotations, f, ensure_ascii=False, indent=4)
            self.status.config(text="Annotations saved successfully.")
        except Exception as e:
            print(f"Warning: Could not save annotations: {e}")
            self.status.config(text="Failed to save annotations.")

    def render_page(self):
        if not self.doc or self.current_page_num < 0 or self.current_page_num >= self.total_pages:
            return

        page = self.doc[self.current_page_num]
        # Sử dụng zoom_factor hiện tại
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)  # Thêm alpha=False để tăng chất lượng

        # Chuyển pixmap sang Image của PIL
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))

        # Chuyển sang PhotoImage của Tkinter
        self.photo_image = ImageTk.PhotoImage(img)

        # Hiển thị lên canvas
        self.canvas.delete("all") # Xóa nội dung cũ
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        self.canvas.config(scrollregion=self.canvas.bbox("all")) # Cập nhật vùng cuộn

        # Cập nhật label số trang
        self.page_label.config(text=f"Page: {self.current_page_num + 1} / {self.total_pages}")
        self.zoom_label.config(text=f"Zoom: {self.zoom_factor:.1f}x")

        # Vẽ lại các annotation cho trang hiện tại
        self.redraw_annotations()

    def redraw_annotations(self):
        if self.current_page_num not in self.annotations:
            return

        page_annotations = self.annotations[self.current_page_num]

        # Vẽ lại highlights
        if "highlights" in page_annotations:
            for hl in page_annotations["highlights"]:
                # hl = [x0, y0, x1, y1, color, alpha]
                x0, y0, x1, y1 = hl[0], hl[1], hl[2], hl[3]
                color = hl[4] if len(hl) > 4 else "yellow"
                alpha = hl[5] if len(hl) > 5 else 0.3
                # Tính toán lại tọa độ theo zoom factor mới
                x0 *= self.zoom_factor
                y0 *= self.zoom_factor
                x1 *= self.zoom_factor
                y1 *= self.zoom_factor
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, stipple="gray50", outline="")

        # Vẽ lại drawings
        if "drawings" in page_annotations:
            for drawing in page_annotations["drawings"]:
                # drawing = ['line', x0, y0, x1, y1, color, width] hoặc ['oval', x0, y0, x1, y1, color, width]
                shape_type = drawing[0]
                coords = drawing[1:5]
                color = drawing[5]
                width = drawing[6]
                # Tính toán lại tọa độ theo zoom factor mới
                coords = [c * self.zoom_factor for c in coords]
                width *= self.zoom_factor
                if shape_type == "line":
                    self.canvas.create_line(*coords, fill=color, width=width)
                elif shape_type == "oval":
                    self.canvas.create_oval(*coords, outline=color, width=width)

        # Vẽ lại notes
        if "notes" in page_annotations:
            for pos_key, note_text in page_annotations["notes"].items():
                x, y = map(int, pos_key.split(','))
                # Tính toán lại vị trí theo zoom factor mới
                x *= self.zoom_factor
                y *= self.zoom_factor
                # Vẽ một biểu tượng nhỏ (hình tròn)
                circle_id = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="black")
                # Gắn nội dung ghi chú vào ID hình tròn
                self.canvas.addtag_withtag(note_text, circle_id)
                self.canvas.tag_bind(circle_id, "<Button-1>", lambda e, t=note_text: self.show_note(t))

    def show_note(self, text):
        messagebox.showinfo("Note", text)

    def on_mouse_down(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.reset_temp_drawings()

        if self.current_tool == "highlight":
            self.current_shape_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline="red", dash=(2, 2) # Dùng nét đứt để preview
            )
        elif self.current_tool == "draw":
            self.current_shape_id = self.canvas.create_line(
                self.start_x, self.start_y, self.start_x, self.start_y,
                fill="blue", width=2, capstyle=tk.ROUND, smooth=tk.TRUE
            )
        elif self.current_tool == "note":
            # Hiển thị hộp thoại nhập ghi chú
            note_text = simpledialog.askstring("Add Note", "Enter your note:")
            if note_text:
                circle_id = self.canvas.create_oval(
                    self.start_x-5, self.start_y-5, self.start_x+5, self.start_y+5,
                    fill="red", outline="black"
                )
                self.temp_note_id = circle_id
                self.temp_note_text = note_text
                self.canvas.tag_bind(circle_id, "<Button-1>", lambda e, t=note_text: self.show_note(t))
        elif self.current_tool == "ocr":
            # Bắt đầu vùng chọn OCR
            self.current_shape_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline="blue", dash=(2, 2)
            )

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        if self.current_tool in ["highlight", "ocr"] and self.current_shape_id:
            self.canvas.coords(self.current_shape_id, self.start_x, self.start_y, cur_x, cur_y)
        elif self.current_tool == "draw" and self.current_shape_id:
            # Thêm điểm mới vào đường vẽ
            coords = list(self.canvas.coords(self.current_shape_id))
            coords.extend([cur_x, cur_y])
            self.canvas.coords(self.current_shape_id, *coords)

    def on_mouse_up(self, event):
        if not self.doc or self.current_page_num < 0 or self.current_page_num >= self.total_pages:
            return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        if self.current_tool == "highlight" and self.current_shape_id:
            # Xóa preview nét đứt
            self.canvas.delete(self.current_shape_id)
            # Xác định tọa độ highlight (chuyển đổi lại từ tọa độ zoomed sang gốc)
            x_coords = sorted([self.start_x, end_x])
            y_coords = sorted([self.start_y, end_y])
            x0, x1 = x_coords[0], x_coords[1]
            y0, y1 = y_coords[0], y_coords[1]
            
            # Chuyển đổi tọa độ về hệ tọa độ gốc của PDF
            x0 /= self.zoom_factor
            y0 /= self.zoom_factor
            x1 /= self.zoom_factor
            y1 /= self.zoom_factor
            
            # Kiểm tra xem vùng chọn có hợp lệ không (khác 0)
            if abs(x1 - x0) > 1 and abs(y1 - y0) > 1:
                # Vẽ lại highlight trên ảnh gốc với tọa độ đã zoom
                self.canvas.create_rectangle(self.start_x, self.start_y, end_x, end_y, fill="yellow", stipple="gray50", outline="")
                # Lưu annotation với tọa độ gốc
                if self.current_page_num not in self.annotations:
                    self.annotations[self.current_page_num] = {"highlights": [], "drawings": [], "notes": {}}
                self.annotations[self.current_page_num]["highlights"].append([x0, y0, x1, y1, "yellow", 0.3])
                self.save_annotations_to_file()

        elif self.current_tool == "draw" and self.current_shape_id:
            # Đã vẽ xong, lưu lại tọa độ cuối
            coords = self.canvas.coords(self.current_shape_id)
            if len(coords) >= 4: # Phải có ít nhất 1 đoạn thẳng
                # Chuyển đổi tọa độ về hệ tọa độ gốc của PDF
                normalized_coords = [c / self.zoom_factor for c in coords]
                if self.current_page_num not in self.annotations:
                    self.annotations[self.current_page_num] = {"highlights": [], "drawings": [], "notes": {}}
                # Lưu toàn bộ đường vẽ với tọa độ gốc
                self.annotations[self.current_page_num]["drawings"].append(["line", *normalized_coords, "blue", 2])
                self.save_annotations_to_file()

        elif self.current_tool == "note" and self.temp_note_id:
            # Chuyển đổi tọa độ về hệ tọa độ gốc của PDF
            x = int(self.start_x / self.zoom_factor)
            y = int(self.start_y / self.zoom_factor)
            # Gắn ghi chú vào dữ liệu
            if self.current_page_num not in self.annotations:
                self.annotations[self.current_page_num] = {"highlights": [], "drawings": [], "notes": {}}
            pos_key = f"{x},{y}"
            self.annotations[self.current_page_num]["notes"][pos_key] = self.temp_note_text
            self.save_annotations_to_file()
            self.temp_note_id = None
            self.temp_note_text = ""

        elif self.current_tool == "ocr" and self.current_shape_id:
            # Xóa preview nét đứt
            self.canvas.delete(self.current_shape_id)
            # Xác định tọa độ vùng OCR (chuyển đổi lại từ tọa độ zoomed sang gốc)
            x_coords = sorted([self.start_x, end_x])
            y_coords = sorted([self.start_y, end_y])
            x0, x1 = x_coords[0], x_coords[1]
            y0, y1 = y_coords[0], y_coords[1]
            
            # Chuyển đổi tọa độ về hệ tọa độ gốc của PDF
            x0 /= self.zoom_factor
            y0 /= self.zoom_factor
            x1 /= self.zoom_factor
            y1 /= self.zoom_factor

            if abs(x1 - x0) > 5 and abs(y1 - y0) > 5: # Kiểm tra vùng chọn đủ lớn
                # Lưu vị trí cuối cùng cho popup
                self.last_ocr_end_pos = (end_x, end_y)  # Lưu tọa độ cuối cùng của vùng OCR
                self.perform_ocr_on_area(x0, y0, x1, y1)

        self.reset_temp_drawings()

    def reset_temp_drawings(self):
        if self.current_shape_id:
            self.canvas.delete(self.current_shape_id)
            self.current_shape_id = None
        if self.temp_note_id:
            self.canvas.delete(self.temp_note_id)
            self.temp_note_id = None
            self.temp_note_text = ""

    def prev_page(self):
        if self.doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self.render_page()

    def next_page(self):
        if self.doc and self.current_page_num < self.total_pages - 1:
            self.current_page_num += 1
            self.render_page()

    def zoom_in(self):
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor = round(self.zoom_factor + self.zoom_step, 2)
            self.render_page()

    def zoom_out(self):
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor = round(self.zoom_factor - self.zoom_step, 2)
            self.render_page()
            
    def reset_zoom(self):
        self.zoom_factor = 1.5
        self.render_page()

    def on_mousewheel(self, event):
        # Cuộn dọc
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_ctrl_wheel(self, event):
        # Zoom bằng Ctrl + cuộn chuột
        if event.state & 0x4:  # Kiểm tra phím Ctrl
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def perform_ocr_on_area(self, x0, y0, x1, y1):
        try:
            import easyocr
        except ImportError:
            messagebox.showerror("Error", "EasyOCR not installed. Please run: pip install easyocr")
            return

        if not self.doc:
            return

        page = self.doc[self.current_page_num]
        # Sử dụng zoom_factor hiện tại để có chất lượng cao hơn
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_data = pix.tobytes("ppm")
        pil_img = Image.open(io.BytesIO(img_data))

        # Chuyển đổi tọa độ sang hệ ảnh đã zoom
        x0 *= self.zoom_factor
        y0 *= self.zoom_factor
        x1 *= self.zoom_factor
        y1 *= self.zoom_factor
        
        cropped_img = pil_img.crop((int(x0), int(y0), int(x1), int(y1)))
        import numpy as np
        img_np = np.array(cropped_img)

        if not hasattr(self, 'easyocr_reader'):
            try:
                self.easyocr_reader = easyocr.Reader(['en', 'vi'], gpu=False)
            except Exception as e:
                messagebox.showerror("OCR Error", f"Failed to initialize EasyOCR: {e}")
                return

        try:
            result = self.easyocr_reader.readtext(img_np, detail=0)
            text = "\n".join(result) if result else ""

            if text.strip():
                # Copy vào clipboard
                self.root.clipboard_clear()
                self.root.clipboard_append(text.strip())
                
                # Hiển thị thông báo và mở popup
                self.status.config(text="OCR text copied to clipboard. Opening analysis window...")
                self.show_ocr_analysis_popup(text.strip())
                
            else:
                messagebox.showinfo("OCR Result", "No text found in the selected area.")

        except Exception as e:
            messagebox.showerror("OCR Error", f"EasyOCR failed: {e}")

    def show_ocr_analysis_popup(self, ocr_text):
        """Mở cửa sổ popup mini để hiển thị kết quả phân tích từ AI"""
        popup = tk.Toplevel(self.root)
        popup.title("OCR Analysis")
        popup.geometry("600x400")  # Kích thước vừa đủ
        popup.resizable(True, True)
        
        # Đặt vị trí popup tại vị trí cuối cùng của vùng OCR (nếu có)
        if self.last_ocr_end_pos:
            # Chuyển tọa độ từ canvas sang màn hình
            canvas_x, canvas_y = self.last_ocr_end_pos
            # Lấy vị trí tuyệt đối của canvas trên màn hình
            canvas_abs_x = self.canvas.winfo_rootx()
            canvas_abs_y = self.canvas.winfo_rooty()
            # Tính toán vị trí popup
            popup_x = canvas_abs_x + int(canvas_x)
            popup_y = canvas_abs_y + int(canvas_y)
            # Đảm bảo popup không bị ra ngoài màn hình
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            popup_x = max(0, min(popup_x, screen_width - 600))
            popup_y = max(0, min(popup_y, screen_height - 400))
            popup.geometry(f"+{popup_x}+{popup_y}")
        
        # Frame chứa nội dung
        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tiêu đề
        title_label = ttk.Label(frame, text="OCR Analysis Result", font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Text widget để hiển thị kết quả
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Arial", 10), bg="white", relief=tk.SUNKEN)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar cho text widget
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Nút đóng
        close_button = ttk.Button(frame, text="Close", command=popup.destroy)
        close_button.pack(pady=(10, 0), anchor=tk.E)
        
        # Bắt đầu phân tích với AI nếu có
        if QWEN_AVAILABLE:
            self.analyze_with_ai(ocr_text, text_widget)
        else:
            text_widget.insert(tk.END, "QwenAgent không được cài đặt. Không thể phân tích nội dung.\n\n")
            text_widget.insert(tk.END, "OCR Text:\n")
            text_widget.insert(tk.END, ocr_text)

    def analyze_with_ai(self, text, text_widget):
        """Gọi QwenAgent để phân tích văn bản và hiển thị kết quả — chạy trong luồng nền"""
        
        def run_analysis():
            try:
                # Khởi tạo agent nếu chưa có
                if not self.qwen_agent:
                    self.qwen_agent = QwenAgent()
                
                input_user = f"Please analyze this text and provide detailed information:\n\n{text}"
                question = str({
                    "promt engineer": PROMT_A,
                    "promt user": input_user
                })

                # Xóa thông báo cũ và bắt đầu streaming
                text_widget.delete("1.0", tk.END)
                text_widget.insert(tk.END, "⏳ AI is analyzing...\n\n")
                text_widget.see(tk.END)

                full_response = ""
                last_sent_index = 0
                
                resp = self.qwen_agent.send(question, stream=True)
                for raw in resp.iter_lines(decode_unicode=True):
                    if not raw.startswith("data: "):
                        continue
                    chunk_str = raw[6:].strip()
                    if chunk_str in ("[DONE]", ""):
                        break

                    try:
                        data = json.loads(chunk_str)
                        delta = data["choices"][0]["delta"]
                        content = delta.get("content", "")
                    except (KeyError, IndexError, json.JSONDecodeError):
                        continue

                    if content:
                        full_response += content
                        
                        # Tách section theo logic của bạn
                        sections = self.split_by_section_delimiters(full_response[last_sent_index:])
                        
                        # Hiển thị từng section hoàn chỉnh
                        while len(sections) >= 2:
                            to_display = sections[0].strip()
                            if to_display:
                                # Cập nhật GUI — PHẢI dùng after() vì đang ở luồng nền
                                def update_text(display_text=to_display):
                                    text_widget.insert(tk.END, display_text + "\n\n")
                                    text_widget.see(tk.END)
                                self.root.after(0, update_text)
                            
                            full_response = "".join(sections[1:])
                            last_sent_index = 0
                            sections = self.split_by_section_delimiters(full_response)

                # Hiển thị phần còn lại
                remaining = full_response[last_sent_index:].strip()
                if remaining:
                    self.root.after(0, lambda: text_widget.insert(tk.END, remaining + "\n"))
                self.root.after(0, lambda: text_widget.insert(tk.END, "\n✅ Analysis complete.\nGMFinn có thể giúp gì cho bạn ?"))
                self.root.after(0, lambda: text_widget.see(tk.END))

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                self.root.after(0, lambda: text_widget.insert(tk.END, error_msg))
                self.root.after(0, lambda: text_widget.see(tk.END))

        # KHỞI CHẠY LUỒNG NỀN
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()

    def split_by_section_delimiters(self, text: str):
        """
        Tách văn bản thành các phần dựa trên:
          - Dòng bắt đầu bằng "## " → bắt đầu section mới, GIỮ LẠI dòng này.
          - Dòng chỉ chứa "---" (có thể có space) → kết thúc section hiện tại, KHÔNG GIỮ LẠI.
        
        Giữ H1 (nếu có ở đầu) cho section đầu tiên.
        """
        lines = text.splitlines(keepends=True)
        parts = []
        current_section = ""

        # Xử lý H1 ở đầu (nếu có)
        h1_line = None
        if lines and re.match(r"^#\s", lines[0]):
            h1_line = lines[0]
            lines = lines[1:]

        current_section = h1_line or ""

        for line in lines:
            # Kiểm tra H2: bắt đầu section mới, GIỮ LẠI dòng này
            if re.match(r"^##\s", line):
                if current_section.strip():
                    parts.append(current_section)
                current_section = line  # bắt đầu section mới với H2
            # Kiểm tra horizontal rule: kết thúc section, KHÔNG GIỮ LẠI
            elif re.fullmatch(r"\s*---\s*", line):
                if current_section.strip():
                    parts.append(current_section)
                    current_section = ""  # bắt đầu section mới trống
                # Nếu current_section rỗng, bỏ qua (tránh section rỗng)
            else:
                current_section += line

        # Thêm phần cuối
        if current_section.strip():
            parts.append(current_section)

        return parts

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFViewerApp(root)
    app.run()