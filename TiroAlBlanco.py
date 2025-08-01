# Importamos las librerías necesarias de Ursina
from ursina import * # Importa todas las clases y funciones principales de Ursina
from ursina.prefabs.first_person_controller import FirstPersonController # Importa el controlador de primera persona
import math # Importa el módulo math para funciones matemáticas (aunque no se usa directamente en este snippet, es útil tenerlo)

# --- Configuración de Niveles ---
# Diccionario que almacena la configuración específica para cada nivel del juego.
LEVEL_CONFIG = {
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 50}, # Configuración para el Nivel 1
    2: {'targets': 12, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 60}, # Configuración para el Nivel 2
    3: {'targets': 15, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 75}, # Configuración para el Nivel 3
    #'targets': número de objetivos a aparecer en este nivel.
    #'speed': rango (mínimo, máximo) de velocidad para los objetivos.
    #'scale': tamaño de los objetivos.
}

# --- Clase para los Objetivos Esféricos (¡Ahora Marios!) ---
# Define una clase para los objetivos que el jugador debe disparar. Hereda de 'Entity' de Ursina.

class TargetSphere(Entity):# Constructor de la clase TargetSphere.
    def __init__(self, speed_range, scale ): # Recibe speed_range (rango de velocidad) y scale (escala del objetivo) como argumentos
        side = random.choice([-1, 1]) # Elige aleatoriamente si el objetivo aparecerá desde la izquierda (-1) o derecha (1).
        # Posición Y ajustada para que salgan más bajas, ahora relativa al nuevo suelo en y=0
        start_pos = Vec3(22 * side, random.uniform(2, 8), random.uniform(15, 25)) # Ajustada para que salgan por encima del suelo
        # (entre 2 y 8 en el eje Y), X: 22 * side (extremo de la pantalla), Y: aleatorio en el rango, Z: aleatorio para la profundidad.
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1)) # Dirección de movimiento del objetivo.
        # X: hacia el centro (-side), Y: un poco hacia arriba o abajo, Z: un poco hacia adelante o atrás.
        


        super().__init__(# Llama al constructor de la clase base (Entity) para inicializar el objeto visual.
            model='quad', # ¡CAMBIADO A 'quad' para usar una imagen 2D! Un 'quad' es un plano de dos triángulos.
            texture='assets/textures/ovni.png', # ¡AQUÍ ES DONDE PONES LA RUTA A TU IMAGEN DE MARIO! La textura que se aplicará al 'quad'.
            color=color.white, # Usa color.white para que la textura no se tiña. Permite que la textura muestre sus colores originales.
            scale=4, # Establece el tamaño del mario.
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
            destroy(self) # Elimina la entidad actual de la escena.
            invoke(spawn_next_target, delay=0.5) # Llama a spawn_next_target después de 0.5 segundos.

    def hit(self): # Método hit se llama cuando este objetivo es impactado por un raycast (un disparo).
        global hits, points # Accede a las variables globales de aciertos y puntos.
        hit_sound.play() # Reproduce el sonido de impacto.
        hits += 1 # Incrementa el contador de aciertos.
        points += 100 # Suma 100 puntos al marcador.
        effect = Entity( # Crea un efecto visual de impacto
            model='quad', # El efecto es un quad (plano 2D).
            texture='assets/textures/hit_effect.png', # Textura para el efecto de impacto.
            color=color.white, # Color blanco para no teñir la textura.
            scale=self.scale * 0.8, # Escala del efecto, ligeramente más pequeño que el mario.
            position=self.world_position, # Posiciona el efecto donde fue impactado el mario.
            shadow=False, # El efecto no proyecta sombra.
            billboard=True # El efecto siempre mira a la cámara.
            )

        effect.animate_scale(self.scale * 1.2, duration=0.2, curve=curve.out_quad) # Anima el crecimiento del efecto.
        effect.fade_out(duration=0.2) # Anima el desvanecimiento del efecto.
        destroy(effect, delay=0.2) # Destruye el efecto después de 0.2 segundos.

        # Destruye el objetivo y spawnea el siguiente
        destroy(self) # Elimina el mario impactado.
        invoke(spawn_next_target, delay=0.5) # Llama a spawn_next_target después de 0.5 segundos para crear un nuevo objetivo.

# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0 # Inicializa los contadores de aciertos, puntos y disparos.
targets_spawned = 0 # Contador de objetivos que han aparecido.
unlocked_level = 1 # Nivel máximo desbloqueado por el jugador.
current_level = 1 # Nivel actual en el que se encuentra el jugador.
game_active = False # Booleano para saber si el juego está en curso.
last_shot_time = 0 # Guarda el momento del último disparo para controlar la cadencia de fuego.
current_bg_music = None # Variable global para mantener una referencia a la música de fondo actual.
player = None # Referencia global para el FirstPersonController

# --- Funciones del Juego ---
def go_to_level_select(): # Función para cambiar al menú de selección de nivel.
    main_menu.disable() # Deshabilita el menú principal.
    start_button.disable() # Deshabilita el botón de inicio.
    quit_button.disable() # Deshabilita el botón de salir.
    fondo_blanco.disable() # Deshabilita el fondo blanco.
    level_select_menu.enable() # Habilita el menú de selección de nivel.
    update_level_buttons() # Actualiza el estado de los botones de nivel (desbloqueados/bloqueados).

def start_level(level): # Función para iniciar un nivel específico.
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music, player
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
        current_bg_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8) # Música para el nivel 2.
    elif current_level == 3:
        current_bg_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8) # Música para el nivel 3.

    if current_bg_music:
        current_bg_music.play() # Reproduce la música desde el principio.

    level_select_menu.disable() # Deshabilita el menú de selección de nivel.
    game_hud.enable() # Habilita el HUD del juego.
    crosshair.enable() # Habilita la mira.
    mouse.locked = True # Bloquea el cursor del ratón en el centro de la pantalla.
    last_shot_time = time.time() # Establece el tiempo del último disparo al momento actual.

    # Habilita el controlador de primera persona
    if player:
        player.enable()
        player.position = (0, 1.8, -15) # Reinicia la posición del jugador al inicio del nivel con altura de ojos estándar
    else:
        player = FirstPersonController(position=(0, 1.8, -15)) # Crea el jugador si no existe, con altura de ojos estándar

    # Establece el padre de las armas directamente a la cámara
    pistol.parent = camera
    rifle.parent = camera
    shotgun.parent = camera

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

    spawn_next_target() # Llama a la función para generar el primer objetivo.

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
    global game_active, unlocked_level, current_bg_music, player
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
    if player:
        player.disable() # Deshabilita el controlador de primera persona
    mouse.locked = False # Desbloquea el cursor del ratón.

      # Calcula la precisión del jugador.
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG.get(current_level, {}).get('accuracy_goal', 0)


