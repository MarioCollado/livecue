# ui/app_ui.py - VERSIÓN SIMPLIFICADA Y LIMPIA
import flet as ft
import time
from core.state import state
from core.playback import playback
from setlist.manager import manager
from ui.themes import ThemeManager
from ui.components import BeatIndicator, TempoDisplay, StatusBar, ProgressBar, MetronomeButton
from ui.header_component import create_header
from version_info import APP_VERSION

# ============================================
# CONFIGURACIÓN
# ============================================
DEBOUNCE_NAV_MS = 300

class TrackListView:
    """Vista de lista de tracks simplificada"""
    
    def __init__(self, theme: ThemeManager, page):
        self.theme = theme
        self.page = page
        self.drag_state = {"dragging_index": None}
        self.column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
    def update(self):
        self.column.controls.clear()
        state.track_progress_bars.clear()
        for idx, track in enumerate(state.tracks):
            self.column.controls.append(self._create_track_item(idx, track))
        self._safe_update()
    
    def _create_track_item(self, track_index: int, track):
        is_selected = track_index == state.current_index
        has_sections = len(track.sections) > 0
        is_expanded = track.expanded
        
        progress_bar = ProgressBar(self.theme.get, width=1220)
        state.track_progress_bars[track_index] = progress_bar
        progress_bar.container.visible = is_selected
        
        header = self._create_track_header(track_index, track, is_selected, has_sections, is_expanded, progress_bar)
        sections = self._create_sections(track_index, track) if is_expanded and has_sections else None
        
        track_column = ft.Column(spacing=0, controls=[header] + ([sections] if sections else []))
        drag_target = ft.DragTarget(
            group="tracks",
            content=track_column,
            on_accept=lambda e, idx=track_index: self._on_drag_accept(idx)
        )
        
        return ft.Draggable(
            group="tracks",
            content=drag_target,
            content_feedback=self._create_drag_feedback(track_index, track),
            on_drag_start=lambda e, idx=track_index: self._on_drag_start(idx)
        )
    
    def _create_track_header(self, track_index, track, is_selected, has_sections, is_expanded, progress_bar):
        return ft.Container(
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    f"{track_index + 1:02d}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE if is_selected else self.theme.get("text_primary"),
                                ),
                                width=36,
                                height=36,
                                border_radius=18,
                                bgcolor=self.theme.get("accent") if is_selected else self.theme.get("bg_secondary"),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=12),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        track.title,
                                        size=15,
                                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                                        color=self.theme.get("text_primary")
                                    ),
                                    ft.Text(
                                        f"{len(track.sections)} sections",
                                        size=11,
                                        color=self.theme.get("text_secondary"),
                                        visible=has_sections
                                    )
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.KEYBOARD_ARROW_DOWN if not is_expanded else ft.Icons.KEYBOARD_ARROW_UP,
                                icon_size=18,
                                on_click=lambda e, idx=track_index: self._toggle_expand(idx),
                                visible=has_sections,
                                icon_color=self.theme.get("accent"),
                            ),
                            ft.Icon(ft.Icons.DRAG_HANDLE, size=18, color=self.theme.get("text_secondary"), opacity=0.3)
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    progress_bar.container,
                    ft.Container(
                        width=None,
                        height=2,
                        bgcolor=self.theme.get("accent"),
                        margin=ft.margin.only(top=6),
                        visible=is_selected
                    )
                ]
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            border_radius=12,
            bgcolor=self.theme.get("bg_card") if is_selected else self.theme.get("bg_card") + "60",
            on_click=lambda e, idx=track_index: self._on_track_click(idx),
        )
    
    def _create_sections(self, track_index, track):
        section_items = []
        for sec_idx, section in enumerate(track.sections):
            section_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(width=48),
                            ft.Container(width=2, height=28, bgcolor=self.theme.get("accent"), opacity=0.4),
                            ft.Container(width=10),
                            ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, size=16, color=self.theme.get("accent"), opacity=0.7),
                            ft.Container(width=8),
                            ft.Text(section.name, size=13, weight=ft.FontWeight.W_500, expand=True, color=self.theme.get("text_primary"))
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border_radius=8,
                    bgcolor=self.theme.get("bg_secondary") + "60",
                    on_click=lambda e, t_idx=track_index, s_idx=sec_idx: self._on_section_click(t_idx, s_idx),
                    ink=True,
                )
            )
        return ft.Container(content=ft.Column(spacing=4, controls=section_items), padding=ft.padding.only(top=8))
    
    def _create_drag_feedback(self, track_index, track):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"{track_index + 1}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Container(width=10),
                    ft.Text(track.title, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
                ],
                spacing=0
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            width=320,
            border_radius=10,
            bgcolor=self.theme.get("accent"),
            opacity=0.95
        )
    
    def _on_track_click(self, track_index):
        state.current_index = track_index
        StatusBar.instance.update(f"Seleccionado: {state.tracks[track_index].title}", self.theme.get("accent"), self._safe_update)
        self.update()
    
    def _toggle_expand(self, track_index):
        state.tracks[track_index].expanded = not state.tracks[track_index].expanded
        self.update()
    
    def _on_section_click(self, track_index, section_index):
        if playback.jump_to_section(track_index, section_index):
            section = state.tracks[track_index].sections[section_index]
            StatusBar.instance.update(f"▶ {section.name}", self.theme.get("accent"), self._safe_update)
    
    def _on_drag_start(self, track_index):
        self.drag_state["dragging_index"] = track_index
    
    def _on_drag_accept(self, track_index):
        start_idx = self.drag_state["dragging_index"]
        if start_idx is None or start_idx == track_index:
            return
        
        moved_track = state.tracks.pop(start_idx)
        state.tracks.insert(track_index, moved_track)
        
        if state.current_index == start_idx:
            state.current_index = track_index
        elif start_idx < state.current_index <= track_index:
            state.current_index -= 1
        elif track_index <= state.current_index < start_idx:
            state.current_index += 1
        
        StatusBar.instance.update(f"✓ Reordenado: {moved_track.title}", self.theme.get("button_play"), self._safe_update)
        self.update()
        self.drag_state["dragging_index"] = None
    
    def _safe_update(self):
        try:
            self.page.update()
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[UPDATE ERROR] {e}")


