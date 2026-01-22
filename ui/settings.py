"""Settings screen"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from database.models import Company, AppSettings
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
        self.tabview.add("Email")
        self.tabview.add("Backup")
        self.tabview.add("About")

        self._create_company_tab()
        self._create_email_tab()
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

    def _create_email_tab(self):
        """Create email settings tab"""
        tab = self.tabview.tab("Email")

        # Scrollable form
        form = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=10)

        # Enable Email
        self.email_enabled_var = ctk.BooleanVar()
        ctk.CTkCheckBox(
            form,
            text="Enable Email Notifications",
            variable=self.email_enabled_var,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 20))

        # Sender Configuration Section
        ctk.CTkLabel(
            form,
            text="Sender Configuration (Gmail)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(form, text="Gmail Address").pack(anchor="w", pady=(10, 5))
        self.sender_email_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.sender_email_var, width=400,
                     placeholder_text="your.email@gmail.com").pack(anchor="w")

        ctk.CTkLabel(form, text="App Password").pack(anchor="w", pady=(15, 5))
        self.app_password_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.app_password_var, width=400,
                     show="*", placeholder_text="16-character app password").pack(anchor="w")

        # Help text for app password
        help_text = ctk.CTkLabel(
            form,
            text="Get App Password: Google Account > Security > 2-Step Verification > App passwords",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        help_text.pack(anchor="w", pady=(2, 0))

        # Recipient Section
        ctk.CTkLabel(
            form,
            text="Recipient",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(25, 5))

        ctk.CTkLabel(form, text="Send invoices to").pack(anchor="w", pady=(10, 5))
        self.recipient_email_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.recipient_email_var, width=400,
                     placeholder_text="accounting@yourcompany.com").pack(anchor="w")

        # Options Section
        ctk.CTkLabel(
            form,
            text="Options",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(25, 5))

        self.auto_send_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form,
            text="Auto-send email when invoice is created",
            variable=self.auto_send_var
        ).pack(anchor="w", pady=(10, 5))

        # Buttons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=30)

        ctk.CTkButton(
            btn_frame,
            text="Test Connection",
            command=self._test_email_connection,
            fg_color="gray"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Save Email Settings",
            command=self._save_email_settings
        ).pack(side="left")

        # Queue Status Section
        ctk.CTkLabel(
            form,
            text="Email Queue Status",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(20, 10))

        self.queue_status_frame = ctk.CTkFrame(form)
        self.queue_status_frame.pack(fill="x", pady=10)

        self.queue_status_label = ctk.CTkLabel(
            self.queue_status_frame,
            text="Checking queue status..."
        )
        self.queue_status_label.pack(pady=10)

        queue_btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        queue_btn_frame.pack(anchor="w", pady=10)

        ctk.CTkButton(
            queue_btn_frame,
            text="Process Queue Now",
            command=self._process_email_queue,
            fg_color="green"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            queue_btn_frame,
            text="Refresh Status",
            command=self._refresh_email_queue_status
        ).pack(side="left")

        # Load settings
        self._load_email_settings()
        self._refresh_email_queue_status()

    def _load_email_settings(self):
        """Load email settings from database"""
        self.email_enabled_var.set(AppSettings.get('email_enabled', 'false') == 'true')
        self.sender_email_var.set(AppSettings.get('email_sender_address', ''))
        self.app_password_var.set(AppSettings.get('email_app_password', ''))
        self.recipient_email_var.set(AppSettings.get('email_recipient', ''))
        self.auto_send_var.set(AppSettings.get('email_auto_send', 'true') == 'true')

    def _save_email_settings(self):
        """Save email settings to database"""
        # Validate sender email
        sender = self.sender_email_var.get().strip()
        if sender:
            valid, error = validate_email(sender)
            if not valid:
                messagebox.showerror("Error", f"Sender email: {error}")
                return

        # Validate recipient email
        recipient = self.recipient_email_var.get().strip()
        if recipient:
            valid, error = validate_email(recipient)
            if not valid:
                messagebox.showerror("Error", f"Recipient email: {error}")
                return

        # Save settings
        AppSettings.set('email_enabled', 'true' if self.email_enabled_var.get() else 'false')
        AppSettings.set('email_sender_address', sender)
        AppSettings.set('email_app_password', self.app_password_var.get())
        AppSettings.set('email_recipient', recipient)
        AppSettings.set('email_auto_send', 'true' if self.auto_send_var.get() else 'false')

        messagebox.showinfo("Success", "Email settings saved successfully!")

    def _test_email_connection(self):
        """Test email connection"""
        # Save current settings first
        sender = self.sender_email_var.get().strip()
        password = self.app_password_var.get()

        if not sender or not password:
            messagebox.showerror("Error", "Please enter Gmail address and App Password first.")
            return

        # Save temporarily for testing
        AppSettings.set('email_sender_address', sender)
        AppSettings.set('email_app_password', password)

        # Test connection
        try:
            from services.email_service import EmailService
            email_service = EmailService()
            success, message = email_service.test_connection()

            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Connection Failed", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test connection: {str(e)}")

    def _refresh_email_queue_status(self):
        """Refresh email queue status display"""
        try:
            from services.email_queue_service import EmailQueueService
            from services.network_service import NetworkService

            queue_service = EmailQueueService()
            network_service = NetworkService()

            status = queue_service.get_queue_status()
            is_online = network_service.is_online()

            connection_status = "Online" if is_online else "Offline"
            connection_color = "green" if is_online else "red"

            status_text = (
                f"Connection: {connection_status}  |  "
                f"Pending: {status['pending']}  |  "
                f"Failed: {status['failed']}  |  "
                f"Sent: {status['sent']}"
            )

            self.queue_status_label.configure(text=status_text)
        except Exception as e:
            self.queue_status_label.configure(text=f"Error loading status: {str(e)}")

    def _process_email_queue(self):
        """Process email queue manually"""
        try:
            from services.email_queue_service import EmailQueueService
            from services.network_service import NetworkService

            network_service = NetworkService()
            if not network_service.is_online():
                messagebox.showwarning("Offline", "Cannot process queue - no internet connection.")
                return

            queue_service = EmailQueueService()
            result = queue_service.process_queue()

            message = f"Queue processed:\n\nSent: {result['sent']}\nFailed: {result['failed']}\nRemaining: {result['remaining']}"
            messagebox.showinfo("Queue Processed", message)

            self._refresh_email_queue_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process queue: {str(e)}")

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
        self._load_email_settings()
        self._refresh_email_queue_status()
        self._refresh_backup_status()
