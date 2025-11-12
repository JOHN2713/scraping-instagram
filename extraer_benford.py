"""
Extractor de Instagram con Análisis de Ley de Benford para detectar bots
La Ley de Benford dice que en datos naturales, el primer dígito sigue una distribución específica.
Los bots suelen generar números que no siguen esta distribución natural.
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
import os
import math
from collections import Counter
from datetime import datetime

# Configuración
DEBUG_FOLDER = "debug_screenshots"
if not os.path.exists(DEBUG_FOLDER):
    os.makedirs(DEBUG_FOLDER)

def setup_driver():
    """Configura el navegador Chrome"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def login_instagram(driver, username, password):
    """Inicia sesión en Instagram"""
    print("🔐 Iniciando sesión en Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    try:
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")
        
        username_input.send_keys(username)
        time.sleep(1)
        password_input.send_keys(password)
        time.sleep(1)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        print("⏳ Esperando confirmación de login...")
        time.sleep(8)
        
        # Manejar popups
        try:
            not_now = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ahora no') or contains(text(), 'Not now')]"))
            )
            not_now.click()
            time.sleep(2)
        except:
            pass
        
        try:
            not_now = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ahora no') or contains(text(), 'Not now')]"))
            )
            not_now.click()
            time.sleep(2)
        except:
            pass
        
        print("✓ Login exitoso")
        return True
        
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return False

def extract_number_from_text(text):
    """Extrae número de un texto como '46 Me gusta' o '1,234 likes'"""
    try:
        # Limpiar y extraer solo dígitos
        numbers = ''.join(filter(str.isdigit, text.replace(',', '').replace('.', '')))
        if numbers and len(numbers) < 10:  # Evitar IDs muy largos
            return int(numbers)
    except:
        pass
    return 0

def extract_likes_robust(driver):
    """Extracción robusta de likes usando múltiples métodos"""
    likes = 0
    
    try:
        # Método 1: Buscar en todas las secciones
        sections = driver.find_elements(By.TAG_NAME, "section")
        for section in sections:
            text = section.text.lower()
            if 'gusta' in text or 'like' in text:
                lines = text.split('\n')
                for line in lines:
                    if 'gusta' in line.lower() or 'like' in line.lower():
                        num = extract_number_from_text(line)
                        if num > 0:
                            likes = num
                            break
            if likes > 0:
                break
        
        # Método 2: Buscar en spans con texto específico
        if likes == 0:
            all_spans = driver.find_elements(By.TAG_NAME, "span")
            for span in all_spans:
                text = span.text.strip()
                if text and ('gusta' in text.lower() or 'like' in text.lower()):
                    num = extract_number_from_text(text)
                    if num > 0:
                        likes = num
                        break
        
        # Método 3: Buscar en enlaces (botón de liked_by)
        if likes == 0:
            try:
                like_link = driver.find_element(By.CSS_SELECTOR, "a[href*='liked_by']")
                text = like_link.find_element(By.TAG_NAME, "span").text
                num = extract_number_from_text(text)
                if num > 0:
                    likes = num
            except:
                pass
                
    except Exception as e:
        print(f"  ⚠ Error extrayendo likes: {e}")
    
    return likes

def extract_comments_robust(driver):
    """Extracción robusta de comentarios"""
    comments = 0
    
    try:
        # Buscar texto con "comentarios" o "comments"
        all_text_elements = driver.find_elements(By.TAG_NAME, "span")
        for element in all_text_elements:
            text = element.text.strip()
            if text and ('comentario' in text.lower() or 'comment' in text.lower()):
                num = extract_number_from_text(text)
                if num > 0 and num != comments:  # Evitar duplicados
                    comments = num
                    break
        
        # Método alternativo: contar elementos de comentarios visibles
        if comments == 0:
            try:
                comment_elements = driver.find_elements(By.CSS_SELECTOR, "ul li[role='menuitem']")
                if len(comment_elements) > 0:
                    comments = len(comment_elements)
            except:
                pass
                
    except Exception as e:
        print(f"  ⚠ Error extrayendo comentarios: {e}")
    
    return comments

