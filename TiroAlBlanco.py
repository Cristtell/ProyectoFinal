# Importamos las librerías necesarias de Ursina
from ursina import * # Importa todas las clases y funciones principales de Ursina
import math # Importa el módulo math para funciones matemáticas (aunque no se usa directamente en este snippet, es útil tenerlo)

# --- Configuración de Niveles ---
# Diccionario que almacena la configuración específica para cada nivel del juego.
LEVEL_CONFIG = { 
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 50}, # Configuración para el Nivel 1 
    2: {'targets': 10, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 60}, # Configuración para el Nivel 2
    3: {'targets': 10, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 75}, # Configuración para el Nivel 3
    #'targets': número de objetivos a aparecer en este nivel.
    #'speed': rango (mínimo, máximo) de velocidad para los objetivos.
    #'scale': tamaño de los objetivos.
}

# --- Clase para los Objetivos Esféricos (¡Ahora Marios!) ---
# Define una clase para los objetivos que el jugador debe disparar. Hereda de 'Entity' de Ursina.

class TargetSphere(Entity):# Constructor de la clase TargetSphere.
    def __init__(self, speed_range, scale):  # Recibe speed_range (rango de velocidad) y scale (escala del objetivo) como argumentos
        side = random.choice([-1, 1]) # Elige aleatoriamente si el objetivo aparecerá desde la izquierda (-1) o derecha (1).
        start_pos = Vec3(22 * side, random.uniform(-8, -2), random.uniform(15, 25)) # Posición Y ajustada para que salgan más bajas
        # (entre -8 y -2 en el eje Y), X: 22 * side (extremo de la pantalla), Y: aleatorio en el rango, Z: aleatorio para la profundidad.
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1))  # Dirección de movimiento del objetivo.
        # X: hacia el centro (-side), Y: un poco hacia arriba o abajo, Z: un poco hacia adelante o atrás.

        
        super().__init__(# Llama al constructor de la clase base (Entity) para inicializar el objeto visual.
            model='quad',  # ¡CAMBIADO A 'quad' para usar una imagen 2D! Un 'quad' es un plano de dos triángulos.
            texture='assets/textures/mario.png', # ¡AQUÍ ES DONDE PONES LA RUTA A TU IMAGEN DE MARIO! La textura que se aplicará al 'quad'.
            color=color.white, # Usa color.white para que la textura no se tiña. Permite que la textura muestre sus colores originales.
            scale=scale, # Establece el tamaño del mario.
            position=start_pos, # Establece la posición inicial del mario
            collider='box',# Cambiamos a 'box' o 'quad' porque ya no es una esfera. 'box' es una buena opción general para colisiones 2D.
            shadow=True, # El mario proyectará una sombra.
            billboard=True # ¡IMPORTANTE! Esto hace que el mario (quad) siempre mire a la cámara, sin importar la rotación, lo que lo hace parecer 2D.
        )

        self.direction = direction # Almacena la dirección de movimiento del mario
        self.speed = random.uniform(speed_range[0], speed_range[1]) # Asigna una velocidad aleatoria dentro del rango.

    def update(self): # Método update se llama automáticamente cada fotograma.
        self.position += self.direction * self.speed * time.dt # Mueve el objetivo. time.dt asegura que el movimiento 
        #sea independiente de la velocidad de fotogramas.
        if abs(self.x) > 24:# Destruye el objetivo si sale de la pantalla (si su posición X absoluta es mayor que 24).
        # e invoca la creación del siguiente objetivo después de un pequeño retraso.
            destroy(self)  # Elimina la entidad actual de la escena.
            invoke(spawn_next_target, delay=0.5) # Llama a spawn_next_target después de 0.5 segundos.

    def hit(self): # Método hit se llama cuando este objetivo es impactado por un raycast (un disparo).
        global hits, points  # Accede a las variables globales de aciertos y puntos.
        hit_sound.play() # Reproduce el sonido de impacto.
        hits += 1 # Incrementa el contador de aciertos.
        points += 100 # Suma 100 puntos al marcador.
        effect = Entity( # Crea un efecto visual de impacto
            model='quad', # El efecto es un quad (plano 2D).
            texture='assets/textures/hit_effect.png', # Textura para el efecto de impacto.
            color=color.white, # Color blanco para no teñir la textura. 
            scale=self.scale * 0.8,  # Escala del efecto, ligeramente más pequeño que el mario.
            position=self.world_position, # Posiciona el efecto donde fue impactado el mario.
            shadow=False, # El efecto no proyecta sombra.
            billboard=True # El efecto siempre mira a la cámara.
            )
        
        effect.animate_scale(self.scale * 1.2, duration=0.2, curve=curve.out_quad) # Anima el crecimiento del efecto.
        effect.fade_out(duration=0.2)  # Anima el desvanecimiento del efecto.
        destroy(effect, delay=0.2) # Destruye el efecto después de 0.2 segundos.

        # Destruye el objetivo y spawnea el siguiente
        destroy(self) # Elimina el mario impactado.
        invoke(spawn_next_target, delay=0.5) # Llama a spawn_next_target después de 0.5 segundos para crear un nuevo objetivo.

# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0  # Inicializa los contadores de aciertos, puntos y disparos.
targets_spawned = 0  # Contador de objetivos que han aparecido.
unlocked_level = 1 # Nivel máximo desbloqueado por el jugador.
current_level = 1 # Nivel actual en el que se encuentra el jugador.
game_active = False # Booleano para saber si el juego está en curso.
last_shot_time = 0 # Guarda el momento del último disparo para controlar la cadencia de fuego.
current_bg_music = None # Variable global para mantener una referencia a la música de fondo actual.


# --- Funciones del Juego ---
def go_to_level_select(): # Función para cambiar al menú de selección de nivel.
    main_menu.disable() # Deshabilita el menú principal.
    start_button.disable() # Deshabilita el botón de inicio.
    quit_button.disable()  # Deshabilita el botón de salir.
    level_select_menu.enable() # Habilita el menú de selección de nivel.
    update_level_buttons() # Actualiza el estado de los botones de nivel (desbloqueados/bloqueados).

def start_level(level): # Función para iniciar un nivel específico.
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music
    current_level = level # Establece el nivel actual.
    hits, points, shots_fired, targets_spawned = 0, 0, 0, 0 # Reinicia los contadores para el nuevo nivel.
    game_active = True # Establece el estado del juego a activo.

    # --- Lógica de la música para reiniciar ---
    # Detenemos y DESTRUIMOS la instancia de música actual si existe.
    if current_bg_music:
        current_bg_music.stop() # Detiene la reproducción.
        destroy(current_bg_music) # ¡IMPORTANTE! Destruye la instancia anterior para liberar recursos.
    
     # Asigna y *CREA UNA NUEVA INSTANCIA* de la música correcta al nivel.
    if current_level == 1:
        current_bg_music = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8) # Música para el nivel 1.
    elif current_level == 2:
        current_bg_music =  Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8) # Música para el nivel 2.
    elif current_level == 3:
        current_bg_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8) # Música para el nivel 3.

    if current_bg_music:
        current_bg_music.play() # Reproduce la música desde el principio.

    level_select_menu.disable() # Deshabilita el menú de selección de nivel.
    game_hud.enable() # Habilita el HUD del juego.
    crosshair.enable() # Habilita la mira.
    mouse.locked = True  # Bloquea el cursor del ratón en el centro de la pantalla.
    last_shot_time = time.time()  # Establece el tiempo del último disparo al momento actual.
    
    # Deshabilita todas las armas y luego habilita la del nivel actual.
    pistol.disable() 
    rifle.disable()
    shotgun.disable()

    if current_level == 1:
        pistol.enable()
    elif current_level == 2:
        rifle.enable()
    elif current_level == 3:
        shotgun.enable()

    # Destruye cualquier objetivo que pueda haber quedado de una partida anterior.
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    spawn_next_target()  # Llama a la función para generar el primer objetivo.
    
def spawn_next_target(): # Función para generar el siguiente objetivo.
    global targets_spawned # Accede a la variable global de objetivos generados.
    if not game_active: return # Si el juego no está activo, no genera objetivos.
    
    # Comprueba si aún quedan objetivos por generar para el nivel actual.
    if targets_spawned < LEVEL_CONFIG.get(current_level, {}).get('targets', 0):
        config = LEVEL_CONFIG.get(current_level, {}) # Obtiene la configuración del nivel actual.
        TargetSphere(config.get('speed', (10, 15)), config.get('scale', 1)) # Crea un nuevo objetivo con la velocidad y escala del nivel actual.
        targets_spawned += 1 # Incrementa el contador de objetivos generados.
        update_hud() # Actualiza el HUD con la nueva información.
    else:
        invoke(end_level, delay=1) # Si no quedan objetivos, llama a end_level después de 1 segundo.

