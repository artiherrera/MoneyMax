🔁 Alias útil para desplegar cambios en producción
Para facilitar el proceso de actualización del código en el servidor, puedes usar un alias llamado deploy_moneymax que automatiza tres pasos en uno:

Accede al directorio del proyecto.
Hace git pull desde la rama main.
Reinicia el servicio de Gunicorn (moneymax.service).
🛠 Cómo crear el alias:

Abre el archivo .bashrc:
nano ~/.bashrc
Agrega esta línea al final del archivo:
alias deploy_moneymax='cd /root/MoneyMax && git pull origin main && sudo systemctl restart moneymax'
Guarda y cierra (Ctrl + O, Enter, Ctrl + X), y luego aplica los cambios:
source ~/.bashrc
✅ Uso del alias:

Cada vez que hagas cambios en la rama main y los subas a GitHub, simplemente entra al servidor y ejecuta:

deploy_moneymax
Esto actualizará el código y reiniciará la aplicación de forma inmediata y segura.