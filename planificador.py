import inrrobot
import voice_recognition
import random
import time
import robot_sockets
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from threading import Thread, currentThread
from deep_translator import GoogleTranslator


class ColorGameStateMachine: 
    def __init__(self):
        """
        Inicializa la máquina de estados del juego de colores
        """
        self.states = {
            "saludar": self.saludar,
            "esperarRespuesta": self.esperarRespuesta,
            "explicarJuego": self.explicarJuego,
            "comenzarJuego": self.comenzarJuego,
            "esperarColor": self.esperarColor,
            "colorOjos": self.colorOjos,
            "colorHablado": self.colorHablado,
            "otroColor": self.otroColor,
            "ningunColor": self.ningunColor,
            "sinRespuesta": self.sinRespuesta,
            "juegoCompletado": self.juegoCompletado,
            "finalizarJuego": self.finalizarJuego,
            "despedirse": self.despedirse,
        }
        self.current_state = "saludar"
        self.attempts = 0
        self.max_attempts = 3
        self.correct_answers = 0
        self.eye_color = ""
        self.spoken_color = ""

    def transition(self, new_state):
        """
        Se cambia el estado actual de la máquina de estados a uno nuevo y se ejecuta la función asociada al nuevo estado
        """
        #while inrrobot.isSpeaking():
        while inrrobot.isExecuting():
            time.sleep(0.2)
        
        print("State: ", self.current_state)
        self.current_state = new_state
        self.states[self.current_state]()
        
    def saludar(self):
        """
        Saluda al paciente al empezar el juego
        """
        inrrobot.wakeUp()
        inrrobot.executeAnimation("intHello", 1)
        inrrobot.say("Hola, ¿qué tal estás?")
        self.transition("esperarRespuesta")
    
    def esperarRespuesta(self):
        """
        Espera la respuesta del paciente al saludo
        """
        inrrobot.startAudioRecording()
        time.sleep(0.5)
        file = robot_sockets.MAIN_PATH + '/robot_recording.ogg'
        inrrobot.startProcessing()
        inrrobot.stopAudioRecording()
        # esperar a que el audio haya terminado de enviarse
        while not robot_sockets.audio_received:
            time.sleep(0.2)
        text = voice_recognition.speech_to_text(file)
        print("Respuesta: ", text)
        response = GoogleTranslator(source='spanish', target='english').translate(text)
        robot_sockets.audio_received = False

        if response:
            # analizar el sentimiento de la respuesta
            sentiment = self.analizarSentimientos(response)
            if sentiment == "positivo":
                inrrobot.say("¡Me alegro!")
            elif sentiment == "negativo":
                inrrobot.say("No te preocupes, estoy aquí para ayudarte.")
            else:
                inrrobot.say("¡Entiendo! Me alegra verte hoy.")
        else:
            inrrobot.say("Estoy seguro de que este juego te va a encantar.")
        self.transition("explicarJuego")

    def explicarJuego(self):
        """
        Explica la dinámica del juego al paciente
        """
        inrrobot.sayAnimated("Hoy vamos a jugar al juego de los colores. Te voy a enseñar un color con los ojos, pero voy a decirte un color diferente. Dime el color que veas en mis ojos.") 
        self.transition("comenzarJuego")

    def comenzarJuego(self):
        """
        Comienza el juego, seleccionando el colores de los LEDs de los ojos y el hablado.
        Termina el juego si el número de intentos supera el máximo
        """
        self.attempts += 1
        if self.attempts <= self.max_attempts:
            if self.attempts > 1:
                inrrobot.say("Probemos otra vez.")
                time.sleep(2)
            self.eye_color = random.choice(colors)
            inrrobot.setLedsColor("FaceLeds", colors_dict[self.eye_color], 1)
            self.spoken_color = random.choice(colors)
            while self.spoken_color == self.eye_color:
                self.spoken_color = random.choice(colors)
            inrrobot.say(self.spoken_color)

            time.sleep(2)
            # cambiar los LEDs a blanco para que el niño no pueda ver el color al responder
            inrrobot.setLedsColor("FaceLeds", "white", 1)

            time.sleep(1)
            if self.attempts < self.max_attempts:
                inrrobot.say("¿Qué color has visto?")
            self.transition("esperarColor")
        else:
            time.sleep(2)
            # se considera que el niño ha completado el juego con éxito si responde correctamente todas las preguntas
            if self.correct_answers == self.max_attempts:
                self.transition("juegoCompletado")
            else:
                self.transition("finalizarJuego")

    def esperarColor(self):
        """
        Espera el color dicho por el paciente
        """
        inrrobot.startAudioRecording()
        time.sleep(0.5)
        file = robot_sockets.MAIN_PATH + '/robot_recording.ogg'
        inrrobot.startProcessing()
        inrrobot.stopAudioRecording()
        while not robot_sockets.audio_received:
            time.sleep(0.2)
        guess = voice_recognition.speech_to_text(file)
        print("Guessed color: ", guess)
        robot_sockets.audio_received = False

        # analizar la respuesta
        if guess:
            if self.eye_color in guess or voice_recognition.calculate_cer(self.eye_color, guess) < 0.3:
                self.transition("colorOjos")
            elif self.spoken_color in guess or voice_recognition.calculate_cer(self.spoken_color, guess) < 0.3:
                self.transition("colorHablado")
            elif [color for color in colors if (color in guess and color != self.eye_color and color != self.spoken_color) or voice_recognition.calculate_cer(color, guess) < 0.3]:
                self.transition("otroColor")
            elif [color for color in colors if (color not in guess and color != self.eye_color and color != self.spoken_color) or voice_recognition.calculate_cer(color, guess) < 0.3]:
                self.transition("ningunColor")
        else:
            self.transition("sinRespuesta")

    def colorOjos(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde correctamente 
        """
        inrrobot.say("¡Muy bien!")
        self.correct_answers += 1
        self.transition("comenzarJuego")
        
    def colorHablado(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde el color que ha dicho el robot
        """
        inrrobot.say("Te he pillado, ese es el color que he dicho, no el color de mis ojos.")
        self.transition("comenzarJuego")

    def otroColor(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde un color que no es el de los ojos ni el dicho por el robot
        """
        inrrobot.say("Ese color no es el color que he dicho ni el color de mis ojos.")
        self.transition("comenzarJuego")

    def ningunColor(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde algo que no es un color
        """
        inrrobot.say("Eso no es un color.")
        self.transition("comenzarJuego")

    def sinRespuesta(self):
        """
        Gestiona la respuesta del NAO cuando el paciente no responde
        """
        inrrobot.say("Perdona, no te he entendido.")
        self.transition("comenzarJuego")

    def juegoCompletado(self):
        """
        Termina el juego porque se ha superado el número de intentos máximo.
        Indica al paciente que ha completado el juego con éxito
        """
        inrrobot.sayAnimated("¡Bien hecho, has completado el juego!")
        self.transition("despedirse")

    def finalizarJuego(self):
        """
        Termina el juego porque se ha superado el número de máximos intentos máximo.
        El juego no se completa con éxito porque el paciente ha cometido fallos
        """
        inrrobot.say("Gracias por jugar al juego de los colores conmigo.")
        self.transition("despedirse")

    def despedirse(self):
        """
        Se despide del paciente al finalizar el juego
        """
        inrrobot.executeAnimation("intHello", 1)
        inrrobot.say("¡Adiós, espero verte pronto!")
        inrrobot.rest()

    def analizarSentimientos(self, response):
        """
        Analiza los sentimientos de la respuesta dada por el paciente haciendo uso de la librería VADER
        """
        # crear un objeto SentimentIntensityAnalyzer
        sentiment_analyzer = SentimentIntensityAnalyzer()

        # obtener el diccionario de sentimientos
        sentiment_dict = sentiment_analyzer.polarity_scores(response)

        # indicar si el sentimiento es positivo, negativo o neutral (CAMBIAR 0.05 Y -0.05)
        if sentiment_dict['compound'] >= 0.05:
            sentiment = "positivo"
        elif sentiment_dict['compound'] <= - 0.05:
            sentiment = "negativo"
        else:
            sentiment = "neutral"

        return sentiment


# connect to the robot
inrrobot.connect()

colors = ["rojo", "azul", "amarillo", "verde", "naranja", "magenta"]
colors_dict = {
        "rojo":"red", 
        "azul":"blue", 
        "amarillo":"yellow", 
        "verde":"green", 
        "naranja":"orange",  
        "magenta":"magenta"
    }

thread_icebox = Thread(target=robot_sockets.connection_robot, args=())
thread_icebox.start()

t_pub_sub_manager = Thread(target=robot_sockets.robot_sockets_manager, name="robot_sockets_manager_thread")
t_pub_sub_manager.start()
for socket_dict in robot_sockets.robot_sockets_list:
    thread_name = socket_dict["name"] + "_listener_thread"
    t_pub_sub = Thread(target=robot_sockets.robot_data_listener, args=([socket_dict]), name=thread_name)
    t_pub_sub.start()


# esperar a que el robot se conecte antes de iniciar el juego
while not robot_sockets.robot_connected:
    time.sleep(0.2)

#inrrobot.startProcessing()

game = ColorGameStateMachine()
game.saludar()

exit_gracefully = True
