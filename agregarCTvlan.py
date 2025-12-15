#!/usr/bin/env python3

from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
import getpass
import sys
import urllib3
import time
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def esperar_ct_desbloqueado(proxmox, nodo, vmid, timeout=60):
    import time

    for _ in range(timeout):
        config = proxmox.nodes(nodo).lxc(vmid).config.get()
        if "lock" not in config:
            return True
        time.sleep(1)

    raise Exception("Timeout esperando a que el CT se desbloquee")

# ===== CONFIG =====
PROXMOX_USER = "root@pam"
VERIFY_SSL = False
BRIDGE = "vmbr30"
NUM_VLANS = 6

print("\n=== DESPLEGAR LXC DESDE PLANTILLA + VLANs ===")

# ===== VALIDAR CREDENCIALES ANTES DE CONTINUAR =====
password = getpass.getpass("Password de Proxmox: ")

try:
    proxmox_test = ProxmoxAPI(
        "172.26.0.101",          # cualquier nodo del cluster
        user=PROXMOX_USER,
        password=password,
        verify_ssl=VERIFY_SSL
    )

    proxmox_test.version.get()

except ResourceException:
    print("\n❌ Error de autenticación con Proxmox")
    print("   Usuario o contraseña incorrectos")
    sys.exit(1)

except Exception as e:
    print("\n❌ Error inesperado al conectar con Proxmox")
    print(e)
    sys.exit(1)

print("\nSelecciona el nodo:")
print("1) Barrosa (172.26.0.101)")
print("2) Zahora  (172.26.0.102)")
print("3) Bolonia (172.26.0.103)")

opcion = input("Nodo: ").strip()

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

usuario = input("Usuario Proxmox (ej: Zalumno1@pve): ").strip()
template_vmid = int(input("VMID de la plantilla LXC: "))
nuevo_vmid = int(input("VMID nuevo para el contenedor: "))
hostname = input("Hostname del contenedor: ")

# ===== EXTRAER NÚMERO DEL USUARIO =====
username = usuario.split("@")[0]
numeros = re.findall(r'\d+', username)

if not numeros:
    print("❌ El usuario no contiene número")
    sys.exit(1)

numero_usuario = int(numeros[-1])
base_vlan = numero_usuario * 10

print(f"\n→ VLAN base detectada: {base_vlan}")
print(f"→ VLANs a crear: {list(range(base_vlan, base_vlan + NUM_VLANS))}")

# ===== CONEXIÓN =====
proxmox = ProxmoxAPI(
    nodo_ip,
    user=PROXMOX_USER,
    password=password,
    verify_ssl=VERIFY_SSL
)

# ===== CLONAR CONTENEDOR =====
print("\nClonando contenedor...")

proxmox.nodes(nodo_name).lxc(template_vmid).clone.post(
    newid=nuevo_vmid,
    hostname=hostname,
    full=1
)

esperar_ct_desbloqueado(proxmox, nodo_name, nuevo_vmid)

# ===== CONFIGURAR REDES CON VLAN =====
print("Configurando interfaces de red...")

net_config = {}

for i, vlan in enumerate(range(base_vlan, base_vlan + NUM_VLANS), start=1):
    net_config[f"net{i}"] = f"name=eth{i},bridge={BRIDGE},tag={vlan},ip=dhcp"

proxmox.nodes(nodo_name).lxc(nuevo_vmid).config.put(**net_config)

# ===== ASIGNAR PERMISOS =====
proxmox.access.acl.put(
    path=f"/vms/{nuevo_vmid}",
    users=usuario,
    roles="alumnos"
)

# ===== ARRANCAR =====
esperar_ct_desbloqueado(proxmox, nodo_name, nuevo_vmid)

print("\n✅ CONTENEDOR DESPLEGADO CORRECTAMENTE")
print(f"Usuario: {usuario}")
print(f"Contenedor: {hostname} (VMID {nuevo_vmid})")
print(f"Bridge: {BRIDGE}")
print(f"VLANs: {list(range(base_vlan, base_vlan + NUM_VLANS))}")