# Función para finalizar un nivel.
def end_level():
    global game_active, unlocked_level, current_bg_music
    game_active = False # Establece el estado del juego a inactivo.

    # Detiene y destruye la música de fondo actual.
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music) # También destruimos la música al finalizar el nivel para liberar recursos.
        current_bg_music = None

    # Deshabilita HUD, armas y mira, los elementos del juego.
    game_hud.disable()
    crosshair.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    mouse.locked = False # Desbloquea el cursor del ratón.

     # Calcula la precisión del jugador.
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG.get(current_level, {}).get('accuracy_goal', 0)
    
     # Crea un panel de fin de nivel para mostrar los resultados.
    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .5), color=color.dark_gray.tint(.2), z=1)
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0, scale=1.5)
    Text(parent=end_panel, text=f"Aciertos: {hits} / {shots_fired}", origin=(0,0), y=-.1, scale=1.5)

    # Lógica para cuando el nivel es completado con éxito.
    if accuracy >= goal:
        message = f"¡NIVEL {current_level} COMPLETADO!"
        if current_level < 3: # Si no es el último nivel, desbloquea el siguiente.
            unlocked_level = max(unlocked_level, current_level + 1) # Asegura que se desbloquee el nivel más alto.

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2) 
        Button(parent=end_panel, text="Menú de Niveles", color=color.azure, scale=(0.25, 0.08), y=-.3, on_click=Func(lambda: 
        (destroy(end_panel), show_level_select_menu()))) # Botón para ir al menú de niveles.
    
    # Lógica para cuando el nivel no es completado (precisión insuficiente).
    else:
        message = "INTÉNTALO DE NUEVO"

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)
        Button(parent=end_panel, text="Reintentar", color=color.azure, scale=(0.25, 0.08), y=-.25, on_click=Func(lambda: 
        (destroy(end_panel), start_level(current_level))))  # Botón para reintentar el nivel.
        Button(parent=end_panel, text="Menú de Niveles", color=color.red, scale=(0.25, 0.08), y=-.4, on_click=Func(lambda: 
        (destroy(end_panel), show_level_select_menu()))) # Botón para volver al menú de niveles.

# Función para mostrar el menú de selección de nivel.
def show_level_select_menu():
    global current_bg_music
    game_hud.disable() # Deshabilita el HUD.
    pistol.disable() # Deshabilita el arma.
    rifle.disable() # Deshabilita el rifle.
    shotgun.disable() # Deshabilita la escopeta.
    crosshair.disable() # Deshabilita la mira.

    # Destruye todos los objetivos que puedan estar en la escena.
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    level_select_menu.enable() # Habilita el menú de selección de nivel.
    update_level_buttons() # Actualiza el estado de los botones de nivel.
    mouse.locked = False# Desbloquea el cursor.

    # Detener y destruir la música de fondo al ir a la selección de nivel.
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

# Función para mostrar el menú principal.
def show_main_menu():
    global current_bg_music
    level_select_menu.disable()  # Deshabilita el menú de selección.
    game_hud.disable() # Deshabilita el HUD del juego.
    pistol.disable() # Deshabilita la pistola.
    rifle.disable() # Deshabilita el rifle.
    shotgun.disable() # Deshabilita la escopeta.
    crosshair.disable() # Deshabilita la mira.

    # Destruye todos los objetivos que puedan estar en la escena.
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    main_menu.enable() # Habilita el menú principal.
    start_button.enable() # Asegura que el botón INICIAR se muestre
    quit_button.enable() # Asegura que el botón SALIR se muestre
    mouse.locked = False # Desbloquea el cursor del ratón.

    # Detener y destruir la música de fondo al ir al menú principal.
    if current_bg_music: 
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

# Función para actualizar el texto del HUD (Heads-Up Display).
def update_hud():
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0 # Calcula la precisión, evitando división por cero.
    hud_text.text = ( # Formatea el texto a mostrar en el HUD.
        f"NIVEL {current_level}\n"
        f"Objetivo: {targets_spawned}/{LEVEL_CONFIG.get(current_level, {}).get('targets', 0)}\n"
        f"Aciertos: {hits}\n"
        f"Precisión: {accuracy:.1f}%"
    )

# Función para actualizar el estado de los botones de selección de nivel (habilitar/deshabilitar).
def update_level_buttons():
    for i, button in enumerate(level_buttons): # Itera sobre cada botón de nivel.
        button.disabled = (i + 1 > unlocked_level) # Deshabilita el botón si su nivel es mayor que el desbloqueado.
        button.text_entity.color = color.white if not button.disabled else color.gray # Cambia el color del texto según si está habilitado o no

# Función para reanudar el juego desde el menú de pausa.
def resume_game():
    global current_bg_music
    pause_menu.disable() # Deshabilita el menú de pausa.
    mouse.locked = True # Bloquea el cursor del ratón.
    application.resume() # Reanuda la lógica del juego de Ursina.

    # Reanuda la música de fondo si estaba sonando (continuará desde donde se pausó).
    if current_bg_music:
        current_bg_music.play()

