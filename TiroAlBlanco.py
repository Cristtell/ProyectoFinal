# Importamos las librerías necesarias de Ursina
from ursina import *
import random
from ursina.prefabs.first_person_controller import FirstPersonController
# Import the unlit_shader explicitly
from ursina.shaders import unlit_shader

# --- Configuración de Niveles ---
LEVEL_CONFIG = {
    1: {'targets': 15, 'speed': (8, 12), 'scale': 1.8, 'accuracy_goal': 50},
    2: {'targets': 20, 'speed': (10, 15), 'scale': 1.6, 'accuracy_goal': 60},
    3: {'targets': 25, 'speed': (18, 25), 'scale': 1.2, 'accuracy_goal': 70}
}

# --- Variables Globales del Juego ---
hits = 0
points = 0
shots_fired = 0
unlocked_level = 1
current_level = 1
game_active = False
spawn_sequence = None # Will hold the Sequence for spawning targets
end_panel = None # Global variable to hold the end level panel

# --- Sonidos (Usando sonidos predeterminados de Ursina or omitting if no equivalents) ---
# For simplicity, we'll use a generic 'click' sound for hit and start, and a 'gunshot' sound for shooting.
# If these don't exist, Ursina will usually just not play them or print a warning.
# You can replace these with your own .wav files in an 'assets/sounds/' folder if you have them.
gunshot_sound = Audio('gunshot', loop=False, autoplay=False, volume=0.3)
hit_sound = Audio('blip', loop=False, autoplay=False, volume=0.5) # Using 'blip' as a placeholder
start_sound = Audio('click', loop=False, autoplay=False, volume=0.5) # Using 'click' as a placeholder

# --- Clase para los Objetivos Esféricos ---
class TargetSphere(Entity):
    def __init__(self, speed_range, scale):
        # Determine starting side (-1 for left, 1 for right)
        side = random.choice([-1, 1])
        # Position targets outside the visible area, slightly elevated and varied in depth
        start_pos = Vec3(22 * side, random.uniform(1, 8), random.uniform(15, 25))
        # Direction towards the center, with slight vertical and depth variation
        direction = Vec3(-side, random.uniform(-.1, .1), random.uniform(-.05, .05)).normalized()

        super().__init__(
            model='sphere',
            # Corrected: Removed 'color.purple' as it's not a valid Ursina color attribute.
            color=random.choice([color.red, color.blue, color.orange, color.green]),
            scale=scale,
            position=start_pos,
            collider='sphere',
            # Add a glow effect for futuristic look
            shader=unlit_shader, # Use unlit shader for emissive color
            emissive=color.white,
            render_queue=0 # Render on top
        )
        
        self.direction = direction
        self.speed = random.uniform(speed_range[0], speed_range[1])
    
    def update(self):
        # Move the target
        self.position += self.direction * self.speed * time.dt
        # Destroy target if it goes too far to the left or right
        if abs(self.x) > 24:
            destroy(self)
            # Check if level should end after a small delay to ensure destruction completes
            invoke(check_level_end, delay=0.01)
            
    def hit(self):
        global hits, points
        hit_sound.play()
        hits += 1
        points += 100
        
        # Visual effect for hit
        effect = Entity(model='sphere', color=color.white, scale=self.scale * 1.5, position=self.world_position,
                        shader=unlit_shader, emissive=color.white, render_queue=0)
        effect.animate_scale(self.scale * 2, duration=0.2, curve=curve.out_quad)
        effect.fade_out(duration=0.2)
        destroy(effect, delay=0.2)
        
        # Animate UI panels on hit
        score_panel.animate_scale(1.05, duration=0.05, curve=curve.out_sine)
        score_panel.animate_scale(1, duration=0.1, delay=0.05)
        hits_panel.animate_scale(1.05, duration=0.05, curve=curve.out_sine)
        hits_panel.animate_scale(1, duration=0.1, delay=0.05)
        
        destroy(self)
        # Check if level should end after a small delay to ensure destruction completes
        invoke(check_level_end, delay=0.01)

# --- Funciones del Juego ---

def go_to_level_select():
    """Transitions from main menu to level selection menu."""
    main_menu.disable()
    level_select_menu.enable()
    update_level_buttons()

def start_level(level):
    """Starts a new game level."""
    global hits, points, shots_fired, game_active, current_level, spawn_sequence, end_panel
    current_level = level
    hits, points, shots_fired = 0, 0, 0
    game_active = True
    start_sound.play()
    level_select_menu.disable()
    game_hud.enable()
    pistol.enable()
    crosshair.enable()
    mouse.locked = True # Lock mouse for aiming

    # Destroy any existing targets before starting a new level
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    
    # Stop any ongoing spawn sequences
    if spawn_sequence:
        spawn_sequence.finish()

    # Destroy end_panel if it exists from a previous game over screen
    if end_panel:
        destroy(end_panel)
        end_panel = None # Reset global variable

    # Start spawning targets for the new level
    invoke(spawn_target_loop, delay=1)

