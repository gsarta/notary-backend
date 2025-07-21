import os
import io
import logging
from pydub import AudioSegment
from openai import OpenAI, APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, openai_api_key: str):
        """
        Inicializa el procesador de audio con la clave API de OpenAI.
        """
        if not openai_api_key:
            logger.error("La clave API de OpenAI no fue proporcionada.")
            raise ValueError("La clave API de OpenAI no puede estar vacía.")
        self.client = OpenAI(api_key=openai_api_key)

    def _split_audio_for_whisper(
        self, audio_file_path: str, segment_duration_ms: int
    ) -> list[io.BytesIO]:
        """
        Divide un archivo de audio en segmentos más pequeños para cumplir con los límites de OpenAI Whisper,
        dividiendo únicamente por duración si el audio es más largo que segment_duration_ms.
        Retorna una lista de objetos BytesIO, cada uno conteniendo un segmento de audio.
        """
        try:
            audio = AudioSegment.from_file(audio_file_path)
        except Exception as e:
            logger.error(f"Error al cargar el archivo de audio {audio_file_path}: {e}")
            raise ValueError(f"No se pudo cargar el archivo de audio: {e}")

        processed_segments = []

        # Si el audio es más largo que la duración máxima del segmento, lo dividimos forzadamente
        if len(audio) > segment_duration_ms:
            for i in range(0, len(audio), segment_duration_ms):
                chunk = audio[i : i + segment_duration_ms]
                buffer = io.BytesIO()
                # Exportar a formato MP3 para OpenAI Whisper.
                chunk.export(buffer, format="mp3")
                buffer.name = (
                    f"segment_{i}.mp3"  # Nombre requerido por la API de OpenAI
                )
                processed_segments.append(buffer)
        else:
            # Si el audio es más corto o igual a la duración máxima del segmento, se procesa como uno solo
            buffer = io.BytesIO()
            audio.export(buffer, format="mp3")
            buffer.name = "full_audio.mp3"  # Nombre para el archivo completo
            processed_segments.append(buffer)

        if not processed_segments and len(audio) == 0:
            raise ValueError(
                "El archivo de audio está vacío o no contiene segmentos válidos."
            )

        return processed_segments

    def transcribe_audio_with_whisper(
        self, audio_file_path: str, segment_duration_ms: int
    ) -> str:
        """
        Envía un archivo de audio (o sus segmentos) a la API de OpenAI Whisper para transcripción.
        Concatena los resultados de la transcripción.
        """
        full_transcription_parts = []

        try:
            audio_segments = self._split_audio_for_whisper(
                audio_file_path, segment_duration_ms
            )
        except ValueError as e:
            logger.error(
                f"Error al procesar segmentos de audio para transcripción: {e}"
            )
            raise

        logger.info(
            f"Transcribiendo {len(audio_segments)} segmentos de audio con Whisper..."
        )
        for i, segment_buffer in enumerate(audio_segments):
            segment_buffer.seek(0)  # Mover el cursor al inicio del buffer antes de leer
            try:
                # La API de Whisper espera un objeto archivo o BytesIO con un atributo 'name'
                transcript_object = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=segment_buffer,
                    response_format="text",  # Solicitar el texto plano
                )
                full_transcription_parts.append(transcript_object)
                logger.info(
                    f"Segmento {i+1}/{len(audio_segments)} transcrito exitosamente."
                )
            except APIError as e:
                logger.error(
                    f"Error de la API de OpenAI al transcribir segmento {i+1}: {e}"
                )
                raise RuntimeError(f"Error de transcripción con OpenAI Whisper: {e}")
            except Exception as e:
                logger.error(
                    f"Ocurrió un error inesperado al transcribir segmento {i+1}: {e}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Error inesperado durante la transcripción del segmento: {e}"
                )

        return " ".join(full_transcription_parts)
