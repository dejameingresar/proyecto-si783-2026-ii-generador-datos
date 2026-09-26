"""nucleo.generadores — catálogo de datos de ejemplo del dominio EPSIS Salud.

Sin dependencias externas: los valores se construyen con `random` y `datetime`
a partir de los catálogos declarados aquí. Cada generador tiene la firma
`f(rng, campo) -> valor` y es determinista dada la semilla.

Los catálogos tienen que ser más grandes que los volúmenes por defecto del
esquema: una columna UNIQUE alimentada por un catálogo finito no puede superar
el número de elementos de ese catálogo.
"""

import datetime as dt
import random
import re

# ------------------------------------------------------------------ personas
NOMBRES_M = [
    "Luis", "Carlos", "Jose", "Juan", "Miguel", "Angel", "Jorge", "Marco", "Fernando",
    "Rodrigo", "Diego", "Cesar", "Christian", "Ricardo", "Sergio", "Andres", "Gustavo",
    "Eduardo", "Raul", "Renzo", "Aldo", "Piero", "Kevin", "Oscar", "Martin", "Daniel",
    "Gabriel", "Leonardo", "Salvador", "Gonzalo", "Hector", "Ivan", "Jaime", "Wilson",
    "Yordy", "Romulo", "Efrain", "Aurelio", "Wilfredo", "Renso", "Yomar", "Apolo",
]
NOMBRES_F = [
    "Maria", "Ana", "Rosa", "Elena", "Katherine", "Nicole", "Claudia", "Cecilia",
    "Milagros", "Yolanda", "Andrea", "Pamela", "Gabriela", "Sofia", "Daniela", "Fernanda",
    "Karina", "Lourdes", "Judy", "Jazmin", "Silvia", "Mercedes", "Martha", "Yeni", "Ruth",
    "Adriana", "Patricia", "Veronica", "Marisol", "Debora", "Karem", "Mileny",
    "Sandy", "Luzmila", "Perla", "Ariana", "Lesly", "Kenia", "Rocio",
]
TODOS_NOMBRES = NOMBRES_M + NOMBRES_F
APELLIDOS = [
    "Rodriguez", "Cardenas", "Quispe", "Mamani", "Ccahuana", "Condori", "Flores", "Chavez",
    "Rojas", "Torres", "Vargas", "Ramos", "Garcia", "Apaza", "Huaman", "Cuti", "Alarcon",
    "Medina", "Ayala", "Rios", "Velasquez", "Arenas", "Paredes", "Choque", "Zeballos",
    "Pinto", "Benavides", "Tapia", "Huisa", "Challco", "Cutipa", "Zevallos", "Gutierrez",
    "Justiniano", "Coila", "Yujra", "Cahuari", "Chipana", "Morales", "Bernal", "Zambrano",
    "Ramirez", "Loayza", "Borda", "Diaz", "Salas", "Huaylla", "Soncco", "Yaipata",
]
DISTRITOS = [
    "Tacna", "Pata", "Tarata", "Ilabaya", "Caplina", "Palca", "Saman", "Echarati",
    "Locumba", "Querecotillo", "Putina", "Chochane", "Alca", "Cumbaza",
]
CALLES = [
    "Av. Bolognesi", "Jr. San Martin", "Av. 28 de Julio", "Jr. Miguel Grau", "Av. Leguia",
    "Jr. La Marina", "Av. Coronel Mercado", "Jr. Zela", "Jr. Reycende", "Jr. Loreto",
    "Av. Almirante Grau", "Jr. San Agustin", "Av. Iberia", "Jr. Powell", "Av. La Paz",
]
CORREOS_DOMINIO = ["epsis-salud.pe", "clinicasanfrancisco.pe", "saludvital.pe", "gmail.com"]