# --- Inicialización de la Aplicación Ursina ---
# Crea la ventana de la aplicación Ursina. Set fullscreen=True to make the window maximize to the full screen.
app = Ursina(title='AIM PRESICION DDC', borderless=False, fullscreen=True)

# --- SOLUCIÓN PARA EL ERROR 'info_text' y color de los números de FPS ---
# Asegúrate de que el contador de FPS esté habilitado
window.fps_counter.enabled = True 

# Función para colorear los textos de depuración
def set_debug_text_color():
    # Iteramos sobre todas las entidades de tipo Text en la escena
    for entity in scene.entities:
        if isinstance(entity, Text):
            # Comprobamos si el texto contiene dígitos y es de color blanco (común para los stats de Ursina)
            if entity.text and any(char.isdigit() for char in entity.text):
                if entity.color == color.white or entity.color == color.light_gray:
                    entity.color = color.black # Cambia el color a negro para que se vea en fondos claros
    # Opcional: ajustar el fondo del contador de FPS si existe
    if window.fps_counter.enabled and hasattr(window.fps_counter, 'bg'):
        window.fps_counter.bg.color = color.clear # Hace el fondo transparente

# Llama a la función después de un pequeño retraso para asegurar que los textos de debug ya existan
invoke(set_debug_text_color, delay=0.1) 


# --- Sonidos ---
gunshot_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.3)
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)

# ¡IMPORTANTE! ELIMINA LAS SIGUIENTES LÍNEAS.
# Las instancias de Audio para la música de fondo se crearán dinámicamente en start_level.
# Esto evita que se carguen todas las músicas al inicio y que se generen múltiples instancias.
#start_sound = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8)
#level2_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8)
#level3_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8)


# --- Creación del Entorno (Cabina de Disparo con estilo oscuro) ---
# Entidad para el fondo general, que no se usa directamente en la cabina de disparo actual (deshabilitado).
shooting_range_background = Entity(
    model='quad',
    texture='assets/textures/mapa.png',
    scale=(100, 50), # Un tamaño grande para cubrir el fondo.
    position=(0, 0, 50), # Posición Z alejada del jugador para que no interfiera con la vista.
    rotation_y =180, # Rotación para que la textura se vea correctamente.
    double_sided=True # Permite que la textura se vea desde ambos lados del plano.
).disable() # Se crea, pero se deshabilita inmediatamente.

# Cabina de Disparo - ESTILO OSCURO*
# Pared trasera del escenario de disparo.
back_wall = Entity(  # Crea una nueva entidad (un objeto en la escena) y la asigna a la variable 'back_wall'.
    model='cube', # Define la forma de la entidad. En este caso, es un cubo.
    scale=(40, 30, 1), # Ancho: 40 unidades, Alto: 30, Profundidad: 1.
    position=(0, 5, 30), # Ubicación central: X=0, Y=5, Z=30 (esta es la pared trasera, lejos del jugador).
    texture='assets/textures/mapa.png', # Textura aplicada a la pared.
    color=color.white, # Cambiado a blanco para que la textura se vea sin tintes de color.
    collider='box' # Asigna un colisionador de tipo caja para interacciones físicas.
)

# Pared izquierda del escenario.
left_wall = Entity(
    model='cube',
    scale=(1, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 60 (cubre el rango Z).
    position=(-20, 5, 7.5), # Posición X ajustada a -20 (izquierda).
    texture='assets/textures/mapa.png', # Textura aplicada a la pared izquierda.
    color=color.white, # Asegura que la textura se vea
    collider='box'
)

# Pared derecha del escenario.
right_wall = Entity(
    model='cube',
    scale=(1, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 60.
    position=(20, 5, 7.5),
    texture='assets/textures/mapa.png', # Posición X ajustada a 20 (derecha).
    color=color.white, # Asegura que la textura se vea
    collider='box'
)

# Techo del escenario.
ceiling = Entity(
    model='cube',
    scale=(42, 1, 45), # ANCHO AJUSTADO: Ahora es 42 para cubrir el espacio de 40 de la pared trasera y un poco más.
    position=(0, 20, 7.5), # Posición X=0 (centrado), Y=20 (altura del techo), Z=7.5 (posición Z central).
    texture='assets/textures/cieloo.png', # Textura del cielo (asumiendo que 'cieloo.png' es la versión oscura).
    color=color.white, # Asegura que la textura se vea
    collider='box'
)

# Suelo (con textura de césped oscuro)
ground_plane = Entity(
    model='plane', # Un plano es una superficie plana.
    scale=(150, 1, 150), # Un tamaño muy grande para asegurar que siempre haya suelo 
    position=(0, -10, 5), # Posición Y ajustada para estar más cerca del nivel de los patos.
    texture='assets/textures/piso.png', # Cambiado a una textura de cesped oscuro.
    texture_scale=(2, 2), # Escala de la textura para que se vea más grande y cercano.
    collider='box'
)

# Cielo del juego (completamente negro).
sky_color = Sky(color=color.black)

# Luz direccional (simula una fuente de luz lejana como el sol).
sun = DirectionalLight(y=10, x=20, shadows=True, color=color.white) # Con sombras y color blanco.
# ¡AÑADIMOS LUZ AMBIENTAL para iluminar las áreas en sombra!
# La luz ambiental ilumina uniformemente toda la escena, reduciendo las sombras muy oscuras.
ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 255)) # Una luz ambiental gris suave.

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 0, -15) # Posición de la cámara (el jugador).
camera.fov = 80 # Campo de visión de la cámara.

