import pygame as pg

# Traduções amigáveis para as ações do jogo
ACTION_LABELS = {
    "thrust": "Acelerar",
    "rotate_left": "Girar Esq",
    "rotate_right": "Girar Dir",
    "shoot": "Atirar",
    "time_bomb": "Bomba",
    "hyperspace": "Hiper",
    "special": "Especial",
}

# Mapeamento Teclado
KEYBOARD_PROFILES = {
    "P1": {
        pg.K_UP: "thrust",
        pg.K_LEFT: "rotate_left",
        pg.K_RIGHT: "rotate_right",
        pg.K_SPACE: "shoot",
        pg.K_RSHIFT: "time_bomb",
        pg.K_DOWN: "hyperspace",
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
    "name": "Xbox / X-Input",
    "axes": {
        0: {"neg": "rotate_left", "pos": "rotate_right"},  # Eixo X
        5: {"pos": "thrust"},  # Gatilho RT
    },
    "buttons": {
        0: "shoot",  # Botão A
        1: "hyperspace",  # Botão B
        2: "time_bomb",  # Botão X
        3: "special",  # Botão Y
        7: "thrust",  # Botão Start/Menu (como reserva)
    },
}

# Perfil unificado para PS4 (DualShock 4) e PS5 (DualSense) — mapeamento SDL2 idêntico
JOYSTICK_PLAYSTATION = {
    "name": "PS4 / PS5",
    "axes": {
        0: {"neg": "rotate_left", "pos": "rotate_right"},  # Analógico esquerdo X
        5: {"pos": "thrust"},  # R2 (gatilho direito analógico)
    },
    "buttons": {
        0: "shoot",  # Cross (X)
        1: "hyperspace",  # Circle (O)
        2: "time_bomb",  # Square (□)
        3: "special",  # Triangle (Δ)
        10: "thrust",  # R1 (botão superior direito)
    },
}

JOYSTICK_GENERIC = {
    "name": "Genérico",
    "axes": {0: {"neg": "rotate_left", "pos": "rotate_right"}},
    "buttons": {0: "shoot", 1: "hyperspace", 2: "time_bomb", 3: "special", 5: "thrust"},
}


def get_key_name(key_code: int) -> str:
    """Traduz o código da tecla para uma string legível."""
    name = pg.key.name(key_code)
    # Ajustes cosméticos para teclas comuns
    mapping = {
        "up": "↑",
        "left": "←",
        "right": "→",
        "space": "Espaco",
        "left shift": "L Shift",
        "down": "↓",
        "left alt": "L Alt",
    }
    return mapping.get(name, name.capitalize())


def get_keyboard_hint(player_label: str) -> list[tuple[str, str]]:
    """Gera lista de (Ação, Tecla) para o menu/lobby."""
    profile = KEYBOARD_PROFILES.get(player_label, {})
    hints = []

    # Agrupa movimento para economizar espaço
    move_keys = [
        get_key_name(k)
        for k, v in profile.items()
        if v in ["thrust", "rotate_left", "rotate_right"]
    ]
    if move_keys:
        hints.append(("Mover", "|".join(move_keys[:3])))

    # Adiciona ações principais
    for action in ["shoot", "time_bomb", "hyperspace"]:
        for k, v in profile.items():
            if v == action:
                hints.append((ACTION_LABELS[action], get_key_name(k)))

    return hints
