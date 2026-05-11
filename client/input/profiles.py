import pygame as pg

# Mapeamento Teclado
KEYBOARD_PROFILES = {
    "P1": {
        pg.K_UP: "thrust",
        pg.K_LEFT: "rotate_left",
        pg.K_RIGHT: "rotate_right",
        pg.K_SPACE: "shoot",
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

JOYSTICK_GENERIC = {
    "axes": {0: {"neg": "rotate_left", "pos": "rotate_right"}},
    "buttons": {2: "shoot", 3: "hyperspace", 0: "special", 1: "thrust"},
}