# --- Arma y Mira (DISEÑOS MEJORADOS y CORREGIDOS) ---
# Asegúrate que todas estas texturas existan en 'assets/textures/'
# y sean archivos .png con transparencia si lo deseas.

# Pistola mejorada
# La entidad 'pistol' ahora solo actúa como un contenedor para sus partes (modelos más pequeños que la componen).
pistol = Entity(parent=camera, position=(0.4, -0.45, 1.2), rotation=(0, 0, 0))
Entity(parent=pistol, model='cube', scale=(0.12, 0.2, 0.6), texture='assets/textures/pistol_body.png', color=color.black) # Cuerpo principal de la pistola.
Entity(parent=pistol, model='cube', scale=(0.12, 0.3, 0.2), position=(0, -0.2, -0.2), texture='assets/textures/pistol_grip.png', color=color.white) # Empuñadura de la pistola.
Entity(parent=pistol, model='cube', scale=(0.1, 0.15, 0.55), position=(0, 0.07, 0), texture='assets/textures/pistol_slide.png', color=color.black) # Corredera de la pistola.
Entity(parent=pistol, model='cube', scale=(0.05, 0.05, 0.1), position=(0, 0.07, 0.3), texture='assets/textures/pistol_barrel.png', color=color.white) # Cañón asomando.
Entity(parent=pistol, model='cube', scale=(0.04, 0.08, 0.05), position=(0, -0.07, -0.1), texture='assets/textures/pistol_trigger.png', color=color.white) # Gatillo de la pistola.
Entity(parent=pistol, model='cube', scale=(0.02, 0.02, 0.05), position=(0, 0.15, 0.25), texture='assets/textures/pistol_sight_front.png', color=color.red) # Miras de la pistola (delantera).
Entity(parent=pistol, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.15, -0.25), texture='assets/textures/pistol_sight_rear.png', color=color.yellow) # Miras de la pistola (trasera).
pistol.disable() # La pistola está deshabilitada por defecto al inicio.


# Rifle mejorado
# La entidad 'rifle' ahora solo actúa como un contenedor.
rifle = Entity(parent=camera, position=(0.6, -0.55, 1.8), rotation=(0,0,0))
Entity(parent=rifle, model='cube', scale=(0.1, 0.1, 1.2), texture='assets/textures/rifle_body.png', color=color.black) # Cuerpo principal / Receptor del rifle.
Entity(parent=rifle, model='cylinder', scale=(0.05, 0.05, 0.8), position=(0, 0, 0.6), rotation_x=90, texture='assets/textures/rifle_barrel.png', color=color.black) # Cañón del rifle.
Entity(parent=rifle, model='cube', scale=(0.1, 0.25, 0.3), position=(0, -0.1, -0.6), texture='assets/textures/rifle_stock.png', color=color.black) # Culata del rifle.
Entity(parent=rifle, model='cube', scale=(0.08, 0.2, 0.1), position=(0, -0.15, -0.3), texture='assets/textures/rifle_grip.png', color=color.black) # Empuñadura de pistola del rifle.
Entity(parent=rifle, model='cylinder', scale=(0.05, 0.05, 0.3), position=(0, 0.08, 0.2), rotation_x=90, texture='assets/textures/rifle_scope.png', color=color.yellow) # Mira telescópica del rifle.
Entity(parent=rifle, model='circle', scale=0.04, position=(0, 0.08, 0.35), rotation_x=90, texture='assets/textures/rifle_scope_lens.png', color=color.red) # Lente de la mira telescópica.
Entity(parent=rifle, model='cube', scale=(0.02, 0.1, 0.02), position=(-0.05, -0.08, 0.3), texture='assets/textures/rifle_bipod_left.png', color=color.white) # Bípode del rifle (patas).
Entity(parent=rifle, model='cube', scale=(0.02, 0.1, 0.02), position=(0.05, -0.08, 0.3), texture='assets/textures/rifle_bipod_right.png', color=color.white) # Cargador del rifle.
Entity(parent=rifle, model='cube', scale=(0.06, 0.2, 0.1), position=(0, -0.1, -0.1), texture='assets/textures/rifle_magazine.png', color=color.white) # Riel Picatinny en la parte superior.
Entity(parent=rifle, model='cube', scale=(0.08, 0.01, 0.8), position=(0, 0.06, 0), texture='assets/textures/rifle_rail.png', color=color.black) # Riel Picatinny en la parte inferior.
rifle.disable() # El rifle está deshabilitado por defecto al inicio.

