# ui/dialogs.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
from core.state import state
from ui.components import StatusBar
import asyncio
from ui.themes import ThemeManager
from setlist.manager import manager
from core.playback import playback
from ui.track_list import TrackListView
from core.i18n import i18n

# ============================================
# DIALOG MANAGER
# ============================================
class DialogManager:
    def __init__(self, page: ft.Page, theme: ThemeManager):
        self.page = page
        self.theme = theme

    async def show_save_setlist(self):
        if not state.locators:
            StatusBar.instance.text.value = f"● {i18n.get('dialog_save_warning_no_locators')}"
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
            return

        name_field = ft.TextField(
            label=i18n.get("dialog_save_name_label"),
            width=350,
            autofocus=True,
            hint_text=i18n.get("dialog_save_name_hint"),
            bgcolor=self.theme.get("bg_card"),
            color=self.theme.get("text_primary"),
            border_color=self.theme.get("accent"),
        )
        error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

        async def close_dlg(e=None):
            dlg.open = False
            self.page.update()

        async def do_save(e=None):
            name = name_field.value.strip()
            if not name:
                error_text.value = i18n.get("dialog_save_error_empty_name")
                error_text.visible = True
                self.page.update()
                return

            if manager.save(name, state.locators, state.tracks):
                sections_count = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.text.value = f"● {i18n.get('dialog_save_success', name, len(state.locators), len(state.tracks), sections_count)}"
                StatusBar.instance.text.color = self.theme.get("button_play")
                await close_dlg()
                await self._update_setlist_counter()
            else:
                error_text.value = i18n.get("dialog_save_error_failed")
                error_text.visible = True
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(i18n.get("dialog_save_title"), color=self.theme.get("text_primary")),
            bgcolor=self.theme.get("bg_secondary"),
            content=ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    name_field,
                    ft.Text(
                        i18n.get("dialog_save_info", len(state.locators), len(state.tracks)),
                        size=12, 
                        italic=True, 
                        color=self.theme.get("text_secondary")
                    ),
                    error_text
                ]
            ),
            actions=[
                ft.TextButton(i18n.get("cancel"), on_click=lambda e: self.page.run_task(close_dlg, e)),
                ft.FilledButton(i18n.get("btn_save"), on_click=lambda e: self.page.run_task(do_save, e))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)

    async def show_load_setlist(self):
        saved = manager.list_all()

        async def close_dlg(e=None):
            dlg.open = False
            self.page.update()

        async def do_load(e=None):
            if not dropdown.value:
                return

            try:
                data = manager.load(dropdown.value)
                if not data or "locators" not in data:
                    StatusBar.instance.text.value = f"● {i18n.get('dialog_load_error')}"
                    StatusBar.instance.text.color = self.theme.get("button_stop")
                    self.page.update()
                    return

                if state.is_playing:
                    playback.stop()
                    await asyncio.sleep(0.2)

                state.locators = data["locators"]
                if "tracks" in data:
                    state.tracks = data["tracks"]

                state.current_index = 0 if state.tracks else -1

                await TrackListView.instance.update(force_refresh=True)

                total_sections = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.text.value = f"● {i18n.get('dialog_load_success', data['name'], len(state.locators), len(state.tracks), total_sections)}"
                StatusBar.instance.text.color = self.theme.get("button_play")
                self.page.update()
                await close_dlg()
            except Exception as ex:
                print(f"[ERROR] do_load: {ex}")
                import traceback
                traceback.print_exc()

        if saved:
            dropdown = ft.Dropdown(
                label=i18n.get("dialog_load_dropdown_label"),
                options=[ft.dropdown.Option(name) for name in saved],
                width=350,
                bgcolor=self.theme.get("bg_card"),
                border_color=self.theme.get("accent"),
            )
            content = ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    dropdown,
                    ft.Text(
                        i18n.get("dialog_load_count", len(saved)), 
                        size=12, 
                        italic=True,
                        color=self.theme.get("text_secondary")
                    )
                ]
            )
            actions = [
                ft.TextButton(i18n.get("cancel"), on_click=lambda e: self.page.run_task(close_dlg, e)),
                ft.FilledButton(i18n.get("btn_load"), on_click=lambda e: self.page.run_task(do_load, e))
            ]
        else:
            content = ft.Column(
                width=400,
                tight=True,
                spacing=12,
                controls=[
                    ft.Text(i18n.get("dialog_load_empty"), size=14, color=self.theme.get("text_primary")),
                    ft.Text(
                        i18n.get("dialog_load_empty_hint"), 
                        size=11, 
                        italic=True,
                        color=self.theme.get("text_secondary")
                    )
                ]
            )
            actions = [ft.TextButton(i18n.get("close"), on_click=lambda e: self.page.run_task(close_dlg, e))]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(i18n.get("dialog_load_title"), color=self.theme.get("text_primary")),
            bgcolor=self.theme.get("bg_secondary"),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)

    async def _update_setlist_counter(self):
            count = len(manager.list_all())
            if hasattr(self, 'save_counter'):
                self.save_counter.value = f"💾 {count}"
                self.page.update()
