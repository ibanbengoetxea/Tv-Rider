# TV Rider 📺🚴

Una aplicación móvil moderna para consultar la programación de la TDT en España en tiempo real.

## 🚀 Cómo empezar

### 1. Configuración del Repositorio (Backend & Automation)

Para que la aplicación tenga datos actualizados automáticamente:

1.  Crea un nuevo repositorio en GitHub (ej. `tv-rider-data`).
2.  Sube las carpetas `.github` y `backend` de este proyecto a tu repositorio.
3.  Ve a la pestaña **Settings** -> **Pages** en tu repositorio de GitHub.
4.  En **Build and deployment** -> **Branch**, selecciona la rama `gh-pages` (se creará automáticamente tras la primera ejecución de la Action) y la carpeta `/ (root)`.
5.  La GitHub Action está configurada para ejecutarse todos los días a las 03:00 UTC. Puedes ejecutarla manualmente desde la pestaña **Actions** seleccionando "Update EPG Data" -> "Run workflow".

### 2. Configuración de la App Móvil

Antes de compilar la aplicación, debes indicar de dónde debe descargar los datos:

1.  Abre el archivo `mobile/src/services/api.ts`.
2.  Cambia las constantes `GITHUB_USERNAME` y `GITHUB_REPO` por tus datos de GitHub.
    ```typescript
    const GITHUB_USERNAME = 'TuUsuario';
    const GITHUB_REPO = 'NombreDeTuRepo';
    ```

### 3. Ejecución Local

#### Backend (Python)
Si quieres generar el JSON de programación manualmente:
```bash
cd backend
pip install -r requirements.txt
python process_epg.py
```
El archivo se generará en la carpeta `output/programacion.json`.

#### App Móvil (Expo)
```bash
cd mobile
npm install
npm run android # Para Android
npm run ios     # Para iOS (requiere Mac)
npm run web     # Para probar en el navegador
```

## 🛠️ Tecnologías utilizadas

*   **App**: React Native + Expo (SDK 55)
*   **Routing**: Expo Router
*   **Rendimiento**: @shopify/flash-list
*   **Estado & Caché**: React Hooks + AsyncStorage
*   **Backend**: Python 3.11 + lxml + GitHub Actions
*   **Hosting**: GitHub Pages (Arquitectura Estática)

## ✨ Características

*   **Zero Database**: No requiere servidores ni bases de datos externas costosas.
*   **Modo Offline**: Los datos se cachean localmente para consultas sin conexión.
*   **Tiempo Real**: Cálculo dinámico del programa actual y barra de progreso.
*   **Pulsing Live Indicator**: Animaciones premium para indicar emisiones en vivo.
*   **Diseño Premium**: Interfaz en modo oscuro inspirada en apps de streaming modernas.
