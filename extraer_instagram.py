# guarda como extraer_instagram.py
import instaloader
import csv
import time
from datetime import timezone
import random

# Configuración más conservadora para evitar bloqueos
L = instaloader.Instaloader(
    download_pictures=False, 
    download_comments=False, 
    save_metadata=False,
    max_connection_attempts=3,
    request_timeout=300.0  # Tiempo de espera más largo
)

# Login
try:
    L.load_session_from_file("iamjohnyv13")
    print("✓ Sesión cargada exitosamente")
except Exception as e:
    print(f"Error cargando sesión: {e}")
    exit(1)

profile_name = "jofre_a21"

try:
    print(f"Obteniendo perfil de {profile_name}...")
    profile = instaloader.Profile.from_username(L.context, profile_name)
    print(f"✓ Perfil encontrado: {profile.full_name}")
    print(f"  Posts totales: {profile.mediacount}")
    
    rows = []
    post_count = 0
    max_posts = 50  # Limitar a 50 posts para evitar bloqueos
    
    print(f"\nExtrayendo hasta {max_posts} posts (esto tomará varios minutos)...")
    
    for post in profile.get_posts():
        if post_count >= max_posts:
            break
            
        try:
            rows.append({
                "shortcode": post.shortcode,
                "date_utc": post.date_utc.isoformat(),
                "likes": post.likes or 0,
                "comments": post.comments or 0,
                "is_video": post.is_video,
                "video_views": getattr(post, "video_view_count", None),
                "caption_length": len(post.caption or "")
            })
            post_count += 1
            print(f"  ✓ Post {post_count}/{max_posts} extraído")
            
            # Espera aleatoria entre 15-25 segundos para parecer más humano
            wait_time = random.uniform(15, 25)
            time.sleep(wait_time)
            
        except instaloader.exceptions.ConnectionException as e:
            print(f"\n⚠ Error de conexión en post {post_count}: {e}")
            print("Esperando 5 minutos antes de continuar...")
            time.sleep(300)  # Espera 5 minutos si hay error
            
        except Exception as e:
            print(f"\n⚠ Error inesperado: {e}")
            continue

    # Guardar CSV
    if rows:
        filename = f"{profile_name}_posts.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n✓ CSV generado: {filename}")
        print(f"✓ Total de posts extraídos: {len(rows)}")
    else:
        print("\n⚠ No se extrajeron posts")
        
except instaloader.exceptions.ConnectionException as e:
    print(f"\n❌ Error de conexión: {e}")
    print("\n💡 Soluciones:")
    print("  1. Espera 30-60 minutos antes de intentar de nuevo")
    print("  2. Instagram ha detectado demasiadas solicitudes")
    print("  3. Considera usar la cuenta desde tu navegador para 'normalizar' la actividad")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