#-----//////////MOSTRAR LOS RESULTADOS////////-----
      # Crea un panel de fin de nivel para mostrar los resultados.
    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .7), color=color.white.tint(.2), z=1)
    Text(
        parent=end_panel, 
        text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", 
        color=color.black, 
        origin=(0,0), 
        y=0, 
        scale=1.9,
        font='assets/fonts/CenturyGothicBold.ttf'
        )
    Text(
        parent=end_panel, 
        text=f"Aciertos: {hits} / {shots_fired}", 
        color=color.black, 
        origin=(0,0), 
        y=-.1, 
        scale=1.9,
        font='assets/fonts/CenturyGothicBold.ttf'
        )

    # Lógica para cuando el nivel es completado con éxito.
    if accuracy >= goal:
        message = f" NIVEL {current_level} COMPLETADO "
        
        if current_level < len(LEVEL_CONFIG): # Si no es el último nivel, desbloquea el siguiente.
            unlocked_level = max(unlocked_level, current_level + 1) # Asegura que se desbloquee el nivel más alto.

        Text(
            parent=end_panel, 
            text=message, 
            color=color.black, 
            origin=(0,0), 
            y=.2, 
            scale=3,
            font='assets/fonts/keetano_katana.ttf'
            )
        Button(
            parent=end_panel, 
            text="Menú de Niveles", 
            highlight_color=color.orange,
            pressed_color=color.yellow,
            color=color.red, 
            scale=(0.40, 0.15), 
            y=-.3,
            text_color=color.white,
            font='assets/fonts/CenturyGothicBold.ttf', 
            texture='assets/textures/button_menu.jpg',
            model='quad',
            radius=0.18,
            on_click=Func(lambda:
        (destroy(end_panel), show_level_select_menu()))) # Botón para ir al menú de niveles.

    # Lógica para cuando el nivel no es completado (precisión insuficiente).
    else:
        message = "INTENTALO DE NUEVO"
        Text(
            parent=end_panel, 
            text=message,
            color=color.black, 
            origin=(0,0), 
            y=.2, 
            scale=3,
            font='assets/fonts/keetano_katana.ttf'
            )
        Button(
            parent=end_panel, 
            text="Reintentar", 
            highlight_color=color.orange,
            pressed_color=color.yellow,
            color=color.red, 
            scale=(0.35, 0.12), 
            y=-.25, 
            text_color=color.white,
            font='assets/fonts/CenturyGothicBold.ttf', 
            texture='assets/textures/button_rententar.jpg',
            model='quad',
            radius=0.18,
            on_click=Func(lambda:
        (destroy(end_panel), start_level(current_level)))) # Botón para reintentar el nivel.
        Button(
            parent=end_panel, 
            text="Menú de Niveles", 
            highlight_color=color.orange,
            pressed_color=color.yellow,
            color=color.red, 
            scale=(0.35, 0.12), 
            text_color=color.white,
            font='assets/fonts/CenturyGothicBold.ttf', 
            texture='assets/textures/button_menu.jpg',
            model='quad',
            radius=0.18,
            y=-.4, 
            on_click=Func(lambda:
        (destroy(end_panel), show_level_select_menu()))) # Botón para volver al menú de niveles.

