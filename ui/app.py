"""Main application window"""
import customtkinter as ctk
from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, THEME


class App(ctk.CTk):
    """Main application window with navigation"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(APP_NAME)
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

        # Current active frame
        self.current_frame = None

        # Show dashboard by default
        self.show_frame("dashboard")

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
            ("Invoices", "invoices", 3),
            ("Credit Notes", "credit_notes", 4),
            ("Products", "products", 5),
            ("Customers", "customers", 6),
            ("Reports", "reports", 7),
            ("Settings", "settings", 8),
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
        self.backup_btn.grid(row=11, column=0, padx=10, pady=(5, 20), sticky="ew")

    def _create_content_area(self):
        """Create main content area"""
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Import frames here to avoid circular imports
        from .dashboard import DashboardFrame
        from .billing import BillingFrame
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


def run_app():
    """Initialize database and run the application"""
    from database.db import init_db

    # Initialize database
    init_db()

    # Create and run app
    app = App()
    app.mainloop()
