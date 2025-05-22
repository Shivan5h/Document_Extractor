# 📄 Purchase Order Document Extractor

A Streamlit-based AI application that extracts structured data from purchase order PDFs using Claude's Vision model (Anthropic API). This tool intelligently reads PDF files and converts them into clean, structured JSON format suitable for automation workflows.

---

## 🚀 Features

- Extracts:
  - Purchase order number, date, expiry
  - Customer & Vendor info (name, address, contact)
  - Tabular item details (items, prices, quantity)
- Converts PDF to images and sends to Claude for vision-based inference
- JSON output ready for automation tools
- Streamlit interface for easy use
- Advanced mode for extracting taxes, discounts, shipping info, etc.

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **AI Model**: Anthropic Claude (Vision)
- **Libraries**:
  - `PyMuPDF` (PDF → image)
  - `httpx` (API request handling)
  - `Pandas` (Tabular visualization)
  - `PIL` (Image processing)

---

## 📂 Project Structure

```bash
├── test.py                 # Streamlit App (Frontend)
├── anthropic_fix.py        # Anthropic API + Vision model integration
├── README.md               # Documentation
├── AI_Intern_Writeup.docx  # Application write-up for internship