# Función para mostrar el menú de selección de nivel.
def show_level_select_menu():
    global current_bg_music, player
    game_hud.disable() # Deshabilita el HUD.
    pistol.disable() # Deshabilita el arma.
    rifle.disable() # Deshabilita el rifle.
    shotgun.disable() # Deshabilita la escopeta.

    crosshair.disable() # Deshabilita la mira.
    if player:
        player.disable() # Deshabilita el controlador de primera persona

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
    global current_bg_music, player
    level_select_menu.disable() # Deshabilita el menú de selección.
    game_hud.disable() # Deshabilita el HUD del juego.
    pistol.disable() # Deshabilita la pistola.
    rifle.disable() # Deshabilita el rifle.
    shotgun.disable() # Deshabilita la escopeta.
    crosshair.disable() # Deshabilita la mira.
    pause_menu.disable() # Asegúrate de que el menú de pausa esté deshabilitado
    if player:
        player.disable() # Deshabilita el controlador de primera persona

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
    global current_bg_music, player
    pause_menu.disable() # Deshabilita el menú de pausa.
    mouse.locked = True # Bloquea el cursor del ratón.
    application.resume() # Reanuda la lógica del juego de Ursina.
    if player:
        player.enable() # Habilita el controlador de primera persona

    # Reanuda la música de fondo si estaba sonando (continuará desde donde se pausó).
    if current_bg_music:
        current_bg_music.play()

# Función para pausar el juego
def pause_game():
    global current_bg_music, player
    if game_active: # Solo pausar si el juego está activo
        application.pause() # Pausa la lógica del juego de Ursina
        mouse.locked = False # Desbloquea el cursor para interactuar con el menú
        pause_menu.enable() # Habilita el menú de pausa
        if player:
            player.disable() # Deshabilita el controlador de primera persona

        # Pausa la música de fondo si está sonando
        if current_bg_music:
            current_bg_music.pause()

