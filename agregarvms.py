#!/usr/bin/env python3

from proxmoxer import ProxmoxAPI
import getpass
import sys
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== CONFIGURACIÓN =====
PROXMOX_USER = "root@pam"
VERIFY_SSL = False

print("\n=== CREAR VMs DESDE PLANTILLA ===")

# ===== INPUT =====
password = getpass.getpass("Password de Proxmox: ")

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

usuario = input("Usuario Proxmox (ej: alumno1@pve): ").strip()
template_vmid = input("VMID de la plantilla: ").strip()
cantidad = int(input("Número de VMs a crear: "))

# ===== CONEXIÓN =====
proxmox = ProxmoxAPI(
    nodo_ip,
    user=PROXMOX_USER,
    password=password,
    verify_ssl=VERIFY_SSL
)

print("\nCreando VMs...\n")

# ===== CREACIÓN DE VMs =====
for i in range(1, cantidad + 1):
    nuevo_vmid = int(template_vmid) + i
    nombre_vm = f"{usuario.split('@')[0]}-vm{i}"

    try:
        # Clonar VM
        proxmox.nodes(nodo_name).qemu(template_vmid).clone.post(
            newid=nuevo_vmid,
            name=nombre_vm,
            full=1
        )

        # Esperar un poco (Proxmox necesita tiempo)
        time.sleep(2)

        # Asignar permisos SOLO a esa VM
        proxmox.access.acl.put(
            path=f"/vms/{nuevo_vmid}",
            users=usuario,
            roles="alumnos"
        )

        print(f"[OK] VM creada: {nombre_vm} (VMID {nuevo_vmid})")

    except Exception as e:
        print(f"[ERROR] VM {nuevo_vmid}: {e}")
