from models import Estudiante, CAMPOS_ESTUDIANTE
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido
gestor = GestorJSON("data/estudiantes.json")

CAMPOS_OBLIGATORIOS =("nombre", "apellido", "email", "carnet")
CAMPOS_BUSCABLES =("nombre", "apellido", "email", "carnet")

RANGO_NOTA = (0, 20)

def emails_registrados(excepto_id=None):
    return {
        registro["email"].lower()
        for registro in gestor.leer()
        if registro["id"] != excepto_id
    }


def carnets_registrados(excepto_id=None):
    return {
        registro["carnet"].upper()
        for registro in gestor.leer()
        if registro["id"] != excepto_id
    }

def siguiente_id():
    ids = [registro["id"] for registro in gestor.leer()]
    return max(ids) + 1 if ids else 1

def buscar_posicion(registros, id_estudiante):
    for indice, registro in enumerate(registros):
        if registro["id"] == id_estudiante:
            return indice
    return None


def texto_a_materias(texto):
    return {materia.strip().title()
            for materia in str(texto).split(",")
            if materia.strip()}

def crear_estudiante(datos):
    try:
        valores = {campo: str(datos.get(campo, "")).strip() for campo in CAMPOS_ESTUDIANTE}
        valores["carnet"] = valores["carnet"].upper()

        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if not valores[campo]]
        if faltantes:
            return False, f"Faltan campos obligatorios: {', '.join(faltantes)}"

        if not es_email_valido(valores["email"]):
            return False, f"El email '{valores['email']}' no tiene un formato válido"
        if valores["email"].lower() in emails_registrados():
            return False, "Ese email ya está registrado"
        if valores["carnet"] in carnets_registrados():
            return False, f"El carnet {valores['carnet']} ya está registrado"
        materias = texto_a_materias(datos.get("materias", ""))
        estudiante = Estudiante(siguiente_id(), **valores, materias=materias)

        registros = gestor.leer()
        registros.append(estudiante.a_diccionario())
        if not gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"

        return True, f"Estudiante {estudiante.obtener_nombre_completo()} creado con id {estudiante.id}"

    except Exception as error:
        return False, f"Error inesperado: {error}"

def obtener_todos():
    return [Estudiante.desde_diccionario(registro) for registro in gestor.leer()]

def obtener_por_id(id_estudiante):
    for estudiante in obtener_todos():
        if estudiante.id == id_estudiante:
            return estudiante
    return None

def buscar_estudiantes(termino):
    termino = termino.strip().lower()
    if not termino:
        return []

    encontrados = []
    for registro in gestor.leer():
        for campo in CAMPOS_BUSCABLES:               
            if termino in str(registro.get(campo, "")).lower():
                encontrados.append(Estudiante.desde_diccionario(registro))
                break                                  
    return encontrados

def actualizar_estudiante(id_estudiante, cambios):
    try:
        desconocidos = set(cambios) - set(CAMPOS_ESTUDIANTE)
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        if not cambios:
            return False, "No se indicó ningún cambio"

        registros = gestor.leer()
        posicion = buscar_posicion(registros, id_estudiante)
        if posicion is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        if "email" in cambios:
            if not es_email_valido(cambios["email"]):
                return False, "El email no tiene un formato válido"
            if cambios["email"].lower() in emails_registrados(excepto_id=id_estudiante):
                return False, "Ese email ya lo usa otro estudiante"

        if "carnet" in cambios:
            cambios["carnet"] = cambios["carnet"].strip().upper()
            if cambios["carnet"] in carnets_registrados(excepto_id=id_estudiante):
                return False, f"El carnet {cambios['carnet']} ya lo usa otro estudiante"

        registros[posicion].update(cambios)             
        if not gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"
        return True, f"Estudiante {id_estudiante} actualizado ({len(cambios)} campo/s)"

    except Exception as error:
        return False, f"Error inesperado: {error}"

def eliminar_estudiante(id_estudiante):
    registros = gestor.leer()
    quedan = [registro for registro in registros if registro["id"] != id_estudiante]

    if len(quedan) == len(registros):
        return False, f"No existe un estudiante con id {id_estudiante}"

    if not gestor.guardar(quedan):
        return False, "No se pudo escribir el archivo"
    return True, f"Estudiante {id_estudiante} eliminado"

def agregar_nota(id_estudiante, materia, nota):
    try:
        materia = str(materia).strip().title()
        if not materia:
            return False, "La materia es obligatoria"
        try:
            nota = float(nota)
        except (ValueError, TypeError):
            return False, f"La nota '{nota}' no es un número"

        minimo, maximo = RANGO_NOTA                    
        if not minimo <= nota <= maximo:
            return False, f"La nota debe estar entre {minimo} y {maximo}"
        if nota.is_integer():
            nota = int(nota)                            
        registros = gestor.leer()
        posicion = buscar_posicion(registros, id_estudiante)
        if posicion is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        estudiante = Estudiante.desde_diccionario(registros[posicion])
        estudiante.agregar_nota(materia, nota)
        registros[posicion] = estudiante.a_diccionario()

        if not gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"
        return True, f"Nota {nota} agregada en {materia} a {estudiante.obtener_nombre_completo()}"

    except Exception as error:
        return False, f"Error inesperado: {error}"


def materias_ofertadas():
    todas = set()
    for estudiante in obtener_todos():
        todas |= estudiante.materias
    return todas


def estudiantes_en_comun(id_a, id_b):
    if id_a == id_b:
        return False, "Debe elegir dos estudiantes distintos"

    estudiante_a = obtener_por_id(id_a)
    estudiante_b = obtener_por_id(id_b)
    if not estudiante_a:
        return False, f"No existe un estudiante con id {id_a}"
    if not estudiante_b:
        return False, f"No existe un estudiante con id {id_b}"

    comunes = estudiante_a.materias_en_comun(estudiante_b)   # usa & en el Modelo
    return True, (estudiante_a.obtener_nombre_completo(),
                  estudiante_b.obtener_nombre_completo(),
                  comunes)
def estadisticas():
    estudiantes = obtener_todos()
    sin_notas = [e.obtener_nombre_completo() for e in estudiantes if not e.notas]
    con_notas = [e for e in estudiantes if e.notas]
    mejor = max(con_notas, key=lambda e: e.obtener_promedio()) if con_notas else None

    return {
        "total": len(estudiantes),
        "materias": sorted(materias_ofertadas()),
        "sin_notas": sin_notas,
        "mejor": f"{mejor.obtener_nombre_completo()} ({mejor.obtener_promedio()})" if mejor else "-",
    }