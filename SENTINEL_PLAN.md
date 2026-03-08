# 🛡️ Proyecto Sentinel: Implementación APK Mobile

## 1. Arquitectura del Sistema
- **Cerebro (Python):** Localizado en `scipia/plugins/session_first_touch/`. Se encarga del análisis cuantitativo y entrenamiento.
- **Cliente (Android/Java):** Localizado en `android/app/`. Se encarga de la UI, descarga de datos de Kraken y ejecución de la inferencia.
- **Puente (GitHub):** 
    - `SaKinMin/Sentinel`: Código fuente (Python + Java).
    - `DrDiazHurtado/Sentinel_APK_model`: Binarios de la APK y modelos entrenados.

## 2. Flujo de Datos "Zero-Cost"
1. **Entrenamiento:** Se genera el modelo `sentinel_v1.ptl` en PC local.
2. **Despliegue:** El modelo se sube al repo `Sentinel_APK_model`.
3. **Sincronización:** La APK al iniciar consulta la API de GitHub para ver si hay un modelo más reciente y lo descarga.
4. **Ejecución:** La APK descarga velas de Kraken (Gratis) y calcula el LLF (Latent Liquidity Field) nativamente en Java.

## 3. Repositorios y Credenciales
- **Código:** `https://github.com/SaKinMin/Sentinel`
- **Modelos/APK:** `https://github.com/DrDiazHurtado/Sentinel_APK_model`
- **Token Configurado:** [Acceso mediante GHP Token proporcionado]

## 4. Próximos Pasos (Hoja de Ruta)
1. [ ] Estructurar proyecto Android (Gradle + Manifest).
2. [ ] Implementar `KrakenClient.java` para obtener OHLCV.
3. [ ] Portar `LatentLiquidityFieldEngine.py` a Java.
4. [ ] Configurar GitHub Action para exportación automática de modelos.