# Escopeta mejorada
shotgun = Entity(parent=camera, position=(0.5, -0.65, 1.5), rotation=(0,0,0))
Entity(parent=shotgun, model='cube', scale=(0.18, 0.15, 1.0), texture='assets/textures/shotgun_body.png', color=color.white) # Cuerpo principal de la escopeta.
Entity(parent=shotgun, model='cylinder', scale=(0.08, 0.08, 0.8), position=(0, 0, 0.5), rotation_x=90, texture='assets/textures/shotgun_barrel.png', color=color.white) # Cañón de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.12, 0.1, 0.25), position=(0, -0.05, 0.2), texture='assets/textures/shotgun_forend.png', color=color.white) # Guardamanos/Bomba de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.18, 0.3, 0.15), position=(0, -0.2, -0.4), texture='assets/textures/shotgun_grip_stock.png', color=color.white) # Culata y empuñadura de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.18, 0.05, 0.3), position=(0, 0.1, -0.1), texture='assets/textures/shotgun_receiver.png', color=color.white) # Recámara o parte superior del cuerpo de la escopeta.
Entity(parent=shotgun, model='cylinder', scale=(0.05, 0.05, 0.7), position=(0, -0.08, 0.3), rotation_x=90, texture='assets/textures/shotgun_magtube.png', color=color.white) # Cargador tubular bajo el cañón de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.02, 0.03, 0.05), position=(0, 0.08, 0.45), texture='assets/textures/shotgun_sight_front.png', color=color.white) # Alza y mira delantera de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.08, -0.2), texture='assets/textures/shotgun_sight_rear.png', color=color.white)  # Alza y mira trasera de la escopeta.
shotgun.disable() # La escopeta está deshabilitada por defecto al inicio.

crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red) # La mira en el centro de la pantalla.

# --- Interfaz de Usuario (UI) Mejorada ---
game_hud = Entity(parent=camera.ui, enabled=False) # Entidad para el HUD del juego, deshabilitada por defecto.
hud_background = Entity(
parent=game_hud, 
model='quad',
scale=(.35, .25), # Tamaño del fondo del HUD.
position=window.bottom_left, color=color.black66) # Posición en la esquina inferior izquierda con un pequeño margen.
# Un color negro semi-transparente.

# Texto del HUD que mostrará la información del juego.
hud_text = Text(
parent=hud_background, 
text="", # Texto inicial vacío.
origin=(-.5, .5), # Origen en la esquina inferior izquierda del texto.
position=(-.45, .45),  # Pequeño margen dentro del fondo del HUD.
scale=1.2  # Tamaño del texto.
)

# --- Menú Principal ---
# El logo ahora se escala para ocupar toda la pantalla y se centra.
main_menu = Entity( 
    parent=camera.ui, # Es hijo de la UI de la cámara para que siempre se vea en pantalla.
    model='quad',  # Es un plano 2D.
    texture='assets/textures/logo.png', # Asegúrate que esta textura exista
    scale=(window.aspect_ratio * 1.1, 1.1), # Escala para cubrir la pantalla completa. Puedes ajustar 1.4 si ves bordes.
    position=(0, 0, 0), # Centrado en la pantalla
    enabled=True, # Habilitado por defecto al iniciar el juego.
    z=0.1, # Un valor Z ligeramente superior para asegurar que esté delante de otros elementos.
    color=color.white # Color blanco para mostrar la textura sin tintes.
)

