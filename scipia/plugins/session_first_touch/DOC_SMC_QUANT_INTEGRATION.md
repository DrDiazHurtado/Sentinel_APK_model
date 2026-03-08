# 🏛️ Scipia: Smart Money Concepts (SMC) to Quant Integration

Este documento detalla la traducción técnica de los conceptos narrativos de "Smart Money" (ICT/SMC) al motor de predicción probabilística de Scipia.

## 1. Mapeo de Conceptos

| Concepto Narrativo (SMC/ICT) | Implementación Cuantitativa en Scipia | Módulo de Ingeniería |
| :--- | :--- | :--- |
| **Fair Value Gap (FVG) / Imbalance** | `Liquidity Void Score` | `latent_liquidity_field_engine.py` |
| **Liquidity Pools (Buy/Sell Side)** | `Stop Cluster Score` | `latent_liquidity_field_engine.py` |
| **Order Blocks / Breakers** | `Rejection & Absorption Score` | `latent_liquidity_field_engine.py` |
| **Market Structure Shift (MSS)** | `MTF Alignment (M15-H1-H4)` | `run_megacap_dashboard.py` |
| **Premium / Discount Arrays** | `Grid-based LLF Asymmetry` | `latent_liquidity_field_engine.py` |

---

## 2. Análisis Técnico de la Integración

### A. Fair Value Gaps (FVG) como "Vacíos de Liquidez"
En lugar de buscar visualmente velas que no se solapan, Scipia utiliza el `Time Acceptance Profile (TP)`. 
- **Lógica**: Si el precio atraviesa una zona con velocidad (alta volatilidad) y sin permanencia, el valor de TP cae a cero. 
- **Ventaja**: El motor KAN detecta la "ausencia de masa" en esa zona del grid, tratándola como un camino de baja resistencia. El sistema predice que el precio "llenará" el vacío rápidamente si el flujo (Flow) está alineado.

### B. Liquidity Pools como "Clusters de Stops"
Lo que SMC denomina "Liquidez por encima/debajo de máximos", Scipia lo modela como **Puntos de Atracción Gravitacional**.
- **Lógica**: Se aplica un Kernel Gaussiano sobre niveles estructurales (`Prev Day High`, `Equal Highs`, `Swing Highs`). 
- **Ventaja**: El sistema cuantifica la "densidad de stops" probable. El motor predictivo entiende que estos niveles actúan como imanes antes de un posible giro (Reversal).

### C. Order Blocks como "Nodos de Absorción"
Un Order Block es una zona de gran acumulación institucional.
- **Lógica**: El `Volume Profile Density (VP)` identifica zonas donde el volumen fue inusualmente alto en un rango estrecho de precio.
- **Ventaja**: El LLF asigna un score de "Masa" alto. El modelo de riesgos competitivos (Hazard Model) utiliza esta masa para definir el **Stop Loss Estructural**, asumiendo que el mercado necesitaría un esfuerzo institucional inmenso para atravesar ese "muro" de órdenes previo.

---

## 3. Filosofía de "Visión de Rayos X"

Al combinar **KAN (Kolmogorov-Arnold Networks)** con el **LLF (Latent Liquidity Field)**, Scipia no opera "patrones de dibujo", sino que opera **probabilidades de microestructura**:

1.  **Detección**: El LLF mapea la topografía (Montañas de órdenes vs Valles de vacíos).
2.  **Validación**: Conformal Prediction asegura que el patrón detectado tiene significancia estadística (90% Confianza).
3.  **Alineación**: El sistema MTF asegura que el "Smart Money" de 4h está empujando en la misma dirección que el "Scalping" de 15m.

---
**Nota**: Esta implementación elimina la subjetividad del análisis técnico manual, proporcionando un marco de decisión institucional ejecutable y auditable.
