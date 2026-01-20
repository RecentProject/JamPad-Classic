import dearpygui.dearpygui as dpg
import pygame
import pynput
import time
import threading
import pygetwindow as gw
from PIL import Image, ImageDraw
from pynput.keyboard import Key, Controller as KeyboardController
import pystray
import json
import os
import sys
import ctypes
import webbrowser
import winsound

# ────────────────────────────────────────────────
# CONFIG & GLOBALS
# ────────────────────────────────────────────────
DEFAULT_CURSOR_SENSITIVITY = 25.0
MOVEMENT_THRESHOLD = 0.18
DEADZONE = 0.12
TRIGGER_THRESHOLD = 0.45
WINDOW_TITLE = "Animal Jam Classic"
APP_TITLE = "JamPad Classic"
PROFILES_FILE = "aj_profiles.json"
GITHUB_URL = "https://github.com/RecentProject/JamPad-Classic"

enabled = False
cursor_sensitivity = DEFAULT_CURSOR_SENSITIVITY
active_joystick_index = 0
always_on_top = False
GUI_READY = False 

# Button Labels
L_TRIGGER_LABEL = "L2"
R_TRIGGER_LABEL = "R2"
BTN_A_LABEL = "X"
BTN_B_LABEL = "O"
BTN_X_LABEL = "Sq"
BTN_Y_LABEL = "Tri"

mouse = pynput.mouse.Controller()
keyboard = KeyboardController()

# ─── KEY MAPPING SYSTEM ───
KEY_OPTIONS = {
    "Backspace": Key.backspace, "Space": Key.space, "Enter": Key.enter, "Shift": Key.shift, "Esc": Key.esc,
    "W": "w", "A": "a", "S": "s", "D": "d",
    "Up": Key.up, "Down": Key.down, "Left": Key.left, "Right": Key.right,
    "E": "e", "Q": "q", "R": "r", "F": "f", "None": None
}

current_bindings = {
    "btn_a": "Space", "btn_b": "None", "btn_x": "None", "btn_y": "None"
}

# State tracking
last_pressed = {
    'up': False, 'down': False, 'left': False, 'right': False, 
    'btn_a': False, 'btn_b': False, 'btn_x': False, 'btn_y': False,
    'click': False, 'r_click': False
}

DIRECTION_MAP = {
    'up': (1, -1, Key.up),
    'down': (1, 1, Key.down),
    'left': (0, -1, Key.left),
    'right': (0, 1, Key.right),
}

gui_colors = {
    "background": [0.09, 0.16, 0.13, 1.0],
    "text": [0.925, 0.886, 0.745, 1.0],
    "sliders": [0.0, 0.47, 0.78, 1.0],
    "tabs": [0.184, 0.404, 0.647, 1.0],
    "buttons": [0.184, 0.404, 0.647, 1.0]
}

# ────────────────────────────────────────────────
# ASSET HELPER
# ────────────────────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ────────────────────────────────────────────────
# CONTROLLER LOGIC
# ────────────────────────────────────────────────
pygame.init()
pygame.joystick.init()
joystick = None

def get_battery_status():
    if not joystick: return "Not Connected"
    try:
        power = joystick.get_power_level()
        if power == "wired": return "Wired (Charging)"
        elif power == "full": return "Battery: Full"
        elif power == "medium": return "Battery: Medium"
        elif power == "low": return "Battery: Low"
        elif power == "empty": return "Battery: Critical!"
        else: return "Battery: Unknown"
    except: return "Battery: Unknown"

def update_button_labels(name):
    global L_TRIGGER_LABEL, R_TRIGGER_LABEL, BTN_A_LABEL, BTN_B_LABEL, BTN_X_LABEL, BTN_Y_LABEL
    name_lower = name.lower()
    if "xbox" in name_lower or "xinput" in name_lower or "microsoft" in name_lower:
        L_TRIGGER_LABEL = "LT"; R_TRIGGER_LABEL = "RT"
        BTN_A_LABEL = "A"; BTN_B_LABEL = "B"; BTN_X_LABEL = "X"; BTN_Y_LABEL = "Y"
    else:
        L_TRIGGER_LABEL = "L2"; R_TRIGGER_LABEL = "R2"
        BTN_A_LABEL = "X"; BTN_B_LABEL = "O"; BTN_X_LABEL = "Sq"; BTN_Y_LABEL = "Tri"
    
    if GUI_READY:
        if dpg.does_item_exist("vis_txt_fire"): dpg.set_value("vis_txt_fire", R_TRIGGER_LABEL)
        if dpg.does_item_exist("vis_txt_a"): dpg.set_value("vis_txt_a", BTN_A_LABEL)
        
        if dpg.does_item_exist("lbl_btn_a"): dpg.set_value("lbl_btn_a", f"Button {BTN_A_LABEL}")
        if dpg.does_item_exist("lbl_btn_b"): dpg.set_value("lbl_btn_b", f"Button {BTN_B_LABEL}")
        if dpg.does_item_exist("lbl_btn_x"): dpg.set_value("lbl_btn_x", f"Button {BTN_X_LABEL}")
        if dpg.does_item_exist("lbl_btn_y"): dpg.set_value("lbl_btn_y", f"Button {BTN_Y_LABEL}")

