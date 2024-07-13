"""
Sistema de Reconocimiento de Voz en una Plataforma de Robótica Social Asistencial
"""
import speech_recognition as sr
from pathlib import Path
import numpy as np
import csv
from bert_score import BERTScorer 
from torchmetrics.text import CharErrorRate


# recognizer instance
rec = sr.Recognizer()

# BERT scorer instance
scorer = BERTScorer(model_type='bert-base-uncased')

# CharErrorRate instance
cer_object = CharErrorRate()

def speech_to_text(file):
    """
    Function to convert the voice that has been recognized to text
    """
    try:
        audio_file = sr.AudioFile(file)
        with audio_file as source:
            audio = rec.record(source) # -----memoria-----> if no duration is specified, the audio source will be recorded until no more audio input is recognized
        
        text = rec.recognize_whisper(audio, language="spanish") # FUNCIONA
        #text = rec.recognize_bing(voice, language="es-ES")
        # ------------------------------------
        # TRY MORE APIs AND RESEARCH THEM
        # ------------------------------------
    except sr.UnknownValueError:
        text = ""
        print("Perdón, no te he entendido") # el NAO debería decir esto
    except sr.RequestError as e:
        text = ""
        print("Error; " + e)

    return text.lower()

def calculate_wer(reference, hypothesis):
    """
    Function to calculate the Word Error Rate (WER) between two strings
    """
    # split the reference and hypothesis sentences into words
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    # initialize a matrix with size |ref_words|+1 x |hyp_words|+1
    mat = np.zeros((len(ref_words) + 1, len(hyp_words) + 1))
    # the number of operations for an empty hypothesis to become the reference
    # is the number of words in the reference (i.e., deleting all words)
    for i in range(len(ref_words) + 1):
        mat[i, 0] = i
    # the number of operations for an empty reference to become the hypothesis
    # is the number of words in the hypothesis (i.e., inserting all words)
    for j in range(len(hyp_words) + 1):
        mat[0, j] = j
    # iterate over the words in the reference and hypothesis
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            # if the words are the same, we take the previous minimum number of operations
            if ref_words[i - 1] == hyp_words[j - 1]:
                mat[i, j] = mat[i - 1, j - 1]
            else:
                # if the words are different, take the minimum of substitution, insertion and deletion
                substitution = mat[i - 1, j - 1] + 1
                insertion = mat[i, j - 1] + 1
                deletion = mat[i - 1, j] + 1
                mat[i, j] = min(substitution, insertion, deletion)
    # the minimum number of operations to transform the hypothesis into the reference is in the bottom-right cell of the matrix
    # we divide this by the number of words in the reference to get the WER
    wer = float(mat[len(ref_words), len(hyp_words)] / len(ref_words))

    return round(wer, 3)

def calculate_bert_score(reference, hypothesis):
    # get precision, recall, and F1 scores
    p, r, f1 = scorer.score([reference], [hypothesis])

    return round(f1.item(), 3)

def calculate_cer(reference, hypothesis):
    # calculate the character error rate
    cer = cer_object([reference], [hypothesis])

    return round(cer.item(), 3)

def get_file_transcript(transcripts, file):
    """
    Function to get the transcript of the given file from a list of transcripts
    """
    for row in transcripts:
        filename, transcript = row
        if Path(filename).stem == file.stem:
            return transcript.lower()
    return ""

def main():
    # specify the path to the wav files
    path = Path('audio_openslr_small')

    # variable to store the mean total WER
    mean_wer = 0
    # variable to store the mean total F1 BERTScore
    mean_bert_f1 = 0
    count = 0

    # read csv file with the original transcriptions of each audio file
    with open('transcripts_openslr.csv', encoding='utf-8-sig') as csv_file:
        transcripts = list(csv.reader(csv_file, delimiter=','))

    # iterate the folder and obtain the transcription of each wav file
    for file in Path.glob(path, '*'):
        if file.is_file() and file.suffix == ".wav":
            count += 1
            print("File number " +count)
        
            # Speech-to-text translation
            text = speech_to_text(str(file))
            print("La transcripción del archivo " + file.stem + ".wav es:\n" + text)

            # Obtaining the original transcription of the audio file
            original_text = get_file_transcript(transcripts, file)
            print("La transcripción original es:\n" + original_text)

            # WER evaluation of the transcription
            wer = calculate_wer(original_text, text)
            bertscore = calculate_bert_score(original_text, text)
            mean_wer += wer
            mean_bert_f1 += bertscore

            print("Word Error Rate (WER): " +wer)
            print("BERTScore: " +bertscore)

            # Writing the wer into a csv file
            with open('wer.csv', 'a') as wer_csv:
                wer_writer = csv.writer(wer_csv, delimiter=',')
                wer_writer.writerow([file.stem, text, original_text, wer])

            # Writing the f1 bertscore into a csv file
            with open('bertscore.csv', 'a') as bert_csv:
                wer_writer = csv.writer(bert_csv, delimiter=',')
                wer_writer.writerow([file.stem, text, original_text, bertscore])

            if wer > 1:
                with open('badfiles.txt', 'a') as badfiles:
                    badfiles.write("" + file.stem + "\n")

    
    # print mean total WER
    print("The mean WER is: " + mean_wer/count)

    # print mean total F1 measure of the BERTScore
    print("The mean F1 measure of the BERTScore is: " + mean_bert_f1/count)

    # ----------- CREAR UN ARCHIVO Y AÑADIR LOS AUDIOFILES QUE TENGAN UN WER SUPERIOR A 1 (O 0.7??) -----------

    # ESOS ARCHIVOS SE PUEDE ELIMINAR DE LA BASE DE DATOS Y CONSIDERARLO COMO "PREPROCESADO DE DATOS"


if __name__ == "__main__":
    #main()

    preds = "mahenta"
    target = "magenta"
    cer = calculate_cer(preds, target)
    print(cer)
