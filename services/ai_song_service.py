# services/ai_song_service.py
import os
import requests
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, AliasChoices
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
load_dotenv()
# ==========================================
# 1. ESQUEMAS DE PYDANTIC (ESTRUCTURA DE SALIDA)
# ==========================================
class SongPart(BaseModel):
    title: Literal['intro', 'verso 1', 'verso 2', 'verso 3', 'verso 4', 'coro', 'puente', 'solo', 'outro'] = Field(
        description="El bloque o sección musical lírica de la estructura.",
        validation_alias=AliasChoices('title', 'name', 'section', 'type', 'part')
    )
    content: str = Field(description="Texto limpio de los versos de la sección. Usa saltos de línea '\\n'")

    @field_validator('title', mode='before')
    @classmethod
    def to_lowercase(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.lower().strip().replace('verso', 'verso ')
            return " ".join(val.split())
        return v

class GeneratedSongSchema(BaseModel):
    name: str = Field(description="El título oficial de la canción o el más adecuado.")
    parts: List[SongPart] = Field(description="Lista de bloques secuenciales de la canción")


# ==========================================
# 2. CONEXIÓN CON LA API EXTERNA DE VERCEL
# ==========================================
def obtener_cancion_desde_api_externa(query_limpio: str) -> Optional[dict]:
    URL_API_VERCEL = "https://song-api-wheat.vercel.app/songs"
    print(f"[INFO] Consultando API Vercel con '?search={query_limpio}'")
    try:
        response = requests.get(URL_API_VERCEL, params={"search": query_limpio}, timeout=6)
        if response.status_code == 200:
            resultados = response.json()
            if isinstance(resultados, list) and len(resultados) > 0:
                return resultados[0]
        return None
    except Exception as e:
        print(f"[WARN] Error de conexión con la API de Vercel: {e}")
        return None


# ==========================================
# 3. FUNCIÓN PRINCIPAL (PROCESAMIENTO E IA)
# ==========================================
def generar_cancion_ia(prompt_usuario: str) -> dict:
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-120b", 
        temperature=0.0
    )
    
    # ---------------------------------------------------------------------
    # PASO 1: Clasificación de Intención y Sanitización del Prompt
    # ---------------------------------------------------------------------
    class IntentionSchema(BaseModel):
        mode: Literal['BUSCAR', 'PROVEER'] = Field(
            description="BUSCAR si quiere rastrear un título/artista en la API. PROVEER si dicta líricas directamente.",
            validation_alias=AliasChoices('mode', 'modo', 'intent', 'intencion')
        )
        cleaned_query: str = Field(
            description="Si es BUSCAR, extrae EXCLUSIVAMENTE el título/artista para la búsqueda. Si es PROVEER, mantiene las líricas intactas.",
            validation_alias=AliasChoices('cleaned_query', 'texto', 'query', 'cleanedQuery')
        )

    structured_intencion = llm.with_structured_output(IntentionSchema, method="json_mode")
    
    prompt_intencion = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres un clasificador y sanitizador de entradas de texto musicales para la app VibePlanner.\n"
            "Tu objetivo es analizar la solicitud del usuario, decidir su intención y limpiar el texto.\n\n"
            "CRÍTICO: Debes responder única y exclusivamente con un objeto JSON válido que siga el esquema provisto.\n"
            "Mapea tus respuestas usando estrictamente las llaves 'mode' y 'cleaned_query'.\n\n"
            "REGLAS:\n"
            "1. Si el usuario pide buscar una canción, menciona un título o un artista de forma natural, el modo es 'BUSCAR'.\n"
            "2. Si el usuario te escribe directamente los bloques, estrofas o la letra entera, el modo es 'PROVEER'."
        )),
        ("human", "{input}")
    ])
    
    print("[INFO] Analizando intención del usuario...")
    analisis_inicial = (prompt_intencion | structured_intencion).invoke({"input": prompt_usuario})
    
    # ---------------------------------------------------------------------
    # PASO 2: Resolución del Origen de los Datos
    # ---------------------------------------------------------------------
    texto_origen = ""
    titulo_sugerido = ""
    autor_sugerido = "Desconocido"
    genero_sugerido = ""
    
    if analisis_inicial.mode == "BUSCAR":
        datos_api = obtener_cancion_desde_api_externa(analisis_inicial.cleaned_query)
        if datos_api:
            titulo_sugerido = datos_api.get("title") or datos_api.get("name") or datos_api.get("nombre") or analisis_inicial.cleaned_query
            autor_sugerido = datos_api.get("author") or datos_api.get("artista") or datos_api.get("artist") or "Desconocido"
            genero_sugerido = datos_api.get("genre") or datos_api.get("genero") or ""
            texto_origen = datos_api.get("lyrics") or datos_api.get("letra") or datos_api.get("content") or ""
            print(f"[INFO] Éxito: Canción '{titulo_sugerido}' de '{autor_sugerido}' recuperada.")
        else:
            print("[WARN] No se encontraron resultados en la API de Vercel.")
            return {
                "bot_response": f"¡Hola! Estuve buscando la canción '{analisis_inicial.cleaned_query}' en nuestro catálogo, pero no logré encontrarla. ¿Me podrías pasar la letra tú mismo para que la estructure?",
                "song_data": None
            }
    else:
        print("[INFO] Modo PROVEER detectado. Procesando líricas directas.")
        texto_origen = analisis_inicial.cleaned_query
        titulo_sugerido = "Estructura Proveída por Usuario"

    if not texto_origen or len(texto_origen.strip()) == 0:
        return {
            "bot_response": "¡Hola! No pude detectar ninguna letra o texto válido en tu mensaje. ¿Podrías volver a intentarlo?",
            "song_data": None
        }

    # ---------------------------------------------------------------------
    # PASO 3: Formateo Estricto de la Estructura Lírica con Pydantic
    # ---------------------------------------------------------------------
    parser = PydanticOutputParser(pydantic_object=GeneratedSongSchema)
    
    prompt_formateador = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres un formateador de datos JSON ultra-preciso especializado en música.\n"
            "Tu trabajo es tomar el texto de la letra provista, identificar las secciones y estructurar todo en el JSON requerido.\n\n"
            "{instrucciones_formato}"
        )),
        ("human", "Título de referencia: {titulo}\nTexto original de la letra:\n\n{texto_crudo}")
    ])
    
    print("[INFO] Estructurando líricas con IA...")
    try:
        chain_formateadora = prompt_formateador | llm | parser
        resultado_ia = chain_formateadora.invoke({
            "titulo": titulo_sugerido,
            "texto_crudo": texto_origen,
            "instrucciones_formato": parser.get_format_instructions()
        })
        
        # Validación de seguridad para textos sin sentido o vacíos
        if not resultado_ia or not resultado_ia.parts or len(resultado_ia.parts) == 0:
            print("[WARN] La IA no pudo identificar una estructura musical válida.")
            return {
                "bot_response": "¡Ups! Estuve analizando el texto que me pasaste, pero no logré identificar una estructura musical clara (como versos o coros). ¿Podrías revisar la letra y asegurarte de separar bien las estrofas?",
                "song_data": None
            }

    except Exception as e:
        print(f"[ERROR] Fallo en el parseo o invocación de la IA: {e}")
        return {
            "bot_response": "Lo siento, tuve un problema interno al procesar y formatear la estructura de la canción. ¿Podrías intentar enviarla de nuevo?",
            "song_data": None
        }
    
    # ---------------------------------------------------------------------
    # PASO 4: Formato Final Enriquecido con Metadata para el Frontend
    # ---------------------------------------------------------------------
    return {
        "bot_response": f"¡Listo! Encontré y procesé la estructura para **{resultado_ia.name}**. Aquí abajo la tienes organizada para tu setlist.",
        "song_data": {
            "name": resultado_ia.name,
            "author": autor_sugerido,
            "genre": genero_sugerido,
            "structure": {
                "parts": [{"title": part.title, "content": part.content} for part in resultado_ia.parts]
            }
        }
    }



