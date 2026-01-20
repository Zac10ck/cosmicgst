"""Settings screen"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from database.models import Company
from services.backup_service import BackupService
from utils.validators import validate_gstin, validate_phone, validate_email


class SettingsFrame(ctk.CTkFrame):
    """Application settings"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.backup_service = BackupService()

        self._create_widgets()
        self._load_company()

    def _create_widgets(self):
        """Create settings screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Settings tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.tabview.add("Company Details")
        self.tabview.add("Backup")
        self.tabview.add("About")

        self._create_company_tab()
        self._create_backup_tab()
        self._create_about_tab()

    def _create_company_tab(self):
        """Create company details tab"""
        tab = self.tabview.tab("Company Details")

        # Scrollable form
        form = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=10)

        # Company Name
        ctk.CTkLabel(form, text="Company/Shop Name *").pack(anchor="w", pady=(10, 5))
        self.company_name_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.company_name_var, width=400).pack(anchor="w")

        # Address
        ctk.CTkLabel(form, text="Address").pack(anchor="w", pady=(15, 5))
        self.address_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.address_var, width=400).pack(anchor="w")

        # GSTIN
        ctk.CTkLabel(form, text="GSTIN").pack(anchor="w", pady=(15, 5))
        self.gstin_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.gstin_var, width=400).pack(anchor="w")

        # Phone
        ctk.CTkLabel(form, text="Phone").pack(anchor="w", pady=(15, 5))
        self.phone_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.phone_var, width=400).pack(anchor="w")

        # Email
        ctk.CTkLabel(form, text="Email").pack(anchor="w", pady=(15, 5))
        self.email_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.email_var, width=400).pack(anchor="w")

        # Bank Details
        ctk.CTkLabel(form, text="Bank Details (for invoice)").pack(anchor="w", pady=(15, 5))
        self.bank_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.bank_var, width=400).pack(anchor="w")

        # Save button
        ctk.CTkButton(
            form,
            text="Save Company Details",
            command=self._save_company
        ).pack(pady=30)

    def _create_backup_tab(self):
        """Create backup settings tab"""
        tab = self.tabview.tab("Backup")

        # Status
        self.backup_status_frame = ctk.CTkFrame(tab)
        self.backup_status_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            self.backup_status_frame,
            text="Backup Status",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        self.backup_status_label = ctk.CTkLabel(
            self.backup_status_frame,
            text="Checking..."
        )
        self.backup_status_label.pack(pady=5)

        self.backup_dir_label = ctk.CTkLabel(
            self.backup_status_frame,
            text="",
            text_color="gray"
        )
        self.backup_dir_label.pack(pady=5)

        self.last_backup_label = ctk.CTkLabel(
            self.backup_status_frame,
            text=""
        )
        self.last_backup_label.pack(pady=(5, 15))

        # Actions
        actions_frame = ctk.CTkFrame(tab, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            actions_frame,
            text="Backup Now",
            fg_color="green",
            command=self._do_backup
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame,
            text="Restore from Backup",
            fg_color="orange",
            command=self._restore_backup
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame,
            text="Refresh Status",
            command=self._refresh_backup_status
        ).pack(side="left", padx=5)

        # Backup list
        ctk.CTkLabel(
            tab,
            text="Available Backups",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 10), padx=20, anchor="w")

        self.backup_list = ctk.CTkScrollableFrame(tab, height=200)
        self.backup_list.pack(fill="x", padx=20, pady=10)

        self._refresh_backup_status()

    def _create_about_tab(self):
        """Create about tab"""
        tab = self.tabview.tab("About")

        from config import APP_NAME, APP_VERSION

        ctk.CTkLabel(
            tab,
            text=APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            tab,
            text=f"Version {APP_VERSION}",
            font=ctk.CTkFont(size=14)
        ).pack()

        ctk.CTkLabel(
            tab,
            text="GST Compliant Billing Software for India",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            tab,
            text="Designed for Kerala-based retail businesses",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack()

        features = [
            "GST Invoice Generation (CGST/SGST)",
            "Barcode Scanner Support",
            "Inventory Management",
            "A4 PDF Invoices",
            "GSTR-1 Export",
            "Google Drive Backup"
        ]

        ctk.CTkLabel(
            tab,
            text="\nFeatures:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(30, 10))

        for feature in features:
            ctk.CTkLabel(tab, text=f"  {feature}").pack()

    def _load_company(self):
        """Load company details"""
        company = Company.get()
        if company:
            self.company_name_var.set(company.name)
            self.address_var.set(company.address or "")
            self.gstin_var.set(company.gstin or "")
            self.phone_var.set(company.phone or "")
            self.email_var.set(company.email or "")
            self.bank_var.set(company.bank_details or "")

    def _save_company(self):
        """Save company details"""
        name = self.company_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Company name is required")
            return

        # Validate GSTIN
        gstin = self.gstin_var.get().strip().upper()
        if gstin:
            valid, error = validate_gstin(gstin)
            if not valid:
                messagebox.showerror("Error", error)
                return

        # Validate phone
        phone = self.phone_var.get().strip()
        if phone:
            valid, error = validate_phone(phone)
            if not valid:
                messagebox.showerror("Error", error)
                return

        # Validate email
        email = self.email_var.get().strip()
        if email:
            valid, error = validate_email(email)
            if not valid:
                messagebox.showerror("Error", error)
                return

        # Save
        company = Company.get()
        if not company:
            company = Company()

        company.name = name
        company.address = self.address_var.get().strip()
        company.gstin = gstin
        company.phone = phone
        company.email = email
        company.bank_details = self.bank_var.get().strip()
        company.save()

        messagebox.showinfo("Success", "Company details saved successfully!")

    def _refresh_backup_status(self):
        """Refresh backup status display"""
        status = self.backup_service.get_backup_status()

        if status.get('google_drive_available'):
            self.backup_status_label.configure(
                text="Google Drive: Connected",
                text_color="green"
            )
        else:
            self.backup_status_label.configure(
                text="Google Drive: Not Found (Install Google Drive Desktop)",
                text_color="orange"
            )

        self.backup_dir_label.configure(
            text=f"Backup folder: {status.get('backup_dir', 'N/A')}"
        )

        if status.get('last_backup'):
            self.last_backup_label.configure(
                text=f"Last backup: {status['last_backup'].strftime('%d-%b-%Y %H:%M')}"
            )
        else:
            self.last_backup_label.configure(text="Last backup: Never")

        # Update backup list
        for widget in self.backup_list.winfo_children():
            widget.destroy()

        backups = self.backup_service.get_backup_list()
        if backups:
            for backup in backups[:10]:  # Show latest 10
                row = ctk.CTkFrame(self.backup_list, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    row,
                    text=backup['filename'],
                    width=200,
                    anchor="w"
                ).pack(side="left")

                ctk.CTkLabel(
                    row,
                    text=backup['modified'].strftime('%d-%b-%Y %H:%M'),
                    width=150
                ).pack(side="left")

                ctk.CTkButton(
                    row,
                    text="Restore",
                    width=70,
                    height=25,
                    fg_color="orange",
                    command=lambda p=backup['path']: self._restore_specific(p)
                ).pack(side="right")
        else:
            ctk.CTkLabel(
                self.backup_list,
                text="No backups found",
                text_color="gray"
            ).pack(pady=20)

    def _do_backup(self):
        """Perform manual backup"""
        result = self.backup_service.create_backup(manual=True)

        if result['success']:
            messagebox.showinfo(
                "Backup Complete",
                f"Backup created successfully!\n\nSaved to: {result['backup_path']}"
            )
            self._refresh_backup_status()
        else:
            messagebox.showerror(
                "Backup Failed",
                f"Failed to create backup:\n{result.get('error', 'Unknown error')}"
            )

    def _restore_backup(self):
        """Restore from backup file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db")],
            title="Select backup file to restore"
        )

        if filename:
            self._restore_specific(filename)

    def _restore_specific(self, path: str):
        """Restore from specific backup"""
        if messagebox.askyesno(
            "Confirm Restore",
            "This will replace all current data with the backup.\n\nAre you sure you want to continue?"
        ):
            result = self.backup_service.restore_backup(path)

            if result['success']:
                messagebox.showinfo(
                    "Restore Complete",
                    "Database restored successfully!\n\nPlease restart the application."
                )
            else:
                messagebox.showerror(
                    "Restore Failed",
                    f"Failed to restore:\n{result.get('error', 'Unknown error')}"
                )

    def refresh(self):
        """Refresh settings"""
        self._load_company()
        self._refresh_backup_status()
