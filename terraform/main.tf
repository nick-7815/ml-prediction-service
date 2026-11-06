terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.60"
    }
  }
}

provider "proxmox" {
  endpoint  = var.pm_api_url
  api_token = "${var.pm_api_token_id}=${var.pm_api_token_secret}"
  insecure  = true
}

variable "pm_api_url" {
  type = string
}

variable "pm_api_token_id" {
  type = string
}

variable "pm_api_token_secret" {
  type      = string
  sensitive = true
}

# ВМ1 — БД (импортирована в Terraform)
resource "proxmox_virtual_environment_vm" "db_server" {
  name      = "vm1-db"
  node_name = "pve"
  on_boot       = true
  scsi_hardware = "virtio-scsi-single"
  tags      = ["db", "ml-project"]

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  operating_system {
    type = "l26"
  }

  memory {
    dedicated = 2048
  }

  network_device {
    bridge = "vmbr1"
  }
}

# ВМ2 — приложение (импортирована в Terraform)
resource "proxmox_virtual_environment_vm" "app_server" {
  name      = "vm2-app"
  node_name = "pve"
  on_boot       = true
  scsi_hardware = "virtio-scsi-single"
  tags      = ["app", "ml-project"]

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  operating_system {
    type = "l26"
  }

  memory {
    dedicated = 2048
  }

  network_device {
    bridge = "vmbr1"
  }
}

output "db_ip" {
  value = "10.10.10.101"
}

output "app_ip" {
  value = "10.10.10.102"
}
