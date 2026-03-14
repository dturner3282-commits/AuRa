"""
AuRA — The Mirror (Android / Desktop)
======================================
Minimal Kivy app. One big empty input box.
Type a file path, search query, or drop a file.
Routes to the signal engine, GDT Easter egg, or file info.

Build APK with: buildozer android debug
"""

import os
import sys
import threading

# Ensure engine is importable from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.lang import Builder

# ============================================================
# KV LAYOUT — Minimal mirror
# ============================================================

KV = """
#:import dp kivy.metrics.dp

<MirrorScreen>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.04, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # ── Title ──
    Label:
        text: 'AURA'
        size_hint_y: None
        height: dp(40)
        font_size: dp(13)
        color: 0.35, 0.35, 0.35, 1
        letter_spacing: dp(4)

    # ── The Box — input area ──
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        size_hint_y: 0.45

        TextInput:
            id: input_box
            hint_text: 'drop a file or type'
            hint_text_color: 0.2, 0.2, 0.2, 1
            background_color: 0.07, 0.07, 0.07, 1
            foreground_color: 0.88, 0.88, 0.88, 1
            cursor_color: 0.5, 0.5, 0.5, 1
            font_size: dp(15)
            font_name: 'RobotoMono'
            multiline: True
            padding: dp(16), dp(16)
            on_text_validate: root.on_submit()

    # ── Action buttons row (appears after detection) ──
    BoxLayout:
        id: actions_row
        size_hint_y: None
        height: dp(44) if root.has_actions else 0
        opacity: 1 if root.has_actions else 0
        padding: dp(16), 0
        spacing: dp(6)

    # ── Browse button ──
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        padding: dp(16), 0
        spacing: dp(8)

        Button:
            text: 'browse'
            font_size: dp(12)
            background_color: 0.12, 0.12, 0.12, 1
            background_normal: ''
            color: 0.5, 0.5, 0.5, 1
            on_release: root.open_file_picker()

        Button:
            text: 'go'
            font_size: dp(12)
            background_color: 0.12, 0.12, 0.12, 1
            background_normal: ''
            color: 0.5, 0.5, 0.5, 1
            on_release: root.on_submit()

    # ── Output area ──
    ScrollView:
        do_scroll_x: False
        bar_width: dp(3)
        bar_color: 0.25, 0.25, 0.25, 0.5

        Label:
            id: output_label
            text: root.output_text
            size_hint_y: None
            height: self.texture_size[1] + dp(20)
            text_size: self.width - dp(32), None
            font_size: dp(13)
            color: 0.6, 0.6, 0.6, 1
            halign: 'left'
            valign: 'top'
            padding: dp(16), dp(8)
"""


# ============================================================
# FILE TYPE DETECTION (inline, no external deps beyond stdlib)
# ============================================================

AUDIO_EXTS = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac', '.wma'}
CODE_EXTS = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.rs', '.go',
             '.rb', '.php', '.swift', '.kt', '.cs', '.lua', '.sh', '.bash'}
CONFIG_EXTS = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.xml',
               '.env', '.conf'}
