# 🤖 Bot de Gestión de Constructores para Clash of Clans

Bot de Telegram para gestionar constructores y construcciones en Clash of Clans. Permite a los miembros del clan registrar sus cuentas y gestionar sus construcciones de manera eficiente.

## 🚀 Características

- 📱 Interfaz intuitiva con botones interactivos
- 👥 Gestión de múltiples cuentas por usuario
- 🏗️ Registro y seguimiento de construcciones
- ⏱️ Control de tiempo de construcción
- 📊 Listado de constructores activos
- ❌ Cancelación de construcciones
- ⚔️ Gestión de guerras
- 🏆 Información de ligas
- 🏰 Datos del clan
- 🏙️ Información del capital

## 📋 Requisitos

- Python 3.8 o superior
- Cuenta de Telegram
- Token de bot de Telegram
- Acceso a la API de Clash of Clans
- Base de datos MongoDB

## 🔧 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/friends_bot.git
cd friends_bot
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
```
Editar el archivo `.env` con tus credenciales:
```
TELEGRAM_TOKEN=tu_token_de_telegram
COC_API_TOKEN=tu_token_de_coc
MONGODB_URI=tu_uri_de_mongodb
CLAN_TAG=tag_de_tu_clan
```

## 🚀 Uso

1. Iniciar el bot:
```bash
python main.py
```

2. En Telegram, usar cualquiera de los siguientes comandos:

### Comandos Disponibles

#### 🏗️ Gestión de Constructores
- `/constructores` - Abre el menú principal de gestión
  - ➕ Añadir Cuenta - Registra una nueva cuenta de constructor
  - 🏗️ Nueva Construcción - Registra una nueva construcción
  - 📋 Listar Cuentas - Muestra las cuentas y construcciones activas
  - ❌ Cancelar Construcción - Cancela una construcción en curso

#### ⚔️ Gestión de Guerras
- `/war` - Muestra información sobre la guerra actual del clan
  - 📊 Estadísticas de la guerra
  - 👥 Lista de participantes
  - ⏱️ Tiempo restante
  - 🎯 Estado de los ataques

#### 🏆 Ligas
- `/league` - Muestra información sobre la liga actual
  - 📈 Posición en la liga
  - 🏅 Puntos y recompensas
  - 👥 Participantes destacados
  - 📊 Estadísticas de la temporada

#### 🏰 Clan
- `/clan` - Muestra información general del clan
  - 📊 Estadísticas del clan
  - 👥 Miembros destacados
  - 🏆 Logros y trofeos
  - 📈 Nivel y requisitos

#### 🏙️ Capital
- `/capital` - Muestra información del capital del clan
  - 🏰 Nivel del capital
  - 💰 Recursos disponibles
  - 🏗️ Construcciones en progreso
  - 📊 Estadísticas de ataques

## 📝 Notas

- El bot solo funciona en chats directos con el bot
- Se requiere que el jugador sea miembro del clan para registrarse
- Las construcciones se pueden cancelar en cualquier momento
- El tiempo de construcción se puede especificar en formato: 3h30m, 2d5h, 45m

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles.

## ✨ Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Clash of Clans API](https://developer.clashofclans.com/)
- [MongoDB](https://www.mongodb.com/) 