def spawn_target_loop():
    """Spawns targets based on the current level configuration."""
    global spawn_sequence
    config = LEVEL_CONFIG[current_level]
    spawn_sequence = Sequence()
    
    for i in range(config['targets']):
        spawn_sequence.append(Func(lambda: TargetSphere(config['speed'], config['scale'])))
        spawn_sequence.append(Wait(random.uniform(1.0, 2.5)))
    spawn_sequence.start()

def check_level_end():
    """Checks if all targets are destroyed or have left the screen to end the level."""
    # Only end level if game is active and no TargetSphere entities are left in the scene
    if game_active and not any(isinstance(e, TargetSphere) for e in scene.entities):
        end_level()

def end_level():
    """Ends the current level, displays results, and handles level progression."""
    global game_active, unlocked_level, end_panel
    game_active = False
    game_hud.disable()
    crosshair.disable()
    pistol.disable()
    mouse.locked = False # Unlock mouse for menu interaction

    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG[current_level]['accuracy_goal']
    
    message = ""
    button_text = ""
    next_level_action_func = None # Will hold the function to call

    if accuracy >= goal:
        message = f"¡NIVEL {current_level} COMPLETADO!"
        if current_level < len(LEVEL_CONFIG): # Check if there's a next level
            unlocked_level = max(unlocked_level, current_level + 1)
            next_level_action_func = lambda: start_level(current_level + 1)
            button_text = "Siguiente Nivel"
        else:
            message = "¡FELICIDADES, HAS COMPLETADO EL JUEGO!"
            next_level_action_func = show_level_select_menu
            button_text = "Menú de Niveles"
    else:
        message = "INTÉNTALO DE NUEVO"
        next_level_action_func = lambda: start_level(current_level)
        button_text = "Reintentar"
        
    # Create end level panel
    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .5), color=color.dark_gray.tint(.2), z=1,
                       origin=(0,0), position=(0,0), collider='box')
    Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2, color=color.white)
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0, scale=1.5, color=color.white)
    Text(parent=end_panel, text=f"Aciertos: {hits} / {LEVEL_CONFIG[current_level]['targets']}", origin=(0,0), y=-.1, scale=1.5, color=color.white)
    
    # Assign on_click directly to invoke the action with a delay
    Button(parent=end_panel, text=button_text, color=color.azure, scale=.3, y=-.3, 
           on_click=Func(lambda: invoke(next_level_action_func, delay=0.3)))


def show_level_select_menu():
    """Shows the level selection menu."""
    global end_panel # Declare end_panel as global
    game_hud.disable()
    pistol.disable()
    crosshair.disable()
    level_select_menu.enable()
    update_level_buttons()
    mouse.locked = False # Unlock mouse for menu interaction

    # Destroy end_panel if it exists from a previous game over screen
    if end_panel:
        destroy(end_panel)
        end_panel = None # Reset global variable

def update_hud():
    """Updates the game HUD (score, hits, accuracy)."""
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    score_text.text = f"{points}"
    hits_text.text = f"{hits}"
    accuracy_text.text = f"Precisión: {accuracy:.1f}%"

def update_level_buttons():
    """Updates the state (enabled/disabled) of level selection buttons."""
    for i, button in enumerate(level_buttons):
        button.disabled = (i + 1 > unlocked_level)
        # Change color for locked levels
        if button.disabled:
            button.color = color.gray
        else:
            button.color = color.azure

# --- Lógica Principal de Ursina ---
def update():
    """Called every frame by Ursina."""
    if game_active:
        update_hud()
        # Camera rotation based on mouse movement
        camera.rotation_y += mouse.velocity[0] * 60
        camera.rotation_x -= mouse.velocity[1] * 60
        camera.rotation_x = clamp(camera.rotation_x, -50, 50)
        camera.rotation_y = clamp(camera.rotation_y, -80, 80) # Limit horizontal rotation

def input(key):
    """Handles user input."""
    global shots_fired
    
    if game_active and key == 'left mouse down':
        shots_fired += 1
        gunshot_sound.play()
        pistol.rotation_x = -10 # Recoil effect
        pistol.animate_rotation_x(0, duration=0.1) # Return to original position

        # Perform a raycast to check for hits
        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=[pistol])
        if hit_info.hit and hasattr(hit_info.entity, 'hit'):
            hit_info.entity.hit()
    
    # Toggle mouse lock with 'escape' key
    if key == 'escape':
        mouse.locked = not mouse.locked
        # If mouse is unlocked, show level select menu
        if not mouse.locked and game_active:
            show_level_select_menu()
        elif mouse.locked and not game_active and level_select_menu.enabled:
            # If re-locking mouse from level select, go back to game (if a level was active)
            level_select_menu.disable()
            game_hud.enable()
            pistol.enable()
            crosshair.enable()


