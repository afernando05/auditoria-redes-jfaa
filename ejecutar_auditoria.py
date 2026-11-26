import os
import sys
from datetime import datetime
from pathlib import Path

from netmiko import ConnectHandler

from auditoria import extraer_hostname, obtener_interfaces_up, generar_reporte


def obtener_datos_dispositivo():
    requeridas = ["NET_DEVICE_HOST", "NET_DEVICE_USER", "NET_DEVICE_PASSWORD"]
    faltantes = [dato for dato in requeridas if not os.getenv(dato)]
    if faltantes:
        raise ValueError("Faltan variables de entorno: " + ", ".join(faltantes))
    return {
        "device_type": os.getenv("NET_DEVICE_TYPE", "cisco_xe"),
        "host": os.environ["NET_DEVICE_HOST"],
        "username": os.environ["NET_DEVICE_USER"],
        "password": os.environ["NET_DEVICE_PASSWORD"],
        "port": int(os.getenv("NET_DEVICE_PORT", "22")),
        "conn_timeout": 20,
        "auth_timeout": 20,
        "banner_timeout": 20,
    }


def main():
    dispositivo = obtener_datos_dispositivo()
    carpeta = Path("respaldos")
    carpeta.mkdir(exist_ok=True)
    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Conectando al dispositivo de laboratorio...")
    with ConnectHandler(**dispositivo) as conexion:
        configuracion = conexion.send_command("show running-config", read_timeout=60)
        interfaces = conexion.send_command("show ip interface brief", read_timeout=30)
        version = conexion.send_command("show version", read_timeout=30)

    hostname = extraer_hostname(configuracion)
    interfaces_activas = obtener_interfaces_up(interfaces)

    archivo_respaldo = carpeta / f"respaldo_{marca_tiempo}.txt"
    archivo_reporte = carpeta / f"reporte_{marca_tiempo}.txt"

    archivo_respaldo.write_text(configuracion, encoding="utf-8")

    reporte = generar_reporte(hostname, interfaces_activas)
    reporte += "\n\nRESUMEN DE VERSION\n"
    reporte += version[:1000]
    archivo_reporte.write_text(reporte, encoding="utf-8")

    print("\nAuditoria finalizada.")
    print(f"Hostname detectado: {hostname}")
    print(f"Interfaces up/up: {len(interfaces_activas)}")
    print(f"Respaldo guardado en: {archivo_respaldo}")
    print(f"Reporte guardado en: {archivo_reporte}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}")