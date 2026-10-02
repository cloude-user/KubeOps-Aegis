# ============================================================
# Reusable Terraform Module: Neo4j Graph Database Instance
# GraphRAG Knowledge Graph Infrastructure for AI-Ops
# ============================================================

resource "azurerm_network_interface" "neo4j_nic" {
  name                = "${var.neo4j_instance_name}-nic"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
  }

  tags = var.tags
}

resource "azurerm_linux_virtual_machine" "neo4j_vm" {
  name                = var.neo4j_instance_name
  resource_group_name = var.resource_group_name
  location            = var.location
  size                = var.vm_size
  admin_username      = var.admin_username

  admin_password                  = var.admin_password
  disable_password_authentication = false

  network_interface_ids = [
    azurerm_network_interface.neo4j_nic.id
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  custom_data = base64encode(<<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose
              systemctl enable docker
              systemctl start docker
              
              docker run -d \
                --name neo4j-graphrag \
                --restart always \
                -p 7474:7474 -p 7687:7687 \
                -e NEO4J_AUTH=neo4j/${var.admin_password} \
                -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
                neo4j:5-community
              EOF
  )

  tags = var.tags
}