def init_joystick():
    global joystick
    if pygame.joystick.get_count() > 0:
        idx = active_joystick_index if active_joystick_index < pygame.joystick.get_count() else 0
        joystick = pygame.joystick.Joystick(idx)
        joystick.init()
        name = joystick.get_name()
        update_button_labels(name)
        return name
    return "No Controller Detected"

controller_name = init_joystick()

def refresh_controller_list():
    count = pygame.joystick.get_count()
    if count == 0: return ["No Controller Detected"]
    return [f"{i}: {pygame.joystick.Joystick(i).get_name()}" for i in range(count)]

def switch_controller(sender, app_data):
    global joystick, active_joystick_index, controller_name
    if not app_data or "No Controller" in app_data: return
    try:
        idx = int(app_data.split(":")[0])
        active_joystick_index = idx
        if joystick: joystick.quit()
        joystick = pygame.joystick.Joystick(active_joystick_index)
        joystick.init()
        controller_name = joystick.get_name()
        update_button_labels(controller_name)
        dpg.set_value("main_controller_text", f"Active: {controller_name}")
        dpg.set_value("battery_text", get_battery_status())
    except: pass

# ────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────
def load_profiles_data():
    if not os.path.exists(PROFILES_FILE): 
        return {}
    try: 
        with open(PROFILES_FILE, 'r') as f: 
            return json.load(f)
    except: 
        return {}

def trigger_key(key_name, pressed, state_key):
    if key_name == "None": return
    target_key = KEY_OPTIONS.get(key_name)
    if not target_key: return

    if pressed:
        if not last_pressed[state_key]:
            keyboard.press(target_key)
            last_pressed[state_key] = True
    else:
        if last_pressed[state_key]:
            keyboard.release(target_key)
            last_pressed[state_key] = False

