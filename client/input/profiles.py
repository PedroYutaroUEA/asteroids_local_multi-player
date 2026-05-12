import pygame as pg

# Mapeamento Teclado
KEYBOARD_PROFILES = {
    "P1": {
        pg.K_UP: "thrust",
        pg.K_LEFT: "rotate_left",
        pg.K_RIGHT: "rotate_right",
        pg.K_SPACE: "shoot",
        pg.K_RSHIFT: "time_bomb",
        pg.K_LSHIFT: "hyperspace",
        pg.K_LALT: "special",
        "join_key": pg.K_1,
    },
    "P2": {
        pg.K_w: "thrust",
        pg.K_a: "rotate_left",
        pg.K_d: "rotate_right",
        pg.K_q: "shoot",
        pg.K_e: "hyperspace",
        pg.K_f: "special",
        pg.K_r: "time_bomb",
        "join_key": pg.K_2,
    },
}

# Mapeamento Joysticks (Normalizado)
# Chaves: 'axes' para polling, 'buttons' para eventos
JOYSTICK_XBOX = {
    "axes": {
        0: {"neg": "rotate_left", "pos": "rotate_right"},  # Eixo X
        5: {"pos": "thrust"},  # Gatilho RT
    },
    "buttons": {
        0: "shoot",  # Botão A
        1: "hyperspace",  # Botão B
        3: "special", # Botão Y
        7: "thrust",  # Botão Start/Menu (como reserva)
    },
}

# Perfil unificado para PS4 (DualShock 4) e PS5 (DualSense) — mapeamento SDL2 idêntico
JOYSTICK_PLAYSTATION = {
    "axes": {
        0: {"neg": "rotate_left", "pos": "rotate_right"},  # Analógico esquerdo X
        5: {"pos": "thrust"},  # R2 (gatilho direito analógico)
    },
    "buttons": {
        0: "shoot",  # Cross (X)
        1: "hyperspace",  # Circle (O)
        3: "time_bomb",  # Triangle (Δ)
        10: "thrust",  # R1 (botão superior direito)
    },
}

JOYSTICK_GENERIC = {
    "axes": {0: {"neg": "rotate_left", "pos": "rotate_right"}},
    "buttons": {0: "shoot", 1: "hyperspace", 3: "time_bomb", 5: "thrust"},
}
