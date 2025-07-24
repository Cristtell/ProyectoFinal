# Importamos las librerías necesarias de Ursina
from ursina import *
import math

from random import uniform, choice


# ---------- CONFIGURACIÓN BÁSICA ----------
app = Ursina()
window.title = 'Tiro al Blanco - Ursina'
window.borderless = False          # dejamos ventana con bordes para poder cerrarla
window.color = color.rgb(135,206,235)   # cielo azul de fondo

# ---------- ENTORNO / FONDO ----------
Sky()                               # cúpula de cielo predeterminada
ground = Entity(                    # suelo plano grande
    model='plane', scale=(80,1,80),
    texture='white_cube', texture_scale=(80,80),
    color=color.light_gray
)


# --- Configuración de Niveles ---
LEVEL_CONFIG = {
    1: {'targets': 15, 'speed': (8, 12), 'scale': 1.8, 'accuracy_goal': 50},
    2: {'targets': 20, 'speed': (10, 15), 'scale': 1.6, 'accuracy_goal': 60},
    3: {'targets': 25, 'speed': (18, 25), 'scale': 1.2, 'accuracy_goal': 70}
}

# --- Clase para los Objetivos Esféricos ---
class TargetSphere(Entity):
    def __init__(self, speed_range, scale): # Corregido: __init__ con doble guion bajo
        side = random.choice([-1, 1])
        start_pos = Vec3(22 * side, random.uniform(1, 8), random.uniform(15, 25))
        direction = Vec3(-side, random.uniform(-.1, .1), random.uniform(-.05, .05))

        super().__init__( # Corregido: __init__ con doble guion bajo
            model='sphere',
            color=random.choice([color.red, color.blue, color.orange]),
            scale=scale,
            position=start_pos,
            collider='sphere'
        )
        self.direction = direction
        self.speed = random.uniform(speed_range[0], speed_range[1])

    def update(self):
        self.position += self.direction * self.speed * time.dt
        if abs(self.x) > 24:
            destroy(self)
            invoke(check_level_end, delay=0.01)

    def hit(self):
        global hits, points
        hit_sound.play()
        hits += 1
        points += 100
        effect = Entity(model='sphere', color=color.white, scale=self.scale*1.5, position=self.world_position)
        effect.animate_scale(self.scale * 2, duration=0.2, curve=curve.out_quad)
        effect.fade_out(duration=0.2)
        destroy(effect, delay=0.2)
        
        # No es necesario animar los paneles si no tienen un modelo visual
        # score_panel.animate_scale(1.05, duration=0.05, curve=curve.out_sine)
        # score_panel.animate_scale(1, duration=0.1, delay=0.05)
        # hits_panel.animate_scale(1.05, duration=0.05, curve=curve.out_sine)
        # hits_panel.animate_scale(1, duration=0.1, delay=0.05)
        
        destroy(self)
        invoke(check_level_end, delay=0.01)


# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0
unlocked_level = 1
current_level = 1
game_active = False

# --- Sonidos ---
gunshot_sound = Audio('assets/sounds/gunshot.wav', loop=False, autoplay=False, volume=0.3)
hit_sound = Audio('assets/sounds/hit.wav', loop=False, autoplay=False, volume=0.5)
start_sound = Audio('assets/sounds/start_bleep.wav', loop=False, autoplay=False, volume=0.5)

# --- Funciones del Juego ---
def go_to_level_select():
    main_menu.disable()
    level_select_menu.enable()
    update_level_buttons()
    mouse.visible = True # Asegura que el cursor sea visible en el menú

def start_level(level):
    global hits, points, shots_fired, game_active, current_level
    current_level = level
    hits, points, shots_fired = 0, 0, 0
    game_active = True
    start_sound.play()
    
    level_select_menu.disable()
    game_hud.enable()
    pistol.enable()
    crosshair.enable()
    mouse.visible = False # Oculta el cursor cuando el juego comienza
    
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    invoke(spawn_target_loop, delay=1)

def spawn_target_loop():
    global spawn_sequence
    config = LEVEL_CONFIG[current_level]
    spawn_sequence = Sequence()
    for i in range(config['targets']):
        spawn_sequence.append(Func(lambda: TargetSphere(config['speed'], config['scale'])))
        spawn_sequence.append(Wait(random.uniform(1.0, 2.5)))
    spawn_sequence.start()

def check_level_end():
    if game_active and not any(isinstance(e, TargetSphere) for e in scene.entities):
        end_level()

def end_level():
    global game_active, unlocked_level
    game_active = False
    
    game_hud.disable()
    crosshair.disable()
    mouse.visible = True # Muestra el cursor al finalizar el nivel

    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG[current_level]['accuracy_goal']
    
    if accuracy >= goal:
        message = f"¡NIVEL {current_level} COMPLETADO!"
        if current_level < 3:
            unlocked_level = max(unlocked_level, current_level + 1)
            next_level_action = lambda: start_level(current_level + 1)
            button_text = "Siguiente Nivel"
        else:
            message = "¡FELICIDADES, HAS COMPLETADO EL JUEGO!"
            next_level_action = show_level_select_menu
            button_text = "Menú de Niveles"
    else:
        message = "INTÉNTALO DE NUEVO"
        next_level_action = lambda: start_level(current_level)
        button_text = "Reintentar"

    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .5), color=color.dark_gray.tint(.2), z=1)
    Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0, scale=1.5)
    Text(parent=end_panel, text=f"Aciertos: {hits} / {LEVEL_CONFIG[current_level]['targets']}", origin=(0,0), y=-.1, scale=1.5)
    Button(parent=end_panel, text=button_text, color=color.azure, scale=.3, y=-.3, on_click=Func(lambda: (destroy(end_panel), next_level_action())))