# --------------------------------------------------------------- clinica
# (nombre, descripcion) — 12 especialidades: el volumen por defecto son 8 filas.
ESPECIALIDADES = [
    ("Cardiologia", "Atencion del sistema cardiovascular yEnumeracion de factores de riesgo"),
    ("Pediatria", "Salud integral del niño y del adolescente"),
    ("Traumatologia", "Lesiones de huesos, articulaciones y tejidos blandos"),
    ("Ginecologia", "Salud de la mujer y control prenatal"),
    ("Oftalmologia", "Diagnostico y tratamiento de la vision"),
    ("Dermatologia", "Enfermedades de la piel, cabello y unas"),
    ("Neumologia", "Enfermedades del sistema respiratorio"),
    ("Gastroenterologia", "Enfermedades del aparato digestivo"),
    ("Endocrinologia", "Hormonas, tiroides y diabetes"),
    ("Nefrologia", "Enfermedades del rinon"),
    ("Psiquiatria", "Salud mental y trastornos conductuales"),
    ("Medicina General", "Atencion integral del paciente en primer nivel"),
]

# (nombre, categoria, presentacion, precio) — 36 medicamentos para volumen 30.
MEDICAMENTOS = [
    ("Paracetamol", "ANALGESICO", "tableta 500 mg", 12.50),
    ("Ibuprofeno", "ANTIINFLAMATORIO", "tableta 400 mg", 18.00),
    ("Amoxicilina", "ANTIBIOTICO", "capsula 500 mg", 34.90),
    ("Azitromicina", "ANTIBIOTICO", "tableta 500 mg", 56.00),
    ("Omeprazol", "ANTIACIDO", "capsula 20 mg", 27.40),
    ("Losartan", "ANTIHIPERTENSIVO", "tableta 50 mg", 31.20),
    ("Atorvastatina", "HIPOLIPEMIANTE", "tableta 20 mg", 48.60),
    ("Metformina", "ANTIDIABETICO", "tableta 850 mg", 22.10),
    ("Salbutamol", "BRONQUIODILATADOR", "inhalador 200 dosis", 39.90),
    ("Cetirizina", "ANTIHISTAMINICO", "tableta 10 mg", 15.70),
    ("Dexametasona", "CORTICOIDE", "tableta 4 mg", 24.30),
    ("Enalaprilo", "ANTIHIPERTENSIVO", "tableta 10 mg", 19.80),
    ("Loratadina", "ANTIHISTAMINICO", "jarabe 60 ml", 21.00),
    ("Ambroxol", "EXPECTORANTE", "jarabe 100 ml", 26.40),
    ("Ciprofloxacino", "ANTIBIOTICO", "tableta 500 mg", 38.70),
    ("Claritromicina", "ANTIBIOTICO", "tableta 500 mg", 47.20),
    ("Ranitidina", "ANTIACIDO", "tableta 150 mg", 16.40),
    ("Prednisona", "CORTICOIDE", "tableta 20 mg", 29.90),
    ("Furosemida", "DIURETICO", "tableta 40 mg", 17.60),
    ("Hidroclorotiazida", "DIURETICO", "tableta 25 mg", 14.30),
    ("Simvastatina", "HIPOLIPEMIANTE", "tableta 20 mg", 35.20),
    ("Amlodipino", "ANTIHIPERTENSIVO", "tableta 5 mg", 23.80),
    ("Metoprolol", "ANTIHIPERTENSIVO", "tableta 100 mg", 41.50),
    ("Insulina Glargine", "ANTIDIABETICO", "inyectable 100 UI/ml", 128.00),
    ("Glibenclamida", "ANTIDIABETICO", "tableta 5 mg", 18.90),
    ("Levotiroxina", "HORMONAL", "tableta 75 mcg", 33.10),
    ("Alendronato", "BLOQUEADOR_OSEO", "tableta 70 mg", 52.80),
    ("Colchicina", "ANTIGOTA", "tableta 0.5 mg", 25.40),
    ("Naproxeno", "ANTIINFLAMATORIO", "tableta 250 mg", 20.60),
    ("Diclofenaco", "ANTIINFLAMATORIO", "gel topico 1%", 28.30),
    ("Lorazepam", "ANSIOLITICO", "tableta 1 mg", 30.90),
    ("Sertralina", "ANTIDEPRESIVO", "tableta 50 mg", 45.20),
    ("Albuterol", "BRONQUIODILATADOR", "inhalador 180 dosis", 37.60),
    ("Beclometasona", "CORTICOIDE_INHALADO", "inhalador 200 dosis", 96.40),
    ("Loperamida", "ANTIDIARREICO", "capsula 2 mg", 13.70),
    ("Ondansetron", "ANTIEMETICO", "tableta 8 mg", 36.10),
]

