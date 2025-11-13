"""
Análisis de Seguidores con Ley de Benford
Extrae los seguidores de un perfil y analiza la distribución de sus números de seguidores
según la Ley de Benford para detectar comportamientos artificiales o bots.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para guardar gráficos sin mostrar ventanas

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
        
        print("✓ Login exitoso\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return False

def extract_number_from_text(text):
    """Extrae número de un texto como '1,234' o '1.2K' o '1M'"""
    try:
        text = text.strip().upper()
        
        # Si tiene K (miles)
        if 'K' in text:
            num_str = text.replace('K', '').replace(',', '.').strip()
            return int(float(num_str) * 1000)
        
        # Si tiene M (millones)
        if 'M' in text:
            num_str = text.replace('M', '').replace(',', '.').strip()
            return int(float(num_str) * 1000000)
        
        # Número normal
        numbers = ''.join(filter(str.isdigit, text.replace(',', '').replace('.', '')))
        if numbers:
            return int(numbers)
    except:
        pass
    return 0

def get_profile_followers_count(driver, profile_username):
    """Obtiene el número de seguidores del perfil principal"""
    print(f"📊 Obteniendo información de @{profile_username}...")
    
    driver.get(f"https://www.instagram.com/{profile_username}/")
    time.sleep(4)
    
    try:
        # Buscar el elemento que contiene "seguidores" o "followers"
        page_text = driver.page_source
        
        # Estrategia 1: Buscar en los enlaces del header
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute('href')
            if href and 'followers' in href:
                # El texto del span dentro del enlace tiene el número
                spans = link.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    text = span.get_attribute('title') or span.text
                    if text:
                        num = extract_number_from_text(text)
                        if num > 0:
                            print(f"✓ Seguidores del perfil: {num:,}\n")
                            return num
        
        # Estrategia 2: Buscar en todos los spans
        all_spans = driver.find_elements(By.TAG_NAME, "span")
        for span in all_spans:
            text = span.get_attribute('title') or span.text
            if text and ('seguidor' in text.lower() or any(char.isdigit() for char in text)):
                num = extract_number_from_text(text)
                if num > 10:  # Filtrar números muy pequeños
                    print(f"✓ Seguidores del perfil: {num:,}\n")
                    return num
                    
    except Exception as e:
        print(f"⚠ Error obteniendo seguidores del perfil: {e}")
    
    return 0

def get_follower_count_from_profile(driver, username):
    """Visita el perfil de un usuario y obtiene su número de seguidores.

    Esta versión usa esperas explícitas y varias estrategias:
    - Busca en el header: normalmente hay un <ul><li> con posts/followers/following
    - Busca enlaces con '/followers' y toma el span (title o text)
    - Busca atributos aria-label o title que puedan contener el número
    - Como fallback, busca cualquier span con dígitos significativos
    """
    try:
        driver.get(f"https://www.instagram.com/{username}/")
        # esperar a que cargue el header del perfil
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        except:
            time.sleep(2)

        # Estrategia 1: buscar en el header -> ul > li
        try:
            header = driver.find_element(By.TAG_NAME, 'header')
            li_items = header.find_elements(By.CSS_SELECTOR, 'ul li')
            for li in li_items:
                try:
                    # si el li contiene enlace a followers
                    a = li.find_element(By.TAG_NAME, 'a')
                    href = a.get_attribute('href') or ''
                    if 'followers' in href:
                        # el número puede estar en un span dentro del enlace
                        try:
                            span = a.find_element(By.TAG_NAME, 'span')
                            text = span.get_attribute('title') or span.text
                            num = extract_number_from_text(text)
                            if num > 0:
                                return num
                        except:
                            # intentar en el li mismo
                            text = li.text
                            num = extract_number_from_text(text)
                            if num > 0:
                                return num
                except:
                    # continuar con siguiente li
                    continue
        except:
            pass

        # Estrategia 2: buscar enlace directo a '/followers' usando XPath
        try:
            el = driver.find_element(By.XPATH, "//a[contains(@href, '/followers')]")
            try:
                span = el.find_element(By.TAG_NAME, 'span')
                text = span.get_attribute('title') or span.text
                num = extract_number_from_text(text)
                if num > 0:
                    return num
            except:
                text = el.text
                num = extract_number_from_text(text)
                if num > 0:
                    return num
        except:
            pass

        # Estrategia 3: buscar atributos aria-label/title en cualquier elemento
        try:
            elems = driver.find_elements(By.XPATH, "//*[@aria-label or @title]")
            for e in elems:
                try:
                    text = e.get_attribute('aria-label') or e.get_attribute('title') or e.text
                    num = extract_number_from_text(text)
                    if num > 0:
                        return num
                except:
                    continue
        except:
            pass

        # Estrategia 4: fallback - buscar cualquier span con dígitos
        try:
            spans = driver.find_elements(By.TAG_NAME, 'span')
            for span in spans:
                try:
                    text = span.get_attribute('title') or span.text
                    num = extract_number_from_text(text)
                    if num > 10:
                        return num
                except:
                    continue
        except:
            pass

    except Exception:
        pass

    return 0

def extract_followers_data(driver, profile_username, max_followers=100):
    """
    Extrae la lista de seguidores y el número de seguidores de cada uno
    """
    print(f"👥 Extrayendo datos de seguidores de @{profile_username}...")
    print(f"   Límite: {max_followers} seguidores\n")
    
    # Ir al perfil
    driver.get(f"https://www.instagram.com/{profile_username}/")
    time.sleep(4)
    
    try:
        # Buscar y hacer click en el enlace de "seguidores"
        print("🔍 Buscando enlace de seguidores...")
        
        # Múltiples estrategias para encontrar el botón de seguidores
        followers_button = None
        
        # Estrategia 1: Por href exacto
        try:
            followers_button = driver.find_element(By.CSS_SELECTOR, f"a[href='/{profile_username}/followers/']")
            print("✓ Estrategia 1: Encontrado por href exacto")
        except:
            pass
        
        # Estrategia 2: Por href parcial
        if not followers_button:
            try:
                followers_button = driver.find_element(By.CSS_SELECTOR, "a[href*='/followers/']")
                print("✓ Estrategia 2: Encontrado por href parcial")
            except:
                pass
        
        # Estrategia 3: Buscar todos los enlaces y filtrar
        if not followers_button:
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute('href')
                    if href and 'followers' in href:
                        followers_button = link
                        print("✓ Estrategia 3: Encontrado por búsqueda de enlaces")
                        break
            except:
                pass
        
        # Estrategia 4: Buscar por texto visible
        if not followers_button:
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    text = link.text.lower()
                    if 'seguidor' in text or 'follower' in text:
                        followers_button = link
                        print("✓ Estrategia 4: Encontrado por texto visible")
                        break
            except:
                pass
        
        if not followers_button:
            print("❌ No se pudo encontrar el enlace de seguidores")
            print("💡 Asegúrate de que el perfil sea público")
            
            # Guardar screenshot para debug
            driver.save_screenshot("debug_no_followers_button.png")
            print("📸 Screenshot guardado: debug_no_followers_button.png")
            return []
        
        print("✓ Abriendo lista de seguidores...")
        followers_button.click()
        time.sleep(6)
        
        # Esperar a que cargue el diálogo de seguidores
        followers_dialog = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
        )
        
        print("✓ Lista de seguidores abierta")
        print("📜 Scrolleando para cargar seguidores...\n")
        
        # Scroll dentro del diálogo para cargar más seguidores
        followers_data = []
        seen_usernames = set()
        scroll_attempts = 0
        max_scroll_attempts = 100  # Aumentado para permitir más scrolls
        
        # Intentar encontrar el contenedor scrolleable con múltiples estrategias
        scrollable_div = None
        scrollable_selectors = [
            "div[role='dialog'] div._aano",
            "div[role='dialog'] > div > div:nth-child(2)",
            "div[role='dialog'] div[style*='overflow']",
            "div.x1dm5mii",  # Clase común de Instagram para listas
            "div._aano",
        ]
        
        for selector in scrollable_selectors:
            try:
                scrollable_div = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✓ Contenedor scrolleable encontrado con selector: {selector[:40]}...\n")
                break
            except:
                continue
        
        if not scrollable_div:
            # Si no encuentra el contenedor, intentar con el diálogo directamente
            print("⚠ No se encontró contenedor scrolleable específico, usando diálogo completo\n")
            scrollable_div = followers_dialog
        
        last_count = 0
        no_new_followers_count = 0
        
        while len(followers_data) < max_followers and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            # Detectar si no se están cargando más seguidores ANTES de procesar
            current_count = len(followers_data)
            if current_count == last_count:
                no_new_followers_count += 1
                if no_new_followers_count >= 8:  # Aumentado de 5 a 8
                    print(f"\n  ⚠ No se detectan más seguidores nuevos después de {scroll_attempts} scrolls")
                    print(f"  ℹ Posiblemente ya se cargaron todos los seguidores disponibles")
                    print(f"  📊 Total extraído: {len(followers_data)}\n")
                    break
            else:
                no_new_followers_count = 0
                last_count = current_count
            
            # Buscar elementos de seguidores en el diálogo
            try:
                # NUEVA ESTRATEGIA: Buscar directamente todos los enlaces dentro del diálogo
                # y filtrar solo los que apuntan a perfiles de usuario
                all_links = followers_dialog.find_elements(By.TAG_NAME, "a")
                
                # Filtrar enlaces que son perfiles de usuario
                user_links = []
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        if href and '/' in href:
                            # Verificar que sea un perfil de usuario válido
                            path = href.replace('https://www.instagram.com/', '').strip('/')
                            # Debe ser solo un username, no rutas largas
                            if (path and 
                                '/' not in path and 
                                path not in ['explore', 'reels', 'direct', 'accounts', 'followers', 'following', 'p', 'stories']):
                                user_links.append(link)
                    except:
                        continue
                
                if scroll_attempts % 5 == 0:
                    print(f"  🔍 Scroll {scroll_attempts}: {len(user_links)} enlaces encontrados, {len(followers_data)} únicos extraídos")
                
                # Procesar cada enlace de usuario
                for user_link in user_links:
                    if len(followers_data) >= max_followers:
                        break
                    
                    try:
                        # Extraer username directamente del href del enlace
                        href = user_link.get_attribute('href')
                        if not href:
                            continue
                        
                        # Extraer username de la URL
                        path = href.replace('https://www.instagram.com/', '').strip('/')
                        username = path
                        
                        # Validar que sea un username válido
                        if not username or '/' in username:
                            continue
                        
                        # Limpiar el username
                        username = username.strip().lstrip('@')
                        
                        # Evitar duplicados
                        if username in seen_usernames:
                            continue
                        
                        # Validar que no sea una palabra reservada
                        if username.lower() in ['seguir', 'follow', 'siguiendo', 'following', 'explore', 'reels', 'direct']:
                            continue
                        
                        seen_usernames.add(username)
                        
                        # Guardar temporalmente (visitaremos el perfil después para obtener el número de seguidores)
                        followers_data.append({
                            'follower_username': username,
                            'follower_count': 0  # Lo obtendremos después visitando el perfil
                        })
                        
                        if len(followers_data) % 10 == 0:
                            print(f"  ✓ Extraídos {len(followers_data)}/{max_followers} seguidores...")
                        
                    except Exception as e:
                        continue
                
                # Hacer scroll hacia abajo
                try:
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                except:
                    # Si falla, intentar scroll en el body
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                
                # Esperar a que carguen nuevos seguidores
                # Usar tiempo variable: menos tiempo si ya hay muchos extraídos
                if len(followers_data) < 20:
                    time.sleep(2.5)  # Más tiempo al inicio
                else:
                    time.sleep(1.5)  # Menos tiempo después
                
            except Exception as e:
                print(f"  ⚠ Error en iteración: {e}")
                time.sleep(2)
                continue
        
        print(f"\n✓ Total de usernames extraídos: {len(followers_data)}")
        
        # Ahora visitar cada perfil para obtener el número de seguidores
        if len(followers_data) > 0:
            print(f"\n🔄 Visitando perfiles para obtener número de seguidores...")
            print(f"   Esto puede tomar {len(followers_data) * 2 // 60}+ minutos...\n")
            
            for idx, follower in enumerate(followers_data, 1):
                username = follower['follower_username']
                print(f"  [{idx}/{len(followers_data)}] Visitando @{username}...", end=" ")
                
                follower_count = get_follower_count_from_profile(driver, username)
                follower['follower_count'] = follower_count
                
                print(f"{follower_count:,} seguidores")
                
                # Pequeña pausa para no parecer bot
                time.sleep(1.5)
            
            print(f"\n✓ Datos de seguidores completados\n")
        
        if len(followers_data) == 0:
            print("\n⚠️ ADVERTENCIA: No se extrajeron seguidores")
            print("📸 Guardando screenshot para debug...")
            driver.save_screenshot("debug_no_followers_extracted.png")
            print("✓ Screenshot guardado: debug_no_followers_extracted.png")
            print("\n💡 Posibles causas:")
            print("   1. Instagram cambió el diseño de la página")
            print("   2. El perfil es privado")
            print("   3. Se necesitan más tiempos de espera")
            print("   4. Instagram detectó el bot y bloqueó el acceso\n")
        else:
            print()
        
        return followers_data
        
    except Exception as e:
        print(f"❌ Error extrayendo seguidores: {e}")
        import traceback
        traceback.print_exc()
        
        # Guardar screenshot
        try:
            driver.save_screenshot("debug_error.png")
            print("📸 Screenshot de error guardado: debug_error.png")
        except:
            pass
        
        return []

def get_first_digit(number):
    """Obtiene el primer dígito de un número"""
    if number == 0:
        return None
    return int(str(abs(number))[0])

def benford_expected_distribution():
    """Retorna la distribución esperada según la Ley de Benford"""
    return {i: math.log10(1 + 1/i) * 100 for i in range(1, 10)}

def analyze_first_digits(followers_data):
    """Analiza la distribución del primer dígito"""
    print("="*70)
    print("📊 ANÁLISIS DE LEY DE BENFORD - PRIMER DÍGITO")
    print("="*70 + "\n")
    
    # Extraer primeros dígitos
    first_digits = []
    for follower in followers_data:
        count = follower['follower_count']
        if count > 0:
            digit = get_first_digit(count)
            if digit:
                first_digits.append(digit)
    
    if not first_digits:
        print("❌ No hay datos suficientes para analizar")
        return None
    
    print(f"✓ Total de números válidos para análisis: {len(first_digits)}\n")
    
    # Contar frecuencias
    digit_counts = Counter(first_digits)
    total = len(first_digits)
    
    # Calcular distribución observada (porcentajes)
    observed_dist = {}
    for digit in range(1, 10):
        count = digit_counts.get(digit, 0)
        percentage = (count / total) * 100
        observed_dist[digit] = percentage
    
    # Distribución esperada (Benford)
    expected_dist = benford_expected_distribution()
    
    # Mostrar tabla comparativa
    print("-"*70)
    print(f"{'Dígito':<10} {'Observado':<15} {'Esperado':<15} {'Desviación':<15}")
    print("-"*70)
    
    total_deviation = 0
    for digit in range(1, 10):
        obs = observed_dist[digit]
        exp = expected_dist[digit]
        dev = abs(obs - exp)
        total_deviation += dev
        
        print(f"{digit:<10} {obs:>6.2f}%{'':<8} {exp:>6.2f}%{'':<8} {dev:>6.2f}%")
    
    avg_deviation = total_deviation / 9
    
    print("-"*70)
    print(f"Desviación promedio: {avg_deviation:.2f}%")
    print("-"*70 + "\n")
    
    # Calcular Chi-cuadrado
    chi_squared = 0
    for digit in range(1, 10):
        expected_count = (expected_dist[digit] / 100) * total
        observed_count = digit_counts.get(digit, 0)
        if expected_count > 0:
            chi_squared += ((observed_count - expected_count) ** 2) / expected_count
    
    # Interpretación
    print("📊 INTERPRETACIÓN:\n")
    
    if avg_deviation < 5:
        print("✅ Distribución MUY CERCANA a la Ley de Benford")
        print("   → Los seguidores parecen ser REALES y ORGÁNICOS\n")
        verdict = "REAL"
    elif avg_deviation < 10:
        print("✅ Distribución CERCANA a la Ley de Benford")
        print("   → Los seguidores probablemente son REALES\n")
        verdict = "PROBABLEMENTE REAL"
    elif avg_deviation < 15:
        print("⚠️  Distribución MODERADAMENTE DESVIADA de Benford")
        print("   → Posible mezcla de seguidores reales y artificiales\n")
        verdict = "SOSPECHOSO"
    else:
        print("🚨 Distribución MUY DESVIADA de la Ley de Benford")
        print("   → Alta probabilidad de seguidores FALSOS o BOTS\n")
        verdict = "ALTA PROBABILIDAD DE BOTS"
    
    print(f"🎯 CONCLUSIÓN: {verdict}")
    print("="*70 + "\n")
    
    return {
        'first_digits': first_digits,
        'digit_counts': dict(digit_counts),
        'observed_dist': observed_dist,
        'expected_dist': expected_dist,
        'avg_deviation': avg_deviation,
        'chi_squared': chi_squared,
        'verdict': verdict,
        'total_analyzed': total
    }

def create_benford_chart(analysis, profile_name):
    """Crea un gráfico comparando la distribución observada vs esperada"""
    print("📊 Generando gráfico comparativo...")
    
    if not analysis:
        print("⚠ No hay datos para generar gráfico")
        return
    
    digits = list(range(1, 10))
    observed = [analysis['observed_dist'][d] for d in digits]
    expected = [analysis['expected_dist'][d] for d in digits]
    
    # Crear figura
    plt.figure(figsize=(12, 7))
    
    # Ancho de las barras
    bar_width = 0.35
    x_pos = range(len(digits))
    
    # Crear barras
    bars1 = plt.bar([x - bar_width/2 for x in x_pos], observed, bar_width, 
                     label='Distribución Observada', color='#FF6B6B', alpha=0.8)
    bars2 = plt.bar([x + bar_width/2 for x in x_pos], expected, bar_width,
                     label='Ley de Benford (Esperada)', color='#4ECDC4', alpha=0.8)
    
    # Etiquetas y título
    plt.xlabel('Primer Dígito', fontsize=12, fontweight='bold')
    plt.ylabel('Frecuencia (%)', fontsize=12, fontweight='bold')
    plt.title(f'Análisis de Ley de Benford - @{profile_name}\n' + 
              f'Desviación Promedio: {analysis["avg_deviation"]:.2f}% | Conclusión: {analysis["verdict"]}',
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(x_pos, digits)
    plt.legend(fontsize=11, loc='upper right')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Agregar valores encima de las barras
    for bar in bars1:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Guardar gráfico
    filename = f"{profile_name}_benford_chart.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Gráfico guardado: {filename}\n")

def save_results_to_csv(profile_name, profile_followers, followers_data, analysis):
    """Guarda todos los resultados en archivos CSV"""
    print("💾 Guardando resultados en CSV...\n")
    
    # 1. Datos completos de seguidores
    followers_filename = f"{profile_name}_seguidores_datos.csv"
    with open(followers_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Username del Seguidor", "Número de Seguidores", "Primer Dígito"])
        
        for follower in followers_data:
            username = follower['follower_username']
            count = follower['follower_count']
            first_digit = get_first_digit(count) if count > 0 else "N/A"
            writer.writerow([username, count, first_digit])
    
    print(f"✓ Datos de seguidores: {followers_filename}")
    
    # 2. Análisis de distribución
    if analysis:
        distribution_filename = f"{profile_name}_distribucion_benford.csv"
        with open(distribution_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Análisis de Ley de Benford - Distribución del Primer Dígito"])
            writer.writerow([])
            writer.writerow(["Perfil analizado:", f"@{profile_name}"])
            writer.writerow(["Seguidores del perfil:", f"{profile_followers:,}"])
            writer.writerow(["Seguidores analizados:", len(followers_data)])
            writer.writerow(["Números válidos analizados:", analysis['total_analyzed']])
            writer.writerow([])
            writer.writerow(["Dígito", "Cantidad", "Frecuencia Observada (%)", "Frecuencia Esperada (%)", "Desviación (%)"])
            
            for digit in range(1, 10):
                count = analysis['digit_counts'].get(digit, 0)
                obs = analysis['observed_dist'][digit]
                exp = analysis['expected_dist'][digit]
                dev = abs(obs - exp)
                writer.writerow([digit, count, f"{obs:.2f}", f"{exp:.2f}", f"{dev:.2f}"])
            
            writer.writerow([])
            writer.writerow(["Desviación Promedio:", f"{analysis['avg_deviation']:.2f}%"])
            writer.writerow(["Chi-cuadrado:", f"{analysis['chi_squared']:.4f}"])
            writer.writerow(["Conclusión:", analysis['verdict']])
        
        print(f"✓ Análisis de distribución: {distribution_filename}")
    
    # 3. Resumen ejecutivo
    summary_filename = f"{profile_name}_resumen.csv"
    with open(summary_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["RESUMEN EJECUTIVO - ANÁLISIS DE SEGUIDORES"])
        writer.writerow([])
        writer.writerow(["Perfil analizado:", f"@{profile_name}"])
        writer.writerow(["Fecha de análisis:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Seguidores totales del perfil:", f"{profile_followers:,}"])
        writer.writerow(["Seguidores analizados:", len(followers_data)])
        writer.writerow([])
        
        if analysis:
            writer.writerow(["=== RESULTADOS DEL ANÁLISIS DE BENFORD ==="])
            writer.writerow(["Números válidos analizados:", analysis['total_analyzed']])
            writer.writerow(["Desviación promedio:", f"{analysis['avg_deviation']:.2f}%"])
            writer.writerow(["Valor Chi-cuadrado:", f"{analysis['chi_squared']:.4f}"])
            writer.writerow([])
            writer.writerow(["🎯 CONCLUSIÓN:", analysis['verdict']])
            writer.writerow([])
            
            if analysis['avg_deviation'] < 10:
                writer.writerow(["Interpretación:", "Los seguidores parecen ser REALES y ORGÁNICOS"])
            elif analysis['avg_deviation'] < 15:
                writer.writerow(["Interpretación:", "Posible mezcla de seguidores reales y artificiales"])
            else:
                writer.writerow(["Interpretación:", "Alta probabilidad de seguidores FALSOS o BOTS"])
    
    print(f"✓ Resumen ejecutivo: {summary_filename}")
    print()

def main():
    """Función principal"""
    # CONFIGURACIÓN
    INSTAGRAM_USERNAME = ""
    INSTAGRAM_PASSWORD = ""  # ⚠️ Cambia esto
    PROFILE_TO_ANALYZE = ""
    MAX_FOLLOWERS = 100  # Cuántos seguidores analizar (más = más tiempo)
    
    if INSTAGRAM_PASSWORD == "TU_CONTRASEÑA_AQUI":
        print("❌ ERROR: Configura tu contraseña")
        return
    
    driver = None
    
    try:
        print("="*70)
        print("🔍 ANÁLISIS DE SEGUIDORES - LEY DE BENFORD")
        print("="*70)
        print(f"Perfil a analizar: @{PROFILE_TO_ANALYZE}")
        print(f"Máximo de seguidores a analizar: {MAX_FOLLOWERS}")
        print("="*70 + "\n")
        
        # Iniciar navegador
        print("🌐 Iniciando navegador Chrome...")
        driver = setup_driver()
        
        # Login
        if not login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
            print("❌ No se pudo iniciar sesión")
            return
        
        # Obtener número de seguidores del perfil principal
        profile_followers = get_profile_followers_count(driver, PROFILE_TO_ANALYZE)
        
        # Extraer datos de seguidores
        followers_data = extract_followers_data(driver, PROFILE_TO_ANALYZE, MAX_FOLLOWERS)
        
        if not followers_data:
            print("❌ No se extrajeron datos de seguidores")
            return
        
        # Analizar con Benford
        analysis = analyze_first_digits(followers_data)
        
        # Crear gráfico
        create_benford_chart(analysis, PROFILE_TO_ANALYZE)
        
        # Guardar CSVs
        save_results_to_csv(PROFILE_TO_ANALYZE, profile_followers, followers_data, analysis)
        
        print("="*70)
        print("✅ ¡ANÁLISIS COMPLETADO EXITOSAMENTE!")
        print("="*70)
        print("\nArchivos generados:")
        print(f"  📄 {PROFILE_TO_ANALYZE}_seguidores_datos.csv")
        print(f"  📊 {PROFILE_TO_ANALYZE}_distribucion_benford.csv")
        print(f"  📝 {PROFILE_TO_ANALYZE}_resumen.csv")
        print(f"  📈 {PROFILE_TO_ANALYZE}_benford_chart.png")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("🔒 Cerrando navegador...")
            time.sleep(2)
            driver.quit()

if __name__ == "__main__":
    main()