class ControlPanel:
    """Panel de controles simplificado"""
    
    def __init__(self, theme: ThemeManager, page):
        self.theme = theme
        self.page = page
        self.last_nav_time = 0
        
        self.metronome_btn = MetronomeButton(theme.get, self._on_metronome_click)
        self.tempo_display = TempoDisplay(theme.get, state.current_tempo, state.time_signature_num)
        self.beat_indicator = BeatIndicator(theme.get)
        
        self.play_btn = self._create_button("PLAY", ft.Icons.PLAY_ARROW_ROUNDED, self._on_play, "button_play")
        self.stop_btn = self._create_button("STOP", ft.Icons.STOP_ROUNDED, self._on_stop, "button_stop")
        self.prev_btn = self._create_nav_btn(ft.Icons.SKIP_PREVIOUS_ROUNDED, self._on_prev)
        self.next_btn = self._create_nav_btn(ft.Icons.SKIP_NEXT_ROUNDED, self._on_next)
        self.scan_btn = self._create_button("SCAN", ft.Icons.SEARCH_ROUNDED, self._on_scan, "button_scan")
        
        self.container = ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            self.metronome_btn.button,
                            self.tempo_display.text,
                            self.beat_indicator.container,
                            StatusBar.instance.text if hasattr(StatusBar, 'instance') else ft.Text("")
                        ]
                    ),
                    border_radius=12,
                    padding=ft.padding.all(18)
                ),
                ft.Divider(thickness=1, color=self.theme.get("accent"), height=8),
                ft.Container(
                    content=ft.Column(
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.play_btn,
                            self.stop_btn,
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[self.prev_btn, self.next_btn]),
                            self.scan_btn
                        ]
                    ),
                    border_radius=12,
                    padding=ft.padding.all(18),
                    expand=True
                )
            ]
        )

    def _create_button(self, text, icon, on_click, color_key):
        return ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(icon, size=24, color=ft.Colors.WHITE),
                    ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ]
            ),
            width=220,
            height=90,
            border_radius=10,
            bgcolor=self.theme.get(color_key),
            on_click=on_click,
            ink=True,
        )
    
    def _create_nav_btn(self, icon, on_click):
        return ft.Container(
            content=ft.Icon(icon, size=28, color=ft.Colors.WHITE),
            width=92,
            height=72,
            border_radius=12,
            bgcolor=self.theme.get("button_nav"),
            on_click=on_click,
            ink=True,
            alignment=ft.alignment.center,
        )
    
    def _on_metronome_click(self, e):
        is_on = playback.toggle_metronome()
        self.metronome_btn.set_state(is_on, self._safe_update)
        StatusBar.instance.update(
            f"Metrónomo: {'ON' if is_on else 'OFF'}",
            self.theme.get("button_metro_on") if is_on else self.theme.get("text_secondary"),
            self._safe_update
        )
    
    def _on_play(self, e):
        if state.current_index < 0:
            StatusBar.instance.update("Sin track seleccionado", self.theme.get("button_stop"), self._safe_update)
            return
        if state.is_playing:
            playback.stop()
            time.sleep(0.15)
        if playback.play_track(state.current_index):
            track = state.tracks[state.current_index]
            StatusBar.instance.update(f"▶ Play: {track.title}", self.theme.get("button_play"), self._safe_update)
    
    def _on_stop(self, e):
        playback.stop()
        StatusBar.instance.update("■ Stop", self.theme.get("button_stop"), self._safe_update)
    
    def _on_next(self, e):
        if self._check_nav_debounce() and playback.next_track():
            time.sleep(0.1)
            TrackListView.instance.update()
    
    def _on_prev(self, e):
        if self._check_nav_debounce() and playback.prev_track():
            time.sleep(0.1)
            TrackListView.instance.update()
    
    def _on_scan(self, e):
        StatusBar.instance.update("Escaneando...", self.theme.get("button_scan"), self._safe_update)
        playback.scan_all()
        time.sleep(0.3)
        state.current_index = 0 if state.tracks else -1
        TrackListView.instance.update()
    
    def _check_nav_debounce(self) -> bool:
        now = time.time()
        if now - self.last_nav_time < DEBOUNCE_NAV_MS / 1000:
            return False
        self.last_nav_time = now
        return True
    
    def _safe_update(self):
        try:
            self.page.update()
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[UPDATE ERROR] {e}")


