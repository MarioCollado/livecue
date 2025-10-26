# ui/app_ui.py
import flet as ft
import threading
import time

from ui.themes import color_schemes
from ui.components import make_beat_indicators
from version_info import APP_VERSION

from core import state
from core.constants import *
from osc import client as osc_client 
from osc.client import send_message
from setlist import manager as setlist_manager

def main(page: ft.Page):
    # enlazar referencia a page en state
    state.page_ref = page

    page.title = "Ableton Cuelist Controller"
    page.window.width = 900
    page.window.height = 800
    page.window.resizable = True
    page.window.maximized = True
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.DARK
    current_theme = list(color_schemes.keys())[0]

    drag_state = {"dragging_index": None}
    beat_polling_active = {"value": True}

    def beat_poller():
        print("[POLLING] Iniciando beat poller...")
        while beat_polling_active["value"]:
            try:
                if state.is_playing:
                    osc_client.send_message("/live/song/get/beat", [])
                    osc_client.send_message("/live/song/get/current_song_time", [])
                    osc_client.send_message("/live/song/get/playing_status", [])
                time.sleep(0.08)
            except Exception as e:
                print(f"[POLLING ERROR] {e}")
                time.sleep(1)

    threading.Thread(target=beat_poller, daemon=True).start()

    def get_color(key):
        return color_schemes[current_theme][key]

    status_text = ft.Text("● Esperando...", size=12, weight=ft.FontWeight.W_500)

    def update_status(msg, color=None):
        status_text.value = f"● {msg}"
        status_text.color = color or get_color("text_secondary")
        page.update()

    def change_palette(e):
        nonlocal current_theme
        current_theme = palette_dropdown.value
        apply_colors()
        update_status(f"Paleta: {current_theme}", get_color("accent"))

    palette_dropdown = ft.Dropdown(
        width=200,
        value=current_theme,
        options=[ft.dropdown.Option(name) for name in color_schemes.keys()],
        on_change=change_palette,
        text_size=12,
        dense=True,
    )

    # --- PULSO VISUAL ---
    beat_indicator = ft.Container(
        width=55,
        height=55,
        border_radius=27,
        bgcolor=get_color("bg_card"),
        alignment=ft.alignment.center,
        content=ft.Icon(
            ft.Icons.CIRCLE,
            size=20,
            color=get_color("text_secondary"),
        ),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

    tempo_display = ft.Text(
        f"{state.current_tempo} BPM | {state.time_signature_num}/4", 
        size=13, 
        weight=ft.FontWeight.W_600, 
        color=get_color("text_primary")
    )

    def trigger_pulse(beat):
        try:
            # Activar pulso en CUALQUIER beat, no solo el 1
            beat_indicator.bgcolor = get_color("pulse_color")
            beat_indicator.scale = 1.15
            page.update()
            
            # Después de 80ms, volver al estado normal
            def reset_pulse():
                time.sleep(0.08)
                beat_indicator.bgcolor = get_color("bg_card")
                beat_indicator.scale = 1.0
                page.update()
            
            threading.Thread(target=reset_pulse, daemon=True).start()
            
        except Exception as e:
            print(f"[UI ERROR] Error en trigger_pulse: {e}")
            
    def update_tempo_display():
        try:
            tempo_display.value = f"{state.current_tempo:.0f} BPM | {state.time_signature_num}/4"
            page.update()
        except Exception as e:
            print(f"Error actualizando tempo: {e}")

    page.trigger_pulse = trigger_pulse
    page.update_tempo_display = update_tempo_display

    # --- METRONOME ---
    def toggle_metronome(e):
        state.metronome_on = not state.metronome_on
        print(f"[USER] Toggle metrónomo → {state.metronome_on}")
        osc_client.send_message("/live/song/set/metronome", [1 if state.metronome_on else 0])
        update_metronome_ui()

    def update_metronome_ui():
        metro_button.icon = ft.Icons.MUSIC_NOTE if state.metronome_on else ft.Icons.MUSIC_OFF
        metro_button.text = "CLICK ON" if state.metronome_on else "CLICK OFF"
        metro_button.style = ft.ButtonStyle(
            color=get_color("button_text"),
            bgcolor=get_color("button_metro_on") if state.metronome_on else get_color("button_metro"),
        )
        update_status(
            f"Metrónomo: {'ON' if state.metronome_on else 'OFF'}",
            get_color("button_metro_on") if state.metronome_on else get_color("text_secondary"),
        )
        page.update()

    page.update_metronome_ui = update_metronome_ui

    metro_button = ft.ElevatedButton(
        icon=ft.Icons.MUSIC_OFF,
        text="CLICK OFF",
        on_click=toggle_metronome,
        width=200,
        height=100,
    )

    # --- SETLIST MANAGEMENT ---
    def save_setlist_dialog(e):
        print(f"\n[UI] Abriendo diálogo de guardar setlist...")
        if not state.locators:
            update_status("⚠️ Sin locators. Presiona SCAN primero", get_color("button_stop"))
            return

        name_field = ft.TextField(
            label="Nombre del setlist",
            width=350,
            autofocus=True,
            hint_text="Ej: Concierto 2024",
            bgcolor=get_color("bg_card"),
            color=get_color("text_primary"),
            border_color=get_color("accent"),
        )

        error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

        def close_dlg(e):
            dlg.open = False
            page.update()

        def do_save(e):
            name = name_field.value.strip()
            if not name:
                error_text.value = "⚠️ Debes ingresar un nombre"
                error_text.visible = True
                page.update()
                return

            locators_to_save = sorted(state.locators, key=lambda x: x["beat"])
            success = setlist_manager.save_setlist(name, locators_to_save)

            if success:
                update_status(f"✓ '{name}' guardado ({len(locators_to_save)} locators)", get_color("button_play"))
                close_dlg(None)
                update_setlist_counter()
            else:
                error_text.value = "❌ Error al guardar el archivo"
                error_text.visible = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("💾 Guardar Setlist", color=get_color("text_primary")),
            bgcolor=get_color("bg_secondary"),
            content=ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    name_field,
                    ft.Text(f"Se guardarán {len(state.locators)} locators", size=12, italic=True, color=get_color("text_secondary")),
                    error_text
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg, style=ft.ButtonStyle(color=get_color("text_secondary"))),
                ft.FilledButton("💾 Guardar", on_click=do_save, style=ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color("accent")))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    def load_setlist_dialog(e):
        saved = setlist_manager.list_setlists()

        def close_dlg(e):
            dlg.open = False
            page.update()

        def do_load(e):
            if dropdown.value:
                data = setlist_manager.load_setlist(dropdown.value)
                if data and "locators" in data:
                    state.locators = sorted(data["locators"], key=lambda x: x["beat"])
                    # Forzar re-parsing desde handlers
                    from osc.handlers import cue_handler
                    # Convertir de nuevo a formato args
                    args = []
                    for loc in state.locators:
                        args.append(loc["name"])
                        args.append(loc["beat"])
                    cue_handler("/live/song/get/cue_points", *args)
                    update_listbox()
                    update_status(f"✓ '{data['name']}' cargado ({len(state.locators)} locators)", get_color("button_play"))
                    close_dlg(None)
                else:
                    update_status("❌ Error al cargar", get_color("button_stop"))

        if saved:
            dropdown = ft.Dropdown(
                label="Setlists guardados",
                options=[ft.dropdown.Option(name) for name in saved],
                width=350,
                bgcolor=get_color("bg_card"),
                color=get_color("text_primary"),
                border_color=get_color("accent"),
            )
            content = ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    dropdown,
                    ft.Text(f"📁 {len(saved)} setlist(s) disponible(s)", size=12, italic=True, color=get_color("text_secondary"))
                ]
            )
            actions = [
                ft.TextButton("Cancelar", on_click=close_dlg, style=ft.ButtonStyle(color=get_color("text_secondary"))),
                ft.FilledButton("📂 Cargar", on_click=do_load, style=ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color("accent")))
            ]
        else:
            content = ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    ft.Text("No hay setlists guardados", size=14, color=get_color("text_primary")),
                    ft.Text("💡 Usa el botón 💾 para guardar tu primer setlist", size=11, italic=True, color=get_color("text_secondary"))
                ]
            )
            actions = [ft.TextButton("Cerrar", on_click=close_dlg, style=ft.ButtonStyle(color=get_color("text_secondary")))]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 Cargar Setlist", color=get_color("text_primary")),
            bgcolor=get_color("bg_secondary"),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    def update_setlist_counter():
        count = len(setlist_manager.list_setlists())
        save_counter.value = f"💾 {count}"
        page.update()

    save_counter = ft.Text(f"💾 0", size=12, weight=ft.FontWeight.W_500, color=get_color("text_secondary"))
    save_btn = ft.IconButton(icon=ft.Icons.SAVE, tooltip="Guardar setlist actual", on_click=save_setlist_dialog, icon_size=22, icon_color=get_color("accent"))
    load_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Cargar setlist guardado", on_click=load_setlist_dialog, icon_size=22, icon_color=get_color("accent"))

    # --- LISTBOX ---
    listbox_items = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def update_listbox():
        listbox_items.controls.clear()

        for track_index, track in enumerate(state.tracks):
            is_selected = track_index == state.current_index
            has_sections = len(track.get("sections", [])) > 0
            is_expanded = track.get("expanded", False)

            def make_click_handler(index):
                def handler(e):
                    state.current_index = index
                    update_status(f"Seleccionado: {state.tracks[index]['title']}", get_color("accent"))
                    update_listbox()
                return handler

            def make_drag_accept(end_index):
                def handler(e):
                    start_index = drag_state["dragging_index"]
                    if start_index is not None and start_index != end_index:
                        moved_item = state.tracks.pop(start_index)
                        state.tracks.insert(end_index, moved_item)
                        if state.current_index == start_index:
                            state.current_index = end_index
                        elif start_index < state.current_index <= end_index:
                            state.current_index -= 1
                        elif end_index <= state.current_index < start_index:
                            state.current_index += 1
                        update_status(f"✓ Reordenado: {moved_item['title']}", get_color("button_play"))
                        update_listbox()
                    drag_state["dragging_index"] = None
                return handler
            
            def make_expand_toggle(index):
                def handler(e):
                    state.tracks[index]["expanded"] = not state.tracks[index].get("expanded", False)
                    update_listbox()
                return handler           

            def make_drag_start(index):
                def handler(e):
                    drag_state["dragging_index"] = index
                return handler

            header = ft.Container(
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"{track_index + 1:02d}",
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=get_color("accent") if is_selected else get_color("text_secondary"),
                                    width=40,
                                ),
                                ft.Container(width=1, height=40, bgcolor=get_color("text_secondary"), opacity=0.2),
                                ft.Container(width=16),
                                ft.Column(
                                    expand=True,
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            track["title"],
                                            size=15,
                                            weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                                            color=get_color("select_fg") if is_selected else get_color("text_primary")
                                        ),
                                        ft.Text(
                                            f"{len(track['sections'])} sections",
                                            size=11,
                                            color=get_color("text_secondary"),
                                            opacity=0.7,
                                        ) if has_sections else ft.Container(height=0),
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.KEYBOARD_ARROW_DOWN if not is_expanded else ft.Icons.KEYBOARD_ARROW_UP,
                                    icon_size=20,
                                    on_click=make_expand_toggle(track_index),
                                    icon_color=get_color("accent"),
                                    visible=has_sections,
                                ),
                                ft.Icon(ft.Icons.DRAG_HANDLE, size=18, color=get_color("text_secondary"), opacity=0.3),
                            ],
                            spacing=0,
                        ),
                        ft.Container(
                            width=None,
                            height=2,
                            bgcolor=get_color("accent"),
                            margin=ft.margin.only(top=8),
                            visible=is_selected,
                            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                        ),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                border_radius=10,
                bgcolor=get_color("select_bg") if is_selected else get_color("bg_card"),
                on_click=make_click_handler(track_index),
            )

            sections_container = None
            if is_expanded and has_sections:
                section_items = []
                for sec_idx, sec in enumerate(track["sections"]):
                    def make_section_click(t_idx, s_idx):
                        def handler(e):
                            section = state.tracks[t_idx]["sections"][s_idx]
                            # Saltar a esa sección
                            osc_client.send_message("/live/song/stop_playing", [])
                            time.sleep(0.05)
                            osc_client.send_message("/live/song/set/current_song_time", [section['beat']])
                            time.sleep(0.05)
                            osc_client.send_message("/live/song/start_playing", [])
                            state.is_playing = True
                            update_status(f"▶ {section['name']}", get_color("accent"))
                        return handler
                    
                    section_items.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(width=60),
                                    ft.Container(width=4, height=30, border_radius=2, bgcolor=get_color("accent"), opacity=0.5),
                                    ft.Container(width=12),
                                    ft.Icon(ft.Icons.LABEL_OUTLINE, size=16, color=get_color("accent"), opacity=0.7),
                                    ft.Text(sec["name"], size=14, weight=ft.FontWeight.W_500, expand=True, color=get_color("text_primary")),
                                    ft.Text(f"+{sec.get('relative_beat', 0):.0f}", size=11, color=get_color("text_secondary"), opacity=0.7),
                                    ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, size=18, color=get_color("accent"), opacity=0.6),
                                    ft.Container(width=12),
                                ],
                                spacing=8,
                            ),
                            padding=ft.padding.symmetric(horizontal=0, vertical=8),
                            border_radius=8,
                            bgcolor=get_color("bg_main"),
                            on_click=make_section_click(track_index, sec_idx),
                            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                        )
                    )
                
                sections_container = ft.Container(
                    content=ft.Column(spacing=4, controls=section_items),
                    padding=ft.padding.only(left=0, right=0, top=8, bottom=8),
                    animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                )

            track_column = ft.Column(spacing=0, controls=[header] + ([sections_container] if sections_container else []))
            drag_target = ft.DragTarget(group="tracks", content=track_column, on_accept=make_drag_accept(track_index))
            draggable = ft.Draggable(
                group="tracks",
                content=drag_target,
                content_feedback=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(width=4, height=40, border_radius=2, bgcolor=get_color("button_text")),
                            ft.Text(f"{track_index + 1}", size=13, weight=ft.FontWeight.BOLD, color=get_color("button_text")),
                            ft.Text(track["title"], size=15, weight=ft.FontWeight.W_600, color=get_color("button_text")),
                        ],
                        spacing=12,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    width=340,
                    bgcolor=get_color("accent"),
                    border_radius=12,
                    opacity=0.92,
                ),
                on_drag_start=make_drag_start(track_index),
            )
            listbox_items.controls.append(draggable)

        page.update()

    page.update_listbox = update_listbox
    state.page_ref = page

    # --- PLAYBACK FUNCTIONS ---
    def scan_midi_sections(sections_track_index=0):
        print(f"[OSC] Solicitando clips de track {sections_track_index}...")
        send_message(f"/live/track/get/arrangement_clips/name", [sections_track_index])
        send_message(f"/live/track/get/arrangement_clips/start_time", [sections_track_index])

    def scan_locators(e):
        print(f"\n[USER] Escaneando locators y estructura...")
        update_status("Escaneando...", get_color("button_scan"))
        
        osc_client.send_message("/live/song/get/cue_points", [])
        time.sleep(0.2)

        scan_midi_sections(0)

        osc_client.send_message("/live/song/get/metronome", [])
        osc_client.send_message("/live/song/get/tempo", [])
        osc_client.send_message("/live/song/get/time_signature", [])
        osc_client.send_message("/live/song/get/playing_status", [])
        update_setlist_counter()
        
        if state.tracks:
            state.current_index = 0
        else:
            state.current_index = -1
        
    def jump_and_play_track(index_track):
        if 0 <= index_track < len(state.tracks):
            track = state.tracks[index_track]
            locator_id = track.get("start_locator_id")
            
            # ← AGREGAR ESTAS LÍNEAS DE DEBUG
            print(f"[DEBUG PLAY] Intentando reproducir track index={index_track}")
            print(f"[DEBUG PLAY] Track: '{track['title']}'")
            print(f"[DEBUG PLAY] Start beat: {track.get('start')}")
            print(f"[DEBUG PLAY] Locator ID guardado: {locator_id}")
            
            if locator_id is None:
                print(f"[USER] ⚠️ Track sin locator ID: {track['title']}")
                update_status("⚠️ Error: sin locator", get_color("button_stop"))
                return

            print(f"[USER] Jump & Play → Locator {locator_id}: {track['title']}")

            osc_client.send_message("/live/song/stop_playing", [])
            time.sleep(0.1)
            osc_client.send_message("/live/song/cue_point/jump", [locator_id])
            time.sleep(0.1)
            osc_client.send_message("/live/song/start_playing", [])
            state.is_playing = True
            update_status(f"▶ Play: {track['title']}", get_color("button_play"))
                        
    def play_selected(e):
        if state.current_index < 0 or state.current_index >= len(state.tracks):
            update_status("Sin track seleccionado", get_color("button_stop"))
            return
        
        # Si ya está reproduciendo, hacer stop completo
        if state.is_playing:
            stop_play(None)  # Llamar a la función stop completa
            time.sleep(0.15)
        
        play_btn.scale = 1.1
        page.update()
        time.sleep(0.1)
        play_btn.scale = 1.0
        page.update()
        jump_and_play_track(state.current_index)
        
    def stop_play(e):
        print(f"\n[USER] Stop")
        osc_client.send_message("/live/song/stop_playing", [])
        state.is_playing = False
        update_status("■ Stop", get_color("button_stop"))

    def next_track(e):
        if state.tracks:
            state.current_index = min(state.current_index + 1, len(state.tracks) - 1)
            update_listbox()
            jump_and_play_track(state.current_index)

    def prev_track(e):
        if state.tracks:
            state.current_index = max(state.current_index - 1, 0)
            update_listbox()
            jump_and_play_track(state.current_index)
        
    # --- BUTTONS ---
    play_btn = ft.ElevatedButton("PLAY", icon=ft.Icons.PLAY_ARROW, on_click=play_selected, width=200, height=80, animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT))
    stop_btn = ft.ElevatedButton("STOP", icon=ft.Icons.STOP, on_click=stop_play, width=200, height=80)
    prev_btn = ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS, icon_size=40, tooltip="Anterior", on_click=prev_track, style=ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color("button_nav"), shape=ft.RoundedRectangleBorder(radius=12)))
    next_btn = ft.IconButton(icon=ft.Icons.SKIP_NEXT, icon_size=40, tooltip="Siguiente", on_click=next_track, style=ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color("button_nav"), shape=ft.RoundedRectangleBorder(radius=12)))
    scan_btn = ft.ElevatedButton("SCAN", icon=ft.Icons.SEARCH, on_click=scan_locators, width=200, height=80)

    header_container = ft.Container()
    listbox_container = ft.Container()
    controls_column = ft.Column()
    main_row = ft.Row()

    def apply_colors():
        page.bgcolor = get_color("bg_main")
        status_text.color = get_color("text_secondary")
        palette_dropdown.bgcolor = get_color("bg_secondary")
        palette_dropdown.color = get_color("text_primary")
        palette_dropdown.border_color = get_color("accent")
        metro_button.style = ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color("button_metro_on") if state.metronome_on else get_color("button_metro"))
        for btn, key in [(scan_btn, "button_scan"), (play_btn, "button_play"), (stop_btn, "button_stop"), (prev_btn, "button_nav"), (next_btn, "button_nav")]:
            btn.style = ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color(key), padding=22)
        header_container.bgcolor = get_color("bg_secondary")
        listbox_container.bgcolor = get_color("bg_secondary")
        beat_indicator.bgcolor = get_color("bg_card")
        tempo_display.color = get_color("text_primary")
        update_listbox()
        page.update()

    header_container.content = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Row(spacing=15, controls=[
                ft.Text("ABLETON SETLIST", size=20, weight=ft.FontWeight.BOLD, color=get_color("accent")),
                ft.Container(width=2, height=30, bgcolor=get_color("accent"), opacity=0.3),
                ft.Text("🎛️", size=16),
                palette_dropdown,
            ]),
            ft.Row(spacing=8, controls=[save_counter, save_btn, load_btn, ft.Container(width=1, height=25, bgcolor=get_color("text_secondary"), opacity=0.3), ft.Text(f"v{APP_VERSION}", size=11, color=get_color("text_secondary"), italic=True)]),
        ],
    )
    header_container.padding = ft.padding.all(20)

    listbox_container.content = listbox_items
    listbox_container.expand = True
    listbox_container.border_radius = 12
    listbox_container.padding = ft.padding.all(20)

    controls_column.spacing = 12
    controls_column.controls = [
        ft.Container(content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[metro_button, tempo_display, beat_indicator, status_text]), bgcolor=get_color("bg_secondary"), border_radius=12, padding=ft.padding.all(20)),
        ft.Divider(thickness=1, color=get_color("text_secondary"), height=8),
        ft.Container(content=ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, controls=[play_btn, stop_btn, ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[prev_btn, next_btn]), scan_btn]), bgcolor=get_color("bg_secondary"), border_radius=12, padding=ft.padding.all(20), expand=True),
    ]

    main_row.spacing = 20
    main_row.expand = True
    main_row.controls = [ft.Column(expand=True, spacing=0, controls=[listbox_container]), ft.Container(width=250, content=controls_column)]

    page.add(ft.Container(expand=True, content=ft.Column(spacing=0, controls=[header_container, ft.Container(expand=True, padding=ft.padding.only(left=20, right=20, bottom=20, top=10), content=main_row)])))

    apply_colors()
    update_setlist_counter()

    print("\n[INIT] Iniciando escaneo inicial...")
    time.sleep(1)
    osc_client.send_message("/live/song/get/metronome", [])
    osc_client.send_message("/live/song/get/tempo", [])
    osc_client.send_message("/live/song/get/time_signature", [])
    osc_client.send_message("/live/song/get/playing_status", [])
    scan_locators(None)
    print("[INIT] ✓ App lista\n")