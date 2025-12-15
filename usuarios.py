#!/usr/bin/env python3

from proxmoxer import ProxmoxAPI
import getpass
import sys
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ===== CONFIGURACIÓN =====
PROXMOX_USER = "root@pam"
PROXMOX_REALM = "pve"
VERIFY_SSL = False

# ===== INPUT PASSWORD =====
password = getpass.getpass("Password de Proxmox: ")

print("\nSelecciona el nodo:")
print("1) Barrosa (172.26.0.101)")
print("2) Zahora  (172.26.0.102)")
print("3) Bolonia (172.26.0.103)")

opcion = input("Nodo: ").strip()

# ===== PEDIR A QUE NODO CREAR USUARIO =====
match opcion:
    case "1":
        nodo_name = "Barrosa"
        nodo_ip = "172.26.0.101"
    case "2":
        nodo_name = "Zahora"
        nodo_ip = "172.26.0.102"
    case "3":
        nodo_name = "Bolonia"
        nodo_ip = "172.26.0.103"
    case _:
        print("❌ Nodo inválido")
        sys.exit(1)

cantidad = int(input("Número de usuarios a crear: "))
prefijo = input("Prefijo de usuario (ej: alumno): ")

# ===== CONEXIÓN =====
proxmox = ProxmoxAPI(
    nodo_ip,
    user=PROXMOX_USER,
    password=password,
    verify_ssl=VERIFY_SSL
)

# ===== CREACIÓN DE USUARIOS =====
def obtener_siguiente_numero_usuario(proxmox, prefijo, realm):
    usuarios = proxmox.access.users.get()
    max_num = 0

    patron = re.compile(rf"^{prefijo}(\d+)@{realm}$")

    for u in usuarios:
        userid = u["userid"]
        match = patron.match(userid)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    return max_num + 1

inicio = obtener_siguiente_numero_usuario(proxmox, prefijo, PROXMOX_REALM)

for i in range(inicio, inicio + cantidad):
    username = f"{prefijo}{i}@{PROXMOX_REALM}"
    user_pass = f"{prefijo}{i}123"

    try:
        # Crear usuario
        proxmox.access.users.post(
            userid=username,
            password=user_pass,
            comment=f"Usuario creado por script para {nodo_name}"
        )

        # Asignar permisos SOLO al nodo
        proxmox.access.acl.put(
            path=f"/nodes/{nodo_name}",
            users=username,
            roles="alumnos"
        )

        print(f"[OK] Usuario creado: {username} en el nodo {nodo_name}")

    except Exception as e:
        print(f"[ERROR] {username}: {e}")

