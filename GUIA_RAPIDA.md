# 🎯 GUÍA RÁPIDA - Análisis de Seguidores

## Paso a Paso

### 1️⃣ Configurar
Abre `analisis_seguidores_benford.py` (línea 502-505):
```python
INSTAGRAM_USERNAME = "tu_usuario"
INSTAGRAM_PASSWORD = "tu_contraseña"  
PROFILE_TO_ANALYZE = "perfil_a_analizar"
MAX_FOLLOWERS = 100
```

### 2️⃣ Ejecutar
```powershell
python analisis_seguidores_benford.py
```

### 3️⃣ Esperar
- 100 seguidores = ~15 minutos
- Verás el navegador Chrome abrirse
- No toques nada mientras trabaja

### 4️⃣ Resultados
Se generan 4 archivos:

📄 **perfil_seguidores_datos.csv**
```
Username, Seguidores, Primer Dígito
user1, 1234, 1
user2, 567, 5
user3, 89, 8
...
```

📊 **perfil_distribucion_benford.csv**
```
Dígito  Observado  Esperado  Desviación
1       28.5%      30.1%     1.6%
2       19.2%      17.6%     1.6%
3       11.8%      12.5%     0.7%
...

Desviación Promedio: 5.23%
Conclusión: PROBABLEMENTE REAL
```

📝 **perfil_resumen.csv**
```
Perfil: @nicole.az13
Seguidores totales: 7
Seguidores analizados: 100
Desviación: 5.23%
CONCLUSIÓN: ✅ PROBABLEMENTE REAL
```

📈 **perfil_benford_chart.png**
Gráfico comparativo visual (barras rojas vs azules)

---

## 📊 ¿Cómo interpretar?

| Desviación | Resultado |
|-----------|-----------|
| 0-5% | ✅ **MUY REAL** - Seguidores orgánicos |
| 5-10% | ✅ **REAL** - Probablemente legítimos |
| 10-15% | ⚠️ **SOSPECHOSO** - Mezcla de reales y falsos |
| +15% | 🚨 **BOTS** - Alta probabilidad de seguidores falsos |

---

## ⚡ Ejemplo Rápido

### Cuenta REAL:
```
Dígito 1: 30.2% ✅ (esperado 30.1%)
Dígito 2: 17.8% ✅ (esperado 17.6%)
Dígito 3: 12.1% ✅ (esperado 12.5%)
→ Desviación: 3.4% → REAL
```

### Cuenta con BOTS:
```
Dígito 1: 15.2% ❌ (esperado 30.1%)
Dígito 2: 14.8% ❌ (esperado 17.6%)
Dígito 3: 14.1% ❌ (esperado 12.5%)
→ Desviación: 18.7% → BOTS
```

---

## ⚠️ Problemas Comunes

**Error: "No se pudo iniciar sesión"**
→ Verifica usuario y contraseña

**Error: "No se encontró enlace de seguidores"**
→ El perfil debe ser público

**Instagram pide verificación**
→ Complétala en el navegador y vuelve a ejecutar

**Sale "0 seguidores extraídos"**
→ Aumenta los tiempos de espera (time.sleep)

---

## 💡 Tips

✅ Empieza con MAX_FOLLOWERS = 50 para probar
✅ Usa perfiles públicos
✅ Espera 30min entre análisis para evitar bloqueos
✅ Guarda el gráfico PNG para presentaciones
✅ Compara varios perfiles para tener contexto

---

¡Listo para usar! 🚀
