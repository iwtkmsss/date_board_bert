from __future__ import annotations

import json
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageTk


DEFAULT_SETTINGS = {
    "window_title": "Mini SC Timer",
    "fullscreen_on_start": False,
    "background_color": "#111417",
    "label_text": "Поточний час",
    "label_color": "#7CFF62",
    "time_color": "#F1FFF0",
    "font_family": "Bahnschrift",
    "label_font_size": 26,
    "time_font_size": 120,
    "time_format": "%H:%M:%S",
}

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 360
UPDATE_INTERVAL_MS = 200
DESIGN_WIDTH = 1920
DESIGN_HEIGHT = 1080
MIN_LABEL_FONT_SIZE = 18
MAX_LABEL_FONT_SIZE = 54
MIN_TIME_FONT_SIZE = 48
MAX_TIME_FONT_SIZE = 180
CONTENT_SPACING = 12
CONTENT_PADDING_X = 40
CONTENT_PADDING_Y = 28
LOGO_PADDING_X = 28
LOGO_PADDING_Y = 24
LOGO_MAX_WIDTH = 280
LOGO_MAX_HEIGHT = 130
GRID_SPACING = 96
GRID_COLOR = "#1A2024"
GRID_ACCENT_COLOR = "#222A2F"
PANEL_BG = "#171C20"
PANEL_BORDER = "#2A3238"
ACCENT_COLOR = "#7CFF62"
TEXT_MUTED = "#879097"
BADGE_BG = "#12171A"
BADGE_BORDER = "#2D3932"
PANEL_PADDING_X = 36
PANEL_PADDING_Y = 26
HINT_BOTTOM_OFFSET = 18
VISUAL_CENTER_RATIO = 0.35
VISUAL_CENTER_MIN_OFFSET = 28
VISUAL_CENTER_MAX_OFFSET = 96
DATE_COLOR = "#93A19A"
UA_MONTHS = (
    "січня",
    "лютого",
    "березня",
    "квітня",
    "травня",
    "червня",
    "липня",
    "серпня",
    "вересня",
    "жовтня",
    "листопада",
    "грудня",
)
FONT_CANDIDATES = (
    "Bahnschrift",
    "Cascadia Mono",
    "Segoe UI",
    "Consolas",
)
TIME_FONT_CANDIDATES = (
    "Cascadia Mono",
    "Consolas",
    "Lucida Console",
    "Courier New",
)
ASSETS_DIRNAME = "assets"
LOGO_FILENAME = "logo.png"
ICON_FILENAMES = (
    "icon.ico",
    "icon.png",
    LOGO_FILENAME,
)


def deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        with settings_path.open("r", encoding="utf-8") as settings_file:
            user_settings = json.load(settings_file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Не вдалося прочитати settings.json: {error}", file=sys.stderr)
        return dict(DEFAULT_SETTINGS)

    return deep_merge(DEFAULT_SETTINGS, user_settings)


class ClockApp:
    def __init__(self, root: tk.Tk, settings: dict, base_dir: Path) -> None:
        self.root = root
        self.settings = settings
        self.base_dir = base_dir
        self.is_fullscreen = False
        self.logo_source: Image.Image | None = None
        self.logo_photo: ImageTk.PhotoImage | None = None
        self.icon_photo: ImageTk.PhotoImage | None = None
        self.font_family = self._resolve_font_family(self.settings["font_family"])
        self.time_font_family = self._resolve_font_family(
            TIME_FONT_CANDIDATES[0],
            TIME_FONT_CANDIDATES,
        )
        self.time_display_sample = self._build_time_display_sample()

        self.root.title(self.settings["window_title"])
        self.root.configure(bg=self.settings["background_color"])
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self._configure_events()
        self._build_layout()
        self._draw_background()
        self._configure_window_icon()
        self._load_logo_source()
        self._apply_scaling()
        self.root.update_idletasks()
        self._update_center_block_position()
        self._update_time()

        if self.settings.get("fullscreen_on_start", False):
            self.set_fullscreen(True)

    def _configure_events(self) -> None:
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)
        self.root.bind("<Configure>", self._handle_resize)

    def _build_layout(self) -> None:
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.root, bg=self.settings["background_color"])
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.bg_canvas = tk.Canvas(
            self.main_frame,
            bg=self.settings["background_color"],
            highlightthickness=0,
            bd=0,
        )
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.header_frame = tk.Frame(self.main_frame, bg=self.settings["background_color"])
        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=LOGO_PADDING_X,
            pady=LOGO_PADDING_Y,
        )
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.logo_label = tk.Label(
            self.header_frame,
            bg=self.settings["background_color"],
            bd=0,
            highlightthickness=0,
        )
        self.logo_label.grid(row=0, column=0, sticky="nw")

        self.brand_badge = tk.Label(
            self.header_frame,
            text="BERT COMPANY",
            fg=ACCENT_COLOR,
            bg=BADGE_BG,
            bd=0,
            highlightthickness=1,
            highlightbackground=BADGE_BORDER,
            padx=16,
            pady=8,
        )
        self.brand_badge.grid(row=0, column=1, sticky="ne")

        self.center_block = tk.Frame(
            self.main_frame,
            bg=self.settings["background_color"],
        )
        self.center_block.place(relx=0.5, rely=0.5, anchor="center")

        self.panel_kicker = tk.Label(
            self.center_block,
            text="LIVE TIME MONITOR",
            fg=ACCENT_COLOR,
            bg=self.settings["background_color"],
            justify="center",
        )
        self.panel_kicker.pack(pady=(0, 18))

        self.panel_frame = tk.Frame(
            self.center_block,
            bg=PANEL_BG,
            bd=0,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
        )
        self.panel_frame.pack()

        self.panel_accent = tk.Frame(self.panel_frame, bg=ACCENT_COLOR, height=3)
        self.panel_accent.pack(fill="x")

        self.panel_body = tk.Frame(self.panel_frame, bg=PANEL_BG)
        self.panel_body.pack(
            padx=PANEL_PADDING_X,
            pady=(PANEL_PADDING_Y, PANEL_PADDING_Y),
        )

        self.panel_divider = tk.Frame(self.panel_body, bg=PANEL_BORDER, height=1)
        self.panel_divider.pack(fill="x", pady=(0, 18))

        self.label_var = tk.StringVar(value=self.settings["label_text"])
        self.time_var = tk.StringVar()
        self.date_var = tk.StringVar()

        self.label_widget = tk.Label(
            self.panel_body,
            textvariable=self.label_var,
            fg=self.settings["label_color"],
            bg=PANEL_BG,
            justify="center",
        )

        self.time_widget = tk.Label(
            self.panel_body,
            textvariable=self.time_var,
            fg=self.settings["time_color"],
            bg=PANEL_BG,
            justify="center",
            width=max(len(self.time_display_sample), 8),
            anchor="center",
        )

        self.date_widget = tk.Label(
            self.panel_body,
            textvariable=self.date_var,
            fg=DATE_COLOR,
            bg=PANEL_BG,
            justify="center",
        )

        self.panel_footer = tk.Label(
            self.panel_body,
            text="BERT COMPANY // LOCAL NODE DISPLAY",
            fg=TEXT_MUTED,
            bg=PANEL_BG,
            justify="center",
        )

        self.controls_hint = tk.Label(
            self.center_block,
            text="F11 // FULLSCREEN    ESC // EXIT",
            fg=TEXT_MUTED,
            bg=self.settings["background_color"],
            justify="center",
        )

        self._update_label_visibility()
        self.time_widget.pack()
        self.date_widget.pack(pady=(12, 0))
        self.panel_footer.pack(pady=(18, 0))
        self.controls_hint.pack(pady=(HINT_BOTTOM_OFFSET, 0))

    def _update_label_visibility(self) -> None:
        if self.settings["label_text"].strip():
            self.label_widget.pack(pady=(0, CONTENT_SPACING))
        else:
            self.label_widget.pack_forget()

    def _load_logo_source(self) -> None:
        logo_path = self._resolve_asset_path(LOGO_FILENAME)
        if not logo_path:
            self.logo_label.configure(image="", text="")
            return

        try:
            self.logo_source = self._load_logo_image(logo_path)
            self._render_logo()
        except OSError as error:
            self.logo_source = None
            print(f"Не вдалося завантажити лого: {error}", file=sys.stderr)

    def _configure_window_icon(self) -> None:
        icon_path = self._resolve_first_asset_path(ICON_FILENAMES)
        if not icon_path:
            return

        try:
            if icon_path.suffix.lower() == ".ico":
                self.root.iconbitmap(default=str(icon_path))
                return

            with Image.open(icon_path) as image:
                image_copy = image.copy()
            image_copy.thumbnail((64, 64), Image.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(image_copy)
            self.root.iconphoto(True, self.icon_photo)
        except (OSError, tk.TclError) as error:
            print(f"Не вдалося завантажити іконку вікна: {error}", file=sys.stderr)

    def _render_logo(self) -> None:
        if self.logo_source is None:
            self.logo_label.configure(image="", text="")
            return

        window_width = max(self.root.winfo_width(), 1)
        window_height = max(self.root.winfo_height(), 1)
        max_width = min(LOGO_MAX_WIDTH, int(window_width * 0.22))
        max_height = min(LOGO_MAX_HEIGHT, int(window_height * 0.14))
        max_width = max(80, max_width)
        max_height = max(48, max_height)

        image_copy = self.logo_source.copy()
        image_copy.thumbnail((max_width, max_height), Image.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(image_copy)
        self.logo_label.configure(image=self.logo_photo, text="")

    def _load_logo_image(self, logo_path: Path) -> Image.Image:
        if logo_path.suffix.lower() == ".svg":
            raise OSError("SVG не підтримується. Використайте PNG або JPG.")

        with Image.open(logo_path) as image:
            return image.copy()

    def _resolve_asset_path(self, filename: str) -> Path | None:
        candidate = self.base_dir / ASSETS_DIRNAME / filename
        if candidate.exists():
            return candidate
        return None

    def _resolve_first_asset_path(self, filenames: tuple[str, ...]) -> Path | None:
        for filename in filenames:
            candidate = self._resolve_asset_path(filename)
            if candidate is not None:
                return candidate
        return None

    def _draw_background(self) -> None:
        width = max(self.main_frame.winfo_width(), 1)
        height = max(self.main_frame.winfo_height(), 1)

        self.bg_canvas.delete("grid")

        for x in range(0, width, GRID_SPACING):
            color = GRID_ACCENT_COLOR if x % (GRID_SPACING * 3) == 0 else GRID_COLOR
            self.bg_canvas.create_line(x, 0, x, height, fill=color, tags="grid")

        for y in range(0, height, GRID_SPACING):
            color = GRID_ACCENT_COLOR if y % (GRID_SPACING * 3) == 0 else GRID_COLOR
            self.bg_canvas.create_line(0, y, width, y, fill=color, tags="grid")

        self.bg_canvas.create_line(0, 92, width, 92, fill=GRID_COLOR, tags="grid")
        self.bg_canvas.create_rectangle(
            18,
            18,
            width - 18,
            height - 18,
            outline="#20272C",
            width=1,
            tags="grid",
        )
        self.bg_canvas.create_text(
            32,
            height - 28,
            anchor="w",
            text="DEV-OPS CLOCK DASHBOARD",
            fill=TEXT_MUTED,
            font=(self.font_family, 11, "normal"),
            tags="grid",
        )

    def _update_center_block_position(self) -> None:
        self.main_frame.update_idletasks()
        header_height = self.header_frame.winfo_height()
        requested_header_height = self.header_frame.winfo_reqheight() + (LOGO_PADDING_Y * 2)
        visual_header_height = max(header_height, requested_header_height)
        visual_offset = int(visual_header_height * VISUAL_CENTER_RATIO)
        visual_offset = max(VISUAL_CENTER_MIN_OFFSET, visual_offset)
        visual_offset = min(VISUAL_CENTER_MAX_OFFSET, visual_offset)
        main_height = max(self.main_frame.winfo_height(), 1)
        block_height = max(self.center_block.winfo_reqheight(), 1)
        max_safe_offset = max(0, ((main_height - block_height) // 2) - 8)
        visual_offset = min(visual_offset, max_safe_offset)

        self.center_block.place_configure(
            relx=0.5,
            rely=0.5,
            anchor="center",
            y=-visual_offset,
        )

    def _resolve_font_family(
        self,
        requested_family: str,
        fallback_candidates: tuple[str, ...] = FONT_CANDIDATES,
    ) -> str:
        available_fonts = set(tkfont.families(self.root))

        if requested_family in available_fonts:
            return requested_family

        for candidate in fallback_candidates:
            if candidate in available_fonts:
                return candidate

        return "TkDefaultFont"

    def _build_time_display_sample(self) -> str:
        sample_time = datetime(2088, 8, 28, 18, 58, 58)
        return sample_time.strftime(self.settings["time_format"])

    @staticmethod
    def _format_date(current_dt: datetime) -> str:
        month_name = UA_MONTHS[current_dt.month - 1]
        return f"{current_dt.day} {month_name} {current_dt.year}"

    def _apply_scaling(self) -> None:
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        scale = min(width / DESIGN_WIDTH, height / DESIGN_HEIGHT)

        header_pad_x = max(12, min(int(width * 0.022), LOGO_PADDING_X))
        header_pad_y = max(10, min(int(height * 0.03), LOGO_PADDING_Y))
        panel_pad_x = max(16, min(int(PANEL_PADDING_X * scale), PANEL_PADDING_X))
        panel_pad_y = max(14, min(int(PANEL_PADDING_Y * scale), PANEL_PADDING_Y))
        kicker_gap = max(8, min(int(18 * scale), 18))
        divider_gap = max(10, min(int(18 * scale), 18))
        date_gap = max(6, min(int(12 * scale), 12))
        footer_gap = max(10, min(int(18 * scale), 18))
        hint_gap = max(10, min(int(HINT_BOTTOM_OFFSET * scale), HINT_BOTTOM_OFFSET))
        badge_pad_x = max(10, min(int(16 * scale), 16))
        badge_pad_y = max(5, min(int(8 * scale), 8))

        label_size = self._clamp_font_size(
            self.settings["label_font_size"] * scale,
            MIN_LABEL_FONT_SIZE,
            MAX_LABEL_FONT_SIZE,
        )
        time_size = self._clamp_font_size(
            self.settings["time_font_size"] * scale,
            MIN_TIME_FONT_SIZE,
            MAX_TIME_FONT_SIZE,
        )
        kicker_size = self._clamp_font_size(14 * scale, 10, 18)
        footer_size = self._clamp_font_size(13 * scale, 10, 16)
        badge_size = self._clamp_font_size(14 * scale, 10, 18)
        hint_size = self._clamp_font_size(12 * scale, 9, 15)
        date_size = self._clamp_font_size(18 * scale, 12, 24)

        self.header_frame.grid_configure(
            padx=header_pad_x,
            pady=header_pad_y,
        )
        self.brand_badge.configure(
            padx=badge_pad_x,
            pady=badge_pad_y,
        )
        self.panel_body.pack_configure(
            padx=panel_pad_x,
            pady=(panel_pad_y, panel_pad_y),
        )
        self.panel_kicker.pack_configure(pady=(0, kicker_gap))
        self.panel_divider.pack_configure(pady=(0, divider_gap))
        self.date_widget.pack_configure(pady=(date_gap, 0))
        self.panel_footer.pack_configure(pady=(footer_gap, 0))
        self.controls_hint.pack_configure(pady=(hint_gap, 0))

        self.label_widget.configure(
            font=(self.font_family, label_size, "normal"),
            wraplength=max(220, int(width * 0.65)),
        )
        self.time_widget.configure(
            font=(self.time_font_family, time_size, "normal"),
        )
        self.panel_kicker.configure(
            font=(self.font_family, kicker_size, "bold"),
        )
        self.panel_footer.configure(
            font=(self.font_family, footer_size, "normal"),
        )
        self.date_widget.configure(
            font=(self.font_family, date_size, "normal"),
        )
        self.brand_badge.configure(
            font=(self.font_family, badge_size, "bold"),
        )
        self.controls_hint.configure(
            font=(self.font_family, hint_size, "normal"),
        )

        if self.logo_source is not None:
            self._render_logo()

    @staticmethod
    def _clamp_font_size(size: float, minimum: int, maximum: int) -> int:
        return max(minimum, min(int(size), maximum))

    def _update_time(self) -> None:
        current_dt = datetime.now()
        self.time_var.set(current_dt.strftime(self.settings["time_format"]))
        self.date_var.set(self._format_date(current_dt))
        self.root.after(UPDATE_INTERVAL_MS, self._update_time)

    def _handle_resize(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self._draw_background()
            self._apply_scaling()
            self._update_center_block_position()

    def set_fullscreen(self, value: bool) -> None:
        self.is_fullscreen = value
        self.root.attributes("-fullscreen", value)

    def _toggle_fullscreen(self, _event: tk.Event) -> str:
        self.set_fullscreen(not self.is_fullscreen)
        return "break"

    def _exit_fullscreen(self, _event: tk.Event) -> str:
        if self.is_fullscreen:
            self.set_fullscreen(False)
        return "break"


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    if len(sys.argv) > 1:
        settings_arg = Path(sys.argv[1]).expanduser()
        settings_path = settings_arg if settings_arg.is_absolute() else Path.cwd() / settings_arg
    else:
        settings_path = base_dir / "settings.json"

    settings = load_settings(settings_path)

    root = tk.Tk()
    ClockApp(root, settings, settings_path.parent)
    root.mainloop()


if __name__ == "__main__":
    main()
