import pyautogui
import subprocess
import time
import os
import datetime

# Configurar pausa entre acciones de pyautogui para mayor estabilidad
pyautogui.PAUSE = 0.5
# Configuración segura - permite mover el mouse a la esquina para abortar
pyautogui.FAILSAFE = True

def rpa_escribir_en_word(texto, ruta_guardado=None):
    """Automatiza la apertura de Word, escritura de texto y guardado - Versión simplificada."""
    try:
        # Forzar guardado en escritorio con nombre claro
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Generar un nombre predeterminado simple
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"documento_word_{timestamp}.docx"
        
        # Construir la ruta completa en el escritorio
        desktop_file_path = os.path.join(desktop_path, file_name)
        
        print(f"[INICIO] Automatización de Word")
        print(f"Ruta de guardado: {desktop_file_path}")
        
        # Verificar si Word ya está abierto y cerrarlo para evitar conflictos
        try:
            subprocess.run("taskkill /im WINWORD.EXE /f", shell=True)
            time.sleep(2)
            print("Word cerrado previamente")
        except:
            pass
        
        # 1. Abrir Microsoft Word
        print("[PASO 1] Abriendo Microsoft Word...")
        subprocess.run("start winword", shell=True)
        time.sleep(6)  # Esperar más tiempo a que Word se abra completamente
        print("Word abierto")
        
        # 2. Escribir contenido (sin crear documento nuevo)
        print("[PASO 2] Escribiendo contenido...")
        # Word debería abrir con un documento en blanco por defecto
        pyautogui.write(texto, interval=0.05)
        print("Contenido escrito")
        time.sleep(2)
        
        # 3. Guardar como (F12 universal o Alt+A, G, A)
        print("[PASO 3] Guardando documento...")
        
        # Presionar F12 (Guardar Como)
        pyautogui.press('f12')
        time.sleep(3)  # Esperar al diálogo
        
        # 4. Especificar ruta en el diálogo
        # Presionar Tab suficientes veces para asegurar que llegamos al campo de ruta/nombre
        for _ in range(3):
            pyautogui.press('tab')
            time.sleep(0.5)
        
        # Escribir la ruta completa
        pyautogui.write(desktop_file_path)
        time.sleep(2)
        print(f"Ruta escrita: {desktop_file_path}")
        
        # 5. Confirmar guardado
        pyautogui.press('enter')
        time.sleep(4)  # Esperar a que se complete el guardado
        print("Confirmación de guardado")
        
        # 6. Verificar si existe diálogo de formato (a veces aparece)
        # Presionar Enter por si acaso hay algún diálogo
        pyautogui.press('enter')
        time.sleep(2)
        
        # 7. Cerrar Word con taskkill (método más fiable)
        print("[PASO 4] Cerrando Word...")
        subprocess.run("taskkill /im WINWORD.EXE /f", shell=True)
        print("Word cerrado forzadamente")
        
        print(f"[FIN] Documento guardado en: {desktop_file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error durante la automatización de Word: {e}")
        # Intentar cerrar Word forzadamente en caso de error
        try:
            subprocess.run("taskkill /im WINWORD.EXE /f", shell=True)
        except:
            pass
        return False

def rpa_crear_en_excel(texto, ruta_guardado=None):
    try:
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"documento_excel_{timestamp}.xlsx"
        desktop_file_path = os.path.join(desktop_path, file_name)
        
        print(f"[INICIO] Automatización de Excel")
        print(f"Ruta de guardado: {desktop_file_path}")
        
        # Verificar si Excel ya está abierto y cerrarlo para evitar conflictos
        try:
            subprocess.run("taskkill /im EXCEL.EXE /f", shell=True)
            time.sleep(2)
            print("Excel cerrado previamente")
        except:
            pass
        
        # 1. Abrir Microsoft Excel
        print("[PASO 1] Abriendo Microsoft Excel...")
        subprocess.run("start excel", shell=True)
        time.sleep(6)  # Esperar a que Excel se abra completamente
        print("Excel abierto")
        
        # 2. Escribir contenido en la hoja activa
        print("[PASO 2] Escribiendo contenido...")
        pyautogui.write(texto, interval=0.05)
        print("Contenido escrito")
        time.sleep(2)
        
        # 3. Guardar como (F12)
        print("[PASO 3] Guardando documento...")
        pyautogui.press('f12')
        time.sleep(3)  # Esperar al diálogo de guardado
        
        # 4. Escribir la ruta completa (campo ya enfocado)
        pyautogui.write(desktop_file_path)
        time.sleep(2)
        print(f"Ruta escrita: {desktop_file_path}")
        
        # 5. Confirmar guardado
        pyautogui.press('enter')
        time.sleep(4)
        print("Confirmación de guardado")
        
        # 6. Manejar posibles diálogos adicionales
        pyautogui.press('enter')
        time.sleep(2)
        
        # 7. Cerrar Excel
        print("[PASO 4] Cerrando Excel...")
        subprocess.run("taskkill /im EXCEL.EXE /f", shell=True)
        print("Excel cerrado forzadamente")
        
        print(f"[FIN] Documento guardado en: {desktop_file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error durante la automatización de Excel: {e}")
        try:
            subprocess.run("taskkill /im EXCEL.EXE /f", shell=True)
        except:
            pass
        return False

