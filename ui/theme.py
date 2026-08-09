"""
Premium dark theme constants for Form16 Scanner.
"""
COLOR_BG = "#0D1117"
COLOR_SURFACE = "#161B22"
COLOR_SURFACE_2 = "#21262D"
COLOR_BORDER = "#30363D"
COLOR_PRIMARY = "#00D4AA"
COLOR_PRIMARY_HOVER = "#00B894"
COLOR_SECONDARY = "#7C3AED"
COLOR_SECONDARY_HOVER = "#6D28D9"
COLOR_TEXT = "#E6EDF3"
COLOR_TEXT_MUTED = "#8B949E"
COLOR_TEXT_DIM = "#484F58"
COLOR_SUCCESS = "#3FB950"
COLOR_WARNING = "#D29922"
COLOR_DANGER = "#F85149"
COLOR_INFO = "#58A6FF"

FONT_FAMILY = "Segoe UI"

def font(size: int = 13, weight: str = "normal") -> tuple:
    return (FONT_FAMILY, size, weight)

FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_HEADING = (FONT_FAMILY, 18, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 13, "normal")
FONT_SMALL = (FONT_FAMILY, 11, "normal")
FONT_MONO = ("Consolas", 12, "normal")

BUTTON_HEIGHT = 80
INPUT_HEIGHT = 38
CORNER_RADIUS = 8
CARD_PADDING = 20

import customtkinter as ctk

def apply_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
