#import inrrobot
import voice_recognition
import random
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
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
        #while inrrobot.isExecuting():
            #time.sleep(0.2)
        
        print("State: ", self.current_state)
        self.current_state = new_state
        self.states[self.current_state]()
        
    def saludar(self):
        """
        Saluda al paciente al empezar el juego
        """
        print("Hola, ¿qué tal estás?")
        #inrrobot.executeAnimation("intHello", 1)
        #inrrobot.say("Hola, ¿qué tal estás?")
        self.transition("esperarRespuesta")
    
    def esperarRespuesta(self):
        """
        Espera la respuesta del paciente al saludo
        """
        response = GoogleTranslator(source='spanish', target='english').translate(input())
        print(response)
        #file = "" # TODO: get file from recording
        #response = voice_recon.speech_to_text(file)
        if response:
            # analizar el sentimiento de la respuesta
            sentiment = self.analizarSentimientos(response)
            if sentiment == "positivo":
                print("¡Me alegro!")
                #inrrobot.say("¡Me alegro!")
            elif sentiment == "negativo":
                print("No te preocupes, estoy aquí para ayudarte.")
                #inrrobot.say("No te preocupes, estoy aquí para ayudarte.")
            else:
                print("¡Entiendo! Me alegra verte hoy.")
                #inrrobot.say("¡Entiendo! Me alegra verte hoy.")
        else:
            print("Estoy seguro de que este juego te va a encantar.")
            #inrrobot.say("Estoy seguro de que este juego te va a encantar.")
        self.transition("explicarJuego")

    def explicarJuego(self):
        """
        Explica la dinámica del juego al paciente
        """
        print("Hoy vamos a jugar al juego de los colores\nTe voy a enseñar un color con los ojos, pero voy a decirte un color diferente\nTienes que decirme el color que veas en mis ojos")
        #inrrobot.sayAnimated("Hoy vamos a jugar al juego de los colores. Te voy a enseñar un color con los ojos, pero voy a decirte un color diferente. Tienes que decirme el color que veas en mis ojos.")
        self.transition("comenzarJuego")

    def comenzarJuego(self):
        """
        Comienza el juego, seleccionando el colores de los LEDs de los ojos y el hablado.
        Termina el juego si el número de intentos supera el máximo
        """
        self.attempts += 1
        if self.attempts <= self.max_attempts:
            if self.attempts > 1:
                print("Probemos otra vez")
                #inrrobot.say("Probemos otra vez")
                time.sleep(2)
            self.eye_color = random.choice(colors)
            #inrrobot.setLedsColor("FaceLeds", colors_dic[self.eye_color], 1)
            print("Color ojos: ", self.eye_color)
            self.spoken_color = random.choice(colors)
            while self.spoken_color == self.eye_color:
                self.spoken_color = random.choice(colors)
            #inrrobot.say(self.spoken_color)
            print("Color hablado: ", self.spoken_color)

            time.sleep(2)
            # cambiar los LEDs a blanco para que el niño no pueda ver el color al responder
            #inrrobot.setLedsColor("FaceLeds", "white", 1)

            time.sleep(1)
            if self.attempts < self.max_attempts:
                print("¿Qué color has visto?")
                #inrrobot.say("¿Qué color has visto?")
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
        guess = input()
        #file = "" # TODO: get file from recording
        #guess = voice_recon.speech_to_text(file)

        """print("CER ojos:", voice_recon.calculate_cer(guess, self.eye_color))
        print("CER hablado:", voice_recon.calculate_cer(guess, self.spoken_color))
        for color in colors:
            print(f"CER color {color}:", voice_recon.calculate_cer(guess, color))"""

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
        print("¡Muy bien!")
        #inrrobot.say("¡Muy bien!")
        self.correct_answers += 1
        self.transition("comenzarJuego")
        
    def colorHablado(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde el color que ha dicho el robot
        """
        print("Te he pillado, ese es el color que he dicho, no el color de mis ojos")
        #inrrobot.say("Te he pillado, ese es el color que he dicho, no el color de mis ojos")
        self.transition("comenzarJuego")

    def otroColor(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde un color que no es el de los ojos ni el dicho por el robot
        """
        print("Ese color no es el color que he dicho ni el color de mis ojos")
        #inrrobot.say("Ese color no es el color que he dicho ni el color de mis ojos")
        self.transition("comenzarJuego")

    def ningunColor(self):
        """
        Gestiona la respuesta del NAO cuando el paciente responde algo que no es un color
        """
        print("Eso no es un color")
        #inrrobot.say("Eso no es un color")
        self.transition("comenzarJuego")

    def sinRespuesta(self):
        """
        Gestiona la respuesta del NAO cuando el paciente no responde
        """
        print("Perdona, no te he entendido")
        #inrrobot.say("Perdona, no te he entendido")
        self.transition("comenzarJuego")

    def juegoCompletado(self):
        """
        Termina el juego porque se ha superado el número de intentos máximo.
        Indica al paciente que ha completado el juego con éxito
        """
        print("¡Bien hecho, has completado el juego!")
        #inrrobot.sayAnimated("¡Bien hecho, has completado el juego!")
        self.transition("despedirse")

    def finalizarJuego(self):
        """
        Termina el juego porque se ha superado el número de máximos intentos máximo.
        El juego no se completa con éxito porque el paciente ha cometido fallos
        """
        print("Gracias por jugar al juego de los colores conmigo")
        #inrrobot.say("Gracias por jugar al juego de los colores conmigo")
        self.transition("despedirse")

    def despedirse(self):
        """
        Se despide del paciente al finalizar el juego
        """
        print("¡Adiós, espero verte pronto!")
        #inrrobot.executeAnimation("intHello", 1)
        #inrrobot.say("¡Adiós, espero verte pronto!")

    def analizarSentimientos(self, response):
        """
        Analiza los sentimientos de la respuesta dada por el paciente haciendo uso de la librería VADER
        """
        # crear un objeto SentimentIntensityAnalyzer
        sentiment_analyzer = SentimentIntensityAnalyzer()

        # obtener el diccionario de sentimientos
        sentiment_dict = sentiment_analyzer.polarity_scores(response)

        # indicar si el sentimiento es positivo, negativo o neutral
        if sentiment_dict['compound'] >= 0.05:
            sentiment = "positivo"
        elif sentiment_dict['compound'] <= - 0.05:
            sentiment = "negativo"
        else:
            sentiment = "neutral"

        return sentiment


# connect to the robot
#inrrobot.connect()

colors = ["rojo", "azul", "amarillo", "verde", "naranja", "magenta"]
colors_dic = {
        "rojo":"red", 
        "azul":"blue", 
        "amarillo":"yellow", 
        "verde":"green", 
        "naranja":"orange",  
        "magenta":"magenta"
    }

game = ColorGameStateMachine()
game.saludar()

