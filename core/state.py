# core/state.py
# Variables globales compartidas entre UI y handlers
locators = []
current_index = -1
metronome_on = False
current_beat = 1
current_tempo = 120.0
time_signature_num = 1
current_song_time = 0.0
is_playing = False

track_progress_bars = {}  # key: track_index, value: ft.Container

# referencia a la page/UI (se asigna desde ui.app_ui)
page_ref = None

# --- NUEVA ESTRUCTURA ---
tracks = []  # Lista jerárquica: cada track contiene secciones

# Índices para navegación
current_index_track = -1  # track seleccionado
current_index_locator = -1  # locator seleccionado