# ────────────────────────────────────────────────
# POLLING THREAD
# ────────────────────────────────────────────────
def poll_gamepad():
    global last_pressed
    battery_timer = 0
    rem_x = 0.0; rem_y = 0.0

    while True:
        if not enabled or not joystick:
            time.sleep(0.1); continue
        
        if time.time() - battery_timer > 5.0:
            if GUI_READY: dpg.set_value("battery_text", get_battery_status())
            battery_timer = time.time()

        is_game_focused = False
        is_app_focused = False
        try:
            active_win = gw.getActiveWindow()
            if active_win:
                if WINDOW_TITLE in active_win.title: is_game_focused = True
                elif APP_TITLE in active_win.title: is_app_focused = True
        except: pass

        if not is_game_focused and not is_app_focused:
            time.sleep(0.1); continue

        pygame.event.pump()

        lx = joystick.get_axis(0); ly = joystick.get_axis(1)
        rx = joystick.get_axis(2) if joystick.get_numaxes() > 2 else 0
        ry = joystick.get_axis(3) if joystick.get_numaxes() > 3 else 0
        l2 = (joystick.get_axis(4) + 1) / 2 if joystick.get_numaxes() > 4 else 0
        r2 = (joystick.get_axis(5) + 1) / 2 if joystick.get_numaxes() > 5 else 0
        btn_a = joystick.get_button(0)
        btn_b = joystick.get_button(1)
        btn_x = joystick.get_button(2)
        btn_y = joystick.get_button(3)

        try:
            dpg.configure_item("vis_l_stick", center=(90 + lx*25, 60 + ly*25))
            dpg.configure_item("vis_r_stick", center=(290 + rx*25, 60 + ry*25))
            dz_radius = 25 * DEADZONE
            dpg.configure_item("vis_dz_l", radius=dz_radius)
            dpg.configure_item("vis_dz_r", radius=dz_radius)

            active_col = [int(c*255) for c in gui_colors["sliders"][:3]]
            dpg.configure_item("vis_btn_a", fill=active_col if btn_a else (60, 60, 60))
            dpg.configure_item("vis_btn_fire", fill=(255, 80, 80) if r2 > TRIGGER_THRESHOLD else (60, 60, 60))
        except: pass

        if is_game_focused:
            for name, (axis, direction, key) in DIRECTION_MAP.items():
                val = joystick.get_axis(axis)
                is_active = (val < -MOVEMENT_THRESHOLD) if direction < 0 else (val > MOVEMENT_THRESHOLD)
                if is_active and not last_pressed[name]:
                    keyboard.press(key); last_pressed[name] = True
                elif not is_active and last_pressed[name]:
                    keyboard.release(key); last_pressed[name] = False

            trigger_key(current_bindings["btn_a"], btn_a, "btn_a")
            trigger_key(current_bindings["btn_b"], btn_b, "btn_b")
            trigger_key(current_bindings["btn_x"], btn_x, "btn_x")
            trigger_key(current_bindings["btn_y"], btn_y, "btn_y")

            if abs(rx) > DEADZONE:
                rem_x += (rx**3) * cursor_sensitivity
                move_x = int(rem_x)
                rem_x -= move_x
                if move_x != 0: mouse.move(move_x, 0)
            else: rem_x = 0.0

            if abs(ry) > DEADZONE:
                rem_y += (ry**3) * cursor_sensitivity
                move_y = int(rem_y)
                rem_y -= move_y
                if move_y != 0: mouse.move(0, move_y)
            else: rem_y = 0.0

            if r2 > TRIGGER_THRESHOLD:
                if not last_pressed['click']: mouse.press(pynput.mouse.Button.left); last_pressed['click'] = True
            else:
                if last_pressed['click']: mouse.release(pynput.mouse.Button.left); last_pressed['click'] = False
            
            if l2 > TRIGGER_THRESHOLD:
                if not last_pressed['r_click']: mouse.press(pynput.mouse.Button.right); last_pressed['r_click'] = True
            else:
                if last_pressed['r_click']: mouse.release(pynput.mouse.Button.right); last_pressed['r_click'] = False

        time.sleep(0.008)

# ────────────────────────────────────────────────
# GUI CALLBACKS
# ────────────────────────────────────────────────
def apply_gui_colors():
    def to_int(color): return tuple(int(c*255) for c in color[:3])
    bg = to_int(gui_colors["background"])
    text = to_int(gui_colors["text"])
    tabs = to_int(gui_colors["tabs"])
    sliders = to_int(gui_colors["sliders"])
    
    if dpg.does_item_exist("global_theme"): dpg.delete_item("global_theme")
    with dpg.theme(tag="global_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, bg)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (bg[0]+10, bg[1]+10, bg[2]+10))
            dpg.add_theme_color(dpg.mvThemeCol_Text, text)
            dpg.add_theme_color(dpg.mvThemeCol_Button, tabs)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (tabs[0]+20, tabs[1]+20, tabs[2]+20))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, sliders)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, tabs)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (tabs[0]+20, tabs[1]+20, tabs[2]+20))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, sliders)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, sliders)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, text)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (bg[0]-10, bg[1]-10, bg[2]-10))
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 6) 
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 3) 
    dpg.bind_theme("global_theme")

def update_color_config(sender, app_data, user_data):
    gui_colors[user_data] = app_data
    apply_gui_colors()

def toggle_mapper():
    global enabled
    enabled = not enabled
    status = "ACTIVE (Running)" if enabled else "DISABLED (Paused)"
    color = (100, 255, 100) if enabled else (255, 100, 100)
    dpg.set_value("status_text", status)
    dpg.configure_item("status_text", color=color)
    dpg.configure_item("toggle_btn", label="Disable Controller (F1)" if enabled else "Enable Controller (F1)")
    
    try:
        if enabled: winsound.Beep(800, 150)
        else: winsound.Beep(500, 150)
    except: pass

def toggle_always_on_top():
    global always_on_top
    always_on_top = not always_on_top
    dpg.set_viewport_always_top(always_on_top)
    dpg.configure_item("top_btn", label="Always On Top: ON" if always_on_top else "Always On Top: OFF")