# --- Funciones de Eventos de Ursina ---
def input(key): # Función que se llama automáticamente cuando se presiona una tecla o botón del ratón.
    global shots_fired, last_shot_time
    if key == 'left mouse down' and game_active: # Si se hace clic izquierdo y el juego está activo.
        current_time = time.time()
        # Control de cadencia de fuego según el arma activa
        fire_rate = 0.5 # Default para pistola
        if current_level == 2: # Rifle
            fire_rate = 0.2
        elif current_level == 3: # Escopeta
            fire_rate = 0.8 # Más lento por el "poder"

        if (current_time - last_shot_time) > fire_rate:
            gunshot_sound.play() # Reproduce el sonido de disparo.
            shots_fired += 1 # Incrementa el contador de disparos.
            update_hud() # Actualiza el HUD.
            last_shot_time = current_time # Actualiza el tiempo del último disparo.

            # Realiza un raycast desde la posición del ratón.
            # El raycast detecta si hay una entidad en la dirección del disparo.
            if mouse.hovered_entity and isinstance(mouse.hovered_entity, TargetSphere):
                mouse.hovered_entity.hit() # Si el raycast golpea un objetivo, llama a su método 'hit'.

    if key == 'escape': # Si se presiona la tecla ESC.
        if game_active:
            if pause_menu.enabled:
                resume_game()
            else:
                pause_game()
        else:
            # Si no está en juego activo (ej. en menús), ir al menú principal
            if level_select_menu.enabled:
                show_main_menu()
            elif main_menu.enabled:
                application.quit() # Si está en el menú principal, salir de la aplicación

def update(): # Función que se llama automáticamente cada fotograma.
    if game_active:
        # Aquí puedes añadir lógica de juego que se actualice constantemente
        # Por ejemplo, mover la cámara ligeramente, efectos visuales, etc.
        pass # Por ahora, no hay lógica de actualización continua en el juego activo.

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
gunshot_sound = Audio('assets/sounds/gunshot.mp3', loop=False, autoplay=False, volume=0.3) # Asegúrate de tener este archivo
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)


#-------////////// INTERFAS DEL JUEGO//////////--------
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
back_wall = Entity(# Crea una nueva entidad (un objeto en la escena) y la asigna a la variable 'back_wall'.
    model='cube', # Define la forma de la entidad. En este caso, es un cubo.
    scale=(40, 30, 1), # Ancho: 40 unidades, Alto: 30, Profundidad: 1.
    position=(0, 15, 30), # Ubicación central: X=0, Y=15 (centro de la pared, para que la base esté en y=0), Z=30.
    texture='assets/textures/mapa4.png', # Textura aplicada a la pared.
    color=color.white, # Cambiado a blanco para que la textura se vea sin tintes de color.
    collider='box' # Asigna un colisionador de tipo caja para interacciones físicas.
)

