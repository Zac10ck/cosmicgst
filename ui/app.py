"""Main application window"""
import customtkinter as ctk
from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, THEME


class App(ctk.CTk):
    """Main application window with navigation"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1000, 600)

        # Set theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create navigation sidebar
        self._create_sidebar()

        # Create main content area
        self._create_content_area()

        # Initialize email processor
        self._init_email_processor()

        # Current active frame
        self.current_frame = None

        # Show dashboard by default
        self.show_frame("dashboard")

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_sidebar(self):
        """Create left sidebar with navigation buttons"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # App title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=APP_NAME,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Navigation buttons
        nav_items = [
            ("Dashboard", "dashboard", 1),
            ("New Bill", "billing", 2),
            ("Quotations", "quotations", 3),
            ("Invoices", "invoices", 4),
            ("Credit Notes", "credit_notes", 5),
            ("Products", "products", 6),
            ("Customers", "customers", 7),
            ("Reports", "reports", 8),
            ("Settings", "settings", 9),
        ]

        self.nav_buttons = {}

        for text, frame_name, row in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=ctk.CTkFont(size=14),
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=lambda f=frame_name: self.show_frame(f)
            )
            btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons[frame_name] = btn

        # Backup button at bottom
        self.backup_btn = ctk.CTkButton(
            self.sidebar,
            text="Backup Now",
            font=ctk.CTkFont(size=12),
            height=35,
            fg_color="green",
            hover_color="darkgreen",
            command=self._do_backup
        )
        self.backup_btn.grid(row=11, column=0, padx=10, pady=(5, 10), sticky="ew")

        # Email status indicator
        self.email_status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.email_status_frame.grid(row=12, column=0, padx=10, pady=(0, 20), sticky="ew")

        self.email_status_label = ctk.CTkLabel(
            self.email_status_frame,
            text="Email: --",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.email_status_label.pack(anchor="w")

    def _create_content_area(self):
        """Create main content area"""
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Import frames here to avoid circular imports
        from .dashboard import DashboardFrame
        from .billing import BillingFrame
        from .quotations import QuotationsFrame
        from .invoices import InvoicesFrame
        from .credit_notes import CreditNotesFrame
        from .products import ProductsFrame
        from .customers import CustomersFrame
        from .reports import ReportsFrame
        from .settings import SettingsFrame

        # Create all frames
        self.frames = {
            "dashboard": DashboardFrame(self.content_frame, self),
            "billing": BillingFrame(self.content_frame, self),
            "quotations": QuotationsFrame(self.content_frame, self),
            "invoices": InvoicesFrame(self.content_frame, self),
            "credit_notes": CreditNotesFrame(self.content_frame, self),
            "products": ProductsFrame(self.content_frame, self),
            "customers": CustomersFrame(self.content_frame, self),
            "reports": ReportsFrame(self.content_frame, self),
            "settings": SettingsFrame(self.content_frame, self),
        }

        # Place all frames in same location
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name: str):
        """Show a specific frame and update navigation"""
        # Update button colors
        for name, btn in self.nav_buttons.items():
            if name == frame_name:
                btn.configure(
                    fg_color=("gray75", "gray25"),
                    text_color=("gray10", "gray90")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray10", "gray90")
                )

        # Show frame
        frame = self.frames.get(frame_name)
        if frame:
            self.current_frame = frame
            frame.tkraise()

            # Refresh frame data if it has a refresh method
            if hasattr(frame, 'refresh'):
                frame.refresh()

    def _do_backup(self):
        """Perform manual backup"""
        from services.backup_service import BackupService
        from tkinter import messagebox

        backup = BackupService()
        result = backup.create_backup(manual=True)

        if result['success']:
            messagebox.showinfo(
                "Backup Complete",
                f"Backup created successfully!\n\nSaved to: {result['backup_path']}"
            )
        else:
            messagebox.showerror(
                "Backup Failed",
                f"Failed to create backup:\n{result.get('error', 'Unknown error')}"
            )

    def _init_email_processor(self):
        """Initialize background email queue processor"""
        try:
            from services.email_queue_processor import EmailQueueProcessor

            self.email_processor = EmailQueueProcessor(self)
            self.email_processor.set_callback('on_queue_processed', self._on_queue_processed)
            self.email_processor.set_callback('on_connection_status_changed', self._on_connection_changed)
            self.email_processor.start()

            # Initial status update
            self._update_email_status()
        except Exception as e:
            print(f"Failed to initialize email processor: {e}")
            self.email_processor = None

    def _update_email_status(self):
        """Update email status indicator"""
        try:
            if self.email_processor:
                status = self.email_processor.get_status()
                connection = "Online" if status['online'] else "Offline"
                pending = status['pending']

                if pending > 0:
                    text = f"Email: {connection} ({pending} pending)"
                else:
                    text = f"Email: {connection}"

                color = "green" if status['online'] else "gray"
                self.email_status_label.configure(text=text, text_color=color)
        except Exception:
            pass

    def _on_queue_processed(self, result):
        """Handle queue processing complete"""
        self._update_email_status()

        # Show notification if emails were sent
        if result.get('sent', 0) > 0:
            from tkinter import messagebox
            messagebox.showinfo(
                "Emails Sent",
                f"Successfully sent {result['sent']} email(s)."
            )

    def _on_connection_changed(self, is_online):
        """Handle connection status change"""
        self._update_email_status()

    def _on_close(self):
        """Handle window close - cleanup resources"""
        try:
            if hasattr(self, 'email_processor') and self.email_processor:
                self.email_processor.stop()
        except Exception:
            pass

        self.destroy()


def run_app():
    """Initialize database and run the application"""
    from database.db import init_db

    # Initialize database
    init_db()

    # Create and run app
    app = App()
    app.mainloop()
