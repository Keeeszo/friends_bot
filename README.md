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
- 🏆 Información de liga actual
- 🏰 Datos del clan
- 🏙️ Información de la capital

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

- `/comandos` - Muestra la lista de comandos disponibles
- `/info` - Muestra información básica del clan
- `/guerra` - Estado detallado de la guerra actual
- `/capital` - Progreso del fin de semana de ataque a la capital
- `/liga` - Información de la liga de clanes actual
- `/miembros` - Lista de miembros + Top 5 donadores del clan
- `/constructores` - Gestión de múltiples constructores para tu cuenta de Telegram

#### 🏗️ Gestión de Constructores
El comando `/constructores` permite:
- ➕ Añadir Cuenta - Registra una nueva cuenta de constructor
- 🏗️ Nueva Construcción - Registra una nueva construcción
- 📋 Listar Cuentas - Muestra las cuentas y construcciones activas
- ❌ Cancelar Construcción - Cancela una construcción en curso

## 📝 Notas

- El bot solo funciona en chats directos + envío de mensajes a un grupo en específico
- Se requiere que el jugador sea miembro del clan para registrarse
- Las construcciones se pueden cancelar en cualquier momento
- El tiempo de construcción se puede especificar en formato: 3h30m, 2d5h, 45m

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles.

## ✨ Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Clash of Clans API](https://developer.clashofclans.com/)
- [MongoDB](https://www.mongodb.com/) 