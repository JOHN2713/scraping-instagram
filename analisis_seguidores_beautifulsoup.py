"""
Análisis de Seguidores con Ley de Benford - VERSIÓN MEJORADA
Usa Selenium + BeautifulSoup para extracción más eficiente y robusta
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
import os
import math
import re
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

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
    """Extrae número de un texto como '1,234' o '1.2K' or '1M'"""
    try:
        text = str(text).strip().upper()
        
        if 'K' in text:
            num_str = text.replace('K', '').replace(',', '.').strip()
            return int(float(re.sub(r'[^\d.]', '', num_str)) * 1000)
        
        if 'M' in text:
            num_str = text.replace('M', '').replace(',', '.').strip()
            return int(float(re.sub(r'[^\d.]', '', num_str)) * 1000000)
        
        numbers = re.sub(r'[^\d]', '', text)
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
        # Usar BeautifulSoup para parsear
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Buscar en los enlaces con "followers"
        for link in soup.find_all('a', href=True):
            if 'followers' in link['href']:
                # Buscar el número en el span title
                title_span = link.find('span', title=True)
                if title_span and title_span.get('title'):
                    num = extract_number_from_text(title_span['title'])
                    if num > 0:
                        print(f"✓ Seguidores del perfil: {num:,}\n")
                        return num
                
                # Buscar en el texto del span
                span = link.find('span')
                if span:
                    num = extract_number_from_text(span.get_text())
                    if num > 0:
                        print(f"✓ Seguidores del perfil: {num:,}\n")
                        return num
    except Exception as e:
        print(f"⚠ Error: {e}")
    
    return 0

def extract_usernames_with_beautifulsoup(html_content):
    """Extrae usernames del HTML usando BeautifulSoup - VERSIÓN AGRESIVA"""
    soup = BeautifulSoup(html_content, 'lxml')
    usernames = set()
    reserved = ['explore', 'reels', 'direct', 'accounts', 'followers', 'following', 'p', 'stories', 'tv', 'reel']
    
    # ESTRATEGIA 1: Buscar todos los enlaces href
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Extraer username de URLs tipo: /username/ o https://instagram.com/username/
        if 'instagram.com/' in href:
            # URL completa
            parts = href.split('instagram.com/')
            if len(parts) > 1:
                username = parts[1].strip('/').split('/')[0].split('?')[0]
                if username and username not in reserved and len(username) < 30 and not username.startswith('http'):
                    usernames.add(username)
        elif href.startswith('/'):
            # URL relativa
            username = href.strip('/').split('/')[0].split('?')[0]
            if username and username not in reserved and len(username) < 30:
                usernames.add(username)
    
    # ESTRATEGIA 2: Buscar usernames en el texto usando regex
    # Formato típico de Instagram: @username o texto que parece username
    username_pattern = r'@?([a-zA-Z0-9._]{1,30})'
    
    # Buscar en todos los span y div que podrían contener usernames
    for element in soup.find_all(['span', 'div', 'a']):
        text = element.get_text(strip=True)
        if text and len(text) < 30 and ' ' not in text:
            # Podría ser un username
            username = text.lstrip('@')
            if (username and 
                username not in reserved and 
                not username.isdigit() and
                len(username) >= 3 and
                any(c.isalnum() for c in username)):
                usernames.add(username)
    
    # ESTRATEGIA 3: Buscar en atributos title, aria-label, alt
    for element in soup.find_all(attrs={'title': True}):
        title = element.get('title', '')
        # Los usernames a veces están en el title
        matches = re.findall(username_pattern, title)
        for match in matches:
            username = match.lstrip('@')
            if username and username not in reserved and len(username) >= 3:
                usernames.add(username)
    
    return usernames

def get_follower_count_from_profile(driver, username):
    """Visita el perfil de un usuario y obtiene su número de seguidores usando BeautifulSoup"""
    try:
        driver.get(f"https://www.instagram.com/{username}/")
        
        # Esperar a que cargue
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        except:
            time.sleep(2)
        
        # Parsear con BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Buscar en enlaces con "followers"
        for link in soup.find_all('a', href=True):
            if 'followers' in link['href']:
                # Buscar en title attribute
                title_span = link.find('span', title=True)
                if title_span and title_span.get('title'):
                    num = extract_number_from_text(title_span['title'])
                    if num > 0:
                        return num
                
                # Buscar en texto
                span = link.find('span')
                if span:
                    num = extract_number_from_text(span.get_text())
                    if num > 0:
                        return num
        
        # Estrategia alternativa: buscar en meta tags
        meta_tag = soup.find('meta', property='og:description')
        if meta_tag and meta_tag.get('content'):
            content = meta_tag['content']
            # Formato: "X Followers, Y Following, Z Posts"
            match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KM]?)\s*(?:Followers|Seguidores)', content, re.IGNORECASE)
            if match:
                num = extract_number_from_text(match.group(1))
                if num > 0:
                    return num
                    
    except Exception:
        pass
    
    return 0

def extract_usernames_selenium_direct(driver):
    """Extrae usernames directamente desde Selenium (complementa BeautifulSoup)"""
    usernames = set()
    reserved = ['explore', 'reels', 'direct', 'accounts', 'followers', 'following', 'p', 'stories', 'tv']
    
    try:
        # Buscar TODOS los enlaces visibles en el diálogo
        dialog = driver.find_element(By.CSS_SELECTOR, "div[role='dialog']")
        links = dialog.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            try:
                href = link.get_attribute('href')
                if href and '/' in href:
                    # Extraer username
                    if 'instagram.com/' in href:
                        username = href.split('instagram.com/')[-1].strip('/').split('/')[0].split('?')[0]
                    else:
                        username = href.strip('/').split('/')[0].split('?')[0]
                    
                    if (username and 
                        username not in reserved and 
                        len(username) < 30 and
                        not username.startswith('http')):
                        usernames.add(username)
            except:
                continue
    except:
        pass
    
    return usernames

def extract_followers_data_improved(driver, profile_username, max_followers=100):
    """Extrae datos de seguidores usando Selenium + BeautifulSoup - MÉTODO HÍBRIDO"""
    print(f"👥 Extrayendo datos de seguidores de @{profile_username}...")
    print(f"   Límite: {max_followers} seguidores")
    print(f"   Método: Selenium + BeautifulSoup (HÍBRIDO)\n")
    
    driver.get(f"https://www.instagram.com/{profile_username}/")
    time.sleep(4)
    
    try:
        # Buscar botón de seguidores
        print("🔍 Buscando enlace de seguidores...")
        
        followers_button = None
        try:
            followers_button = driver.find_element(By.CSS_SELECTOR, f"a[href='/{profile_username}/followers/']")
            print("✓ Encontrado por CSS selector")
        except:
            try:
                followers_button = driver.find_element(By.XPATH, "//a[contains(@href, '/followers')]")
                print("✓ Encontrado por XPath")
            except:
                print("❌ No se encontró el botón de seguidores")
                return []
        
        print("✓ Abriendo lista de seguidores...")
        followers_button.click()
        time.sleep(6)
        
        # Esperar el diálogo
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
        )
        
        print("✓ Diálogo de seguidores abierto")
        print("📜 Extrayendo usernames con scroll agresivo y BeautifulSoup...\n")
        
        all_usernames = set()
        scroll_count = 0
        max_scrolls = 150  # Aumentado
        no_change_count = 0
        last_html_length = 0
        
        # Encontrar el div scrolleable
        scrollable_div = None
        try:
            scrollable_div = driver.find_element(By.CSS_SELECTOR, "div[role='dialog'] > div > div:nth-child(2)")
            print("✓ Contenedor scrolleable encontrado\n")
        except:
            try:
                scrollable_div = driver.find_element(By.CSS_SELECTOR, "div[role='dialog']")
                print("✓ Contenedor scrolleable encontrado (fallback)\n")
            except:
                print("⚠ No se encontró contenedor scrolleable")
                return []
        
        while len(all_usernames) < max_followers and scroll_count < max_scrolls:
            scroll_count += 1
            
            # MÚLTIPLES SCROLLS RÁPIDOS para cargar más contenido
            for _ in range(3):  # 3 scrolls consecutivos
                try:
                    driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight", 
                        scrollable_div
                    )
                except:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.3)  # Pequeña pausa entre scrolls
            
            # ESPERAR a que Instagram cargue más contenido
            time.sleep(3.5)  # Aumentado significativamente
            
            # Obtener el HTML actual y parsearlo con BeautifulSoup
            html_content = driver.page_source
            current_html_length = len(html_content)
            
            # MÉTODO HÍBRIDO: Combinar BeautifulSoup + Selenium directo
            new_usernames_bs = extract_usernames_with_beautifulsoup(html_content)
            new_usernames_selenium = extract_usernames_selenium_direct(driver)
            
            # Combinar ambos conjuntos
            new_usernames = new_usernames_bs.union(new_usernames_selenium)
            
            # Agregar nuevos usernames
            before_count = len(all_usernames)
            all_usernames.update(new_usernames)
            after_count = len(all_usernames)
            
            # Detectar si ya no hay nuevos usernames Y el HTML no está creciendo
            if after_count == before_count and current_html_length == last_html_length:
                no_change_count += 1
                if no_change_count >= 5:  # Reducido de 8 a 5 pero con doble condición
                    print(f"\n  ⚠ No se detectan más seguidores nuevos después de {scroll_count} scrolls")
                    print(f"  ℹ HTML estático detectado - fin de lista")
                    print(f"  ✓ Total extraído: {len(all_usernames)}\n")
                    break
            else:
                no_change_count = 0
                last_html_length = current_html_length
            
            if scroll_count % 3 == 0:  # Reporte más frecuente
                print(f"  🔍 Scroll {scroll_count}: {len(all_usernames)} usernames únicos | HTML: {current_html_length:,} bytes")
            
            # Si ya alcanzamos el objetivo, parar
            if len(all_usernames) >= max_followers:
                print(f"\n  ✅ Objetivo alcanzado: {len(all_usernames)} seguidores\n")
                break
        
        # Convertir a lista
        usernames_list = list(all_usernames)[:max_followers]
        
        print(f"\n✓ Total de usernames únicos extraídos: {len(usernames_list)}")
        
        # Crear estructura de datos
        followers_data = [{'follower_username': username, 'follower_count': 0} for username in usernames_list]
        
        # Visitar cada perfil para obtener el número de seguidores
        if len(followers_data) > 0:
            print(f"\n🔄 Visitando perfiles para obtener número de seguidores...")
            print(f"   Esto puede tomar {len(followers_data) * 2 // 60}+ minutos...\n")
            
            for idx, follower in enumerate(followers_data, 1):
                username = follower['follower_username']
                print(f"  [{idx}/{len(followers_data)}] @{username}...", end=" ")
                
                follower_count = get_follower_count_from_profile(driver, username)
                follower['follower_count'] = follower_count
                
                print(f"{follower_count:,} seguidores")
                
                time.sleep(1.2)
            
            print(f"\n✓ Extracción completada\n")
        
        return followers_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
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
    
    digit_counts = Counter(first_digits)
    total = len(first_digits)
    
    observed_dist = {}
    for digit in range(1, 10):
        count = digit_counts.get(digit, 0)
        percentage = (count / total) * 100
        observed_dist[digit] = percentage
    
    expected_dist = benford_expected_distribution()
    
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
    
    chi_squared = 0
    for digit in range(1, 10):
        expected_count = (expected_dist[digit] / 100) * total
        observed_count = digit_counts.get(digit, 0)
        if expected_count > 0:
            chi_squared += ((observed_count - expected_count) ** 2) / expected_count
    
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
    
    plt.figure(figsize=(12, 7))
    
    bar_width = 0.35
    x_pos = range(len(digits))
    
    bars1 = plt.bar([x - bar_width/2 for x in x_pos], observed, bar_width, 
                     label='Distribución Observada', color='#FF6B6B', alpha=0.8)
    bars2 = plt.bar([x + bar_width/2 for x in x_pos], expected, bar_width,
                     label='Ley de Benford (Esperada)', color='#4ECDC4', alpha=0.8)
    
    plt.xlabel('Primer Dígito', fontsize=12, fontweight='bold')
    plt.ylabel('Frecuencia (%)', fontsize=12, fontweight='bold')
    plt.title(f'Análisis de Ley de Benford - @{profile_name}\n' + 
              f'Desviación Promedio: {analysis["avg_deviation"]:.2f}% | Conclusión: {analysis["verdict"]}',
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(x_pos, digits)
    plt.legend(fontsize=11, loc='upper right')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar in bars1:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    filename = f"{profile_name}_benford_chart.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Gráfico guardado: {filename}\n")

def save_results_to_csv(profile_name, profile_followers, followers_data, analysis):
    """Guarda todos los resultados en archivos CSV"""
    print("💾 Guardando resultados en CSV...\n")
    
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
    
    summary_filename = f"{profile_name}_resumen.csv"
    with open(summary_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["RESUMEN EJECUTIVO - ANÁLISIS DE SEGUIDORES"])
        writer.writerow([])
        writer.writerow(["Perfil analizado:", f"@{profile_name}"])
        writer.writerow(["Fecha de análisis:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Método de extracción:", "Selenium + BeautifulSoup"])
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
    INSTAGRAM_USERNAME = "iamjohnyv13"
    INSTAGRAM_PASSWORD = "Diana2809"
    PROFILE_TO_ANALYZE = "mtc_castu"
    MAX_FOLLOWERS = 100
    
    driver = None
    
    try:
        print("="*70)
        print("🔍 ANÁLISIS DE SEGUIDORES - VERSIÓN MEJORADA")
        print("   Método: Selenium + BeautifulSoup")
        print("="*70)
        print(f"Perfil a analizar: @{PROFILE_TO_ANALYZE}")
        print(f"Máximo de seguidores a analizar: {MAX_FOLLOWERS}")
        print("="*70 + "\n")
        
        print("🌐 Iniciando navegador Chrome...")
        driver = setup_driver()
        
        if not login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
            print("❌ No se pudo iniciar sesión")
            return
        
        profile_followers = get_profile_followers_count(driver, PROFILE_TO_ANALYZE)
        
        followers_data = extract_followers_data_improved(driver, PROFILE_TO_ANALYZE, MAX_FOLLOWERS)
        
        if not followers_data:
            print("❌ No se extrajeron datos de seguidores")
            return
        
        analysis = analyze_first_digits(followers_data)
        
        if analysis:
            create_benford_chart(analysis, PROFILE_TO_ANALYZE)
        
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
