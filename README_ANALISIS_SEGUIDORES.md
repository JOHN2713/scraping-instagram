# 🔍 Análisis de Seguidores con Ley de Benford

## 📋 ¿Qué hace este script?

Este script analiza los seguidores de un perfil de Instagram usando la **Ley de Benford** para detectar si los seguidores son reales o artificiales (bots).

### Proceso:

1. **Entra al perfil** de Instagram especificado
2. **Obtiene el número total de seguidores** del perfil
3. **Abre la lista de seguidores** y extrae cada uno
4. **Para cada seguidor, obtiene cuántos seguidores tiene**
5. **Analiza el primer dígito** de esos números de seguidores
6. **Compara con la Ley de Benford** para detectar anomalías
7. **Genera un gráfico visual** comparando distribución real vs esperada
8. **Crea 4 archivos de salida** con toda la información

---

## 🎯 ¿Qué es la Ley de Benford?

La **Ley de Benford** dice que en datos naturales (como poblaciones, números en noticias, transacciones), el primer dígito NO se distribuye uniformemente:

- **Dígito 1**: Aparece ~30.1% de las veces
- **Dígito 2**: Aparece ~17.6% de las veces
- **Dígito 3**: Aparece ~12.5% de las veces
- ...y así sucesivamente

### ¿Por qué funciona para detectar bots?

- **Seguidores reales**: Sus números de seguidores siguen patrones naturales (Benford)
- **Seguidores falsos/bots**: Sus números son artificiales y NO siguen Benford

---

## 🚀 Cómo usar

### 1. Configurar el script

Abre `analisis_seguidores_benford.py` y configura:

```python
INSTAGRAM_USERNAME = "tu_usuario"      # Tu usuario de Instagram
INSTAGRAM_PASSWORD = "tu_contraseña"    # Tu contraseña
PROFILE_TO_ANALYZE = "perfil_a_analizar"  # Perfil que quieres analizar
MAX_FOLLOWERS = 100  # Cuántos seguidores analizar (100-500 recomendado)
```

### 2. Ejecutar

```powershell
python analisis_seguidores_benford.py
```

### 3. Esperar

El proceso toma tiempo:
- **100 seguidores**: ~10-15 minutos
- **200 seguidores**: ~20-30 minutos
- **500 seguidores**: ~45-60 minutos

---

## 📊 Archivos generados

### 1. `perfil_seguidores_datos.csv`
Contiene la lista completa de seguidores:
- Username del seguidor
- Número de seguidores que tiene
- Primer dígito de ese número

### 2. `perfil_distribucion_benford.csv`
Análisis detallado de la distribución:
- Frecuencia observada por cada dígito (1-9)
- Frecuencia esperada según Benford
- Desviación calculada
- Chi-cuadrado y conclusión

### 3. `perfil_resumen.csv`
Resumen ejecutivo con:
- Datos del perfil
- Conclusión final
- Interpretación de resultados

### 4. `perfil_benford_chart.png`
**Gráfico visual** que muestra:
- Barras ROJAS: Distribución observada (datos reales)
- Barras AZULES: Ley de Benford (esperada)
- Título con desviación y conclusión

---

## 📈 Interpretación de Resultados

### Desviación Promedio:

| Desviación | Interpretación |
|-----------|----------------|
| **< 5%** | ✅ Seguidores **MUY REALES** y orgánicos |
| **5-10%** | ✅ Seguidores **PROBABLEMENTE REALES** |
| **10-15%** | ⚠️ **SOSPECHOSO** - Posible mezcla de reales y falsos |
| **> 15%** | 🚨 **ALTA PROBABILIDAD DE BOTS** |

### Ejemplo de conclusiones:

```
Desviación Promedio: 3.45%
🎯 CONCLUSIÓN: REAL
→ Los seguidores parecen ser REALES y ORGÁNICOS
```

```
Desviación Promedio: 18.72%
🎯 CONCLUSIÓN: ALTA PROBABILIDAD DE BOTS
→ Alta probabilidad de seguidores FALSOS o BOTS
```

---

## ⚙️ Configuración Avanzada

### Cambiar número de seguidores a analizar:

```python
MAX_FOLLOWERS = 200  # Analizar 200 seguidores (más precisión, más tiempo)
```

**Recomendaciones:**
- **Mínimo**: 50 seguidores (resultados menos confiables)
- **Óptimo**: 100-200 seguidores (buen balance)
- **Máximo**: 500+ seguidores (muy preciso pero lento)

### Si el script falla:

1. **Instagram pide verificación**: Completa la verificación en el navegador
2. **Rate limiting**: Espera 30 minutos y vuelve a intentar
3. **No encuentra elementos**: Instagram cambió el diseño, reporta el error

---

## 🎨 Ejemplo de Gráfico

El gráfico generado mostrará algo así:

```
     Análisis de Ley de Benford - @perfil
     Desviación: 7.23% | Conclusión: PROBABLEMENTE REAL

40% |  ▓▓▓
    |  ▓▓▓     
30% |  ▓▓▓  ▒▒
    |  ▓▓▓  ▒▒
20% |  ▓▓▓  ▒▒  ▓▓  ▒▒
    |  ▓▓▓  ▒▒  ▓▓  ▒▒  ▓▓  ▒▒
10% |  ▓▓▓  ▒▒  ▓▓  ▒▒  ▓▓  ▒▒  ▓▓  ▒▒  ▓▓  ▒▒
    +--------------------------------------------------
       1    2    3    4    5    6    7    8    9

    ▓▓▓ = Distribución Observada (tus datos)
    ▒▒▒ = Ley de Benford (esperada)
```

---

## ⚠️ Limitaciones

1. **Requiere muchos datos**: Mínimo 50 seguidores para resultados confiables
2. **Tiempo**: Puede tomar 30-60 minutos para 200+ seguidores
3. **Rate limiting**: Instagram puede bloquear si haces demasiadas requests
4. **Cambios de UI**: Si Instagram cambia su diseño, el script puede fallar

---

## 💡 Consejos

- **Empieza con 100 seguidores** para probar
- **Usa cuentas públicas** (más fácil de analizar)
- **Espera entre análisis** (no analices 10 perfiles seguidos)
- **Compara resultados** de varios perfiles para contexto
- **Guarda los gráficos** para presentaciones o reportes

---

## 📞 Soporte

Si tienes problemas:
1. Verifica tu usuario y contraseña
2. Revisa que el perfil sea público
3. Asegúrate de tener conexión a internet estable
4. Intenta con MAX_FOLLOWERS = 50 primero

---

## 🎓 Referencias

- [Ley de Benford - Wikipedia](https://es.wikipedia.org/wiki/Ley_de_Benford)
- [Benford's Law for Bot Detection](https://en.wikipedia.org/wiki/Benford%27s_law)