def update_sensitivity(sender, app_data): global cursor_sensitivity; cursor_sensitivity = app_data
def update_param(sender, app_data, user_data): 
    global MOVEMENT_THRESHOLD, DEADZONE, TRIGGER_THRESHOLD
    if user_data == "move": MOVEMENT_THRESHOLD = app_data
    elif user_data == "dead": DEADZONE = app_data
    elif user_data == "trig": TRIGGER_THRESHOLD = app_data

def update_binding(sender, app_data, user_data):
    current_bindings[user_data] = app_data

def reset_defaults(sender, app_data):
    global cursor_sensitivity, MOVEMENT_THRESHOLD, DEADZONE, TRIGGER_THRESHOLD, gui_colors, current_bindings
    cursor_sensitivity = 25.0; MOVEMENT_THRESHOLD = 0.18; DEADZONE = 0.12; TRIGGER_THRESHOLD = 0.45
    current_bindings = {"btn_a": "Space", "btn_b": "None", "btn_x": "None", "btn_y": "None"}
    gui_colors["background"] = [0.09, 0.16, 0.13, 1.0]
    gui_colors["text"] = [0.925, 0.886, 0.745, 1.0]
    gui_colors["sliders"] = [0.0, 0.47, 0.78, 1.0]
    gui_colors["tabs"] = [0.184, 0.404, 0.647, 1.0]
    
    dpg.set_value("sens_slider", cursor_sensitivity)
    dpg.set_value("mv_slider", MOVEMENT_THRESHOLD)
    dpg.set_value("dz_slider", DEADZONE)
    dpg.set_value("tr_slider", TRIGGER_THRESHOLD)
    dpg.set_value("bind_a", "Space")
    dpg.set_value("bind_b", "None")
    dpg.set_value("bind_x", "None")
    dpg.set_value("bind_y", "None")
    apply_gui_colors()

def save_profile(sender, app_data):
    name = dpg.get_value("profile_name")
    if not name: return
    data = load_profiles_data()
    data[name] = {
        "sens": cursor_sensitivity, "move": MOVEMENT_THRESHOLD, "dead": DEADZONE, "trig": TRIGGER_THRESHOLD, 
        "colors": gui_colors, "bindings": current_bindings
    }
    with open(PROFILES_FILE, 'w') as f: json.dump(data, f)
    dpg.configure_item("profile_combo", items=list(data.keys()))

def apply_loaded_profile(sender, app_data):
    global cursor_sensitivity, MOVEMENT_THRESHOLD, DEADZONE, TRIGGER_THRESHOLD, gui_colors, current_bindings
    data = load_profiles_data()
    if app_data in data:
        p = data[app_data]
        cursor_sensitivity = p.get("sens", 25.0)
        MOVEMENT_THRESHOLD = p.get("move", 0.18)
        DEADZONE = p.get("dead", 0.12)
        TRIGGER_THRESHOLD = p.get("trig", 0.45)
        if "colors" in p: gui_colors.update(p["colors"]); apply_gui_colors()
        if "bindings" in p: 
            current_bindings.update(p["bindings"])
            dpg.set_value("bind_a", current_bindings["btn_a"])
            dpg.set_value("bind_b", current_bindings["btn_b"])
            dpg.set_value("bind_x", current_bindings["btn_x"])
            dpg.set_value("bind_y", current_bindings["btn_y"])
            
        dpg.set_value("sens_slider", cursor_sensitivity)
        dpg.set_value("mv_slider", MOVEMENT_THRESHOLD)
        dpg.set_value("dz_slider", DEADZONE)
        dpg.set_value("tr_slider", TRIGGER_THRESHOLD)

def on_press(key):
    if key == Key.f1: toggle_mapper()
    elif key == Key.f2: toggle_always_on_top()

keyboard_listener = pynput.keyboard.Listener(on_press=on_press)
keyboard_listener.start()

def create_tray_image():
    try:
        png_path = resource_path("logo.png")
        if os.path.exists(png_path): return Image.open(png_path)
    except: pass
    img = Image.new('RGB', (64, 64), (23, 42, 32))
    dc = ImageDraw.Draw(img)
    dc.ellipse((16, 16, 48, 48), fill=(47, 103, 165))
    return img

def quit_app(icon, item): 
    icon.stop()
    dpg.stop_dearpygui()
    
tray_icon = pystray.Icon("JamPad", create_tray_image(), "JamPad", menu=pystray.Menu(pystray.MenuItem("Toggle", lambda i, It: toggle_mapper()), pystray.MenuItem("Quit", quit_app)))
threading.Thread(target=tray_icon.run, daemon=True).start()

