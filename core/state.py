# core/state.py
# Variables globales compartidas entre UI y handlers
locators = []
current_index = -1
metronome_on = False
current_beat = 1
current_tempo = 120.0
time_signature_num = 4
current_song_time = 0.0
is_playing = False

# referencia a la page/UI (se asigna desde ui.app_ui)
page_ref = None
