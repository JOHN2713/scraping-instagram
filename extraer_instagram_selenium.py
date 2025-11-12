"""
Extractor de Instagram usando Selenium (método alternativo sin API)
Simula un navegador real para evitar bloqueos de rate limiting
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import json
import os
from datetime import datetime

# Crear carpeta para screenshots de debug
DEBUG_FOLDER = "debug_screenshots"
if not os.path.exists(DEBUG_FOLDER):
    os.makedirs(DEBUG_FOLDER)

def setup_driver():
    """Configura el navegador Chrome con opciones para evitar detección"""
    chrome_options = Options()
    
    # Opciones para evitar detección como bot
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent real
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Opcional: ejecutar en modo headless (sin ventana visible)
    # chrome_options.add_argument('--headless')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # Eliminar la propiedad webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def login_instagram(driver, username, password):
    """Inicia sesión en Instagram"""
    print("🔐 Iniciando sesión en Instagram...")
    
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    try:
        # Esperar y llenar el formulario de login
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")
        
        username_input.send_keys(username)
        time.sleep(1)
        password_input.send_keys(password)
        time.sleep(1)
        
        # Click en botón de login
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        print("⏳ Esperando confirmación de login...")
        time.sleep(8)
        
        # Manejar popup "Guardar información de inicio de sesión"
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ahora no') or contains(text(), 'Not now')]"))
            )
            not_now_button.click()
            time.sleep(2)
        except:
            print("⚠ No apareció popup de guardar login")
        
        # Manejar popup de notificaciones
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ahora no') or contains(text(), 'Not now')]"))
            )
            not_now_button.click()
            time.sleep(2)
        except:
            print("⚠ No apareció popup de notificaciones")
        
        print("✓ Login exitoso")
        return True
        
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return False

def extract_profile_posts(driver, profile_username):
    """Extrae datos de posts de un perfil"""
    print(f"\n📊 Extrayendo posts de @{profile_username}...")
    
    # Ir al perfil
    driver.get(f"https://www.instagram.com/{profile_username}/")
    time.sleep(5)
    
    posts_data = []
    
    try:
        # Obtener todos los enlaces de posts
        print("🔍 Buscando posts en el perfil...")
        
        # Scroll para cargar todos los posts (útil si hay muchos)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):  # Hacer scroll 3 veces
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Encontrar todos los enlaces de posts
        post_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        post_urls = list(set([link.get_attribute('href') for link in post_links]))
        
        print(f"✓ Encontrados {len(post_urls)} posts\n")
        
        # Visitar cada post individualmente
        for idx, post_url in enumerate(post_urls, 1):
            print(f"📸 Extrayendo post {idx}/{len(post_urls)}: {post_url}")
            
            try:
                driver.get(post_url)
                time.sleep(5)  # Esperar a que cargue completamente
                
                # Extraer shortcode de la URL
                shortcode = post_url.split('/p/')[1].rstrip('/')
                
                # Extraer fecha (del atributo datetime)
                try:
                    date_element = driver.find_element(By.CSS_SELECTOR, "time[datetime]")
                    date_str = date_element.get_attribute("datetime")
                except:
                    date_str = datetime.now().isoformat()
                
                # Extraer likes - Múltiples estrategias
                likes = 0
                try:
                    # Estrategia 1: Buscar por texto "Me gusta" o "likes"
                    page_source = driver.page_source
                    
                    # Buscar en secciones específicas con diferentes selectores
                    selectors = [
                        "section > div > span > a > span",  # Contador de likes
                        "a[href*='/liked_by/'] span",
                        "section span[class*='_']",
                        "button span",
                    ]
                    
                    for selector in selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                text = element.text.strip()
                                # Buscar números que indiquen likes
                                if any(word in text.lower() for word in ['gusta', 'like', 'me gusta']):
                                    # Extraer el número
                                    numbers = ''.join(filter(str.isdigit, text.replace(',', '').replace('.', '')))
                                    if numbers:
                                        likes = int(numbers)
                                        break
                            if likes > 0:
                                break
                        except:
                            continue
                    
                    # Estrategia 2: Si no encontró, buscar directamente en el texto visible
                    if likes == 0:
                        try:
                            # Buscar el elemento que contiene "46 Me gusta"
                            all_text = driver.find_elements(By.TAG_NAME, "span")
                            for span in all_text:
                                text = span.text.strip()
                                if 'gusta' in text.lower() or 'like' in text.lower():
                                    numbers = ''.join(filter(str.isdigit, text.replace(',', '').replace('.', '')))
                                    if numbers and len(numbers) < 10:  # Evitar IDs largos
                                        likes = int(numbers)
                                        break
                        except:
                            pass
                    
                    # Si no se encontraron likes, guardar screenshot para debug
                    if likes == 0:
                        screenshot_path = os.path.join(DEBUG_FOLDER, f"post_{shortcode}_nolikes.png")
                        driver.save_screenshot(screenshot_path)
                        print(f"  ⚠ No se encontraron likes - Screenshot guardado: {screenshot_path}")
                        
                        # Intentar imprimir el HTML relevante para debugging
                        try:
                            sections = driver.find_elements(By.TAG_NAME, "section")
                            if len(sections) >= 2:
                                print(f"  🔍 DEBUG: Texto visible en la sección de likes:")
                                section_text = sections[1].text[:200]  # Primeros 200 caracteres
                                print(f"     {section_text}...")
                        except:
                            pass
                    else:
                        print(f"  ✅ Likes encontrados: {likes}")
                    
                except Exception as e:
                    print(f"  ⚠ Error extrayendo likes: {e}")
                    likes = 0
                
                # Extraer comentarios
                try:
                    # Buscar el número de comentarios en el texto
                    all_text = driver.find_elements(By.TAG_NAME, "span")
                    comments = 0
                    for span in all_text:
                        text = span.text.strip()
                        if 'comentario' in text.lower() or 'comment' in text.lower():
                            numbers = ''.join(filter(str.isdigit, text.replace(',', '').replace('.', '')))
                            if numbers and len(numbers) < 10:
                                comments = int(numbers)
                                break
                    print(f"  → Comentarios encontrados: {comments}")
                except Exception as e:
                    print(f"  ⚠ Error extrayendo comentarios: {e}")
                    comments = 0
                
                # Detectar si es video
                try:
                    video_element = driver.find_element(By.CSS_SELECTOR, "video")
                    is_video = True
                except:
                    is_video = False
                
                # Extraer caption
                try:
                    # Múltiples estrategias para el caption
                    caption_text = ""
                    selectors_caption = [
                        "h1",
                        "div[class*='_a9zs'] span",
                        "span[class*='_ap3a']",
                    ]
                    
                    for selector in selectors_caption:
                        try:
                            caption_element = driver.find_element(By.CSS_SELECTOR, selector)
                            caption_text = caption_element.text
                            if len(caption_text) > 10:  # Si encontró texto significativo
                                break
                        except:
                            continue
                    
                    caption_length = len(caption_text)
                    print(f"  → Caption length: {caption_length}")
                except Exception as e:
                    print(f"  ⚠ Error extrayendo caption: {e}")
                    caption_length = 0
                
                # Guardar datos
                post_data = {
                    "shortcode": shortcode,
                    "date_utc": date_str,
                    "likes": likes,
                    "comments": comments,
                    "is_video": is_video,
                    "video_views": None,  # Difícil de extraer con Selenium
                    "caption_length": caption_length,
                    "url": post_url
                }
                
                posts_data.append(post_data)
                print(f"  ✅ RESUMEN: {likes} likes, {comments} comentarios, Video: {is_video}, Caption: {caption_length} caracteres\n")
                
                # Espera aleatoria para simular comportamiento humano
                time.sleep(3)
                
            except Exception as e:
                print(f"  ⚠ Error extrayendo post: {e}")
                continue
        
        return posts_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return posts_data

def save_to_csv(data, filename):
    """Guarda los datos en CSV"""
    if not data:
        print("⚠ No hay datos para guardar")
        return
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n✓ Datos guardados en: {filename}")
    print(f"✓ Total de posts: {len(data)}")

def main():
    """Función principal"""
    # CONFIGURACIÓN
    INSTAGRAM_USERNAME = "iamjohnyv13"  # Tu usuario de Instagram
    INSTAGRAM_PASSWORD = "Diana2809"  # ⚠️ CAMBIA ESTO
    PROFILE_TO_EXTRACT = "nicole.az13"
    
    # Verificar que se configuró la contraseña
    if INSTAGRAM_PASSWORD == "TU_CONTRASEÑA_AQUI":
        print("❌ ERROR: Debes configurar tu contraseña en la línea 226")
        print("   Edita el archivo y cambia INSTAGRAM_PASSWORD por tu contraseña real")
        return
    
    driver = None
    
    try:
        # Configurar navegador
        print("🌐 Iniciando navegador Chrome...")
        driver = setup_driver()
        
        # Login
        if not login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
            print("❌ No se pudo iniciar sesión")
            return
        
        # Extraer posts
        posts = extract_profile_posts(driver, PROFILE_TO_EXTRACT)
        
        # Guardar a CSV
        if posts:
            filename = f"{PROFILE_TO_EXTRACT}_posts_selenium.csv"
            save_to_csv(posts, filename)
        
        print("\n✅ Proceso completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        
    finally:
        if driver:
            print("\n🔒 Cerrando navegador...")
            time.sleep(2)
            driver.quit()

if __name__ == "__main__":
    main()