# Los botones ya NO son hijos de main_menu, son hijos de camera.ui directamente
# para poder posicionarlos independientemente sobre el logo que ocupa toda la pantalla.
start_button = Button( # Botón "INICIAR" en el menú principal.
    parent=camera.ui, 
    text="INICIAR", # Texto del botón.
    color=color.azure, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.lime, # Color al presionar el botón.
    scale=(0.30, 0.10), # Escala del botón.
    x=-0.32, # Posición X del botón (izquierda).
    y=-0.32, # Posición Y del botón (abajo).
    text_origin=(0,0), # Origen del texto en el centro del botón.
    text_color=color.white, # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.15, # Radio para bordes redondeados.
    texture='assets/textures/button_start.jpg',  # Usa una textura personalizada si tienes una
    on_click=go_to_level_select,    # Acción al hacer clic, va al menú de selección de nivel.
    z=-0.1 # Un valor Z ligeramente superior para asegurar que esté delante de otros elementos.
    # tooltip eliminado
)

quit_button = Button( # Botón "SALIR" en el menú principal.
    parent=camera.ui,
    text="SALIR", # Texto del botón.
    color=color.red, # Color del botón.
    highlight_color=color.orange, # Color al pasar el ratón por encima.
    pressed_color=color.yellow, # Color al presionar el botón.
    scale=(0.30, 0.10), # Escala del botón.
    x=0.32, # Posición X del botón (derecha).
    y=-0.32, # Posición Y del botón (abajo).
    text_origin=(0,0), # Origen del texto en el centro del botón.
    text_color=color.white, # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.15, # Radio para bordes redondeados.
    texture='assets/textures/button_quit.jpg',  # Usa una textura personalizada si tienes una
    on_click=application.quit, # Acción al hacer clic, cierra la aplicación.
    z=-0.1 # Un valor Z ligeramente superior para asegurar que esté delante de otros elementos.
    # tooltip eliminado
)


# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False) # Entidad para el menú de selección de nivel, deshabilitada por defecto.
level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.4) # Título del menú.

level_1_button = Button( #Boton para el Nivel 1.
    parent=level_select_menu,   
    text="Nivel 1", # Texto del botón.
    scale=(0.35, 0.12), # Escala del botón.
    y=0.13, # Posición Y del botón (arriba).
    color=color.red, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.lime, # Color al presionar el botón.
    text_color=color.white,   # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.18,  
    texture='assets/textures/button_level1.jpg',  # Usa una textura personalizada si tienes una
    on_click=lambda: start_level(1) # Acción al hacer clic, inicia el nivel 1.
)

level_2_button = Button(# Botón para el Nivel 2.
    parent=level_select_menu,
    text="Nivel 2", # Texto del botón.
    scale=(0.35, 0.12), # Escala del botón.
    y=-0.01, # Posición Y del botón (casi al centro).
    color=color.red, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.azure, # Color al presionar el botón.
    text_color=color.white, # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.18, # Radio para bordes redondeados.
    texture='assets/textures/button_level2.jpg',  # Usa una textura personalizada si tienes una
    on_click=lambda: start_level(2) # Acción al hacer clic, inicia el nivel 2.
)

level_3_button = Button( # Botón para el Nivel 3.
    parent=level_select_menu,
    text="Nivel 3", # Texto del botón.
    scale=(0.35, 0.12), # Escala del botón.
    y=-0.15,  # Cambiado para que aparezca debajo del botón 2
    color=color.red, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.azure, # Color al presionar el botón.
    text_color=color.white, # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.18, # Radio para bordes redondeados.
    texture='assets/textures/button_level3.jpg',  # Usa una textura personalizada si tienes una
    on_click=lambda: start_level(3) # Acción al hacer clic, inicia el nivel 3.
)

# Lista de botones de nivel para iterar sobre ellos y actualizar su estado.
level_buttons = [level_1_button, level_2_button, level_3_button]

# --- Menú de Pausa ---
pause_menu = Entity(parent=camera.ui, enabled=False, model='quad', scale=(0.5, 0.5), color=color.black90)
Text(parent=pause_menu, text="Juego en Pausa", origin=(0,0), y=0.4, scale=2)

Button(parent=pause_menu, text="Reanudar Juego", color=color.azure, scale=(0.8, 0.2), y=0.15, on_click=resume_game)
Button(parent=pause_menu, text="Menú de Niveles", color=color.blue, scale=(0.8, 0.2), y=-0.1, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_level_select_menu())))
Button(parent=pause_menu, text="Salir al Menú Principal", color=color.red, scale=(0.8, 0.2), y=-0.35, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_main_menu())))