# --- Inicialización de la Aplicación Ursina ---
app = Ursina(borderless=False)

# --- Creación del Entorno Futurista Mejorado ---
# Ground with a simple white_cube texture and color for grid-like appearance
ground = Entity(model='plane', scale=(50, 1, 50), position=(0, 0, 5), texture='white_cube', texture_scale=(25,25), color=color.dark_gray)
back_wall = Entity(model='plane', scale=(50, 20, 1), position=(0, 10, 30), rotation_x=90, color=color.black)
left_wall = Entity(model='plane', scale=(50, 20, 1), position=(-25, 10, 5), rotation_z=-90, color=color.black)
right_wall = Entity(model='plane', scale=(50, 20, 1), position=(25, 10, 5), rotation_z=90, color=color.black)
ceiling = Entity(model='plane', scale=(50,1,50), position=(0,20,5), rotation_x=180, color=color.black)

# Emissive lines for futuristic aesthetic
Entity(model='quad', scale=(50, .5), position=(0, 0.1, 30), rotation_x=90, color=color.cyan.tint(-.5), emissive=True)
Entity(model='quad', scale=(50, .5), position=(-24.9, 0.1, 5), rotation_z=-90, color=color.red.tint(-.5), emissive=True)
Entity(model='quad', scale=(50, .5), position=(24.9, 0.1, 5), rotation_z=90, color=color.red.tint(-.5), emissive=True)

sky = Sky(color=color.black)
AmbientLight(color=color.rgba(100, 100, 100, 0.1))

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 3, -15)
camera.fov = 80
mouse.locked = False # Start with mouse unlocked for menu interaction

# --- Arma y Mira ---
pistol = Entity(parent=camera, model='cube', scale=(0.1, 0.2, 0.7), position=(0.4, -0.4, 1), color=color.black, enabled=False)
crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red, enabled=False)

# --- Interfaz de Usuario (UI) Mejorada ---
# Adjusted HUD position (y=0.3) to prevent covering game content
game_hud = Entity(parent=camera.ui, y=0.3, enabled=False) # Moved HUD lower to prevent overlap
# Adjusted scale for score_panel, hits_panel, and accuracy_panel
score_panel = Entity(parent=game_hud, model='quad', scale=(.15, .08), position=(-.2, 0), color=color.black66, origin=(0,0)) # Increased panel height
Text(parent=score_panel, text="PUNTOS", origin=(0,0), y=0.3, scale=2, color=color.white) # Positioned label higher within panel
score_text = Text(parent=score_panel, text="0", origin=(0,0), y=-0.3, scale=3, color=color.white) # Positioned number lower within panel

hits_panel = Entity(parent=game_hud, model='quad', scale=(.15, .08), position=(.2, 0), color=color.black66, origin=(0,0)) # Increased panel height
Text(parent=hits_panel, text="ACIERTOS", origin=(0,0), y=0.3, scale=2, color=color.white) # Positioned label higher within panel
hits_text = Text(parent=hits_panel, text="0", origin=(0,0), y=-0.3, scale=3, color=color.white) # Positioned number lower within panel

accuracy_panel = Entity(parent=game_hud, model='quad', scale=(.2, .08), position=(0, 0), color=color.black66, origin=(0,0)) # Increased panel height
accuracy_text = Text(parent=accuracy_panel, text="Precisión: {accuracy:.1f}%", origin=(0, 0), scale=2.5, color=color.white) # Centered accuracy text

# --- Menú Principal ---
main_menu = Entity(parent=camera.ui, enabled=True)
title = Text(parent=main_menu, text="Guardianes del Blanco", scale=3, origin=(0,0), y=0.2, color=color.white, background=True)
start_button = Button(parent=main_menu, text="INICIAR", color=color.azure, scale=(0.4, 0.1), y=0, on_click=go_to_level_select)
quit_button = Button(parent=main_menu, text="SALIR", color=color.azure, scale=(0.4, 0.1), y=-0.15, on_click=application.quit)

# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False)
level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.3, color=color.white)
level_1_button = Button(parent=level_select_menu, text="Nivel 1", scale=(0.3, 0.1), y=0.1, on_click=lambda: start_level(1))
level_2_button = Button(parent=level_select_menu, text="Nivel 2", scale=(0.3, 0.1), y=0, on_click=lambda: start_level(2))
level_3_button = Button(parent=level_select_menu, text="Nivel 3", scale=(0.3, 0.1), y=-0.1, on_click=lambda: start_level(3))
level_buttons = [level_1_button, level_2_button, level_3_button]

# Initial update of level buttons state
update_level_buttons()

# Run the Ursina application
app.run()