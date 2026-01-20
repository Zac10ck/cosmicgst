# GST Billing Software

A lightweight, offline-first billing application for Kerala-based retail shops with GST compliance.

## Features

- **GST Compliant Invoicing** - CGST/SGST for intra-state (Kerala)
- **Barcode Scanner Support** - Quick billing with USB scanners
- **Inventory Management** - Track stock with low-stock alerts
- **A4 PDF Invoices** - Professional invoice printing
- **Customer Management** - Save customer details
- **Reports** - Daily sales, GST summary, stock reports
- **GSTR-1 Export** - JSON export for GST portal
- **Google Drive Backup** - Automatic cloud backup

## Download

Go to [Releases](../../releases) and download `GST_Billing.exe`

## Usage

1. Download `GST_Billing.exe`
2. Double-click to run (no installation needed)
3. Go to **Settings** → Enter your shop details
4. Add products in **Products** tab
5. Start billing in **New Bill** tab

## Tech Stack

- **Backend**: Python, SQLite
- **Frontend**: CustomTkinter
- **PDF**: ReportLab

## Building from Source

```bash
pip install customtkinter pillow reportlab num2words python-dateutil pyinstaller
python assets/create_icon.py
pyinstaller --onefile --windowed --name "GST_Billing" --icon "assets/icon.ico" main.py
```

## License

Free for personal and commercial use.
