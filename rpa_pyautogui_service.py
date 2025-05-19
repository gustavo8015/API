import pyautogui
import subprocess
import time
import os

# Configurar pausa entre acciones de pyautogui para mayor estabilidad
pyautogui.PAUSE = 0.5
# Configuración segura - permite mover el mouse a la esquina para abortar
pyautogui.FAILSAFE = True

def rpa_escribir_en_word(texto, ruta_guardado=None):
    """Automatiza la apertura de Word, escritura de texto y guardado."""
    try:
        # Abrir Microsoft Word en Windows
        subprocess.run("start winword", shell=True)
        time.sleep(5)  # Esperar a que Word se abra completamente

        # Crear un nuevo documento (Ctrl + N en Word en inglés, Ctrl + U en español)
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(2)  # Esperar a que el documento se cree

        # Escribir el texto en el documento
        pyautogui.write(texto, interval=0.05)
        time.sleep(1)

        # Guardar el documento
        pyautogui.hotkey('ctrl', 'g')  # Ctrl+G en español (Guardar)
        time.sleep(1)
        
        # Si se especificó una ruta, escribirla
        if ruta_guardado:
            pyautogui.write(ruta_guardado)
            time.sleep(0.5)
        
        pyautogui.press('enter')
        time.sleep(2)

        # Cerrar Word
        pyautogui.hotkey('alt', 'f4')
        time.sleep(1)
        # Si pregunta por guardar cambios, aceptar
        pyautogui.press('s')  # 'S' para "Sí" en español
        
        print(f"RPA completado: Texto escrito y documento guardado en Word.")
        return True
        
    except Exception as e:
        print(f"Error durante la automatización de Word: {e}")
        return False

def rpa_crear_en_excel(datos, ruta_guardado=None):
    """Automatiza la apertura de Excel, entrada de datos y guardado."""
    try:
        # Abrir Microsoft Excel en Windows
        subprocess.run("start excel", shell=True)
        time.sleep(5)  # Esperar a que Excel se abra completamente

        # Excel suele abrir con una hoja en blanco lista para usar
        
        # Ingresar los datos (formato esperado: lista de listas o filas separadas por newline)
        if isinstance(datos, str):
            # Si es string, dividir por líneas
            filas = datos.strip().split('\n')
            for i, fila in enumerate(filas):
                # Moverse a la primera celda de la fila
                pyautogui.press('home')  # Ir al inicio de la fila
                for j, valor in enumerate(fila.split(',')):
                    # Escribir valor
                    pyautogui.write(valor)
                    # Moverse a la siguiente celda (derecha)
                    pyautogui.press('right')
                # Moverse a la siguiente fila
                if i < len(filas) - 1:  # Si no es la última fila
                    pyautogui.press('down')
        
        time.sleep(1)
        
        # Guardar la hoja de cálculo
        pyautogui.hotkey('ctrl', 'g')  # Ctrl+G en español (Guardar)
        time.sleep(1)
        
        # Si se especificó una ruta, escribirla
        if ruta_guardado:
            pyautogui.write(ruta_guardado)
            time.sleep(0.5)
            
        pyautogui.press('enter')
        time.sleep(2)
        
        # Cerrar Excel
        pyautogui.hotkey('alt', 'f4')
        time.sleep(1)
        # Si pregunta por guardar cambios, aceptar
        pyautogui.press('s')  # 'S' para "Sí" en español
        
        print(f"RPA completado: Datos ingresados y hoja de cálculo guardada en Excel.")
        return True
        
    except Exception as e:
        print(f"Error durante la automatización de Excel: {e}")
        return False

def rpa_crear_en_powerpoint(titulo, contenido, ruta_guardado=None):
    """Automatiza la apertura de PowerPoint, creación de diapositivas y guardado."""
    try:
        # Abrir Microsoft PowerPoint en Windows
        subprocess.run("start powerpnt", shell=True)
        time.sleep(5)  # Esperar a que PowerPoint se abra completamente
        
        # Crear nueva presentación (PowerPoint suele abrir con una diapositiva en blanco)
        
        # Configurar el título de la primera diapositiva
        pyautogui.write(titulo, interval=0.05)
        
        # Moverse al área de contenido (Tab)
        pyautogui.press('tab')
        
        # Escribir el contenido
        pyautogui.write(contenido, interval=0.05)
        
        # Si hay más diapositivas, agregarlas
        # (Esto sería más complejo y dependería del formato específico del contenido)
        
        time.sleep(1)
        
        # Guardar la presentación
        pyautogui.hotkey('ctrl', 'g')  # Ctrl+G en español (Guardar)
        time.sleep(1)
        
        # Si se especificó una ruta, escribirla
        if ruta_guardado:
            pyautogui.write(ruta_guardado)
            time.sleep(0.5)
            
        pyautogui.press('enter')
        time.sleep(2)
        
        # Cerrar PowerPoint
        pyautogui.hotkey('alt', 'f4')
        time.sleep(1)
        # Si pregunta por guardar cambios, aceptar
        pyautogui.press('s')  # 'S' para "Sí" en español
        
        print(f"RPA completado: Presentación creada y guardada en PowerPoint.")
        return True
        
    except Exception as e:
        print(f"Error durante la automatización de PowerPoint: {e}")
        return False

def ejecutar_office_automation(app, accion, texto_contenido, ruta_guardado=None):
    """Función principal para la automatización de Office."""
    
    # Crear directorio si no existe
    if ruta_guardado:
        directorio = os.path.dirname(ruta_guardado)
        if directorio and not os.path.exists(directorio):
            try:
                os.makedirs(directorio)
                print(f"Directorio creado: {directorio}")
            except Exception as e:
                print(f"Error al crear directorio: {str(e)}")
                ruta_guardado = os.path.join(os.path.expanduser('~'), 'Desktop', 
                                           f'documento_rpa_{app}.{"docx" if app=="word" else "xlsx" if app=="excel" else "pptx"}')
                print(f"Usando ruta alternativa: {ruta_guardado}")
    
    # Ejecutar la automatización según la aplicación solicitada
    if app.lower() == 'word':
        return rpa_escribir_en_word(texto_contenido, ruta_guardado)
    elif app.lower() == 'excel':
        return rpa_crear_en_excel(texto_contenido, ruta_guardado)
    elif app.lower() == 'powerpoint':
        # Para PowerPoint, separamos título y contenido si viene con formato
        if '|' in texto_contenido:
            titulo, contenido = texto_contenido.split('|', 1)
        else:
            titulo, contenido = "Título de la Presentación", texto_contenido
        return rpa_crear_en_powerpoint(titulo, contenido, ruta_guardado)
    else:
        print(f"Aplicación no soportada: {app}")
        return False