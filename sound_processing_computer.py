import alsaaudio
import audioop
import math

# Set the audio parameters
device = 'default'
sample_rate = 44100  # 44.1 kHz

# Open the audio input stream
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device, channels=1, rate=sample_rate, format=alsaaudio.PCM_FORMAT_S16_LE, periodsize=1024)


# Main loop to continuously print audio levels
try:
    while True:
        # Read audio data from the microphone
        _, data = inp.read()

        # Calculate the peak audio level in decibels
        peak_amplitude = audioop.max(data, 2)

        # Convert amplitude to decibels
        decibels = 20 * math.log10(peak_amplitude)  # Assuming 16-bit audio
        print(f"Decibels: {decibels:.2f} dB")

except KeyboardInterrupt:
    print("Stopping the script.")
