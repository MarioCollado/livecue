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

# ============================================
# DIALOG MANAGER
# ============================================
class DialogManager:
    def __init__(self, page: ft.Page, theme: ThemeManager):
        self.page = page
        self.theme = theme

    async def show_save_setlist(self):
        if not state.locators:
            StatusBar.instance.text.value = "● ⚠️ Sin locators. Presiona SCAN primero"
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
            return

        name_field = ft.TextField(
            label="Nombre del setlist",
            width=350,
            autofocus=True,
            hint_text="Ej: Concierto 2024",
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
                error_text.value = "⚠️ Debes ingresar un nombre"
                error_text.visible = True
                self.page.update()
                return

            if manager.save(name, state.locators, state.tracks):
                sections_count = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.text.value = f"● ✓ '{name}' guardado ({len(state.locators)} locators, {len(state.tracks)} tracks, {sections_count} sections)"
                StatusBar.instance.text.color = self.theme.get("button_play")
                await close_dlg()
                await self._update_setlist_counter()
            else:
                error_text.value = "✖ Error al guardar"
                error_text.visible = True
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("💾 Guardar Setlist", color=self.theme.get("text_primary")),
            bgcolor=self.theme.get("bg_secondary"),
            content=ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    name_field,
                    ft.Text(
                        f"Se guardarán {len(state.locators)} locators y {len(state.tracks)} tracks",
                        size=12, 
                        italic=True, 
                        color=self.theme.get("text_secondary")
                    ),
                    error_text
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.run_task(close_dlg, e)),
                ft.FilledButton("💾 Guardar", on_click=lambda e: self.page.run_task(do_save, e))
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
                    StatusBar.instance.text.value = "● ✖ Error al cargar"
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

                await TrackListView.instance.update()

                total_sections = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.text.value = f"● ✓ '{data['name']}' cargado ({len(state.locators)} locators, {len(state.tracks)} tracks, {total_sections} sections)"
                StatusBar.instance.text.color = self.theme.get("button_play")
                self.page.update()
                await close_dlg()
            except Exception as ex:
                print(f"[ERROR] do_load: {ex}")
                import traceback
                traceback.print_exc()

        if saved:
            dropdown = ft.Dropdown(
                label="Setlists guardados",
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
                        f"📁 {len(saved)} setlist(s) disponible(s)", 
                        size=12, 
                        italic=True,
                        color=self.theme.get("text_secondary")
                    )
                ]
            )
            actions = [
                ft.TextButton("Cancelar", on_click=lambda e: self.page.run_task(close_dlg, e)),
                ft.FilledButton("📂 Cargar", on_click=lambda e: self.page.run_task(do_load, e))
            ]
        else:
            content = ft.Column(
                width=400,
                tight=True,
                spacing=12,
                controls=[
                    ft.Text("No hay setlists guardados", size=14, color=self.theme.get("text_primary")),
                    ft.Text(
                        "💡 Usa el botón 💾 para guardar tu primer setlist", 
                        size=11, 
                        italic=True,
                        color=self.theme.get("text_secondary")
                    )
                ]
            )
            actions = [ft.TextButton("Cerrar", on_click=lambda e: self.page.run_task(close_dlg, e))]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 Cargar Setlist", color=self.theme.get("text_primary")),
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
