# PDBase Assistant

<div align="center">
  <img src="./img/bg2.png" alt="PDF Viewer Background" 
       style="border: 2px solid #e0e0e0; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); width: 500;"
  />
</div>

### *Offline. Annotate. OCR. Explain.*  
📄 PDF Viewer with AI Analysis- PDbase Assistant  << Hỗ trợ thao tác với file pdf >>
> A lightweight, fully manual, no-nonsense PDF viewer built in Python — no web servers, no cloud dependencies. Just you, your PDF, and AI that explains it like a human.

---

## ✅ Features

| Feature | Description |
|--------|-------------|
| 📂 **Open & Navigate** | Load any PDF with smooth zoom (1.0x–5.0x) and page navigation. |
| ✍️ **Manual Annotation** | Highlight, draw freehand lines, or add sticky notes — all saved locally. |
| 🧠 **OCR on Selection** | Select text area → extract with EasyOCR → auto-copy to clipboard. |
| 🤖 **AI Explanation** | If `QwenAgent` is installed, analyze selected OCR text with context-aware AI (non-academic, clear explanations). |
| 💾 **Persistent Annotations** | All highlights, notes, and drawings saved in `.annot.json` beside your PDF. |
| 🚀 **Background Context Load** | Full PDF text is read and cached in `~/gmfiNN/` on open — speeds up AI analysis. |
| ⚡ **Threaded UI** | No freezing. OCR and AI run in background threads. |
| 🛡️ **Offline-First** | Zero reliance on web APIs or cloud services. Runs entirely locally. |

---

## 📦 Requirements

### Core (Required)
```bash
pip install PyMuPDF pillow easyocr
```
<span style="font-size: 1.2em;">📜 License</span>  
MIT © 2025 — Use freely. Modify. Share. No credit needed.  
Built by Võ Tiến Thiện — for those who code to understand, not to click.