DOSIS = [
    "1 capsula cada 8 horas",
    "1 tableta cada 12 horas",
    "5 ml cada 6 horas",
    "aplicar 2 veces al dia",
    "1 capsula cada 24 horas",
    "1 comprimido al acostarse",
    "1 tableta por la manana",
    "2 veces al dia con alimentos",
]
TIPOS_CONSULTA = [
    "Consulta general",
    "Control de enfermedad cronica",
    "Evaluacion inicial",
    "Revision de resultados",
    "Consulta de control",
    "Atencion de urgencia",
]
DIAGNOSTICOS = [
    "Hipertension arterial",
    "Diabetes mellitus tipo 2",
    "Infeccion respiratoria superior",
    "Lumbago",
    "Gastritis cronica",
    "Dermatitis alergica",
    "Cefalea tensional",
    "Conjuntivitis",
    "Asma bronquial",
    "Ulcera peptica",
    "Anemia ferropenica",
    "Fractura de radio distal",
    "Catarata senil",
    "Gota",
    "Obesidad grado I",
    "Rinitis alérgica",
    "Bronquitis aguda",
    "Artritis osteoarticular",
]
OBSERVACIONES = [
    "Control en 30 dias",
    "Se indica radiografia de control",
    "Se solicita analisis de laboratorio",
    "Dieta hiposodica",
    "Reposo relativo por 3 dias",
    "Se entrega informe medico",
    "Continua tratamiento vigente",
    "Se deriva a especialista",
    "Se adjunta receta medica",
    "Se explica uso correto del medicamento",
]


# ------------------------------------------------------------------ utilidades
def fecha_aleatoria(rng, ini, fin):
    dias = (fin - ini).days
    return ini + dt.timedelta(days=rng.randint(0, dias))


# ---------------------------------------------------------------- generadores
def _nombre_completo(rng, _campo):
    return f"{rng.choice(TODOS_NOMBRES)} {rng.choice(TODOS_NOMBRES)}"


def _apellidos(rng, _campo):
    return f"{rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"


def _dni(rng, _campo):
    """DNI peruano real: RENIEC registra 8 digitos, sin digito verificador impreso.

    Fuentes: el digito verificador del DNI no aparece en el documento; se calcula
    bajo demanda con el algoritmo modulo 11 (factores 3,2,7,6,5,4,3,2) que exige
    consultar un servicio externo. Por eso el generador produce 8 digitos, que es
    lo que se persiste en el padron, y no un digito inventado.
    """
    return f"{rng.randint(10_000_000, 99_999_999)}"


def _email(rng, campo):
    usuario = f"{rng.choice(TODOS_NOMBRES).lower()}.{rng.choice(APELLIDOS).lower()}"
    return f"{usuario}{rng.randint(1, 9999)}@{rng.choice(CORREOS_DOMINIO)}"


# Sin tildes ni signos que rompan un correo. El nombre y el apellido de la fila se
# convierten a una direccion plausible en vez de sortearla aparte.
_ASCII = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def _parte_texto(texto, quitar_nombres_compuestos=True):
    limpio = str(texto).translate(_ASCII)
    limpio = "".join(c for c in limpio if c.isalnum() or c == " ")
    limpio = " ".join(limpio.split())
    if quitar_nombres_compuestos:
        # "Luis Carlos Rodriguez" -> solo la ultima palabra es el apellido.
        palabras = limpio.split()
        if len(palabras) > 1:
            limpio = palabras[-1]
    return limpio.lower() or "usuario"


