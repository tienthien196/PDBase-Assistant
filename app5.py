import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import json
import os
import io

class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced PDF Viewer Desktop App")
        self.root.geometry("1200x900")

        # --- Biến trạng thái ---
        self.doc = None
        self.current_page_num = 0
        self.total_pages = 0
        self.page_image = None
        self.photo_image = None
        self.current_tool = "select"  # 'select', 'highlight', 'draw', 'note'
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
                self.root.clipboard_clear()
                self.root.clipboard_append(text.strip())
                self.status.config(text="OCR text copied to clipboard.")
                messagebox.showinfo("OCR Result", f"Text copied:\n\n{text.strip()}")
            else:
                messagebox.showinfo("OCR Result", "No text found in the selected area.")

        except Exception as e:
            messagebox.showerror("OCR Error", f"EasyOCR failed: {e}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFViewerApp(root)
    app.run()