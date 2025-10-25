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
    beat_indicators = []
    for i in range(4):
        indicator = ft.Container(
            width=45,
            height=45,
            border_radius=22,
            bgcolor=get_color("bg_card"),
            alignment=ft.alignment.center,
            content=ft.Text(str(i+1), size=16, weight=ft.FontWeight.BOLD, color=get_color("text_secondary")),
        )
        beat_indicators.append(indicator)

    tempo_display = ft.Text(f"{state.current_tempo} BPM", size=12, weight=ft.FontWeight.W_600, color=get_color("text_primary"))

    def trigger_pulse(beat):
        try:
            for idx, indicator in enumerate(beat_indicators):
                if idx < state.time_signature_num:
                    indicator.bgcolor = get_color("bg_card")
                    indicator.visible = True
                else:
                    indicator.visible = False

            if 0 < beat <= len(beat_indicators) and beat <= state.time_signature_num:
                beat_indicators[beat - 1].bgcolor = get_color("pulse_color")

            page.update()
        except Exception as e:
            print(f"[UI ERROR] Error en trigger_pulse: {e}")

    def update_tempo_display():
        try:
            tempo_display.value = f"{state.current_tempo:.0f} BPM | {state.time_signature_num}/4"
            for idx, indicator in enumerate(beat_indicators):
                indicator.visible = idx < state.time_signature_num
            page.update()
        except Exception as e:
            print(f"Error actualizando tempo: {e}")

    # Exponer métodos para handlers OSC (igual que antes)
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
        print(f"[UI] Locators disponibles para guardar: {len(state.locators)}")

        if not state.locators:
            print(f"[UI] ❌ No hay locators para guardar")
            update_status("⚠️ Sin locators. Presiona SCAN primero", get_color("button_stop"))
            return

        name_field = ft.TextField(
            label="Nombre del setlist",
            width=350,
            autofocus=True,
            hint_text="Ej: Concierto 2024",
        )

        error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

        def close_dlg(e):
            print(f"[UI] Cerrando diálogo de guardar")
            dlg.open = False
            page.update()

        def do_save(e):
            name = name_field.value.strip()
            print(f"\n[USER] Solicitando guardar setlist: '{name}'")
            print(f"[USER] Locators a guardar: {len(state.locators)}")

            if not name:
                print(f"[USER] ❌ Nombre vacío")
                update_status("Error: nombre vacío", get_color("button_stop"))
                error_text.value = "⚠️ Debes ingresar un nombre"
                error_text.visible = True
                page.update()
                return

            print(f"[USER] Llamando a save_setlist()...")
            success = setlist_manager.save_setlist(name, state.locators)
            print(f"[USER] Resultado del guardado: {success}")

            if success:
                update_status(f"✓ '{name}' guardado ({len(state.locators)} locators)", get_color("button_play"))
                close_dlg(None)
                update_setlist_counter()
            else:
                update_status("❌ Error al guardar", get_color("button_stop"))
                error_text.value = "❌ Error al guardar el archivo"
                error_text.visible = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("💾 Guardar Setlist"),
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
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.FilledButton("💾 Guardar", on_click=do_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # SOLUCIÓN: Usar page.open() en lugar de solo asignar
        print(f"[UI] Abriendo diálogo con page.open()...")
        page.open(dlg)
        print(f"[UI] ✓ Diálogo abierto")


    def load_setlist_dialog(e):
        print(f"\n[UI] Abriendo diálogo de cargar setlist...")

        saved = setlist_manager.list_setlists()
        print(f"[UI] Setlists encontrados: {saved}")

        def close_dlg(e):
            print(f"[UI] Cerrando diálogo de cargar")
            dlg.open = False
            page.update()

        def do_load(e):
            if dropdown.value:
                print(f"[USER] Cargando setlist: {dropdown.value}")
                data = setlist_manager.load_setlist(dropdown.value)
                if data and "locators" in data:
                    state.locators = data["locators"]
                    print(f"[USER] ✓ Cargados {len(state.locators)} locators")
                    update_listbox()
                    update_status(f"✓ '{data['name']}' cargado ({len(state.locators)} locators)", get_color("button_play"))
                    close_dlg(None)
                else:
                    print(f"[USER] ❌ Error cargando setlist")
                    update_status("❌ Error al cargar", get_color("button_stop"))

        if saved:
            dropdown = ft.Dropdown(
                label="Setlists guardados",
                options=[ft.dropdown.Option(name) for name in saved],
                width=350,
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
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.FilledButton("📂 Cargar", on_click=do_load),
            ]
        else:
            content = ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    ft.Text("No hay setlists guardados", size=14),
                    ft.Text("💡 Usa el botón 💾 para guardar tu primer setlist", size=11, italic=True, color=get_color("text_secondary"))
                ]
            )
            actions = [ft.TextButton("Cerrar", on_click=close_dlg)]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 Cargar Setlist"),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # SOLUCIÓN: Usar page.open() en lugar de solo asignar
        print(f"[UI] Abriendo diálogo con page.open()...")
        page.open(dlg)
        print(f"[UI] ✓ Diálogo abierto")


    def update_setlist_counter():
        count = len(setlist_manager.list_setlists())
        save_counter.value = f"💾 {count}"
        page.update()

    save_counter = ft.Text(f"💾 0", size=12, weight=ft.FontWeight.W_500, color=get_color("text_secondary"))
    save_btn = ft.IconButton(
        icon=ft.Icons.SAVE,
        tooltip="Guardar setlist actual",
        on_click=save_setlist_dialog,
        icon_size=22,
        icon_color=get_color("accent")
    )
    load_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        tooltip="Cargar setlist guardado",
        on_click=load_setlist_dialog,
        icon_size=22,
        icon_color=get_color("accent")
    )
    # --- LISTBOX ---
    listbox_items = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def update_listbox():
        listbox_items.controls.clear()
        for i, locator in enumerate(state.locators):
            is_selected = i == state.current_index

            def make_click_handler(index):
                def handler(e):
                    state.current_index = index
                    update_status(f"Seleccionado: {state.locators[index]['name']}", get_color("accent"))
                    update_listbox()
                return handler

            def make_drag_accept(end_index):
                def handler(e):
                    start_index = drag_state["dragging_index"]
                    if start_index is not None and start_index != end_index:
                        moved_item = state.locators.pop(start_index)
                        state.locators.insert(end_index, moved_item)
                        if state.current_index == start_index:
                            state.current_index = end_index
                        elif start_index < state.current_index <= end_index:
                            state.current_index -= 1
                        elif end_index <= state.current_index < start_index:
                            state.current_index += 1
                        update_status(f"✓ Reordenado: {moved_item['name']}", get_color("button_play"))
                        update_listbox()
                    drag_state["dragging_index"] = None
                return handler

            def make_drag_start(index):
                def handler(e):
                    drag_state["dragging_index"] = index
                    update_status(f"Arrastrando: {state.locators[index]['name']}", get_color("button_scan"))
                return handler

            # Construcción del item del listbox
            drag_target = ft.DragTarget(
                group="locators",
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            # Acento lateral
                            ft.Container(
                                width=4,
                                height=45,
                                border_radius=2,
                                bgcolor=get_color("accent") if is_selected else ft.Colors.TRANSPARENT,
                                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                            ),
                            ft.Container(width=12),
                            # Badge numerado
                            ft.Container(
                                content=ft.Text(
                                    str(i+1),
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=get_color("accent") if is_selected else get_color("text_secondary")
                                ),
                                width=32,
                                height=32,
                                border_radius=16,
                                border=ft.border.all(2, get_color("accent") if is_selected else get_color("text_secondary")),
                                alignment=ft.alignment.center,
                                bgcolor=ft.Colors.TRANSPARENT,
                            ),
                            ft.Container(width=12),
                            # Contenido
                            ft.Column(
                                expand=True,
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        locator['name'],
                                        size=15,
                                        weight=ft.FontWeight.W_600,
                                        color=get_color("select_fg") if is_selected else get_color("text_primary")
                                    ),
                                    ft.Text(
                                        "● Ready to play",
                                        size=10,
                                        color=get_color("accent"),
                                        opacity=0.8,
                                        visible=is_selected
                                    ),
                                ],
                            ),
                            # Icono
                            ft.Icon(
                                ft.Icons.CHEVRON_RIGHT if is_selected else ft.Icons.DRAG_INDICATOR,
                                size=20,
                                color=get_color("accent") if is_selected else get_color("text_secondary"),
                                opacity=1 if is_selected else 0.4
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=ft.padding.only(left=0, right=16, top=10, bottom=10),
                    border_radius=12,
                    bgcolor=get_color("select_bg") if is_selected else get_color("bg_card"),
                    animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                ),
                on_accept=make_drag_accept(i),
            )

            draggable = ft.Draggable(
                group="locators",
                content=drag_target,
                content_feedback=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=4,
                                height=40,
                                border_radius=2,
                                bgcolor=get_color("button_text"),
                            ),
                            ft.Text(
                                f"{i+1}",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=get_color("button_text")
                            ),
                            ft.Text(
                                locator['name'],
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=get_color("button_text")
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    width=340,
                    bgcolor=get_color("accent"),
                    border_radius=12,
                    opacity=0.92,
                ),
                on_drag_start=make_drag_start(i),
            )

            drag_target.content.on_click = make_click_handler(i)
            listbox_items.controls.append(draggable)

        page.update()

    page.update_listbox = update_listbox
    page_ref = page
    page_ref.update_listbox = update_listbox

    # --- PLAYBACK FUNCTIONS ---
    def scan_locators(e):
        print(f"\n[USER] Escaneando locators...")
        update_status("Escaneando...", get_color("button_scan"))
        osc_client.send_message("/live/song/get/cue_points", [])
        osc_client.send_message("/live/song/get/metronome", [])
        osc_client.send_message("/live/song/get/tempo", [])
        osc_client.send_message("/live/song/get/time_signature", [])
        osc_client.send_message("/live/song/get/playing_status", [])
        update_setlist_counter()

    def jump_and_play(index):
        if 0 <= index < len(state.locators):
            locator_id = state.locators[index]['id']
            print(f"\n[USER] Jump & Play → Locator {locator_id}: {state.locators[index]['name']}")

            osc_client.send_message("/live/song/stop_playing", [])
            time.sleep(0.1)
            osc_client.send_message("/live/song/cue_point/jump", [locator_id])
            time.sleep(0.1)
            osc_client.send_message("/live/song/start_playing", [])
            state.is_playing = True

            osc_client.send_message("/live/song/get/tempo", [])
            osc_client.send_message("/live/song/get/time_signature", [])
            osc_client.send_message("/live/song/get/playing_status", [])

            update_status(f"▶ Play: {state.locators[index]['name']}", get_color("button_play"))

    def play_selected(e):
        if 0 <= state.current_index < len(state.locators):
            play_btn.scale = 1.1
            page.update()
            time.sleep(0.1)
            play_btn.scale = 1.0
            page.update()
            jump_and_play(state.current_index)

    def stop_play(e):
        print(f"\n[USER] Stop")
        osc_client.send_message("/live/song/stop_playing", [])
        state.is_playing = False
        update_status("■ Stop", get_color("button_stop"))

    def next_locator(e):
        if not state.locators:
            return
        if state.current_index == -1:
            state.current_index = 0
        elif state.current_index + 1 < len(state.locators):
            state.current_index += 1
        else:
            return
        update_listbox()
        jump_and_play(state.current_index)

    def prev_locator(e):
        if not state.locators:
            return
        if state.current_index == -1:
            state.current_index = len(state.locators) - 1
        elif state.current_index - 1 >= 0:
            state.current_index -= 1
        else:
            return
        update_listbox()
        jump_and_play(state.current_index)

    # --- BUTTONS ---
    play_btn = ft.ElevatedButton("PLAY", icon=ft.Icons.PLAY_ARROW, on_click=play_selected, width=200, height=80,
                                 animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT))
    stop_btn = ft.ElevatedButton("STOP", icon=ft.Icons.STOP, on_click=stop_play, width=200, height=80)
    # --- BOTONES DE NAVEGACIÓN SOLO ICONO ---
    prev_btn = ft.IconButton(
        icon=ft.Icons.SKIP_PREVIOUS,
        icon_size=40,
        tooltip="Anterior",
        on_click=prev_locator,
        style=ft.ButtonStyle(
            color=get_color("button_text"),
            bgcolor=get_color("button_nav"),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    next_btn = ft.IconButton(
        icon=ft.Icons.SKIP_NEXT,
        icon_size=40,
        tooltip="Siguiente",
        on_click=next_locator,
        style=ft.ButtonStyle(
            color=get_color("button_text"),
            bgcolor=get_color("button_nav"),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )
    scan_btn = ft.ElevatedButton("SCAN", icon=ft.Icons.SEARCH, on_click=scan_locators, width=200, height=80)

    # Contenedores principales
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

        metro_button.style = ft.ButtonStyle(
            color=get_color("button_text"),
            bgcolor=get_color("button_metro_on") if state.metronome_on else get_color("button_metro"),
        )

        for btn, key in [(scan_btn, "button_scan"), (play_btn, "button_play"),
                         (stop_btn, "button_stop"), (prev_btn, "button_nav"), (next_btn, "button_nav")]:
            btn.style = ft.ButtonStyle(color=get_color("button_text"), bgcolor=get_color(key), padding=22)

        header_container.bgcolor = get_color("bg_secondary")
        listbox_container.bgcolor = get_color("bg_secondary")

        for indicator in beat_indicators:
            indicator.bgcolor = get_color("bg_card")
        tempo_display.color = get_color("text_primary")

        update_listbox()
        page.update()

    # --- UI LAYOUT (CORREGIDO) ---
    header_container.content = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Row(
                spacing=15,
                controls=[
                    ft.Text("ABLETON SETLIST", size=20, weight=ft.FontWeight.BOLD, color=get_color("accent")),
                    ft.Container(width=2, height=30, bgcolor=get_color("accent"), opacity=0.3),  # Divider visible
                    ft.Text("🎛️", size=16),
                    palette_dropdown,
                ],
            ),
            ft.Row(
                spacing=8,
                controls=[
                    save_counter,
                    save_btn,
                    load_btn,
                    ft.Container(width=1, height=25, bgcolor=get_color("text_secondary"), opacity=0.3),
                    ft.Text(f"v{APP_VERSION}", size=11, color=get_color("text_secondary"), italic=True),
                ],
            ),
        ],
    )
    header_container.padding = ft.padding.all(20)

    listbox_container.content = listbox_items
    listbox_container.expand = True
    listbox_container.border_radius = 12
    listbox_container.padding = ft.padding.all(20)

    controls_column.spacing = 12
    controls_column.controls = [
        ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    metro_button,
                    tempo_display,
                    ft.Row(controls=beat_indicators, alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                    status_text
                ],
            ),
            bgcolor=get_color("bg_secondary"),
            border_radius=12,
            padding=ft.padding.all(20),
            # no expand aquí (mantén su altura natural)
        ),
        # --- DIVIDER FINO (NO EXPANDE) ---
        ft.Divider(
            thickness=1,
            color=get_color("text_secondary"),
            height=8,              # espacio total que reserva (opcional)
        ),
        # --- BLOQUE DE BOTONES DE CONTROL ---
        ft.Container(
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,  # ← ESTO CENTRA VERTICALMENTE
                controls=[
                    play_btn,
                    stop_btn,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[prev_btn, next_btn],
                    ),
                    scan_btn,
                ]
            ),
            bgcolor=get_color("bg_secondary"),
            border_radius=12,
            padding=ft.padding.all(20),
            expand=True,  # que los botones ocupen el resto si hace falta
        ),
    ]

    main_row.spacing = 20
    main_row.expand = True
    main_row.controls = [
        ft.Column(expand=True, spacing=0, controls=[listbox_container]),
        ft.Container(width=250, content=controls_column),
    ]

    page.add(ft.Container(
        expand=True,
        content=ft.Column(
            spacing=0,
            controls=[
                header_container,
                ft.Container(
                    expand=True,
                    padding=ft.padding.only(left=20, right=20, bottom=20, top=10),
                    content=main_row
                ),
            ]
        )
    ))

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

# Exponer la función main para ft.app
# Nota: en main.py llamamos ft.app(target=ui.app_ui.main)
