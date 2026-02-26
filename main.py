"""
📊 Haftalik Odatlar Kuzatuvchisi - Professional Habit Tracker
A comprehensive habit and task tracking application with data visualization.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging
import warnings
import io
from PIL import Image
import matplotlib
from matplotlib.figure import Figure

# Configure matplotlib before using
matplotlib.use('TkAgg')

# Suppress matplotlib warnings
warnings.filterwarnings('ignore')

# Configure logging to save to a file as well as output to console
log_file = Path("tracker_errors.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# THEME COLORS
LIGHT_MODE = {
    "bg": "#F4F6F9",
    "frame": "#FFFFFF",
    "text": "#333333",
    "accent": "#2FA572",
    "accent_light": "#A0D9C1",
    "border": "#E0E0E0",
    "error": "#E74C3C",
    "warning": "#F39C12",
    "success": "#27AE60"
}

DARK_MODE = {
    "bg": "#1a1a1a",
    "frame": "#2d2d2d",
    "text": "#E0E0E0",
    "accent": "#2FA572",
    "accent_light": "#A0D9C1",
    "border": "#404040",
    "error": "#E74C3C",
    "warning": "#F39C12",
    "success": "#27AE60"
}

DATA_FILE = Path("tracker_data.json")


class ThemeManager:
    """Manages application theme switching between light and dark modes."""
    
    def __init__(self):
        self.current_theme = "light"

    def get(self, key):
        """Get color value for current theme."""
        theme = LIGHT_MODE if self.current_theme == "light" else DARK_MODE
        return theme.get(key, "#000000")

    def toggle(self):
        """Toggle between light and dark theme."""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        logger.info(f"Theme changed to: {self.current_theme}")

    def is_dark(self):
        """Check if dark theme is active."""
        return self.current_theme == "dark"


class DataManager:
    """Handles all data persistence and operations."""
    
    @staticmethod
    def load_data():
        """Load data from JSON file."""
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
        return {}
    
    @staticmethod
    def save_data(data):
        """Save data to JSON file."""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Data saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False
    
    @staticmethod
    def get_week_start(date):
        """Get the start date of the week (Monday)."""
        return date - timedelta(days=date.weekday())
    
    @staticmethod
    def calculate_habit_completion_rate(daily_data, habit, week_start):
        """Calculate completion rate for a habit across the week."""
        completed = 0
        for i in range(7):
            date = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            if date in daily_data and habit in daily_data[date].get("habits", {}):
                if daily_data[date]["habits"][habit]:
                    completed += 1
        return (completed / 7) * 100


class TrackerApp(ctk.CTk):
    """Main habit tracking application."""
    
    def __init__(self):
        super().__init__()
        self.title("📊 Haftalik Odatlar Kuzatuvchisi - Professional Tracker")
        
        # Ekran o'lchamlarini olish va to'liq ekran qilish
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.minsize(1000, 700)
        
        # Oynani to'liq ekranda ochish (Maximize window)
        try:
            self.state('zoomed')
            # CustomTkinter da ishonchli ishlashi uchun biroz kechikish bilan ham chaqiramiz
            self.after(200, lambda: self.state('zoomed'))
        except Exception as e:
            logger.error(f"Maximize error: {e}")
            
        ctk.set_appearance_mode("light")

        # Suppress benign Tkinter errors that happen during widget destruction
        import tkinter
        def custom_exception_handler(exc, val, tb):
            if isinstance(val, tkinter.TclError) and "bad window path name" in str(val):
                pass
            else:
                import traceback
                # Format the traceback and log it to our file instead of just printing
                error_msg = "".join(traceback.format_exception(exc, val, tb))
                logger.error(f"Uncatched Tkinter Exception:\n{error_msg}")
        self.report_callback_exception = custom_exception_handler

        self.theme = ThemeManager()
        
        # Load data
        stored_data = DataManager.load_data()
        self.daily_data = stored_data.get('daily_data', {})
        self.habits = stored_data.get('habits', [
            "Erta uyg'onish",
            "Shirnitik yemashlik",
            "Sovuq dush",
            "O'qish",
            "Gym",
            "Kod yozish",
            "Ingliz tili"
        ])
        self.task_templates = stored_data.get('task_templates', ["Vazifa 1", "Vazifa 2", "Vazifa 3", "Vazifa 4", "Vazifa 5"])
        
        self.week_start_date = DataManager.get_week_start(datetime.now())
        self.initialize_week_data()

        # UI elements store
        self.week_charts = {}
        self.week_image_labels = {}
        self.bar_chart_fig = None
        self.bar_chart_image_label = None
        self.weekly_overall_chart_fig = None
        self.weekly_overall_chart_image_label = None
        self.daily_stats_labels = {}
        self.habit_vars = {}
        self.habit_progress_labels = {}
        self.habit_progress_bars = {}
        self.weekly_percent_label = None
        self.weekly_stats_containers = {}

        self.setup_ui()
        
        # Lazy load charts to significantly improve startup time
        logger.info("UI structure created, deferring chart generation...")
        self.after(100, self.update_all_charts)

    def initialize_week_data(self):
        """Initialize data structure for all days in the week."""
        for i in range(7):
            date = (self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            if date not in self.daily_data:
                self.daily_data[date] = {
                    "tasks": self.task_templates.copy(),
                    "task_status": {t: False for t in self.task_templates},
                    "habits": {h: False for h in self.habits}
                }
            else:
                # Ensure all habits are in the data
                for habit in self.habits:
                    if habit not in self.daily_data[date]["habits"]:
                        self.daily_data[date]["habits"][habit] = False

    def save_data(self):
        """Save current application state to file."""
        data = {
            'daily_data': self.daily_data,
            'habits': self.habits,
            'task_templates': self.task_templates
        }
        DataManager.save_data(data)

    def setup_ui(self):
        """Setup main UI layout with professional structure."""
        try:
            main = ctk.CTkScrollableFrame(self, fg_color="transparent")
            main.pack(fill="both", expand=True, padx=15, pady=15)

            # === TOP: HEADER ===
            self.create_header(main)

            # === SECTION 1: OVERALL GROWTH BAR CHART (Full width) ===
            self.create_bar_chart_section(main)

            # === SECTION 2: HABITS TRACKER (Full width, directly below growth) ===
            self.create_habits_section(main)

            # === SECTION 3: DAILY INDICATORS (Donuts) ===
            self.create_weekly_donuts_section(main)

            # === SECTION 4: DAILY TASKS (Below indicators) ===
            self.create_daily_tasks_section(main)

            # === FOOTER: Add items ===
            self.create_add_items_section(main)
        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Kritik Xatolik", f"Dastur interfeysini qurishda xatolik yuz berdi. Dasturni qayta pusk qiling. Xato: {e}")

    def create_header(self, parent):
        """Create professional header with title and controls."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        # Left side: Title and info
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left, text="📊 Haftalik Odatlar Kuzatuvchisi",
            font=("Helvetica", 40, "bold"),
            text_color=self.theme.get("accent")
        ).pack(anchor="w")

        ctk.CTkLabel(
            left, text="Professional Habit Tracking Dashboard",
            font=("Helvetica", 18),
            text_color=self.theme.get("text")
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            left, text="👨‍💻 Dasturchi: Valijon Ergashev | 📞 Tel: +998 77 342 33 21",
            font=("Helvetica", 14, "italic"),
            text_color=self.theme.get("text")
        ).pack(anchor="w", pady=(2, 0))

        # Right side: Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="📥 Excel ga yuklash", width=160, height=50,
            font=("Helvetica", 14, "bold"),
            fg_color=self.theme.get("accent"),
            hover_color=self.theme.get("accent_light"),
            command=self.export_to_excel
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🌙 Mavzu", width=120, height=50,
            font=("Helvetica", 14, "bold"),
            fg_color=self.theme.get("accent"),
            hover_color=self.theme.get("accent_light"),
            command=self.toggle_theme_action
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="💾 Saqlash", width=120, height=50,
            font=("Helvetica", 14, "bold"),
            fg_color=self.theme.get("accent"),
            hover_color=self.theme.get("accent_light"),
            command=self.save_data
        ).pack(side="left", padx=5)

    def create_weekly_donuts_section(self, parent):
        """Create weekly donut charts showing daily task completion."""
        frame = ctk.CTkFrame(parent, fg_color=self.theme.get("frame"), corner_radius=12,
                           border_width=2, border_color=self.theme.get("border"))
        frame.pack(fill="both", expand=True, padx=0, pady=15)

        ctk.CTkLabel(
            frame, text="📊 Kunlik Ko'rsatkichlar",
            font=("Helvetica", 18, "bold"),
            text_color=self.theme.get("accent")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        charts_container = ctk.CTkScrollableFrame(frame, fg_color="transparent", orientation="horizontal", height=240)
        charts_container.pack(fill="both", expand=True, padx=10, pady=10)

        days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]

        for i in range(7):
            date = (self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            day = days_uz[i]

            # Day box
            day_box = ctk.CTkFrame(
                charts_container, fg_color=self.theme.get("bg"),
                corner_radius=10, border_width=2,
                border_color=self.theme.get("border"),
                width=220
            )
            day_box.pack(side="left", fill="y", expand=False, padx=6, pady=4)
            day_box.pack_propagate(False)

            # Header frame to match Daily Tasks
            header_frame = ctk.CTkFrame(day_box, fg_color="transparent")
            header_frame.pack(fill="x", padx=8, pady=(8, 6))

            # Date label
            ctk.CTkLabel(
                header_frame, text=f"{day}\n{date}",
                font=("Helvetica", 12, "bold"),
                text_color=self.theme.get("accent")
            ).pack(side="left", expand=True)

            # Mini donut chart
            fig = Figure(figsize=(2, 2), dpi=100)
            ax = fig.add_subplot(111)
            fig.patch.set_facecolor(self.theme.get("bg"))
            self.week_charts[date] = (fig, ax)

            # Image Label to avoid TkCanvas scrolling bugs
            lbl = ctk.CTkLabel(day_box, text="")
            lbl.pack(fill="both", expand=True, padx=3, pady=3)
            self.week_image_labels[date] = lbl

    def create_bar_chart_section(self, parent):
        """Create bar chart showing overall weekly progress with weekly stats side by side."""
        # Main container for both bar chart and weekly stats
        main_container = ctk.CTkFrame(parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, pady=15)

        # LEFT SIDE: BAR CHART (50% width)
        left_frame = ctk.CTkFrame(
            main_container, fg_color=self.theme.get("frame"),
            corner_radius=12, border_width=2,
            border_color=self.theme.get("border"),
            width=700, height=280
        )
        left_frame.pack(side="left", fill="none", expand=False, padx=(0, 8))
        left_frame.pack_propagate(False)

        ctk.CTkLabel(
            left_frame, text="📈 Umumiy O'sish",
            font=("Helvetica", 16, "bold"),
            text_color=self.theme.get("accent")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Calculate actual completion rates
        days = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya']
        completed_counts = []

        for i in range(7):
            date = (self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self.daily_data:
                tasks = self.daily_data[date]["tasks"]
                completed = sum(1 for t in tasks if self.daily_data[date]["task_status"].get(t, False))
                total = len(tasks) if tasks else 1
                percent = int((completed / total) * 100)
            else:
                percent = 0
            completed_counts.append(percent)

        # Create bar chart
        fig = Figure(figsize=(7, 3.5), dpi=100)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(self.theme.get("frame"))
        
        bars = ax.bar(days, completed_counts, color=self.theme.get("accent"), 
                     alpha=0.85, edgecolor=self.theme.get("accent_light"), linewidth=2)
        
        ax.set_ylim(0, 110)
        ax.set_ylabel("Foiz (%)", fontsize=12, fontweight='bold')
        ax.set_xlabel("Hafta kunlari", fontsize=12, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.theme.get("border"))
        ax.spines['bottom'].set_color(self.theme.get("border"))
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Add percentage labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{int(height)}%', ha='center', va='bottom', 
                    fontsize=11, fontweight='bold', color=self.theme.get("accent"))

        ax.set_facecolor(self.theme.get("frame"))
        self.bar_chart_fig = fig
        
        # Image Label to avoid TkCanvas scrolling bugs
        self.bar_chart_image_label = ctk.CTkLabel(left_frame, text="")
        self.bar_chart_image_label.pack(fill="both", expand=True, padx=10, pady=10)

        # RIGHT SIDE: WEEKLY STATS (50% width)
        right_frame = ctk.CTkFrame(
            main_container, fg_color=self.theme.get("frame"),
            corner_radius=15, border_width=2,
            border_color=self.theme.get("border"),
            width=700, height=270
        )
        right_frame.pack(side="right", fill="none", expand=False, padx=(8, 0))
        right_frame.pack_propagate(False)

        ctk.CTkLabel(
            right_frame, text="📊 Haftalik Vazifalar",
            font=("Helvetica", 18, "bold"),
            text_color=self.theme.get("accent")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Calculate overall weekly stats
        total_tasks = 0
        completed_tasks = 0
        for i in range(7):
            date = (self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self.daily_data:
                tasks = self.daily_data[date]["tasks"]
                total_tasks += len(tasks)
                completed_tasks += sum(1 for t in tasks if self.daily_data[date]["task_status"].get(t, False))

        weekly_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        # Big circular progress display
        stats_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        stats_container.pack(fill="both", expand=True, padx=15, pady=0)

        # Overall percentage in a circular donut chart
        self.weekly_overall_chart_fig = Figure(figsize=(2, 2), dpi=100)
        self.weekly_overall_chart_fig.patch.set_facecolor(self.theme.get("frame"))
        
        self.weekly_overall_chart_image_label = ctk.CTkLabel(stats_container, text="")
        self.weekly_overall_chart_image_label.pack(pady=(10, 5))

        # Completed/Total count
        self.weekly_tasks_count_label = ctk.CTkLabel(
            stats_container, text=f"{completed_tasks} / {total_tasks} Bajarildi",
            font=("Helvetica", 20, "bold"),
            text_color=self.theme.get("text")
        )
        self.weekly_tasks_count_label.pack(pady=10)

        # Store references for updates
        self.weekly_percent_label = ctk.CTkLabel(
            stats_container, text="Haftalik Umumiy Natija",
            font=("Helvetica", 16),
            text_color=self.theme.get("accent")
        )
        self.weekly_percent_label.pack(pady=10)
        self.weekly_stats_containers = {"completed": completed_tasks, "total": total_tasks}

    def create_habits_section(self, parent):
        """Create comprehensive habits tracker section below overall growth."""
        frame = ctk.CTkFrame(
            parent, fg_color=self.theme.get("frame"),
            corner_radius=12, border_width=2,
            border_color=self.theme.get("border")
        )
        frame.pack(fill="both", expand=True, pady=15)

        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header_frame, text="🎯 Odatlar Kuzatuvchisi (Haftalik Ko'rsatkichlar)",
            font=("Helvetica", 16, "bold"),
            text_color=self.theme.get("accent")
        ).pack(side="left")

        ctk.CTkButton(
            header_frame, text="🗑️ Barchasini tozalash", width=150, height=32,
            font=("Helvetica", 13, "bold"),
            fg_color=self.theme.get("error"),
            hover_color="#c0392b",
            command=self.clear_all_habits
        ).pack(side="left", padx=(15, 0))

        # Right-aligned inline input area
        input_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        input_container.pack(side="right")

        self.inline_habit_entry = ctk.CTkEntry(
            input_container, placeholder_text="Yangi odat...",
            font=("Helvetica", 13), height=32, width=350
        )
        self.inline_habit_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            input_container, text="➕ Qo'shish", width=100, height=32,
            font=("Helvetica", 13, "bold"),
            fg_color=self.theme.get("accent"),
            hover_color=self.theme.get("accent_light"),
            command=self.add_habit_inline
        ).pack(side="left")

        # Scrollable habits container
        self.habits_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.habits_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        self.populate_habits_list()

    def populate_habits_list(self):
        for widget in self.habits_scroll.winfo_children():
            widget.destroy()

        # Header row
        header = ctk.CTkFrame(self.habits_scroll, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(0, 12))

        ctk.CTkLabel(
            header, text="Odatlar", width=200,
            font=("Helvetica", 14, "bold"),
            text_color=self.theme.get("accent")
        ).pack(side="left", padx=5)

        days_uz = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
        for day in days_uz:
            ctk.CTkLabel(
                header, text=day, width=40,
                font=("Helvetica", 13, "bold"),
                text_color=self.theme.get("accent")
            ).pack(side="left", padx=10)

        ctk.CTkLabel(
            header, text="Jarayon", width=300,
            font=("Helvetica", 14, "bold"),
            text_color=self.theme.get("accent")
        ).pack(side="left", padx=5)

        # Habit rows
        self.habit_vars = {}
        self.habit_progress_labels = {}
        self.habit_progress_bars = {}

        for h_idx, habit in enumerate(self.habits):
            row = ctk.CTkFrame(self.habits_scroll, fg_color=self.theme.get("bg"), corner_radius=8)
            row.pack(fill="x", padx=5, pady=6)

            actions_frame = ctk.CTkFrame(row, fg_color="transparent")
            actions_frame.pack(side="left", padx=(8, 0), pady=10)

            ctk.CTkButton(
                actions_frame, text="✎", width=25, height=25,
                font=("Helvetica", 14), fg_color="transparent",
                text_color=self.theme.get("accent"), hover_color=self.theme.get("bg"),
                command=lambda h=habit: self.edit_habit(h)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_frame, text="🗑️", width=25, height=25,
                font=("Helvetica", 14), fg_color="transparent",
                text_color=self.theme.get("error"), hover_color=self.theme.get("bg"),
                command=lambda h=habit: self.delete_habit(h)
            ).pack(side="left", padx=2)

            # Habit name
            display_name = habit if len(habit) <= 18 else habit[:15] + "..."
            ctk.CTkLabel(
                row, text=display_name, width=140, anchor="w",
                font=("Helvetica", 13),
                text_color=self.theme.get("text")
            ).pack(side="left", padx=(5, 8), pady=10)

            # Checkboxes for each day
            row_vars = {}
            for d_idx in range(7):
                date = (self.week_start_date + timedelta(days=d_idx)).strftime("%Y-%m-%d")
                var = ctk.IntVar(value=self.daily_data[date]["habits"].get(habit, False))

                cb = ctk.CTkCheckBox(
                    row, text="", variable=var, width=25,
                    fg_color=self.theme.get("accent"),
                    hover_color=self.theme.get("accent_light"),
                    checkmark_color=self.theme.get("frame"),
                    command=lambda h=habit, d=date, v=var: self.update_habit(h, d, v)
                )
                cb.pack(side="left", padx=7, pady=10)
                row_vars[d_idx] = var

            self.habit_vars[h_idx] = row_vars

            # Progress section with larger components
            progress_frame = ctk.CTkFrame(row, fg_color="transparent", width=220)
            progress_frame.pack(side="left", padx=8, pady=10)

            prog_bar = ctk.CTkProgressBar(
                progress_frame, width=200, height=20,
                fg_color=self.theme.get("border"),
                progress_color=self.theme.get("accent")
            )
            prog_bar.pack(side="left", padx=5)
            prog_bar.set(0)
            self.habit_progress_bars[h_idx] = prog_bar

            prog_lbl = ctk.CTkLabel(
                progress_frame, text="0%", width=50,
                font=("Helvetica", 14, "bold"),
                text_color=self.theme.get("accent")
            )
            prog_lbl.pack(side="left", padx=8)
            self.habit_progress_labels[h_idx] = prog_lbl

    def create_daily_tasks_section(self, parent):
        """Create daily tasks section showing task breakdown for each day."""
        frame = ctk.CTkFrame(
            parent, fg_color=self.theme.get("frame"),
            corner_radius=12, border_width=2,
            border_color=self.theme.get("border")
        )
        frame.pack(fill="both", expand=True, padx=0, pady=15)

        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header_frame, text="✅ Kunlik Vazifalar",
            font=("Helvetica", 16, "bold"),
            text_color=self.theme.get("accent")
        ).pack(side="left")

        ctk.CTkButton(
            header_frame, text="🗑️ Barchasini tozalash", width=150, height=32,
            font=("Helvetica", 13, "bold"),
            fg_color=self.theme.get("error"),
            hover_color="#c0392b",
            command=self.clear_all_tasks
        ).pack(side="left", padx=(15, 0))

        # Days container
        self.tasks_days_container = ctk.CTkScrollableFrame(frame, fg_color="transparent", orientation="horizontal", height=240)
        self.tasks_days_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.populate_tasks_list()

    def populate_tasks_list(self):
        for widget in self.tasks_days_container.winfo_children():
            widget.destroy()

        days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]

        self.daily_stats_labels = {}

        for d_idx in range(7):
            date = (self.week_start_date + timedelta(days=d_idx)).strftime("%Y-%m-%d")
            day = days_uz[d_idx]

            day_frame = ctk.CTkFrame(
                self.tasks_days_container, fg_color=self.theme.get("bg"),
                corner_radius=10, border_width=1,
                border_color=self.theme.get("border"),
                width=220
            )
            day_frame.pack(side="left", fill="y", expand=False, padx=6, pady=4)
            day_frame.pack_propagate(False)

            # Header with tiny '+' button for Day-Specific task
            header_frame = ctk.CTkFrame(day_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=8, pady=(8, 6))

            ctk.CTkLabel(
                header_frame, text=f"{day}\n{date}",
                font=("Helvetica", 12, "bold"),
                text_color=self.theme.get("accent")
            ).pack(side="left", expand=True)

            ctk.CTkButton(
                header_frame, text="+", width=25, height=25,
                font=("Helvetica", 16, "bold"), fg_color="transparent",
                text_color=self.theme.get("accent"), hover_color=self.theme.get("border"),
                command=lambda d=date: self.add_task_to_day(d)
            ).pack(side="right")

            # Tasks
            tasks_scroll = ctk.CTkScrollableFrame(day_frame, fg_color="transparent", height=150)
            tasks_scroll.pack(fill="both", expand=True, padx=5, pady=5)

            for task in self.daily_data[date]["tasks"]:
                task_row = ctk.CTkFrame(tasks_scroll, fg_color="transparent")
                task_row.pack(anchor="w", padx=4, pady=2, fill="x")

                var = ctk.IntVar(value=self.daily_data[date]["task_status"].get(task, False))

                # Truncate string to avoid pushing buttons out of view
                display_task = task if len(task) <= 18 else task[:15] + "..."

                cb = ctk.CTkCheckBox(
                    task_row, text=display_task, variable=var,
                    font=("Helvetica", 11),
                    fg_color=self.theme.get("accent"),
                    hover_color=self.theme.get("accent_light"),
                    text_color=self.theme.get("text"),
                    command=lambda t=task, d=date, v=var: self.update_task(t, d, v)
                )
                cb.pack(side="left", expand=True, fill="x")

                ctk.CTkButton(
                    task_row, text="🗑️", width=20, height=20,
                    font=("Helvetica", 10), fg_color="transparent",
                    text_color=self.theme.get("error"), hover=False,
                    command=lambda t=task, d=date: self.delete_task(t, d)
                ).pack(side="right", padx=1)

                ctk.CTkButton(
                    task_row, text="✎", width=20, height=20,
                    font=("Helvetica", 10), fg_color="transparent",
                    text_color=self.theme.get("accent"), hover=False,
                    command=lambda t=task, d=date: self.edit_task(t, d)
                ).pack(side="right", padx=1)

            # Stats
            stats_lbl = ctk.CTkLabel(
                day_frame, text="",
                font=("Helvetica", 12, "bold"),
                text_color=self.theme.get("accent")
            )
            stats_lbl.pack(padx=5, pady=(6, 8))
            self.daily_stats_labels[date] = stats_lbl

    def create_add_items_section(self, parent):
        """Create input section for adding new habits and tasks."""
        frame = ctk.CTkFrame(
            parent, fg_color=self.theme.get("frame"),
            corner_radius=12, border_width=2,
            border_color=self.theme.get("border")
        )
        frame.pack(fill="x", pady=15)

        ctk.CTkLabel(
            frame, text="➕ Yangi Qo'shish",
            font=("Helvetica", 18, "bold"),
            text_color=self.theme.get("accent")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.add_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Odatlar yoki vazifa nomini kiriting...",
            font=("Helvetica", 13), height=50
        )
        self.add_entry.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkButton(
            input_frame, text="➕ Odatlar", width=150, height=50,
            font=("Helvetica", 14, "bold"),
            fg_color=self.theme.get("accent"),
            hover_color=self.theme.get("accent_light"),
            command=self.add_habit_global
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            input_frame, text="➕ Vazifa", width=150, height=50,
            font=("Helvetica", 14, "bold"),
            fg_color=self.theme.get("accent"),
            hover_color=self.theme.get("accent_light"),
            command=self.add_task_template
        ).pack(side="left", padx=5)

    def update_habit(self, habit, date, var):
        """Update habit status and refresh charts."""
        status = bool(var.get())
        self.daily_data[date]["habits"][habit] = status
        logger.info(f"Odat holati o'zgardi (Habit toggled): '{habit}' sanada {date} -> {status}")
        self.update_all_charts()

    def update_task(self, task, date, var):
        """Update task status and refresh charts."""
        status = bool(var.get())
        self.daily_data[date]["task_status"][task] = status
        logger.info(f"Vazifa holati o'zgardi (Task toggled): '{task}' sanada {date} -> {status}")
        self.update_all_charts()

    def update_all_charts(self):
        """Update all visualizations with current data."""
        try:
            # Update daily donut charts
            for date, (fig, ax) in self.week_charts.items():
                if date not in self.daily_data:
                    continue
                tasks = self.daily_data[date]["tasks"]
                completed = sum(1 for t in tasks if self.daily_data[date]["task_status"].get(t, False))
                total = len(tasks) if tasks else 1
                percent = int((completed / total) * 100)

                ax.clear()
                colors = [self.theme.get("accent"), self.theme.get("border")]
                wedges, texts = ax.pie([completed, total - completed], colors=colors, 
                                       startangle=90, wedgeprops=dict(width=0.35, 
                                       edgecolor=self.theme.get("bg")))
                ax.text(0, 0, f"{percent}%", ha='center', va='center',
                        fontsize=11, fontweight='bold', color=self.theme.get("accent"))

                if date in self.week_image_labels:
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1, facecolor=fig.get_facecolor())
                    buf.seek(0)
                    img = Image.open(buf)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(170, 170))
                    self.week_image_labels[date].configure(image=ctk_img)
                    self.week_image_labels[date].image = ctk_img  # Prevent Garbage Collection

            # Update daily stats labels
            for date, lbl in self.daily_stats_labels.items():
                if date not in self.daily_data:
                    continue
                tasks = self.daily_data[date]["tasks"]
                completed = sum(1 for t in tasks if self.daily_data[date]["task_status"].get(t, False))
                total = len(tasks) if tasks else 0
                lbl.configure(text=f"✓ {completed}/{total}")

            # Update habit progress bars and labels
            for h_idx, habit in enumerate(self.habits):
                if h_idx not in self.habit_vars:
                    continue
                completed = sum(1 for d_idx in range(7) if d_idx in self.habit_vars[h_idx] and self.habit_vars[h_idx][d_idx].get())
                percent = int((completed / 7) * 100)

                if h_idx in self.habit_progress_bars:
                    self.habit_progress_bars[h_idx].set(percent / 100)

                if h_idx in self.habit_progress_labels:
                    self.habit_progress_labels[h_idx].configure(text=f"{percent}%")

            # Update overall growth bar chart
            self.update_bar_chart()
        except Exception as e:
            logger.error(f"Error updating charts: {e}")

    def update_bar_chart(self):
        """Update the overall growth bar chart with current data."""
        try:
            if self.bar_chart_fig is None or self.bar_chart_image_label is None:
                return

            days = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya']
            completed_counts = []

            for i in range(7):
                date = (self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                if date in self.daily_data:
                    tasks = self.daily_data[date]["tasks"]
                    completed = sum(1 for t in tasks if self.daily_data[date]["task_status"].get(t, False))
                    total = len(tasks) if tasks else 1
                    percent = int((completed / total) * 100)
                else:
                    percent = 0
                completed_counts.append(percent)

            ax = self.bar_chart_fig.axes[0]
            ax.clear()

            bars = ax.bar(days, completed_counts, color=self.theme.get("accent"), 
                         alpha=0.85, edgecolor=self.theme.get("accent_light"), linewidth=2)

            ax.set_ylim(0, 110)
            ax.set_ylabel("Foiz (%)", fontsize=12, fontweight='bold')
            ax.set_xlabel("Hafta kunlari", fontsize=12, fontweight='bold')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(self.theme.get("border"))
            ax.spines['bottom'].set_color(self.theme.get("border"))
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                        f'{int(height)}%', ha='center', va='bottom',
                        fontsize=11, fontweight='bold', color=self.theme.get("accent"))

            ax.set_facecolor(self.theme.get("frame"))
            
            buf = io.BytesIO()
            self.bar_chart_fig.savefig(buf, format="png", bbox_inches="tight", facecolor=self.bar_chart_fig.get_facecolor())
            buf.seek(0)
            img = Image.open(buf)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(600, 250))
            self.bar_chart_image_label.configure(image=ctk_img)
            self.bar_chart_image_label.image = ctk_img  # Prevent Garbage Collection
            
            # Update weekly stats if they exist
            if hasattr(self, 'weekly_percent_label'):
                total_tasks = 0
                completed_tasks = 0
                for i in range(7):
                    date = (self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                    if date in self.daily_data:
                        tasks = self.daily_data[date]["tasks"]
                        total_tasks += len(tasks)
                        completed_tasks += sum(1 for t in tasks if self.daily_data[date]["task_status"].get(t, False))
                
                weekly_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
                
                # Update the large generic label if it still exists (fallback), otherwise draw donut
                if hasattr(self, 'weekly_percent_large_label'):
                    self.weekly_percent_large_label.configure(text=f"{weekly_percent}%")
                    
                if getattr(self, 'weekly_overall_chart_fig', None) and getattr(self, 'weekly_overall_chart_image_label', None):
                    ax_overall = self.weekly_overall_chart_fig.add_subplot(111) if not self.weekly_overall_chart_fig.axes else self.weekly_overall_chart_fig.axes[0]
                    ax_overall.clear()
                    
                    colors = [self.theme.get("accent"), self.theme.get("border")]
                    comp_val = completed_tasks
                    rem_val = total_tasks - completed_tasks
                    if total_tasks == 0:
                        comp_val, rem_val = 0, 1
                        
                    ax_overall.pie([comp_val, rem_val], colors=colors, startangle=90, 
                                   wedgeprops=dict(width=0.3, edgecolor=self.theme.get("frame")))
                    ax_overall.text(0, 0, f"{weekly_percent}%", ha='center', va='center',
                                    fontsize=20, fontweight='bold', color=self.theme.get("accent"))
                    
                    buf2 = io.BytesIO()
                    self.weekly_overall_chart_fig.savefig(buf2, format="png", bbox_inches="tight", pad_inches=0, facecolor=self.theme.get("frame"))
                    buf2.seek(0)
                    img2 = Image.open(buf2)
                    ctk_img2 = ctk.CTkImage(light_image=img2, dark_image=img2, size=(160, 160))
                    self.weekly_overall_chart_image_label.configure(image=ctk_img2)
                    self.weekly_overall_chart_image_label.image = ctk_img2
                    
                if hasattr(self, 'weekly_tasks_count_label'):
                    self.weekly_tasks_count_label.configure(text=f"{completed_tasks} / {total_tasks} Bajarildi")
                
                # The labels will be updated through the refresh, but we store the data
                self.weekly_stats_containers = {"completed": completed_tasks, "total": total_tasks, "percent": weekly_percent}
        except Exception as e:
            logger.error(f"Error updating bar chart: {e}")

    def add_habit_global(self):
        """Add a new habit to the tracker."""
        text = self.add_entry.get().strip()
        if not text:
            logger.warning("Empty habit name provided")
            return
        
        if text in self.habits:
            logger.info(f"Habit '{text}' already exists")
            return
        
        self.habits.append(text)
        for date in self.daily_data:
            self.daily_data[date]["habits"][text] = False
        
        self.add_entry.delete(0, "end")
        logger.info(f"Added new habit: {text}")
        self.populate_habits_list()
        self.update_all_charts()

    def add_habit_inline(self):
        """Add a new habit directly from the inline entry."""
        new_habit = self.inline_habit_entry.get().strip()
        if new_habit:
            if new_habit in self.habits:
                logger.info(f"Habit '{new_habit}' already exists")
                return
            
            self.habits.append(new_habit)
            for date in self.daily_data:
                self.daily_data[date]["habits"][new_habit] = False
            
            logger.info(f"Added new inline habit: {new_habit}")
            self.inline_habit_entry.delete(0, "end")
            self.populate_habits_list()
            self.update_all_charts()

    def add_task_template(self):
        """Add a new task template to all days."""
        text = self.add_entry.get().strip()
        if not text:
            logger.warning("Empty task name provided")
            return
        
        if text in self.task_templates:
            logger.info(f"Task template '{text}' already exists")
            return
        
        self.task_templates.append(text)
        for date in self.daily_data:
            self.daily_data[date]["tasks"].append(text)
            self.daily_data[date]["task_status"][text] = False
        
        self.add_entry.delete(0, "end")
        logger.info(f"Added new task template: {text}")
        self.populate_tasks_list()
        self.update_all_charts()

    def add_task_to_day(self, date):
        """Add a specific task only to the selected day's dictionary."""
        dialog = ctk.CTkInputDialog(text=f"{date} uchun yangi vazifa:", title="Kunga Vazifa Qo'shish")
        new_task = dialog.get_input()
        if new_task and new_task.strip():
            new_task = new_task.strip()
            
            if new_task in self.daily_data[date]["tasks"]:
                return # Already exists in this day
                
            self.daily_data[date]["tasks"].append(new_task)
            self.daily_data[date]["task_status"][new_task] = False
                
            logger.info(f"Added custom daily task: {new_task} on {date}")
            self.populate_tasks_list()
            self.update_all_charts()

    def toggle_theme_action(self):
        """Toggle between light and dark theme."""
        self.theme.toggle()
        self.refresh_ui()

    def refresh_ui(self):
        """Refresh entire UI to reflect changes."""
        # Set focus to the main window to prevent active widgets from throwing focus errors when deleted
        self.focus_set()
        
        # Clear all widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        # Set appearance mode after widgets are destroyed to prevent update loop bugs
        mode = "dark" if self.theme.is_dark() else "light"
        ctk.set_appearance_mode(mode)
        
        # Reset UI element references
        self.week_charts = {}
        self.week_image_labels = {}
        self.daily_stats_labels = {}
        self.habit_vars = {}
        self.habit_progress_labels = {}
        self.habit_progress_bars = {}
        
        # Rebuild UI
        self.setup_ui()
        logger.info("UI refreshed successfully (charts rendering deferred)")
        self.after(100, self.update_all_charts)

    def edit_habit(self, old_habit):
        try:
            dialog = ctk.CTkInputDialog(text=f"'{old_habit}' nomini o'zgartirish:", title="Tahrirlash")
            new_habit = dialog.get_input()
            if new_habit and new_habit.strip() and new_habit != old_habit:
                new_habit = new_habit.strip()
                if new_habit in self.habits:
                    logger.warning(f"Odatni o'zgartirish xatosi: '{new_habit}' nomli odat ro'yxatda allaqachon mavjud.")
                    import tkinter.messagebox as messagebox
                    messagebox.showwarning("Ogohlantirish", "Bunday odat allaqachon mavjud!")
                    return # Already exists
                
                idx = self.habits.index(old_habit)
                self.habits[idx] = new_habit
                
                for date in self.daily_data:
                    val = self.daily_data[date]["habits"].pop(old_habit, False)
                    self.daily_data[date]["habits"][new_habit] = val
                    
                logger.info(f"Odat qayta nomlandi (Habit renamed): '{old_habit}' -> '{new_habit}'")
                self.populate_habits_list()
                self.update_all_charts()
        except Exception as e:
            logger.error(f"Error editing habit '{old_habit}': {e}")

    def delete_habit(self, habit):
        if habit in self.habits:
            from tkinter import messagebox
            confirm = messagebox.askyesno("Tasdiqlash", f"'{habit}' odatini barcha kunlardan o'chirmoqchimisiz?")
            if confirm:
                self.habits.remove(habit)
                for date in self.daily_data:
                    self.daily_data[date]["habits"].pop(habit, None)
                logger.info(f"Odat o'chirildi (Habit deleted): '{habit}'")
                self.populate_habits_list()
                self.update_all_charts()

    def edit_task(self, old_task, date):
        try:
            dialog = ctk.CTkInputDialog(text=f"'{old_task}' nomini o'zgartirish ({date}):", title="Tahrirlash")
            new_task = dialog.get_input()
            if new_task and new_task.strip() and new_task != old_task:
                new_task = new_task.strip()
                
                if new_task in self.daily_data[date]["tasks"]:
                    logger.warning(f"Vazifani o'zgartirish xatosi: '{new_task}' nomli vazifa ({date}) ro'yxatida allaqachon mavjud.")
                    import tkinter.messagebox as messagebox
                    messagebox.showwarning("Ogohlantirish", "Bunday vazifa allaqachon mavjud!")
                    return
                    
                t_idx = self.daily_data[date]["tasks"].index(old_task)
                self.daily_data[date]["tasks"][t_idx] = new_task
                val = self.daily_data[date]["task_status"].pop(old_task, False)
                self.daily_data[date]["task_status"][new_task] = val
                    
                logger.info(f"Vazifa qayta nomlandi (Task renamed): '{old_task}' -> '{new_task}' (sana: {date})")
                self.populate_tasks_list()
                self.update_all_charts()
        except Exception as e:
             logger.error(f"Error editing task '{old_task}' on {date}: {e}")

    def delete_task(self, task, date):
        try:
            from tkinter import messagebox
            confirm = messagebox.askyesno("Tasdiqlash", f"'{task}' vazifasini ({date}) dan o'chirmoqchimisiz?")
            if confirm:
                if task in self.daily_data[date]["tasks"]:
                    self.daily_data[date]["tasks"].remove(task)
                    self.daily_data[date]["task_status"].pop(task, None)
                    logger.info(f"Vazifa o'chirildi (Task deleted): '{task}' (sana: {date})")
                    
                self.populate_tasks_list()
                self.update_all_charts()
        except Exception as e:
            logger.error(f"Error deleting task '{task}' on {date}: {e}")

    def clear_all_habits(self):
        """Clear all habits after confirmation."""
        from tkinter import messagebox
        if not self.habits:
            messagebox.showinfo("Ma'lumot", "Odatlar ro'yxati bo'sh.")
            return
            
        confirm = messagebox.askyesno("Tasdiqlash", "Haqiqatan ham barcha odatlarni o'chirmoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.")
        if confirm:
            self.habits.clear()
            for date in self.daily_data:
                self.daily_data[date]["habits"].clear()
            self.populate_habits_list()
            self.update_all_charts()
            logger.info("All habits cleared.")

    def clear_all_tasks(self):
        """Clear all tasks (and task templates) after confirmation."""
        from tkinter import messagebox
        
        has_tasks = len(self.task_templates) > 0
        if not has_tasks:
            for date in self.daily_data:
                if self.daily_data[date]["tasks"]:
                    has_tasks = True
                    break
                    
        if not has_tasks:
            messagebox.showinfo("Ma'lumot", "Vazifalar ro'yxati bo'sh.")
            return

        confirm = messagebox.askyesno("Tasdiqlash", "Haqiqatan ham barcha vazifalarni o'chirmoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.")
        if confirm:
            self.task_templates.clear()
            for date in self.daily_data:
                self.daily_data[date]["tasks"].clear()
                self.daily_data[date]["task_status"].clear()
            self.populate_tasks_list()
            self.update_all_charts()
            logger.info("All tasks cleared.")

    def export_to_excel(self):
        """Export current weekly data to an Excel file using Pandas."""
        try:
            import pandas as pd
            from tkinter import filedialog
            from tkinter import messagebox
            import os
            
            # Prompt for save file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Excel faylini saqlash",
                initialfile=f"Odatlar_{self.week_start_date.strftime('%Y-%m-%d')}.xlsx"
            )
            
            if not file_path:
                return
                
            days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
            dates = [(self.week_start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            
            # 1. Habits DF
            habit_data = {"Odatlar": self.habits}
            for i, date in enumerate(dates):
                col_name = f"{days_uz[i]} ({date})"
                habit_data[col_name] = [
                    f"Bajarildi: {h}" if self.daily_data[date]["habits"].get(h, False) else f"Bajarilmadi: {h}"
                    for h in self.habits
                ]
            df_habits = pd.DataFrame(habit_data)
            
            # 2. Tasks DF
            all_tasks = set(self.task_templates)
            for date in dates:
                if date in self.daily_data:
                    all_tasks.update(self.daily_data[date]["tasks"])
            
            all_tasks_list = list(all_tasks)
            task_data = {"Vazifalar": all_tasks_list}
            for i, date in enumerate(dates):
                col_name = f"{days_uz[i]} ({date})"
                task_data[col_name] = [
                    f"Bajarildi: {t}" if self.daily_data[date]["task_status"].get(t, False) else ("-" if t not in self.daily_data[date]["tasks"] else f"Bajarilmadi: {t}")
                    for t in all_tasks_list
                ]
            df_tasks = pd.DataFrame(task_data)
            
            # Write to Excel with auto-adjusted columns
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_habits.to_excel(writer, sheet_name='Odatlar', index=False)
                df_tasks.to_excel(writer, sheet_name='Vazifalar', index=False)
                
                # Auto-adjust column widths
                from openpyxl.utils import get_column_letter
                for worksheet_name in writer.sheets:
                    worksheet = writer.sheets[worksheet_name]
                    for col in worksheet.columns:
                        max_length = 0
                        column = col[0].column_letter # Get the column name
                        for cell in col:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                            except:
                                pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column].width = adjusted_width
                
            messagebox.showinfo("Muvaffaqiyatli", f"Ma'lumotlar saqlandi:\n{file_path}")
            logger.info(f"Exported data to {file_path}")
            
        except ImportError:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xatolik", "Excel ga yuklash uchun qaramliklar o'rnatilmagan (pandas, openpyxl). Iltimos, dasturni qayta ishga tushiring yoki terminalda 'pip install pandas openpyxl' deb yozing.")
            logger.error("Missing pandas or openpyxl for export")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xatolik", f"Eksport qilishda xatolik yuz berdi: {e}")
            logger.error(f"Export error: {e}")


if __name__ == "__main__":
    app = TrackerApp()
    app.mainloop()