def rpa_crear_en_powerpoint(titulo=None, contenido=None, ruta_guardado=None):
    try:
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"presentacion_powerpoint.pptx"
        desktop_file_path = os.path.join(desktop_path, file_name)
        
        # Texto a insertar
        titulo_especifico = "Es un documento creado automticamente mediante RPA."
        subtitulo_especifico = "La automatizacion robotica de procesos (RPA) permite crear documentos de manera automatica sin intervencin manual."
        
        print(f"[INICIO] Automatización de PowerPoint")
        print(f"Ruta de guardado: {desktop_file_path}")
        
        # Verificar si PowerPoint ya está abierto y cerrarlo
        try:
            subprocess.run("taskkill /im POWERPNT.EXE /f", shell=True)
            time.sleep(2)
            print("PowerPoint cerrado previamente")
        except:
            pass
        
        # 1. Abrir Microsoft PowerPoint
        print("[PASO 1] Abriendo Microsoft PowerPoint...")
        subprocess.run("start powerpnt", shell=True)
        time.sleep(6)
        print("PowerPoint abierto")
        
        # Presionar Esc para asegurarnos de que no hay diálogos abiertos
        pyautogui.press('esc')
        time.sleep(0.5)
        
        # 2. Escribir contenido en la diapositiva
        print("[PASO 2] Escribiendo título...")
        
        # Escribir título
        pyautogui.write(titulo_especifico, interval=0.05)
        time.sleep(1)
        
        # SOLUCIÓN PARA EL SUBTÍTULO
        print("Navegando al subtítulo...")
        
        # Obtener dimensiones de la pantalla
        screen_width, screen_height = pyautogui.size()
        
        # Hacer clic directamente en el área del subtítulo (ajustar estas coordenadas según sea necesario)
        # Estas coordenadas apuntan a un punto más bajo en la diapositiva, donde suele estar el subtítulo
        pyautogui.click(screen_width // 2, (screen_height // 2) + 150)
        time.sleep(1)
        
        # Hacer doble clic para asegurarnos de que el área está seleccionada para edición
        pyautogui.doubleClick()
        time.sleep(1)
        
        # Escribir subtítulo
        print("Escribiendo subtítulo...")
        pyautogui.write(subtitulo_especifico, interval=0.05)
        print("Contenido escrito")
        time.sleep(2)
        
        # 3. Guardar como (F12)
        print("[PASO 3] Guardando presentación...")
        pyautogui.press('f12')
        time.sleep(3)
        
        # 4. Escribir la ruta completa
        pyautogui.write(desktop_file_path)
        time.sleep(2)
        print(f"Nombre de archivo escrito: {file_name}")
        
        # 5. Confirmar guardado
        pyautogui.press('enter')
        time.sleep(4)
        print("Confirmación de guardado")
        
        # 6. Manejar posibles diálogos adicionales
        pyautogui.press('enter')
        time.sleep(2)
        
        # 7. Cerrar PowerPoint
        print("[PASO 4] Cerrando PowerPoint...")
        subprocess.run("taskkill /im POWERPNT.EXE /f", shell=True)
        print("PowerPoint cerrado forzadamente")
        
        print(f"[FIN] Presentación guardada en: {desktop_path}\\{file_name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error durante la automatización de PowerPoint: {e}")
        try:
            subprocess.run("taskkill /im POWERPNT.EXE /f", shell=True)
        except:
            pass
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