def show_level_select_menu():
    game_hud.disable()
    pistol.disable()
    crosshair.disable()
    level_select_menu.enable()
    update_level_buttons()
    mouse.visible = True # Muestra el cursor al volver al menú de selección de nivel

def update_hud():
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    score_label_and_value.text = f"PUNTOS: {points}"
    hits_label_and_value.text = f"ACIERTOS: {hits}"
    accuracy_text.text = f"Precisión: {accuracy:.1f}%"

# --- Inicialización de la Aplicación Ursina ---
app = Ursina(borderless=False)

# --- Creación del Entorno Futurista Mejorado ---
ground = Entity(model='plane', scale=(50, 1, 50), position=(0, 0, 5), texture='assets/textures/grid.png', texture_scale=(25,25))
back_wall = Entity(model='plane', scale=(50, 20, 1), position=(0, 10, 30), rotation_x=90, color=color.black)
left_wall = Entity(model='plane', scale=(50, 20, 1), position=(-25, 10, 5), rotation_z=-90, color=color.black)
right_wall = Entity(model='plane', scale=(50, 20, 1), position=(25, 10, 5), rotation_z=90, color=color.black)
ceiling = Entity(model='plane', scale=(50,1,50), position=(0,20,5), rotation_x=180, color=color.black)

Entity(model='quad', scale=(50, .5), position=(0, 0.1, 30), rotation_x=90, color=color.cyan.tint(-.5), emissive=True)
Entity(model='quad', scale=(50, .5), position=(-24.9, 0.1, 5), rotation_z=-90, color=color.red.tint(-.5), emissive=True)
Entity(model='quad', scale=(50, .5), position=(24.9, 0.1, 5), rotation_z=90, color=color.red.tint(-.5), emissive=True)

sky = Sky(color=color.black)
AmbientLight(color=color.rgba(100, 100, 100, 10)) # Ajustado el alpha para más luz

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 3, -15)
camera.fov = 80

# --- Arma y Mira ---
pistol = Entity(parent=camera, model='cube', scale=(0.1, 0.2, 0.7), position=(0.4, -0.4, 1), color=color.black)
crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red)

# --- Interfaz de Usuario (UI) Mejorada ---
game_hud = Entity(parent=camera.ui, y=0.47) # Posición general del HUD más arriba

# Puntos: Etiqueta y valor en una sola entidad de texto
score_label_and_value = Text(parent=game_hud, text="PUNTOS: 0", origin=(-.5, 0), x=-.45, y=0, scale=1.5, color=color.white)

# Aciertos: Etiqueta y valor en una sola entidad de texto
hits_label_and_value = Text(parent=game_hud, text="ACIERTOS: 0", origin=(.5, 0), x=.45, y=0, scale=1.5, color=color.white)

# Precisión: Centrado
accuracy_text = Text(parent=game_hud, text="Precisión: 0.0%", origin=(0, 0), x=0, y=0, scale=1.5, color=color.white)

# --- Menú Principal ---
main_menu = Entity(parent=camera.ui, enabled=True)
title = Text(parent=main_menu, text="AIM PRECISION DDC ", scale=3, origin=(0,0), y=0.2, color=color.white, background=True)
start_button = Button(parent=main_menu, text="INICIAR", color=color.azure, scale=(0.4, 0.1), y=0, on_click=go_to_level_select)
quit_button = Button(parent=main_menu, text="SALIR", color=color.azure, scale=(0.4, 0.1), y=-0.15, on_click=application.quit)

# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False)
level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.3)
level_1_button = Button(parent=level_select_menu, text="Nivel 1", scale=(0.3, 0.1), y=0.1, on_click=lambda: start_level(1))
level_2_button = Button(parent=level_select_menu, text="Nivel 2", scale=(0.3, 0.1), y=0, on_click=lambda: start_level(2))
level_3_button = Button(parent=level_select_menu, text="Nivel 3", scale=(0.3, 0.1), y=-0.1, on_click=lambda: start_level(3))
level_buttons = [level_1_button, level_2_button, level_3_button]
def update_level_buttons():
    for i, button in enumerate(level_buttons):
        button.disabled = (i + 1 > unlocked_level)

# --- Lógica Principal ---
def update():
    if game_active:
        update_hud()
    camera.rotation_y += mouse.velocity[0] * 60
    camera.rotation_x -= mouse.velocity[1] * 60
    camera.rotation_x = clamp(camera.rotation_x, -50, 50)
    camera.rotation_y = clamp(camera.rotation_y, -80, 80)

def input(key):
    global shots_fired
    if game_active and key == 'left mouse down':
        shots_fired += 1
        gunshot_sound.play()
        pistol.rotation_x = -10
        pistol.animate_rotation_x(0, duration=0.1)
        
        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=[pistol])
        if hit_info.hit and hasattr(hit_info.entity, 'hit'):
            hit_info.entity.hit()
    
# --- Iniciar el Juego ---
game_hud.disable()
pistol.disable()
crosshair.disable()
mouse.visible = True # Asegura que el cursor sea visible al iniciar la aplicación
app.run()