TEXT_EXTS = {'.txt', '.md', '.rst', '.csv', '.log', '.tex'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico'}


def detect_category(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in AUDIO_EXTS:
        return 'audio'
    if ext in CODE_EXTS:
        return 'code'
    if ext in CONFIG_EXTS:
        return 'config'
    if ext in TEXT_EXTS:
        return 'text'
    if ext in IMAGE_EXTS:
        return 'image'
    return 'binary'


def get_actions(category):
    """Return list of (key, label) tuples for the given category."""
    if category == 'audio':
        return [('decode', 'Decode signal'), ('freq', 'Frequencies'), ('info', 'File info')]
    if category == 'code':
        return [('detect', 'Find gaps'), ('fix', 'Fix code'), ('info', 'File info')]
    if category == 'config':
        return [('validate', 'Validate'), ('info', 'File info')]
    if category in ('text', 'image', 'binary'):
        return [('info', 'File info')]
    return [('info', 'File info')]


# ============================================================
# GDT Easter Egg
# ============================================================

GDT_TEXT = """Uncle Greg's Gap Detection Technology (GDT)

G = |E - O|        Gap magnitude (expected vs observed)
C = [L, U]         Confidence interval
Classifier         Binary gap / no-gap decision
S = 1 - (SumG / N) Soundness score
Delta + C Engine   Iterative gap closure

Thank you, Greg, for the ideas and groundwork
that helped spark this project.
Your thinking opened the gap. We followed it."""

GDT_TRIGGERS = {'greg turner', 'uncle greg', 'gdt', 'greg'}


# ============================================================
# SCREEN CLASS
# ============================================================

class MirrorScreen(BoxLayout):
    output_text = StringProperty('')
    has_actions = BooleanProperty(False)
    _current_path = None
    _current_category = None

    def on_submit(self):
        text = self.ids.input_box.text.strip()
        if not text:
            return

        # Easter egg check
        if text.lower() in GDT_TRIGGERS:
            self.output_text = GDT_TEXT
            self._clear_actions()
            return

        # File path check
        if os.path.isfile(text):
            self._current_path = text
            self._current_category = detect_category(text)
            self._show_actions()
            self.output_text = '%s detected: %s' % (
                self._current_category, os.path.basename(text))
            return

        # Just echo text back for now
        self.output_text = text

    def _show_actions(self):
        row = self.ids.actions_row
        row.clear_widgets()
        actions = get_actions(self._current_category)
        for key, label in actions:
            btn = Button(
                text=label,
                font_size=dp(12),
                background_color=(0.12, 0.12, 0.12, 1),
                background_normal='',
                color=(0.7, 0.7, 0.7, 1),
            )
            btn.bind(on_release=lambda inst, k=key: self._run_action(k))
            row.add_widget(btn)
        self.has_actions = True

    def _clear_actions(self):
        self.ids.actions_row.clear_widgets()
        self.has_actions = False

    def _run_action(self, key):
        if not self._current_path:
            return

        self.output_text = 'processing...'

        if key == 'decode' and self._current_category == 'audio':
            # Run signal decode in background thread
            thread = threading.Thread(
                target=self._decode_signal, daemon=True)
            thread.start()
            return

        if key == 'freq' and self._current_category == 'audio':
            thread = threading.Thread(
                target=self._freq_inventory, daemon=True)
            thread.start()
            return

        if key == 'info':
            self._show_file_info()
            return

        self.output_text = '%s: not yet implemented' % key

    def _decode_signal(self):
        try:
            from engine import decode_file
            result = decode_file(self._current_path)
            word = result.get('decoded_word', '---')
            meaning = result.get('decoded_meaning', '')
            ecl = result.get('ecl', 0)
            confidence = result.get('confidence', '?')
            signal_type = result.get('signal_type', '?')
            report = result.get('technical_report', '')

            text = '%s = "%s"\nECL: %.1f / 7.0\nConfidence: %s\nSignal: %s' % (
                word, meaning, ecl, confidence, signal_type)
            if report:
                text += '\n\n' + report

            Clock.schedule_once(lambda dt: setattr(self, 'output_text', text))
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self, 'output_text', 'Error: %s' % str(e)))

    def _freq_inventory(self):
        try:
            from engine import decode_file
            import numpy as np
            from scipy.io import wavfile

            rate, data = wavfile.read(self._current_path)
            if len(data.shape) > 1:
                data = data[:, 0]
            data = data.astype(np.float64)

            fft = np.fft.rfft(data)
            freqs = np.fft.rfftfreq(len(data), 1.0 / rate)
            magnitudes = np.abs(fft)

            # Top 20 frequencies
            top_idx = np.argsort(magnitudes)[-20:][::-1]
            lines = ['Top frequencies:']
            for i in top_idx:
                if freqs[i] > 20:
                    lines.append('  %.1f Hz  (mag: %.0f)' % (freqs[i], magnitudes[i]))

            Clock.schedule_once(
                lambda dt: setattr(self, 'output_text', '\n'.join(lines)))
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self, 'output_text', 'Error: %s' % str(e)))

    def _show_file_info(self):
        path = self._current_path
        try:
            size = os.path.getsize(path)
            if size < 1024:
                size_str = '%d B' % size
            elif size < 1024 * 1024:
                size_str = '%.1f KB' % (size / 1024)
            else:
                size_str = '%.1f MB' % (size / (1024 * 1024))

            ext = os.path.splitext(path)[1]
            self.output_text = (
                'File: %s\n'
                'Size: %s\n'
                'Type: %s\n'
                'Category: %s\n'
                'Path: %s'
            ) % (os.path.basename(path), size_str, ext, self._current_category, path)
        except Exception as e:
            self.output_text = 'Error: %s' % str(e)

    def open_file_picker(self):
        content = BoxLayout(orientation='vertical', spacing=dp(8))

        try:
            from android.storage import primary_external_storage_path
            start_path = primary_external_storage_path()
        except ImportError:
            start_path = os.path.expanduser('~')

        chooser = FileChooserListView(
            path=start_path,
            size_hint_y=1,
        )

        btn_bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        cancel_btn = Button(
            text='Cancel',
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            color=(0.8, 0.8, 0.8, 1),
        )
        select_btn = Button(
            text='Select',
            background_color=(0.15, 0.15, 0.25, 1),
            background_normal='',
            color=(0.8, 0.8, 0.8, 1),
        )
        btn_bar.add_widget(cancel_btn)
        btn_bar.add_widget(select_btn)

        content.add_widget(chooser)
        content.add_widget(btn_bar)

        popup = Popup(
            title='Select File',
            content=content,
            size_hint=(0.95, 0.9),
        )

        def on_select(instance):
            if chooser.selection:
                path = chooser.selection[0]
                self.ids.input_box.text = path
                self._current_path = path
                self._current_category = detect_category(path)
                self._show_actions()
                self.output_text = '%s detected: %s' % (
                    self._current_category, os.path.basename(path))
            popup.dismiss()

        def on_cancel(instance):
            popup.dismiss()

        select_btn.bind(on_release=on_select)
        cancel_btn.bind(on_release=on_cancel)
        popup.open()


# ============================================================
# APP
# ============================================================

class AuraApp(App):
    title = 'AuRA'

    def build(self):
        Builder.load_string(KV)
        Window.clearcolor = (0.04, 0.04, 0.04, 1)
        return MirrorScreen()

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    AuraApp().run()