def extract_profile_data(driver, profile_username, max_posts=50):
    """Extrae datos del perfil para análisis de Benford"""
    print(f"\n📊 Extrayendo datos de @{profile_username}...")
    
    driver.get(f"https://www.instagram.com/{profile_username}/")
    time.sleep(5)
    
    posts_data = []
    
    try:
        # Scroll para cargar posts
        print("🔍 Cargando posts del perfil...")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Encontrar enlaces de posts
        post_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        post_urls = list(set([link.get_attribute('href') for link in post_links]))[:max_posts]
        
        print(f"✓ Encontrados {len(post_urls)} posts para analizar\n")
        
        # Extraer datos de cada post
        for idx, post_url in enumerate(post_urls, 1):
            print(f"📸 Post {idx}/{len(post_urls)}: {post_url}")
            
            try:
                driver.get(post_url)
                time.sleep(4)
                
                shortcode = post_url.split('/p/')[1].rstrip('/')
                
                # Fecha
                try:
                    date_element = driver.find_element(By.CSS_SELECTOR, "time[datetime]")
                    date_str = date_element.get_attribute("datetime")
                except:
                    date_str = datetime.now().isoformat()
                
                # Likes
                likes = extract_likes_robust(driver)
                
                # Comentarios
                comments = extract_comments_robust(driver)
                
                # Video?
                try:
                    driver.find_element(By.CSS_SELECTOR, "video")
                    is_video = True
                except:
                    is_video = False
                
                # Caption
                caption_length = 0
                try:
                    h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                    for h1 in h1_elements:
                        text = h1.text.strip()
                        if len(text) > caption_length:
                            caption_length = len(text)
                except:
                    pass
                
                # Guardar datos
                post_data = {
                    "post_number": idx,
                    "shortcode": shortcode,
                    "date_utc": date_str,
                    "likes": likes,
                    "comments": comments,
                    "is_video": is_video,
                    "caption_length": caption_length,
                    "url": post_url
                }
                
                posts_data.append(post_data)
                
                print(f"  ✅ Likes: {likes}, Comentarios: {comments}, Video: {is_video}\n")
                
                # Debug si no hay likes
                if likes == 0:
                    screenshot_path = os.path.join(DEBUG_FOLDER, f"post_{idx}_debug.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"  ⚠ Screenshot guardado: {screenshot_path}\n")
                
                time.sleep(3)
                
            except Exception as e:
                print(f"  ⚠ Error: {e}\n")
                continue
        
        return posts_data
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return posts_data

def get_first_digit(number):
    """Obtiene el primer dígito de un número"""
    if number == 0:
        return None
    return int(str(abs(number))[0])

def benford_expected_distribution():
    """Retorna la distribución esperada según la Ley de Benford"""
    return {i: math.log10(1 + 1/i) for i in range(1, 10)}

def analyze_benford(data, field_name):
    """Analiza un campo de datos según la Ley de Benford"""
    print(f"\n📊 Analizando campo '{field_name}' con Ley de Benford...")
    
    # Extraer primeros dígitos
    first_digits = []
    for item in data:
        value = item.get(field_name, 0)
        digit = get_first_digit(value)
        if digit is not None:
            first_digits.append(digit)
    
    if not first_digits:
        print(f"  ⚠ No hay datos suficientes para '{field_name}'")
        return None
    
    # Contar frecuencias
    digit_counts = Counter(first_digits)
    total = len(first_digits)
    
    # Calcular distribución observada
    observed_dist = {i: digit_counts.get(i, 0) / total for i in range(1, 10)}
    
    # Distribución esperada (Benford)
    expected_dist = benford_expected_distribution()
    
    # Calcular Chi-cuadrado para medir desviación
    chi_squared = 0
    for digit in range(1, 10):
        expected_count = expected_dist[digit] * total
        observed_count = digit_counts.get(digit, 0)
        if expected_count > 0:
            chi_squared += ((observed_count - expected_count) ** 2) / expected_count
    
    # Calcular desviación promedio
    avg_deviation = sum(abs(observed_dist[i] - expected_dist[i]) for i in range(1, 10)) / 9
    
    return {
        "field": field_name,
        "total_samples": total,
        "observed_distribution": observed_dist,
        "expected_distribution": expected_dist,
        "chi_squared": chi_squared,
        "avg_deviation": avg_deviation,
        "digit_counts": dict(digit_counts)
    }

def generate_benford_report(posts_data, profile_name):
    """Genera reporte completo con análisis de Benford"""
    print("\n" + "="*70)
    print("📊 ANÁLISIS DE LEY DE BENFORD - DETECCIÓN DE BOTS")
    print("="*70)
    
    # Analizar likes
    likes_analysis = analyze_benford(posts_data, "likes")
    
    # Analizar comentarios
    comments_analysis = analyze_benford(posts_data, "comments")
    
    # Guardar datos raw
    raw_filename = f"{profile_name}_datos_raw.csv"
    with open(raw_filename, "w", newline="", encoding="utf-8") as f:
        if posts_data:
            writer = csv.DictWriter(f, fieldnames=posts_data[0].keys())
            writer.writeheader()
            writer.writerows(posts_data)
    print(f"\n✓ Datos raw guardados: {raw_filename}")
    
    # Guardar análisis de Benford
    benford_filename = f"{profile_name}_analisis_benford.csv"
    with open(benford_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Campo", "Dígito", "Frecuencia Observada (%)", "Frecuencia Esperada (%)", "Desviación (%)"])
        
        for analysis in [likes_analysis, comments_analysis]:
            if analysis:
                writer.writerow([])  # Línea vacía
                writer.writerow([f"=== {analysis['field'].upper()} ==="])
                writer.writerow([f"Total de muestras: {analysis['total_samples']}"])
                writer.writerow([f"Chi-cuadrado: {analysis['chi_squared']:.4f}"])
                writer.writerow([f"Desviación promedio: {analysis['avg_deviation']:.4f}"])
                writer.writerow([])
                
                for digit in range(1, 10):
                    obs = analysis['observed_distribution'][digit] * 100
                    exp = analysis['expected_distribution'][digit] * 100
                    dev = abs(obs - exp)
                    writer.writerow([analysis['field'], digit, f"{obs:.2f}", f"{exp:.2f}", f"{dev:.2f}"])
    
    print(f"✓ Análisis de Benford guardado: {benford_filename}")
    
    # Determinar si es posible bot
    print("\n" + "="*70)
    print("🤖 EVALUACIÓN: ¿Es esta cuenta un BOT?")
    print("="*70)
    
    bot_score = 0
    max_score = 0
    reasons = []
    
    # Criterio 1: Desviación de la Ley de Benford en likes
    if likes_analysis and likes_analysis['total_samples'] >= 5:
        max_score += 40
        deviation = likes_analysis['avg_deviation']
        if deviation > 0.15:  # Desviación alta
            bot_score += 40
            reasons.append(f"❌ LIKES: Desviación alta de Benford ({deviation:.2%}). Distribución no natural.")
        elif deviation > 0.10:
            bot_score += 20
            reasons.append(f"⚠️  LIKES: Desviación moderada de Benford ({deviation:.2%}). Sospechoso.")
        else:
            reasons.append(f"✅ LIKES: Distribución natural de Benford ({deviation:.2%}).")
    
    # Criterio 2: Desviación de la Ley de Benford en comentarios
    if comments_analysis and comments_analysis['total_samples'] >= 5:
        max_score += 30
        deviation = comments_analysis['avg_deviation']
        if deviation > 0.15:
            bot_score += 30
            reasons.append(f"❌ COMENTARIOS: Desviación alta de Benford ({deviation:.2%}). Distribución no natural.")
        elif deviation > 0.10:
            bot_score += 15
            reasons.append(f"⚠️  COMENTARIOS: Desviación moderada ({deviation:.2%}). Sospechoso.")
        else:
            reasons.append(f"✅ COMENTARIOS: Distribución natural de Benford ({deviation:.2%}).")
    
    # Criterio 3: Patrones sospechosos en engagement
    if posts_data:
        max_score += 30
        likes_list = [p['likes'] for p in posts_data if p['likes'] > 0]
        
        if likes_list:
            # Todos los posts con likes muy similares
            avg_likes = sum(likes_list) / len(likes_list)
            variance = sum((x - avg_likes) ** 2 for x in likes_list) / len(likes_list)
            std_dev = variance ** 0.5
            coefficient_variation = (std_dev / avg_likes) if avg_likes > 0 else 0
            
            if coefficient_variation < 0.15:  # Muy poca variación
                bot_score += 30
                reasons.append(f"❌ ENGAGEMENT: Likes muy uniformes (CV={coefficient_variation:.2f}). Comportamiento de bot.")
            elif coefficient_variation < 0.25:
                bot_score += 15
                reasons.append(f"⚠️  ENGAGEMENT: Variación baja en likes (CV={coefficient_variation:.2f}). Sospechoso.")
            else:
                reasons.append(f"✅ ENGAGEMENT: Variación natural en likes (CV={coefficient_variation:.2f}).")
    
    # Resultado final
    print()
    for reason in reasons:
        print(reason)
    
    print("\n" + "-"*70)
    if max_score > 0:
        percentage = (bot_score / max_score) * 100
        print(f"📊 PUNTUACIÓN DE BOT: {bot_score}/{max_score} ({percentage:.1f}%)")
        
        if percentage >= 70:
            conclusion = "🚨 ALTA PROBABILIDAD DE BOT"
            color = "ROJO"
        elif percentage >= 40:
            conclusion = "⚠️  ACTIVIDAD SOSPECHOSA"
            color = "AMARILLO"
        else:
            conclusion = "✅ CUENTA PROBABLEMENTE REAL"
            color = "VERDE"
        
        print(f"🎯 CONCLUSIÓN: {conclusion}")
    else:
        print("⚠️  No hay suficientes datos para determinar")
        percentage = 0
        conclusion = "DATOS INSUFICIENTES"
        color = "GRIS"
    
    print("="*70)
    
    # Guardar conclusión
    conclusion_filename = f"{profile_name}_conclusion.csv"
    with open(conclusion_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Análisis de Detección de Bot - Instagram"])
        writer.writerow(["Perfil", profile_name])
        writer.writerow(["Fecha de análisis", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Total de posts analizados", len(posts_data)])
        writer.writerow([])
        writer.writerow(["Puntuación de bot", f"{bot_score}/{max_score}"])
        writer.writerow(["Porcentaje", f"{percentage:.1f}%"])
        writer.writerow(["Conclusión", conclusion])
        writer.writerow(["Nivel de alerta", color])
        writer.writerow([])
        writer.writerow(["Razones:"])
        for reason in reasons:
            writer.writerow([reason])
    
    print(f"\n✓ Conclusión guardada: {conclusion_filename}")

def main():
    """Función principal"""
    # CONFIGURACIÓN
    INSTAGRAM_USERNAME = "iamjohnyv13"
    INSTAGRAM_PASSWORD = "Diana2809"  # ⚠️ Cambia esto
    PROFILE_TO_ANALYZE = "jofre_a21"
    MAX_POSTS = 50  # Cuántos posts analizar
    
    if INSTAGRAM_PASSWORD == "TU_CONTRASEÑA_AQUI":
        print("❌ ERROR: Configura tu contraseña en la línea 407")
        return
    
    driver = None
    
    try:
        print("="*70)
        print("🤖 DETECTOR DE BOTS DE INSTAGRAM - LEY DE BENFORD")
        print("="*70)
        print(f"Perfil a analizar: @{PROFILE_TO_ANALYZE}")
        print(f"Posts máximos: {MAX_POSTS}")
        print("="*70)
        
        # Iniciar navegador
        print("\n🌐 Iniciando navegador Chrome...")
        driver = setup_driver()
        
        # Login
        if not login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
            print("❌ No se pudo iniciar sesión")
            return
        
        # Extraer datos
        posts_data = extract_profile_data(driver, PROFILE_TO_ANALYZE, MAX_POSTS)
        
        if not posts_data:
            print("❌ No se extrajeron datos")
            return
        
        # Analizar con Benford
        generate_benford_report(posts_data, PROFILE_TO_ANALYZE)
        
        print("\n✅ ¡Análisis completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\n🔒 Cerrando navegador...")
            time.sleep(2)
            driver.quit()

if __name__ == "__main__":
    main()