# --- Lógica Principal ---
def update(): # Función 'update' se llama automáticamente cada fotograma del juego.
    global current_bg_music
    if not application.paused and game_active: # Solo ejecuta la lógica de movimiento de la cámara y HUD si el juego no está pausado y está activo.
        update_hud()  # Actualiza la información mostrada en el HUD.
        camera.rotation_y += mouse.velocity.x * 60 # Ajusta la rotación de la cámara en el eje Y según el movimiento del ratón.
        camera.rotation_x -= mouse.velocity.y * 60 # Ajusta la rotación de la cámara en el eje X según el movimiento del ratón.
        camera.rotation_x = clamp(camera.rotation_x, -50, 50) # Limita la rotación en el eje X para evitar voltear demasiado la cámara.
        camera.rotation_y = clamp(camera.rotation_y, -80, 80)  # Limita la rotación en el eje Y para evitar giros excesivos.
    elif application.paused and current_bg_music and current_bg_music.playing: # Si el juego está pausado y hay música de fondo reproduciéndose.
        current_bg_music.pause() # Pausa la música de fondo.

def input(key): # Función 'input' se llama automáticamente cuando hay una entrada de teclado o ratón.
    global shots_fired, last_shot_time, current_bg_music
    if key == 'escape' and game_active: # Lógica para pausar/despausar el juego con la tecla 'escape'.
        application.paused = not application.paused # Invierte el estado de pausa de la aplicación.
        pause_menu.enabled = application.paused  # Habilita/deshabilita el menú de pausa según el estado de la aplicación.
        mouse.locked = not pause_menu.enabled # Bloquea/desbloquea el cursor del ratón según el estado del menú de pausa.
        if application.paused: # Pausa o reanuda la música según el estado de pausa del juego.
            if current_bg_music:
                current_bg_music.pause()
        else:
            if current_bg_music:
                current_bg_music.play()

    # Si el juego está pausado, ignora otras entradas de teclado/ratón.
    if application.paused:
        return
    
     # Lógica para disparar con el clic izquierdo del ratón cuando el juego está activo.
    if game_active and key == 'left mouse down': # Control de cadencia de fuego para todas las armas (evita disparos demasiado rápidos).
        if time.time() - last_shot_time < 0.5: # Si ha pasado menos de 0.5 segundos desde el último disparo, no dispares.
            return
        last_shot_time = time.time()  # Actualiza el tiempo del último disparo.

        shots_fired += 1 # Incrementa el contador de disparos.
        gunshot_sound.play() # Reproduce el sonido de disparo.

        # Animación del retroceso del arma según el nivel actual.
        if current_level == 1:
            pistol.rotation_x = -10 # Ajusta el retroceso de la pistola.
            pistol.animate_rotation_x(0, duration=0.1)  # Anima la rotación de la pistola.
            ignore_list = [pistol] # Lista de entidades a ignorar en el raycast (para que el raycast no impacte el arma).
        elif current_level == 2:
            rifle.rotation_x = -5 # Ajusta el retroceso del rifle.
            rifle.animate_rotation_x(0, duration=0.1) # Anima la rotación del rifle.
            ignore_list = [rifle] # Lista de entidades a ignorar en el raycast.
        elif current_level == 3:
            shotgun.rotation_x = -15 # Ajusta el retroceso de la escopeta.
            shotgun.animate_rotation_x(0, duration=0.1) # Anima la rotación de la escopeta.
            ignore_list = [shotgun] # Lista de entidades a ignorar en el raycast.
        else:
            ignore_list = [] # Si no hay un nivel activo, no ignoramos nada.

        # Realiza un raycast (un "disparo" invisible) desde la cámara hacia adelante
        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=ignore_list)
        if hit_info.hit and hasattr(hit_info.entity, 'hit'):# Si el raycast impacta algo y ese algo tiene un método 'hit', lo llama.
            hit_info.entity.hit()


# --- Iniciar el Juego ---
# Estas líneas se ejecutan una vez al inicio del script, antes de que el bucle principal de la aplicación comience.
# Sirven para asegurar que la UI del juego y las armas estén ocultas, y el ratón desbloqueado,
# antes de que el jugador interactúe con el menú principal.

game_hud.disable() # Deshabilita la interfaz de usuario del juego (HUD), haciéndola invisible al inicio
pistol.disable() # Deshabilita la entidad de la pistola, ocultándola de la vista al inicio.
rifle.disable() # Deshabilita la entidad del rifle, ocultándola de la vista al inicio.
shotgun.disable() # Deshabilita la entidad de la escopeta, ocultándola de la vista al inicio.
crosshair.disable() # Deshabilita la mira del arma, haciéndola invisible al inicio.
mouse.locked = False # Desbloquea el cursor del ratón, permitiendo que se mueva libremente por la pantalla
# (necesario para interactuar con los botones del menú).
app.run() # Inicia la aplicación Ursina, lo que hace que la ventana del juego se abra y el bucle principal comience a ejecutarse.