def setup_font():
    with dpg.font_registry():
        font_path = resource_path("font.ttf")
        if os.path.exists(font_path):
            with dpg.font(font_path, 17.5) as f: 
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.bind_font(f); return
        sys_font = "C:/Windows/Fonts/segoeui.ttf"
        if os.path.exists(sys_font):
            with dpg.font(sys_font, 17.5) as f: 
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.bind_font(f)

# ────────────────────────────────────────────────
# GUI LAYOUT
# ────────────────────────────────────────────────
dpg.create_context()
setup_font()
icon_path = resource_path("icon.ico")
if not os.path.exists(icon_path): icon_path = "" 

dpg.create_viewport(title="JamPad Classic", width=420, height=600, small_icon=icon_path, large_icon=icon_path)
dpg.setup_dearpygui()

with dpg.window(tag="main_window", width=420, height=600):
    with dpg.tab_bar():
        # ─── MAIN TAB ───
        with dpg.tab(label="Main"):
            dpg.add_spacer(height=2)
            with dpg.group():
                dpg.add_text("Status: DISABLED (Paused)", tag="status_text", color=(255, 100, 100))
                dpg.add_text(f"Active: {controller_name}", tag="main_controller_text")
                dpg.add_text(get_battery_status(), tag="battery_text", color=(150, 255, 150))
            dpg.add_spacer(height=2)
            dpg.add_combo(items=refresh_controller_list(), label="Controller", callback=switch_controller, width=-1)
            dpg.add_separator(); dpg.add_spacer(height=5)
            
            # VISUALIZER (Now with Deadzone Rings)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=10)
                with dpg.drawlist(width=380, height=120):
                    dpg.draw_rectangle((0, 0), (380, 120), color=(0,0,0,0), thickness=0) 
                    
                    # Left Stick
                    dpg.draw_circle((90, 60), 40, color=(150,150,150), thickness=2)
                    dpg.draw_circle((90, 60), 5, color=(255,50,50), tag="vis_dz_l") # Deadzone Ring
                    dpg.draw_circle((90, 60), 15, fill=(200,200,200), tag="vis_l_stick")
                    dpg.draw_text((75, 105), "Move", size=13)
                    
                    # Right Stick
                    dpg.draw_circle((290, 60), 40, color=(150,150,150), thickness=2)
                    dpg.draw_circle((290, 60), 5, color=(255,50,50), tag="vis_dz_r") # Deadzone Ring
                    dpg.draw_circle((290, 60), 15, fill=(200,200,200), tag="vis_r_stick")
                    dpg.draw_text((270, 105), "Cursor", size=13)
                    
                    # Buttons
                    dpg.draw_circle((190, 40), 12, fill=(60,60,60), tag="vis_btn_fire")
                    dpg.draw_text((182, 33), R_TRIGGER_LABEL, tag="vis_txt_fire", size=13)
                    dpg.draw_circle((190, 80), 12, fill=(60,60,60), tag="vis_btn_a")
                    dpg.draw_text((186, 73), BTN_A_LABEL, tag="vis_txt_a", size=13, color=(255,255,255))
            
            dpg.add_spacer(height=5)
            with dpg.group():
                dpg.add_text("Sensitivity")
                dpg.add_slider_float(tag="sens_slider", default_value=DEFAULT_CURSOR_SENSITIVITY, min_value=1.0, max_value=100.0, callback=update_sensitivity, height=26)
                dpg.add_spacer(height=5)
                dpg.add_button(label="Enable Controller (F1)", tag="toggle_btn", callback=toggle_mapper, width=-1, height=42)
                dpg.add_button(label="Always On Top (F2)", tag="top_btn", callback=toggle_always_on_top, width=-1, height=42)

        # ─── CONTROLS TAB (NEW) ───
        with dpg.tab(label="Controls"):
            dpg.add_spacer(height=5)
            dpg.add_text("Button Mapping")
            dpg.add_separator(); dpg.add_spacer(height=5)
            
            keys = list(KEY_OPTIONS.keys())
            dpg.add_text(f"Button {BTN_A_LABEL}", tag="lbl_btn_a")
            dpg.add_combo(items=keys, default_value="Space", callback=update_binding, user_data="btn_a", tag="bind_a", width=-1)
            dpg.add_spacer(height=5)
            
            dpg.add_text(f"Button {BTN_B_LABEL}", tag="lbl_btn_b")
            dpg.add_combo(items=keys, default_value="None", callback=update_binding, user_data="btn_b", tag="bind_b", width=-1)
            dpg.add_spacer(height=5)
            
            dpg.add_text(f"Button {BTN_X_LABEL}", tag="lbl_btn_x")
            dpg.add_combo(items=keys, default_value="None", callback=update_binding, user_data="btn_x", tag="bind_x", width=-1)
            dpg.add_spacer(height=5)
            
            dpg.add_text(f"Button {BTN_Y_LABEL}", tag="lbl_btn_y")
            dpg.add_combo(items=keys, default_value="None", callback=update_binding, user_data="btn_y", tag="bind_y", width=-1)

        # ─── SETTINGS TAB ───
        with dpg.tab(label="Settings"):
            dpg.add_spacer(height=5); dpg.add_text("Input Tuning")
            dpg.add_slider_float(label="Move Thresh", default_value=MOVEMENT_THRESHOLD, max_value=1.0, callback=update_param, user_data="move", tag="mv_slider", height=26)
            dpg.add_slider_float(label="Deadzone", default_value=DEADZONE, max_value=0.5, callback=update_param, user_data="dead", tag="dz_slider", height=26)
            dpg.add_slider_float(label="Trigger Threshold", default_value=TRIGGER_THRESHOLD, max_value=1.0, callback=update_param, user_data="trig", tag="tr_slider", height=26)
            dpg.add_spacer(height=5); dpg.add_separator(); dpg.add_spacer(height=5); dpg.add_text("Colors")
            with dpg.group(horizontal=True):
                dpg.add_color_picker(label="BG", default_value=gui_colors["background"], no_alpha=True, width=120, callback=update_color_config, user_data="background")
                dpg.add_color_picker(label="Text", default_value=gui_colors["text"], no_alpha=True, width=120, callback=update_color_config, user_data="text")
            with dpg.group(horizontal=True):
                dpg.add_color_picker(label="Tabs", default_value=gui_colors["tabs"], no_alpha=True, width=120, callback=update_color_config, user_data="tabs")
                dpg.add_color_picker(label="Active", default_value=gui_colors["sliders"], no_alpha=True, width=120, callback=update_color_config, user_data="sliders")

        # ─── PROFILES TAB ───
        with dpg.tab(label="Profiles"):
            dpg.add_spacer(height=5); dpg.add_text("Configuration Manager"); dpg.add_separator(); dpg.add_spacer(height=5)
            dpg.add_input_text(label="Name", tag="profile_name", height=30)
            dpg.add_button(label="Save Profile", callback=save_profile, width=-1, height=42)
            dpg.add_spacer(height=5)
            dpg.add_combo(items=list(load_profiles_data().keys()) if os.path.exists(PROFILES_FILE) else [], label="Load", tag="profile_combo", callback=apply_loaded_profile, width=-1)

        # ─── HELP TAB ───
        with dpg.tab(label="Help"):
            dpg.add_spacer(height=5); dpg.add_text("Controls Reference"); dpg.add_separator()
            dpg.add_text("Left Stick  :  Move Character\nRight Stick :  Move Mouse Cursor\nR2 / RT     :  Left Click (Hold to Drag)\nL2 / LT     :  Right Click\nF1 Key      :  Toggle App ON/OFF\nF2 Key      :  Toggle Always on Top")
            dpg.add_spacer(height=10); dpg.add_text("Tips & Troubleshooting"); dpg.add_separator()
            dpg.add_text("- Window Position: Drag the top bar to move this window.\n- Focus Issue: If typing doesn't work, click the game window once.\n- Controller: If not detected, restart the app with controller plugged in.\n- Visualizer: You can view sticks moving here without affecting your mouse!", wrap=380)
            dpg.add_spacer(height=15)
            dpg.add_button(label="Reset All Settings to Defaults", callback=reset_defaults, width=-1, height=35)
            dpg.add_spacer(height=5)
            dpg.add_button(label="Open GitHub / Updates", callback=lambda: webbrowser.open(GITHUB_URL), width=-1, height=35)

dpg.set_primary_window("main_window", True)
dpg.show_viewport()

# Dark Mode Title Bar
try:
    hwnd = ctypes.windll.user32.FindWindowW(None, "JamPad Classic")
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
except: pass

apply_gui_colors()
GUI_READY = True

threading.Thread(target=poll_gamepad, daemon=True).start()
dpg.start_dearpygui()
dpg.destroy_context()
keyboard_listener.stop()
tray_icon.stop()
pygame.quit()