def email_de_fila(fila, rng):
    """Correo coherente con el nombre y el apellido de la propia fila.

    Sin esto el generador produce "Ana Cesar Yola Cahuari" con un correo de otra
    persona: el dato existe pero es incoherente consigo mismo.
    """
    nombres = fila.get("nombres") or ""
    apellidos = fila.get("apellidos") or ""
    base = f"{_parte_texto(nombres, quitar_nombres_compuestos=False)}." \
           f"{_parte_texto(apellidos)}"
    base = re.sub(r"[^a-z0-9.]", "", base)[:40]
    return f"{base}{rng.randint(1, 999)}@{rng.choice(CORREOS_DOMINIO)}"


def _telefono(rng, _campo):
    return f"+51 9{rng.randint(10_000_000, 99_999_999)}"


def _nacimiento(rng, _campo):
    return fecha_aleatoria(rng, dt.date(1935, 1, 1), dt.date(2010, 12, 31))


def _fecha_registro(rng, _campo):
    return fecha_aleatoria(rng, dt.date(2015, 1, 1), dt.date(2026, 7, 31))


def _fecha_ingreso(rng, _campo):
    return fecha_aleatoria(rng, dt.date(2012, 1, 1), dt.date(2026, 7, 31))


def _hora(rng, _campo):
    h = rng.choice([8, 8, 9, 9, 10, 10, 11, 12, 15, 16, 17, 18])
    return f"{h:02d}:{rng.choice(['00', '30'])}"


def _precio(rng, _campo):
    return round(rng.uniform(35.0, 180.0), 2)


def _salario(rng, _campo):
    return round(rng.uniform(2800.0, 6500.0), 2)


def _codigo(rng, campo):
    prefijo = campo.get("prefijo", "COD")
    return f"{prefijo}-{rng.randint(10000, 99999)}"


def _direccion(rng, _campo):
    return f"{rng.choice(CALLES)} {rng.randint(100, 1999)}, {rng.choice(DISTRITOS)}"


def _especialidad_nombre(rng, _campo):
    return rng.choice(ESPECIALIDADES)[0]


def _especialidad_descripcion(rng, _campo):
    return rng.choice(ESPECIALIDADES)[1]


def _medicamento_nombre(rng, _campo):
    return rng.choice(MEDICAMENTOS)[0]


def _medicamento_categoria(rng, _campo):
    return rng.choice(MEDICAMENTOS)[1]


def _medicamento_presentacion(rng, _campo):
    return rng.choice(MEDICAMENTOS)[2]


def _dosis(rng, _campo):
    return rng.choice(DOSIS)


def _tipo_consulta(rng, _campo):
    return rng.choice(TIPOS_CONSULTA)


def _diagnostico(rng, _campo):
    return rng.choice(DIAGNOSTICOS)


def _observacion(rng, _campo):
    return rng.choice(OBSERVACIONES)


def _descripcion(rng, _campo):
    return f"{rng.choice(DIAGNOSTICOS)} - {rng.choice(OBSERVACIONES)}"


def _booleano(rng, _campo):
    return 1 if rng.random() < 0.85 else 0


# Registro de generadores disponibles para el campo "generador" del esquema.
GENERADORES = {
    "nombres": _nombre_completo,
    "apellidos": _apellidos,
    "dni": _dni,
    "email": _email,
    "telefono": _telefono,
    "nacimiento": _nacimiento,
    "fecha_registro": _fecha_registro,
    "fecha_ingreso": _fecha_ingreso,
    "hora": _hora,
    "precio": _precio,
    "salario": _salario,
    "codigo": _codigo,
    "direccion": _direccion,
    "especialidad_nombre": _especialidad_nombre,
    "especialidad_descripcion": _especialidad_descripcion,
    "medicamento_nombre": _medicamento_nombre,
    "medicamento_categoria": _medicamento_categoria,
    "medicamento_presentacion": _medicamento_presentacion,
    "dosis": _dosis,
    "tipo_consulta": _tipo_consulta,
    "diagnostico": _diagnostico,
    "observacion": _observacion,
    "descripcion": _descripcion,
    "booleano": _booleano,
    "stock": lambda rng, c: rng.randint(0, 400),
    "cantidad": lambda rng, c: rng.randint(1, 3),
    "duracion_dias": lambda rng, c: rng.choice([3, 5, 7, 10, 14, 30]),
}