# Pared izquierda del escenario.
left_wall = Entity(
    model='cube',
    scale=(2, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 60 (cubre el rango Z).
    position=(-20, 15, 7.5), # Posición X ajustada a -20 (izquierda), Y=15 para que la base esté en y=0.
    texture='assets/textures/mapa4.png', # Textura aplicada a la pared izquierda.
    color=color.white, # Asegura que la textura se vea
    collider='box'
)

# Pared derecha del escenario.
right_wall = Entity(
    model='cube',
    scale=(2, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 60.
    position=(20, 15, 7.5), # Posición X ajustada a 20 (derecha), Y=15 para que la base esté en y=0.
    texture='assets/textures/mapa4.png', # Textura aplicada a la pared derecha.
    color=color.white, # Asegura que la textura se vea
    collider='box'
)

# Techo del escenario.
ceiling = Entity(
    model='cube',
    scale=(42, 1, 45), # ANCHO AJUSTADO: Ahora es 42 para cubrir el espacio de 40 de la pared trasera y un poco más.
    position=(0, 30, 7.5), # Posición X=0 (centrado), Y=30 (altura del techo, encima de las paredes), Z=7.5 (posición Z central).
    texture='assets/textures/cielo.jpg', # Textura del cielo (asumiendo que 'cieloo.png' es la versión oscura).
    color=color.white, # Asegura que la textura se vea
    collider='box'
)

# Suelo (con textura de césped oscuro)
ground_plane = Entity(
    model='plane', # Un plano es una superficie plana.
    scale=(150, 1, 150), # Un tamaño muy grande para asegurar que siempre haya suelo
    position=(0, 0, 5), # ¡CAMBIADO! Posición Y ahora en 0, que es la base del mundo.
    texture='assets/textures/cesped.png', # Cambiado a una textura de cesped oscuro.
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
# camera.position = (0, 0, -15) # Esta línea se reemplaza por la creación del FirstPersonController
camera.fov = 80 # Campo de visión de la cámara.

# --- Arma y Mira (DISEÑOS MEJORADOS y CORREGIDOS) ---
# Asegúrate que todas estas texturas existan en 'assets/textures/'
# y sean archivos .png con transparencia si lo deseas.

# Pistola mejorada
# La entidad 'pistol' ahora solo actúa como un contenedor para sus partes (modelos más pequeños que la componen).
pistol = Entity(parent=None, position=(0.4, -0.45, 1.2), rotation=(0, 0, 0)) # Parent se asignará en start_level
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
rifle = Entity(parent=None, position=(0.6, -0.55, 1.8), rotation=(0,0,0)) # Parent se asignará en start_level
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
shotgun = Entity(parent=None, position=(0.5, -0.65, 1.5), rotation=(0,0,0)) # Parent se asignará en start_level
Entity(parent=shotgun, model='cube', scale=(0.18, 0.15, 1.0), texture='assets/textures/shotgun_body.png', color=color.black) # Cuerpo principal de la escopeta.
Entity(parent=shotgun, model='cylinder', scale=(0.08, 0.08, 0.8), position=(0, 0, 0.5), rotation_x=90, texture='assets/textures/shotgun_barrel.png', color=color.white) # Cañón de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.12, 0.1, 0.25), position=(0, -0.05, 0.2), texture='assets/textures/shotgun_forend.png', color=color.white) # Guardamanos/Bomba de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.18, 0.3, 0.15), position=(0, -0.2, -0.4), texture='assets/textures/shotgun_grip_stock.png', color=color.white) # Culata y empuñadura de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.18, 0.05, 0.3), position=(0, 0.1, -0.1), texture='assets/textures/shotgun_receiver.png', color=color.yellow) # Recámara o parte superior del cuerpo de la escopeta.
Entity(parent=shotgun, model='cylinder', scale=(0.05, 0.05, 0.7), position=(0, -0.08, 0.3), rotation_x=90, texture='assets/textures/shotgun_magtube.png', color=color.white) # Cargador tubular bajo el cañón de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.02, 0.03, 0.05), position=(0, 0.08, 0.45), texture='assets/textures/shotgun_sight_front.png', color=color.red) # Alza y mira delantera de la escopeta.
Entity(parent=shotgun, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.08, -0.2), texture='assets/textures/shotgun_sight_rear.png', color=color.yellow) # Alza y mira trasera de la escopeta.
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
position=(-.45, .45), # Pequeño margen dentro del fondo del HUD.
scale=1.2 # Tamaño del texto.
)

# --- Menú Principal ---
# El logo ahora se escala para ocupar toda la pantalla y se centra.

fondo_blanco = Entity( 
    parent=camera.ui, 
    model='quad', 
    color=color.white, 
    scale=(window.aspect_ratio * 1.1, 1.1), # ligeramente más grande que el logo 
    position=(0, 0, 0), 
    z=0.0, # asegúrate de que esté detrás del logo 
    enabled=True 
)

main_menu = Entity(
    parent=camera.ui, # Es hijo de la UI de la cámara para que siempre se vea en pantalla.
    model='quad', # Es un plano 2D.
    texture='assets/textures/logo3.png', # Asegúrate que esta textura exista
    scale=(window.aspect_ratio * 1, 1), # Escala para cubrir la pantalla completa. Puedes ajustar 1.4 si ves bordes.
    position=(0,0, 0), # Centrado en la pantalla
    enabled=True, # Habilitado por defecto al iniciar el juego.
    z=-0.1, # Un valor Z ligeramente superior para asegurar que esté delante de otros elementos.
    color=color.white # Color blanco para mostrar la textura sin tintes.
)

#------/////////// BOTONES DEL JUEGO ////////////---------
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
    radius=0.18, # Radio para bordes redondeados.
    texture='assets/textures/button_start.jpg', # Usa una textura personalizada si tienes una
    on_click=go_to_level_select, # Acción al hacer clic, va al menú de selección de nivel.
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
    radius=0.18, # Radio para bordes redondeados.
    texture='assets/textures/button_quit.jpg', # Usa una textura personalizada si tienes una
    on_click=application.quit, # Acción al hacer clic, cierra la aplicación.
    z=-0.1 # Un valor Z ligeramente superior para asegurar que esté delante de otros elementos.
    # tooltip eliminado
)


# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False) # Entidad para el menú de selección de nivel, deshabilitada por defecto.
level_title = Text(
    parent=level_select_menu, 
    text="Seleccionar Nivel", 
    scale=4, 
    origin=(0,0), 
    y=0.3, 
    color=color.white,
    font='assets/fonts/keetano_katana.ttf'
    ) # Título del menú.

level_1_button = Button( #Boton para el Nivel 1.
    parent=level_select_menu, 
    text="Nivel 1", # Texto del botón.
    scale=(0.35, 0.12), # Escala del botón.
    y=0.13, # Posición Y del botón (arriba).
    color=color.azure, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.lime, # Color al presionar el botón.
    text_color=color.white,  # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.18, 
    texture='assets/textures/button_level1.jpg', # Usa una textura personalizada si tienes una
    on_click=lambda: start_level(1) # Acción al hacer clic, inicia el nivel 1.
)

level_2_button = Button(# Botón para el Nivel 2.
    parent=level_select_menu,
    text="Nivel 2", # Texto del botón.
    scale=(0.35, 0.12), # Escala del botón.
    y=-0.01, # Posición Y del botón (casi al centro).
    color=color.azure, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.lime, # Color al presionar el botón.
    text_color=color.white, # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.18, # Radio para bordes redondeados.
    texture='assets/textures/button_level2.jpg', # Usa una textura personalizada si tienes una
    on_click=lambda: start_level(2) # Acción al hacer clic, inicia el nivel 2.
)

level_3_button = Button( # Botón para el Nivel 3.
    parent=level_select_menu,
    text="Nivel 3", # Texto del botón.
    scale=(0.35, 0.12), # Escala del botón.
    y=-0.15, # Cambiado para que aparezca debajo del botón 2
    color=color.azure, # Color del botón.
    highlight_color=color.cyan, # Color al pasar el ratón por encima.
    pressed_color=color.lime, # Color al presionar el botón.
    text_color=color.white, # Color del texto del botón.
    model='quad', # Modelo del botón, un plano 2D.
    radius=0.18, # Radio para bordes redondeados.
    texture='assets/textures/button_level3.jpg', # Usa una textura personalizada si tienes una
    on_click=lambda: start_level(3) # Acción al hacer clic, inicia el nivel 3.
)

# Lista de botones de nivel para facilitar la actualización de su estado.
level_buttons = [level_1_button, level_2_button, level_3_button]

# Botón para volver al menú principal desde la selección de nivel
back_to_main_menu_button = Button(
    parent=level_select_menu,
    text="Volver al Menú Principal",
    scale=(0.35, 0.12),
    y=-0.35, # Posición debajo de los botones de nivel
    color=color.red,
    highlight_color=color.cyan,
    pressed_color=color.orange,
    text_color=color.white,
    model='quad',
    radius=0.18,
    texture='assets/textures/button_menu.jpg',
    on_click=show_main_menu
)
#-----/////////////---
# --- Menú de Pausa ---
pause_menu = Entity(parent=camera.ui, enabled=False) # Entidad para el menú de pausa, deshabilitada por defecto.
pause_background = Entity(parent=pause_menu, model='quad', scale=(.6, .6), color=color.white, z=1) # Fondo semitransparente.
pause_text = Text(
    parent=pause_menu, 
    text="PAUSA", 
    scale=4, 
    origin=(0,0), 
    y=0.2, 
    z=-0.1, 
    color=color.black,
    font='assets/fonts/keetano_katana.ttf'
    ) # Título de pausa.

resume_button = Button(
    parent=pause_menu,
    text="Reanudar",
    scale=(0.3, 0.1),
    y=0,
    radius=0.18,
    color=color.azure,
    highlight_color=color.cyan,
    pressed_color=color.lime,
    texture='assets/textures/button_reanudar.jpg',
    on_click=resume_game
)

quit_to_main_button = Button(
    parent=pause_menu,
    text="Salir al Menú Principal",
    scale=(0.3, 0.1),
    y=-0.15,
    radius=0.18,
    color=color.red,
    highlight_color=color.orange,
    pressed_color=color.yellow,
    texture='assets/textures/button_menu.jpg',
    on_click=show_main_menu
)

# Iniciar el juego mostrando el menú principal al principio
show_main_menu()

# --- Ejecutar la Aplicación Ursina ---
app.run() # Inicia el bucle principal de Ursina.