class DialogManager:
    """Gestor de diálogos simplificado"""
    
    def __init__(self, page, theme: ThemeManager):
        self.page = page
        self.theme = theme
    
    def show_save_setlist(self):
        if not state.locators:
            StatusBar.instance.update("⚠️ Sin locators. Presiona SCAN primero", self.theme.get("button_stop"), self._safe_update)
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
        
        def close_dlg(e):
            dlg.open = False
            self._safe_update()
        
        def do_save(e):
            name = name_field.value.strip()
            if not name:
                error_text.value = "⚠️ Debes ingresar un nombre"
                error_text.visible = True
                self._safe_update()
                return
            
            if manager.save(name, state.locators, state.tracks):
                sections_count = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.update(
                    f"✓ '{name}' guardado ({len(state.locators)} locators, {len(state.tracks)} tracks, {sections_count} sections)",
                    self.theme.get("button_play"),
                    self._safe_update
                )
                close_dlg(None)
                self._update_setlist_counter()
            else:
                error_text.value = "❌ Error al guardar"
                error_text.visible = True
                self._safe_update()
        
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
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.FilledButton("💾 Guardar", on_click=do_save)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)
    
    def show_load_setlist(self):
        saved = manager.list_all()
        
        def close_dlg(e):
            dlg.open = False
            self._safe_update()
        
        def do_load(e):
            if not dropdown.value:
                return
            
            data = manager.load(dropdown.value)
            if not data or "locators" not in data:
                StatusBar.instance.update("❌ Error al cargar", self.theme.get("button_stop"), self._safe_update)
                return
            
            state.locators = data["locators"]
            if "tracks" in data:
                state.tracks = data["tracks"]
            
            state.current_index = 0 if state.tracks else -1
            TrackListView.instance.update()
            
            total_sections = sum(len(t.sections) for t in state.tracks)
            StatusBar.instance.update(
                f"✓ '{data['name']}' cargado ({len(state.locators)} locators, {len(state.tracks)} tracks, {total_sections} sections)",
                self.theme.get("button_play"),
                self._safe_update
            )
            close_dlg(None)
        
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
                    ft.Text(f"📁 {len(saved)} setlist(s) disponible(s)", size=12, italic=True, color=self.theme.get("text_secondary"))
                ]
            )
            actions = [
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.FilledButton("📂 Cargar", on_click=do_load)
            ]
        else:
            content = ft.Column(
                width=400,
                tight=True,
                spacing=12,
                controls=[
                    ft.Text("No hay setlists guardados", size=14, color=self.theme.get("text_primary")),
                    ft.Text("💡 Usa el botón 💾 para guardar tu primer setlist", size=11, italic=True, color=self.theme.get("text_secondary"))
                ]
            )
            actions = [ft.TextButton("Cerrar", on_click=close_dlg)]
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 Cargar Setlist", color=self.theme.get("text_primary")),
            bgcolor=self.theme.get("bg_secondary"),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)
    
    def _update_setlist_counter(self):
        count = len(manager.list_all())
        if hasattr(self, 'save_counter'):
            self.save_counter.value = f"💾 {count}"
            self._safe_update()
    
    def _safe_update(self):
        try:
            self.page.update()
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[UPDATE ERROR] {e}")

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main(page: ft.Page):
    try:
        print("[UI] Inicializando página...")
        state.page_ref = page
        
        page.title = "Ableton Setlist Controller"
        page.window.width = 900
        page.window.height = 800
        page.window.resizable = True
        page.window.maximized = True
        page.padding = 0
        page.spacing = 0
        page.theme_mode = ft.ThemeMode.DARK
        
        print("[UI] Creando componentes...")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return
    
    theme = ThemeManager("Mono Dark")
    page.theme = ft.Theme(color_scheme_seed=theme.get("accent"))
    
    status_bar = StatusBar(theme.get)
    StatusBar.instance = status_bar
    
    track_list = TrackListView(theme, page)
    TrackListView.instance = track_list
    
    control_panel = ControlPanel(theme, page)
    dialog_manager = DialogManager(page, theme)
    
    save_counter = ft.Text(f"💾 {len(manager.list_all())}", size=12, weight=ft.FontWeight.W_500, color=theme.get("text_primary"))
    
    def update_setlist_counter():
        save_counter.value = f"💾 {len(manager.list_all())}"
        try:
            page.update()
        except:
            pass
    
    dialog_manager.save_counter = save_counter
    
    save_btn = ft.IconButton(icon=ft.Icons.SAVE, on_click=lambda e: dialog_manager.show_save_setlist(), icon_size=22)
    load_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=lambda e: dialog_manager.show_load_setlist(), icon_size=22)
    
    palette_dropdown = ft.Dropdown(
        width=180,
        value=theme.current_name,
        options=[ft.dropdown.Option(name) for name in ThemeManager.list_themes()],
        text_size=13,
        bgcolor=theme.get("bg_card") + "00",
        border_color=theme.get("accent") + "00",
        focused_border_color=theme.get("accent") + "00",
        text_style=ft.TextStyle(weight=ft.FontWeight.W_600, color=theme.get("text_primary")),
        content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
    )
    
    def on_theme_change(e):
        theme.set_theme(palette_dropdown.value)
        apply_colors()
        StatusBar.instance.update(f"Paleta: {theme.current_name}", theme.get("accent"), lambda: page.update())
    
    palette_dropdown.on_change = on_theme_change
    
    header_container = create_header(
        page,
        palette_dropdown,
        save_counter,
        save_btn,
        load_btn,
        theme.get
    )
    
    listbox_container = ft.Container(
        content=track_list.column,
        expand=True,
        border_radius=12,
        padding=ft.padding.all(18),
        bgcolor=theme.get("bg_card") + "40",
    )
    
    main_row = ft.Row(
        spacing=18,
        expand=True,
        controls=[
            ft.Column(expand=True, spacing=0, controls=[listbox_container]),
            ft.Container(width=250, content=control_panel.container)
        ]
    )
    
    page.add(
        ft.Container(
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    header_container,
                    ft.Container(
                        expand=True,
                        padding=ft.padding.only(left=18, right=18, bottom=18, top=10),
                        content=main_row
                    )
                ]
            )
        )
    )
    
    def trigger_pulse(beat: int):
        control_panel.beat_indicator.pulse(beat, state.time_signature_num, lambda: page.update())
    
    def update_tempo_display():
        control_panel.tempo_display.update(state.current_tempo, state.time_signature_num, lambda: page.update())
    
    def update_track_progress(current_beat: float):
        if 0 <= state.current_index < len(state.tracks):
            track = state.tracks[state.current_index]
            progress_bar = state.track_progress_bars.get(state.current_index)
            if progress_bar:
                progress = track.get_progress(current_beat)
                progress_bar.update_progress(progress)
    
    def update_listbox():
        track_list.update()
    
    def update_metronome_ui():
        control_panel.metronome_btn.set_state(state.metronome_on, lambda: page.update())
    
    page.trigger_pulse = trigger_pulse
    page.update_tempo_display = update_tempo_display
    page.update_track_progress = update_track_progress
    page.update_listbox = update_listbox
    page.update_metronome_ui = update_metronome_ui
    
    def apply_colors():
        page.bgcolor = theme.get("bg_main")
        listbox_container.bgcolor = theme.get("bg_card") + "40"
        
        new_header = create_header(
            page,
            palette_dropdown,
            save_counter,
            save_btn,
            load_btn,
            theme.get
        )
        
        page.controls[0].content.controls[0] = new_header
        
        control_panel.beat_indicator.container.bgcolor = theme.get("bg_card")
        control_panel.tempo_display.text.color = theme.get("text_primary")
                
        track_list.update()
        page.update()
    
    apply_colors()
    
    time.sleep(1)
    playback.scan_all()
    
    print("[INIT] ✓ App lista\n")